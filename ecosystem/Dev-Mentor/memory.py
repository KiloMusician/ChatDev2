"""
memory.py — Persistent agent memory system for DevMentor / Terminal Depths.

Storage: SQLite (agent_memory.db) — zero-cost, always local.

Tables:
  interactions    — every command/API call + result
  errors          — tracebacks with context and resolution
  learnings       — extracted insights and patterns
  tasks           — task queue (pending/running/done)
  generated_content — LLM outputs with hash dedup
  llm_cache       — semantic response cache (hash → response)
  skills          — capability proficiency tracking

Usage:
    from memory import Memory
    mem = Memory()
    mem.log_interaction("generate_challenge", "networking", "Packet Sniffer", success=True, duration_ms=320)
    mem.add_learning("When generating challenges, always validate JSON before returning.", tags=["llm","json"])
    stats = mem.get_stats()
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional


DB_PATH = Path(".devmentor/agent_memory.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS interactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          REAL    NOT NULL DEFAULT (unixepoch('now', 'subsec')),
    session_id  TEXT,
    type        TEXT    NOT NULL,
    input       TEXT,
    output      TEXT,
    success     INTEGER NOT NULL DEFAULT 1,
    duration_ms INTEGER DEFAULT 0,
    metadata    TEXT
);

CREATE TABLE IF NOT EXISTS errors (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          REAL    NOT NULL DEFAULT (unixepoch('now', 'subsec')),
    error_type  TEXT    NOT NULL,
    message     TEXT,
    traceback   TEXT,
    context     TEXT,
    resolved    INTEGER NOT NULL DEFAULT 0,
    resolution  TEXT
);

CREATE TABLE IF NOT EXISTS learnings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          REAL    NOT NULL DEFAULT (unixepoch('now', 'subsec')),
    insight     TEXT    NOT NULL,
    tags        TEXT,
    source      TEXT,
    confidence  REAL    DEFAULT 1.0
);

CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          REAL    NOT NULL DEFAULT (unixepoch('now', 'subsec')),
    description TEXT    NOT NULL,
    priority    INTEGER DEFAULT 5,
    status      TEXT    NOT NULL DEFAULT 'pending',
    category    TEXT,
    created_at  REAL    NOT NULL DEFAULT (unixepoch('now', 'subsec')),
    started_at  REAL,
    completed_at REAL,
    result      TEXT,
    metadata    TEXT
);

CREATE TABLE IF NOT EXISTS generated_content (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          REAL    NOT NULL DEFAULT (unixepoch('now', 'subsec')),
    content_type TEXT   NOT NULL,
    content_hash TEXT   NOT NULL UNIQUE,
    content     TEXT    NOT NULL,
    metadata    TEXT,
    used_in_game INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS llm_cache (
    prompt_hash TEXT PRIMARY KEY,
    prompt      TEXT    NOT NULL,
    response    TEXT    NOT NULL,
    backend     TEXT,
    model       TEXT,
    created_at  REAL    NOT NULL DEFAULT (unixepoch('now', 'subsec')),
    last_hit    REAL,
    hit_count   INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS skills (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    category    TEXT,
    description TEXT,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    last_used   REAL,
    confidence  REAL    DEFAULT 0.5
);

CREATE TABLE IF NOT EXISTS agent_performance (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          REAL    NOT NULL DEFAULT (unixepoch('now', 'subsec')),
    agent       TEXT    NOT NULL,
    task_type   TEXT    NOT NULL,
    success     INTEGER NOT NULL DEFAULT 1,
    duration_ms INTEGER DEFAULT 0,
    output_len  INTEGER DEFAULT 0,
    notes       TEXT
);

CREATE INDEX IF NOT EXISTS idx_agent_perf_agent ON agent_performance(agent);
CREATE INDEX IF NOT EXISTS idx_agent_perf_type  ON agent_performance(task_type);
CREATE INDEX IF NOT EXISTS idx_interactions_ts   ON interactions(ts);
CREATE INDEX IF NOT EXISTS idx_interactions_type ON interactions(type);
CREATE INDEX IF NOT EXISTS idx_errors_type       ON errors(error_type);
CREATE INDEX IF NOT EXISTS idx_errors_resolved   ON errors(resolved);
CREATE INDEX IF NOT EXISTS idx_tasks_status      ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority    ON tasks(priority DESC);
CREATE INDEX IF NOT EXISTS idx_generated_type    ON generated_content(content_type);
"""


