#!/usr/bin/env python3
"""AI Council Voting System - Multi-Agent Consensus & Decision Making.

Implements actual voting logic for the AI Council to enable:
- Multi-agent consensus on decisions
- Weighted voting based on agent expertise
- Confidence scoring and consensus validation
- Decision history and audit trails
- Real-time voting and deliberation

This is the missing link that transforms the AI Council from routing
infrastructure into an actual decision-making body.
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class VoteChoice(Enum):
    """Possible votes in the council."""

    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"
    NEEDS_MORE_INFO = "needs_more_info"


class ConsensusLevel(Enum):
    """Level of consensus achieved."""

    UNANIMOUS = "unanimous"
    STRONG = "strong"  # 80%+
    MODERATE = "moderate"  # 60-80%
    WEAK = "weak"  # 40-60%
    DEADLOCK = "deadlock"  # <40%


@dataclass
class AgentVote:
    """A single agent's vote on a decision."""

    agent_id: str
    agent_name: str
    vote: VoteChoice
    confidence: float  # 0-1, how confident in this vote
    expertise_level: float  # 0-1, agent's expertise in this domain
    reasoning: str  # Why the agent voted this way
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def weight(self) -> float:
        """Calculate weighted vote power based on expertise and confidence."""
        return self.expertise_level * self.confidence


@dataclass
class CouncilDecision:
    """A decision made by the AI Council."""

    decision_id: str
    topic: str
    description: str
    proposed_by: str
    votes: list[AgentVote] = field(default_factory=list)
    consensus_level: ConsensusLevel | None = None
    final_vote: VoteChoice | None = None
    execution_plan: str = ""
    status: str = "pending"  # pending, approved, rejected, executing, completed
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str | None = None
    artifacts: list[str] = field(default_factory=list)  # Results/outputs


