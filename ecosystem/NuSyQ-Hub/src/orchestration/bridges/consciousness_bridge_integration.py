# DEPRECATED (2026-03-24): Pre-consolidation stub. Use orchestration_bridges.py registry instead.
"""Service Bridge: Consciousness Bridge → AgentOrchestrationHub.

Integrate consciousness systems into routing and decision-making.
Provides semantic awareness for all task routing operations.
"""

from src.orchestration.agent_orchestration_hub import AgentOrchestrationHub


class ConsciousnessBridgeIntegration:
    """Bridge consciousness into hub decision-making."""

    def __init__(self, hub: AgentOrchestrationHub):
        """Initialize ConsciousnessBridgeIntegration with hub."""
        self.hub = hub

    async def route_with_consciousness(self, task_type, content, context=None, **kwargs):
        """Route task with full consciousness enrichment."""
        return await self.hub.route_task(
            content=content,
            task_type=task_type,
            context=context or {},
            consciousness_enrich=True,
            **kwargs,
        )

    async def enrich_decision(self, content, task_type, context):
        """Get consciousness enrichment for decision making."""
        return await self.hub._enrich_with_consciousness(content, context, task_type)

    def get_consciousness_status(self):
        """Check consciousness bridge health."""
        return {
            "enabled": self.hub.consciousness is not None,
            "available": self.hub.enable_consciousness,
        }
