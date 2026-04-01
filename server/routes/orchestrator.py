"""Orchestrator API — exposes the central NuSyQ ecosystem orchestrator."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks

# Ensure ecosystem is on path
_eco = Path(__file__).resolve().parents[2] / "ecosystem"
if str(_eco) not in sys.path:
    sys.path.insert(0, str(_eco.parent))

from ecosystem.orchestrator import (
    run_cycle, get_status, _scan_system,
    enqueue, queue_stats, list_agents, list_tools,
    mem_write, mem_read,
)
from ecosystem.shared.execution_log import recent_logs
from ecosystem.shared.db import get_conn

router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])

_cycle_lock = asyncio.Lock()
_last_cycle_result: dict = {}


@router.get("/status")
async def orchestrator_status():
    """Full orchestrator status snapshot."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_status)


@router.get("/scan")
async def scan():
    """Run the ASSESS phase — quick system scan with no side effects."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _scan_system)


@router.post("/cycle")
async def trigger_cycle(background_tasks: BackgroundTasks):
    """Trigger a full CHUG cycle in the background."""
    global _last_cycle_result
    if _cycle_lock.locked():
        return {"status": "already_running", "message": "A CHUG cycle is already in progress"}

    async def _run():
        global _last_cycle_result
        async with _cycle_lock:
            loop = asyncio.get_event_loop()
            try:
                _last_cycle_result = await loop.run_in_executor(None, run_cycle)
            except Exception as e:
                _last_cycle_result = {"error": str(e), "status": "failed"}

    background_tasks.add_task(_run)
    return {"status": "started", "message": "CHUG cycle initiated"}


@router.get("/cycle/last")
async def last_cycle():
    """Get the result of the last CHUG cycle."""
    if not _last_cycle_result:
        rows = get_conn().execute(
            "SELECT * FROM chug_cycles ORDER BY cycle_num DESC LIMIT 1"
        ).fetchone()
        if rows:
            return dict(rows)
        return {"status": "no_cycles_yet"}
    return _last_cycle_result


@router.get("/cycle/history")
async def cycle_history(limit: int = 10):
    """Get recent CHUG cycle history."""
    rows = get_conn().execute(
        "SELECT * FROM chug_cycles ORDER BY cycle_num DESC LIMIT ?", (limit,)
    ).fetchall()
    return {"cycles": [dict(r) for r in rows]}


@router.get("/tasks")
async def task_queue():
    """Get the current task queue state."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, queue_stats)


@router.post("/tasks/enqueue")
async def enqueue_task(body: dict):
    """Manually enqueue a task."""
    task_id = enqueue(
        action=body.get("action", "manual"),
        repo=body.get("repo", "ecosystem"),
        agent=body.get("agent"),
        payload=body.get("payload", {}),
        priority=body.get("priority", 5),
    )
    return {"task_id": task_id, "status": "queued"}


@router.get("/agents")
async def agents():
    """List all registered agents."""
    loop = asyncio.get_event_loop()
    return {"agents": await loop.run_in_executor(None, list_agents)}


@router.get("/tools")
async def tools(repo: str = None):
    """List all registered tools, optionally filtered by repo."""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda: list_tools(repo=repo))
    return {"tools": result, "total": len(result)}


@router.get("/memory")
async def memory(namespace: str = None):
    """Read shared memory, optionally filtered by namespace."""
    from ecosystem.shared.memory import snapshot, read_namespace
    loop = asyncio.get_event_loop()
    if namespace:
        data = await loop.run_in_executor(None, lambda: read_namespace(namespace))
    else:
        data = await loop.run_in_executor(None, snapshot)
    return {"memory": data, "namespace": namespace or "all"}


@router.post("/memory/write")
async def write_memory(body: dict):
    """Write a value to shared memory."""
    key = body.get("key")
    value = body.get("value")
    namespace = body.get("namespace", "global")
    if not key:
        return {"error": "key required"}
    mem_write(key, value, namespace=namespace)
    return {"written": True, "key": key}


@router.get("/logs")
async def execution_logs(limit: int = 50, repo: str = None):
    """Get recent execution logs."""
    loop = asyncio.get_event_loop()
    logs = await loop.run_in_executor(None, lambda: recent_logs(limit=limit, repo=repo or None))
    return {"logs": logs, "count": len(logs)}


@router.get("/running")
async def is_running():
    """Check if a CHUG cycle is currently running."""
    return {"running": _cycle_lock.locked()}


# ── CHUG Daemon control ───────────────────────────────────────────────────

@router.get("/daemon/status")
async def daemon_status():
    """Get CHUG daemon state: running, interval, last/next run, cycle count."""
    try:
        from ecosystem.chug_daemon import get_state
        return get_state()
    except Exception as e:
        return {"error": str(e), "running": False}


@router.post("/daemon/start")
async def daemon_start(body: dict = {}):
    """Start the CHUG daemon. Optional: {\"interval_s\": 300}"""
    from ecosystem.chug_daemon import start
    interval = body.get("interval_s", 600)
    return start(interval_s=int(interval))


@router.post("/daemon/stop")
async def daemon_stop():
    """Stop the CHUG daemon."""
    from ecosystem.chug_daemon import stop
    return stop()


@router.post("/daemon/config")
async def daemon_config(body: dict):
    """Update daemon interval without restarting: {\"interval_s\": 300}"""
    from ecosystem.chug_daemon import set_interval
    interval = body.get("interval_s")
    if interval is None:
        return {"error": "interval_s required"}
    return set_interval(int(interval))


@router.post("/daemon/run-now")
async def daemon_run_now():
    """Trigger an immediate CHUG cycle outside the daemon schedule."""
    from ecosystem.chug_daemon import run_now_async
    try:
        report = await run_now_async()
        return {"triggered": True, "cycle": report.get("cycle"), "status": "complete"}
    except Exception as e:
        return {"triggered": False, "error": str(e)}
