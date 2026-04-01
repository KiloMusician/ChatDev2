#!/usr/bin/env python3
"""Quest System Status Reporter"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.Rosetta_Quest_System.quest_engine import QuestEngine


def main():
    engine = QuestEngine()
    quests = engine.list_quests()

    completed = [q for q in quests if q["status"] == "completed"]
    in_progress = [q for q in quests if q["status"] == "in_progress"]
    pending = [q for q in quests if q["status"] == "pending"]

    print("=" * 60)
    print("🎯 QUEST SYSTEM STATUS REPORT")
    print("=" * 60)
    print()
    print(f"📊 Overall Progress: {len(completed)}/{len(quests)} quests completed")
    print(f"   ✅ Completed: {len(completed)}")
    print(f"   🔄 In Progress: {len(in_progress)}")
    print(f"   📋 Pending: {len(pending)}")
    print()

    if completed:
        print("✅ Completed Quests:")
        for q in completed:
            print(f"   {q['id']}: {q['title']}")
        print()

    if in_progress:
        print("🔄 In Progress:")
        for q in in_progress:
            print(f"   {q['id']}: {q['title']}")
        print()

    if pending:
        print("📋 Pending Quests:")
        for q in pending:
            print(f"   {q['id']}: {q['title']}")
        print()

    print("=" * 60)


if __name__ == "__main__":
    main()
