"""Agent Communication, Orchestration, and Ecosystem System.

OmniTag: {
    "purpose": "agents_subsystem",
    "tags": ["Agents", "Communication", "Orchestration", "Ecosystem"],
    "category": "infrastructure",
    "evolution_stage": "v2.0"
}

Note: This module uses __getattr__ for lazy imports. Pylint E0603 warnings
about undefined names in __all__ are false positives.
"""

# pylint: disable=E0603

from __future__ import annotations

from src.agents.agent_communication_hub import (Agent, AgentCommunicationHub,
                                                AgentRole, AgentStats, Message,
                                                MessageType, get_agent_hub)

__all__ = [
    "AdaptiveTimeoutManager",
    "Agent",
    "AgentCommunicationHub",
    "AgentOrchestrationHub",
    "AgentQuest",
    "AgentQuestSummary",
    "AgentRole",
    "AgentStats",
    "AutonomousDevelopmentAgent",
    "ExecutionMode",
    "Message",
    "MessageType",
    "RegisteredService",
    "ServiceCapability",
    "TaskLock",
    "TaskPriority",
    "UnifiedAgentEcosystem",
    "get_agent_hub",
    "get_agent_orchestration_hub",
    "get_timeout_manager",
]


def __getattr__(name: str) -> object:
    if name in ("AgentOrchestrationHub", "get_agent_orchestration_hub"):
        from src.agents.agent_orchestration_hub import (
            AgentOrchestrationHub, get_agent_orchestration_hub)

        return locals()[name]
    if name in (
        "TaskPriority",
        "ExecutionMode",
        "TaskLock",
        "ServiceCapability",
        "RegisteredService",
    ):
        from src.agents.agent_orchestration_types import (ExecutionMode,
                                                          RegisteredService,
                                                          ServiceCapability,
                                                          TaskLock,
                                                          TaskPriority)

        return locals()[name]
    if name in ("AdaptiveTimeoutManager", "get_timeout_manager"):
        from src.agents.adaptive_timeout_manager import (
            AdaptiveTimeoutManager, get_timeout_manager)

        return locals()[name]
    if name == "AutonomousDevelopmentAgent":
        from src.agents.autonomous_development_agent import \
            AutonomousDevelopmentAgent

        return AutonomousDevelopmentAgent
    if name in ("UnifiedAgentEcosystem", "AgentQuest", "AgentQuestSummary"):
        from src.agents.unified_agent_ecosystem import (AgentQuest,
                                                        AgentQuestSummary,
                                                        UnifiedAgentEcosystem)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
