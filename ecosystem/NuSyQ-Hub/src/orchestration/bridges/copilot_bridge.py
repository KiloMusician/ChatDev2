"""Service Bridge: GitHub Copilot Integration → AgentOrchestrationHub.

Copilot routing and code generation through hub.
Integrates GitHub Copilot into universal routing system.
"""

from src.orchestration.agent_orchestration_hub import AgentOrchestrationHub


class CopilotBridge:
    """Bridge GitHub Copilot into hub."""

    def __init__(self, hub: AgentOrchestrationHub):
        """Initialize CopilotBridge with hub."""
        self.hub = hub

    async def generate_with_copilot(self, description, context=None, **kwargs):
        """Generate code/content via GitHub Copilot through hub."""
        return await self.hub.route_task(
            content=description,
            task_type="generate",
            target_system="copilot",
            context=context or {},
            **kwargs,
        )

    async def code_review_with_copilot(self, code, **kwargs):
        """Code review via Copilot."""
        return await self.hub.route_task(
            content=code,
            task_type="review",
            target_system="copilot",
            context={"type": "code_review"},
            **kwargs,
        )

    async def documentation_with_copilot(self, content, **kwargs):
        """Generate documentation via Copilot."""
        return await self.hub.route_task(
            content=content, task_type="document", target_system="copilot", **kwargs
        )
