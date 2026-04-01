#!/usr/bin/env python3
"""Integration Module - AI Council + Task Queue + Feedback Loop.

This module ties the three Phase 1 systems together:
1. AI Council Voting - Makes decisions with consensus
2. Agent Task Queue - Manages work assignments
3. Feedback Loop Engine - Converts errors to decisions to tasks to execution

Together they form a complete feedback loop: Error → Decision → Task → Assignment → Execution
"""

from __future__ import annotations

import json
import logging
import time as time_module
from datetime import datetime
from pathlib import Path
from typing import Any

from src.orchestration.agent_task_queue import AgentTaskQueue
from src.orchestration.ai_council_voting import (AICouncilVoting,
                                                 ConsensusLevel, VoteChoice)
from src.orchestration.feedback_loop_engine import (ErrorReport,
                                                    FeedbackLoopEngine)

logger = logging.getLogger(__name__)


class IntegratedMultiAgentSystem:
    """Integrates voting, task queue, and feedback loop into unified orchestration."""

    def __init__(
        self,
        council: AICouncilVoting | None = None,
        task_queue: AgentTaskQueue | None = None,
        feedback_loop: FeedbackLoopEngine | None = None,
        system_dir: Path | str = "state/multi_agent_system",
    ):
        """Initialize integrated system.

        Args:
            council: AI Council voting system
            task_queue: Agent task queue
            feedback_loop: Feedback loop engine
            system_dir: Directory for system state
        """
        self.system_dir = Path(system_dir)
        self.system_dir.mkdir(parents=True, exist_ok=True)

        self.council = council or AICouncilVoting()
        self.task_queue = task_queue or AgentTaskQueue()
        self.feedback_loop = feedback_loop or FeedbackLoopEngine(task_queue=self.task_queue)

        # Register default agents with capabilities
        self._register_default_agents()

        logger.info("🤝 Integrated Multi-Agent System initialized")

    def _register_default_agents(self) -> None:
        """Register default agents with capabilities."""
        agents = [
            {
                "id": "copilot",
                "name": "GitHub Copilot",
                "capabilities": ["code_fix", "refactor", "test", "lint", "analysis"],
                "max_concurrent_tasks": 3,
            },
            {
                "id": "claude",
                "name": "Claude (Anthropic)",
                "capabilities": ["analysis", "architecture", "review", "documentation", "code_fix"],
                "max_concurrent_tasks": 2,
            },
            {
                "id": "chatdev",
                "name": "ChatDev",
                "capabilities": ["test", "integration", "optimization", "code_fix"],
                "max_concurrent_tasks": 1,
            },
            {
                "id": "ollama",
                "name": "Ollama Local LLM",
                "capabilities": ["analysis", "documentation"],
                "max_concurrent_tasks": 5,
            },
        ]

        for agent in agents:
            agent_dict: dict[str, Any] = agent
            self.task_queue.register_agent(
                agent_id=agent_dict["id"],
                agent_name=agent_dict["name"],
                capabilities=agent_dict["capabilities"],
                max_concurrent_tasks=agent_dict["max_concurrent_tasks"],
            )
            logger.debug(f"📌 Registered agent: {agent_dict['name']}")

    def process_errors_with_voting(
        self,
        error_report_path: Path | str | None = None,
    ) -> dict[str, Any]:
        """Process errors with council voting before task assignment.

        Full workflow:
        1. Ingest errors from report
        2. Group errors into decision topics
        3. Create council decisions for each group
        4. Agents vote on approach
        5. If approved, create tasks and assign to agents

        Args:
            error_report_path: Path to error report file
            require_council_approval: If True, wait for council approval before creating tasks

        Returns:
            Status dictionary with results
        """
        logger.info("🚀 Starting error processing with council voting")

        # Step 1: Ingest errors
        if error_report_path:
            error_count = self.feedback_loop.ingest_errors_from_report(error_report_path)
        else:
            error_count = len(self.feedback_loop._error_queue)
        if error_count == 0:
            logger.warning("No errors to process")
            return {"success": True, "status": "no_errors", "error_count": 0}

        # Step 2: Create decision topics from error groups
        error_groups = self._group_errors_by_type()
        decisions_created = 0

        for group_key, errors in error_groups.items():
            # Create council decision
            topic = f"Fix {group_key}"
            description = f"Address {len(errors)} {group_key} error(s):\n" + "\n".join(
                f"  - {e.file_path}:{e.line_number}" for e in errors
            )

            # Generate decision ID
            decision_id = f"decision_{group_key.replace(' ', '_')}_{int(time_module.time())}"

            decision = self.council.create_decision(
                decision_id=decision_id,
                topic=topic,
                description=description,
                proposed_by="FeedbackLoopEngine",
            )
            decisions_created += 1

            logger.info(f"📋 Created decision: {topic} (ID: {decision.decision_id})")

            # Step 3: Simulate council voting
            # In production, agents would actually vote; for now, auto-approve for testing
            self._simulate_council_voting(decision)

            # Step 4: If approved, process errors
            if decision.status == "approved":
                processed = self.feedback_loop.process_error_queue(max_errors=len(errors))
                logger.info(f"✅ Decision approved. Processed {processed} errors")
            else:
                logger.warning(f"❌ Decision not approved. Status: {decision.status}")

        return {
            "success": True,
            "status": "complete",
            "errors_ingested": error_count,
            "decisions_created": decisions_created,
            "tasks_assigned": len(
                [loop for loop in self.feedback_loop._loops.values() if loop.agent_id]
            ),
            "timestamp": datetime.now().isoformat(),
        }

    def _group_errors_by_type(self) -> dict[str, list[ErrorReport]]:
        """Group errors by type for decision creation.

        Args:
            None

        Returns:
            Dictionary mapping error type to list of errors
        """
        groups: dict[str, list[ErrorReport]] = {}
        for error in self.feedback_loop._error_queue:
            if error.error_type not in groups:
                groups[error.error_type] = []
            groups[error.error_type].append(error)
        return groups

    def _simulate_council_voting(self, decision: Any) -> None:
        """Simulate council voting for testing purposes.

        Args:
            decision: Decision to vote on
        """
        # Get registered agents and have them vote
        agents = list(self.task_queue._agent_registry.values())

        if not agents:
            logger.warning("No agents registered for voting")
            return

        for agent in agents:
            # Simulate voting based on agent capabilities vs task requirements
            confidence = 0.8
            vote = VoteChoice.APPROVE
            expertise = 0.7

            self.council.cast_vote(
                decision_id=decision.decision_id,
                agent_id=agent["id"],
                agent_name=agent["name"],
                vote=vote,
                confidence=confidence,
                expertise_level=expertise,
                reasoning=f"{agent['name']} votes to proceed with fix.",
            )

        logger.info(f"🗳️  Council voting completed for decision {decision.decision_id}")

    def get_system_status(self) -> dict[str, Any]:
        """Get comprehensive system status.

        Returns:
            Status dictionary with all component statuses
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "council": {
                "total_decisions": len(self.council.list_decisions()),
                "approved": len(
                    [d for d in self.council.list_decisions() if d.status == "approved"]
                ),
                "pending": len([d for d in self.council.list_decisions() if d.status == "pending"]),
                "deadlocked": len(
                    [
                        d
                        for d in self.council.list_decisions()
                        if d.consensus_level == ConsensusLevel.DEADLOCK
                    ]
                ),
            },
            "task_queue": self.task_queue.get_queue_status(),
            "feedback_loop": self.feedback_loop.get_engine_status(),
            "agents": {
                agent_id: {
                    "name": agent["name"],
                    "current_load": agent["current_load"],
                    "max_concurrent": agent["max_concurrent_tasks"],
                    "completed": agent.get("completed_tasks", 0),
                }
                for agent_id, agent in self.task_queue._agent_registry.items()
            },
        }

    def demonstrate_workflow(self) -> None:
        """Demonstrate the complete workflow with sample data.

        Creates sample errors, routes through council, assigns to agents.
        """
        logger.info("🎬 Starting workflow demonstration")

        # Create sample errors
        sample_errors = [
            ErrorReport(
                error_id="mypy_001",
                error_type="mypy",
                file_path="src/orchestration/unified_ai_orchestrator.py",
                line_number=42,
                message='error: Incompatible types in assignment (expression has type "str", variable has type "int")',
                severity="high",
                source_system="mypy",
            ),
            ErrorReport(
                error_id="mypy_002",
                error_type="mypy",
                file_path="src/guild/guild_board.py",
                line_number=156,
                message='error: Need type annotation for "x"',
                severity="medium",
                source_system="mypy",
            ),
            ErrorReport(
                error_id="ruff_001",
                error_type="ruff",
                file_path="src/orchestration/multi_ai_orchestrator.py",
                line_number=89,
                message="F401: Module imported but unused",
                severity="low",
                source_system="ruff",
            ),
        ]

        for error in sample_errors:
            self.feedback_loop.ingest_error(error)

        logger.info(f"📥 Ingested {len(sample_errors)} sample errors")

        # Process with voting
        result = self.process_errors_with_voting(
            error_report_path=None,  # Using ingested errors
        )

        logger.info(f"✨ Workflow demonstration complete: {result}")

        # Show final status
        status = self.get_system_status()
        logger.info(f"📊 Final system status:\n{json.dumps(status, indent=2)}")
