# DEPRECATED (2026-03-24): Pre-consolidation stub. Use orchestration_bridges.py registry instead.
"""Service Bridge: Multi-Agent Consensus → AgentOrchestrationHub.

Coordinate consensus voting and multi-system coordination.
Enables collaborative decision-making across AI agents.
"""

from src.orchestration.agent_orchestration_hub import AgentOrchestrationHub


class MultiAgentConsensusBridge:
    """Bridge multi-agent consensus into hub."""

    def __init__(self, hub: AgentOrchestrationHub):
        """Initialize MultiAgentConsensusBridge with hub."""
        self.hub = hub

    async def consensus_route(
        self, task_type, content, systems=None, strategy="weighted", **kwargs
    ):
        """Route task with consensus voting across systems."""
        return await self.hub.orchestrate_multi_agent_task(
            content=content,
            task_type=task_type,
            systems=systems,
            voting_strategy=strategy,
            **kwargs,
        )

    async def simple_voting(self, task_type, content, systems=None, **kwargs):
        """Consensus via simple majority vote."""
        return await self.consensus_route(
            task_type, content, systems=systems, strategy="simple", **kwargs
        )

    async def weighted_voting(self, task_type, content, systems=None, **kwargs):
        """Consensus via weighted confidence scores."""
        return await self.consensus_route(
            task_type, content, systems=systems, strategy="weighted", **kwargs
        )

    async def ranked_voting(self, task_type, content, systems=None, **kwargs):
        """Consensus via ranked choice voting."""
        return await self.consensus_route(
            task_type, content, systems=systems, strategy="ranked", **kwargs
        )
