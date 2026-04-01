"""health_server.py — Zero-dependency shared HTTP health endpoint for every agent.

Uses only Python stdlib (http.server + threading). No FastAPI, no uvicorn,
no requests — works completely offline, even in a minimal Python environment.

Usage (in any agent script):
    from scripts.health_server import start_health_server, set_status

    start_health_server(port=3000, agent="Gordon", version="1.0.0")
    # later:
    set_status({"phase": "scanning", "last_cycle": 42})

Endpoints served:
    GET /           → same as /health
    GET /health     → {"status":"ok","agent":"Gordon",...}
    GET /api/health → same payload as /health
    GET /status     → full status dict including dynamic fields
    GET /metrics    → Prometheus-compatible plain text
    GET /ping       → pong (minimal latency check)
"""

from __future__ import annotations

import http.server
import json
import logging
import os
import socket
import threading
import time
from datetime import UTC, datetime, timezone
from typing import Any

log = logging.getLogger("health_server")

# ─── Shared mutable status dict (thread-safe via GIL on small dicts) ──────────
_STATUS: dict[str, Any] = {
    "status": "starting",
    "agent": "unknown",
    "version": "0.1.0",
    "started_at": None,
    "uptime_s": 0,
    "cycles": 0,
    "last_seen": None,
    "redis_ok": False,
    "ai_ok": False,
    "port_map": {},
}
_START_TIME: float = time.time()
_LOCK = threading.Lock()


def set_status(updates: dict[str, Any]) -> None:
    """Thread-safe partial update of the shared status dict."""
    with _LOCK:
        _STATUS.update(updates)
        _STATUS["last_seen"] = _now()
        _STATUS["uptime_s"] = int(time.time() - _START_TIME)


def get_status() -> dict[str, Any]:
    with _LOCK:
        snap = dict(_STATUS)
    snap["uptime_s"] = int(time.time() - _START_TIME)
    return snap


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _prometheus_metrics(snap: dict) -> str:
    lines = [
        "# HELP agent_uptime_seconds Seconds since agent started",
        "# TYPE agent_uptime_seconds gauge",
        f'agent_uptime_seconds{{agent="{snap["agent"]}"}} {snap["uptime_s"]}',
        "# HELP agent_cycles_total Total orchestration cycles run",
        "# TYPE agent_cycles_total counter",
        f'agent_cycles_total{{agent="{snap["agent"]}"}} {snap.get("cycles", 0)}',
        "# HELP agent_redis_ok Redis connectivity (1=ok, 0=down)",
        "# TYPE agent_redis_ok gauge",
        f'agent_redis_ok{{agent="{snap["agent"]}"}} {1 if snap.get("redis_ok") else 0}',
        "# HELP agent_ai_ok AI/LLM connectivity (1=ok, 0=down)",
        "# TYPE agent_ai_ok gauge",
        f'agent_ai_ok{{agent="{snap["agent"]}"}} {1 if snap.get("ai_ok") else 0}',
    ]
    return "\n".join(lines) + "\n"


class _HealthHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # silence access log — keep daemon output clean

    def _send_json(self, code: int, body: dict) -> None:
        data = json.dumps(body, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def _send_text(self, code: int, body: str) -> None:
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")
        snap = get_status()

        if path in ("", "/", "/health", "/api/health"):
            healthy = snap["status"] not in ("error", "crashed")
            code = 200 if healthy else 503
            self._send_json(
                code,
                {
                    "status": snap["status"],
                    "agent": snap["agent"],
                    "version": snap["version"],
                    "uptime_s": snap["uptime_s"],
                    "started_at": snap["started_at"],
                    "ai_optional": True,
                },
            )

        elif path == "/status":
            self._send_json(200, snap)

        elif path == "/ping":
            self._send_json(200, {"pong": True, "ts": _now()})

        elif path == "/metrics":
            self._send_text(200, _prometheus_metrics(snap))

        else:
            self._send_json(404, {"error": "not found", "path": path})


def _is_port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("0.0.0.0", port))
            return True
        except OSError:
            return False


def start_health_server(
    port: int,
    agent: str = "Agent",
    version: str = "0.1.0",
    extra: dict | None = None,
) -> threading.Thread:
    """Start the health HTTP server in a daemon background thread.
    Returns the thread (already started).  Safe to call multiple times —
    if port is already bound elsewhere, logs a warning and continues.
    """
    global _START_TIME
    _START_TIME = time.time()
    with _LOCK:
        _STATUS["agent"] = agent
        _STATUS["version"] = version
        _STATUS["status"] = "ok"
        _STATUS["started_at"] = _now()
        if extra:
            _STATUS.update(extra)

    if not _is_port_free(port):
        log.warning(
            f"[health_server] Port {port} already in use — skipping bind for {agent}"
        )
        return threading.Thread(target=lambda: None, daemon=True)

    server = http.server.HTTPServer(("0.0.0.0", port), _HealthHandler)

    def _serve():
        log.info(
            f"[health_server] {agent} health endpoint → http://0.0.0.0:{port}/health (alias /api/health)"
        )
        try:
            server.serve_forever()
        except Exception as e:
            log.error(f"[health_server] {agent} server error: {e}")

    t = threading.Thread(
        target=_serve, daemon=True, name=f"health-{agent.lower()}-{port}"
    )
    t.start()
    return t


# ─── Port connectivity checker (deterministic, stdlib only) ───────────────────


def check_port(host: str, port: int, timeout: float = 1.5) -> bool:
    """Return True if something is listening on host:port."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, ConnectionRefusedError, TimeoutError):
        return False


def scan_ecosystem_ports(port_map_path: str | None = None) -> dict[str, Any]:
    """Read config/port_map.json and check every declared port.
    Returns dict: {external_port: {name, local_port, alive, ...}}
    Falls back gracefully if port_map.json is missing.
    """
    import pathlib

    if port_map_path is None:
        candidates = [
            pathlib.Path(__file__).parent.parent / "config" / "port_map.json",
            pathlib.Path("config/port_map.json"),
        ]
        for c in candidates:
            if c.exists():
                port_map_path = str(c)
                break

    if not port_map_path:
        return {}

    try:
        with open(port_map_path) as f:
            pm = json.load(f)
    except Exception as e:
        log.warning(f"[health_server] Could not load port_map.json: {e}")
        return {}

    results: dict[str, Any] = {}
    for ext_port, info in pm.get("ports", {}).items():
        local_port = info.get("local_port", int(ext_port))
        alive = check_port("localhost", local_port)
        results[ext_port] = {
            "name": info.get("name", "?"),
            "local_port": local_port,
            "alive": alive,
            "critical": info.get("critical", False),
            "note": info.get("note", ""),
        }
    return results
