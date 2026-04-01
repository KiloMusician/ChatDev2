"""API subsystem — FastAPI server for NuSyQ-Hub reactive state APIs.

Provides REST endpoints for system state, agent management, hacking
mechanics, quest tracking, problem resolution, and code generation.
Runs on localhost:8000 via uvicorn.

OmniTag: {
    "purpose": "api_subsystem",
    "tags": ["API", "FastAPI", "REST", "SystemState"],
    "category": "api",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.api.main import app

__all__ = ["app"]


def __getattr__(name: str):
    if name == "app":
        from src.api.main import app

        return app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
