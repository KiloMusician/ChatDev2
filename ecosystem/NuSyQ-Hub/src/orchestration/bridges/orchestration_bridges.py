# NOTE: The ConsciousnessBridge class defined inline in this file is a
# DEPRECATED duplicate. Use src/integration/consciousness_bridge.py (Phase 1 canonical).
# All other bridge adapters in this registry are valid; only ConsciousnessBridge
# is scheduled for removal during Phase 3 cleanup.
"""Unified Orchestration Bridges - Consolidated service adapters.

Sprint 3 consolidation: Combines all bridge adapters into a single registry.

Previous individual files:
- agent_task_router_bridge.py
- chatdev_bridge.py
- consciousness_bridge_integration.py
- consensus_voting_bridge.py
- continue_bridge.py
- copilot_bridge.py
- ollama_bridge.py
- quantum_healing_bridge.py

Usage:
    from src.orchestration.bridges import BridgeRegistry

    registry = BridgeRegistry(hub)
    ollama = registry.get("ollama")
    result = await ollama.analyze_with_ollama(content)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from src.orchestration.agent_orchestration_hub import AgentOrchestrationHub

logger = logging.getLogger(__name__)


# =============================================================================
# BRIDGE IMPLEMENTATIONS
# =============================================================================


class OllamaBridge:
    """Bridge Ollama local LLM into hub."""

    def __init__(self, hub: AgentOrchestrationHub):
        """Initialize OllamaBridge with hub."""
        self.hub = hub

    async def analyze_with_ollama(
        self,
        content: str,
        model: str | None = None,
        context: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Analyze content using Ollama local LLM through hub."""
        ctx = context or {}
        if model:
            ctx["model"] = model
        return await self.hub.route_task(
            content=content,
            task_type="analyze",
            target_system="ollama",
            context=ctx,
            **kwargs,
        )

    async def code_analysis(self, code: str, **kwargs) -> dict[str, Any]:
        """Specialized code analysis via Ollama."""
        return await self.analyze_with_ollama(code, context={"type": "code"}, **kwargs)

    async def semantic_search(self, query: str, **kwargs) -> dict[str, Any]:
        """Semantic search using Ollama embeddings."""
        return await self.analyze_with_ollama(query, context={"type": "semantic"}, **kwargs)


