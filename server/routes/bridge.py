"""
TerminalDepths / ChatDev Bridge API
=====================================
Stable bridge surface — all ecosystem repos call this, not the full game API.

Surfaces:
  GET  /api/bridge/ping
  GET  /api/bridge/status
  GET  /api/bridge/manifest
  GET  /api/bridge/quests
  POST /api/bridge/quests/sync
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

import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

_ECO = Path(__file__).resolve().parents[2] / "ecosystem"
_WORKSPACE = _ECO.parent  # /home/runner/workspace
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

# ── Quest catalogue ─────────────────────────────────────────────────────────
_QUEST_FILES = [
    _ECO / "Dev-Mentor" / "challenges" / "ctf" / name
    for name in ("crypto.json", "forensics.json", "network.json",
                 "reverse_engineering.json", "web.json")
]

def _load_quests() -> list:
    """Read all CTF quest JSON files from Dev-Mentor and return a flat list."""
    all_quests: list = []
    for path in _QUEST_FILES:
        if not path.exists():
            continue
        try:
            raw = json.loads(path.read_text())
            if isinstance(raw, list):
                all_quests.extend(raw)
            elif isinstance(raw, dict):
                all_quests.extend(raw.values())
        except Exception:
            pass
    return all_quests

def _sync_quests_to_memory(quests: list) -> dict:
    """Write quest summary into shared memory and return stats."""
    by_cat: Dict[str, int] = {}
    total_xp = 0
    for q in quests:
        if isinstance(q, dict):
            cat = q.get("category", "unknown")
            by_cat[cat] = by_cat.get(cat, 0) + 1
            total_xp += q.get("xp", 0)
    summary = {
        "total": len(quests),
        "by_category": by_cat,
        "categories": list(by_cat.keys()),
        "total_xp": total_xp,
        "synced_at": time.time(),
    }
    mem_write("devmentor.quests.summary", json.dumps(summary), namespace="bridge")
    mem_write("devmentor.quests.synced", str(len(quests)), namespace="bridge")
    log_action("quest.sync", "success", repo="Dev-Mentor", agent="bridge")
    return summary


# ── Ping / Status ──────────────────────────────────────────────────────────

@router.get("/ping")
async def ping():
    return {
        "status": "ok",
        "bridge": "chatdev",
        "uptime_s": round(time.time() - _BOOT_TIME, 1),
        "timestamp": time.time(),
    }


@router.get("/status")
async def bridge_status():
    """Compact bridge status for UI panels — uptime, quest count, repo health."""
    import urllib.request, concurrent.futures
    quests = _load_quests()
    cached_synced = mem_read("devmentor.quests.synced")

    repos = list_repos()
    repo_urls = {r["id"]: (r.get("health") or r.get("api")) for r in repos if r.get("id")}

    def _probe_all():
        result = {}
        def _probe(item):
            rid, url = item
            if not url:
                return rid, False
            try:
                with urllib.request.urlopen(url, timeout=2) as r:
                    return rid, r.status == 200
            except Exception:
                return rid, False
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            for rid, ok in pool.map(_probe, repo_urls.items()):
                result[rid] = ok
        return result

    probe_results = await asyncio.to_thread(_probe_all)
    online_repos = [rid for rid, ok in probe_results.items() if ok]
    offline_repos = [rid for rid, ok in probe_results.items() if not ok]

    return {
        "status": "online",
        "uptime_s": round(time.time() - _BOOT_TIME, 1),
        "sessions_active": len(_sessions),
        "quests": {
            "total": len(quests),
            "categories": sorted({q.get("category", "?") for q in quests if isinstance(q, dict)}),
            "synced_to_memory": cached_synced is not None,
            "synced_count": int(cached_synced) if cached_synced and cached_synced.isdigit() else 0,
        },
        "repos": {
            "online": online_repos,
            "offline": offline_repos,
            "total": len(list_repos()),
        },
        "commands_available": sorted(_COMMAND_HANDLERS.keys()),
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
        "commands_available": sorted(_COMMAND_HANDLERS.keys()),
        "command_count": len(_COMMAND_HANDLERS),
        "pages": {
            "home": "/",
            "ecosystem": "/ecosystem",
            "orchestrator": "/orchestrator",
            "workflows": "/workflows",
            "vuegraph": "/graph",
        },
    }


# ── SSE Event Stream ────────────────────────────────────────────────────────

@router.get("/events")
async def bridge_events(request: Request):
    """
    Server-Sent Events stream — aggregates events from all repos.
    Event types: ping, log, health, project
    """
    from ecosystem.shared.execution_log import recent_logs

    async def event_generator():
        last_log_count = 0
        last_health_check = 0.0

        while True:
            if await request.is_disconnected():
                break

            now = time.time()

            # ── ping every 5s ─────────────────────────────────────────────
            yield f"event: ping\ndata: {json.dumps({'t': round(now, 1)})}\n\n"

            # ── new execution log entries ─────────────────────────────────
            try:
                logs = recent_logs(limit=50)
                if len(logs) > last_log_count:
                    for entry in logs[:len(logs) - last_log_count]:
                        payload = json.dumps({
                            "action": entry.get("action"),
                            "repo": entry.get("repo"),
                            "status": entry.get("status"),
                            "ts": entry.get("started_at"),
                        })
                        yield f"event: log\ndata: {payload}\n\n"
                    last_log_count = len(logs)
            except Exception:
                pass

            # ── health snapshot every 30s (threaded to avoid blocking event loop) ──
            if now - last_health_check >= 30:
                try:
                    import urllib.request as _urllib, concurrent.futures as _cf
                    _probes = {
                        "chatdev":         "http://localhost:6400/health",
                        "dev_mentor":      "http://localhost:8008/api/manifest",
                        "nusyq_hub":       "http://localhost:3003/api/status",
                        "concept_samurai": "http://localhost:3002/",
                    }

                    def _do_probes():
                        ok = []
                        def _p(item):
                            sn, url = item
                            try:
                                with _urllib.urlopen(url, timeout=2) as r:
                                    return sn if r.status == 200 else None
                            except Exception:
                                return None
                        with _cf.ThreadPoolExecutor(max_workers=4) as p:
                            for r in p.map(_p, _probes.items()):
                                if r:
                                    ok.append(r)
                        return ok

                    online = await asyncio.to_thread(_do_probes)
                    payload = json.dumps({
                        "online": len(online),
                        "services": online,
                        "repos": {"online": online, "total": len(_probes)},
                    })
                    yield f"event: health\ndata: {payload}\n\n"
                    last_health_check = now
                except Exception:
                    pass

            await asyncio.sleep(5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ── Projects ────────────────────────────────────────────────────────────────

_WAREHOUSE = Path(__file__).resolve().parents[2] / "WareHouse"


def _list_projects() -> list:
    """Scan WareHouse/ and return metadata for each project directory."""
    if not _WAREHOUSE.exists():
        return []
    projects = []
    for d in sorted(_WAREHOUSE.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not d.is_dir():
            continue
        files = list(d.iterdir())
        py_files = [f.name for f in files if f.suffix == ".py"]
        has_prompt = any(f.suffix == ".prompt" for f in files)
        prompt_text = None
        if has_prompt:
            pf = next((f for f in files if f.suffix == ".prompt"), None)
            try:
                prompt_text = pf.read_text()[:500]
            except Exception:
                pass
        size_kb = sum(f.stat().st_size for f in files if f.is_file()) // 1024
        projects.append({
            "name": d.name,
            "file_count": len(files),
            "has_code": bool(py_files),
            "py_files": py_files[:10],
            "has_prompt": has_prompt,
            "prompt_preview": prompt_text,
            "size_kb": size_kb,
            "modified_at": d.stat().st_mtime,
        })
    return projects


@router.get("/projects")
async def projects_list():
    """List all ChatDev WareHouse projects with metadata."""
    import os
    api_key_available = bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"))
    projects = _list_projects()
    return {
        "total": len(projects),
        "api_key_available": api_key_available,
        "warehouse_path": str(_WAREHOUSE),
        "projects": projects,
    }


@router.get("/projects/{name:path}")
async def project_detail(name: str):
    """Return detailed metadata for a specific WareHouse project."""
    d = _WAREHOUSE / name
    if not d.exists() or not d.is_dir():
        return {"error": f"project '{name}' not found"}
    files = list(d.iterdir())
    file_list = []
    for f in files:
        if f.is_file():
            try:
                preview = f.read_text()[:300] if f.suffix in (".py", ".md", ".txt", ".prompt", ".html", ".js") else None
            except Exception:
                preview = None
            file_list.append({"name": f.name, "size_bytes": f.stat().st_size, "preview": preview})
    return {
        "name": name,
        "files": file_list,
        "total_files": len(file_list),
        "has_code": any(f["name"].endswith(".py") for f in file_list),
    }


# ── Quests ─────────────────────────────────────────────────────────────────

@router.get("/quests")
async def quests_list():
    """Return all Dev-Mentor CTF quests, with memory-sync status."""
    quests = _load_quests()
    cached_synced = mem_read("devmentor.quests.synced")
    by_cat: Dict[str, int] = {}
    total_xp = 0
    for q in quests:
        if isinstance(q, dict):
            cat = q.get("category", "unknown")
            by_cat[cat] = by_cat.get(cat, 0) + 1
            total_xp += q.get("xp", 0)
    return {
        "total": len(quests),
        "total_xp": total_xp,
        "categories": sorted(by_cat.keys()),
        "by_category": by_cat,
        "synced": cached_synced is not None,
        "synced_count": int(cached_synced) if cached_synced and cached_synced.isdigit() else 0,
        "quests": quests,
    }


@router.post("/quests/sync")
async def quests_sync():
    """Sync Dev-Mentor quest catalogue into shared memory and return stats."""
    quests = _load_quests()
    summary = _sync_quests_to_memory(quests)
    return {"synced": True, **summary}


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
    import urllib.request, concurrent.futures
    repos = list_repos()

    def _probe(repo):
        rid = repo.get("id", "?")
        url = repo.get("health") or repo.get("api")
        if not url:
            return rid, {"status": repo.get("status", "unknown"), "reachable": False}
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                return rid, {"status": "online", "reachable": True, "code": r.status}
        except Exception as e:
            return rid, {"status": "offline", "reachable": False, "error": str(e)[:60]}

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for rid, info in pool.map(_probe, repos):
            results[rid] = info
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
    import urllib.request, concurrent.futures
    # chatdev = self; probe it in a thread to avoid blocking the async event loop
    ext_probes = {
        "dev_mentor":      "http://localhost:8008/api/manifest",
        "nusyq_hub":       "http://localhost:3003/api/status",
        "concept_samurai": "http://localhost:3002/",
    }
    status = {"chatdev": {"online": True, "code": 200, "note": "self"}}

    def _probe(name_url):
        name, url = name_url
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                return name, {"online": True, "code": r.status}
        except Exception as e:
            return name, {"online": False, "error": str(e)[:60]}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for name, result in pool.map(_probe, ext_probes.items()):
            status[name] = result

    return {"nusyq_status": status, "timestamp": time.time(), "hub_port": 3003}


@_register_cmd("sync steward status")
def _cmd_sync_status(ctx):
    """Read-only ecosystem sync snapshot (no git writes)."""
    import subprocess, threading
    _ECO_STEWARD = _ECO / "sync_steward.py"
    if not _ECO_STEWARD.exists():
        return {"error": "sync_steward.py not found in ecosystem/"}
    try:
        r = subprocess.run(
            [sys.executable, str(_ECO_STEWARD), "--mode", "status", "--json"],
            capture_output=True, text=True, timeout=30,
            cwd=str(_WORKSPACE),
        )
        import json as _json
        return _json.loads(r.stdout) if r.returncode in (0, 1) else {"error": r.stderr[:200]}
    except Exception as e:
        return {"error": str(e)[:80]}


@_register_cmd("sync steward hourly")
def _cmd_sync_hourly(ctx):
    """Lightweight catch-up: fetch + inspect divergence, no commit/push."""
    import subprocess
    _ECO_STEWARD = _ECO / "sync_steward.py"
    if not _ECO_STEWARD.exists():
        return {"error": "sync_steward.py not found"}

    def _run():
        subprocess.run(
            [sys.executable, str(_ECO_STEWARD), "--mode", "hourly", "--log"],
            cwd=str(_WORKSPACE), capture_output=True, timeout=60,
        )

    import threading
    threading.Thread(target=_run, daemon=True).start()
    log_action("sync.steward.hourly", "triggered", repo="ecosystem", agent="bridge")
    return {"sync_steward": "hourly", "status": "started in background", "log_dir": "ecosystem/logs/steward/"}


@_register_cmd("sync steward full")
def _cmd_sync_full(ctx):
    """Full steward cycle: fetch, rebase, validate, stage, commit, push."""
    import subprocess
    _ECO_STEWARD = _ECO / "sync_steward.py"
    if not _ECO_STEWARD.exists():
        return {"error": "sync_steward.py not found"}

    def _run():
        subprocess.run(
            [sys.executable, str(_ECO_STEWARD), "--mode", "full", "--log"],
            cwd=str(_WORKSPACE), capture_output=True, timeout=120,
        )

    import threading
    threading.Thread(target=_run, daemon=True).start()
    log_action("sync.steward.full", "triggered", repo="ecosystem", agent="bridge")
    return {"sync_steward": "full", "status": "started in background", "log_dir": "ecosystem/logs/steward/"}


@_register_cmd("sync steward dryrun")
def _cmd_sync_dryrun(ctx):
    """Full steward pipeline in dry-run mode — inspect only, zero writes."""
    import subprocess, json as _json
    _ECO_STEWARD = _ECO / "sync_steward.py"
    if not _ECO_STEWARD.exists():
        return {"error": "sync_steward.py not found"}
    try:
        r = subprocess.run(
            [sys.executable, str(_ECO_STEWARD), "--mode", "full", "--dry-run", "--json"],
            capture_output=True, text=True, timeout=60, cwd=str(_WORKSPACE),
        )
        return _json.loads(r.stdout) if r.returncode in (0, 1) else {"error": r.stderr[:200]}
    except Exception as e:
        return {"error": str(e)[:80]}


@_register_cmd("gordon status")
def _cmd_gordon_status(ctx):
    """Fetch Gordon orchestrator status from Dev-Mentor."""
    import urllib.request
    try:
        with urllib.request.urlopen("http://localhost:8008/api/gordon/status", timeout=3) as r:
            import json as _json
            data = _json.loads(r.read())
            return {"gordon": data, "source": "dev_mentor"}
    except Exception as e:
        return {"gordon": {"ok": False, "error": str(e)}, "source": "dev_mentor"}


@_register_cmd("gordon run")
def _cmd_gordon_run(ctx):
    """Trigger one Gordon orchestrator cycle (subprocess, non-blocking)."""
    import subprocess, threading
    gordon_script = _ECO / "Dev-Mentor" / "scripts" / "gordon_orchestrator.py"
    if not gordon_script.exists():
        return {"gordon_run": False, "error": "gordon_orchestrator.py not found"}

    def _run():
        subprocess.run(
            [sys.executable, str(gordon_script), "--mode", "once"],
            cwd=str(_ECO / "Dev-Mentor"),
            capture_output=True, timeout=30,
        )

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    log_action("gordon.run", "triggered", repo="Dev-Mentor", agent="bridge")
    return {"gordon_run": True, "mode": "once", "note": "cycle started in background"}


@_register_cmd("serena find")
def _cmd_serena_find(ctx):
    """Query Serena (Dev-Mentor) for symbol/function search."""
    import urllib.request, json as _json
    query = ctx.get("query", ctx.get("args", "bridge integration"))
    try:
        body = _json.dumps({"query": query, "limit": 8}).encode()
        req = urllib.request.Request(
            "http://localhost:8008/api/serena/ask", data=body,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            return _json.loads(r.read())
    except Exception as e:
        return {"serena": "unreachable", "error": str(e)[:60]}


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


@_register_cmd("projects")
def _cmd_projects(ctx):
    import os
    projects = _list_projects()
    return {
        "total": len(projects),
        "api_key_available": bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")),
        "projects": [{k: v for k, v in p.items() if k != "prompt_preview"} for p in projects[:20]],
    }


@_register_cmd("quest sync")
def _cmd_quest_sync(ctx):
    quests = _load_quests()
    summary = _sync_quests_to_memory(quests)
    return {"synced": True, **summary}


@_register_cmd("integrate")
def _cmd_integrate(ctx):
    from ecosystem.orchestrator import bootstrap
    result = bootstrap()
    # Auto-sync quests on every integrate
    quests = _load_quests()
    quest_summary = _sync_quests_to_memory(quests)
    return {"integrated": True, "bootstrap": result, "quests_synced": quest_summary["total"], "quest_summary": quest_summary}


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
