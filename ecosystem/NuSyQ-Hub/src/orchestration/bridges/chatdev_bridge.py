# DEPRECATED (2026-03-24): Pre-consolidation stub. Use orchestration_bridges.py registry instead.
"""Service Bridge: ChatDev Orchestrator → AgentOrchestrationHub.

Redirect ChatDev development orchestration to new hub.
Unifies ChatDev project creation under consciousness-aware routing.
"""

from src.orchestration.agent_orchestration_hub import AgentOrchestrationHub


class ChatDevBridge:
    """Bridge for ChatDev integration into hub."""

    def __init__(self, hub: AgentOrchestrationHub):
        """Initialize ChatDevBridge with hub."""
        self.hub = hub

    async def generate_with_chatdev(self, task, project_name=None, model="gpt-3.5-turbo", **kwargs):
        """Generate code/projects via ChatDev through hub."""
        return await self.hub.route_to_chatdev(
            task=task, project_name=project_name, model=model, **kwargs
        )

    async def orchestrate_multi_agent_development(self, task, systems=None, **kwargs):
        """Multi-agent development via consensus."""
        return await self.hub.orchestrate_multi_agent_task(
            content=task, task_type="generate", systems=systems or ["chatdev"], **kwargs
        )
