"""Dual-write helpers: append JSONL and write to DuckDB.

This module provides small helpers for producers to append an event to the
JSONL state file and immediately reflect it in DuckDB. It uses a best-effort
approach: append+fsync to JSONL then perform a single-row insert into DuckDB.

Note: true distributed atomicity requires transactional producers or an external
coordinator. This helper favors simplicity for local deployments.
"""

from __future__ import annotations

import contextlib
import json
import os
from pathlib import Path
from typing import Any

import duckdb

# Optional imports moved to top-level and guarded so linters don't flag
# import-outside-toplevel while preserving optional dependency behavior.

try:
    from .ingest import create_tables
except ImportError:
    create_tables = None  # type: ignore[assignment]


try:
    import psycopg2
    from psycopg2.extras import Json
except ImportError:
    psycopg2 = None
    Json = None


def _fsync_file(f):
    f.flush()
    os.fsync(f.fileno())


def append_to_jsonl(jsonl_path: Path, obj: dict[str, Any]) -> None:
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False) + "\n")
        _fsync_file(fh)


def insert_single_event(db_path: Path, obj: dict[str, Any]) -> None:
    """Insert a single event into DuckDB (creates tables if missing).

    This function connects to a DuckDB file, ensures tables are present via the
    project ingest helpers, and inserts a single row for the incoming event.
    It performs simple upsert logic for quest-related events.
    """
    con = duckdb.connect(str(db_path))
    try:
        # ensure tables exist (no-op if create_tables not available)
        if create_tables is not None:
            create_tables(con)

        ts = obj.get("timestamp")
        ev = obj.get("event")
        details = obj.get("details") or {}

        # insert into events
        con.execute(
            "INSERT INTO events (timestamp,event,details) VALUES (?, ?, ?)",
            [ts, ev, json.dumps(details, ensure_ascii=False)],
        )

        # if quest-like, upsert minimal fields
        if ev in ("add_quest", "update_quest_status") and isinstance(details, dict):
            q = {
                "id": details.get("id"),
                "title": details.get("title"),
                "description": details.get("description"),
                "questline": details.get("questline"),
                "status": details.get("status"),
                "created_at": details.get("created_at"),
                "updated_at": details.get("updated_at"),
                "dependencies": json.dumps(details.get("dependencies", []), ensure_ascii=False),
                "tags": json.dumps(details.get("tags", []), ensure_ascii=False),
                "history": json.dumps(details.get("history", []), ensure_ascii=False),
                "priority": details.get("priority"),
            }
            if q.get("id"):
                # delete existing then insert
                con.execute("DELETE FROM quests WHERE id = ?", [q["id"]])
                con.execute(
                    "INSERT INTO quests (id,title,description,questline,status,created_at,updated_at,dependencies,tags,history,priority) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    [
                        q["id"],
                        q["title"],
                        q["description"],
                        q["questline"],
                        q["status"],
                        q["created_at"],
                        q["updated_at"],
                        q["dependencies"],
                        q["tags"],
                        q["history"],
                        q["priority"],
                    ],
                )

        if ev == "add_questline" and isinstance(details, dict):
            name = details.get("name")
            if name:
                con.execute("DELETE FROM questlines WHERE name = ?", [name])
                con.execute(
                    "INSERT INTO questlines (name,description,tags,created_at,updated_at) VALUES (?,?,?,?,?)",
                    [
                        name,
                        details.get("description"),
                        json.dumps(details.get("tags", []), ensure_ascii=False),
                        details.get("created_at"),
                        details.get("updated_at"),
                    ],
                )
    finally:
        with contextlib.suppress(OSError):  # swallow OS-level close failures; best-effort
            con.close()


def dual_write(jsonl_path: Path, db_path: Path, obj: dict[str, Any]) -> None:
    """Append to JSONL and insert into DuckDB (best-effort atomicity).

    Order: append JSONL (fsync) -> insert into DuckDB. If DB insert fails, the
    JSONL append remains; a reconciliation pass can re-ingest missing events.
    """
    append_to_jsonl(jsonl_path, obj)
    insert_single_event(db_path, obj)


def emit_to_timescale(conninfo: str, obj: dict[str, Any]) -> None:
    """Emit an event to Timescale/Postgres using psycopg2.

    This function is a best-effort helper; it imports psycopg2 at runtime so
    the module is optional. The caller should handle retries and feature
    toggles. The example assumes a `quest_events` table exists with columns
    (timestamp, event, details).
    """
    if psycopg2 is None or Json is None:
        raise RuntimeError("psycopg2 is not installed; install requirements-timescale.txt")

    ts = obj.get("timestamp")
    ev = obj.get("event")
    details = obj.get("details") or {}

    conn = None
    try:
        conn = psycopg2.connect(conninfo)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO quest_events (timestamp, event, details) VALUES (%s, %s, %s)",
            (ts, ev, Json(details)),
        )
        conn.commit()
    finally:
        if conn:
            with contextlib.suppress(OSError):  # swallow OS-level close failures; best-effort
                conn.close()