class Memory:
    """Thread-safe persistent agent memory backed by SQLite."""

    def __init__(self, db_path: str | Path = DB_PATH):
        self._path = str(db_path)
        self._local = threading.local()
        self._init_db()

    # ── Connection management ──────────────────────────────────────────────────

    def _conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self._path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    @contextmanager
    def _db(self):
        conn = self._conn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def _init_db(self):
        with self._db() as conn:
            conn.executescript(_SCHEMA)

    @staticmethod
    def _now_ts() -> float:
        return time.time()

    # ── Interactions ──────────────────────────────────────────────────────────

    def log_interaction(
        self,
        interaction_type: str,
        input_data: Any = None,
        output_data: Any = None,
        *,
        success: bool = True,
        duration_ms: int = 0,
        session_id: str | None = None,
        metadata: dict | None = None,
    ) -> int:
        now = self._now_ts()
        row = (
            now,
            session_id,
            interaction_type,
            json.dumps(input_data) if not isinstance(input_data, str) else input_data,
            json.dumps(output_data) if not isinstance(output_data, str) else output_data,
            1 if success else 0,
            duration_ms,
            json.dumps(metadata) if metadata else None,
        )
        with self._db() as conn:
            cur = conn.execute(
                "INSERT INTO interactions (ts, session_id, type, input, output, success, duration_ms, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                row,
            )
            return cur.lastrowid

    # ── Errors ────────────────────────────────────────────────────────────────

    def log_error(
        self,
        error_type: str,
        message: str,
        traceback: str = "",
        context: str = "",
    ) -> int:
        now = self._now_ts()
        with self._db() as conn:
            cur = conn.execute(
                "INSERT INTO errors (ts, error_type, message, traceback, context) VALUES (?, ?, ?, ?, ?)",
                (now, error_type, message, traceback, context),
            )
            return cur.lastrowid

    def resolve_error(self, error_id: int, resolution: str) -> None:
        with self._db() as conn:
            conn.execute(
                "UPDATE errors SET resolved=1, resolution=? WHERE id=?",
                (resolution, error_id),
            )

    # ── Learnings ─────────────────────────────────────────────────────────────

    def add_learning(
        self,
        insight: str,
        tags: list[str] | None = None,
        source: str = "",
        confidence: float = 1.0,
    ) -> int:
        now = self._now_ts()
        with self._db() as conn:
            cur = conn.execute(
                "INSERT INTO learnings (ts, insight, tags, source, confidence) VALUES (?, ?, ?, ?, ?)",
                (now, insight, json.dumps(tags or []), source, confidence),
            )
            return cur.lastrowid

    def get_learnings(self, tag: str | None = None, limit: int = 20) -> list[dict]:
        with self._db() as conn:
            if tag:
                rows = conn.execute(
                    "SELECT * FROM learnings WHERE tags LIKE ? ORDER BY ts DESC LIMIT ?",
                    (f'%"{tag}"%', limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM learnings ORDER BY ts DESC LIMIT ?", (limit,)
                ).fetchall()
        return [dict(r) for r in rows]

    # ── Tasks ─────────────────────────────────────────────────────────────────

    def add_task(
        self,
        description: str,
        priority: int = 5,
        category: str = "general",
        metadata: dict | None = None,
    ) -> int:
        now = self._now_ts()
        with self._db() as conn:
            cur = conn.execute(
                "INSERT INTO tasks (ts, description, priority, category, created_at, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                (now, description, priority, category, now, json.dumps(metadata) if metadata else None),
            )
            return cur.lastrowid

    def get_pending_tasks(self, limit: int = 20) -> list[dict]:
        with self._db() as conn:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE status='pending' ORDER BY priority DESC, ts ASC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def start_task(self, task_id: int) -> None:
        now = self._now_ts()
        with self._db() as conn:
            conn.execute(
                "UPDATE tasks SET status='running', started_at=? WHERE id=?",
                (now, task_id),
            )

    def complete_task(self, task_id: int, result: str = "") -> None:
        now = self._now_ts()
        with self._db() as conn:
            conn.execute(
                "UPDATE tasks SET status='done', completed_at=?, result=? WHERE id=?",
                (now, result, task_id),
            )

    def fail_task(self, task_id: int, reason: str = "") -> None:
        now = self._now_ts()
        with self._db() as conn:
            conn.execute(
                "UPDATE tasks SET status='failed', completed_at=?, result=? WHERE id=?",
                (now, reason, task_id),
            )

    # ── Generated content ─────────────────────────────────────────────────────

    def store_generated(
        self,
        content_type: str,
        content: str,
        metadata: dict | None = None,
        used_in_game: bool = False,
    ) -> int | None:
        h = hashlib.sha256(content.encode()).hexdigest()[:32]
        now = self._now_ts()
        try:
            with self._db() as conn:
                cur = conn.execute(
                    "INSERT INTO generated_content (ts, content_type, content_hash, content, metadata, used_in_game) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (now, content_type, h, content, json.dumps(metadata) if metadata else None, 1 if used_in_game else 0),
                )
                return cur.lastrowid
        except sqlite3.IntegrityError:
            return None  # duplicate

    def get_generated(self, content_type: str, limit: int = 50) -> list[dict]:
        with self._db() as conn:
            rows = conn.execute(
                "SELECT * FROM generated_content WHERE content_type=? ORDER BY ts DESC LIMIT ?",
                (content_type, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── LLM cache ─────────────────────────────────────────────────────────────

    def cache_get(self, prompt: str, prefix: str = "") -> str | None:
        h = hashlib.sha256((prefix + prompt).encode()).hexdigest()
        with self._db() as conn:
            row = conn.execute(
                "SELECT response FROM llm_cache WHERE prompt_hash=?", (h,)
            ).fetchone()
            if row:
                now = self._now_ts()
                conn.execute(
                    "UPDATE llm_cache SET hit_count=hit_count+1, last_hit=? WHERE prompt_hash=?",
                    (now, h),
                )
                return row["response"]
        return None

    def cache_put(
        self,
        prompt: str,
        response: str,
        backend: str = "",
        model: str = "",
        prefix: str = "",
    ) -> None:
        h = hashlib.sha256((prefix + prompt).encode()).hexdigest()
        now = self._now_ts()
        with self._db() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO llm_cache (prompt_hash, prompt, response, backend, model, created_at, last_hit, hit_count) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (h, prompt[:1000], response, backend, model, now, now, 1),
            )

    def cache_stats(self) -> dict:
        with self._db() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as entries, SUM(hit_count) as total_hits FROM llm_cache"
            ).fetchone()
        return dict(row) if row else {}

    # ── Skills ────────────────────────────────────────────────────────────────

    def record_skill_use(self, name: str, success: bool, category: str = "") -> None:
        now = self._now_ts()
        with self._db() as conn:
            conn.execute(
                """INSERT INTO skills (name, category, success_count, failure_count, last_used, confidence)
                   VALUES (?, ?, ?, ?, ?, 0.5)
                   ON CONFLICT(name) DO UPDATE SET
                     success_count = success_count + ?,
                     failure_count = failure_count + ?,
                     last_used = ?,
                     confidence = CAST(success_count + ? AS REAL) /
                                  CAST(success_count + failure_count + 1 AS REAL)
                """,
                (
                    name, category,
                    1 if success else 0,
                    0 if success else 1,
                    now,
                    1 if success else 0,
                    0 if success else 1,
                    now,
                    1 if success else 0,
                ),
            )

    def get_weak_skills(self, threshold: float = 0.6) -> list[dict]:
        with self._db() as conn:
            rows = conn.execute(
                "SELECT * FROM skills WHERE confidence < ? AND (success_count + failure_count) >= 3 ORDER BY confidence ASC",
                (threshold,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Agent performance tracking ────────────────────────────────────────────

    def log_agent_performance(
        self,
        agent: str,
        task_type: str,
        success: bool,
        duration_ms: int = 0,
        output_len: int = 0,
        notes: str = "",
    ) -> None:
        """Record how well an agent performed on a task type."""
        now = self._now_ts()
        with self._db() as conn:
            conn.execute(
                "INSERT INTO agent_performance (ts, agent, task_type, success, duration_ms, output_len, notes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (now, agent, task_type, 1 if success else 0, duration_ms, output_len, notes),
            )

    def get_best_agent_for(self, task_type: str, candidates: list[str] | None = None) -> str | None:
        """Return the agent with highest success rate for a given task type."""
        with self._db() as conn:
            if candidates:
                placeholders = ",".join("?" * len(candidates))
                rows = conn.execute(
                    f"SELECT agent, AVG(success) as rate, COUNT(*) as runs "
                    f"FROM agent_performance WHERE task_type=? AND agent IN ({placeholders}) "
                    f"GROUP BY agent HAVING runs >= 2 ORDER BY rate DESC LIMIT 1",
                    [task_type] + candidates,
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT agent, AVG(success) as rate, COUNT(*) as runs "
                    "FROM agent_performance WHERE task_type=? "
                    "GROUP BY agent HAVING runs >= 2 ORDER BY rate DESC LIMIT 1",
                    (task_type,),
                ).fetchall()
        return dict(rows[0])["agent"] if rows else None

    def get_agent_leaderboard(self) -> list[dict]:
        """Return agent performance summary sorted by success rate."""
        with self._db() as conn:
            rows = conn.execute(
                "SELECT agent, task_type, COUNT(*) as runs, "
                "ROUND(AVG(success)*100,1) as success_pct, "
                "ROUND(AVG(duration_ms)) as avg_ms "
                "FROM agent_performance GROUP BY agent, task_type ORDER BY success_pct DESC, runs DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Semantic-style search (keyword-based) ──────────────────────────────────

    def query_similar(self, description: str, content_type: str | None = None, limit: int = 5) -> list[dict]:
        """Find stored generated content whose content overlaps with description keywords.

        Uses SQLite LIKE on content — good enough for dedup without embeddings.
        Returns list of matching records.
        """
        keywords = [w.lower() for w in description.split() if len(w) > 3][:8]
        if not keywords:
            return []

        with self._db() as conn:
            if content_type:
                base = "SELECT * FROM generated_content WHERE content_type=? AND ("
                params: list = [content_type]
            else:
                base = "SELECT * FROM generated_content WHERE ("
                params = []

            clauses = " OR ".join("LOWER(content) LIKE ?" for _ in keywords)
            params += [f"%{kw}%" for kw in keywords]

            rows = conn.execute(
                base + clauses + f") ORDER BY ts DESC LIMIT {int(limit)}",
                params,
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Code/test/doc convenience wrappers ────────────────────────────────────

    def store_code(self, name: str, code: str, test: str = "", doc: str = "") -> dict[str, int | None]:
        """Store generated code, optional test, and optional doc — all hash-deduped."""
        results = {
            "code_id": self.store_generated("code", code, metadata={"name": name}),
            "test_id": self.store_generated("test", test, metadata={"name": name}) if test else None,
            "doc_id": self.store_generated("doc", doc, metadata={"name": name}) if doc else None,
        }
        return results

    def get_code(self, name: str) -> list[dict]:
        """Retrieve all stored code entries for a given name."""
        all_code = self.get_generated("code", limit=200)
        return [
            c for c in all_code
            if c.get("metadata") and json.loads(c["metadata"] or "{}").get("name") == name
        ]

    # ── Stats & reporting ─────────────────────────────────────────────────────

    def get_stats(self, hours: int = 24) -> dict:
        since = time.time() - hours * 3600
        with self._db() as conn:
            total = conn.execute("SELECT COUNT(*) FROM interactions WHERE ts > ?", (since,)).fetchone()[0]
            success = conn.execute(
                "SELECT COUNT(*) FROM interactions WHERE ts > ? AND success=1", (since,)
            ).fetchone()[0]
            errors = conn.execute("SELECT COUNT(*) FROM errors WHERE ts > ?", (since,)).fetchone()[0]
            unresolved = conn.execute(
                "SELECT COUNT(*) FROM errors WHERE resolved=0", ()
            ).fetchone()[0]
            pending_tasks = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE status='pending'"
            ).fetchone()[0]
            cache = self.cache_stats()
            learnings_count = conn.execute("SELECT COUNT(*) FROM learnings").fetchone()[0]
            generated_count = conn.execute("SELECT COUNT(*) FROM generated_content").fetchone()[0]

        rate = round(success / total * 100, 1) if total else 0
        return {
            "period_hours": hours,
            "interactions": total,
            "success_rate_pct": rate,
            "errors_new": errors,
            "errors_unresolved": unresolved,
            "pending_tasks": pending_tasks,
            "cache_entries": cache.get("entries", 0),
            "cache_hits": cache.get("total_hits", 0),
            "learnings": learnings_count,
            "generated_content": generated_count,
        }

    def get_recent_errors(self, limit: int = 10, unresolved_only: bool = False) -> list[dict]:
        with self._db() as conn:
            q = "SELECT * FROM errors"
            if unresolved_only:
                q += " WHERE resolved=0"
            q += " ORDER BY ts DESC LIMIT ?"
            rows = conn.execute(q, (limit,)).fetchall()
        return [dict(r) for r in rows]

    def get_recent_interactions(self, hours: int = 24, type_filter: str | None = None) -> list[dict]:
        since = time.time() - hours * 3600
        with self._db() as conn:
            if type_filter:
                rows = conn.execute(
                    "SELECT * FROM interactions WHERE ts > ? AND type=? ORDER BY ts DESC",
                    (since, type_filter),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM interactions WHERE ts > ? ORDER BY ts DESC",
                    (since,),
                ).fetchall()
        return [dict(r) for r in rows]


# ── Module singleton ───────────────────────────────────────────────────────────

_instance: Memory | None = None
_lock = threading.Lock()


def get_memory() -> Memory:
    global _instance
    with _lock:
        if _instance is None:
            _instance = Memory()
    return _instance


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    mem = Memory()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"

    if cmd == "stats":
        s = mem.get_stats()
        print("=== Memory Stats (last 24h) ===")
        for k, v in s.items():
            print(f"  {k:<25} {v}")

    elif cmd == "learnings":
        for l in mem.get_learnings(limit=10):
            print(f"[{l['id']}] {l['insight'][:80]}")

    elif cmd == "errors":
        for e in mem.get_recent_errors(unresolved_only="--unresolved" in sys.argv):
            print(f"[{e['id']}] {e['error_type']}: {e['message'][:60]}")

    elif cmd == "tasks":
        for t in mem.get_pending_tasks():
            print(f"[{t['id']}] P{t['priority']} {t['description'][:70]}")

    elif cmd == "test":
        mem.log_interaction("test", "hello world", "success response", success=True, duration_ms=42)
        mem.add_learning("Test learning works correctly.", tags=["test"])
        mem.add_task("Test task from CLI", priority=3, category="test")
        mem.log_error("TestError", "A sample error message", "traceback here", "unit test")
        mem.store_generated("challenge", '{"title": "Test Challenge", "xp": 50}')
        mem.cache_put("test prompt", "cached response", backend="stub")
        cached = mem.cache_get("test prompt")
        assert cached == "cached response", "Cache miss!"
        print("All memory tests passed.")
        s = mem.get_stats()
        print(f"Stats: interactions={s['interactions']} learnings={s['learnings']}")

    else:
        print(f"Usage: python memory.py [stats|learnings|errors|tasks|test]")
