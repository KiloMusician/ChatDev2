"""
Model Registry — SQLite-backed catalog of all models in the ΔΨΣ ecosystem.

Msg⛛ protocol: every significant operation is tagged [ML⛛{registry}].

Auto-seeds from config/models.yaml on first run.
Discovers live Ollama models via GET http://localhost:11434/api/tags.
Stores: id, name, type, source, status, capabilities (JSON), last_seen.

REST API (mounted by main.py at /api/models):
  GET  /api/models          — list all models
  GET  /api/models/{id}     — single model detail
  POST /api/models/register — add / update a model
  POST /api/models/discover — trigger live Ollama discovery
  GET  /api/models/status   — registry health
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests
import yaml

# ── Paths ────────────────────────────────────────────────────────────────────

_ROOT = Path(__file__).resolve().parent.parent
_DB_PATH = _ROOT / "state" / "model_registry.db"
_YAML_PATH = _ROOT / "config" / "models.yaml"

_OLLAMA_BASE = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

_lock = threading.Lock()


# ── Schema ────────────────────────────────────────────────────────────────────

_DDL = """
CREATE TABLE IF NOT EXISTS models (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    model_type      TEXT DEFAULT 'generation',
    source          TEXT DEFAULT 'ollama',
    endpoint        TEXT,
    capabilities    TEXT,   -- JSON list
    context_length  INTEGER DEFAULT 4096,
    status          TEXT DEFAULT 'unknown',
    quantization    TEXT,
    tags            TEXT,   -- JSON list
    priority        INTEGER DEFAULT 50,
    description     TEXT,
    last_seen       REAL,
    registered_at   REAL
);

CREATE TABLE IF NOT EXISTS inference_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id    TEXT,
    task_type   TEXT,
    prompt_len  INTEGER,
    response_len INTEGER,
    latency_ms  REAL,
    backend     TEXT,
    tags        TEXT,   -- Msg⛛ envelope JSON
    ts          REAL
);
"""


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def _init_db() -> None:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _conn() as c:
        c.executescript(_DDL)


# ── Seed from YAML ────────────────────────────────────────────────────────────

def _seed_from_yaml() -> int:
    if not _YAML_PATH.exists():
        return 0
    data = yaml.safe_load(_YAML_PATH.read_text())
    models = data.get("models", [])
    count = 0
    with _conn() as c:
        for m in models:
            mid = m.get("id", "")
            if not mid:
                continue
            caps = json.dumps(m.get("capabilities", []))
            tags = json.dumps(m.get("suitable_for", []))
            c.execute(
                """INSERT OR IGNORE INTO models
                   (id, name, model_type, source, endpoint, capabilities,
                    context_length, status, priority, description, tags,
                    registered_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    mid,
                    m.get("name", mid),
                    _infer_type(m.get("capabilities", [])),
                    m.get("provider", "ollama"),
                    m.get("endpoint", ""),
                    caps,
                    m.get("context_length", 4096),
                    "registered",
                    m.get("priority", 50),
                    m.get("description", ""),
                    tags,
                    time.time(),
                ),
            )
            count += 1
        c.commit()
    return count


def _infer_type(caps: list) -> str:
    if "embedding" in caps:
        return "embedding"
    if "vision" in caps:
        return "vision"
    if "code" in caps:
        return "code"
    return "generation"


# ── Live Ollama Discovery ─────────────────────────────────────────────────────

def discover_ollama(timeout: int = 3) -> List[Dict]:
    """Query Ollama for running models, upsert into registry."""
    found = []
    try:
        resp = requests.get(f"{_OLLAMA_BASE}/api/tags", timeout=timeout)
        if resp.status_code != 200:
            return found
        data = resp.json()
    except Exception:
        return found

    models = data.get("models", [])
    now = time.time()
    with _conn() as c:
        for m in models:
            mid = m.get("name", "")
            if not mid:
                continue
            mtype = _infer_type([])
            if "embed" in mid or "nomic" in mid or "mxbai" in mid:
                mtype = "embedding"
            elif "code" in mid or "coder" in mid:
                mtype = "code"

            size_bytes = m.get("size", 0)
            size_gb = round(size_bytes / 1e9, 1)

            c.execute(
                """INSERT INTO models
                       (id, name, model_type, source, endpoint, capabilities,
                        status, description, last_seen, registered_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(id) DO UPDATE SET
                       status='active', last_seen=excluded.last_seen""",
                (
                    mid,
                    mid,
                    mtype,
                    "ollama",
                    f"{_OLLAMA_BASE}/api/chat",
                    json.dumps(["chat", mtype]),
                    "active",
                    f"Ollama model — {size_gb}GB",
                    now,
                    now,
                ),
            )
            found.append({"id": mid, "type": mtype, "size_gb": size_gb})
        c.commit()

    _log_ml_event("discover", {"found": len(found), "models": [f["id"] for f in found]})
    return found


