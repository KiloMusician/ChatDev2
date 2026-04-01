"""NuSyQ-Hub Orchestration Bridges.

Unified bridge adapters for integrating external systems with AgentOrchestrationHub.

Sprint 3 consolidation: All bridges now in orchestration_bridges.py

Usage:
    from src.orchestration.bridges import BridgeRegistry, OllamaBridge

    # Via registry (recommended)
    registry = BridgeRegistry(hub)
    result = await registry.ollama.analyze_with_ollama(content)

    # Direct import (for typing/specialized use)
    from src.orchestration.bridges import ChatDevBridge
"""

# Consolidated bridge exports
from src.orchestration.bridges.orchestration_bridges import (
    AgentTaskRouterBridge, BridgeRegistry, ChatDevBridge, ConsciousnessBridge,
    ConsensusBridge, ContinueBridge, CopilotBridge, OllamaBridge,
    QuantumHealingBridge)

__all__ = [
    "AgentTaskRouterBridge",
    # Registry (primary API)
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
