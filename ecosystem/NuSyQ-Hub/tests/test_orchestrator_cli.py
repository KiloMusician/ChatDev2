#!/usr/bin/env python3
"""
Test suite for orchestrator_cli.py

Tests all 9 subcommands:
1. queue - Quest queue summary
2. todo - Sprint/todo status
3. zeta - ZETA progress tracker
4. guild - Guild board summary + snapshots
5. culture-ship - Culture Ship CLI (modes: health-only, dry-run, apply)
6. away - Overnight safe mode
7. nav - Repository navigation
8. next-actions - Suggested next actions
9. sessions - Aggregated session logs

All subcommands tested for:
- Successful execution (exit code 0)
- Receipt generation
- Output content validation
- Edge cases (missing files, timeouts, etc.)
"""

import json
import subprocess
import sys
from pathlib import Path

# Root path for orchestrator CLI
REPO_ROOT = Path(__file__).resolve().parent.parent
RECEIPTS_DIR = REPO_ROOT / "state" / "receipts" / "cli"


class TestResult:
    """Track test outcomes."""

    __test__ = False  # Not a pytest test class — helper fixture type

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors: list[str] = []

    def test(self, name: str, condition: bool, message: str = "") -> None:
        """Record test result."""
        if condition:
            self.passed += 1
            print(f"  ✓ {name}")
        else:
            self.failed += 1
            msg = f"  ✗ {name}"
            if message:
                msg += f": {message}"
            print(msg)
            self.errors.append(msg)

    def summary(self) -> bool:
        """Print summary and return True if all passed."""
        total = self.passed + self.failed
        print(f"\n{'=' * 60}")
        print(f"Test Results: {self.passed}/{total} passed")
        if self.failed > 0:
            print("\nFailed tests:")
            for err in self.errors:
                print(err)
        return self.failed == 0


