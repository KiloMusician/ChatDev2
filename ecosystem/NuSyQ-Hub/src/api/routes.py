# DEPRECATED: Use src/api/agents_api.py (Phase 1 canonical) for agent/task routing.
# This file is an unwired legacy stub — it is NOT included in src/api/main.py.
# Kept for historical reference; do not add new logic here.
"""Lightweight API routes for task-style interactions."""

from __future__ import annotations

from typing import Any

try:
    from fastapi import APIRouter

    FASTAPI_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    FASTAPI_AVAILABLE = False
    APIRouter = None


router = APIRouter() if FASTAPI_AVAILABLE and APIRouter is not None else None


def get_router():
    """Return the API router if FastAPI is available."""
    return router


if router:

    @router.get("/tasks")
    def list_tasks() -> dict[str, Any]:
        return {"tasks": []}

    @router.post("/tasks")
    def create_task(payload: dict[str, Any]) -> dict[str, Any]:
        return {"status": "accepted", "task": payload}
