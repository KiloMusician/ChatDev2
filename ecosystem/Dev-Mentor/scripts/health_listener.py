#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = BASE_DIR / "state" / "runtime" / "hub_health_probe.jsonl"
MAX_LOG_AGE_SECONDS = 300
CRITICAL_FLAGS = {
    "api_health_unreachable",
    "api_status_unreachable",
    "status_file_missing",
}


def parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_latest_record() -> dict[str, Any] | None:
    if not LOG_FILE.exists():
        return None
    try:
        lines = [
            line.strip()
            for line in LOG_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if not lines:
            return None
        return json.loads(lines[-1])
    except Exception:
        return None


def classify(record: dict[str, Any] | None) -> dict[str, Any]:
    if not record:
        return {
            "ok": False,
            "critical": False,
            "reason": "hub_probe_log_missing",
            "record": None,
        }

    stamp = parse_iso(record.get("ts"))
    if not stamp:
        return {
            "ok": False,
            "critical": False,
            "reason": "hub_probe_timestamp_invalid",
            "record": record,
        }
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=UTC)
    age_seconds = (datetime.now(UTC) - stamp).total_seconds()
    if age_seconds > MAX_LOG_AGE_SECONDS:
        return {
            "ok": False,
            "critical": False,
            "reason": "hub_probe_stale",
            "age_seconds": round(age_seconds, 2),
            "record": record,
        }

    drift_flags = set(record.get("drift_flags") or [])
    healthy = bool(record.get("healthy"))
    consecutive_failures = int(record.get("consecutive_failures") or 0)
    critical = bool(
        record.get("manual_intervention_required")
        or consecutive_failures >= 3
        or drift_flags.intersection(CRITICAL_FLAGS)
    )

    reason = (
        "healthy"
        if healthy and not critical
        else "hub_critical" if critical else "hub_degraded"
    )
    return {
        "ok": True,
        "healthy": healthy,
        "critical": critical,
        "reason": reason,
        "drift_flags": sorted(drift_flags),
        "consecutive_failures": consecutive_failures,
        "ts": record.get("ts"),
        "age_seconds": round(age_seconds, 2),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Classify the latest NuSyQ-Hub probe result for orchestration gating."
    )
    parser.add_argument(
        "--once", action="store_true", help="Emit the current classification as JSON"
    )
    parser.parse_args(argv)
    print(json.dumps(classify(load_latest_record()), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
