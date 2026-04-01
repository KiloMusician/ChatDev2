"""Simple state store for NuSyQ spine (rotating snapshot)."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "state" / "state.json"
STATE_PATH.parent.mkdir(parents=True, exist_ok=True)


def snapshot_state(extra: dict | None = None) -> dict[str, Any]:
    data = {
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "status": "ok",
    }
    if extra:
        data.update(extra)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


def read_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {}
    with open(STATE_PATH, encoding="utf-8") as f:
        return cast(dict[str, Any], json.load(f))
