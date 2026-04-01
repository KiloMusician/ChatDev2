"""
td_bridge.py — NuSyQ-Hub ← zero-setup TerminalDepths bridge.

Drop this file anywhere in a repo and import it directly:

    from td_bridge import td, hub, td_command, td_heartbeat

Quick reference
---------------
    td.ping()                        → {"status": "ok", ...}
    td.manifest()                    → full bridge manifest
    td.command("boot")               → run a bridge command
    td.command("agents")             → list agents
    td.command("projects")           → list WareHouse projects
    td.task("scan_repo", repo="...")  → enqueue a task
    td.repo_status()                 → all repo health
    td.agent_dispatch("ada", "scan") → dispatch an agent

    hub.status()                     → orchestrator status
    hub.agents()                     → agent registry
    hub.memory_write("k", val)       → write shared memory
    hub.memory_read("k")             → read shared memory
    hub.enqueue("action", repo="...") → add task to queue

    td_heartbeat()                   → register this repo with bridge
    td_hub_status()                  → NuSyQ-Hub API status (port 3003)
    td_game_state()                  → read persisted game state
    td_push_state(update_dict)       → merge-update game state
    td_consciousness()               → read consciousness metrics
    td_push_consciousness(update)    → update consciousness metrics

This repo: REPO_ID = "nusyq_hub"
"""
from __future__ import annotations

import sys
import os
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Optional

# ── Metadata ────────────────────────────────────────────────────────────────
REPO_ID   = "nusyq_hub"
REPO_NAME = "NuSyQ-Hub"

# ── Workspace auto-resolution ────────────────────────────────────────────────
# Works from any depth: repo root, subdirectory, or scripts/ folder.
_THIS_DIR = Path(__file__).resolve().parent

def _find_workspace(start: Path) -> Path:
    p = start
    for _ in range(8):
        if (p / "ecosystem").is_dir() and (p / "server").is_dir():
            return p
        p = p.parent
    return start

_WORKSPACE = _find_workspace(_THIS_DIR)
if str(_WORKSPACE) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE))

# ── Lazy import from nusyq_surface ──────────────────────────────────────────
try:
    from ecosystem.nusyq_surface.bridge_client import BridgeClient
    from ecosystem.nusyq_surface.hub_client import HubClient
    td  = BridgeClient()
    hub = HubClient()
    _CLIENTS_OK = True
except Exception as _e:
    _CLIENTS_OK = False
    class _FallbackClient:
        def __getattr__(self, name):
            def _stub(*a, **kw):
                return {"error": f"nusyq_surface unavailable: {_e}", "method": name}
            return _stub
    td  = _FallbackClient()
    hub = _FallbackClient()


# ── Convenience wrappers ─────────────────────────────────────────────────────

def td_ping() -> dict:
    """Quick health check against the ChatDev bridge."""
    return td.ping()

def td_manifest() -> dict:
    """Full bridge manifest — capabilities, repos, agents, surfaces."""
    return td.manifest()

def td_command(cmd: str, context: dict = None) -> dict:
    """Run any registered bridge command (boot, agents, tools, repo list, projects …)."""
    return td.command(cmd, context)

def td_task(action: str, repo: str = REPO_ID, payload: dict = None, priority: int = 5) -> str:
    """Enqueue a task in the shared task queue. Returns task_id."""
    r = td.task_add(action, repo=repo, payload=payload, priority=priority)
    return r.get("task_id", "")

def td_repo_list() -> list:
    """All repos registered in the ecosystem."""
    r = td.repo_status()
    return r.get("repos", []) if isinstance(r, dict) else []

def td_dispatch(agent: str, task: str, payload: dict = None) -> dict:
    """Dispatch an agent task via the bridge."""
    return td.agent_dispatch(agent, task, payload)

def td_session(session_id: str = None) -> dict:
    """Open or resume a bridge session."""
    return td.session_open(session_id)


