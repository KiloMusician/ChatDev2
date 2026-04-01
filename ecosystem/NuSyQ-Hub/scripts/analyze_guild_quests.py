#!/usr/bin/env python3
"""Analyze guild quests and categorize them for bulk operations.

Terminology:
- qid / quest_id: UUID string identifying a quest (QuestId type alias)
- qids: List of quest IDs (list[QuestId])
"""

import json
from collections import defaultdict
from pathlib import Path

# Type alias for clarity (mirrors src/guild/guild_board.py)
QuestId = str


def main():
    guild_path = Path("state/guild/guild_board.json")
    with guild_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    quests = data.get("quests", {})
    print("\n=== Guild Quest Analysis ===")
    print(f"Total quests: {len(quests)}")

    # Categorize
    by_state = defaultdict(list)
    by_tag = defaultdict(list)
    by_title_prefix = defaultdict(list)
    duplicates = defaultdict(list)

    for qid, quest in quests.items():
        state = quest.get("state", "unknown")
        by_state[state].append(qid)

        for tag in quest.get("tags", []):
            by_tag[tag].append(qid)

        title = quest.get("title", "")
        prefix = title.split("]")[0] + "]" if "]" in title else title[:30]
        by_title_prefix[prefix].append(qid)

        # Track potential duplicates by similar title
        norm_title = title.lower().strip()
        duplicates[norm_title].append(qid)

    print("\n--- By State ---")
    for state, qids in sorted(by_state.items()):
        print(f"  {state}: {len(qids)}")

    print("\n--- Top Tags ---")
    for tag, qids in sorted(by_tag.items(), key=lambda x: -len(x[1]))[:10]:
        print(f"  {tag}: {len(qids)}")

    print("\n--- Exact Duplicates (same title) ---")
    dup_count = 0
    dup_ids = []
    for title, qids in duplicates.items():
        if len(qids) > 1:
            dup_count += len(qids) - 1  # Keep 1, count rest as duplicates
            dup_ids.extend(qids[1:])  # First is original, rest are duplicates
            if len(qids) <= 5:  # Only show small groups
                print(f"  '{title[:60]}': {len(qids)} copies")
    print(f"  TOTAL duplicates to close: {dup_count}")

    # Test quests (auto-generated for testing)
    test_quests = [
        qid
        for qid in quests
        if "test" in quests[qid].get("title", "").lower() and "auto-generated" in quests[qid].get("tags", [])
    ]
    print("\n--- Test/Auto-Generated Quests ---")
    print(f"  Closeable test quests: {len(test_quests)}")

    # Action summary
    print("\n=== Recommended Actions ===")
    print(f"1. Close {dup_count} duplicate quests (same exact title)")
    print(f"2. Close {len(test_quests)} test/auto-generated quests")
    print(f"3. Review remaining {len(quests) - dup_count - len(test_quests)} real quests")

    # Output closeable quest IDs
    closeable = set(dup_ids) | set(test_quests)
    print(f"\nTotal closeable: {len(closeable)} quests")

    # Save closeable IDs
    output = {"closeable_quest_ids": list(closeable), "reason": "duplicates_or_test"}
    with open("state/guild/closeable_quests.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print("\nSaved closeable IDs to state/guild/closeable_quests.json")


if __name__ == "__main__":
    main()
