"""RosettaStone + OmniTag event schema and logger.

- RosettaStone: input normalization (keys/strings, CRLF->LF, stable hash)
- OmniTag: lightweight tagging from event fields and context
- EventLogger: append-only JSONL writer to Reports/events per-day files

No external dependencies; designed for Windows-friendly paths.

cSpell:ignore omnitag gethostname edir
"""

from __future__ import annotations

import hashlib
import json
import platform
import socket
import threading
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
EVENT_DIR = ROOT / "Reports" / "events"
EVENT_DIR.mkdir(parents=True, exist_ok=True)

SCHEMA_VERSION = "1.0.0"


# ---------------- RosettaStone normalization ----------------


def rs_normalize(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize dict payload and add a stable content hash."""
    norm: Dict[str, Any] = {}
    for k, v in payload.items():
        key = str(k).strip()
        if isinstance(v, str):
            norm[key] = v.strip().replace("\r\n", "\n")
        else:
            norm[key] = v
    norm["content_hash"] = hashlib.sha256(
        json.dumps(norm, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return norm


# ---------------- OmniTag tagging ----------------


def omnitag(event: Dict[str, Any]) -> List[str]:
    """Derive tags from event fields.

    Stable tags: component, action, severity, outcome, task_type, complexity,
    agent, os, host.
    """
    tags: List[str] = []
    comp = event.get("component")
    action = event.get("action")
    sev = event.get("severity")
    outcome = event.get("outcome")
    task_type = event.get("task_type")
    complexity = event.get("complexity")
    agent = event.get("agent")

    if comp:
        tags.append(f"component:{comp}")
    if action:
        tags.append(f"action:{action}")
    if sev:
        tags.append(f"severity:{sev}")
    if outcome:
        tags.append(f"outcome:{outcome}")
    if task_type:
        tags.append(f"task:{task_type}")
    if complexity:
        tags.append(f"complexity:{complexity}")
    if agent:
        tags.append(f"agent:{agent}")

    # System tags
    try:
        tags.append(f"os:{platform.system().lower()}")
    except (ValueError, OSError, AttributeError):
        pass
    try:
        tags.append(f"host:{socket.gethostname().lower()}")
    except (ValueError, OSError, AttributeError):
        pass

    # Deduplicate while preserving order
    seen = set()
    out: List[str] = []
    for t in tags:
        if t not in seen:
            out.append(t)
            seen.add(t)
    return out


# ---------------- Event record + logger ----------------


@dataclass
class EventRecord:
    """Structured event record with normalized payload and OmniTags.

    Attributes:
        timestamp: ISO 8601 event timestamp
        event_id: Unique UUID for this event
        schema_version: Event schema version
        component: Originating component (e.g., rosetta_pipeline)
        action: Event action (e.g., start, route_decision, end)
        severity: Event severity (info, warning, error)
        outcome: Optional outcome (success, failure)
        task_type: Optional task type (e.g., code_generation)
        complexity: Optional complexity (simple, moderate, complex)
        agent: Optional agent name
        payload: Original event payload
        rs: RosettaStone normalized payload with content_hash
        tags: OmniTag-derived tags
        context: Additional contextual metadata
    """

    timestamp: str
    event_id: str
    schema_version: str
    component: str
    action: str
    severity: str
    outcome: Optional[str]
    task_type: Optional[str]
    complexity: Optional[str]
    agent: Optional[str]
    payload: Dict[str, Any]
    rs: Dict[str, Any]
    tags: List[str]
    context: Dict[str, Any]


class EventLogger:
    """Thread-safe append-only JSONL event logger.

    Writes EventRecord objects to daily JSONL files at
    Reports/events/events_YYYYMMDD.jsonl.
    """

    def __init__(self, event_dir: Optional[Path] = None):
        self.event_dir = event_dir or EVENT_DIR
        self.event_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _file_for_today(self) -> Path:
        """Return the JSONL file path for today's events."""
        day = datetime.now().strftime("%Y%m%d")
        return self.event_dir / f"events_{day}.jsonl"

    def write(self, record: EventRecord) -> Path:
        """Append event record to today's JSONL log file.

        Args:
            record: EventRecord to persist

        Returns:
            Path to the JSONL file written
        """
        path = self._file_for_today()
        line = json.dumps(asdict(record), ensure_ascii=False)
        with self._lock:
            with open(path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        return path


def log_event(
    component: str,
    action: str,
    payload: Dict[str, Any],
    *,
    severity: str = "info",
    outcome: Optional[str] = None,
    task_type: Optional[str] = None,
    complexity: Optional[str] = None,
    agent: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    logger: Optional[EventLogger] = None,
) -> EventRecord:
    """Create, tag, and persist a structured event"""
    normalized = rs_normalize(payload)
    base = {
        "component": component,
        "action": action,
        "severity": severity,
        "outcome": outcome,
        "task_type": task_type,
        "complexity": complexity,
        "agent": agent,
    }
    base_tags = omnitag(base)

    rec = EventRecord(
        timestamp=datetime.now().isoformat(),
        event_id=str(uuid.uuid4()),
        schema_version=SCHEMA_VERSION,
        component=component,
        action=action,
        severity=severity,
        outcome=outcome,
        task_type=task_type,
        complexity=complexity,
        agent=agent,
        payload=payload,
        rs=normalized,
        tags=base_tags,
        context=context or {},
    )

    (logger or EventLogger()).write(rec)
    return rec


def export_event_index(event_dir: Optional[Path] = None) -> Path:
    """Create a simple summary index of recent events (counts per tag).

    Output: Reports/events/index.json
    """
    edir = event_dir or EVENT_DIR
    index: Dict[str, Any] = {
        "generated_at": datetime.now().isoformat(),
        "by_tag": {},
        "by_component": {},
    }

    for path in sorted(edir.glob("events_*.jsonl"))[-30:]:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                for t in e.get("tags", []):
                    index["by_tag"][t] = index["by_tag"].get(t, 0) + 1
                comp = e.get("component") or "unknown"
                index["by_component"][comp] = index["by_component"].get(comp, 0) + 1

    out = edir / "index.json"
    out.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return out
