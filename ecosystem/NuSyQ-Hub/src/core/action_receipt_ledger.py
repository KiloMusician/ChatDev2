"""Epistemic-Operational Lattice: Execution Plane with Receipt Ledger.

Wraps action execution in full tracing and immutable receipt logging:
1. **Pre-execution:** Capture intent, validate preconditions
2. **Execution:** Delegate to background_task_orchestrator
3. **Post-execution:** Validate postconditions, emit receipt
4. **Ledger:** Append-only JSONL with all action evidence

Usage:
    from src.core.action_receipt_ledger import ActionReceiptLedger
    ledger = ActionReceiptLedger()
    receipt = ledger.execute_action(action, world_state)
    print(receipt['status'], receipt['duration_s'])
"""

import json
import logging
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

# Import types from planning module
try:
    from src.core.plan_from_world_state import Action, RiskLevel, TaskType
except ImportError:
    # Fallback: redefine minimal types
    from enum import Enum

    class TaskType(Enum):
        ANALYSIS = "analysis"
        CODE_GENERATION = "code_generation"
        CODE_REVIEW = "code_review"
        DEBUGGING = "debugging"
        TESTING = "testing"
        DOCUMENTATION = "documentation"
        REFACTORING = "refactoring"
        POLICY_EVALUATION = "policy_evaluation"


try:
    from src.core.quest_receipt_linkage import link_receipt_to_quest
except ImportError:
    link_receipt_to_quest = None


# --- Receipt Model ---


