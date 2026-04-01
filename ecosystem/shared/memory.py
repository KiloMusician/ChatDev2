"""Shared memory layer — all agents can read/write key-value context across sessions."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from .db import get_conn


def write(key: str, value: Any, namespace: str = "global") -> None:
    conn = get_conn()
    conn.execute(
        """INSERT INTO shared_memory (key, value, namespace, updated_at)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(key) DO UPDATE SET
               value=excluded.value,
               namespace=excluded.namespace,
               updated_at=excluded.updated_at""",
        (key, json.dumps(value), namespace, datetime.utcnow().isoformat()),
    )
    conn.commit()


def read(key: str, default: Any = None) -> Any:
    row = get_conn().execute(
        "SELECT value FROM shared_memory WHERE key=?", (key,)
    ).fetchone()
    if row is None:
        return default
    try:
        return json.loads(row[0])
    except Exception:
        return row[0]


def read_namespace(namespace: str) -> dict[str, Any]:
    rows = get_conn().execute(
        "SELECT key, value, updated_at FROM shared_memory WHERE namespace=? ORDER BY updated_at DESC",
        (namespace,),
    ).fetchall()
    return {r["key"]: {"value": json.loads(r["value"]), "updated_at": r["updated_at"]} for r in rows}


def delete(key: str) -> None:
    get_conn().execute("DELETE FROM shared_memory WHERE key=?", (key,))
    get_conn().commit()


def snapshot() -> dict:
    rows = get_conn().execute(
        "SELECT key, value, namespace, updated_at FROM shared_memory ORDER BY namespace, key"
    ).fetchall()
    return [
        {"key": r["key"], "value": json.loads(r["value"]), "namespace": r["namespace"], "updated_at": r["updated_at"]}
        for r in rows
    ]
