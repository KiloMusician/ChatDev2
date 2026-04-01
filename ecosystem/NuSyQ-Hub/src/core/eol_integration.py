"""Epistemic-Operational Lattice: Unified Integration.

Ties together the three planes (Observation, Planning, Execution) into a coherent
decision cycle accessible via the orchestrate.py facade.

Implements the sense → propose → critique → act → learn lifecycle.

Usage:
    from src.core.eol_integration import EOLOrchestrator
    eol = EOLOrchestrator()

    # Phase 1: Sense + Propose
    world_state = eol.sense()
    actions = eol.propose(world_state, user_objective="Analyze errors")

    # Phase 2: Critique (optional, requires policy compiler)
    # approved_action = eol.critique(actions[0], world_state)

    # Phase 3: Act
    receipt = eol.act(actions[0], world_state)

    # Phase 4: Learn (deferred to v0.2)
    # eol.learn(receipt)
"""

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from src.core.action_receipt_ledger import (ActionReceipt,
                                                ActionReceiptLedger)
    from src.core.build_world_state import build_world_state
    from src.core.plan_from_world_state import (PlanGenerator,
                                                plan_from_world_state)
except ModuleNotFoundError:
    # Support direct execution: `python src/core/eol_integration.py`
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from src.core.action_receipt_ledger import (ActionReceipt,
                                                ActionReceiptLedger)
    from src.core.build_world_state import build_world_state
    from src.core.plan_from_world_state import (PlanGenerator,
                                                plan_from_world_state)

logger = logging.getLogger(__name__)


