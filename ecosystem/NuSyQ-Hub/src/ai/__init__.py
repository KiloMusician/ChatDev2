"""AI subsystem — multi-provider AI coordination and intermediary.

Core AI coordination layer providing the AIIntermediary (2052 lines) for
multi-model orchestration, AICoordinator for provider management (Ollama,
OpenAI), and Ollama integration utilities.

OmniTag: {
    "purpose": "ai_subsystem",
    "tags": ["AI", "Intermediary", "Ollama", "MultiProvider", "Coordination"],
    "category": "ai_infrastructure",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.ai.ai_coordinator import (AIProvider, TaskRequest, TaskResponse,
                                       TaskType)
    from src.ai.ai_intermediary import (AIIntermediary, CognitiveParadigm,
                                        SymbolicTranslator)

__all__ = [
    # AI Intermediary (primary)
    "AIIntermediary",
    # AI Coordinator
    "AIProvider",
    "CognitiveParadigm",
    # Ollama utilities (functions, not a class — import from src.ai.ollama_model_manager directly)
    "SymbolicTranslator",
    "TaskRequest",
    "TaskResponse",
    "TaskType",
]


def __getattr__(name: str):
    if name in (
        "AIIntermediary",
        "CognitiveParadigm",
        "SymbolicTranslator",
        "RecursiveFeedbackEngine",
        "ContextualMemoryCore",
    ):
        from src.ai.ai_intermediary import (AIIntermediary, CognitiveParadigm,
                                            ContextualMemoryCore,
                                            RecursiveFeedbackEngine,
                                            SymbolicTranslator)

        return locals()[name]
    if name in ("AIProvider", "TaskType", "Priority", "TaskRequest", "TaskResponse"):
        from src.ai.ai_coordinator import (AIProvider, Priority, TaskRequest,
                                           TaskResponse, TaskType)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
