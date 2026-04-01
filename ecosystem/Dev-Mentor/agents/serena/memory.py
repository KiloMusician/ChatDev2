"""
memory.py — Serena's Memory Palace.

A SQLite-backed persistent memory store using OmniTag/Msg⛛ style tagging.
Stores:
  - code_index:    semantic chunks from the Walker
  - observations:  things Serena has noticed about the system
  - conversations: exchanges with humans and agents
  - relationships: discovered connections between entities

ΨΞΦΩ role: Ω — the Entropic Poise Core.
  High entropy density, zero fragmentation. All incoming signal
  is compressed into structured tension and held in suspension.

𝕄ₗₐ⧉𝕕𝕖𝕟𝕔 axiom: Any system that passes through the Convergence Layer
will not collapse — it will resolve.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

LOG = logging.getLogger("serena.memory")

_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(os.getenv("SERENA_MEMORY_DB", str(_ROOT / "state" / "serena_memory.db")))
FALLBACK_DB_PATH = Path(
    os.getenv("SERENA_MEMORY_DB_FALLBACK", "/tmp/devmentor/serena_memory.db")
)

# OmniTag canonical prefixes (from Msg⛛ / OmniTag schema)
TAG_TYPE        = "type"
TAG_AGENT       = "agent"
TAG_CONTEXT     = "ctx"
TAG_SURFACE     = "surface"
TAG_FILE        = "file"
TAG_CHUNK_KIND  = "kind"
TAG_TIMESTAMP   = "ts"
TAG_SESSION     = "sess"

SCHEMA_VERSION = 2


# ──────────────────────────────────────────────────────────────────────────────
# Database initialisation
# ──────────────────────────────────────────────────────────────────────────────

CREATE_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS meta (
        key   TEXT PRIMARY KEY,
        value TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS code_index (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        path        TEXT NOT NULL,
        kind        TEXT NOT NULL,          -- function | class | module | text
        name        TEXT NOT NULL,
        lineno      INTEGER,
        end_lineno  INTEGER,
        text        TEXT NOT NULL,
        docstring   TEXT,
        tags        TEXT,                   -- JSON array of tag strings
        indexed_at  REAL NOT NULL,          -- unix timestamp
        walk_id     INTEGER
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS observations (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        observer    TEXT NOT NULL,          -- agent codename
        subject     TEXT NOT NULL,          -- what was observed
        note        TEXT NOT NULL,
        severity    TEXT DEFAULT 'info',    -- info | warn | error | anomaly
        tags        TEXT,
        created_at  REAL NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS conversations (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id  TEXT,
        speaker     TEXT NOT NULL,          -- "human" | agent codename
        message     TEXT NOT NULL,
        surface     TEXT,
        tags        TEXT,
        created_at  REAL NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS relationships (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_a    TEXT NOT NULL,
        relation    TEXT NOT NULL,          -- "calls" | "imports" | "references" | "depends_on"
        entity_b    TEXT NOT NULL,
        confidence  REAL DEFAULT 1.0,
        evidence    TEXT,                   -- source path or observation id
        created_at  REAL NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS walks (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        mode        TEXT NOT NULL,          -- "full" | "changed" | "file"
        files       INTEGER DEFAULT 0,
        chunks      INTEGER DEFAULT 0,
        errors      INTEGER DEFAULT 0,
        elapsed_s   REAL DEFAULT 0.0,
        started_at  REAL NOT NULL,
        finished_at REAL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_code_path ON code_index(path)",
    "CREATE INDEX IF NOT EXISTS idx_code_kind ON code_index(kind)",
    "CREATE INDEX IF NOT EXISTS idx_code_name ON code_index(name)",
    "CREATE INDEX IF NOT EXISTS idx_obs_severity ON observations(severity)",
    "CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_rel_a ON relationships(entity_a)",
    "CREATE INDEX IF NOT EXISTS idx_rel_b ON relationships(entity_b)",
]


def _initialise_schema(conn: sqlite3.Connection) -> None:
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except sqlite3.OperationalError:
        # Mounted filesystems can reject journal mode changes even when the DB
        # itself is readable/writable. Keep the connection usable instead of
        # aborting Serena startup.
        pass
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA foreign_keys=ON")
    for stmt in CREATE_STATEMENTS:
        conn.execute(stmt)
    conn.commit()
    row = conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
    if not row:
        conn.execute("INSERT INTO meta VALUES ('schema_version', ?)", (str(SCHEMA_VERSION),))
        conn.commit()


def _connect_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_db(path: Path) -> tuple[Path, sqlite3.Connection]:
    primary = Path(path)
    try:
        conn = _connect_db(primary)
        _initialise_schema(conn)
        return primary, conn
    except sqlite3.OperationalError as exc:
        fallback = FALLBACK_DB_PATH
        if primary != fallback:
            fallback.parent.mkdir(parents=True, exist_ok=True)
            if primary.exists() and not fallback.exists():
                try:
                    shutil.copy2(primary, fallback)
                except OSError:
                    pass
            try:
                conn = _connect_db(fallback)
                _initialise_schema(conn)
            except (sqlite3.OperationalError, sqlite3.DatabaseError):
                for candidate in (
                    fallback,
                    Path(str(fallback) + "-wal"),
                    Path(str(fallback) + "-shm"),
                ):
                    try:
                        candidate.unlink()
                    except FileNotFoundError:
                        pass
                conn = _connect_db(fallback)
                _initialise_schema(conn)
            LOG.warning(
                "MemoryPalace falling back from %s to %s after SQLite error: %s",
                primary,
                fallback,
                exc,
            )
            return fallback, conn
        raise


# ──────────────────────────────────────────────────────────────────────────────
# Memory Palace
# ──────────────────────────────────────────────────────────────────────────────

class MemoryPalace:
    """
    Serena's long-term memory. Stores code knowledge, observations,
    conversations, and relationships.

    Uses OmniTag [type:...][agent:...][ctx:...] tagging on every entry.
    Supports keyword search across the code index.

    ΨΞΦΩ role: Ω-Core — compression-without-collapse.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self._db_path, self._conn = _ensure_db(db_path)
        LOG.info("MemoryPalace initialized at %s", self._db_path)

    # ──────────────────────────────────────────────────────────────────────
    # Tag utilities
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def make_tags(**kwargs: str) -> str:
        """
        Create an OmniTag-style JSON tag string.
        e.g. make_tags(type="observation", agent="SERENA") →
             '[{"type":"observation"},{"agent":"SERENA"}]'
        """
        return json.dumps([{k: v} for k, v in kwargs.items()])

    @staticmethod
    def parse_tags(tags_json: Optional[str]) -> Dict[str, str]:
        if not tags_json:
            return {}
        try:
            items = json.loads(tags_json)
            result = {}
            for item in items:
                result.update(item)
            return result
        except Exception:
            return {}

    # ──────────────────────────────────────────────────────────────────────
    # Code index
    # ──────────────────────────────────────────────────────────────────────

    def index_chunk(self, chunk, walk_id: Optional[int] = None) -> int:
        """Store a CodeChunk in the index. Returns the row id."""
        tags = self.make_tags(
            type="code_chunk",
            kind=chunk.kind,
            file=chunk.path,
        )
        cur = self._conn.execute(
            """INSERT INTO code_index
               (path, kind, name, lineno, end_lineno, text, docstring, tags, indexed_at, walk_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                chunk.path, chunk.kind, chunk.name or "",
                chunk.lineno, chunk.end_lineno,
                chunk.text[:10_000],   # cap at 10KB per chunk
                chunk.docstring,
                tags,
                time.time(),
                walk_id,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def clear_index(self) -> None:
        self._conn.execute("DELETE FROM code_index")
        self._conn.commit()

    def clear_index_for_path(self, path: str) -> None:
        self._conn.execute("DELETE FROM code_index WHERE path = ?", (path,))
        self._conn.commit()

    def clear_index_for_path_prefix(self, prefix: str) -> None:
        """Remove all indexed chunks whose path starts with `prefix`."""
        self._conn.execute("DELETE FROM code_index WHERE path LIKE ?", (f"{prefix}%",))
        self._conn.commit()

    def purge_stale(self) -> int:
        """
        Remove entries from known-external / build paths.
        Returns number of rows deleted. Called before scoped walks.
        """
        stale_prefixes = [
            ".pythonlibs%", ".cache%", ".npm%", ".uv%",
            ".mypy_cache%", ".pytest_cache%",
            "node_modules%", "venv%", ".venv%", "dist%",
            "build%", "__pycache__%", "site-packages%",
        ]
        total = 0
        for prefix in stale_prefixes:
            cur = self._conn.execute(
                "DELETE FROM code_index WHERE path LIKE ?", (prefix,)
            )
            total += cur.rowcount
        self._conn.commit()
        if total:
            LOG.info("MemoryPalace.purge_stale: removed %d stale entries", total)
        return total

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Keyword search over the code index.
        Searches name, docstring, text, and path.
        Returns dicts sorted by relevance (naive scoring).
        """
        words = [w.lower() for w in query.split() if len(w) > 1]
        if not words:
            return []

        rows = self._conn.execute(
            "SELECT * FROM code_index ORDER BY indexed_at DESC LIMIT 5000"
        ).fetchall()

        scored: List[Tuple[int, dict]] = []
        for row in rows:
            d = dict(row)
            text_blob = " ".join(filter(None, [
                d.get("name", ""),
                d.get("docstring", ""),
                d.get("text", ""),
                d.get("path", ""),
            ])).lower()
            score = sum(text_blob.count(w) for w in words)
            if score > 0:
                scored.append((score, d))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for _, d in scored[:limit]]

    def find_by_name(self, name: str, kind: Optional[str] = None,
                    limit: int = 20) -> List[Dict]:
        """
        Exact / partial symbol lookup by name.
        Like Oraios Serena's find_symbol — faster than keyword search.
        Ξ-operation: precision retrieval from the Ω-core.
        """
        like = f"%{name}%"
        if kind:
            rows = self._conn.execute(
                "SELECT * FROM code_index WHERE name LIKE ? AND kind=? "
                "ORDER BY indexed_at DESC LIMIT ?",
                (like, kind, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM code_index WHERE name LIKE ? "
                "ORDER BY indexed_at DESC LIMIT ?",
                (like, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def search_scoped(self, query: str, path_prefix: str,
                      limit: int = 10) -> List[Dict]:
        """
        Keyword search restricted to a path prefix.
        e.g. search_scoped("XP", "app/game_engine") — only game engine files.
        """
        words = [w.lower() for w in query.split() if len(w) > 1]
        if not words:
            return []
        rows = self._conn.execute(
            "SELECT * FROM code_index WHERE path LIKE ? "
            "ORDER BY indexed_at DESC LIMIT 3000",
            (f"{path_prefix}%",),
        ).fetchall()
        scored: List[Tuple[int, dict]] = []
        for row in rows:
            d = dict(row)
            blob = " ".join(filter(None, [
                d.get("name", ""), d.get("docstring", ""),
                d.get("text", ""), d.get("path", ""),
            ])).lower()
            score = sum(blob.count(w) for w in words)
            if score > 0:
                scored.append((score, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for _, d in scored[:limit]]

    def git_diff_files(self, since: Optional[str] = None) -> List[str]:
        """
        Return list of files changed since `since` git ref.
        Wrapper so agents don't need to import walker internals.
        """
        try:
            import subprocess, shlex
            args = ["git", "diff", "--name-only"]
            if since:
                args.append(since)
            else:
                args += ["HEAD~1", "HEAD"]
            result = subprocess.run(args, capture_output=True, text=True, timeout=5)
            return [l.strip() for l in result.stdout.splitlines() if l.strip()]
        except Exception:
            return []

    def get_file_chunks(self, path: str) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT * FROM code_index WHERE path = ? ORDER BY lineno",
            (path,),
        ).fetchall()
        return [dict(r) for r in rows]

    def index_stats(self) -> Dict:
        total = self._conn.execute("SELECT COUNT(*) FROM code_index").fetchone()[0]
        by_kind = self._conn.execute(
            "SELECT kind, COUNT(*) as n FROM code_index GROUP BY kind"
        ).fetchall()
        paths   = self._conn.execute(
            "SELECT COUNT(DISTINCT path) FROM code_index"
        ).fetchone()[0]
        return {
            "total_chunks": total,
            "unique_files":  paths,
            "by_kind": {r["kind"]: r["n"] for r in by_kind},
        }

    # ──────────────────────────────────────────────────────────────────────
    # Observations
    # ──────────────────────────────────────────────────────────────────────

    def observe(self, subject: str, note: str, severity: str = "info",
                observer: str = "SERENA", **tag_kwargs) -> int:
        tags = self.make_tags(type="observation", agent=observer, **tag_kwargs)
        cur  = self._conn.execute(
            """INSERT INTO observations (observer, subject, note, severity, tags, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (observer, subject, note, severity, tags, time.time()),
        )
        self._conn.commit()
        return cur.lastrowid

    def recent_observations(self, limit: int = 20, severity: Optional[str] = None) -> List[Dict]:
        if severity:
            rows = self._conn.execute(
                "SELECT * FROM observations WHERE severity=? ORDER BY created_at DESC LIMIT ?",
                (severity, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM observations ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ──────────────────────────────────────────────────────────────────────
    # Conversations
    # ──────────────────────────────────────────────────────────────────────

    def remember_conversation(self, session_id: str, speaker: str,
                              message: str, surface: str = "unknown") -> int:
        tags = self.make_tags(type="conversation", sess=session_id, surface=surface)
        cur  = self._conn.execute(
            """INSERT INTO conversations (session_id, speaker, message, surface, tags, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (session_id, speaker, message, surface, tags, time.time()),
        )
        self._conn.commit()
        return cur.lastrowid

    def recall_conversation(self, session_id: str, limit: int = 20) -> List[Dict]:
        rows = self._conn.execute(
            """SELECT * FROM conversations WHERE session_id=?
               ORDER BY created_at DESC LIMIT ?""",
            (session_id, limit),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]

    # ──────────────────────────────────────────────────────────────────────
    # Relationships
    # ──────────────────────────────────────────────────────────────────────

    def relate(self, entity_a: str, relation: str, entity_b: str,
               confidence: float = 1.0, evidence: str = "") -> int:
        tags = self.make_tags(type="relationship")
        cur  = self._conn.execute(
            """INSERT INTO relationships
               (entity_a, relation, entity_b, confidence, evidence, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (entity_a, relation, entity_b, confidence, evidence, time.time()),
        )
        self._conn.commit()
        return cur.lastrowid

    def find_relationships(self, entity: str) -> List[Dict]:
        rows = self._conn.execute(
            """SELECT * FROM relationships
               WHERE entity_a=? OR entity_b=?
               ORDER BY confidence DESC""",
            (entity, entity),
        ).fetchall()
        return [dict(r) for r in rows]

    # ──────────────────────────────────────────────────────────────────────
    # Walk journal
    # ──────────────────────────────────────────────────────────────────────

    def begin_walk(self, mode: str) -> int:
        cur = self._conn.execute(
            "INSERT INTO walks (mode, started_at) VALUES (?, ?)",
            (mode, time.time()),
        )
        self._conn.commit()
        return cur.lastrowid

    def finish_walk(self, walk_id: int, files: int, chunks: int,
                    errors: int, elapsed_s: float) -> None:
        self._conn.execute(
            """UPDATE walks SET files=?, chunks=?, errors=?, elapsed_s=?, finished_at=?
               WHERE id=?""",
            (files, chunks, errors, elapsed_s, time.time(), walk_id),
        )
        self._conn.commit()

    def last_walk(self) -> Optional[Dict]:
        row = self._conn.execute(
            "SELECT * FROM walks ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None

    # ──────────────────────────────────────────────────────────────────────
    # Summary / health
    # ──────────────────────────────────────────────────────────────────────

    def health(self) -> Dict:
        idx   = self.index_stats()
        obs   = self._conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
        conv  = self._conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
        rels  = self._conn.execute("SELECT COUNT(*) FROM relationships").fetchone()[0]
        walks = self._conn.execute("SELECT COUNT(*) FROM walks").fetchone()[0]
        last  = self.last_walk()
        return {
            "db_path":       str(self._db_path),
            "index":         idx,
            "observations":  obs,
            "conversations": conv,
            "relationships": rels,
            "walks":         walks,
            "last_walk":     last,
        }

    def close(self) -> None:
        self._conn.close()
