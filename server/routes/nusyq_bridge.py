"""NuSyQ bridge — satisfies Dev-Mentor cross-service polling + persists state to shared memory."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter

_ECO = Path(__file__).resolve().parents[2] / "ecosystem"
if str(_ECO.parent) not in sys.path:
    sys.path.insert(0, str(_ECO.parent))

from ecosystem.shared.memory import write as mem_write, read as mem_read
from ecosystem.shared.execution_log import log_action

router = APIRouter(prefix="/api/nusyq", tags=["nusyq-bridge"])

_NS = "game_state"   # shared memory namespace for all game state
_PFX = "nusyq."     # key prefix to avoid collision with other namespaces


def _gread(key: str, default=None):
    """Read a game-state value from shared memory (already JSON-decoded by mem_read)."""
    val = mem_read(_PFX + key)
    return default if val is None else val


def _gwrite(key: str, value: Any):
    """Write a game-state value to shared memory (mem_write handles serialisation)."""
    mem_write(_PFX + key, value, namespace=_NS)


# ── Colonist state ─────────────────────────────────────────────────────────

@router.get("/colonist_state")
async def colonist_state():
    """Return persisted colonist state (written by RimWorld bridge or simulated)."""
    saved = _gread("colonists")
    if saved:
        return saved
    return {
        "colonists": [],
        "total": 0,
        "source": "chatdev-2.0-bridge",
        "note": "No colonist data yet — push via POST /api/nusyq/colonist_state",
        "last_updated": None,
    }


@router.post("/colonist_state")
async def update_colonist_state(body: dict):
    """Accept colonist state push from RimWorld bridge or SimulatedVerse."""
    payload = {
        "colonists": body.get("colonists", []),
        "total": body.get("total", len(body.get("colonists", []))),
        "source": body.get("source", "push"),
        "last_updated": time.time(),
    }
    _gwrite("colonists", payload)
    log_action("colonist_state.update", "success", repo="nusyq_bridge", agent="bridge")
    return {"saved": True, "total": payload["total"]}


# ── Game state ──────────────────────────────────────────────────────────────

_DEFAULT_GAME_STATE: Dict[str, Any] = {
    "phase": "idle",
    "tick": 0,
    "resources": {"energy": 0, "materials": 0, "population": 0, "research": 0},
    "buildings": {"generators": 0, "factories": 0, "labs": 0, "farms": 0},
    "consciousness_level": 0,
    "unlocks": {},
    "flags": {},
    "last_updated": None,
    "source": "chatdev-2.0-bridge",
}


@router.get("/game/state")
async def game_state():
    """Return persisted game state."""
    saved = _gread("game_state")
    return saved if saved else _DEFAULT_GAME_STATE


@router.post("/game/state")
async def update_game_state(body: dict):
    """Write game state update — merges into existing state."""
    existing = _gread("game_state") or dict(_DEFAULT_GAME_STATE)
    for k, v in body.items():
        if isinstance(v, dict) and isinstance(existing.get(k), dict):
            existing[k].update(v)
        else:
            existing[k] = v
    existing["last_updated"] = time.time()
    _gwrite("game_state", existing)
    log_action("game_state.update", "success", repo="nusyq_bridge", agent="bridge")
    return {"saved": True, "state": existing}


# ── Consciousness ───────────────────────────────────────────────────────────

@router.get("/consciousness")
async def get_consciousness():
    """Return consciousness state (persisted)."""
    state = _gread("consciousness") or {
        "level": 0, "xp": 0, "energy": 10, "population": 1, "research": 0,
        "lattice_connections": 0, "last_updated": None,
    }
    return state


@router.post("/consciousness")
async def update_consciousness(body: dict):
    """Update consciousness state."""
    existing = _gread("consciousness") or {}
    existing.update(body)
    existing["last_updated"] = time.time()
    _gwrite("consciousness", existing)
    return {"saved": True}


# ── Session history ─────────────────────────────────────────────────────────

@router.get("/sessions")
async def list_sessions():
    """Return list of persisted session IDs."""
    raw = _gread("session_ids") or []
    return {"sessions": raw, "total": len(raw)}


@router.post("/sessions/{session_id}")
async def persist_session(session_id: str, body: dict):
    """Persist a session's metadata to shared memory."""
    _gwrite(f"session.{session_id}", {**body, "session_id": session_id, "saved_at": time.time()})
    # Track session IDs
    ids = _gread("session_ids") or []
    if session_id not in ids:
        ids.append(session_id)
        _gwrite("session_ids", ids)
    return {"saved": True, "session_id": session_id}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Retrieve a persisted session."""
    data = _gread(f"session.{session_id}")
    if data is None:
        return {"error": f"session '{session_id}' not found"}
    return data


# ── Service identity ────────────────────────────────────────────────────────

@router.get("/manifest")
async def nusyq_manifest():
    return {
        "service": "ChatDev 2.0 (DevAll)",
        "version": "2.0.0",
        "capabilities": ["workflow_orchestration", "multi_agent", "vue_graph",
                         "persistent_game_state", "bridge_events"],
        "ecosystem_role": "orchestrator",
        "ports": {"frontend": 5000, "backend": 6400},
    }


@router.get("/ping")
async def nusyq_ping():
    return {"pong": True, "service": "chatdev-2.0"}


@router.post("/register")
async def nusyq_register(body: dict = None):
    """Accept agent registration calls from Dev-Mentor NuSyQ bridge."""
    if body:
        agent_id = body.get("agent_id", "unknown")
        _gwrite(f"registered_agent.{agent_id}", {**body, "registered_at": time.time()})
    return {"registered": True, "service": "chatdev-2.0"}


@router.get("/state")
async def service_state():
    """Top-level service state summary."""
    gs = _gread("game_state") or {}
    cs = _gread("colonists") or {}
    con = _gread("consciousness") or {}
    return {
        "state": "running",
        "service": "chatdev-2.0",
        "game_phase": gs.get("phase", "idle"),
        "colonists": cs.get("total", 0),
        "consciousness_level": con.get("level", 0),
        "last_game_update": gs.get("last_updated"),
    }
