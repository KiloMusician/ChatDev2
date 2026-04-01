#!/usr/bin/env python3
"""Index obsolete current_state archives into a compact canonical summary."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_DIR = ROOT / "archive" / "obsolete"
OUTPUT_JSON = ROOT / "state" / "reports" / "obsolete_current_state_archive_index.json"
OUTPUT_MD = ROOT / "state" / "reports" / "obsolete_current_state_archive_summary.md"


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize(path: Path) -> str:
    return str(path).replace("\\", "/")


def parse_timestamp(name: str) -> str | None:
    match = re.search(r"current_state_(\d{4}-\d{2}-\d{2})[_-](\d{6})", name)
    if match:
        stamp = f"{match.group(1)}T{match.group(2)}Z"
        return stamp
    match = re.search(r"current_state_(\d{8})_(\d{6})", name)
    if match:
        stamp = f"{match.group(1)}T{match.group(2)}Z"
        return stamp
    return None


def read_title(path: Path) -> str:
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if stripped:
                return stripped[:140]
    except OSError:
        return "unreadable"
    return "empty"


def main() -> int:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(ARCHIVE_DIR.glob("current_state_*.md"))
    entries = []
    month_counter: Counter[str] = Counter()

    for path in files:
        timestamp = parse_timestamp(path.name)
        month_bucket = timestamp[:7] if timestamp else "unknown"
        month_counter[month_bucket] += 1
        entries.append(
            {
                "name": path.name,
                "path": normalize(path),
                "size_bytes": path.stat().st_size,
                "timestamp": timestamp,
                "title": read_title(path),
            }
        )

    total_bytes = sum(entry["size_bytes"] for entry in entries)
    newest = max(entries, key=lambda entry: entry["timestamp"] or "", default=None)
    oldest = min(entries, key=lambda entry: entry["timestamp"] or "9999", default=None)

    payload = {
        "generated_at": iso_now(),
        "artifact_authority": "generated canonical archive index",
        "source_path": normalize(ARCHIVE_DIR),
        "file_count": len(entries),
        "total_bytes": total_bytes,
        "oldest": oldest,
        "newest": newest,
        "monthly_counts": dict(sorted(month_counter.items())),
        "latest_entries": sorted(
            entries,
            key=lambda entry: entry["timestamp"] or "",
            reverse=True,
        )[:12],
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Obsolete Current State Archive Summary",
        "",
        "Artifact authority: generated canonical archive summary",
        "",
        f"- Generated: `{payload['generated_at']}`",
        f"- Source: `{payload['source_path']}`",
        f"- File count: `{payload['file_count']}`",
        f"- Total bytes: `{payload['total_bytes']}`",
        f"- Oldest: `{oldest['name'] if oldest else 'n/a'}`",
        f"- Newest: `{newest['name'] if newest else 'n/a'}`",
        "",
        "## Monthly Counts",
        "",
    ]
    for month, count in payload["monthly_counts"].items():
        lines.append(f"- `{month}`: `{count}`")
    lines.extend(["", "## Latest Entries", ""])
    for entry in payload["latest_entries"]:
        lines.append(f"- `{entry['name']}`: {entry['title']}")
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"index": normalize(OUTPUT_JSON), "summary": normalize(OUTPUT_MD), "count": len(entries)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
