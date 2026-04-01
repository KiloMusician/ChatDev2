#!/usr/bin/env python3
"""Direct integration test: Convert PUs to quests."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from Rosetta_Quest_System.quest_engine import QuestEngine


def convert_pu_batch_to_quests(batch_size: int = 10) -> dict:
    """Convert a batch of PUs to quests directly."""
    engine = QuestEngine()
    queue_file = Path(__file__).parent.parent / "data" / "unified_pu_queue.json"

    result = {
        "quests_created": 0,
        "quests_failed": 0,
        "pus_processed": [],
    }

    # Load PU queue
    with open(queue_file) as f:
        pu_queue = json.load(f)

    # Filter eligible PUs
    eligible = [p for p in pu_queue if p.get("status") == "completed" and not p.get("associated_quest_id")]

    # Map PU types to questlines
    pu_type_map = {
        "BugFixPU": "Bug Fixes",
        "RefactorPU": "Refactoring",
        "FeaturePU": "Features",
        "DocPU": "Documentation",
        "AnalysisPU": "Analysis & Audits",
        "TestPU": "Testing",
    }

    print(f"🔄 Converting '{batch_size}' of {len(eligible)} eligible PUs to quests...\n")

    # Process batch
    for pu in eligible[:batch_size]:
        try:
            pu_type = pu.get("type", "AnalysisPU")
            questline = pu_type_map.get(pu_type, "Autonomous")

            quest_id = engine.add_quest(
                title=pu.get("title", f"Task: {pu.get('id')}"),
                description=f"""Auto-converted from PU: {pu.get("id")}

Type: {pu_type}
Priority: {pu.get("priority", "medium")}
Source: {pu.get("source_repo", "unknown")}
""",
                questline=questline,
                tags=[pu_type, "autonomous", f"source:{pu.get('source_repo')}"],
                priority=pu.get("priority", "medium"),
            )

            if quest_id:
                # Update PU with quest reference
                pu["associated_quest_id"] = quest_id
                result["quests_created"] += 1
                result["pus_processed"].append(
                    {
                        "pu_id": pu.get("id"),
                        "quest_id": quest_id,
                        "type": pu_type,
                        "title": pu.get("title")[:50],
                    }
                )
        except Exception as e:
            result["quests_failed"] += 1
            print(f"❌ Error processing PU {pu.get('id')}: {e}")

    # Save updated queue
    with open(queue_file, "w") as f:
        json.dump(pu_queue, f, indent=2)

    return result


def main():
    """Run the integration test."""
    print("=" * 70)
    print("🚀 PU → Quest Engine Integration Test")
    print("=" * 70)
    print()

    # Run conversion
    result = convert_pu_batch_to_quests(batch_size=10)

    print("\n✅ Conversion Complete:")
    print(f"   Quests created: {result['quests_created']}")
    print(f"   Quests failed: {result['quests_failed']}")
    print()

    if result["pus_processed"]:
        print("📋 Sample Conversions:")
        for item in result["pus_processed"][:5]:
            print(f"   • {item['type']:10} → Quest {item['quest_id'][:8]}")
            print(f"     {item['title']}")

    # Verify in quest engine
    engine = QuestEngine()
    print("\n📊 Quest Engine State:")
    print(f"   Total quests: {len(engine.quests)}")
    print(f"   Total questlines: {len(engine.questlines)}")

    # Check for autonomous quests
    auto_quests = [q for q in engine.quests.values() if "autonomous" in q.tags]
    print(f"   Autonomous-tagged quests: {len(auto_quests)}")

    return 0 if result["quests_created"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
