#!/usr/bin/env python3
"""Convert TODO comments to structured quest items.

This script scans for TODO/FIXME/XXX comments and converts them into
structured quest items in the Rosetta Quest System.

Usage:
    python scripts/todos_to_quests.py [--limit N] [--dry-run]
"""

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.LOGGING.modular_logging_system import get_logger

logger = get_logger(__name__)

QUEST_LOG_PATH = Path("src/Rosetta_Quest_System/quest_log.jsonl")


def _is_meaningful_description(text: str) -> bool:
    """Reject punctuation-only TODO payloads."""
    stripped = text.strip()
    if not stripped:
        return False
    alnum_count = sum(1 for ch in stripped if ch.isalnum())
    if alnum_count < 3:
        return False
    return True


def extract_todos(directory: Path = Path("src")) -> list[dict[str, Any]]:
    """Extract TODO comments from source files.

    Args:
        directory: Directory to scan

    Returns:
        List of TODO items with file, line, and description
    """
    todos = []
    pattern = re.compile(r"^\s*#\s*(TODO|FIXME|XXX|HACK):?\s*(.+)", re.IGNORECASE)

    for py_file in directory.rglob("*.py"):
        if ".venv" in str(py_file) or "__pycache__" in str(py_file):
            continue

        try:
            lines = py_file.read_text(encoding="utf-8").split("\n")
            for line_num, line in enumerate(lines, 1):
                match = pattern.match(line)
                if match:
                    marker, description = match.groups()
                    description = description.strip()
                    if not _is_meaningful_description(description):
                        continue
                    try:
                        relpath = str(py_file.relative_to(Path.cwd()))
                    except ValueError:
                        relpath = str(py_file)

                    todos.append(
                        {
                            "file": relpath,
                            "line": line_num,
                            "marker": marker.upper(),
                            "description": description,
                            "priority": "high" if marker.upper() == "FIXME" else "medium",
                        }
                    )
        except Exception as e:
            # modular logger expects a single message string
            logger.error(f"Failed to process {py_file}: {e}")

    return todos


def create_quest_from_todo(todo: dict[str, Any]) -> dict[str, Any]:
    """Convert a TODO item into a quest format.

    Args:
        todo: TODO item dict

    Returns:
        Quest item dict
    """
    quest = {
        "id": f"TODO_{todo['file'].replace('/', '_').replace('.py', '')}_{todo['line']}",
        "title": f"{todo['marker']}: {todo['description'][:60]}",
        "description": todo["description"],
        "source": "automated_todo_conversion",
        "location": {"file": todo["file"], "line": todo["line"]},
        "priority": todo["priority"],
        "tags": ["todo", todo["marker"].lower(), "code-quality"],
        "created_at": datetime.now(UTC).isoformat(),
        "status": "pending",
        "agent_suggested": "copilot",
        "estimated_effort": "15min" if todo["marker"] == "TODO" else "30min",
    }

    return quest


def append_quests_to_log(quests: list[dict[str, Any]], dry_run: bool = False) -> int:
    """Append quests to the quest log.

    Args:
        quests: List of quest dicts
        dry_run: If True, only print what would be added

    Returns:
        Number of quests added
    """
    if dry_run:
        logger.info(f"[DRY RUN] Would add {len(quests)} quests")
        return 0

    # Ensure quest log directory exists
    QUEST_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Load existing quest IDs to avoid duplicates
    existing_ids = set()
    if QUEST_LOG_PATH.exists():
        try:
            with open(QUEST_LOG_PATH, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        if "id" in entry:
                            existing_ids.add(entry["id"])
        except Exception as e:
            logger.error(f"Failed to read existing quests: {e}")

    # Append new quests
    added = 0
    with open(QUEST_LOG_PATH, "a", encoding="utf-8") as f:
        for quest in quests:
            if quest["id"] not in existing_ids:
                f.write(json.dumps(quest) + "\n")
                added += 1
                logger.info(f"Added quest: {quest['id']}")

    return added


def main():
    """Execute TODO to quest conversion."""
    parser = argparse.ArgumentParser(description="Convert TODOs to quest items")
    parser.add_argument("--limit", type=int, help="Limit number of quests to create")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created")
    parser.add_argument("--priority", choices=["high", "medium", "low"], help="Filter by priority")
    args = parser.parse_args()

    print("=" * 60)
    print("TODO TO QUEST CONVERTER")
    print("=" * 60)
    if args.dry_run:
        print("🔍 DRY RUN MODE")
    print()

    # Extract TODOs
    print("📝 Scanning for TODO comments...")
    todos = extract_todos()
    print(f"Found {len(todos)} TODO items")

    # Filter by priority if specified
    if args.priority:
        todos = [t for t in todos if t["priority"] == args.priority]
        print(f"Filtered to {len(todos)} {args.priority} priority items")

    # Limit if specified
    if args.limit:
        todos = todos[: args.limit]
        print(f"Limited to {args.limit} items")

    # Convert to quests
    print("\n🎯 Creating quest items...")
    quests = [create_quest_from_todo(todo) for todo in todos]

    # Show sample
    if quests:
        print("\nSample quest:")
        print(json.dumps(quests[0], indent=2))

    # Append to quest log
    print(f"\n💾 Adding quests to {QUEST_LOG_PATH}...")
    added = append_quests_to_log(quests, dry_run=args.dry_run)

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"TODOs found: {len(extract_todos())}")
    print(f"Quests created: {len(quests)}")
    if not args.dry_run:
        print(f"Quests added: {added} (duplicates skipped)")
    print()

    if args.dry_run:
        print("✅ Dry run complete - use without --dry-run to add quests")
    else:
        print("✅ Quest conversion complete!")
        print(f"View quests: cat {QUEST_LOG_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
