"""system/status.py — NuSyQ-Hub system heartbeat/status abstraction.

Provides a programmatic, always-on indicator of system state for agents and orchestration code.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

STATUS_FILE = Path(__file__).resolve().parents[2] / "state" / "system_status.json"
STATUS_LOCK = threading.Lock()

DEFAULT_STATUS: dict[str, Any] = {
    "status": "off",
    "timestamp": None,
    "run_id": None,
    "details": {},
}


def set_system_status(status: str, run_id: str | None = None, details: dict | None = None):
    """Set the system status ('on' or 'off'), with optional run_id and details."""
    payload = {
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "run_id": run_id,
        "details": details or {},
    }
    with STATUS_LOCK:
        STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)


def get_system_status() -> dict[Any, Any]:
    """Get the current system status as a dict."""
    if not STATUS_FILE.exists():
        return DEFAULT_STATUS.copy()
    with STATUS_LOCK:
        try:
            with open(STATUS_FILE, encoding="utf-8") as f:
                result: dict[Any, Any] = json.load(f)
                return result
        except Exception:
            return DEFAULT_STATUS.copy()


def is_system_on() -> bool:
    """Return True if the system is 'on' according to the status file."""
    status = get_system_status()
    return status.get("status") == "on"


def heartbeat(run_id: str | None = None, details: dict | None = None):
    """Update the heartbeat timestamp and keep system 'on'."""
    current = get_system_status()
    set_system_status(
        status="on",
        run_id=run_id or current.get("run_id"),
        details=details or current.get("details", {}),
    )
