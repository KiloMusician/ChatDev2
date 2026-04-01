#!/usr/bin/env python3
"""Sync quests from ecosystem to guild board"""

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.guild.guild_board import GuildBoard


async def sync_quests():
    """Sync quests from quest_assignments.json to guild board."""
    quest_file = ROOT / "data" / "ecosystem" / "quest_assignments.json"
    if not quest_file.exists():
        print("❌ Quest assignments file not found")
        return

    # Load quest assignments
    with open(quest_file) as f:
        assignments = json.load(f)

    board = GuildBoard()

    synced = 0
    for agent_id, quest_list in assignments.get("assignments", {}).items():
        for quest_data in quest_list:
            quest_id = quest_data.get("quest_id", f"quest-{synced}")
            title = quest_data.get("title", quest_data.get("task", "Untitled Quest"))
            description = quest_data.get("description", "")
            priority = quest_data.get("priority", 3)
            safety_tier = quest_data.get("safety_tier", "standard")
            tags = quest_data.get("tags", [])

            # Add to board using method signature
            success, added_id = await board.add_quest(
                quest_id=quest_id,
                title=title,
                description=description,
                priority=priority,
                safety_tier=safety_tier,
                tags=tags,
            )

            if success:
                # If this quest is assigned, claim it
                if quest_data.get("status") == "assigned":
                    await board.claim_quest(added_id, agent_id)
                synced += 1

    print(f"✅ Synced {synced} quests to guild board")
    print(f"📊 Total quests on board: {len(board.board.quests)}")


if __name__ == "__main__":
    asyncio.run(sync_quests())
