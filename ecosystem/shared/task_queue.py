"""Shared task queue — repos submit tasks here; the orchestrator picks them up."""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, List, Optional

from .db import get_conn


def enqueue(
    action: str,
    repo: str,
    agent: Optional[str] = None,
    payload: Any = None,
    priority: int = 5,
) -> str:
    task_id = str(uuid.uuid4())
    get_conn().execute(
        """INSERT INTO task_queue (task_id, repo, agent, action, payload, priority)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (task_id, repo, agent, action, json.dumps(payload or {}), priority),
    )
    get_conn().commit()
    return task_id


def dequeue(limit: int = 1) -> List[dict]:
    rows = get_conn().execute(
        """SELECT * FROM task_queue WHERE status='queued'
           ORDER BY priority ASC, created_at ASC LIMIT ?""",
        (limit,),
    ).fetchall()
    out = []
    for row in rows:
        get_conn().execute(
            "UPDATE task_queue SET status='running', updated_at=? WHERE task_id=?",
            (datetime.utcnow().isoformat(), row["task_id"]),
        )
        get_conn().commit()
        d = dict(row)
        d["payload"] = json.loads(d.get("payload") or "{}")
        out.append(d)
    return out


def complete(task_id: str, result: Any = None) -> None:
    get_conn().execute(
        "UPDATE task_queue SET status='done', result=?, updated_at=? WHERE task_id=?",
        (json.dumps(result), datetime.utcnow().isoformat(), task_id),
    )
    get_conn().commit()


def fail(task_id: str, error: str) -> None:
    get_conn().execute(
        "UPDATE task_queue SET status='failed', error=?, updated_at=? WHERE task_id=?",
        (error, datetime.utcnow().isoformat(), task_id),
    )
    get_conn().commit()


def queue_stats() -> dict:
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM task_queue").fetchone()[0]
    by_status = {
        row["status"]: row["cnt"]
        for row in conn.execute(
            "SELECT status, COUNT(*) as cnt FROM task_queue GROUP BY status"
        ).fetchall()
    }
    recent = [
        dict(r)
        for r in conn.execute(
            "SELECT task_id, repo, agent, action, status, created_at FROM task_queue ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
    ]
    return {"total": total, "by_status": by_status, "recent": recent}
