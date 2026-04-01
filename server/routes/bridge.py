"""
TerminalDepths / ChatDev Bridge API
=====================================
Stable bridge surface — all ecosystem repos call this, not the full game API.

Surfaces:
  GET  /api/bridge/ping
  GET  /api/bridge/manifest
  POST /api/bridge/command
  POST /api/bridge/task/add
  GET  /api/bridge/repo/list
  GET  /api/bridge/repo/status
  GET  /api/bridge/repo/status/{name}
  POST /api/bridge/repo/open
  POST /api/bridge/repo/exec
  POST /api/bridge/agent/dispatch
  POST /api/bridge/session/open
  GET  /api/bridge/session/state/{session_id}
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Request

_ECO = Path(__file__).resolve().parents[2] / "ecosystem"
if str(_ECO.parent) not in sys.path:
    sys.path.insert(0, str(_ECO.parent))

from ecosystem.nusyq_surface.registry import get_registry, list_repos, get_repo
from ecosystem.nusyq_surface.env import REGISTRY_PATH
from ecosystem.shared.task_queue import enqueue
from ecosystem.shared.memory import write as mem_write, read as mem_read
from ecosystem.shared.execution_log import log_action

router = APIRouter(prefix="/api/bridge", tags=["bridge"])

# Simple in-process session store
_sessions: Dict[str, Dict] = {}

_BOOT_TIME = time.time()


# ── Ping ───────────────────────────────────────────────────────────────────

@router.get("/ping")
async def ping():
    return {
        "status": "ok",
        "bridge": "chatdev",
        "uptime_s": round(time.time() - _BOOT_TIME, 1),
        "timestamp": time.time(),
    }


# ── Manifest ───────────────────────────────────────────────────────────────

@router.get("/manifest")
async def manifest():
    """Full bridge manifest — capabilities, repos, agents, surfaces."""
    registry = get_registry()
    online_repos = [r for r in list_repos() if r.get("status") == "online"]
    return {
        "bridge_version": "1.0.0",
        "cockpit": "chatdev",
        "cockpit_api": "http://localhost:6400",
        "orchestrator": "http://localhost:6400/api/orchestrator",
        "surfaces": ["web", "rest", "ws"],
        "capabilities": [
            "workflow_engine", "multi_agent", "vuegraph", "orchestrator",
            "chug_cycle", "shared_memory", "task_queue", "tool_registry",
            "agent_registry", "execution_log", "repo_bridge", "session_mgmt",
        ],
        "repos": {r["id"]: {"name": r.get("name"), "status": r.get("status"), "api": r.get("api")} for r in list_repos()},
        "online_repos": len(online_repos),
        "total_repos": len(list_repos()),
        "sessions_active": len(_sessions),
        "pages": {
            "home": "/",
            "ecosystem": "/ecosystem",
            "orchestrator": "/orchestrator",
            "workflows": "/workflows",
            "vuegraph": "/graph",
        },
    }


# ── Command ────────────────────────────────────────────────────────────────

_COMMAND_HANDLERS: Dict[str, Any] = {}


def _register_cmd(name: str):
    def decorator(fn):
        _COMMAND_HANDLERS[name] = fn
        return fn
    return decorator


@_register_cmd("repo list")
def _cmd_repo_list(ctx):
    return {"repos": list_repos()}


@_register_cmd("repo status")
def _cmd_repo_status(ctx):
    import urllib.request
    results = {}
    for repo in list_repos():
        health_url = repo.get("health") or repo.get("api")
        if not health_url:
            results[repo["id"]] = {"status": repo.get("status", "unknown"), "reachable": False}
            continue
        try:
            with urllib.request.urlopen(health_url, timeout=2) as r:
                results[repo["id"]] = {"status": "online", "reachable": True, "code": r.status}
        except Exception as e:
            results[repo["id"]] = {"status": "offline", "reachable": False, "error": str(e)[:60]}
    return {"repo_status": results}


@_register_cmd("chug run")
def _cmd_chug_run(ctx):
    task_id = enqueue("chug_cycle_trigger", repo="ecosystem", agent="bridge", priority=2)
    return {"task_id": task_id, "message": "CHUG cycle queued"}


@_register_cmd("serena status")
def _cmd_serena_status(ctx):
    import urllib.request
    try:
        with urllib.request.urlopen("http://localhost:8008/api/manifest", timeout=3) as r:
            data = json.loads(r.read())
        return {"serena": "reachable via Dev-Mentor", "manifest_keys": list(data.keys())}
    except Exception as e:
        return {"serena": "unreachable", "error": str(e)[:60]}


@_register_cmd("nusyq status")
def _cmd_nusyq_status(ctx):
    import urllib.request
    probes = {
        "chatdev": "http://localhost:6400/health",
        "dev_mentor": "http://localhost:8008/api/manifest",
        "concept_samurai": "http://localhost:3002/",
    }
    status = {}
    for name, url in probes.items():
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                status[name] = {"online": True, "code": r.status}
        except Exception as e:
            status[name] = {"online": False, "error": str(e)[:40]}
    return {"nusyq_status": status, "timestamp": time.time()}


@_register_cmd("agents")
def _cmd_agents(ctx):
    from ecosystem.shared.agent_registry import list_agents
    return {"agents": list_agents()}


@_register_cmd("tools")
def _cmd_tools(ctx):
    from ecosystem.shared.tool_registry import list_tools
    return {"tools": list_tools()}


@_register_cmd("memory snapshot")
def _cmd_memory_snapshot(ctx):
    from ecosystem.shared.memory import snapshot
    return {"memory": snapshot()}


@_register_cmd("boot")
def _cmd_boot(ctx):
    log_action("boot", "success", repo="bridge", agent="bridge")
    return {
        "status": "online",
        "message": "ChatDev bridge is active. All surfaces ready.",
        "cockpit": "http://localhost:5000",
        "orchestrator": "/orchestrator",
        "ecosystem": "/ecosystem",
    }


@_register_cmd("integrate")
def _cmd_integrate(ctx):
    from ecosystem.orchestrator import bootstrap
    result = bootstrap()
    return {"integrated": True, "bootstrap": result}


@router.post("/command")
async def bridge_command(body: dict):
    """
    Execute a bridge command.
    Known commands: boot, integrate, repo list, repo status, nusyq status,
                    serena status, agents, tools, memory snapshot, chug run
    """
    cmd = body.get("command", "").strip().lower()
    context = body.get("context", {})

    handler = _COMMAND_HANDLERS.get(cmd)
    if handler:
        log_action(f"bridge.cmd:{cmd}", "success", repo="bridge", agent="bridge")
        return {"command": cmd, "result": handler(context)}

    # Fuzzy match
    matches = [k for k in _COMMAND_HANDLERS if k.startswith(cmd.split()[0])]
    return {
        "command": cmd,
        "error": "unknown command",
        "suggestions": matches,
        "available": sorted(_COMMAND_HANDLERS.keys()),
    }


# ── Task ───────────────────────────────────────────────────────────────────

@router.post("/task/add")
async def task_add(body: dict):
    task_id = enqueue(
        action=body.get("action", "bridge_task"),
        repo=body.get("repo", "ecosystem"),
        agent=body.get("agent"),
        payload=body.get("payload", {}),
        priority=body.get("priority", 5),
    )
    return {"task_id": task_id, "status": "queued"}


# ── Repo ───────────────────────────────────────────────────────────────────

@router.get("/repo/list")
async def repo_list():
    return {"repos": list_repos()}


@router.get("/repo/status")
async def repo_status_all():
    return _cmd_repo_status({})


@router.get("/repo/status/{name}")
async def repo_status_one(name: str):
    import urllib.request
    r = get_repo(name)
    if not r:
        return {"error": f"repo '{name}' not found in registry"}
    health_url = r.get("health") or r.get("api")
    reachable = False
    code = None
    if health_url:
        try:
            with urllib.request.urlopen(health_url, timeout=3) as resp:
                reachable = True
                code = resp.status
        except Exception:
            pass
    return {**r, "reachable": reachable, "http_code": code}


@router.post("/repo/open")
async def repo_open(body: dict):
    name = body.get("name", "")
    r = get_repo(name)
    if not r:
        return {"error": f"repo '{name}' not found"}
    mem_write(f"repo.last_opened", name, namespace="bridge")
    log_action(f"repo.open:{name}", "success", repo="bridge", agent="bridge")
    return {
        "opened": name,
        "root": r.get("root"),
        "api": r.get("api"),
        "capabilities": r.get("capabilities", []),
    }


@router.post("/repo/exec")
async def repo_exec(body: dict):
    """Execute a shell command in a repo's root directory."""
    name = body.get("repo", "")
    cmd = body.get("command", "")
    if not name or not cmd:
        return {"error": "repo and command required"}
    r = get_repo(name)
    if not r:
        return {"error": f"repo '{name}' not found"}
    root = r.get("root", ".")
    if not Path(root).exists():
        return {"error": f"repo root not found: {root}"}
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=root,
            capture_output=True, text=True, timeout=15,
        )
        log_action(f"repo.exec:{name}", "success", repo=name, agent="bridge")
        return {
            "repo": name,
            "command": cmd,
            "returncode": result.returncode,
            "stdout": result.stdout[-1000:],
            "stderr": result.stderr[-500:],
        }
    except subprocess.TimeoutExpired:
        return {"error": "command timed out"}
    except Exception as e:
        return {"error": str(e)}