# ── NuSyQ-Hub direct calls (port 3003) ──────────────────────────────────────
_HUB_API = "http://localhost:3003"

def _hub_get(path: str, timeout: int = 4) -> dict:
    try:
        with urllib.request.urlopen(f"{_HUB_API}{path}", timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e), "path": path}

def _hub_post(path: str, data: dict = None, timeout: int = 4) -> dict:
    try:
        body = json.dumps(data or {}).encode()
        req = urllib.request.Request(
            f"{_HUB_API}{path}", data=body,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e), "path": path}

def td_hub_status() -> dict:
    """NuSyQ-Hub reactive API status (port 3003/api/status)."""
    return _hub_get("/api/status")

def td_hub_agents() -> dict:
    """List agents known to NuSyQ-Hub."""
    return _hub_get("/api/agents")

def td_hub_quests() -> dict:
    """List quests from NuSyQ-Hub."""
    return _hub_get("/api/quests")

def td_hub_systems() -> dict:
    """NuSyQ-Hub system metrics."""
    return _hub_get("/api/metrics")


# ── Game state (persisted via ChatDev bridge) ────────────────────────────────
_NUSYQ_API = "http://localhost:6400"

def _nusyq_get(path: str) -> dict:
    try:
        with urllib.request.urlopen(f"{_NUSYQ_API}{path}", timeout=4) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def _nusyq_post(path: str, data: dict) -> dict:
    try:
        body = json.dumps(data).encode()
        req = urllib.request.Request(
            f"{_NUSYQ_API}{path}", data=body,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=4) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def td_game_state() -> dict:
    """Read the persisted game/simulation state from the bridge."""
    return _nusyq_get("/api/nusyq/game/state")

def td_push_state(update: dict) -> dict:
    """Merge-update the persisted game state (partial update supported)."""
    return _nusyq_post("/api/nusyq/game/state", update)

def td_consciousness() -> dict:
    """Read the persisted consciousness metrics."""
    return _nusyq_get("/api/nusyq/consciousness")

def td_push_consciousness(update: dict) -> dict:
    """Update consciousness metrics."""
    return _nusyq_post("/api/nusyq/consciousness", update)

def td_colonists() -> dict:
    """Read colonist state (RimWorld bridge / SimulatedVerse)."""
    return _nusyq_get("/api/nusyq/colonist_state")

def td_push_colonists(colonists: list, source: str = REPO_ID) -> dict:
    """Push colonist state to the bridge."""
    return _nusyq_post("/api/nusyq/colonist_state", {"colonists": colonists, "source": source})


# ── Heartbeat / self-registration ────────────────────────────────────────────

def td_heartbeat(extra: dict = None) -> dict:
    """
    Register this repo with the ChatDev bridge — call on startup.
    Logs the repo's identity and health to shared memory.
    """
    payload = {
        "repo_id": REPO_ID,
        "repo_name": REPO_NAME,
        "ts": time.time(),
        "workspace": str(_WORKSPACE),
        "clients_ok": _CLIENTS_OK,
        **(extra or {}),
    }
    result = hub.memory_write(f"heartbeat.nusyq_hub", payload)
    # Also fire a register command so it shows in the bridge manifest
    td.command("integrate", {"repo": REPO_ID})
    return {"heartbeat": "sent", "repo": REPO_ID, **result} if isinstance(result, dict) else {"heartbeat": "sent", "repo": REPO_ID}


# ── Smoke test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import pprint
    print(f"=== td_bridge smoke test — NuSyQ-Hub (nusyq_hub) ===")
    print("workspace:", _WORKSPACE)
    print("clients_ok:", _CLIENTS_OK)
    print()
    print("[ping]")
    pprint.pprint(td_ping())
    print()
    print("[hub_status]")
    pprint.pprint(td_hub_status())
    print()
    print("[game_state]")
    pprint.pprint(td_game_state())
    print()
    print("[heartbeat]")
    pprint.pprint(td_heartbeat())
