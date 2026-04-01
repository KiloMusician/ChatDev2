"""
Service Registry — The Switchboard.

Every service in the ΔΨΣ ecosystem registers here on startup, publishing:
  - name, host, port, health_endpoint, capabilities, tags

The Gateway (port 5000 FastAPI app) consults this to know what's running.
The Telephone Operator pattern: services are extensions, the registry is the
switchboard, and callers just dial 5000.

Msg⛛ tagging: [SVC⛛{registry}]

REST API (mounted by main.py at /api/services):
  GET  /api/services              — list all services (optional ?cap= filter)
  GET  /api/services/{name}       — single service detail
  POST /api/services/register     — register or heartbeat a service
  POST /api/services/deregister   — remove a service
  GET  /api/services/health       — run health checks on all services
  GET  /api/services/gateway      — routing table as gateway would see it
"""
from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional

import requests

_ROOT = Path(__file__).resolve().parent.parent.parent
_DB_PATH = _ROOT / "state" / "service_registry.db"

_STALE_SECONDS = 300  # 5 minutes without heartbeat → stale
_AGENT_STALE_SECONDS = 90  # 90 seconds without heartbeat → stale
_PROCESS_STALE_SECONDS = 300  # 5 minutes without process sighting → stale

_DDL = """
CREATE TABLE IF NOT EXISTS services (
    name             TEXT PRIMARY KEY,
    host             TEXT NOT NULL DEFAULT 'localhost',
    port             INTEGER NOT NULL,
    health_endpoint  TEXT DEFAULT '/health',
    capabilities     TEXT,   -- JSON list
    tags             TEXT,   -- JSON list
    description      TEXT,
    registered_at    REAL,
    last_heartbeat   REAL
);

CREATE TABLE IF NOT EXISTS agents (
    agent_id         TEXT PRIMARY KEY,
    name             TEXT NOT NULL,
    kind             TEXT NOT NULL DEFAULT 'agent',
    capabilities     TEXT,
    channels         TEXT,
    tags             TEXT,
    description      TEXT,
    metadata         TEXT,
    registered_at    REAL,
    last_heartbeat   REAL,
    status           TEXT NOT NULL DEFAULT 'online'
);

CREATE TABLE IF NOT EXISTS processes (
    pid            INTEGER PRIMARY KEY,
    name           TEXT NOT NULL,
    start_time     TEXT,
    last_seen      REAL,
    is_ecosystem   INTEGER NOT NULL DEFAULT 0,
    metadata       TEXT
);

CREATE INDEX IF NOT EXISTS idx_processes_last_seen ON processes(last_seen);
CREATE INDEX IF NOT EXISTS idx_processes_name ON processes(name);

CREATE TABLE IF NOT EXISTS gateway_events (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    event    TEXT,
    service  TEXT,
    detail   TEXT,
    ts       REAL
);
"""


