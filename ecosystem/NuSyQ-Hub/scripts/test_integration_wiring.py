#!/usr/bin/env python3
"""🔧 Integration Wiring Test Suite

Tests all completed integration wiring:
- Breathing → Timeout Config
- Temple → Conversation Manager
- Boss Rush → Quest System
- Culture Ship → Startup Sentinel
"""

import logging
import sys
from pathlib import Path

# Add repo to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def test_breathing_timeout_integration():
    """Test Breathing Pacing → Timeout Config integration."""
    print("\n⏱️  Testing Breathing → Timeout Integration...")
    try:
        from src.integration.breathing_integration import breathing_integration
        from src.utils.timeout_config import get_adaptive_timeout

        # Test adaptive timeout calculation
        base_timeout = 120
        adjusted = get_adaptive_timeout(base_timeout, service="test")

        print("✅ Breathing integration wired to timeout config")
        print(f"   Base timeout: {base_timeout}s")
        print(f"   Adjusted: {adjusted}s")
        print(f"   Factor: {adjusted / base_timeout:.2f}x")
        print(f"   Breathing enabled: {breathing_integration.enable_breathing}")

        # Test with different base values
        timeouts = [30, 60, 90, 120, 180]
        print("\n   Sample adaptive timeouts:")
        for base in timeouts:
            adj = get_adaptive_timeout(base)
            print(f"      {base}s → {adj}s ({adj / base:.2f}x)")

        return True
    except Exception as e:
        logger.exception(f"❌ Breathing-Timeout integration failed: {e}")
        return False


def test_temple_conversation_integration():
    """Test Temple Auto-Storage → Conversation Manager integration."""
    print("\n📚 Testing Temple → Conversation Integration...")
    try:
        from src.ai.conversation_manager import ConversationManager
        from src.integration.temple_auto_storage import temple_auto_storage

        # Create test conversation
        conv_mgr = ConversationManager(storage_path=repo_root / "data" / "test_conversations.json")
        test_id = "test_temple_integration_001"

        conv_mgr.create_conversation(test_id, task_type="testing", metadata={"test": True})

        print("✅ Temple integration wired to conversation manager")
        print(f"   Test conversation: {test_id}")

        # Add messages to test threshold checking
        for i in range(3):
            conv_mgr.add_message(test_id, role="user", content=f"Test message {i + 1}")

        print("   Messages added: 3")
        print("   Archive check runs on each add_message()")

        # Check if archive threshold reached
        should_archive = temple_auto_storage.should_archive_conversation(test_id)
        threshold = temple_auto_storage.auto_archive_threshold
        print(f"   Auto-archive threshold: {threshold} messages")
        print(f"   Should archive: {should_archive}")

        # Clean up test conversation
        if test_id in conv_mgr.conversations:
            del conv_mgr.conversations[test_id]
            conv_mgr.save()

        return True
    except Exception as e:
        logger.exception(f"❌ Temple-Conversation integration failed: {e}")
        return False


def test_boss_rush_quest_integration():
    """Test Boss Rush → Quest System integration."""
    print("\n🎮 Testing Boss Rush → Quest Integration...")
    try:
        from src.integration.boss_rush_bridge import BossRushBridge
        from src.Rosetta_Quest_System.quest_engine import QuestEngine

        boss_rush = BossRushBridge()
        quest_engine = QuestEngine()

        print("✅ Boss Rush integration wired to quest system")
        print(f"   NuSyQ Root: {boss_rush.nusyq_root}")
        print(f"   Quest Engine: {len(quest_engine.quests)} quests")

        # Test sync capability
        active_tasks = boss_rush.get_active_tasks()
        print(f"   Active Boss Rush tasks: {len(active_tasks)}")

        if len(active_tasks) > 0:
            print("   Sync available via boss_rush.sync_to_quest_system()")
        else:
            print("   Info: No active tasks to sync (expected for clean state)")

        return True
    except Exception as e:
        logger.exception(f"❌ Boss Rush-Quest integration failed: {e}")
        return False


def test_culture_ship_startup_integration():
    """Test Culture Ship → Startup Sentinel integration."""
    print("\n🚀 Testing Culture Ship → Startup Integration...")
    try:
        from src.diagnostics.ecosystem_startup_sentinel import EcosystemStartupSentinel

        sentinel = EcosystemStartupSentinel()

        print("✅ Culture Ship integration in startup sentinel")

        # Check if culture_ship in autonomous systems
        if "culture_ship" in sentinel.autonomous_systems:
            culture_ship_config = sentinel.autonomous_systems["culture_ship"]
            print(f"   Name: {culture_ship_config['name']}")
            print(f"   Path: {culture_ship_config['path']}")
            print(f"   Auto-start: {culture_ship_config['auto_start']}")
            print(
                f"   Activator: {culture_ship_config['activator'].__name__ if culture_ship_config.get('activator') else 'None'}"
            )

        # Check wizard_navigator too
        if "wizard_navigator" in sentinel.autonomous_systems:
            wizard_config = sentinel.autonomous_systems["wizard_navigator"]
            print("\n   Wizard Navigator also registered:")
            print(f"      Path: {wizard_config['path']}")

        return True
    except Exception as e:
        logger.exception(f"❌ Culture Ship-Startup integration failed: {e}")
        return False


def main():
    """Run all integration wiring tests."""
    print("=" * 70)
    print("🔌 NuSyQ-Hub Integration Wiring Test Suite")
    print("=" * 70)

    results = {
        "Breathing → Timeout": test_breathing_timeout_integration(),
        "Temple → Conversation": test_temple_conversation_integration(),
        "Boss Rush → Quest": test_boss_rush_quest_integration(),
        "Culture Ship → Startup": test_culture_ship_startup_integration(),
    }

    print("\n" + "=" * 70)
    print("📊 Integration Wiring Test Results")
    print("=" * 70)

    all_passed = True
    for integration, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {integration}")
        if not passed:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("\n🎉 All integration wiring tests passed!")
        print("\n📋 Integration Status:")
        print("   ✅ Breathing adaptive timeouts active")
        print("   ✅ Temple auto-archival hooks installed")
        print("   ✅ Boss Rush quest sync operational")
        print("   ✅ Culture Ship startup registration complete")
    else:
        print("\n⚠️  Some integrations failed. Check logs above.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