class ChatDevBridge:
    """Bridge for ChatDev integration into hub."""

    def __init__(self, hub: AgentOrchestrationHub):
        """Initialize ChatDevBridge with hub."""
        self.hub = hub

    async def generate_with_chatdev(
        self,
        task: str,
        project_name: str | None = None,
        model: str = "gpt-3.5-turbo",
        **kwargs,
    ) -> dict[str, Any]:
        """Generate code/projects via ChatDev through hub."""
        return await self.hub.route_to_chatdev(
            task=task, project_name=project_name, model=model, **kwargs
        )

    async def orchestrate_multi_agent_development(
        self,
        task: str,
        systems: list | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Multi-agent development via consensus."""
        return await self.hub.orchestrate_multi_agent_task(
            content=task, task_type="generate", systems=systems or ["chatdev"], **kwargs
        )


class ConsciousnessBridge:
    """Bridge consciousness integration into hub."""

    def __init__(self, hub: AgentOrchestrationHub):
        """Initialize ConsciousnessBridge with hub."""
        self.hub = hub

    async def consciousness_aware_route(
        self,
        content: str,
        consciousness_level: int = 1,
        **kwargs,
    ) -> dict[str, Any]:
        """Route with consciousness-level awareness."""
        return await self.hub.route_task(
            content=content,
            task_type="consciousness",
            context={"consciousness_level": consciousness_level},
            **kwargs,
        )


class ConsensusBridge:
    """Bridge for consensus voting operations."""

    def __init__(self, hub: AgentOrchestrationHub):
        """Initialize ConsensusBridge with hub."""
        self.hub = hub

    async def request_consensus(
        self,
        proposal: str,
        voters: list | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Request consensus vote on a proposal."""
        return await self.hub.orchestrate_multi_agent_task(
            content=proposal,
            task_type="vote",
            systems=voters or ["ollama", "claude"],
            **kwargs,
        )


class ContinueBridge:
    """Bridge for Continue IDE integration."""

    def __init__(self, hub: AgentOrchestrationHub):
        """Initialize ContinueBridge with hub."""
        self.hub = hub

    async def continue_completion(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Get completion via Continue integration."""
        return await self.hub.route_task(
            content=prompt,
            task_type="complete",
            target_system="continue",
            context=context,
            **kwargs,
        )


class CopilotBridge:
    """Bridge for GitHub Copilot integration."""

    def __init__(self, hub: AgentOrchestrationHub):
        """Initialize CopilotBridge with hub."""
        self.hub = hub

    async def copilot_suggest(
        self,
        code_context: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Get code suggestions via Copilot."""
        return await self.hub.route_task(
            content=code_context,
            task_type="suggest",
            target_system="copilot",
            **kwargs,
        )


class AgentTaskRouterBridge:
    """Bridge for agent task routing."""

    def __init__(self, hub: AgentOrchestrationHub):
        """Initialize AgentTaskRouterBridge with hub."""
        self.hub = hub

    async def route_to_agent(
        self,
        task: str,
        agent_id: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Route task to specific agent."""
        return await self.hub.route_task(
            content=task,
            task_type="execute",
            target_system=agent_id,
            **kwargs,
        )


class QuantumHealingBridge:
    """Bridge for quantum-enhanced healing operations."""

    def __init__(self, hub: AgentOrchestrationHub):
        """Initialize QuantumHealingBridge with hub."""
        self.hub = hub

    async def quantum_heal(
        self,
        error_context: dict[str, Any],
        **kwargs,
    ) -> dict[str, Any]:
        """Apply quantum-enhanced healing to error."""
        return await self.hub.route_task(
            content=str(error_context),
            task_type="heal",
            target_system="quantum",
            context=error_context,
            **kwargs,
        )


# =============================================================================
# BRIDGE REGISTRY
# =============================================================================


class BridgeRegistry:
    """Unified registry for all orchestration bridges.

    Provides lazy instantiation and caching of bridge instances.
    """

    BRIDGE_CLASSES: ClassVar[dict] = {
        "ollama": OllamaBridge,
        "chatdev": ChatDevBridge,
        "consciousness": ConsciousnessBridge,
        "consensus": ConsensusBridge,
        "continue": ContinueBridge,
        "copilot": CopilotBridge,
        "agent_router": AgentTaskRouterBridge,
        "quantum_healing": QuantumHealingBridge,
    }

    def __init__(self, hub: AgentOrchestrationHub):
        """Initialize registry with hub reference."""
        self.hub = hub
        self._bridges: dict[str, Any] = {}

    def get(self, name: str) -> Any:
        """Get or create a bridge by name."""
        if name not in self._bridges:
            if name not in self.BRIDGE_CLASSES:
                raise KeyError(
                    f"Unknown bridge: {name}. Available: {list(self.BRIDGE_CLASSES.keys())}"
                )
            self._bridges[name] = self.BRIDGE_CLASSES[name](self.hub)
        return self._bridges[name]

    def list_bridges(self) -> list:
        """List available bridge names."""
        return list(self.BRIDGE_CLASSES.keys())

    @property
    def ollama(self) -> OllamaBridge:
        """Convenience accessor for Ollama bridge."""
        return self.get("ollama")

    @property
    def chatdev(self) -> ChatDevBridge:
        """Convenience accessor for ChatDev bridge."""
        return self.get("chatdev")

    @property
    def consciousness(self) -> ConsciousnessBridge:
        """Convenience accessor for consciousness bridge."""
        return self.get("consciousness")

    @property
    def consensus(self) -> ConsensusBridge:
        """Convenience accessor for consensus bridge."""
        return self.get("consensus")


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "AgentTaskRouterBridge",
    # Registry
    "BridgeRegistry",
    "ChatDevBridge",
    "ConsciousnessBridge",
    "ConsensusBridge",
    "ContinueBridge",
    "CopilotBridge",
    # Individual bridges
    "OllamaBridge",
    "QuantumHealingBridge",
]
