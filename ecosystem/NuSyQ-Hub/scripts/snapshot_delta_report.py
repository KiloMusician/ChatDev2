#!/usr/bin/env python3
"""Generate delta reports from the latest system snapshots."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

STATE_DIR = Path("state/reports")
REPORTS_DIR = Path("reports")
QUEST_LOG_FILE = Path("src/Rosetta_Quest_System/quest_log.jsonl")
GUILD_EVENTS_FILE = Path("state/guild/guild_events.jsonl")

METRIC_LINE_RE = re.compile(r"-\s+([^:]+):\s*`([^`]*)`")


def _collect_state_files() -> list[Path]:
    files = sorted(STATE_DIR.glob("current_state*.md"), key=lambda p: p.stat().st_mtime)
    return files


def _parse_state(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {
        "snapshot": None,
        "timestamp": None,
        "metrics": {},
        "changes": [],
    }
    mode: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            mode = None
            continue
        if line.startswith("- **Snapshot ID**"):
            data["snapshot"] = line.split(":", 1)[1].strip(" `")
            continue
        if line.startswith("- Timestamp"):
            data["timestamp"] = line.split(":", 1)[1].strip(" `")
            continue
        if line.startswith("##"):
            if "Current Metrics" in line:
                mode = "metrics"
            elif "Changes Since" in line:
                mode = "changes"
            else:
                mode = None
            continue
        if mode == "metrics":
            match = METRIC_LINE_RE.match(line)
            if match:
                key, value = match.groups()
                data["metrics"][key] = value
        elif mode == "changes" and line.startswith("- "):
            data["changes"].append(line[2:].strip())
    return data


def _format_metric_diff(current: dict[str, Any], previous: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    keys = set(current["metrics"]) | set(previous["metrics"])
    for key in sorted(keys):
        cur_val = current["metrics"].get(key)
        prev_val = previous["metrics"].get(key)
        if cur_val is None or prev_val is None:
            continue
        if cur_val.isdigit() and prev_val.isdigit():
            cur_num = int(cur_val)
            prev_num = int(prev_val)
            diff = cur_num - prev_num
            indicator = f" ({'+' if diff >= 0 else ''}{diff} since {prev_num})" if diff != 0 else " (unchanged)"
            lines.append(f"- {key}: {cur_num}{indicator}")
        else:
            if cur_val != prev_val:
                lines.append(f"- {key}: {cur_val} (was {prev_val})")
    return lines


def _write_report(content: str, filename: str) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / filename
    path.write_text(content, encoding="utf-8")
    return path


def _append_quest(report_path: Path) -> None:
    details = {
        "id": f"snapshot_delta_{int(datetime.utcnow().timestamp())}",
        "title": "Capture snapshot delta",
        "description": "Logged a delta summary between the last two current_state reports.",
        "questline": "System Maintenance",
        "status": "completed",
        "dependencies": [],
        "tags": ["snapshot", "delta", "ops"],
        "proof": [str(report_path)],
    }
    entry = {"timestamp": datetime.utcnow().isoformat(), "event": "add_quest", "details": details}
    QUEST_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with QUEST_LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _append_guild_event(report_path: Path) -> None:
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "snapshot_delta",
        "data": {
            "message": "Snapshot delta report generated",
            "report": str(report_path),
        },
    }
    GUILD_EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with GUILD_EVENTS_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def main() -> int:
    files = _collect_state_files()
    if len(files) < 2:
        print("Not enough snapshots to compute deltas; run auto_cycle to generate more.")
        return 0
    previous, latest = files[-2], files[-1]
    previous_state = _parse_state(previous)
    latest_state = _parse_state(latest)
    diffs = _format_metric_diff(latest_state, previous_state)

    lines = ["# Snapshot Delta Report", "", f"Generated: {datetime.utcnow().isoformat()}", ""]
    lines.append(f"- Latest: {latest.name} ({latest_state.get('timestamp')})")
    lines.append(f"- Previous: {previous.name} ({previous_state.get('timestamp')})")
    lines.append("")
    lines.append("## Metric Deltas")
    if diffs:
        lines.extend(diffs)
    else:
        lines.append("- No metric changes detected")
    lines.append("")
    lines.append("## Latest Changes Since Last Snapshot")
    changes = latest_state.get("changes") or []
    if changes:
        lines.extend(f"- {c}" for c in changes)
    else:
        lines.append("- (no change details available)")

    report_path = _write_report("\n".join(lines), "snapshot_delta_report.md")
    _append_quest(report_path)
    _append_guild_event(report_path)
    print(f"Snapshot delta report written to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
