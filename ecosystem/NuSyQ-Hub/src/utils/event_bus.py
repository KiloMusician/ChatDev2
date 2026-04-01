"""Event Bus Utility - Append events to canonical log streams.

This helper makes it trivial for any system component to emit events
that the monitoring terminals can tail in real-time.

Usage:
    from src.utils.event_bus import emit_event

    emit_event("agent_bus", "task_routed", {"task_id": 42, "agent": "claude"})
    emit_event("council_decisions", "vote_cast", {"voter": "copilot", "choice": "approve"})
    emit_event("culture_ship_audits", "proof_validated", {"proof_id": 123, "valid": True})
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Canonical log bus paths
LOGS_DIR = Path(__file__).resolve().parents[2] / "state" / "logs"

LOG_STREAMS = {
    "agent_bus": LOGS_DIR / "agent_bus.log",
    "council_decisions": LOGS_DIR / "council_decisions.log",
    "culture_ship_audits": LOGS_DIR / "culture_ship_audits.log",
    "chatdev_latest": LOGS_DIR / "chatdev_latest.log",
    "moderator": LOGS_DIR / "moderator.log",
    "errors": LOGS_DIR / "errors.log",
    "anomalies": LOGS_DIR / "anomalies.log",
    "test_history": LOGS_DIR / "test_history.log",
}


def emit_event(
    stream: str,
    event_type: str,
    payload: dict[str, Any] | None = None,
    message: str | None = None,
) -> None:
    """Emit an event to a canonical log stream.

    Args:
        stream: Stream name (e.g., "agent_bus", "council_decisions")
        event_type: Event type (e.g., "task_routed", "vote_cast")
        payload: Optional dict of event data
        message: Optional human-readable message

    Example:
        emit_event("agent_bus", "task_assigned",
                   {"task_id": 42, "agent": "claude"},
                   "Claude assigned to refactor compute_deltas()")
    """
    # Ensure logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Get log path
    log_path = LOG_STREAMS.get(stream)
    if not log_path:
        # Unknown stream - create it
        log_path = LOGS_DIR / f"{stream}.log"

    # Build event line
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    parts = [timestamp, f"EVENT={event_type}"]

    if payload:
        parts.append(f"payload={json.dumps(payload, separators=(',', ':'))}")

    if message:
        parts.append(f"msg={message}")

    event_line = " | ".join(parts)

    # Append to log
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(event_line + "\n")


def emit_agent_message(agent: str, message: str, **kwargs) -> None:
    """Convenience: emit to agent_bus."""
    emit_event("agent_bus", "agent_message", {"agent": agent, **kwargs}, message)


def emit_council_vote(voter: str, choice: str, **kwargs) -> None:
    """Convenience: emit to council_decisions."""
    emit_event("council_decisions", "vote_cast", {"voter": voter, "choice": choice, **kwargs})


def emit_audit(audit_type: str, result: bool, **kwargs) -> None:
    """Convenience: emit to culture_ship_audits."""
    emit_event("culture_ship_audits", audit_type, {"result": result, **kwargs})


def emit_error(severity: str, message: str, **kwargs) -> None:
    """Convenience: emit to errors log."""
    emit_event("errors", "error_logged", {"severity": severity, **kwargs}, message)


# Example usage in orchestrator or worker:
if __name__ == "__main__":
    # Test the bus
    emit_event("agent_bus", "bus_test", {"test": True}, "Event bus test successful")
    emit_agent_message("test_agent", "Test message from event bus")
    emit_council_vote("claude", "approve", task_id=999)
    emit_audit("proof_validation", True, proof_id=123)
    emit_error("WARNING", "This is a test error message", file="event_bus.py")

    logger.info("✅ Test events emitted to all streams")
    logger.info(f"Check: {LOGS_DIR}")
