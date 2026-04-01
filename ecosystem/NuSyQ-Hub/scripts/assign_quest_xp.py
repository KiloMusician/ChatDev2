#!/usr/bin/env python3
"""Assign XP Values to Quests

Assigns XP values to completed quests based on tags and complexity.
Calculates retroactive XP earnings for the quest system.

XP Formula:
- easy: 100 XP
- medium: 250 XP
- hard: 500 XP
- epic: 1000 XP
- Multipliers for special tags

OmniTag: [quests, xp, gamification]
"""

import argparse
import json
from pathlib import Path


def calculate_xp(quest: dict) -> int:
    """Calculate XP for a quest based on tags and complexity."""
    tags = quest.get("tags", [])

    # Base XP from complexity
    base_xp = 100  # default
    for tag in tags:
        if tag == "easy":
            base_xp = 100
        elif tag == "medium":
            base_xp = 250
        elif tag == "hard":
            base_xp = 500
        elif tag == "epic":
            base_xp = 1000

    # Multipliers for special quest types
    multiplier = 1.0
    special_tags = set(tags)

    if "critical" in special_tags:
        multiplier += 0.5
    if "architecture" in special_tags:
        multiplier += 0.3
    if "performance" in special_tags:
        multiplier += 0.2
    if "security" in special_tags:
        multiplier += 0.4
    if "integration" in special_tags:
        multiplier += 0.2

    return int(base_xp * multiplier)


def assign_quest_xp(award_skill: str | None = None, award_game: bool = False):
    """Assign XP values to all completed quests."""
    quest_file = Path("src/Rosetta_Quest_System/quests.json")
    quests = json.load(quest_file.open())

    total_xp = 0
    updated_count = 0

    for quest in quests:
        # Only assign XP to completed quests
        if quest.get("status") in ("completed", "complete"):
            # Skip if already has XP
            if quest.get("xp", 0) == 0:
                xp = calculate_xp(quest)
                quest["xp"] = xp
                total_xp += xp
                updated_count += 1
            else:
                total_xp += quest.get("xp", 0)

    # Save updated quests
    with quest_file.open("w") as f:
        json.dump(quests, f, indent=2)

    completed = sum(1 for q in quests if q.get("status") in ("completed", "complete"))

    print(f"✅ Assigned XP to {updated_count} quests")
    print(f"📊 Total XP earned: {total_xp}")
    print(f"🎯 Completed quests: {completed}")
    print(f"📈 Average XP per quest: {total_xp // completed if completed > 0 else 0}")

    if award_skill and total_xp > 0:
        try:
            from src.system.rpg_inventory import award_xp

            award_fn = None
            if award_game:
                try:
                    from src.api.systems import award_game_progress

                    award_fn = award_game_progress
                except Exception:
                    award_fn = None

            result = award_xp(award_skill, total_xp, award_game_fn=award_fn)
            print(f"✅ Awarded {total_xp} XP to skill '{award_skill}'")
            if result.get("game_award"):
                print("🏆 Game award applied")
        except Exception as exc:
            print(f"⚠️  XP award failed: {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Assign XP to completed quests.")
    parser.add_argument("--award-skill", help="Skill name to award total XP to")
    parser.add_argument(
        "--award-game",
        action="store_true",
        help="Also award game XP/achievement via game award endpoint (best-effort)",
    )
    args = parser.parse_args()
    assign_quest_xp(award_skill=args.award_skill, award_game=args.award_game)
