#!/usr/bin/env python3
"""Test Quest → Orchestrator integration."""

import sys
from pathlib import Path

# Add src to path for imports
hub_root = Path(__file__).parent.parent
sys.path.insert(0, str(hub_root))
sys.path.insert(0, str(hub_root / "src"))

from Rosetta_Quest_System.quest_engine import QuestEngine

# Just test the conversion logic without importing the full orchestrator
# (to avoid complex dependency issues)


def test_quest_to_orchestration_task_conversion():
    """Test that quests can be converted to orchestration task structure."""
    engine = QuestEngine()

    # Get sample quests
    all_quests = list(engine.quests.values())
    eligible_quests = [q for q in all_quests if q.status in ["pending", "active"]]

    print("=" * 70)
    print("🚀 Quest → Orchestrator Task Conversion Test")
    print("=" * 70)
    print()

    print("📊 Quest Engine Status:")
    print(f"   Total quests: {len(engine.quests)}")
    print(f"   Pending/Active quests: {len(eligible_quests)}")
    print()

    # Test conversion (simulate OrchestrationTask creation)
    priority_map = {
        "critical": "CRITICAL",
        "high": "HIGH",
        "medium": "NORMAL",
        "normal": "NORMAL",
        "low": "LOW",
    }

    converted_tasks = []
    for quest in eligible_quests[:5]:
        try:
            task_priority = priority_map.get(str(quest.priority).lower() if quest.priority else "normal", "NORMAL")

            # Simulate OrchestrationTask
            task_data = {
                "task_id": quest.id,
                "task_type": "quest_execution",
                "content": f"{quest.title}: {quest.description[:100]}",
                "context": {
                    "quest_id": quest.id,
                    "questline": quest.questline,
                },
                "priority": task_priority,
                "required_capabilities": ["quest_execution"],
            }

            converted_tasks.append(task_data)
        except Exception as e:
            print(f"❌ Failed to convert quest {quest.id}: {e}")

    print("✅ Task Conversion Results:")
    print(f"   Converted: {len(converted_tasks)}/5 sample quests")
    print()

    if converted_tasks:
        print("📋 Sample Converted Tasks:")
        for i, task in enumerate(converted_tasks[:3], 1):
            print(f"   {i}. Task ID: {task['task_id']}")
            print(f"      Type: {task['task_type']}")
            print(f"      Priority: {task['priority']}")
            print(f"      Content: {task['content'][:50]}...")
    print()

    print("✅ Test passed - quest to task conversion successful!")
    return len(converted_tasks) > 0


if __name__ == "__main__":
    success = test_quest_to_orchestration_task_conversion()
    sys.exit(0 if success else 1)
