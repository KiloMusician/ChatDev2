"""Shared subsystem — common utilities and model registry.

Provides shared infrastructure used across NuSyQ subsystems, including
the model registry for tracking available AI models across providers
(LM Studio, Ollama, OpenAI, etc.).

OmniTag: {
    "purpose": "shared_subsystem",
    "tags": ["Shared", "ModelRegistry", "Common", "Infrastructure"],
    "category": "infrastructure",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

__all__ = ["ModelRegistry"]


def __getattr__(name: str):
    if name == "ModelRegistry":
        from src.shared.model_registry import ModelRegistry

        return ModelRegistry
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