@dataclass
class ActionReceipt:
    """Immutable proof of action execution."""

    receipt_id: str
    action_id: str
    timestamp_start: str
    timestamp_end: str
    duration_s: float
    agent: str
    task_type: str
    status: str  # "SUCCESS", "FAILED", "PARTIAL", "CANCELLED"
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    artifacts: list[str] = field(default_factory=list)
    preconditions_met: bool = False
    postconditions_met: bool = False
    postcondition_validation_results: dict[str, bool] = field(default_factory=dict)
    error_message: str | None = None
    linked_quest_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize receipt to dict."""
        return asdict(self)

    def to_jsonl(self) -> str:
        """Serialize receipt to JSONL (single line)."""
        return json.dumps(self.to_dict(), default=str)


# --- Precondition & Postcondition Validators ---


class PreconditionValidator:
    """Check that action preconditions are met."""

    @staticmethod
    def validate_all(
        preconditions: list[str], world_state: dict[str, Any]
    ) -> tuple[bool, dict[str, Any]]:
        """Validate all preconditions. Return (all_valid, details)."""
        import re

        details: dict[str, Any] = {}

        for precond in preconditions:
            # Parse precondition (simplistic pattern matching)
            if "online" in precond:
                # Check agent status in world state
                agents_status = PreconditionValidator._check_agents(world_state)
                match = re.search(
                    r"agent\s+([a-zA-Z0-9_\-]+)\s+is\s+online", precond, re.IGNORECASE
                )
                if match:
                    agent_name = match.group(1).strip().lower()
                    agent_record = agents_status.get(agent_name)
                    if not isinstance(agent_record, dict):
                        # Case-insensitive fallback for registry keys
                        agent_record = next(
                            (
                                info
                                for name, info in agents_status.items()
                                if str(name).strip().lower() == agent_name
                                and isinstance(info, dict)
                            ),
                            {},
                        )
                    details[precond] = bool(agent_record.get("online", False))
                else:
                    # Unknown "online" precondition shape; fail closed.
                    details[precond] = False
            elif "tokens" in precond:
                # Check budget
                budget = world_state.get("policy_state", {}).get("resource_budgets", {})
                token_budget = budget.get("token_budget_remaining", 0)
                required = PreconditionValidator._extract_number(precond)
                details[precond] = token_budget >= required
            elif "time" in precond:
                # Check time budget
                budget = world_state.get("policy_state", {}).get("resource_budgets", {})
                time_budget = budget.get("time_budget_remaining_s", 0)
                required = PreconditionValidator._extract_number(precond)
                details[precond] = time_budget >= required
            else:
                # Default: assume satisfied unless proven otherwise
                details[precond] = True

        all_valid = all(details.values())
        return all_valid, details

    @staticmethod
    def _check_agents(world_state: dict[str, Any]) -> dict[str, Any]:
        """Extract agent status from world state."""
        return world_state.get("runtime_state", {}).get("agent_capabilities", {})

    @staticmethod
    def _extract_number(text: str) -> int:
        """Extract first integer from string."""
        import re

        match = re.search(r"\d+", text)
        return int(match.group()) if match else 0


class PostconditionValidator:
    """Check that action postconditions are met."""

    @staticmethod
    def validate_all(
        postconditions: list[str],
        exit_code: int | None,
        stdout: str,
        stderr: str,
    ) -> tuple[bool, dict[str, bool]]:
        """Validate all postconditions. Return (all_valid, details)."""
        details: dict[str, bool] = {}

        for postcond in postconditions:
            # Parse postcondition
            if "completed" in postcond.lower():
                # Check exit code is 0
                details[postcond] = exit_code == 0
            elif "receipt" in postcond.lower() or "logged" in postcond.lower():
                # This will be checked after ledger append; mark as satisfied
                details[postcond] = True
            elif "error" in postcond.lower():
                # Check that no errors in output
                details[postcond] = (exit_code == 0) and (
                    not stderr or "error" not in stderr.lower()
                )
            else:
                # Default: satisfied if exit code 0
                details[postcond] = exit_code == 0

        all_valid = all(details.values())
        return all_valid, details


# --- Action Receipt Ledger ---


class ActionReceiptLedger:
    """Manages action execution + receipt logging."""

    def __init__(
        self,
        ledger_file: Path = Path("src/core/action_receipt_ledger.jsonl"),
        workspace_root: Path = Path("."),
    ):
        """Initialize ActionReceiptLedger with ledger_file and workspace_root."""
        self.ledger_file = ledger_file
        self.workspace_root = workspace_root
        self.ledger_file.parent.mkdir(parents=True, exist_ok=True)

    def execute_action(
        self,
        action: dict[str, Any],
        world_state: dict[str, Any],
        dry_run: bool = False,
    ) -> ActionReceipt:
        """Execute action and emit receipt.

        Args:
            action: Action dict from planning module
            world_state: Current world state
            dry_run: If True, simulate execution without actually dispatching

        Returns:
            ActionReceipt with full execution trace
        """
        receipt_id = str(uuid4())
        action_id = action.get("action_id", str(uuid4()))
        agent = action.get("agent", "unknown")
        task_type = action.get("task_type", "unknown")
        timestamp_start = datetime.now(UTC).isoformat()

        # Phase 1: Validate preconditions
        preconditions = action.get("preconditions", [])
        precond_valid, precond_details = PreconditionValidator.validate_all(
            preconditions, world_state
        )

        if not precond_valid:
            logger.warning(f"Action {action_id} preconditions not met: {precond_details}")
            receipt = ActionReceipt(
                receipt_id=receipt_id,
                action_id=action_id,
                timestamp_start=timestamp_start,
                timestamp_end=datetime.now(UTC).isoformat(),
                duration_s=0.0,
                agent=agent,
                task_type=task_type,
                status="CANCELLED",
                exit_code=1,
                preconditions_met=False,
                error_message=f"Preconditions not met: {precond_details}",
            )
            self._append_receipt(receipt)
            return receipt

        # Phase 2: Execute action (delegate to background orchestrator)
        if dry_run:
            exit_code = 0
            stdout = f"[DRY RUN] Would execute: {action.get('description')}"
            stderr = ""
        else:
            exit_code, stdout, stderr = self._dispatch_action(action, world_state)

        timestamp_end = datetime.now(UTC).isoformat()
        duration_s = (
            datetime.fromisoformat(timestamp_end) - datetime.fromisoformat(timestamp_start)
        ).total_seconds()

        # Phase 3: Validate postconditions
        postconditions = action.get("postconditions", [])
        postcond_valid, postcond_details = PostconditionValidator.validate_all(
            postconditions, exit_code, stdout, stderr
        )

        # Phase 4: Build receipt
        status = "SUCCESS" if exit_code == 0 else "FAILED"
        if not postcond_valid:
            status = "PARTIAL"

        receipt = ActionReceipt(
            receipt_id=receipt_id,
            action_id=action_id,
            timestamp_start=timestamp_start,
            timestamp_end=timestamp_end,
            duration_s=duration_s,
            agent=agent,
            task_type=task_type,
            status=status,
            exit_code=exit_code,
            stdout=stdout[:2000],  # Truncate large outputs
            stderr=stderr[:1000],
            preconditions_met=precond_valid,
            postconditions_met=postcond_valid,
            postcondition_validation_results=postcond_details,
            error_message=None if exit_code == 0 else (stderr or "Unknown error"),
            linked_quest_id=action.get("quest_dependency")
            or world_state.get("objective", {}).get("quest_id"),
            metadata={
                "policy_category": action.get("policy_category", ""),
                "estimated_cost": action.get("estimated_cost", {}),
                "risk_score": action.get("risk_score", 0.0),
            },
        )

        # Phase 5: Log receipt to immutable ledger
        self._append_receipt(receipt)
        self._record_memory_linkage(receipt, world_state)

        logger.info(f"Action {action_id} completed with status {status} (exit_code={exit_code})")
        return receipt

    def _dispatch_action(
        self,
        action: dict[str, Any],
        _world_state: dict[str, Any],
    ) -> tuple[int, str, str]:
        """Dispatch action to background task orchestrator.

        Returns:
            (exit_code, stdout, stderr)
        """
        agent = action.get("agent", "ollama")
        description = action.get("description", "Unknown task")
        action.get("task_type", "analysis")

        # Try to dispatch via background_task_orchestrator
        try:
            # Build command to dispatch task
            dispatch_cmd = [
                sys.executable,
                "scripts/start_nusyq.py",
                "dispatch",
                "ask",
                agent,
                description,
            ]

            result = subprocess.run(
                dispatch_cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.workspace_root),
            )

            return result.returncode, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            return 124, "", "Action execution timeout"
        except Exception as e:
            logger.error(f"Failed to dispatch action: {e}")
            return 1, "", str(e)

    def _append_receipt(self, receipt: ActionReceipt) -> None:
        """Append receipt to immutable ledger."""
        try:
            with open(self.ledger_file, "a", encoding="utf-8") as f:
                f.write(receipt.to_jsonl() + "\n")
            logger.debug(f"Receipt {receipt.receipt_id} appended to ledger")
        except Exception as e:
            logger.error(f"Failed to append receipt to ledger: {e}")

    def _record_memory_linkage(
        self,
        receipt: ActionReceipt,
        world_state: dict[str, Any],
    ) -> None:
        """Attach receipt to quest memory when quest_dependency exists."""
        quest_id = receipt.linked_quest_id
        if not quest_id or not link_receipt_to_quest:
            return
        try:
            link_receipt_to_quest(
                receipt=receipt.to_dict(),
                quest_id=quest_id,
                world_state=world_state,
                workspace_root=self.workspace_root,
            )
        except Exception as exc:
            logger.warning("Failed to record quest-receipt linkage: %s", exc)

    def read_receipts(
        self,
        action_id: str | None = None,
        agent: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[ActionReceipt]:
        """Read receipts from ledger with optional filtering.

        Returns:
            List of receipts (most recent first)
        """
        receipts = []

        if not self.ledger_file.exists():
            return receipts

        try:
            with open(self.ledger_file, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        # Apply filters
                        if action_id and data.get("action_id") != action_id:
                            continue
                        if agent and data.get("agent") != agent:
                            continue
                        if status and data.get("status") != status:
                            continue

                        receipt = ActionReceipt(**data)
                        receipts.append(receipt)
                    except json.JSONDecodeError:
                        logger.warning(f"Malformed ledger line: {line[:100]}")
                        continue

            # Return most recent first
            receipts.sort(key=lambda r: r.timestamp_end, reverse=True)
            return receipts[:limit]

        except Exception as e:
            logger.error(f"Failed to read ledger: {e}")
            return receipts

    def get_action_stats(self) -> dict[str, Any]:
        """Compute statistics over ledger."""
        receipts = self.read_receipts(limit=10000)

        total = len(receipts)
        successful = len([r for r in receipts if r.status == "SUCCESS"])
        failed = len([r for r in receipts if r.status == "FAILED"])
        partial = len([r for r in receipts if r.status == "PARTIAL"])

        avg_duration = sum(r.duration_s for r in receipts) / total if total > 0 else 0.0

        agents = {}
        for receipt in receipts:
            if receipt.agent not in agents:
                agents[receipt.agent] = {"count": 0, "successful": 0}
            agents[receipt.agent]["count"] += 1
            if receipt.status == "SUCCESS":
                agents[receipt.agent]["successful"] += 1

        return {
            "total_actions": total,
            "successful": successful,
            "failed": failed,
            "partial": partial,
            "success_rate": successful / total if total > 0 else 0.0,
            "avg_duration_s": avg_duration,
            "by_agent": agents,
        }


# --- Convenience Functions ---


def execute_action_and_log(
    action: dict[str, Any],
    world_state: dict[str, Any],
    ledger_file: Path | None = None,
) -> ActionReceipt:
    """Initialize ActionReceiptLedger."""
    """Execute an action and log receipt (convenience function)."""
    ledger = ActionReceiptLedger(ledger_file or Path("src/core/action_receipt_ledger.jsonl"))
    return ledger.execute_action(action, world_state)


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)

    ledger = ActionReceiptLedger()

    # Sample action
    sample_action = {
        "action_id": str(uuid4()),
        "agent": "ollama",
        "task_type": "analysis",
        "description": "Analyze the error report",
        "preconditions": ["Agent ollama is online", "Available tokens >= 500"],
        "postconditions": ["Task completed with status recorded"],
        "quest_dependency": "quest-123",
    }

    sample_world_state = {
        "policy_state": {
            "resource_budgets": {
                "token_budget_remaining": 5000,
                "time_budget_remaining_s": 300,
            }
        },
        "runtime_state": {
            "agent_capabilities": {
                "ollama": {"online": True, "latency_ms": 100},
            }
        },
    }

    # Execute (dry run)
    receipt = ledger.execute_action(sample_action, sample_world_state, dry_run=True)
    logger.info(f"Receipt: {receipt.receipt_id}, Status: {receipt.status}")
    logger.info(f"Stats: {ledger.get_action_stats()}")