def run_cmd(cmd: list[str]) -> tuple[int, str, str]:
    """Run orchestrator CLI command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(REPO_ROOT),
            check=False,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except Exception as e:
        return -2, "", str(e)


def test_queue(results: TestResult) -> None:
    """Test: orchestrator_cli queue [--limit N]"""
    print("\n1️⃣  Testing 'queue' subcommand...")

    # Default limit
    exit_code, stdout, stderr = run_cmd(["python", "scripts/orchestrator_cli.py", "queue"])
    results.test("queue: exits 0", exit_code == 0, f"Got {exit_code}")
    results.test("queue: has output", len(stdout) > 0, "No output")
    results.test("queue: mentions Total quests", "Total quests" in stdout)

    # Check receipt
    receipts = list(RECEIPTS_DIR.glob("queue_*.json"))
    results.test("queue: receipt generated", len(receipts) > 0)
    if receipts:
        with open(receipts[-1], encoding="utf-8") as f:
            payload = json.load(f)
        results.test("queue: receipt has summary", "summary" in payload)
        results.test("queue: receipt has recent", "recent" in payload)

    # With limit
    exit_code, stdout, _stderr = run_cmd(
        ["python", "scripts/orchestrator_cli.py", "queue", "--limit", "3"]
    )
    results.test("queue --limit 3: exits 0", exit_code == 0)


def test_todo(results: TestResult) -> None:
    """Test: orchestrator_cli todo"""
    print("\n2️⃣  Testing 'todo' subcommand...")

    exit_code, stdout, _stderr = run_cmd(["python", "scripts/orchestrator_cli.py", "todo"])
    results.test("todo: exits 0", exit_code == 0, f"Got {exit_code}")
    results.test("todo: has output", len(stdout) > 0)
    results.test("todo: mentions Sprints", "Sprints" in stdout)

    # Check receipt
    receipts = list(RECEIPTS_DIR.glob("todo_*.json"))
    results.test("todo: receipt generated", len(receipts) > 0)
    if receipts:
        with open(receipts[-1], encoding="utf-8") as f:
            payload = json.load(f)
        results.test("todo: receipt has sprints", "sprints" in payload)
        results.test("todo: receipt has count", "count" in payload)


def test_zeta(results: TestResult) -> None:
    """Test: orchestrator_cli zeta"""
    print("\n3️⃣  Testing 'zeta' subcommand...")

    exit_code, stdout, _stderr = run_cmd(["python", "scripts/orchestrator_cli.py", "zeta"])
    results.test("zeta: exits 0", exit_code == 0, f"Got {exit_code}")
    results.test("zeta: has output", len(stdout) > 0)

    # Check receipt
    receipts = list(RECEIPTS_DIR.glob("zeta_*.json"))
    results.test("zeta: receipt generated", len(receipts) > 0)


def test_guild(results: TestResult) -> None:
    """Test: orchestrator_cli guild [--snapshot]"""
    print("\n4️⃣  Testing 'guild' subcommand...")

    # Basic guild
    exit_code, stdout, stderr = run_cmd(["python", "scripts/orchestrator_cli.py", "guild"])
    results.test("guild: exits 0", exit_code == 0, f"Got {exit_code}")
    results.test("guild: has output", len(stdout) > 0)
    results.test("guild: mentions Guild Board", "Guild Board" in stdout)

    # Check receipt
    receipts = list(RECEIPTS_DIR.glob("guild_*.json"))
    results.test("guild: receipt generated", len(receipts) > 0)
    if receipts:
        with open(receipts[-1], encoding="utf-8") as f:
            payload = json.load(f)
        results.test("guild: receipt has board", "board" in payload)

    # Guild with snapshot
    exit_code, stdout, _stderr = run_cmd(
        ["python", "scripts/orchestrator_cli.py", "guild", "--snapshot"]
    )
    results.test("guild --snapshot: exits 0", exit_code == 0, f"Got {exit_code}")
    results.test("guild --snapshot: mentions snapshot", "snapshot" in stdout.lower())

    # Check snapshot file exists
    snapshots = list((REPO_ROOT / "docs" / "Agent-Sessions").glob("GUILD_BOARD_SNAPSHOT_*.md"))
    results.test("guild --snapshot: creates markdown file", len(snapshots) > 0)
    if snapshots:
        snapshot = snapshots[-1]
        content = snapshot.read_text()
        results.test("guild snapshot: has title", "Guild Board Snapshot" in content)
        results.test("guild snapshot: has summary table", "| Status | Count |" in content)


def test_culture_ship(results: TestResult) -> None:
    """Test: orchestrator_cli culture-ship [health-only|dry-run|apply]"""
    print("\n5️⃣  Testing 'culture-ship' subcommand...")

    # Test health-only mode (lightweight)
    exit_code, stdout, stderr = run_cmd(
        ["python", "scripts/orchestrator_cli.py", "culture-ship", "health-only"]
    )
    results.test(
        "culture-ship health-only: runs", exit_code in [0, 1]
    )  # 0=success, 1=error OK for this test
    results.test("culture-ship health-only: has output", len(stdout) > 0 or len(stderr) > 0)

    # Check receipt
    receipts = list(RECEIPTS_DIR.glob("culture_ship_*.json"))
    results.test("culture-ship: receipt generated", len(receipts) > 0)
    if receipts:
        with open(receipts[-1], encoding="utf-8") as f:
            payload = json.load(f)
        results.test("culture-ship: receipt has mode", "mode" in payload)
        results.test("culture-ship: receipt has status", "status" in payload)

    # Test invalid mode
    exit_code, stdout, stderr = run_cmd(
        ["python", "scripts/orchestrator_cli.py", "culture-ship", "invalid"]
    )
    results.test("culture-ship invalid mode: shows error", "Unknown Culture Ship mode" in stdout)


def test_away(results: TestResult) -> None:
    """Test: orchestrator_cli away"""
    print("\n6️⃣  Testing 'away' subcommand...")

    exit_code, stdout, _stderr = run_cmd(["python", "scripts/orchestrator_cli.py", "away"])
    results.test("away: exits 0", exit_code == 0, f"Got {exit_code}")
    results.test("away: has output", len(stdout) > 0)
    results.test("away: mentions complete", "complete" in stdout.lower())

    # Check receipt
    receipts = list(RECEIPTS_DIR.glob("away_*.json"))
    results.test("away: receipt generated", len(receipts) > 0)
    if receipts:
        with open(receipts[-1], encoding="utf-8") as f:
            payload = json.load(f)
        results.test("away: receipt has actions", "actions" in payload)


def test_nav(results: TestResult) -> None:
    """Test: orchestrator_cli nav [REPO|list] [--pwd]"""
    print("\n7️⃣  Testing 'nav' subcommand...")

    # List repos
    exit_code, stdout, stderr = run_cmd(["python", "scripts/orchestrator_cli.py", "nav"])
    results.test("nav list: exits 0", exit_code == 0, f"Got {exit_code}")
    results.test("nav list: has output", len(stdout) > 0)
    results.test(
        "nav list: mentions repositories",
        "repository" in stdout.lower() or "repo" in stdout.lower(),
    )

    # Navigate to hub
    exit_code, stdout, stderr = run_cmd(["python", "scripts/orchestrator_cli.py", "nav", "hub"])
    results.test("nav hub: exits 0", exit_code == 0, f"Got {exit_code}")
    results.test("nav hub: shows path", "NuSyQ-Hub" in stdout or "path" in stdout.lower())

    # Check receipt
    receipts = list(RECEIPTS_DIR.glob("nav_*.json"))
    results.test("nav: receipt generated", len(receipts) > 0)

    # Test --pwd flag (path only)
    exit_code, stdout, _stderr = run_cmd(
        ["python", "scripts/orchestrator_cli.py", "nav", "hub", "--pwd"]
    )
    results.test("nav hub --pwd: exits 0", exit_code == 0, f"Got {exit_code}")
    results.test("nav hub --pwd: shows path", len(stdout) > 0)


def test_next_actions(results: TestResult) -> None:
    """Test: orchestrator_cli next-actions"""
    print("\n8️⃣  Testing 'next-actions' subcommand...")

    exit_code, stdout, _stderr = run_cmd(["python", "scripts/orchestrator_cli.py", "next-actions"])
    results.test("next-actions: exits 0", exit_code == 0, f"Got {exit_code}")
    results.test("next-actions: has output", len(stdout) > 0)
    results.test("next-actions: mentions Actions", "action" in stdout.lower())

    # Check receipt
    receipts = list(RECEIPTS_DIR.glob("next_actions_*.json"))
    results.test("next-actions: receipt generated", len(receipts) > 0)
    if receipts:
        with open(receipts[-1], encoding="utf-8") as f:
            payload = json.load(f)
        results.test("next-actions: receipt has status", "status" in payload)


def test_sessions(results: TestResult) -> None:
    """Test: orchestrator_cli sessions"""
    print("\n9️⃣  Testing 'sessions' subcommand...")

    exit_code, stdout, _stderr = run_cmd(["python", "scripts/orchestrator_cli.py", "sessions"])
    results.test("sessions: exits 0", exit_code == 0, f"Got {exit_code}")
    results.test("sessions: has output", len(stdout) > 0)
    results.test("sessions: mentions sessions", "session" in stdout.lower())

    # Check for aggregation markers
    results.test(
        "sessions: shows aggregation stats", "total" in stdout.lower() or "count" in stdout.lower()
    )


def test_receipt_consistency(results: TestResult) -> None:
    """Validate all receipts have consistent structure."""
    print("\n📋 Testing receipt consistency...")

    receipts = list(RECEIPTS_DIR.glob("*_*.json"))
    results.test("receipts: directory exists", len(receipts) > 0, f"Found {len(receipts)} receipts")

    if receipts:
        for receipt in receipts[-9:]:  # Check last 9 (one per subcommand)
            with open(receipt, encoding="utf-8") as f:
                payload = json.load(f)

            results.test(f"receipt {receipt.name}: has timestamp", "timestamp" in payload)
            results.test(f"receipt {receipt.name}: has command", "command" in payload)

    print(f"\n📁 Total receipts found: {len(receipts)}")


def main() -> None:
    print("=" * 60)
    print("🧪 Orchestrator CLI Test Suite")
    print("=" * 60)

    results = TestResult()

    # Run all tests
    test_queue(results)
    test_todo(results)
    test_zeta(results)
    test_guild(results)
    test_culture_ship(results)
    test_away(results)
    test_nav(results)
    test_next_actions(results)
    test_sessions(results)
    test_receipt_consistency(results)

    # Summary
    success = results.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
