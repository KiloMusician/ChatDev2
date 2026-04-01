"""Migrate `src/Rosetta_Quest_System/quest_log.jsonl` into the SQL tasks table.

Usage:
  python scripts/migrate_quest_log.py
"""

import json
from pathlib import Path

from src.task_runtime.db import Database


def migrate(quest_log_path: Path, db: Database):
    if not quest_log_path.exists():
        print("No quest_log.jsonl found at", quest_log_path)
        return 0

    inserted = 0
    with quest_log_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                q = json.loads(line)
            except json.JSONDecodeError:
                # skip malformed
                continue

            title = q.get("title") or q.get("objective") or q.get("name") or "Unnamed Quest"
            meta = json.dumps(q)
            # naive: create a task per quest
            db.execute(
                "INSERT INTO tasks (project_id, objective, metadata, status) VALUES (?, ?, ?, 'pending')",
                (None, title, meta),
            )
            inserted += 1

    print(f"Inserted {inserted} quests into tasks table")
    return inserted


def main():
    repo_root = Path(__file__).resolve().parents[1]
    quest_log = repo_root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
    db = Database()
    migrate(quest_log, db)


if __name__ == "__main__":
    main()
