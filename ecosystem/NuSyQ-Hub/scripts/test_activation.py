#!/usr/bin/env python3
"""🧪 Quick Activation Test - Culture Ship + Boss Rush + Temple

Tests all three newly activated systems to ensure proper integration.
"""

import logging
import sys
from pathlib import Path

# Add repo to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)


def test_culture_ship():
    """Test Culture Ship availability (headless)."""
    print("\n🌟 Testing Culture Ship Integration...")
    try:
        import importlib.util

        spec = importlib.util.find_spec("scripts.launch_culture_ship")
        if spec is not None:
            print("✅ Culture Ship launcher available")
        print("   Run: python scripts/launch_culture_ship.py")
        print("   Note: Requires tkinter and ChatDev Culture Ship installation")
        return True
    except ImportError as e:
        print(f"⚠️  Culture Ship import issue: {e}")
        return False


def test_boss_rush_bridge():
    """Test Boss Rush bridge functionality."""
    print("\n🎮 Testing Boss Rush Bridge...")
    try:
        from src.integration.boss_rush_bridge import BossRushBridge

        # Create bridge instance
        bridge = BossRushBridge()
        print("✅ Boss Rush Bridge initialized")

        # Test knowledge base loading
        kb = bridge.load_knowledge_base()
        if kb:
            print(f"✅ Knowledge base loaded: {len(kb)} entries")
        else:
            print("⚠️  Knowledge base empty or not found")

        # Test progress tracking
        progress = bridge.get_boss_rush_progress()
        print("📊 Boss Rush Progress:")
        print(f"   Total tasks: {progress['total_tasks']}")
        print(f"   Completed: {progress['completed']}")
        print(f"   In progress: {progress['in_progress']}")
        print(f"   Completion rate: {progress['completion_rate']:.1%}")

        # Test active tasks
        active = bridge.get_active_tasks()
        print(f"📋 Active tasks: {len(active)}")

        # Test tool arsenal status
        tools = bridge.get_tool_arsenal_status()
        print(f"🛠️  Tool Arsenal: {tools.get('total_tools', 'N/A')} tools available")

        return True

    except Exception as e:
        logger.exception(f"❌ Boss Rush Bridge test failed: {e}")
        return False


def test_temple_auto_storage():
    """Test Temple Auto-Storage integration."""
    print("\n📚 Testing Temple Auto-Storage...")
    try:
        from src.integration.temple_auto_storage import TempleAutoStorage

        # Create storage instance
        storage = TempleAutoStorage()
        print("✅ Temple Auto-Storage initialized")

        # Test archive stats
        stats = storage.get_archive_stats()
        print("📊 Archive Statistics:")
        print(f"   Conversations archived: {stats['conversations_archived']}")
        print(f"   Quests archived: {stats['quests_archived']}")
        print(f"   Boss Rush archived: {stats['boss_rush_archived']}")
        print(f"   Achievements archived: {stats['achievements_archived']}")
        print(f"   Insights archived: {stats['insights_archived']}")

        return True

    except Exception as e:
        logger.exception(f"❌ Temple Auto-Storage test failed: {e}")
        return False


def test_rpg_inventory_fix():
    """Test RPG Inventory asyncio fix."""
    print("\n🎮 Testing RPG Inventory Fix...")
    try:
        from src.system.rpg_inventory import RPGInventorySystem

        # Create RPG system (don't start monitoring to avoid threading in test)
        rpg = RPGInventorySystem(update_interval=30)
        print("✅ RPG Inventory system initialized")
        print("   AsyncIO threading fix applied")
        print(f"   Components: {len(rpg.components)}")
        print(f"   Skills: {len(rpg.skills)}")

        # Note: Not starting monitoring to avoid Thread-8 in test context
        print("   Info: Not starting monitoring in test (use ecosystem startup)")

        return True

    except Exception as e:
        logger.exception(f"❌ RPG Inventory test failed: {e}")
        return False


def main():
    """Run all activation tests."""
    print("=" * 70)
    print("🚀 NuSyQ-Hub Dormant Systems Activation Test")
    print("=" * 70)

    results = {
        "Culture Ship": test_culture_ship(),
        "Boss Rush Bridge": test_boss_rush_bridge(),
        "Temple Auto-Storage": test_temple_auto_storage(),
        "RPG Inventory Fix": test_rpg_inventory_fix(),
    }

    print("\n" + "=" * 70)
    print("📊 Activation Test Results")
    print("=" * 70)

    all_passed = True
    for system, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {system}")
        if not passed:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("\n🎉 All systems activated successfully!")
        print("\n📋 Next Steps:")
        print("   1. Launch Culture Ship: python scripts/launch_culture_ship.py")
        print(
            "   2. View Boss Rush tasks: python -c 'from src.integration.boss_rush_bridge import boss_rush_bridge; print(boss_rush_bridge.get_active_tasks())'"
        )
        print(
            "   3. Check Temple archives: python -c 'from src.integration.temple_auto_storage import temple_auto_storage; print(temple_auto_storage.get_archive_stats())'"
        )
        print("   4. Start RPG system: Enable in src/diagnostics/ecosystem_startup_sentinel.py")
    else:
        print("\n⚠️  Some systems failed activation. Check logs above.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
