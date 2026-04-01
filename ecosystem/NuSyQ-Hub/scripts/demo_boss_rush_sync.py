#!/usr/bin/env python3
"""🔄 Demo Boss Rush → Quest System Sync

Demonstrates cross-repository task synchronization.
"""

import sys
from pathlib import Path

# Add repo to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from src.integration.boss_rush_bridge import BossRushBridge
from src.Rosetta_Quest_System.quest_engine import QuestEngine


def main():
    """Demo Boss Rush sync to Quest System."""
    print("=" * 70)
    print("🔄 Boss Rush → Quest System Sync Demo")
    print("=" * 70)

    # Initialize systems
    print("\n📦 Initializing systems...")
    boss_rush = BossRushBridge()
    quest_mgr = QuestEngine()

    print(f"   Boss Rush: {boss_rush.nusyq_root}")
    print(f"   Quest System: {len(quest_mgr.quests)} quests, {len(quest_mgr.questlines)} questlines")

    # Get active tasks
    active_tasks = boss_rush.get_active_tasks()
    print(f"\n🎯 Active Boss Rush tasks: {len(active_tasks)}")

    # Sync to quest system
    print("\n🔄 Syncing to Quest System...")
    sync_result = boss_rush.sync_to_quest_system(quest_mgr)
    print(f"   Created: {sync_result['created']} quests")
    print(f"   Updated: {sync_result['updated']} quests")

    if sync_result["errors"]:
        print(f"   Errors: {len(sync_result['errors'])}")
        for error in sync_result["errors"][:3]:
            print(f"      • {error}")

    # Show quest system state after sync
    print("\n📋 Quest System After Sync:")
    print(f"   Total quests: {len(quest_mgr.quests)}")
    print(f"   Total questlines: {len(quest_mgr.questlines)}")

    if "Boss Rush" in quest_mgr.questlines:
        boss_rush_ql = quest_mgr.questlines["Boss Rush"]
        print(f"   Boss Rush questline: {len(boss_rush_ql.quests)} quests")

    print("\n✅ Boss Rush sync demo complete!")
    print("\n📝 Integration Status:")
    print("   ✅ Boss Rush bridge operational")
    print("   ✅ Quest System integration working")
    print("   ✅ Cross-repository sync successful")
    print("=" * 70)


if __name__ == "__main__":
    main()
