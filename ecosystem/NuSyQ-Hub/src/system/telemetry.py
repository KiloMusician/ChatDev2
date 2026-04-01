"""Lightweight telemetry stubs (Phase 5 prep).

Provides structured span-like logging to a mission control report file.
Can be upgraded to full OpenTelemetry later.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from src.config.feature_flag_manager import is_feature_enabled

REPORT_PATH = Path("state") / "reports" / "mission_control_latest.json"


def log_span(name: str, attributes: dict[str, Any]) -> None:
    if not is_feature_enabled("mission_control_enabled"):
        return
    entry = {
        "ts": time.time(),
        "span": name,
        "attributes": attributes,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {"spans": []}
    if REPORT_PATH.exists():
        try:
            data = json.loads(REPORT_PATH.read_text())
        except Exception:
            data = {"spans": []}
    data.setdefault("spans", []).append(entry)
    REPORT_PATH.write_text(json.dumps(data, indent=2))


def health_gate(status: str, details: dict[str, Any]) -> None:
    log_span("health_gate", {"status": status, **details})
