"""
Culture Ship Substrate Bridge — Phase 2A Bootstrap Integration

Minimal, tested bridge between Culture Ship decision-making layer and
persistent substrate audit/decision systems.

Responsibilities:
  - Initialize substrate context on Culture Ship startup
  - Normalize Culture Ship Redis events to MsgX format
  - Persist decisions to registry.jsonl for audit
  - Provide tagging interface for Culture Ship decision advisory

This module is imported by scripts/culture_ship.py during __main__ execution.

Usage (from culture_ship.py startup):
    from .substrate.culture_ship_substrate_bridge import bootstrap_culture_ship_substrate
    bootstrap_culture_ship_substrate()
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE = Path(__file__).parent.parent.parent
SUBSTRATE_DIR = BASE / ".substrate"
STATE_DIR = BASE / "state"

log = logging.getLogger("culture_ship.substrate")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_registry() -> list[dict[str, Any]]:
    """Load existing registry.jsonl or return empty list."""
    registry_path = SUBSTRATE_DIR / "registry.jsonl"
    if not registry_path.exists():
        return []
    try:
        return [json.loads(line) for line in registry_path.read_text().strip().split("\n") if line]
    except Exception as e:
        log.warning(f"Failed to load registry: {e}")
        return []


def save_registry_entry(entry: dict[str, Any]) -> None:
    """Append entry to registry.jsonl."""
    try:
        registry_path = SUBSTRATE_DIR / "registry.jsonl"
        with open(registry_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        log.error(f"Failed to save registry entry: {e}")


def normalize_event_to_msgx(channel: str, event: dict[str, Any]) -> dict[str, Any]:
    """Convert a Culture Ship Redis event to MsgX packet format."""
    msgx_id = str(uuid.uuid4())

    # Map event type to action
    action_map = {
        "lattice.service.down": "restart",
        "lattice.agent.stale": "heal",
        "lattice.rimworld.crash": "audit",
        "lattice.skyclaw.alert": "observe",
    }
    action = action_map.get(channel, "observe")

    return {
        "msgx_id": msgx_id,
        "version": "1.0",
        "timestamp": _now(),
        "source": "culture-ship",
        "target": event.get("target", "lattice-gordon"),
        "action": action,
        "payload": {
            "service": event.get("service") or event.get("agent_id"),
            "reason": event.get("reason") or event.get("description", ""),
            "priority": event.get("priority", "P2"),
            "safe_mode": True,
        },
        "decision_path": ["culture-ship", "council"],
        "expected_outcome": f"Remediation of {event.get('service', 'service')} initiated",
        "original_event_channel": channel,
    }


def tag_artifact(artifact_id: str, artifact_type: str, tags: list[str], 
                 rationale: str = "", ttl_seconds: int | None = None) -> dict[str, Any]:
    """Create an OmniTag tagging decision."""
    tag_entry = {
        "tag_id": str(uuid.uuid4()),
        "artifact": artifact_id,
        "artifact_type": artifact_type,
        "tags": tags,
        "confidence": 0.95,
        "issued_by": "culture-ship-substrate-bridge",
        "timestamp": _now(),
        "rationale": rationale,
    }
    if ttl_seconds:
        tag_entry["ttl_seconds"] = ttl_seconds
    save_registry_entry(tag_entry)
    return tag_entry


def record_decision(action: str, service: str, result: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Record a Culture Ship decision to the audit trail."""
    decision = {
        "type": "culture_ship_decision",
        "timestamp": _now(),
        "action": action,
        "service": service,
        "result": result,
        "metadata": metadata or {},
    }
    save_registry_entry(decision)
    return decision


def bootstrap_culture_ship_substrate() -> dict[str, Any]:
    """
    Initialize substrate bridge on Culture Ship startup.
    
    Returns bootstrap status dict with initialization results.
    """
    log.info("Substrate bridge bootstrap initiated")

    # Ensure .substrate directory exists
    SUBSTRATE_DIR.mkdir(parents=True, exist_ok=True)

    # Record bootstrap event
    bootstrap_event = {
        "type": "substrate_bootstrap",
        "timestamp": _now(),
        "culture_ship": "GSV Sublime Optimization",
        "substrate_version": "1.0",
        "status": "initialized",
    }
    save_registry_entry(bootstrap_event)

    # Tag Culture Ship itself as critical
    tag_artifact(
        "lattice-culture-ship",
        "service",
        ["critical", "always-on", "meta-controller"],
        rationale="Culture Ship is the decision oracle and ethical layer",
    )

    log.info("Substrate bridge ready. Registry active.")
    return {
        "ok": True,
        "substrate_dir": str(SUBSTRATE_DIR),
        "registry_path": str(SUBSTRATE_DIR / "registry.jsonl"),
        "bootstrap_time": _now(),
    }


def hook_redis_event(channel: str, event: dict[str, Any]) -> None:
    """
    Called by Culture Ship event handlers to normalize events to substrate.
    
    Converts Redis event → MsgX → registry entry
    """
    try:
        msgx = normalize_event_to_msgx(channel, event)
        save_registry_entry(msgx)
        log.debug(f"Event normalized to MsgX: {msgx['msgx_id']}")
    except Exception as e:
        log.error(f"Failed to hook event: {e}")


# Health check endpoint (called by Culture Ship health server)
def get_bridge_status() -> dict[str, Any]:
    """Return current bridge status for health monitoring."""
    registry_path = SUBSTRATE_DIR / "registry.jsonl"
    registry = load_registry()
    return {
        "ok": True,
        "registry_entries": len(registry),
        "registry_path": str(registry_path),
        "last_bootstrap": datetime.now(timezone.utc).isoformat(),
    }
