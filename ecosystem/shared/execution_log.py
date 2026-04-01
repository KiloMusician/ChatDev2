"""Execution logger — structured log of all agent actions across the ecosystem."""
from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from typing import Any, List, Optional

from .db import get_conn


def log_action(
    action: str,
    status: str,
    repo: str = "ecosystem",
    agent: Optional[str] = None,
    cycle: Optional[int] = None,
    duration_ms: Optional[int] = None,
    notes: Optional[str] = None,
) -> str:
    log_id = str(uuid.uuid4())
    get_conn().execute(
        """INSERT INTO execution_log (log_id, cycle, repo, agent, action, status, duration_ms, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (log_id, cycle, repo, agent, action, status, duration_ms, notes),
    )
    get_conn().commit()
    return log_id


@contextmanager
def timed_action(action: str, repo: str, agent: str = None, cycle: int = None):
    """Context manager that logs an action with timing."""
    start = time.monotonic()
    log_id = None
    try:
        yield
        duration_ms = int((time.monotonic() - start) * 1000)
        log_id = log_action(action, "success", repo=repo, agent=agent, cycle=cycle, duration_ms=duration_ms)
    except Exception as e:
        duration_ms = int((time.monotonic() - start) * 1000)
        log_action(action, "error", repo=repo, agent=agent, cycle=cycle, duration_ms=duration_ms, notes=str(e)[:200])
        raise


def recent_logs(limit: int = 50, repo: Optional[str] = None, cycle: Optional[int] = None) -> List[dict]:
    q = "SELECT * FROM execution_log WHERE 1=1"
    args: list = []
    if repo:
        q += " AND repo=?"
        args.append(repo)
    if cycle is not None:
        q += " AND cycle=?"
        args.append(cycle)
    q += " ORDER BY created_at DESC LIMIT ?"
    args.append(limit)
    return [dict(r) for r in get_conn().execute(q, args).fetchall()]


def cycle_summary(cycle: int) -> dict:
    rows = get_conn().execute(
        "SELECT repo, agent, action, status, duration_ms FROM execution_log WHERE cycle=?",
        (cycle,),
    ).fetchall()
    success = sum(1 for r in rows if r["status"] == "success")
    errors = sum(1 for r in rows if r["status"] == "error")
    return {
        "cycle": cycle,
        "total_actions": len(rows),
        "success": success,
        "errors": errors,
        "actions": [dict(r) for r in rows],
    }
