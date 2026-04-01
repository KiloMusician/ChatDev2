"""Advanced Consensus Voting System.

Implements weighted multi-agent consensus for improved accuracy.
Tracks agent performance profiles and adapts voting weights based on historical accuracy.

Features:
- Agent profiling (accuracy, latency, token efficiency)
- Weighted voting (not just majority)
- Confidence scoring
- Learning mechanism for adaptive weights
- Multiple consensus strategies (majority, weighted, ranked)

OmniTag: [consensus, voting, multi-agent, accuracy, learning, weighted aggregation]
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class VotingStrategy(Enum):
    """Consensus voting strategies."""

    MAJORITY = "majority"  # Simple majority vote (1 vote = 1 weight)
    WEIGHTED = "weighted"  # Weighted by agent accuracy
    RANKED_CHOICE = "ranked_choice"  # Weighted by ranking preference
    CONFIDENCE = "confidence"  # Select response with highest confidence


@dataclass
class AgentProfile:
    """Performance profile of an agent."""

    agent_name: str
    total_attempts: int = 0
    successful_votes: int = 0
    total_latency: float = 0.0
    total_tokens: int = 0
    specializations: dict[str, float] = field(default_factory=dict)

    # Calculated metrics
    accuracy: float = 0.0
    avg_latency: float = 0.0
    avg_tokens: int = 0
    reliability_score: float = 0.5  # 0.0-1.0, default neutral

    def update(self, success: bool, latency: float, tokens: int, task_type: str = "general"):
        """Update profile with new result."""
        self.total_attempts += 1
        if success:
            self.successful_votes += 1

        self.total_latency += latency
        self.total_tokens += tokens

        # Recalculate metrics
        self.accuracy = self.successful_votes / self.total_attempts
        self.avg_latency = self.total_latency / self.total_attempts
        self.avg_tokens = int(self.total_tokens / self.total_attempts)

        # Update specialization score for this task type
        if task_type not in self.specializations:
            self.specializations[task_type] = 0.0

        if success:
            self.specializations[task_type] = min(
                1.0,
                self.specializations[task_type] + 0.05,  # Increment by 5% per success
            )
        else:
            self.specializations[task_type] = max(
                0.0,
                self.specializations[task_type] - 0.02,  # Decrement by 2% per failure
            )

        # Calculate reliability: 70% accuracy + 20% consistency + 10% speed
        accuracy_component = self.accuracy * 0.7
        speed_component = (1.0 - min(self.avg_latency / 30.0, 1.0)) * 0.1  # Normalize to 30s
        consistency_component = (
            1.0 - (sum(self.specializations.values()) / max(len(self.specializations), 1) * 0.5)
        ) * 0.2

        self.reliability_score = accuracy_component + speed_component + consistency_component

    def get_weight(self) -> float:
        """Get voting weight based on reliability."""
        return max(0.1, self.reliability_score)  # Minimum 0.1 to allow any agent to contribute

    def get_specialization_boost(self, task_type: str) -> float:
        """Get boost factor for specific task type."""
        base_weight = self.get_weight()
        specialization = self.specializations.get(task_type, 0.0)
        return base_weight * (0.5 + specialization)  # Weight between 0.5x and 1.5x of base

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "agent_name": self.agent_name,
            "total_attempts": self.total_attempts,
            "accuracy": round(self.accuracy, 3),
            "avg_latency": round(self.avg_latency, 2),
            "avg_tokens": self.avg_tokens,
            "reliability_score": round(self.reliability_score, 3),
            "specializations": {k: round(v, 2) for k, v in self.specializations.items()},
        }


@dataclass
class ConsensusResponse:
    """Result of consensus voting."""

    selected_response: str
    strategy_used: VotingStrategy
    confidence: float
    agent_votes: dict[str, float]  # agent_name -> weight
    response_scores: dict[str, float]  # response_text -> score
    reasoning: str


class AdvancedConsensusVoter:
    """Weighted multi-agent consensus voting system."""

    def __init__(self, learning_enabled: bool = True):
        """Initialize AdvancedConsensusVoter with learning_enabled."""
        self.agent_profiles: dict[str, AgentProfile] = {}
        self.learning_enabled = learning_enabled
        self.voting_history: list[dict[str, Any]] = []

    def register_agent(self, agent_name: str) -> AgentProfile:
        """Register an agent in the system."""
        if agent_name not in self.agent_profiles:
            self.agent_profiles[agent_name] = AgentProfile(agent_name=agent_name)
        return self.agent_profiles[agent_name]

    def get_agent_profile(self, agent_name: str) -> AgentProfile | None:
        """Get profiling info for an agent."""
        return self.agent_profiles.get(agent_name)

    def record_agent_result(
        self,
        agent_name: str,
        success: bool,
        latency: float,
        tokens: int,
        task_type: str = "general",
    ):
        """Record result of an agent's work for learning."""
        if self.learning_enabled:
            profile = self.register_agent(agent_name)
            profile.update(success, latency, tokens, task_type)
            logger.info(
                f"Updated {agent_name}: accuracy={profile.accuracy:.2%}, reliability={profile.reliability_score:.2f}"
            )

    def vote(
        self,
        responses: dict[str, str],  # agent_name -> response_text
        task_type: str = "general",
        strategy: VotingStrategy = VotingStrategy.WEIGHTED,
        weights: dict[str, float] | None = None,
    ) -> ConsensusResponse:
        """Perform weighted consensus voting on agent responses.

        Args:
            responses: Dict mapping agent names to their responses
            task_type: Type of task (for specialization scoring)
            strategy: Voting strategy to use
            weights: Optional custom weights (overrides learned weights)

        Returns:
            ConsensusResponse with selected response and metadata
        """
        if not responses:
            raise ValueError("No responses provided for voting")

        if strategy == VotingStrategy.MAJORITY:
            return self._vote_majority(responses, task_type)

        elif strategy == VotingStrategy.WEIGHTED:
            return self._vote_weighted(responses, task_type, weights)

        elif strategy == VotingStrategy.RANKED_CHOICE:
            return self._vote_ranked_choice(responses, task_type)

        elif strategy == VotingStrategy.CONFIDENCE:
            return self._vote_confidence(responses, task_type)

        else:
            # Fallback to weighted
            return self._vote_weighted(responses, task_type, weights)

    def _vote_majority(self, responses: dict[str, str], task_type: str) -> ConsensusResponse:
        """Simple majority voting (one agent = one vote)."""
        del task_type
        response_votes: dict[str, int] = {}
        agent_votes: dict[str, float] = {}

        for agent, response in responses.items():
            agent_votes[agent] = 1.0
            response_votes[response] = response_votes.get(response, 0) + 1

        # Find response with most votes
        selected = max(response_votes.items(), key=lambda x: x[1])
        confidence = selected[1] / len(responses)

        return ConsensusResponse(
            selected_response=selected[0],
            strategy_used=VotingStrategy.MAJORITY,
            confidence=confidence,
            agent_votes=agent_votes,
            response_scores={r: float(c) for r, c in response_votes.items()},
            reasoning=f"Majority vote: {selected[1]}/{len(responses)} agents selected this response",
        )

    def _vote_weighted(
        self, responses: dict[str, str], task_type: str, weights: dict[str, float] | None = None
    ) -> ConsensusResponse:
        """Weighted voting based on agent reliability scores."""
        response_scores: dict[str, float] = {}
        agent_votes: dict[str, float] = {}
        total_weight = 0.0

        for agent, response in responses.items():
            # Get weight for this agent
            if weights and agent in weights:
                weight = weights[agent]
            else:
                profile = self.get_agent_profile(agent) or self.register_agent(agent)
                weight = profile.get_specialization_boost(task_type)

            agent_votes[agent] = weight
            total_weight += weight

            # Add weighted vote to this response
            response_scores[response] = response_scores.get(response, 0.0) + weight

        # Normalize scores
        response_scores = {r: s / total_weight for r, s in response_scores.items()}

        # Select response with highest score
        selected = max(response_scores.items(), key=lambda x: x[1])

        return ConsensusResponse(
            selected_response=selected[0],
            strategy_used=VotingStrategy.WEIGHTED,
            confidence=selected[1],
            agent_votes=agent_votes,
            response_scores=response_scores,
            reasoning=f"Weighted vote: selected response with {selected[1]:.1%} confidence",
        )

    def _vote_ranked_choice(self, responses: dict[str, str], task_type: str) -> ConsensusResponse:
        """Ranked choice voting for better consensus."""
        # For simplicity, use weighted voting with rankings
        # In production, would implement full ranked-choice logic
        return self._vote_weighted(responses, task_type)

    def _vote_confidence(self, responses: dict[str, str], task_type: str) -> ConsensusResponse:
        """Select response from agent with highest confidence (best profile)."""
        best_agent = None
        best_confidence = 0.0
        agent_votes: dict[str, float] = {}

        for agent, _response in responses.items():
            profile = self.get_agent_profile(agent) or self.register_agent(agent)
            confidence = profile.get_specialization_boost(task_type)
            agent_votes[agent] = confidence

            if confidence > best_confidence:
                best_confidence = confidence
                best_agent = agent

        selected_response = responses[best_agent] if best_agent else next(iter(responses.values()))

        return ConsensusResponse(
            selected_response=selected_response,
            strategy_used=VotingStrategy.CONFIDENCE,
            confidence=best_confidence,
            agent_votes=agent_votes,
            response_scores={responses[agent]: agent_votes[agent] for agent in responses},
            reasoning=f"High-confidence selection: {best_agent} (confidence={best_confidence:.1%})",
        )

    def get_agent_rankings(self, task_type: str | None = None) -> list[tuple[str, float]]:
        """Get ranked list of agents by reliability/specialization."""
        rankings = []

        for agent_name, profile in self.agent_profiles.items():
            score = (
                profile.get_specialization_boost(task_type) if task_type else profile.get_weight()
            )

            rankings.append((agent_name, score))

        return sorted(rankings, key=lambda x: x[1], reverse=True)

    def generate_report(self) -> str:
        """Generate human-readable report of agent profiles and voting."""
        report = ["🤖 ADVANCED CONSENSUS VOTING REPORT\n"]

        # Agent rankings
        rankings = self.get_agent_rankings()
        report.append("[AGENT RANKINGS BY RELIABILITY]")
        for i, (agent, score) in enumerate(rankings, 1):
            profile = self.agent_profiles[agent]
            report.append(
                f"  {i}. {agent:<25} | Accuracy: {profile.accuracy:.1%} | Reliability: {score:.2f}"
            )

        # Voting history
        if self.voting_history:
            report.append("\n[RECENT VOTING HISTORY]")
            report.append(f"  Total votes: {len(self.voting_history)}")

            # Strategy distribution
            strategies = {}
            for vote in self.voting_history:
                strategy = vote.get("strategy", "unknown")
                strategies[strategy] = strategies.get(strategy, 0) + 1

            report.append("\n  Distribution by strategy:")
            for strategy, count in strategies.items():
                report.append(f"    - {strategy}: {count}")

        report.append("\n[SYSTEM STATS]")
        report.append(f"  Registered agents: {len(self.agent_profiles)}")
        report.append(f"  Learning enabled: {self.learning_enabled}")

        return "\n".join(report)


