"""NuSyQ bridge stubs — satisfies Dev-Mentor's cross-service polling without errors."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/nusyq", tags=["nusyq-bridge"])


@router.get("/colonist_state")
async def colonist_state():
    """Stub endpoint — Dev-Mentor polls this to sync colonist state across services."""
    return {
        "colonists": [],
        "total": 0,
        "source": "chatdev-2.0-bridge",
        "note": "SimulatedVerse not running — stub response",
    }


@router.get("/manifest")
async def nusyq_manifest():
    """NuSyQ manifest stub — returns ChatDev 2.0 service identity."""
    return {
        "service": "ChatDev 2.0 (DevAll)",
        "version": "2.0.0",
        "capabilities": ["workflow_orchestration", "multi_agent", "vue_graph"],
        "ecosystem_role": "orchestrator",
        "ports": {"frontend": 5000, "backend": 6400},
    }


@router.get("/ping")
async def nusyq_ping():
    return {"pong": True, "service": "chatdev-2.0"}


@router.post("/register")
async def nusyq_register(body: dict = None):
    """Accept agent registration calls from Dev-Mentor NuSyQ bridge."""
    return {"registered": True, "service": "chatdev-2.0"}


@router.get("/game/state")
async def game_state():
    """Stub for Dev-Mentor autoboot probe of /api/game/state."""
    return {"state": "stub", "service": "chatdev-2.0", "note": "No game engine in this service"}


@router.get("/state")
async def service_state():
    """Stub for /api/state probe."""
    return {"state": "running", "service": "chatdev-2.0"}