class AICouncilVoting:
    """Manages voting and consensus for the AI Council."""

    def __init__(self, state_dir: Path | str = "state/council"):
        """Initialize the voting system.

        Args:
            state_dir: Directory to store council state and decisions
        """
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.decisions_file = self.state_dir / "decisions.jsonl"
        self.voting_history_file = self.state_dir / "voting_history.jsonl"

        # In-memory cache of current decisions
        self._decisions: dict[str, CouncilDecision] = {}
        self._load_decisions()

    def _load_decisions(self) -> None:
        """Load decisions from persistence."""
        if self.decisions_file.exists():
            try:
                for line in self.decisions_file.read_text().strip().split("\n"):
                    if line.strip():
                        data = json.loads(line)
                        self._decisions[data["decision_id"]] = self._deserialize_decision(data)
            except (json.JSONDecodeError, ValueError, OSError) as e:
                logger.error(f"Failed to load decisions: {e}")

    def _deserialize_decision(self, data: dict[str, Any]) -> CouncilDecision:
        """Deserialize a decision from JSON."""
        decision = CouncilDecision(
            decision_id=data["decision_id"],
            topic=data["topic"],
            description=data["description"],
            proposed_by=data["proposed_by"],
            execution_plan=data.get("execution_plan", ""),
            status=data.get("status", "pending"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            completed_at=data.get("completed_at"),
            artifacts=data.get("artifacts", []),
        )

        # Reconstruct votes
        for vote_data in data.get("votes", []):
            vote = AgentVote(
                agent_id=vote_data["agent_id"],
                agent_name=vote_data["agent_name"],
                vote=VoteChoice(vote_data["vote"]),
                confidence=vote_data["confidence"],
                expertise_level=vote_data["expertise_level"],
                reasoning=vote_data["reasoning"],
                timestamp=vote_data.get("timestamp", datetime.now().isoformat()),
            )
            decision.votes.append(vote)

        if data.get("consensus_level"):
            decision.consensus_level = ConsensusLevel(data["consensus_level"])

        if data.get("final_vote"):
            decision.final_vote = VoteChoice(data["final_vote"])

        return decision

    def create_decision(
        self, decision_id: str, topic: str, description: str, proposed_by: str
    ) -> CouncilDecision:
        """Create a new decision for the council to vote on.

        Args:
            decision_id: Unique identifier for this decision
            topic: Topic/category of decision
            description: Full description of what's being decided
            proposed_by: Agent or system that proposed this decision

        Returns:
            The created decision object
        """
        decision = CouncilDecision(
            decision_id=decision_id,
            topic=topic,
            description=description,
            proposed_by=proposed_by,
        )
        self._decisions[decision_id] = decision
        self._save_decision(decision)

        logger.info(f"📋 Council decision created: {decision_id} ({topic}) - awaiting votes")
        return decision

    def cast_vote(
        self,
        decision_id: str,
        agent_id: str,
        agent_name: str,
        vote: VoteChoice,
        confidence: float,
        expertise_level: float,
        reasoning: str,
    ) -> None:
        """Cast a vote on a decision.

        Args:
            decision_id: ID of the decision being voted on
            agent_id: ID of the agent voting
            agent_name: Name of the agent voting
            vote: The agent's vote choice
            confidence: How confident the agent is (0-1)
            expertise_level: Agent's expertise in this domain (0-1)
            reasoning: Explanation of the vote
        """
        if decision_id not in self._decisions:
            logger.error(f"Decision {decision_id} not found")
            return

        decision = self._decisions[decision_id]

        # Remove previous vote from this agent if exists
        decision.votes = [v for v in decision.votes if v.agent_id != agent_id]

        # Add new vote
        agent_vote = AgentVote(
            agent_id=agent_id,
            agent_name=agent_name,
            vote=vote,
            confidence=confidence,
            expertise_level=expertise_level,
            reasoning=reasoning,
        )
        decision.votes.append(agent_vote)

        logger.info(
            f"🗳️  {agent_name} voted {vote.value} on {decision_id} "
            f"(confidence: {confidence:.1%}, expertise: {expertise_level:.1%})"
        )

        # Log the vote
        vote_record = {
            "timestamp": datetime.now().isoformat(),
            "decision_id": decision_id,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "vote": vote.value,
            "confidence": confidence,
            "expertise_level": expertise_level,
        }
        with open(self.voting_history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(vote_record) + "\n")

        # Auto-evaluate if we have enough votes
        self._evaluate_consensus(decision_id)
        self._save_decision(decision)

    def _evaluate_consensus(self, decision_id: str) -> bool:
        """Evaluate if consensus has been reached on a decision.

        Returns:
            True if consensus reached, False otherwise
        """
        decision = self._decisions[decision_id]

        if not decision.votes or decision.status != "pending":
            return False

        # Calculate weighted votes
        approve_weight = sum(v.weight() for v in decision.votes if v.vote == VoteChoice.APPROVE)
        reject_weight = sum(v.weight() for v in decision.votes if v.vote == VoteChoice.REJECT)
        total_weight = approve_weight + reject_weight

        if total_weight == 0:
            return False

        approve_pct = approve_weight / total_weight if total_weight > 0 else 0

        # Determine consensus level and decision
        if approve_pct >= 0.99:
            decision.consensus_level = ConsensusLevel.UNANIMOUS
            decision.final_vote = VoteChoice.APPROVE
            decision.status = "approved"
            log_fn = logger.info
        elif approve_pct >= 0.80:
            decision.consensus_level = ConsensusLevel.STRONG
            decision.final_vote = VoteChoice.APPROVE
            decision.status = "approved"
            log_fn = logger.info
        elif approve_pct >= 0.60:
            decision.consensus_level = ConsensusLevel.MODERATE
            decision.final_vote = VoteChoice.APPROVE
            decision.status = "approved"
            log_fn = logger.info
        elif approve_pct >= 0.40:
            decision.consensus_level = ConsensusLevel.WEAK
            decision.final_vote = VoteChoice.ABSTAIN
            decision.status = "deadlock"
            log_fn = logger.warning
        else:
            decision.consensus_level = ConsensusLevel.DEADLOCK
            decision.final_vote = VoteChoice.REJECT
            decision.status = "rejected"
            log_fn = logger.warning

        log_fn(
            f"🏛️  Consensus on {decision_id}: {decision.consensus_level.value} "
            f"({approve_pct:.1%} approve) → {decision.final_vote.value}"
        )

        return decision.status in ("approved", "rejected")

    def get_decision(self, decision_id: str) -> CouncilDecision | None:
        """Get a decision by ID.

        Args:
            decision_id: ID of the decision

        Returns:
            The decision object or None if not found
        """
        return self._decisions.get(decision_id)

    def list_decisions(
        self, status: str | None = None, topic: str | None = None
    ) -> list[CouncilDecision]:
        """List decisions with optional filtering.

        Args:
            status: Filter by status (pending, approved, rejected, etc.)
            topic: Filter by topic

        Returns:
            List of matching decisions
        """
        decisions = list(self._decisions.values())

        if status:
            decisions = [d for d in decisions if d.status == status]

        if topic:
            decisions = [d for d in decisions if d.topic == topic]

        return decisions

    def approve_decision(self, decision_id: str, execution_plan: str = "") -> bool:
        """Mark a decision as approved and ready for execution.

        Args:
            decision_id: ID of the decision
            execution_plan: Plan for executing this decision

        Returns:
            True if approved, False otherwise
        """
        decision = self._decisions.get(decision_id)
        if not decision:
            return False

        decision.status = "approved"
        decision.execution_plan = execution_plan
        self._save_decision(decision)

        logger.info(f"✅ Decision {decision_id} approved for execution")
        return True

    def complete_decision(self, decision_id: str, artifacts: list[str] | None = None) -> bool:
        """Mark a decision as completed with optional artifacts.

        Args:
            decision_id: ID of the decision
            artifacts: List of artifact paths from execution

        Returns:
            True if completed, False otherwise
        """
        decision = self._decisions.get(decision_id)
        if not decision:
            return False

        decision.status = "completed"
        decision.completed_at = datetime.now().isoformat()
        if artifacts:
            decision.artifacts = artifacts

        self._save_decision(decision)

        logger.info(f"🎉 Decision {decision_id} completed with {len(decision.artifacts)} artifacts")
        return True

    def _save_decision(self, decision: CouncilDecision) -> None:
        """Save a decision to persistence."""
        try:
            # Read existing decisions
            decisions = []
            if self.decisions_file.exists():
                for line in self.decisions_file.read_text().strip().split("\n"):
                    if line.strip():
                        decisions.append(json.loads(line))

            # Remove old version of this decision
            decisions = [d for d in decisions if d["decision_id"] != decision.decision_id]

            # Add updated version
            decision_dict = asdict(decision)
            # Convert vote objects and their enum fields
            decision_dict["votes"] = [
                {
                    **asdict(v),
                    "vote": v.vote.value,  # Convert VoteChoice enum to string
                }
                for v in decision.votes
            ]
            decision_dict["consensus_level"] = (
                decision.consensus_level.value if decision.consensus_level else None
            )
            decision_dict["final_vote"] = decision.final_vote.value if decision.final_vote else None
            decisions.append(decision_dict)

            # Write back
            content = "\n".join(json.dumps(d) for d in decisions)
            self.decisions_file.write_text(content + "\n", encoding="utf-8")
        except (json.JSONDecodeError, ValueError, OSError) as e:
            logger.error(f"Failed to save decision: {e}")

    def get_council_status(self) -> dict[str, Any]:
        """Get overall status of the council.

        Returns:
            Dictionary with council metrics and statistics
        """
        decisions = list(self._decisions.values())

        return {
            "total_decisions": len(decisions),
            "pending": len([d for d in decisions if d.status == "pending"]),
            "approved": len([d for d in decisions if d.status == "approved"]),
            "rejected": len([d for d in decisions if d.status == "rejected"]),
            "completed": len([d for d in decisions if d.status == "completed"]),
            "active_votes": sum(len(d.votes) for d in decisions if d.status == "pending"),
            "timestamp": datetime.now().isoformat(),
        }

    def dispatch_to_background(
        self,
        decision_id: str,
        task_type: str = "code_analysis",
    ) -> dict[str, Any]:
        """Dispatch an approved decision to BackgroundTaskOrchestrator for execution.

        This bridges AI Council decisions to actual task execution via local LLMs.

        Args:
            decision_id: ID of the approved decision to execute
            task_type: Type of task (code_analysis, code_generation, etc.)

        Returns:
            Dict with task_id and status, or error info
        """
        decision = self._decisions.get(decision_id)
        if not decision:
            return {"success": False, "error": f"Decision {decision_id} not found"}

        if decision.status != "approved":
            return {
                "success": False,
                "error": f"Decision {decision_id} is not approved (status: {decision.status})",
            }

        try:
            from src.orchestration.background_task_orchestrator import (
                BackgroundTaskOrchestrator, TaskPriority, TaskTarget)

            # Build execution prompt from decision
            prompt = f"""Execute AI Council Decision: {decision.topic}

Description: {decision.description}

Execution Plan: {decision.execution_plan or "Implement as described"}

Consensus: {decision.consensus_level.value if decision.consensus_level else "N/A"}
Approved by: {len([v for v in decision.votes if v.vote == VoteChoice.APPROVE])} agents

Please execute this task and provide results."""

            orchestrator = BackgroundTaskOrchestrator()

            # Determine priority based on consensus level
            if (
                decision.consensus_level == ConsensusLevel.UNANIMOUS
                or decision.consensus_level == ConsensusLevel.STRONG
            ):
                priority = TaskPriority.HIGH
            else:
                priority = TaskPriority.NORMAL

            task = orchestrator.submit_task(
                prompt=prompt,
                target=TaskTarget.AUTO,
                priority=priority,
                requesting_agent="ai_council",
                task_type=task_type,
            )

            # Update decision status to executing
            decision.status = "executing"
            decision.execution_plan = f"Background task: {task.task_id}"
            self._save_decision(decision)

            logger.info(
                f"🚀 Council decision {decision_id} dispatched to background: {task.task_id}"
            )

            return {
                "success": True,
                "decision_id": decision_id,
                "task_id": task.task_id,
                "target": task.target.value,
                "model": task.model,
                "status": "executing",
            }

        except ImportError as e:
            logger.warning(f"BackgroundTaskOrchestrator not available: {e}")
            return {
                "success": False,
                "error": "BackgroundTaskOrchestrator not available",
            }
        except Exception as e:
            logger.exception(f"Failed to dispatch decision {decision_id}: {e}")
            return {"success": False, "error": str(e)}

    def check_execution_status(self, decision_id: str) -> dict[str, Any]:
        """Check the execution status of a council decision.

        Args:
            decision_id: ID of the decision to check

        Returns:
            Dict with execution status and results
        """
        decision = self._decisions.get(decision_id)
        if not decision:
            return {"success": False, "error": f"Decision {decision_id} not found"}

        if decision.status != "executing":
            return {
                "success": True,
                "decision_id": decision_id,
                "status": decision.status,
                "message": f"Decision is not currently executing (status: {decision.status})",
            }

        # Extract task_id from execution plan if available
        task_id = None
        if decision.execution_plan and "Background task:" in decision.execution_plan:
            task_id = decision.execution_plan.replace("Background task:", "").strip()

        if not task_id:
            return {
                "success": True,
                "decision_id": decision_id,
                "status": "executing",
                "message": "No task ID found in execution plan",
            }

        try:
            from src.orchestration.background_task_orchestrator import \
                BackgroundTaskOrchestrator

            orchestrator = BackgroundTaskOrchestrator()
            task = orchestrator.tasks.get(task_id)

            if not task:
                return {
                    "success": True,
                    "decision_id": decision_id,
                    "task_id": task_id,
                    "status": "unknown",
                    "message": "Task not found in orchestrator",
                }

            # If task completed, update decision
            if task.status.value == "completed":
                decision.status = "completed"
                decision.completed_at = datetime.now().isoformat()
                if task.result:
                    decision.artifacts.append(f"Result: {task.result[:500]}")
                self._save_decision(decision)

            return {
                "success": True,
                "decision_id": decision_id,
                "task_id": task_id,
                "task_status": task.status.value,
                "progress": task.progress,
                "result": task.result[:500] if task.result else None,
                "error": task.error,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