def demo_advanced_voting():
    """Demonstrate advanced consensus voting."""
    logger.info("🤖 ADVANCED CONSENSUS VOTING DEMO\n")

    voter = AdvancedConsensusVoter(learning_enabled=True)

    # Simulate agent performance history
    logger.info("[1] BUILDING AGENT PROFILES")

    # Agent 1: Strong general performer
    voter.record_agent_result("qwen2.5-coder:7b", True, 10.0, 250, "code_review")
    voter.record_agent_result("qwen2.5-coder:7b", True, 11.0, 240, "code_review")
    voter.record_agent_result("qwen2.5-coder:7b", False, 8.5, 200, "code_generation")

    # Agent 2: Good at code review, weak at generation
    voter.record_agent_result("starcoder2:15b", True, 12.0, 300, "code_review")
    voter.record_agent_result("starcoder2:15b", True, 13.0, 310, "code_review")
    voter.record_agent_result("starcoder2:15b", False, 15.0, 400, "code_generation")

    # Agent 3: Good at generation
    voter.record_agent_result("deepseek-coder-v2:16b", False, 20.0, 600, "code_review")
    voter.record_agent_result("deepseek-coder-v2:16b", True, 18.0, 550, "code_generation")
    voter.record_agent_result("deepseek-coder-v2:16b", True, 19.0, 580, "code_generation")

    logger.info("Build profiles - Done\n")

    # Show rankings
    logger.info("[2] AGENT RANKINGS")
    rankings = voter.get_agent_rankings(task_type="code_review")
    for agent, score in rankings:
        logger.info(f"  {agent:<30} | Specialization score: {score:.2f}")

    # Perform voting scenarios
    logger.info("\n[3] CONSENSUS VOTING SCENARIOS")

    # Scenario 1: Code review task
    logger.info("\nScenario 1: Code Review Task")
    responses = {
        "qwen2.5-coder:7b": "This code looks good, consider adding error handling.",
        "starcoder2:15b": "This code looks good, consider adding error handling.",
        "deepseek-coder-v2:16b": "Security issue: missing input validation.",
    }

    result_weighted = voter.vote(
        responses, task_type="code_review", strategy=VotingStrategy.WEIGHTED
    )
    logger.info("  Weighted voting:")
    logger.info(f"    Selected: {result_weighted.selected_response[:50]}...")
    logger.info(f"    Confidence: {result_weighted.confidence:.1%}")
    logger.info(f"    Agent votes: {result_weighted.agent_votes}")

    # Scenario 2: Code generation task
    logger.info("\nScenario 2: Code Generation Task")
    responses_gen = {
        "qwen2.5-coder:7b": "def hello(): pass",
        "starcoder2:15b": "def hello(): print('hello')",
        "deepseek-coder-v2:16b": "def hello():\n    print('Hello, World!')\n    return None",
    }

    result_gen = voter.vote(
        responses_gen, task_type="code_generation", strategy=VotingStrategy.WEIGHTED
    )
    logger.info("  Weighted voting for code generation:")
    logger.info(f"    Selected: {result_gen.selected_response[:50]}...")
    logger.info(f"    Confidence: {result_gen.confidence:.1%}")

    # Show final report
    logger.info("\n[4] FINAL REPORT")
    logger.info(voter.generate_report())


if __name__ == "__main__":
    demo_advanced_voting()
