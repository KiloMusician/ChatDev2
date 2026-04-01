#!/usr/bin/env python3
"""Verify Services - Test that all critical services are working correctly"""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.terminal_output import (
    to_claude,
    to_metrics,
    to_tasks,
    to_zeta,
)


def test_terminal_routing():
    """Test that terminal routing works."""
    print("\n🧪 Testing Terminal Routing...")

    try:
        to_tasks("✅ Test message to Tasks terminal")
        to_zeta("✅ Test message to Zeta terminal")
        to_metrics("✅ Test message to Metrics terminal")
        to_claude("✅ Test message to Claude terminal")

        # Check that messages were written
        time.sleep(0.5)

        checks = [
            ("tasks", ROOT / "data" / "terminal_logs" / "tasks.log"),
            ("zeta", ROOT / "data" / "terminal_logs" / "zeta.log"),
            ("metrics", ROOT / "data" / "terminal_logs" / "metrics.log"),
            ("claude", ROOT / "data" / "terminal_logs" / "claude.log"),
        ]

        passed = 0
        for name, log_file in checks:
            if log_file.exists():
                content = log_file.read_text()
                if "Test message" in content:
                    print(f"   ✅ {name.title()} terminal: OK")
                    passed += 1
                else:
                    print(f"   ❌ {name.title()} terminal: No test message found")
            else:
                print(f"   ❌ {name.title()} terminal: Log file not found")

        return passed == len(checks)
    except Exception as e:
        print(f"   ❌ Terminal routing failed: {e}")
        return False


def test_pu_queue():
    """Test that PU queue is functional."""
    print("\n🧪 Testing PU Queue...")

    try:
        from src.automation.unified_pu_queue import UnifiedPUQueue

        queue = UnifiedPUQueue()
        # Get statistics
        stats = queue.get_statistics()

        print(f"   📊 Total PUs: {stats.get('total', 0)}")
        print(f"      - queued: {stats.get('queued', 0)}")
        print(f"      - approved: {stats.get('approved', 0)}")
        print(f"      - executing: {stats.get('executing', 0)}")
        print(f"      - completed: {stats.get('completed', 0)}")
        print(f"      - failed: {stats.get('failed', 0)}")

        print("   ✅ PU Queue: OK")
        return True
    except Exception as e:
        print(f"   ❌ PU Queue failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_cross_sync():
    """Test that cross ecosystem sync is functional."""
    print("\n🧪 Testing Cross Ecosystem Sync...")

    try:
        from src.tools.cross_ecosystem_sync import CrossEcosystemSync

        CrossEcosystemSync()
        print("   ✅ Cross Ecosystem Sync: OK")
        return True
    except Exception as e:
        print(f"   ❌ Cross Ecosystem Sync failed: {e}")
        return False


def test_service_status():
    """Test that services are running."""
    print("\n🧪 Testing Service Status...")

    state_file = ROOT / "state" / "services" / "services.json"
    if not state_file.exists():
        print("   ❌ No services running")
        return False

    try:
        state = json.loads(state_file.read_text())
        services = state.get("services", {})

        if not services:
            print("   ❌ No services configured")
            return False

        all_running = True
        for name, info in services.items():
            status = info.get("status", "unknown")
            if status == "running":
                print(f"   ✅ {name.replace('_', ' ').title()}: Running")
            else:
                print(f"   ❌ {name.replace('_', ' ').title()}: {status}")
                all_running = False

        return all_running
    except Exception as e:
        print(f"   ❌ Service status check failed: {e}")
        return False


def test_log_files():
    """Test that log files are being written."""
    print("\n🧪 Testing Log Files...")

    log_dir = ROOT / "data" / "service_logs"
    if not log_dir.exists():
        print("   ❌ Service logs directory not found")
        return False

    expected_logs = ["pu_queue.log", "cross_sync.log", "guild_renderer.log"]
    found = 0

    for log_name in expected_logs:
        log_file = log_dir / log_name
        if log_file.exists() and log_file.stat().st_size > 0:
            print(f"   ✅ {log_name}: Present ({log_file.stat().st_size} bytes)")
            found += 1
        else:
            print(f"   ❌ {log_name}: Missing or empty")

    return found == len(expected_logs)


def main():
    """Run all tests."""
    print("=" * 70)
    print("🔍 NUSYQ-HUB SERVICE VERIFICATION")
    print("=" * 70)

    tests = [
        ("Terminal Routing", test_terminal_routing),
        ("PU Queue", test_pu_queue),
        ("Cross Ecosystem Sync", test_cross_sync),
        ("Service Status", test_service_status),
        ("Log Files", test_log_files),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ {name} crashed: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print("📊 TEST RESULTS")
    print("=" * 70)
    print(f"\n✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed == 0:
        print("\n🎉 All tests passed! Services are working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
