#!/usr/bin/env python3
"""Sync PROJECT_STATUS_CHECKLIST.md work items into the Rosetta quest log."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

CHECKLIST_PATTERN = re.compile(r"^\s*-\s*\[\s*\]\s+(.*)")
CHECKLIST_PATH_DEFAULT = Path("docs/Checklists/PROJECT_STATUS_CHECKLIST.md")
QUEST_LOG_PATH_DEFAULT = Path("src/Rosetta_Quest_System/quest_log.jsonl")


def read_checklist_items(checklist_path: Path) -> list[str]:
    """Return unchecked checklist entries from the provided file."""
    if not checklist_path.exists():
        raise FileNotFoundError(f"Checklist missing: {checklist_path}")

    items: list[str] = []
    for line in checklist_path.read_text(encoding="utf-8").splitlines():
        match = CHECKLIST_PATTERN.match(line)
        if not match:
            continue
        item = match.group(1).strip()
        if item:
            items.append(item)
    return items


def slugify(text: str) -> str:
    """Create a filesystem-safe slug for the given text."""
    normalized = re.sub(r"[^a-z0-9]+", "_", text.lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized[:60] or "checklist_item"


def build_checklist_entry(item_text: str, checklist_path: Path) -> dict[str, object]:
    """Build a quest log entry for a checklist item."""
    source_hash = hashlib.sha1(item_text.encode("utf-8")).hexdigest()[:8]
    slug = slugify(item_text)
    quest_id = f"checklist_{slug}_{source_hash}"

    details = {
        "id": quest_id,
        "title": item_text,
        "description": f"Automatically promoted from {checklist_path.name}: {item_text}",
        "questline": "Project Checklist",
        "status": "pending",
        "priority": "medium",
        "tags": ["checklist_sync", "project_status"],
        "source": "project_status_checklist",
        "source_checklist_item": item_text,
        "source_checklist_id": source_hash,
        "created_at": datetime.utcnow().isoformat(),
        "agent_suggested": "checklist_syncer",
    }

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "add_quest",
        "details": details,
    }
    return entry


def load_existing_checklist_ids(quest_log_path: Path) -> set[str]:
    """Collect checklist identifiers already recorded in the quest log."""
    ids: set[str] = set()
    if not quest_log_path.exists():
        return ids

    with quest_log_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            details = entry.get("details", {}) or {}
            for key in ("id", "source_checklist_id"):
                if value := details.get(key):
                    ids.add(str(value))
    return ids


def append_checklist_entries(
    entries: Sequence[dict[str, object]],
    quest_log_path: Path,
    dry_run: bool = False,
) -> tuple[int, int]:
    """Add new checklist entries to the quest log, skipping duplicates."""
    existing_ids = load_existing_checklist_ids(quest_log_path)
    to_add: list[dict[str, object]] = []
    skipped = 0

    for entry in entries:
        details = entry.get("details", {}) or {}
        identifiers = {details.get("id"), details.get("source_checklist_id")}
        if any(identifier in existing_ids for identifier in identifiers if identifier):
            skipped += 1
            continue

        to_add.append(entry)
        if new_id := details.get("id"):
            existing_ids.add(str(new_id))
        if source_id := details.get("source_checklist_id"):
            existing_ids.add(str(source_id))

    if not dry_run:
        quest_log_path.parent.mkdir(parents=True, exist_ok=True)
        with quest_log_path.open("a", encoding="utf-8") as handle:
            for entry in to_add:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return len(to_add), skipped


def sync_project_checklist(
    checklist_path: Path,
    quest_log_path: Path,
    dry_run: bool = False,
    limit: int | None = None,
) -> tuple[int, int]:
    """Run the checklist sync workflow and return (added, skipped)."""
    items = read_checklist_items(checklist_path)
    if limit:
        items = items[:limit]

    entries = [build_checklist_entry(item, checklist_path) for item in items]
    added, skipped = append_checklist_entries(entries, quest_log_path, dry_run=dry_run)
    return added, skipped


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Promote checklist items into quests.")
    parser.add_argument(
        "--checklist-path",
        type=Path,
        default=CHECKLIST_PATH_DEFAULT,
        help="Checklist Markdown file to read",
    )
    parser.add_argument(
        "--quest-log-path",
        type=Path,
        default=QUEST_LOG_PATH_DEFAULT,
        help="Quest log to append entries to",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be added without writing",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit the number of checklist entries to sync",
    )

    args = parser.parse_args()

    try:
        added, skipped = sync_project_checklist(
            checklist_path=args.checklist_path,
            quest_log_path=args.quest_log_path,
            dry_run=args.dry_run,
            limit=args.limit,
        )
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        return 1

    print("=" * 60)
    print("PROJECT CHECKLIST SYNC")
    print("=" * 60)
    print(f"Checklist items scanned: {len(read_checklist_items(args.checklist_path))}")
    print(f"Quests added: {added}")
    print(f"Quests skipped (duplicates): {skipped}")
    if args.dry_run:
        print("Info: Dry run mode - no writes occurred.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
