# DEPRECATED (2026-03-24): Pre-consolidation stub. Use orchestration_bridges.py registry instead.
"""Service Bridge: AgentTaskRouter → AgentOrchestrationHub.

Redirect legacy AgentTaskRouter calls to new hub system.
Provides backward compatibility while enabling full consciousness integration.
"""

from src.orchestration.agent_orchestration_hub import AgentOrchestrationHub
from src.tools.agent_task_router import AgentTaskRouter


class AgentTaskRouterBridge:
    """Redirect bridge for legacy AgentTaskRouter → new AgentOrchestrationHub."""

    def __init__(self, hub: AgentOrchestrationHub):
        """Initialize AgentTaskRouterBridge with hub."""
        self.hub = hub
        self.legacy_router = AgentTaskRouter()

    async def route_task_legacy(self, task_type, content, **kwargs):
        """Legacy interface: route via new hub."""
        return await self.hub.route_task(content=content, task_type=task_type, **kwargs)
