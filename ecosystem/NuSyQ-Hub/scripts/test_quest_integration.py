#!/usr/bin/env python3
"""Test PU → Quest integration."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from Rosetta_Quest_System.quest_engine import QuestEngine


def test_pu_to_quest_conversion():
    """Test that the autonomous loop can create quests from PUs."""
    engine = QuestEngine()

    # Check initial state
    print("📊 Initial State:")
    print(f"   Total quests: {len(engine.quests)}")
    print(f"   Questlines: {list(engine.questlines.keys())}\n")

    # Load PU queue
    queue_file = Path(__file__).parent.parent / "data" / "unified_pu_queue.json"
    if not queue_file.exists():
        print("❌ PU queue file not found")
        return False

    with open(queue_file) as f:
        pus = json.load(f)

    # Check for eligible PUs (completed without quest reference)
    eligible_pus = [p for p in pus if p.get("status") == "completed" and not p.get("associated_quest_id")]

    print("🔍 PU Queue Analysis:")
    print(f"   Total PUs: {len(pus)}")
    print(f"   Completed PUs: {len([p for p in pus if p.get('status') == 'completed'])}")
    print(f"   Eligible for quest conversion: {len(eligible_pus)}\n")

    if eligible_pus:
        print(f"✅ Found {len(eligible_pus)} eligible PUs for conversion:")
        for pu in eligible_pus[:3]:
            print(f"   - {pu['type']}: {pu['title'][:50]}")
        print()
    else:
        print("⚠️  No eligible PUs found without associated quest IDs\n")

    # Simulate the quest creation logic from autonomous_loop
    created_quests = 0
    for pu in eligible_pus[:3]:  # Test with first 3
        pu_type = pu.get("type", "AnalysisPU")

        # Map to questline
        pu_type_map = {
            "BugFixPU": "Bug Fixes",
            "RefactorPU": "Refactoring",
            "FeaturePU": "Features",
            "DocPU": "Documentation",
            "AnalysisPU": "Analysis & Audits",
            "TestPU": "Testing",
        }
        questline = pu_type_map.get(pu_type, "Autonomous")

        # Create quest
        quest_id = engine.add_quest(
            title=pu.get("title", f"Task: {pu.get('id')}"),
            description=f"Auto-converted from PU {pu.get('id')}",
            questline=questline,
            tags=[pu_type, "autonomous"],
            priority=pu.get("priority", "medium"),
        )

        if quest_id:
            created_quests += 1
            print(f"✅ Created quest {quest_id} from PU {pu.get('id')}")

    print("\n📈 Results:")
    print(f"   New quests created: {created_quests}")
    print(f"   Total quests now: {len(engine.quests)}")

    # Check for new Autonomous chapter
    if "Autonomous" in engine.questlines:
        auto_quests = [q for q in engine.quests.values() if q.questline == "Autonomous"]
        print(f"   Quests in 'Autonomous' chapter: {len(auto_quests)}")
        if auto_quests:
            print("   Recent autonomous quests:")
            for q in auto_quests[-2:]:
                print(f"     - {q.title}")

    return created_quests > 0


if __name__ == "__main__":
    success = test_pu_to_quest_conversion()
    sys.exit(0 if success else 1)
