"""system/status.py — NuSyQ-Hub system heartbeat/status abstraction with CASCADE ACTIONS.

Provides a programmatic, always-on indicator of system state for agents and orchestration code.

🔥 CASCADE ACTIONS ENABLED:
- Status changes emit events to event_bus
- Transitions trigger cascades (startup, shutdown, error, recovery)
- Heartbeat includes health checks
- Auto-healing integration on errors
"""

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


STATUS_FILE = Path(__file__).resolve().parents[2] / "state" / "system_status.json"
STATUS_LOCK = threading.Lock()

DEFAULT_STATUS = {
    "status": "off",
    "timestamp": None,
    "run_id": None,
    "details": {},
    "health": "unknown",
}

# Track state for cascade detection
_previous_status: str | None = None
_heartbeat_count = 0
_last_heartbeat_time: datetime | None = None


def _emit_event_safe(
    stream: str, event_type: str, payload: dict | None = None, message: str | None = None
):
    """Safely emit event to event bus (doesn't fail if unavailable)."""
    try:
        from src.utils.event_bus import emit_event

        emit_event(stream, event_type, payload or {}, message)
    except Exception:
        logger.debug("Suppressed Exception", exc_info=True)


def _trigger_startup_cascades(run_id: str | None, details: dict[str, Any]):
    """🔥 CASCADE: System startup actions."""
    _emit_event_safe("system_status", "startup_cascades_begin", {"run_id": run_id})

    try:
        from src.integration.n8n_integration import N8NClient

        n8n = N8NClient()
        n8n.trigger_workflow("system-startup", {"run_id": run_id, "details": details})
    except Exception:
        logger.debug("Suppressed Exception", exc_info=True)

    _emit_event_safe("system_status", "startup_cascades_complete", {"run_id": run_id})


def _trigger_shutdown_cascades(run_id: str | None, details: dict[str, Any]):
    """🔥 CASCADE: System shutdown actions."""
    _emit_event_safe("system_status", "shutdown_cascades_begin", {"run_id": run_id})

    try:
        from src.integration.n8n_integration import N8NClient

        n8n = N8NClient()
        n8n.trigger_workflow("system-shutdown", {"run_id": run_id})
    except Exception:
        logger.debug("Suppressed Exception", exc_info=True)

    _emit_event_safe("system_status", "shutdown_cascades_complete", {"run_id": run_id})


def _trigger_error_cascades(from_status: str, details: dict[str, Any]):
    """🔥 CASCADE: System error actions - triggers auto-healing."""
    error_message = details.get("message", "System entered error state")
    _emit_event_safe("errors", "system_error_state", details, error_message)

    try:
        from src.orchestration.auto_healing import (AutoHealingMonitor,
                                                    ErrorContext)

        monitor = AutoHealingMonitor(enable_auto_heal=True)
        context = ErrorContext(
            error_type="system_error",
            error_message=error_message,
            span_name="system_status",
            timestamp=datetime.now().timestamp(),
            attributes=details,
        )
        monitor.on_error(Exception(error_message), context)
        _emit_event_safe("system_status", "auto_healing_triggered", {"error": error_message})
    except Exception as e:
        _emit_event_safe("errors", "auto_healing_failed", {"error": str(e)})


def _trigger_recovery_cascades(run_id: str | None, details: dict[str, Any]):
    """🔥 CASCADE: System recovery actions."""
    _emit_event_safe("system_status", "recovery_complete", {"run_id": run_id}, "System recovered")


def _handle_status_transition(old: str, new: str, run_id: str | None, details: dict[str, Any]):
    """🔥 CASCADE: Handle status transitions."""
    if old == "off" and new == "on":
        _trigger_startup_cascades(run_id, details)
    elif old == "on" and new == "off":
        _trigger_shutdown_cascades(run_id, details)
    elif new == "error":
        _trigger_error_cascades(old, details)
    elif old == "error" and new == "on":
        _trigger_recovery_cascades(run_id, details)


def set_system_status(
    status: str,
    health: str = "healthy",
    run_id: str | None = None,
    details: dict | None = None,
    message: str | None = None,
):
    """Set system status AND trigger cascade actions."""
    global _previous_status

    old_status = get_system_status().get("status", "off")

    payload = {
        "status": status,
        "health": health,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "run_id": run_id,
        "details": details or {},
        "message": message,
    }

    with STATUS_LOCK:
        STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    _emit_event_safe(
        "system_status",
        "status_change",
        {"from": old_status, "to": status, "health": health},
        message or f"Status: {old_status} → {status}",
    )

    if old_status != status:
        _handle_status_transition(old_status, status, run_id, details or {})

    _previous_status = status


def get_system_status() -> dict:
    """Get current system status."""
    if not STATUS_FILE.exists():
        return DEFAULT_STATUS.copy()
    with STATUS_LOCK:
        try:
            with open(STATUS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_STATUS.copy()


def is_system_on() -> bool:
    """Return True if system is 'on'."""
    return get_system_status().get("status") == "on"


def heartbeat(run_id: str | None = None, details: dict | None = None):
    """Update heartbeat AND trigger periodic health cascades."""
    global _heartbeat_count, _last_heartbeat_time

    current = get_system_status()
    now = datetime.now()

    if _last_heartbeat_time:
        elapsed = (now - _last_heartbeat_time).total_seconds()
        if elapsed > 60:
            _emit_event_safe(
                "anomalies",
                "heartbeat_stale",
                {"elapsed_seconds": elapsed},
                f"Heartbeat stale ({elapsed:.1f}s)",
            )

    set_system_status(
        status="on",
        health=current.get("health", "healthy"),
        run_id=run_id or current.get("run_id"),
        details={
            **current.get("details", {}),
            **(details or {}),
            "heartbeat_count": _heartbeat_count,
            "last_heartbeat": now.isoformat(),
        },
    )

    _heartbeat_count += 1
    _last_heartbeat_time = now
