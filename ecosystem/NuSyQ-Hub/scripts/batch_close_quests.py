#!/usr/bin/env python3
"""Batch close duplicate/test quests from guild board.

Terminology:
- qid / quest_id: UUID string identifying a quest (QuestId type alias)
- qids: List of quest IDs (list[QuestId])
"""

import json
from datetime import UTC, datetime
from pathlib import Path

# Type alias for clarity (mirrors src/guild/guild_board.py)
QuestId = str


def main():
    guild_path = Path("state/guild/guild_board.json")
    close_path = Path("state/guild/closeable_quests.json")

    with guild_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    with close_path.open("r", encoding="utf-8") as f:
        closeable = json.load(f)

    close_ids = set(closeable.get("closeable_quest_ids", []))
    quests = data.get("quests", {})

    closed_count = 0
    now = datetime.now(UTC).isoformat()

    for qid in close_ids:
        if qid in quests and quests[qid].get("state") == "open":
            quests[qid]["state"] = "closed"
            quests[qid]["closed_at"] = now
            # Note: closed_reason not used - causes schema error in QuestEntry
            closed_count += 1

    data["quests"] = quests
    data["timestamp"] = now

    with guild_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Count remaining open
    remaining_open = sum(1 for q in quests.values() if q.get("state") == "open")

    print("=== Batch Close Complete ===")
    print(f"Closed: {closed_count} quests")
    print(f"Remaining open: {remaining_open}")

    # Show remaining open quests
    print("\n--- Remaining Open Quests ---")
    for _qid, quest in quests.items():
        if quest.get("state") == "open":
            title = quest.get("title", "")[:60]
            tags = quest.get("tags", [])
            print(f"  [{quest.get('priority', '?')}] {title}")
            print(f"      Tags: {', '.join(tags)}")


if __name__ == "__main__":
    main()
