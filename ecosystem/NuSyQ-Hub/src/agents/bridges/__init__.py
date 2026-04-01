"""Agent Service Bridges - Unified Access to AI Services.

This package provides bridge modules for backward compatibility and simplified
access to various AI services through the AgentOrchestrationHub.

All bridges delegate to the central hub while maintaining familiar interfaces.
"""

from src.agents.bridges.agent_registry_bridge import AgentRegistryBridge
from src.agents.bridges.agent_task_router_bridge import AgentTaskRouter
from src.agents.bridges.chatdev_orchestrator_bridge import \
    ChatDevDevelopmentOrchestrator
from src.agents.bridges.claude_orchestrator_bridge import ClaudeOrchestrator
from src.agents.bridges.consciousness_bridge_bridge import ConsciousnessBridge
from src.agents.bridges.guild_board_bridge import GuildBoardBridge
from src.agents.bridges.multi_ai_orchestrator_bridge import MultiAIOrchestrator
from src.agents.bridges.ollama_integration_bridge import \
    OllamaIntegrationBridge
from src.agents.bridges.quantum_problem_resolver_bridge import \
    QuantumProblemResolver
from src.agents.bridges.unified_ai_orchestrator_bridge import \
    UnifiedAIOrchestrator

__all__ = [
    "AgentRegistryBridge",
    "AgentTaskRouter",
    "ChatDevDevelopmentOrchestrator",
    "ClaudeOrchestrator",
    "ConsciousnessBridge",
    "GuildBoardBridge",
    "MultiAIOrchestrator",
    "OllamaIntegrationBridge",
    "QuantumProblemResolver",
    "UnifiedAIOrchestrator",
]
