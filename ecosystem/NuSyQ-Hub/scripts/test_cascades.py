#!/usr/bin/env python3
"""
Cascade Actions Test Script

Tests the new cascade system to ensure status changes trigger appropriate actions.

Usage:
    python scripts/test_cascades.py [test_name]

Tests:
    all          - Run all cascade tests
    startup      - Test startup cascades
    shutdown     - Test shutdown cascades
    error        - Test error cascades
    recovery     - Test recovery cascades
    heartbeat    - Test heartbeat cascades
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.system.status import get_system_status, heartbeat, set_system_status


def print_test_header(test_name: str):
    """Print test header."""
    print(f"\n{'=' * 60}")
    print(f"🧪 TEST: {test_name}")
    print(f"{'=' * 60}\n")


def print_test_result(passed: bool, message: str):
    """Print test result."""
    symbol = "✅" if passed else "❌"
    print(f"{symbol} {message}")


def check_event_log(stream: str, event_type: str) -> bool:
    """Check if event was logged to event bus."""
    log_file = Path("state/logs") / f"{stream}.log"
    if not log_file.exists():
        return False

    content = log_file.read_text()
    return event_type in content


def test_startup_cascade():
    """Test OFF → ON transition triggers startup cascades."""
    print_test_header("Startup Cascade")

    # Ensure we're starting from OFF
    set_system_status("off", run_id="test-001")
    time.sleep(0.1)

    # Trigger startup
    print("🔄 Triggering startup (OFF → ON)...")
    set_system_status("on", run_id="test-002", details={"test": "startup"}, message="Test startup")
    time.sleep(0.5)  # Give cascades time to run

    # Check results
    status = get_system_status()
    print_test_result(status["status"] == "on", f"Status is 'on': {status['status']}")

    event_logged = check_event_log("system_status", "startup_cascades_begin")
    print_test_result(event_logged, "Startup cascade event logged")

    print(f"\n📄 Current status:\n{status}\n")


def test_shutdown_cascade():
    """Test ON → OFF transition triggers shutdown cascades."""
    print_test_header("Shutdown Cascade")

    # Ensure we're ON first
    set_system_status("on", run_id="test-003")
    time.sleep(0.1)

    # Trigger shutdown
    print("🔄 Triggering shutdown (ON → OFF)...")
    set_system_status("off", run_id="test-003", details={"reason": "test"}, message="Test shutdown")
    time.sleep(0.5)

    # Check results
    status = get_system_status()
    print_test_result(status["status"] == "off", f"Status is 'off': {status['status']}")

    event_logged = check_event_log("system_status", "shutdown_cascades_begin")
    print_test_result(event_logged, "Shutdown cascade event logged")

    print(f"\n📄 Current status:\n{status}\n")


def test_error_cascade():
    """Test transition to ERROR triggers auto-healing."""
    print_test_header("Error Cascade (Auto-Healing)")

    # Ensure we're ON first
    set_system_status("on", run_id="test-004")
    time.sleep(0.1)

    # Trigger error
    print("🔄 Triggering error state (ON → ERROR)...")
    set_system_status(
        "error",
        health="critical",
        run_id="test-004",
        details={"message": "Test error for cascade", "error_code": "TEST-001"},
        message="Test error cascade",
    )
    time.sleep(1.0)  # Give auto-healing time to trigger

    # Check results
    status = get_system_status()
    print_test_result(status["status"] == "error", f"Status is 'error': {status['status']}")

    error_logged = check_event_log("errors", "system_error_state")
    print_test_result(error_logged, "Error event logged to errors stream")

    healing_logged = check_event_log("system_status", "auto_healing_triggered")
    print_test_result(healing_logged, "Auto-healing trigger logged")

    print(f"\n📄 Current status:\n{status}\n")


def test_recovery_cascade():
    """Test ERROR → ON transition triggers recovery cascades."""
    print_test_header("Recovery Cascade")

    # Ensure we're in ERROR state first
    set_system_status("error", health="critical", run_id="test-005", details={"message": "Pre-recovery error"})
    time.sleep(0.1)

    # Trigger recovery
    print("🔄 Triggering recovery (ERROR → ON)...")
    set_system_status(
        "on",
        health="healthy",
        run_id="test-005",
        details={"recovered_at": time.time()},
        message="Test recovery cascade",
    )
    time.sleep(0.5)

    # Check results
    status = get_system_status()
    print_test_result(status["status"] == "on", f"Status is 'on': {status['status']}")
    print_test_result(status["health"] == "healthy", f"Health is 'healthy': {status['health']}")

    recovery_logged = check_event_log("system_status", "recovery_complete")
    print_test_result(recovery_logged, "Recovery event logged")

    print(f"\n📄 Current status:\n{status}\n")


def test_heartbeat_cascade():
    """Test heartbeat triggers periodic health checks."""
    print_test_header("Heartbeat Cascade")

    # Set system ON
    set_system_status("on", run_id="test-006")
    time.sleep(0.1)

    # Send several heartbeats
    print("💓 Sending 12 heartbeats (health check on 10th)...")
    for i in range(1, 13):
        heartbeat(run_id="test-006", details={"beat": i})
        print(f"   Beat {i}/12", end="\r")
        time.sleep(0.1)

    print("\n")

    # Check results
    status = get_system_status()
    heartbeat_count = status.get("details", {}).get("heartbeat_count", 0)
    print_test_result(heartbeat_count >= 12, f"Heartbeat count: {heartbeat_count}")

    has_last_heartbeat = "last_heartbeat" in status.get("details", {})
    print_test_result(has_last_heartbeat, "Last heartbeat timestamp recorded")

    print(f"\n📄 Current status:\n{status}\n")


def test_stale_heartbeat():
    """Test stale heartbeat detection."""
    print_test_header("Stale Heartbeat Detection")

    # Set system ON and send first heartbeat
    set_system_status("on", run_id="test-007")
    heartbeat(run_id="test-007")
    time.sleep(0.1)

    print("💓 First heartbeat sent")
    print("⏰ Waiting 3 seconds (simulating stale heartbeat)...")
    time.sleep(3)

    # Send second heartbeat (should detect staleness)
    print("💓 Sending second heartbeat after delay...")
    heartbeat(run_id="test-007")
    time.sleep(0.5)

    # Check for stale heartbeat event
    stale_logged = check_event_log("anomalies", "heartbeat_stale")
    print_test_result(stale_logged, "Stale heartbeat detected and logged")

    print()


def run_all_tests():
    """Run all cascade tests."""
    print("\n" + "🧪" * 30)
    print("   CASCADE ACTIONS TEST SUITE")
    print("🧪" * 30)

    test_startup_cascade()
    test_shutdown_cascade()
    test_error_cascade()
    test_recovery_cascade()
    test_heartbeat_cascade()
    test_stale_heartbeat()

    print("\n" + "=" * 60)
    print("✅ ALL CASCADE TESTS COMPLETE")
    print("=" * 60)
    print("\n📁 Check logs in: state/logs/")
    print("   - system_status.log - Status change events")
    print("   - errors.log - Error events")
    print("   - anomalies.log - Anomaly events")
    print()


def main():
    """Main test runner."""
    test_name = sys.argv[1] if len(sys.argv) > 1 else "all"

    tests = {
        "all": run_all_tests,
        "startup": test_startup_cascade,
        "shutdown": test_shutdown_cascade,
        "error": test_error_cascade,
        "recovery": test_recovery_cascade,
        "heartbeat": test_heartbeat_cascade,
        "stale": test_stale_heartbeat,
    }

    if test_name not in tests:
        print(f"❌ Unknown test: {test_name}")
        print(f"Available tests: {', '.join(tests.keys())}")
        sys.exit(1)

    tests[test_name]()


if __name__ == "__main__":
    main()
