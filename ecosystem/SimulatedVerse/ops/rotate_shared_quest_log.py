#!/usr/bin/env python3
"""Rotate the oversized shared cultivation quest log into archives."""

from __future__ import annotations

import argparse
import gzip
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = ROOT / "shared_cultivation"
QUEST_LOG_PATH = SHARED_DIR / "quest_log.jsonl"
ARCHIVE_DIR = SHARED_DIR / "archive"
STATUS_PATH = SHARED_DIR / "quest_log_rotation_status.json"
DEFAULT_MAX_BYTES = 5_000_000
DEFAULT_KEEP_LINES = 10_000


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def byte_len(lines: list[str]) -> int:
    return sum(len(line.encode("utf-8")) for line in lines)


def build_rotation_plan(lines: list[str], max_bytes: int, keep_lines: int) -> tuple[list[str], list[str]]:
    if not lines:
        return [], []
    kept = lines[-keep_lines:] if keep_lines > 0 else []
    if not kept:
        kept = lines[-1:]
    while len(kept) > 1 and byte_len(kept) > max_bytes:
        kept = kept[1:]
    archived = lines[: len(lines) - len(kept)]
    return archived, kept


def write_status(payload: dict) -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Apply the rotation instead of reporting only.")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--keep-lines", type=int, default=DEFAULT_KEEP_LINES)
    args = parser.parse_args()

    SHARED_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    lines = QUEST_LOG_PATH.read_text(encoding="utf-8").splitlines(keepends=True) if QUEST_LOG_PATH.exists() else []
    current_size = QUEST_LOG_PATH.stat().st_size if QUEST_LOG_PATH.exists() else 0
    archived_lines, kept_lines = build_rotation_plan(lines, args.max_bytes, args.keep_lines)
    needs_rotation = current_size > args.max_bytes and bool(archived_lines)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_path = ARCHIVE_DIR / f"quest_log_{timestamp}.jsonl.gz"

    payload = {
        "generated_at": iso_now(),
        "tool": "rotate_shared_quest_log",
        "quest_log_path": str(QUEST_LOG_PATH).replace("\\", "/"),
        "archive_dir": str(ARCHIVE_DIR).replace("\\", "/"),
        "max_bytes": args.max_bytes,
        "keep_lines": args.keep_lines,
        "current_size_bytes": current_size,
        "line_count": len(lines),
        "needs_rotation": needs_rotation,
        "apply_requested": args.apply,
        "archived_line_count": len(archived_lines),
        "kept_line_count": len(kept_lines),
        "projected_size_bytes": byte_len(kept_lines),
        "proposed_archive_path": str(archive_path).replace("\\", "/") if needs_rotation else None,
        "status": "noop",
    }

    if args.apply and needs_rotation:
        with gzip.open(archive_path, "wt", encoding="utf-8") as handle:
            handle.writelines(archived_lines)
        QUEST_LOG_PATH.write_text("".join(kept_lines), encoding="utf-8")
        payload["status"] = "rotated"
        payload["archive_path"] = str(archive_path).replace("\\", "/")
        payload["current_size_bytes"] = QUEST_LOG_PATH.stat().st_size
    elif needs_rotation:
        payload["status"] = "rotation_recommended"

    write_status(payload)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
