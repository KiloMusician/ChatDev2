"""Shared SQLite database — single source of truth for the entire NuSyQ ecosystem."""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "ecosystem.db"
_local = threading.local()


def get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn


def init_schema():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS task_queue (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id     TEXT UNIQUE NOT NULL,
        repo        TEXT NOT NULL,
        agent       TEXT,
        action      TEXT NOT NULL,
        payload     TEXT,
        status      TEXT NOT NULL DEFAULT 'queued',
        priority    INTEGER NOT NULL DEFAULT 5,
        created_at  TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
        result      TEXT,
        error       TEXT
    );

    CREATE TABLE IF NOT EXISTS agent_registry (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id    TEXT UNIQUE NOT NULL,
        name        TEXT NOT NULL,
        repo        TEXT,
        endpoint    TEXT,
        capabilities TEXT,
        status      TEXT NOT NULL DEFAULT 'idle',
        last_seen   TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS tool_registry (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        tool_id     TEXT UNIQUE NOT NULL,
        name        TEXT NOT NULL,
        repo        TEXT NOT NULL,
        path        TEXT,
        description TEXT,
        input_schema TEXT,
        enabled     INTEGER NOT NULL DEFAULT 1,
        registered_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS execution_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        log_id      TEXT UNIQUE NOT NULL,
        cycle       INTEGER,
        repo        TEXT,
        agent       TEXT,
        action      TEXT NOT NULL,
        status      TEXT NOT NULL,
        duration_ms INTEGER,
        notes       TEXT,
        created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS shared_memory (
        key         TEXT PRIMARY KEY,
        value       TEXT,
        namespace   TEXT NOT NULL DEFAULT 'global',
        updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS chug_cycles (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        cycle_num   INTEGER UNIQUE NOT NULL,
        phase       TEXT NOT NULL,
        status      TEXT NOT NULL DEFAULT 'running',
        scan_result TEXT,
        actions     TEXT,
        improvements TEXT,
        started_at  TEXT NOT NULL DEFAULT (datetime('now')),
        completed_at TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_task_status ON task_queue(status);
    CREATE INDEX IF NOT EXISTS idx_exec_log_cycle ON execution_log(cycle);
    CREATE INDEX IF NOT EXISTS idx_exec_log_repo ON execution_log(repo);
    CREATE INDEX IF NOT EXISTS idx_memory_ns ON shared_memory(namespace);
    """)
    conn.commit()


init_schema()