# ── Agent ──────────────────────────────────────────────────────────────────

@router.post("/agent/dispatch")
async def agent_dispatch(body: dict):
    agent = body.get("agent", "")
    task = body.get("task", "")
    payload = body.get("payload", {})
    if not agent or not task:
        return {"error": "agent and task required"}

    task_id = enqueue(
        action=task,
        repo="bridge",
        agent=agent,
        payload={"dispatched_by": "bridge", **payload},
        priority=3,
    )
    log_action(f"agent.dispatch:{agent}", "success", repo="bridge", agent=agent)
    return {"dispatched": True, "agent": agent, "task": task, "task_id": task_id}


# ── Session ────────────────────────────────────────────────────────────────

@router.post("/session/open")
async def session_open(body: dict):
    session_id = body.get("session_id") or str(uuid.uuid4())[:8]
    context = body.get("context", {})
    _sessions[session_id] = {
        "session_id": session_id,
        "context": context,
        "opened_at": time.time(),
        "commands": [],
    }
    log_action(f"session.open:{session_id}", "success", repo="bridge", agent="bridge")
    return {"session_id": session_id, "status": "open"}


@router.get("/session/state/{session_id}")
async def session_state(session_id: str):
    s = _sessions.get(session_id)
    if not s:
        return {"error": f"session '{session_id}' not found"}
    return s