@contextmanager
def _conn():
    c = sqlite3.connect(str(_DB_PATH), check_same_thread=False, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    try:
        yield c
    finally:
        c.close()


def _init_db() -> None:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _conn() as c:
        c.executescript(_DDL)
        c.commit()


# ── Write ─────────────────────────────────────────────────────────────────────

def register(
    name: str,
    port: int,
    host: str = "localhost",
    health_endpoint: str = "/health",
    capabilities: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    description: str = "",
) -> None:
    now = time.time()
    with _conn() as c:
        c.execute(
            """INSERT INTO services
               (name, host, port, health_endpoint, capabilities, tags,
                description, registered_at, last_heartbeat)
               VALUES (?,?,?,?,?,?,?,?,?)
               ON CONFLICT(name) DO UPDATE SET
                   host=excluded.host,
                   port=excluded.port,
                   health_endpoint=excluded.health_endpoint,
                   capabilities=excluded.capabilities,
                   tags=excluded.tags,
                   description=excluded.description,
                   last_heartbeat=excluded.last_heartbeat""",
            (
                name, host, port, health_endpoint,
                json.dumps(capabilities or []),
                json.dumps(tags or []),
                description, now, now,
            ),
        )
        c.commit()
    _log_event("register", name, f"port={port}")


def heartbeat(name: str) -> bool:
    with _conn() as c:
        cur = c.execute(
            "UPDATE services SET last_heartbeat=? WHERE name=?",
            (time.time(), name),
        )
        c.commit()
        return cur.rowcount > 0


def deregister(name: str) -> bool:
    with _conn() as c:
        cur = c.execute("DELETE FROM services WHERE name=? RETURNING name", (name,))
        found = cur.fetchone() is not None
        if found:
            _log_event("deregister", name, "service removed")
        c.commit()
    return found


def upsert_process(
    pid: int,
    name: str,
    start_time: Optional[str] = None,
    is_ecosystem: bool = False,
    metadata: Optional[Dict] = None,
) -> None:
    upsert_processes(
        [
            {
                "pid": pid,
                "name": name,
                "start_time": start_time,
                "is_ecosystem": is_ecosystem,
                "metadata": metadata or {},
            }
        ]
    )


def upsert_processes(processes: List[Dict]) -> int:
    if not processes:
        return 0

    now = time.time()
    rows = []
    for process in processes:
        try:
            rows.append(
                (
                    int(process["pid"]),
                    str(process["name"]),
                    process.get("start_time"),
                    now,
                    1 if process.get("is_ecosystem") else 0,
                    json.dumps(process.get("metadata") or {}),
                )
            )
        except Exception:
            continue

    if not rows:
        return 0

    with _conn() as c:
        c.executemany(
            """INSERT INTO processes
               (pid, name, start_time, last_seen, is_ecosystem, metadata)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(pid) DO UPDATE SET
                   name=excluded.name,
                   start_time=excluded.start_time,
                   last_seen=excluded.last_seen,
                   is_ecosystem=excluded.is_ecosystem,
                   metadata=excluded.metadata""",
            rows,
        )
        c.commit()
    return len(rows)


def _log_event(event: str, service: str, detail: str = "") -> None:
    with _conn() as c:
        c.execute(
            "INSERT INTO gateway_events (event, service, detail, ts) VALUES (?,?,?,?)",
            (event, service, detail, time.time()),
        )
        c.commit()


def _log_agent_event(event: str, agent_id: str, detail: str = "") -> None:
    _log_event(f"agent:{event}", agent_id, detail)


# ── Read ──────────────────────────────────────────────────────────────────────

def get_service(name: str) -> Optional[Dict]:
    with _conn() as c:
        row = c.execute("SELECT * FROM services WHERE name=?", (name,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["capabilities"] = json.loads(d.get("capabilities") or "[]")
    d["tags"] = json.loads(d.get("tags") or "[]")
    d["stale"] = (time.time() - (d.get("last_heartbeat") or 0)) > _STALE_SECONDS
    return d


def list_services(cap_filter: Optional[str] = None) -> List[Dict]:
    with _conn() as c:
        if cap_filter:
            rows = c.execute(
                "SELECT * FROM services WHERE capabilities LIKE ? ORDER BY name",
                (f"%{cap_filter}%",),
            ).fetchall()
        else:
            rows = c.execute("SELECT * FROM services ORDER BY name").fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["capabilities"] = json.loads(d.get("capabilities") or "[]")
        d["tags"] = json.loads(d.get("tags") or "[]")
        d["stale"] = (time.time() - (d.get("last_heartbeat") or 0)) > _STALE_SECONDS
        result.append(d)
    return result


def list_processes(
    only_ecosystem: bool = False,
    stale_threshold_seconds: Optional[int] = _PROCESS_STALE_SECONDS,
) -> List[Dict]:
    clauses = []
    params: list[object] = []
    if only_ecosystem:
        clauses.append("is_ecosystem=1")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with _conn() as c:
        rows = c.execute(
            f"SELECT * FROM processes {where} ORDER BY is_ecosystem DESC, name, pid",
            params,
        ).fetchall()

    result = []
    for row in rows:
        d = dict(row)
        try:
            d["metadata"] = json.loads(d.get("metadata") or "{}")
        except Exception:
            d["metadata"] = {}
        d["is_ecosystem"] = bool(d.get("is_ecosystem"))
        threshold = _PROCESS_STALE_SECONDS if stale_threshold_seconds is None else stale_threshold_seconds
        d["stale"] = threshold >= 0 and (time.time() - (d.get("last_seen") or 0)) > threshold
        result.append(d)
    return result


def prune_stale_processes(
    age_seconds: int = _PROCESS_STALE_SECONDS,
    active_processes: Optional[List[Dict]] = None,
) -> int:
    cutoff = time.time() - age_seconds
    active_keys = None
    if active_processes:
        active_keys = {
            (int(proc["pid"]), str(proc.get("start_time") or ""))
            for proc in active_processes
            if proc.get("pid") is not None
        }

    with _conn() as c:
        rows = c.execute(
            "SELECT pid, start_time FROM processes WHERE last_seen < ?",
            (cutoff,),
        ).fetchall()
        prune_ids = []
        for row in rows:
            key = (int(row["pid"]), str(row["start_time"] or ""))
            if active_keys is not None and key in active_keys:
                continue
            prune_ids.append(int(row["pid"]))

        if not prune_ids:
            return 0

        placeholders = ",".join("?" for _ in prune_ids)
        c.execute(f"DELETE FROM processes WHERE pid IN ({placeholders})", prune_ids)
        c.commit()
    return len(prune_ids)


def process_stats(stale_threshold_seconds: int = _PROCESS_STALE_SECONDS) -> Dict:
    processes = list_processes(stale_threshold_seconds=stale_threshold_seconds)
    total = len(processes)
    live = sum(1 for proc in processes if not proc["stale"])
    ecosystem = sum(1 for proc in processes if proc["is_ecosystem"])
    ecosystem_live = sum(1 for proc in processes if proc["is_ecosystem"] and not proc["stale"])
    return {
        "total": total,
        "live": live,
        "stale": total - live,
        "ecosystem": ecosystem,
        "ecosystem_live": ecosystem_live,
    }


def register_agent(
    agent_id: str,
    capabilities: Optional[List[str]] = None,
    channels: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    description: str = "",
    metadata: Optional[Dict] = None,
    *,
    name: Optional[str] = None,
    kind: str = "agent",
    status: str = "online",
) -> None:
    now = time.time()
    with _conn() as c:
        c.execute(
            """INSERT INTO agents
               (agent_id, name, kind, capabilities, channels, tags, description,
                metadata, registered_at, last_heartbeat, status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(agent_id) DO UPDATE SET
                   name=excluded.name,
                   kind=excluded.kind,
                   capabilities=excluded.capabilities,
                   channels=excluded.channels,
                   tags=excluded.tags,
                   description=excluded.description,
                   metadata=excluded.metadata,
                   last_heartbeat=excluded.last_heartbeat,
                   status=excluded.status""",
            (
                agent_id,
                name or agent_id,
                kind,
                json.dumps(capabilities or []),
                json.dumps(channels or []),
                json.dumps(tags or []),
                description,
                json.dumps(metadata or {}),
                now,
                now,
                status,
            ),
        )
        c.commit()
    _log_agent_event("register", agent_id, f"kind={kind} status={status}")


def heartbeat_agent(agent_id: str, status: str = "online", metadata: Optional[Dict] = None) -> bool:
    with _conn() as c:
        cur = c.execute(
            """UPDATE agents
               SET last_heartbeat=?, status=?, metadata=COALESCE(?, metadata)
               WHERE agent_id=?
               RETURNING agent_id""",
            (time.time(), status, json.dumps(metadata) if metadata is not None else None, agent_id),
        )
        found = cur.fetchone() is not None
        c.commit()
    if found:
        _log_agent_event("heartbeat", agent_id, f"status={status}")
    return found


def deregister_agent(agent_id: str) -> bool:
    with _conn() as c:
        cur = c.execute("DELETE FROM agents WHERE agent_id=? RETURNING agent_id", (agent_id,))
        found = cur.fetchone() is not None
        c.commit()
    if found:
        _log_agent_event("deregister", agent_id, "agent removed")
    return found


def get_agent(agent_id: str) -> Optional[Dict]:
    with _conn() as c:
        row = c.execute("SELECT * FROM agents WHERE agent_id=?", (agent_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["capabilities"] = json.loads(d.get("capabilities") or "[]")
    d["channels"] = json.loads(d.get("channels") or "[]")
    d["tags"] = json.loads(d.get("tags") or "[]")
    d["metadata"] = json.loads(d.get("metadata") or "{}")
    d["stale"] = (time.time() - (d.get("last_heartbeat") or 0)) > _AGENT_STALE_SECONDS
    return d


def list_agents(cap_filter: Optional[str] = None) -> List[Dict]:
    with _conn() as c:
        if cap_filter:
            rows = c.execute(
                "SELECT * FROM agents WHERE capabilities LIKE ? ORDER BY agent_id",
                (f"%{cap_filter}%",),
            ).fetchall()
        else:
            rows = c.execute("SELECT * FROM agents ORDER BY agent_id").fetchall()
    agents = []
    for row in rows:
        d = dict(row)
        d["capabilities"] = json.loads(d.get("capabilities") or "[]")
        d["channels"] = json.loads(d.get("channels") or "[]")
        d["tags"] = json.loads(d.get("tags") or "[]")
        d["metadata"] = json.loads(d.get("metadata") or "{}")
        d["stale"] = (time.time() - (d.get("last_heartbeat") or 0)) > _AGENT_STALE_SECONDS
        agents.append(d)
    return agents


def agent_stats() -> Dict:
    with _conn() as c:
        total = c.execute("SELECT COUNT(*) FROM agents").fetchone()[0]
    agents = list_agents()
    live = sum(1 for agent in agents if not agent["stale"])
    return {"total": total, "live": live, "stale": total - live}


def gateway_table() -> List[Dict]:
    """Routing table for the gateway — only live (non-stale) services."""
    all_svcs = list_services()
    return [s for s in all_svcs if not s["stale"]]


def health_check_all(timeout: int = 2) -> List[Dict]:
    """Probe health endpoint of every registered service."""
    services = list_services()
    results = []
    for svc in services:
        url = f"http://{svc['host']}:{svc['port']}{svc['health_endpoint']}"
        try:
            r = requests.get(url, timeout=timeout)
            status = "healthy" if r.status_code < 400 else f"http_{r.status_code}"
        except requests.exceptions.ConnectionError:
            status = "unreachable"
        except requests.exceptions.Timeout:
            status = "timeout"
        except Exception as e:
            status = f"error: {e}"
        results.append({
            "name": svc["name"],
            "host": svc["host"],
            "port": svc["port"],
            "status": status,
            "stale": svc["stale"],
            "capabilities": svc["capabilities"],
        })
    return results


def registry_stats() -> Dict:
    with _conn() as c:
        total = c.execute("SELECT COUNT(*) FROM services").fetchone()[0]
        events = c.execute(
            "SELECT COUNT(*) FROM gateway_events WHERE ts > ?",
            (time.time() - 3600,),
        ).fetchone()[0]
    all_svcs = list_services()
    live = sum(1 for s in all_svcs if not s["stale"])
    return {
        "total": total,
        "live": live,
        "stale": total - live,
        "events_last_hour": events,
        "agents": agent_stats(),
        "processes": process_stats(),
    }


# ── Seed from config/port_map.json ───────────────────────────────────────────

def seed_from_port_map() -> int:
    port_map_path = _ROOT / "config" / "port_map.json"
    if not port_map_path.exists():
        return 0
    try:
        data = json.loads(port_map_path.read_text())
        ports = data.get("ports", {})
    except Exception:
        return 0

    count = 0
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(_DB_PATH), check_same_thread=False, timeout=10)
    con.execute("PRAGMA journal_mode=WAL")
    try:
        for _ext_port, info in ports.items():
            name = info.get("service", "")
            local_port = info.get("local_port") or info.get("port", 0)
            if not name or not local_port:
                continue
            caps = []
            if info.get("critical"):
                caps.append("critical")
            if not info.get("ai_required", True):
                caps.append("offline")
            existing = con.execute(
                "SELECT name FROM services WHERE name=?", (name,)
            ).fetchone()
            if not existing:
                con.execute(
                    """INSERT OR IGNORE INTO services
                       (name, host, port, health_endpoint, capabilities, tags,
                        description, registered_at, last_heartbeat)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (
                        name, "localhost", local_port,
                        info.get("health", "/health"),
                        json.dumps(caps), json.dumps([]),
                        info.get("note", ""), time.time(), 0,
                    ),
                )
                count += 1
        con.commit()
    finally:
        con.close()
    return count


def initialise() -> Dict:
    _init_db()
    seeded = seed_from_port_map()
    stats = registry_stats()
    return {"seeded_from_port_map": seeded, **stats}
