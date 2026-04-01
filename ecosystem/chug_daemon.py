"""
CHUG Daemon — Continuous Habitat Upgrade Generator
====================================================
Auto-runs CHUG cycles on a configurable interval.
Runs as an asyncio background task inside the FastAPI event loop.

Default interval: 10 minutes.
Min interval: 60 seconds.
"""
from __future__ import annotations

import asyncio
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

_ECO = Path(__file__).resolve().parent
if str(_ECO.parent) not in sys.path:
    sys.path.insert(0, str(_ECO.parent))

from ecosystem.shared.memory import write as mem_write, read as mem_read
from ecosystem.shared.execution_log import log_action

log = logging.getLogger("chug_daemon")

# ── State ──────────────────────────────────────────────────────────────────

_DEFAULT_INTERVAL = 600       # seconds (10 minutes)
_MIN_INTERVAL     = 60        # hard floor
_task: Optional[asyncio.Task] = None

_state = {
    "running":        False,
    "interval_s":     _DEFAULT_INTERVAL,
    "total_cycles":   0,
    "last_run_at":    None,
    "last_run_cycle": None,
    "next_run_at":    None,
    "started_at":     None,
    "errors":         0,
    "last_error":     None,
}


def _save_state() -> None:
    mem_write("daemon.state", _state, namespace="chug_daemon")


def get_state() -> dict:
    return {**_state, "task_alive": _task is not None and not _task.done()}


# ── Daemon loop ────────────────────────────────────────────────────────────

async def _daemon_loop() -> None:
    """Main daemon loop — runs forever until cancelled."""
    _state["running"]    = True
    _state["started_at"] = datetime.utcnow().isoformat()
    _save_state()
    log.info("CHUG daemon started (interval=%ds)", _state["interval_s"])

    try:
        while True:
            interval = max(_state["interval_s"], _MIN_INTERVAL)
            next_run = datetime.utcnow() + timedelta(seconds=interval)
            _state["next_run_at"] = next_run.isoformat()
            _save_state()

            log.info("Next CHUG cycle in %ds (at %s)", interval, next_run.strftime("%H:%M:%S"))
            await asyncio.sleep(interval)

            # Run cycle in executor so it doesn't block the event loop
            loop = asyncio.get_event_loop()
            t0 = time.monotonic()
            try:
                from ecosystem.orchestrator import run_cycle
                report = await loop.run_in_executor(None, run_cycle)
                elapsed = round(time.monotonic() - t0, 2)
                _state["total_cycles"]   += 1
                _state["last_run_at"]    = datetime.utcnow().isoformat()
                _state["last_run_cycle"] = report.get("cycle")
                _save_state()
                log.info(
                    "CHUG cycle #%d complete in %.1fs | tasks=%d upgrades=%s",
                    report.get("cycle", "?"),
                    elapsed,
                    report.get("tasks_harvested", 0),
                    report.get("upgrades", {}).get("system_health", {}).get("health_pct", "?"),
                )
                log_action(
                    "chug_daemon.cycle",
                    "success",
                    repo="ecosystem",
                    agent="chug_daemon",
                    cycle=report.get("cycle"),
                    duration_ms=int(elapsed * 1000),
                    notes=f"daemon cycle #{_state['total_cycles']}",
                )
            except Exception as e:
                _state["errors"]     += 1
                _state["last_error"] = str(e)[:200]
                _save_state()
                log.error("CHUG daemon cycle error: %s", e)
                log_action("chug_daemon.cycle", "error", repo="ecosystem",
                           agent="chug_daemon", notes=str(e)[:200])

    except asyncio.CancelledError:
        _state["running"]     = False
        _state["next_run_at"] = None
        _save_state()
        log.info("CHUG daemon stopped")


# ── Public control API ─────────────────────────────────────────────────────

def start(interval_s: int = _DEFAULT_INTERVAL) -> dict:
    global _task
    if _task is not None and not _task.done():
        return {"status": "already_running", "interval_s": _state["interval_s"]}

    _state["interval_s"] = max(interval_s, _MIN_INTERVAL)
    _task = asyncio.create_task(_daemon_loop())
    _task.set_name("chug_daemon")
    log_action("chug_daemon.start", "success", repo="ecosystem", agent="chug_daemon",
               notes=f"interval={_state['interval_s']}s")
    return {"status": "started", "interval_s": _state["interval_s"]}


def stop() -> dict:
    global _task
    if _task is None or _task.done():
        _state["running"] = False
        _save_state()
        return {"status": "not_running"}
    _task.cancel()
    _task = None
    _state["running"] = False
    _save_state()
    log_action("chug_daemon.stop", "success", repo="ecosystem", agent="chug_daemon")
    return {"status": "stopped"}


def set_interval(interval_s: int) -> dict:
    clamped = max(interval_s, _MIN_INTERVAL)
    _state["interval_s"] = clamped
    _save_state()
    return {"status": "updated", "interval_s": clamped, "note": "takes effect on next sleep"}


def run_now() -> dict:
    """Immediately trigger a cycle (outside the daemon schedule)."""
    from ecosystem.task_queue_helper import enqueue_cycle
    return enqueue_cycle()


async def run_now_async() -> dict:
    """Immediately run a cycle in the executor without waiting for the schedule."""
    loop = asyncio.get_event_loop()
    from ecosystem.orchestrator import run_cycle
    report = await loop.run_in_executor(None, run_cycle)
    _state["total_cycles"]   += 1
    _state["last_run_at"]    = datetime.utcnow().isoformat()
    _state["last_run_cycle"] = report.get("cycle")
    _save_state()
    return report
