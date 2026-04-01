"""Registry subsystem — model registry REST API.

Provides a FastAPI-based REST API for registering and listing AI models
across providers. Backed by the shared ModelRegistry for persistent
model tracking across the NuSyQ ecosystem.

OmniTag: {
    "purpose": "registry_subsystem",
    "tags": ["Registry", "ModelRegistry", "FastAPI", "REST"],
    "category": "api",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

__all__ = ["RegisterPayload"]


def __getattr__(name: str):
    if name == "RegisterPayload":
        from src.registry.api import RegisterPayload

        return RegisterPayload
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
