# DEPRECATED (2026-03-24): Pre-consolidation stub. Use orchestration_bridges.py registry instead.
"""Service Bridge: Ollama Integration → AgentOrchestrationHub.

Local LLM routing and model selection through hub.
Integrates Ollama models into consciousness-aware routing.
"""

from src.orchestration.agent_orchestration_hub import AgentOrchestrationHub


class OllamaBridge:
    """Bridge Ollama local LLM into hub."""

    def __init__(self, hub: AgentOrchestrationHub):
        """Initialize OllamaBridge with hub."""
        self.hub = hub

    async def analyze_with_ollama(self, content, model=None, context=None, **kwargs):
        """Analyze content using Ollama local LLM through hub."""
        return await self.hub.route_task(
            content=content,
            task_type="analyze",
            target_system="ollama",
            context=context or {"model": model} if model else context,
            **kwargs,
        )

    async def code_analysis(self, code, **kwargs):
        """Specialized code analysis via Ollama."""
        return await self.analyze_with_ollama(code, context={"type": "code"}, **kwargs)

    async def semantic_search(self, query, **kwargs):
        """Semantic search using Ollama embeddings."""
        return await self.analyze_with_ollama(query, context={"type": "semantic"}, **kwargs)
