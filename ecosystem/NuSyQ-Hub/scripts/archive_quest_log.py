#!/usr/bin/env python3
"""Archive large quest log file and keep only recent entries.

Moves old quest log to archives and keeps the most recent N entries.
"""

import json
from datetime import datetime
from pathlib import Path


def archive_quest_log(keep_recent: int = 500) -> None:
    """Archive quest log and keep only recent entries."""
    base_path = Path(__file__).resolve().parents[1]
    quest_log_path = base_path / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
    archives_dir = base_path / "data" / "Rosetta_Quest_System" / "archives"

    # Create archives directory
    archives_dir.mkdir(parents=True, exist_ok=True)

    if not quest_log_path.exists():
        print(f"Quest log not found: {quest_log_path}")
        return

    # Read all entries
    entries = []
    with open(quest_log_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    print(f"Total quest log entries: {len(entries)}")

    if len(entries) <= keep_recent:
        print(f"Quest log has {len(entries)} entries, no archival needed (threshold: {keep_recent})")
        return

    # Archive old entries
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = archives_dir / f"quest_log_archive_{date_str}.jsonl"

    old_entries = entries[:-keep_recent]
    recent_entries = entries[-keep_recent:]

    # Write old entries to archive
    with open(archive_path, "w", encoding="utf-8") as f:
        for entry in old_entries:
            f.write(json.dumps(entry) + "\n")

    print(f"✓ Archived {len(old_entries)} old entries to: {archive_path.name}")

    # Keep only recent entries in main log
    with open(quest_log_path, "w", encoding="utf-8") as f:
        for entry in recent_entries:
            f.write(json.dumps(entry) + "\n")

    print(f"✓ Kept {len(recent_entries)} recent entries in quest_log.jsonl")

    # Calculate size reduction
    original_size = quest_log_path.stat().st_size if quest_log_path.exists() else 0
    archive_size = archive_path.stat().st_size

    print("\nSize reduction:")
    print(f"  Archive: {archive_size / 1024:.1f} KB")
    print(f"  Current log: {original_size / 1024:.1f} KB (after cleanup)")


if __name__ == "__main__":
    archive_quest_log(keep_recent=500)
