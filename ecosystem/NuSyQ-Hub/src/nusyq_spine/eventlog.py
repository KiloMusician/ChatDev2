"""Simple JSONL event logger for the NuSyQ spine."""

import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVENTS_PATH = ROOT / "state" / "events.jsonl"
EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)


def append_event(event: dict) -> None:
    """Append a compact event dict to the JSONL event log.

    Event schema (compact): trace_id, actor, action, inputs_hash, outputs_hash, timestamp, status
    """
    if not isinstance(event, dict):
        raise TypeError("event must be a dict")
    event = dict(event)
    event.setdefault("timestamp", datetime.now(UTC).isoformat().replace("+00:00", "Z"))
    with open(EVENTS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def read_events(limit: int = 100) -> list[dict]:
    res: list[dict] = []
    if not EVENTS_PATH.exists():
        return res
    with open(EVENTS_PATH, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            try:
                res.append(json.loads(line))
            except (json.JSONDecodeError, ValueError):
                continue
    return res
