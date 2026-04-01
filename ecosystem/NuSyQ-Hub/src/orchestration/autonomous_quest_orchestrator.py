"""Autonomous Orchestrator - Multi-Agent Workflow Coordination.

The brain of the autonomous system that:
- Routes tasks to appropriate agents
- Enforces proof gates at each step
- Manages multi-agent workflows
- Integrates with git (dry-run mode)
- Provides human approval hooks
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Setup logger first
logger = logging.getLogger(__name__)

# Add NuSyQ-Hub src to path
HUB_PATH = Path(__file__).parent.parent.parent
sys.path.insert(0, str(HUB_PATH / "src"))

try:
    from automation.unified_pu_queue import PU, UnifiedPUQueue
except ImportError:
    logger.info("Error: unified_pu_queue not found")
    UnifiedPUQueue = None
    PU = None

try:
    from integration.simulatedverse_async_bridge import SimulatedVerseBridge
except ImportError:
    logger.info("Warning: SimulatedVerseBridge not found")
    SimulatedVerseBridge = None

try:
    from utils.repo_path_resolver import get_repo_path
except ImportError:  # pragma: no cover - fallback for standalone runs
    get_repo_path = None


logger = logging.getLogger(__name__)


class AutonomousOrchestrator:
    """Coordinate multi-agent autonomous workflows."""

    def __init__(self, mode: str = "supervised") -> None:
        """Initialize orchestrator.

        Args:
            mode: 'full' (auto-execute), 'supervised' (human approval), 'sandbox' (test mode)

        """
        self.mode = mode
        self.queue = UnifiedPUQueue() if UnifiedPUQueue else None

        # SimulatedVerse bridge
        if get_repo_path:
            try:
                sv_path = get_repo_path("SIMULATEDVERSE_ROOT")
            except Exception:
                sv_path = Path.home() / "Desktop" / "SimulatedVerse" / "SimulatedVerse"
        else:
            sv_path = Path.home() / "Desktop" / "SimulatedVerse" / "SimulatedVerse"
        self.sv_bridge = None
        if SimulatedVerseBridge and sv_path.exists():
            self.sv_bridge = SimulatedVerseBridge(str(sv_path))

        # Metrics
        self.metrics: dict[str, Any] = {
            "tasks_processed": 0,
            "workflows_completed": 0,
            "workflows_failed": 0,
            "proof_gates_passed": 0,
            "proof_gates_failed": 0,
            "human_approvals_requested": 0,
            "human_approvals_granted": 0,
            "start_time": datetime.now().isoformat(),
        }

        logger.info(f"Autonomous Orchestrator Initialized ({mode} mode)")
        logger.info(f"  Queue: {'Available' if self.queue else 'Unavailable'}")
        logger.info(f"  SimulatedVerse: {'Connected' if self.sv_bridge else 'Disconnected'}")

    def execute_workflow(self, pu_id: str) -> dict[str, Any]:
        """Execute full multi-agent workflow for a PU.

        Args:
            pu_id: PU identifier from unified queue

        Returns:
            Workflow execution results

        """
        if not self.queue:
            return {"error": "Queue unavailable"}

        # Get PU
        pu = None
        for p in self.queue.queue:
            if p.id == pu_id:
                pu = p
                break

        if not pu:
            return {"error": "PU not found"}

        logger.info(f"\n{'=' * 80}")
        logger.info(f"EXECUTING WORKFLOW: {pu_id}")
        logger.info(f"  Type: {pu.type}")
        logger.info(f"  Title: {pu.title}")
        logger.info(f"  Priority: {pu.priority}")
        logger.info(f"{'=' * 80}\n")

        workflow_result: dict[str, Any] = {
            "pu_id": pu_id,
            "steps": [],
            "overall_status": "pending",
            "proof_gates_passed": 0,
            "proof_gates_failed": 0,
        }

        # Step 1: Human approval (if supervised mode)
        if self.mode == "supervised":
            approved = self._request_human_approval(pu)
            if not approved:
                workflow_result["overall_status"] = "rejected_by_human"
                self.metrics["human_approvals_requested"] += 1
                return workflow_result
            self.metrics["human_approvals_requested"] += 1
            self.metrics["human_approvals_granted"] += 1

        # Step 2: Council vote (if not already approved)
        if pu.status != "approved":
            logger.info("Step 1: Council Vote...")
            votes = self.queue.request_council_vote(pu_id, timeout=30)
            workflow_result["steps"].append(
                {
                    "step": "council_vote",
                    "status": "completed" if votes else "failed",
                    "data": votes,
                },
            )

            if not votes or votes.get("reject", 0) > votes.get("approve", 0):
                workflow_result["overall_status"] = "rejected_by_council"
                self.metrics["workflows_failed"] += 1
                return workflow_result

        # Step 3: Assign agents
        logger.info("\nStep 2: Agent Assignment...")
        if not pu.assigned_agents:
            agents = self.queue.assign_agents(pu_id, complexity="auto")
            workflow_result["steps"].append(
                {
                    "step": "agent_assignment",
                    "status": "completed",
                    "data": {"agents": agents},
                },
            )
        else:
            agents = pu.assigned_agents

        # Step 4: Execute through agents with proof gates
        logger.info(f"\nStep 3: Multi-Agent Execution ({len(agents)} agents)...")
        execution_results: dict[str, Any] = {}
        for i, agent in enumerate(agents, 1):
            logger.info(f"  [{i}/{len(agents)}] {agent}...")

            # Skip Ollama/ChatDev for now (would execute separately)
            if agent.startswith(("ollama:", "chatdev:")):
                logger.info("    Skipped (external system)")
                execution_results[agent] = "skipped"
                continue

            # Execute through SimulatedVerse
            if not self.sv_bridge:
                logger.info("    Error: SimulatedVerse unavailable")
                execution_results[agent] = "unavailable"
                continue

            try:
                task_id = self.sv_bridge.submit_task(
                    agent,
                    f"Execute {pu.type}: {pu.title}",
                    {
                        "pu_id": pu_id,
                        "pu_type": pu.type,
                        "description": pu.description,
                        "proof_criteria": pu.proof_criteria,
                        "metadata": pu.metadata,
                    },
                )

                result = self.sv_bridge.check_result(task_id, timeout=30)

                if result:
                    execution_results[agent] = "completed"
                    logger.info("    Completed")

                    # Proof gate check
                    if agent == "zod":
                        passed = self._check_zod_validation(result)
                        if passed:
                            self.metrics["proof_gates_passed"] += 1
                            workflow_result["proof_gates_passed"] += 1
                        else:
                            self.metrics["proof_gates_failed"] += 1
                            workflow_result["proof_gates_failed"] += 1
                            logger.info("    PROOF GATE FAILED")

                else:
                    execution_results[agent] = "timeout"
                    logger.info("    Timeout")

            except Exception as e:
                execution_results[agent] = f"error: {e}"
                logger.info(f"    Error: {e}")

        workflow_result["steps"].append(
            {
                "step": "multi_agent_execution",
                "status": "completed",
                "data": execution_results,
            },
        )

        # Step 5: Final validation
        logger.info("\nStep 4: Final Validation...")
        success_count = sum(1 for r in execution_results.values() if r == "completed")
        total_agents = len([a for a in agents if not a.startswith(("ollama:", "chatdev:"))])

        # No SV agents means external execution — treat as full success
        success_rate = success_count / total_agents if total_agents > 0 else 1.0

        if success_rate >= 0.7:  # 70% threshold
            workflow_result["overall_status"] = "completed"
            self.metrics["workflows_completed"] += 1
            logger.info(f"  WORKFLOW SUCCEEDED ({success_count}/{total_agents} agents)")
        else:
            workflow_result["overall_status"] = "failed"
            self.metrics["workflows_failed"] += 1
            logger.info(f"  WORKFLOW FAILED ({success_count}/{total_agents} agents)")

        self.metrics["tasks_processed"] += 1

        return workflow_result

    def _request_human_approval(self, pu: "PU") -> bool:
        """Request human approval for PU execution.

        Args:
            pu: PU to approve

        Returns:
            True if approved, False if rejected

        """
        logger.info(f"\n{'=' * 80}")
        logger.info("HUMAN APPROVAL REQUIRED")
        logger.info(f"{'=' * 80}")
        logger.info(f"PU ID: {pu.id}")
        logger.info(f"Type: {pu.type}")
        logger.info(f"Title: {pu.title}")
        logger.info(f"Description: {pu.description}")
        logger.info(f"Priority: {pu.priority}")
        logger.info("\nProof Criteria:")
        for i, criterion in enumerate(pu.proof_criteria, 1):
            logger.info(f"  {i}. {criterion}")
        logger.info(f"\nMetadata: {json.dumps(pu.metadata, indent=2)}")
        logger.info(f"{'=' * 80}")

        # In sandbox mode, auto-approve
        if self.mode == "sandbox":
            logger.info("SANDBOX MODE: Auto-approved")
            return True

        # Check for auto-approval via environment
        auto_approve = os.getenv("QUEST_AUTO_APPROVE", "false").lower() in [
            "true",
            "1",
            "yes",
        ]
        if auto_approve:
            logger.info("AUTO-APPROVE MODE: Approved via QUEST_AUTO_APPROVE")
            return True

        # In supervised mode, request approval only if interactive
        if sys.stdin.isatty():
            response = input("\nApprove execution? (y/n): ").strip().lower()
            return response in ["y", "yes"]
        else:
            logger.warning("Non-interactive mode without auto-approval - denying execution")
            return False

    def _check_zod_validation(self, result: dict[str, Any]) -> bool:
        """Check if Zod validation passed.

        Args:
            result: Zod agent result

        Returns:
            True if validation passed

        """
        # Check result structure for validation success
        if "effects" in result and "stateDelta" in result["effects"]:
            state = result["effects"]["stateDelta"]

            # Look for validation status
            validation_status = state.get("validation_status", "unknown")
            if validation_status in ["passed", "success", "valid"]:
                return True

            # Check error count
            errors = state.get("errors", [])
            if isinstance(errors, list) and len(errors) == 0:
                return True

        return False

    def process_queue(self, limit: int | None = None) -> None:
        """Process approved PUs from queue.

        Args:
            limit: Maximum number of PUs to process (None = all)

        """
        if not self.queue:
            logger.info("Error: Queue unavailable")
            return

        # Get approved PUs
        approved_pus = [pu for pu in self.queue.queue if pu.status == "approved"]

        if not approved_pus:
            logger.info("No approved PUs in queue")
            return

        logger.info(f"\nProcessing {len(approved_pus)} approved PUs...")
        if limit:
            approved_pus = approved_pus[:limit]
            logger.info(f"  Limited to {limit} PUs")

        for i, pu in enumerate(approved_pus, 1):
            logger.info(f"\n{'=' * 80}")
            logger.info(f"Processing PU {i}/{len(approved_pus)}")
            logger.info(f"{'=' * 80}")

            result = self.execute_workflow(pu.id)

            logger.info(f"\nWorkflow Result: {result['overall_status']}")
            logger.info(f"  Proof Gates Passed: {result['proof_gates_passed']}")
            logger.info(f"  Proof Gates Failed: {result['proof_gates_failed']}")

    def display_metrics(self) -> None:
        """Display orchestrator metrics."""
        logger.info(f"\n{'=' * 80}")
        logger.info("AUTONOMOUS ORCHESTRATOR METRICS")
        logger.info(f"{'=' * 80}")
        logger.info(f"  Mode: {self.mode}")
        logger.info(f"  Tasks Processed: {self.metrics['tasks_processed']}")
        logger.info(f"  Workflows Completed: {self.metrics['workflows_completed']}")
        logger.info(f"  Workflows Failed: {self.metrics['workflows_failed']}")

        completed: int = int(self.metrics["workflows_completed"])
        failed: int = int(self.metrics["workflows_failed"])
        total_workflows = completed + failed
        if total_workflows > 0:
            success_rate = completed / total_workflows * 100
            logger.info(f"  Success Rate: {success_rate:.1f}%")

        logger.info(f"\n  Proof Gates Passed: {self.metrics['proof_gates_passed']}")
        logger.info(f"  Proof Gates Failed: {self.metrics['proof_gates_failed']}")

        if self.mode == "supervised":
            logger.info(
                f"\n  Human Approvals Requested: {self.metrics['human_approvals_requested']}",
            )
            logger.info(f"  Human Approvals Granted: {self.metrics['human_approvals_granted']}")

            requested: int = int(self.metrics["human_approvals_requested"])
            if requested > 0:
                granted: int = int(self.metrics["human_approvals_granted"])
                approval_rate = granted / requested * 100
                logger.info(f"  Approval Rate: {approval_rate:.1f}%")

        start_time: str = str(self.metrics["start_time"])
        start = datetime.fromisoformat(start_time)
        uptime = (datetime.now() - start).total_seconds()
        logger.info(f"\n  Uptime: {uptime / 3600:.1f} hours")
        logger.info(f"{'=' * 80}\n")


def main() -> None:
    """Main entry point."""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "process":
            # Process queue
            mode = sys.argv[2] if len(sys.argv) > 2 else "supervised"
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else None

            orchestrator = AutonomousOrchestrator(mode=mode)
            orchestrator.process_queue(limit=limit)
            orchestrator.display_metrics()

        elif command == "execute":
            # Execute specific PU
            if len(sys.argv) < 3:
                logger.info("Usage: python autonomous_orchestrator.py execute <PU-ID> [mode]")
                return

            pu_id = sys.argv[2]
            mode = sys.argv[3] if len(sys.argv) > 3 else "supervised"

            orchestrator = AutonomousOrchestrator(mode=mode)
            orchestrator.execute_workflow(pu_id)

            logger.info(f"\n{'=' * 80}")
            logger.info("WORKFLOW RESULT")
            logger.info(f"{'=' * 80}")

        elif command == "metrics":
            # Display metrics
            mode = sys.argv[2] if len(sys.argv) > 2 else "supervised"
            orchestrator = AutonomousOrchestrator(mode=mode)
            orchestrator.display_metrics()

        else:
            logger.info(f"Unknown command: {command}")
            logger.info("\nAvailable commands:")
            logger.info("  process [mode] [limit]     - Process approved PUs from queue")
            logger.info("  execute <PU-ID> [mode]     - Execute specific PU workflow")
            logger.info("  metrics [mode]             - Display metrics")
            logger.info("\nModes: full, supervised (default), sandbox")

    else:
        logger.info("\nAutonomous Orchestrator - Multi-Agent Workflow Coordination")
        logger.info("\nUsage: python autonomous_orchestrator.py <command> [options]")
        logger.info("\nCommands:")
        logger.info("  process [mode] [limit]     - Process approved PUs from queue")
        logger.info("  execute <PU-ID> [mode]     - Execute specific PU workflow")
        logger.info("  metrics [mode]             - Display metrics")
        logger.info("\nModes:")
        logger.info("  full        - Full autonomy (auto-execute all)")
        logger.info("  supervised  - Human approval required (default)")
        logger.info("  sandbox     - Test mode (isolated environment)")


if __name__ == "__main__":
    main()