# ── Query helpers ─────────────────────────────────────────────────────────────

def list_models(status_filter: Optional[str] = None) -> List[Dict]:
    with _conn() as c:
        if status_filter:
            rows = c.execute(
                "SELECT * FROM models WHERE status=? ORDER BY priority DESC", (status_filter,)
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM models ORDER BY priority DESC"
            ).fetchall()
    return [dict(r) for r in rows]


def get_model(model_id: str) -> Optional[Dict]:
    with _conn() as c:
        row = c.execute("SELECT * FROM models WHERE id=?", (model_id,)).fetchone()
    return dict(row) if row else None


def register_model(data: Dict) -> str:
    mid = data.get("id") or data.get("name", "unknown").lower().replace(" ", "-")
    now = time.time()
    with _conn() as c:
        c.execute(
            """INSERT INTO models
               (id, name, model_type, source, endpoint, capabilities,
                status, description, last_seen, registered_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET
                   status=excluded.status,
                   last_seen=excluded.last_seen""",
            (
                mid,
                data.get("name", mid),
                data.get("type", "generation"),
                data.get("source", "custom"),
                data.get("endpoint", ""),
                json.dumps(data.get("capabilities", [])),
                data.get("status", "registered"),
                data.get("description", ""),
                now,
                now,
            ),
        )
        c.commit()
    _log_ml_event("register", {"model_id": mid})
    return mid


def registry_stats() -> Dict:
    with _conn() as c:
        total = c.execute("SELECT COUNT(*) FROM models").fetchone()[0]
        active = c.execute("SELECT COUNT(*) FROM models WHERE status='active'").fetchone()[0]
        by_type = c.execute(
            "SELECT model_type, COUNT(*) as n FROM models GROUP BY model_type"
        ).fetchall()
        recent_inf = c.execute(
            "SELECT COUNT(*) FROM inference_log WHERE ts > ?", (time.time() - 3600,)
        ).fetchone()[0]
    return {
        "total": total,
        "active": active,
        "by_type": {r["model_type"]: r["n"] for r in by_type},
        "inferences_last_hour": recent_inf,
    }


# ── Msg⛛ logging ──────────────────────────────────────────────────────────────

def _log_ml_event(event_type: str, meta: Dict) -> None:
    envelope = {
        "tag": f"[ML⛛{{{event_type}}}]",
        "ts": time.time(),
        **meta,
    }
    try:
        _ROOT.joinpath("state", "ml_events.jsonl").parent.mkdir(parents=True, exist_ok=True)
        with open(_ROOT / "state" / "ml_events.jsonl", "a") as f:
            f.write(json.dumps(envelope) + "\n")
    except Exception:
        pass


def log_inference(model_id: str, task_type: str, prompt_len: int,
                  response_len: int, latency_ms: float, backend: str) -> None:
    envelope = {
        "tag": "[ML⛛{inference}]",
        "model_id": model_id,
        "task_type": task_type,
        "latency_ms": latency_ms,
        "ts": time.time(),
    }
    with _conn() as c:
        c.execute(
            """INSERT INTO inference_log
               (model_id, task_type, prompt_len, response_len, latency_ms, backend, tags, ts)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                model_id, task_type, prompt_len, response_len,
                latency_ms, backend, json.dumps(envelope), time.time(),
            ),
        )
        c.commit()
    _log_ml_event("inference", envelope)


# ── Startup ───────────────────────────────────────────────────────────────────

def initialise() -> Dict:
    _init_db()
    seeded = _seed_from_yaml()
    discovered = discover_ollama()
    stats = registry_stats()
    return {
        "seeded_from_yaml": seeded,
        "discovered_live": len(discovered),
        "total_in_registry": stats["total"],
        "active": stats["active"],
    }
