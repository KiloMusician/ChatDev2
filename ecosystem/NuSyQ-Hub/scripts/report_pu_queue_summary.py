#!/usr/bin/env python3
"""Generate human-readable summaries for the PU queue report and Culture Ship cycle log.

This script consumes the JSON produced by `python -m src.automation.unified_pu_queue report`
and the log produced by `scripts/test_culture_ship_cycle.py`, then writes a short markdown
summary for dashboards or guild boards.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def load_report(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_cycle_log(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if not path.exists():
        return entries

    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def build_summary(report: dict[str, Any], recent_limit: int = 5) -> str:
    stats = report.get("statistics", {})
    recent = report.get("recent", [])[-recent_limit:]
    lines = [
        "# PU Queue Summary",
        f"- Generated: {report.get('generated_at', datetime.now().isoformat())}",
        f"- Total PUs: {stats.get('total_pus', 0)}",
        f"- Completion rate: {stats.get('completion_rate', 0):.1%}",
        "",
        "## Breakdowns",
        "### By Status",
    ]
    for status, count in stats.get("by_status", {}).items():
        lines.append(f"- {status}: {count}")
    lines.append("### By Repository")
    for repo, count in stats.get("by_repository", {}).items():
        lines.append(f"- {repo}: {count}")
    lines.append("### By Type")
    for pu_type, count in stats.get("by_type", {}).items():
        lines.append(f"- {pu_type}: {count}")
    lines.append("")
    lines.append(f"## Recent PUs (last {len(recent)} entries)")
    for pu in recent:
        lines.append(f"- **{pu['id']}** ({pu['status']}) - {pu['title']} [{pu['priority']} / {pu['source_repo']}]")
    return "\n".join(lines)


def build_culture_ship_summary(entries: list[dict[str, Any]], limit: int = 5) -> str:
    lines = [
        "# Culture Ship Cycle Log",
        f"- Total rounds logged: {len(entries)}",
        "",
        f"## Latest {min(limit, len(entries))} summaries",
    ]
    for entry in entries[-limit:]:
        lines.append(
            f"- {entry.get('timestamp')} - Issues {entry.get('issues_identified')} | "
            f"Decisions {entry.get('decisions_made')} | Fixes {entry.get('total_fixes_applied')}"
        )
    return "\n".join(lines)


def write_summary(report_path: Path, log_path: Path, output_path: Path) -> None:
    report = load_report(report_path)
    entries = load_cycle_log(log_path)
    output_lines = [
        build_summary(report),
        "",
        build_culture_ship_summary(entries),
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(output_lines), encoding="utf-8")


def main() -> int:
    report_path = Path("reports/pu_queue_status.json")
    log_path = Path("reports/culture_ship_cycle.log")
    output_path = Path("reports/pu_queue_summary.md")
    if not report_path.exists():
        print(f"Report missing: {report_path}")
        return 1

    write_summary(report_path, log_path, output_path)
    print(f"PU queue summary saved to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