class EOLOrchestrator:
    """Orchestrates the Epistemic-Operational Lattice decision cycle."""

    def __init__(
        self,
        workspace_root: Path = Path("."),
        ledger_file: Path = Path("src/core/action_receipt_ledger.jsonl"),
        state_snapshot_file: Path = Path("state/world_state_snapshot.json"),
    ):
        """Initialize EOLOrchestrator with workspace_root, ledger_file, and state_snapshot_file."""
        self.workspace_root = workspace_root
        self.ledger = ActionReceiptLedger(ledger_file, workspace_root=workspace_root)
        self.state_snapshot_file = state_snapshot_file
        self.state_snapshot_file.parent.mkdir(parents=True, exist_ok=True)
        self.planner = PlanGenerator()
        self.previous_world_state: dict[str, Any] | None = None
        self._consciousness_loop: Any | None = None  # Lazy-init on first SECURITY critique

    # --- Plane 1: Observation (Sense) ---

    def sense(self) -> dict[str, Any]:
        """Build a unified world state by observing all signals.

        Returns:
            World state snapshot matching world_state.schema.json
        """
        logger.info("EOL: Sensing world state...")

        # Build world state from observations + coherence reconciliation
        world_state = build_world_state(
            self.workspace_root,
            previous_state=self.previous_world_state,
        )

        # Persist snapshot for audit trail
        self._write_state_snapshot(world_state)

        # Cache for drift detection in next cycle
        self.previous_world_state = world_state

        logger.info(
            f"EOL: World state built (epoch={world_state['decision_epoch']}, "
            f"signals={len(world_state['signals']['facts'])}, "
            f"contradictions={len(world_state['coherence']['contradictions'])})"
        )

        return world_state

    # --- Plane 2: Planning (Propose) ---

    def propose(
        self,
        world_state: dict[str, Any],
        user_objective: str = "",
    ) -> list[dict[str, Any]]:
        """Generate ordered action candidates from world state + objective.

        Args:
            world_state: Output from sense()
            user_objective: What the user wants

        Returns:
            Ordered list of Action dicts (ready for critique/execution)
        """
        logger.info(f"EOL: Proposing actions for objective: {user_objective}")

        # Generate plan
        plan = plan_from_world_state(world_state, user_objective)
        actions = plan["actions"]

        logger.info(f"EOL: Generated {len(actions)} action candidates")
        for i, action in enumerate(actions, 1):
            risk = action.get("risk_score", 0.0)
            cost = action.get("estimated_cost", {})
            logger.debug(
                f"  {i}. {action['agent']}/{action['task_type']} risk={risk:.2f} tokens={cost.get('tokens', 0)}"
            )

        return actions

    # --- Plane 3: Critique (Policy Gates - v0.2) ---

    def critique(
        self,
        action: dict[str, Any],
        world_state: dict[str, Any],
    ) -> bool:
        """Evaluate action against policies (simplified v0.1).

        In v0.2, this will integrate with policy_compiler.py to evaluate
        explicit safety gates + Culture Ship approval loops.

        Args:
            action: Action candidate from propose()
            world_state: Current world state

        Returns:
            True if action is approved, False otherwise
        """
        # v0.1: Simple heuristic checks
        risk_score = action.get("risk_score", 0.0)
        max_risk = (
            world_state.get("policy_state", {}).get("safety_gates", {}).get("max_risk_score", 0.7)
        )

        policy_category = action.get("policy_category", "FEATURE")

        logger.info(
            f"EOL: Critiquing action {action['action_id'][:8]}... risk={risk_score:.2f} category={policy_category}"
        )

        if risk_score > max_risk:
            logger.warning(f"EOL: Action rejected (risk {risk_score:.2f} > max {max_risk})")
            return False

        # v0.2: Check Culture Ship approval for SECURITY category actions
        if policy_category == "SECURITY":
            approved = self._request_culture_ship_approval(action, world_state)
            if not approved:
                logger.warning(
                    f"EOL: SECURITY action {action['action_id'][:8]}... rejected by Culture Ship"
                )
                return False

        logger.info("EOL: Action approved")
        return True

    def _request_culture_ship_approval(
        self, action: dict[str, Any], world_state: dict[str, Any]
    ) -> bool:
        """Ask Culture Ship (ConsciousnessLoop) to approve a SECURITY-category action.

        Auto-approves gracefully when the SimulatedVerse bridge is unavailable.
        """
        if self._consciousness_loop is None:
            try:
                from src.orchestration.consciousness_loop import \
                    ConsciousnessLoop

                self._consciousness_loop = ConsciousnessLoop()
                self._consciousness_loop.initialize()
            except Exception as exc:
                logger.debug("EOL: ConsciousnessLoop unavailable (%s) — auto-approving", exc)
                return True

        action_desc = (
            f"{action.get('task_type', 'unknown')} on {action.get('agent', 'unknown')}: "
            f"{action.get('description', action.get('action_id', '?'))[:120]}"
        )
        context = {
            "action_id": action.get("action_id"),
            "risk_score": action.get("risk_score", 0.0),
            "policy_category": "SECURITY",
            "decision_epoch": world_state.get("decision_epoch"),
        }
        approval = self._consciousness_loop.request_approval(action_desc, context)
        logger.info(
            "EOL: Culture Ship %s SECURITY action — %s",
            "approved" if approval.approved else "VETOED",
            approval.reason,
        )
        return approval.approved

    # --- Plane 4: Execution (Act) ---

    def act(
        self,
        action: dict[str, Any],
        world_state: dict[str, Any],
        dry_run: bool = False,
    ) -> ActionReceipt:
        """Execute action and emit receipt.

        Args:
            action: Action dict from propose()
            world_state: Current world state
            dry_run: If True, simulate without actual dispatch

        Returns:
            ActionReceipt with full execution trace
        """
        action_id = action.get("action_id", "unknown")
        logger.info(f"EOL: Acting on {action_id[:8]}... (agent={action.get('agent')})")

        # Execute with full receipt tracing
        receipt = self.ledger.execute_action(action, world_state, dry_run=dry_run)

        logger.info(f"EOL: Action completed with status {receipt.status}")

        return receipt

    # --- Plane 5: Learning (v0.2) ---

    def learn(self, receipt: ActionReceipt) -> None:
        """Evaluate action outcome + update agent rankings (deferred to v0.2).

        In v0.2, this will:
        1. Check if action achieved postconditions
        2. Evaluate user satisfaction (if available)
        3. Update agent success rates
        4. Adjust risk assessments
        5. Feed back to future planning
        """
        logger.debug(f"EOL: Learning from receipt {receipt.receipt_id}")

        # v0.2 adaptive learning implementation
        try:
            ledger = ActionReceiptLedger(self.workspace_root)

            # 1. Retrieve historical performance for this action type
            action_type = receipt.action_type
            history = [r for r in ledger.recent(limit=50) if r.action_type == action_type]

            # 2. Calculate success rate for this action type
            if history:
                successful = sum(1 for r in history if r.status == "completed")
                success_rate = successful / len(history)
                logger.debug(f"EOL: Action type '{action_type}' success rate: {success_rate:.1%}")

            # 3. Update agent performance metrics (if agent tracking available)
            agent_used = receipt.metadata.get("agent")
            if agent_used:
                agent_history = [r for r in history if r.metadata.get("agent") == agent_used]
                if agent_history:
                    agent_success = sum(1 for r in agent_history if r.status == "completed")
                    agent_rate = agent_success / len(agent_history)
                    logger.debug(f"EOL: Agent '{agent_used}' success rate: {agent_rate:.1%}")

            # 4. Log learning event for future reference
            logger.info(
                f"EOL: Learned from {receipt.receipt_id} - action={action_type}, status={receipt.status}"
            )
        except Exception as e:
            logger.warning(f"EOL: Learning failed for {receipt.receipt_id}: {e}")

    # --- Complete Decision Cycle ---

    def full_cycle(
        self,
        user_objective: str = "",
        auto_execute: bool = False,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Run complete sense → propose → critique → act cycle.

        Args:
            user_objective: What user wants done
            auto_execute: If True, automatically execute top action
            dry_run: If True, simulate execution

        Returns:
            {
                "world_state": {...},
                "actions": [...],
                "execution_results": [...],
                "metadata": {...}
            }
        """
        logger.info(f"EOL: Starting full cycle (objective={user_objective[:50]}...)")

        # Phase 1: Sense
        world_state = self.sense()

        # Phase 2: Propose
        actions = self.propose(world_state, user_objective)

        if not actions:
            logger.warning("EOL: No actions generated; cycle complete with no output")
            return {
                "world_state": world_state,
                "actions": [],
                "execution_results": [],
                "metadata": {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "reason": "No valid actions for objective",
                },
            }

        # Phase 3: Critique
        approved_actions = []
        for action in actions:
            if self.critique(action, world_state):
                approved_actions.append(action)

        if not approved_actions:
            logger.warning("EOL: No actions passed critique; cycle complete with no execution")
            return {
                "world_state": world_state,
                "actions": actions,
                "execution_results": [],
                "metadata": {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "reason": "All actions rejected by policy gates",
                },
            }

        # Phase 4: Execute (top-ranked action if auto_execute)
        execution_results = []
        if auto_execute:
            top_action = approved_actions[0]
            logger.info(
                f"EOL: Auto-executing top action: {top_action['agent']}/{top_action['task_type']}"
            )
            receipt = self.act(top_action, world_state, dry_run=dry_run)
            execution_results.append(receipt.to_dict())

        # Return structured output
        return {
            "world_state": world_state,
            "actions": list(actions),  # Include all candidates
            "approved_actions": approved_actions,
            "execution_results": execution_results,
            "metadata": {
                "timestamp": datetime.now(UTC).isoformat(),
                "user_objective": user_objective,
                "total_candidates": len(actions),
                "approved": len(approved_actions),
                "executed": len(execution_results),
                "schema_version": "0.1",
            },
        }

    # --- State Persistence ---

    def _write_state_snapshot(self, world_state: dict[str, Any]) -> None:
        """Write world state snapshot to disk for audit trail."""
        try:
            with open(self.state_snapshot_file, "w", encoding="utf-8") as f:
                json.dump(world_state, f, indent=2, default=str)
            logger.debug(f"State snapshot written to {self.state_snapshot_file}")
        except Exception as e:
            logger.error(f"Failed to write state snapshot: {e}")

    def read_state_snapshot(self) -> dict[str, Any] | None:
        """Read the current state snapshot if it exists."""
        try:
            if self.state_snapshot_file.exists():
                with open(self.state_snapshot_file, encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, ValueError, OSError) as e:
            logger.error(f"Failed to read state snapshot: {e}")
        return None

    # --- Statistics & Debugging ---

    def stats(self) -> dict[str, Any]:
        """Get statistics about action execution."""
        return self.ledger.get_action_stats()

    def debug_info(self) -> dict[str, Any]:
        """Get debug info for troubleshooting."""
        return {
            "workspace_root": str(self.workspace_root),
            "ledger_file": str(self.ledger.ledger_file),
            "state_snapshot_file": str(self.state_snapshot_file),
            "action_stats": self.stats(),
            "previous_world_state_epoch": (self.previous_world_state or {}).get(
                "decision_epoch", -1
            ),
        }


# --- Integration with orchestrate.py ---


def integrate_eol_with_orchestrate() -> None:
    """Wire EOL into the main orchestration facade.

    This function should be called during orchestrate.py initialization
    to make EOL methods available via the unified nusyq interface.
    """
    logger.info("Integrating Epistemic-Operational Lattice with orchestrate.py")

    # Wire EOL methods into the orchestrate facade
    try:
        from src.core.orchestrate import nusyq

        # Create EOL orchestrator instance
        eol = EOLOrchestrator()

        # Add EOL methods to the unified facade
        nusyq.sense = eol.sense
        nusyq.propose = eol.propose
        nusyq.critique = eol.critique
        nusyq.act = eol.act
        nusyq.learn = eol.learn
        nusyq.full_cycle = eol.full_cycle

        logger.info(
            "EOL methods registered: nusyq.sense(), .propose(), .critique(), .act(), .learn()"
        )
    except ImportError as e:
        logger.warning(f"EOL integration deferred - orchestrate not available: {e}")
    except Exception as e:
        logger.error(f"EOL integration failed: {e}")


def full_cycle(
    user_objective: str = "",
    auto_execute: bool = False,
    dry_run: bool = False,
    workspace_root: Path = Path("."),
) -> dict[str, Any]:
    """Module-level convenience wrapper used by tests/automation."""
    orchestrator = EOLOrchestrator(workspace_root=workspace_root)
    return orchestrator.full_cycle(
        user_objective=user_objective,
        auto_execute=auto_execute,
        dry_run=dry_run,
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.core.eol_integration",
        description="Run EOL sense/propose/critique/act full cycle",
    )
    parser.add_argument(
        "--objective",
        default="Analyze the error report and suggest fixes",
        help="Objective used for action proposal",
    )
    parser.add_argument(
        "--auto",
        "--auto-execute",
        dest="auto_execute",
        action="store_true",
        help="Execute the top approved action",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate execution without dispatching action (default unless --live)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Disable dry-run mode when auto execution is enabled",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full cycle output as JSON",
    )
    return parser


if __name__ == "__main__":
    # Quick test / automation entrypoint
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s: %(message)s",
    )
    args = _build_arg_parser().parse_args()

    eol = EOLOrchestrator(workspace_root=Path("."))

    dry_run = True
    if args.live:
        dry_run = False
    elif args.dry_run:
        dry_run = True

    result = eol.full_cycle(
        user_objective=args.objective,
        auto_execute=args.auto_execute,
        dry_run=dry_run,
    )

    if args.json:
        logger.info(json.dumps(result, indent=2, default=str))
        raise SystemExit(0)

    logger.info("\n=== EOL Cycle Result ===")
    logger.info(json.dumps(result["metadata"], indent=2))
    logger.info(f"\nActions proposed: {len(result['actions'])}")
    logger.info(f"Actions approved: {len(result['approved_actions'])}")
    logger.info(f"Actions executed: {len(result['execution_results'])}")

    if result["actions"]:
        logger.info("\nTop action:")
        top = result["actions"][0]
        logger.info(f"  Agent: {top['agent']}")
        logger.info(f"  Task: {top['task_type']}")
        logger.info(f"  Risk: {top['risk_score']:.2f}")
        logger.info(f"  Cost: {top['estimated_cost']['tokens']} tokens")
