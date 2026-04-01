"""Advanced Consensus Integration.

Integrates weighted voting and agent profiling into the UnifiedAIOrchestrator.
Enables multi-agent consensus with learned weights and confidence scoring.

OmniTag: [orchestration, consensus, integration, profiling, weighted voting]
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from advanced_consensus_voter import (AdvancedConsensusVoter,
                                      ConsensusResponse, VotingStrategy)

logger = logging.getLogger(__name__)

# Profile storage
PROFILES_FILE = Path("state/profiles/agent_profiles.json")


class ConsensusIntegrator:
    """Integrates advanced consensus voting into orchestration."""

    def __init__(self):
        """Initialize ConsensusIntegrator."""
        self.voter = AdvancedConsensusVoter(learning_enabled=True)
        self.profiles_file = PROFILES_FILE
        self.load_profiles()

    def load_profiles(self):
        """Load persisted agent profiles."""
        if self.profiles_file.exists():
            try:
                with open(self.profiles_file) as f:
                    data = json.load(f)

                for agent_data in data.get("agents", []):
                    agent_name = agent_data["agent_name"]
                    profile = self.voter.register_agent(agent_name)

                    # Restore from saved data
                    profile.total_attempts = agent_data.get("total_attempts", 0)
                    profile.successful_votes = agent_data.get("successful_votes", 0)
                    profile.total_latency = agent_data.get("total_latency", 0.0)
                    profile.total_tokens = agent_data.get("total_tokens", 0)
                    profile.specializations = agent_data.get("specializations", {})

                    # Recalculate metrics
                    if profile.total_attempts > 0:
                        profile.accuracy = profile.successful_votes / profile.total_attempts
                        profile.avg_latency = profile.total_latency / profile.total_attempts
                        profile.avg_tokens = int(profile.total_tokens / profile.total_attempts)

                logger.info(f"Loaded profiles for {len(self.voter.agent_profiles)} agents")

            except Exception as e:
                logger.error(f"Failed to load profiles: {e}")

    def save_profiles(self):
        """Save agent profiles for persistence."""
        try:
            self.profiles_file.parent.mkdir(parents=True, exist_ok=True)

            profiles_data = {
                "timestamp": datetime.now().isoformat(),
                "agents": [profile.to_dict() for profile in self.voter.agent_profiles.values()],
            }

            with open(self.profiles_file, "w") as f:
                json.dump(profiles_data, f, indent=2)

            logger.info(f"Saved profiles for {len(self.voter.agent_profiles)} agents")

        except Exception as e:
            logger.error(f"Failed to save profiles: {e}")

    async def run_consensus_task(
        self,
        task_description: str,
        agents: list[str],
        task_type: str = "general",
        voting_strategy: VotingStrategy = VotingStrategy.WEIGHTED,
        timeout: float = 30.0,
    ) -> ConsensusResponse:
        """Run a task on multiple agents and perform consensus voting.

        Args:
            task_description: What to do
            agents: List of agent names to query
            task_type: Type of task (for specialization scoring)
            voting_strategy: How to aggregate responses
            timeout: Max time to wait for all responses

        Returns:
            ConsensusResponse with selected answer and metadata
        """
        # NOTE: This is a stub - in production, would call actual orchestrator
        # For now, simulates responses

        logger.info(f"Running consensus task: {task_description}")
        logger.info(f"Agents: {agents}, Strategy: {voting_strategy.value}")

        # Simulate getting responses from agents
        responses = await self._get_agent_responses(task_description, agents, timeout)

        # Perform weighted consensus vote
        result = self.voter.vote(responses, task_type=task_type, strategy=voting_strategy)

        logger.info(
            f"Consensus result: confidence={result.confidence:.1%}, reasoning={result.reasoning}"
        )

        # Save profiles (learning)
        self.save_profiles()

        return result

    async def _get_agent_responses(
        self, task: str, agents: list[str], timeout: float
    ) -> dict[str, str]:
        """Query multiple agents in parallel and collect responses.

        NOTE: Stub implementation. In production, would call actual orchestrator.
        """
        del timeout
        responses = {}

        # Simulate responses (would be real in production)
        for agent in agents:
            # In reality: await orchestrator.query_agent(agent, task)
            # For now: return mock response
            responses[agent] = f"Response from {agent}: {task[:30]}..."

        return responses

    def record_validation(
        self, agent: str, task_type: str, success: bool, latency: float, tokens: int
    ):
        """Record agent performance for learning."""
        self.voter.record_agent_result(agent, success, latency, tokens, task_type)
        self.save_profiles()

    def get_agent_metrics(self, agent: str | None = None) -> dict[str, Any]:
        """Get detailed metrics for agent(s)."""
        if agent:
            profile = self.voter.get_agent_profile(agent)
            if profile:
                return profile.to_dict()
            return None

        return {
            agent_name: profile.to_dict()
            for agent_name, profile in self.voter.agent_profiles.items()
        }

    def get_recommendations(self, task_type: str) -> list[str]:
        """Get recommended agents for a specific task type.

        Based on specialization profiles.
        """
        rankings = self.voter.get_agent_rankings(task_type=task_type)
        return [agent for agent, _ in rankings[:3]]  # Top 3


# Integration test
async def test_consensus_integration():
    """Test integration of consensus voting."""
    logger.info("🤖 CONSENSUS INTEGRATION TEST\n")

    integrator = ConsensusIntegrator()

    # Scenario 1: Code review consensus
    logger.info("[1] Running code review consensus task...")
    result = integrator.voter.vote(
        {
            "agent1": "Code quality is good, add logging",
            "agent2": "Code quality is good, add logging",
            "agent3": "Security issue: missing validation",
        },
        task_type="code_review",
        strategy=VotingStrategy.WEIGHTED,
    )

    logger.info(f"Selected: {result.selected_response}")
    logger.info(f"Confidence: {result.confidence:.1%}\n")

    # Record agent results for learning
    logger.info("[2] Recording agent performance...")
    integrator.record_validation("agent1", "code_review", True, 10.0, 200)
    integrator.record_validation("agent2", "code_review", True, 12.0, 210)
    integrator.record_validation("agent3", "code_review", False, 15.0, 300)
    logger.info("Profiles updated\n")

    # Get recommendations
    logger.info("[3] Getting recommendations for code_review tasks...")
    recommendations = integrator.get_recommendations("code_review")
    logger.info(f"Recommended agents: {recommendations}\n")

    # Show metrics
    logger.info("[4] Agent metrics:")
    metrics = integrator.get_agent_metrics()
    for agent_name, agent_metrics in metrics.items():
        logger.info(
            f"  {agent_name}: accuracy={agent_metrics['accuracy']:.1%}, "
            f"reliability={agent_metrics['reliability_score']:.2f}"
        )


if __name__ == "__main__":
    asyncio.run(test_consensus_integration())
