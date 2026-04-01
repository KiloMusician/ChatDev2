#!/usr/bin/env python3
"""NuSyQ Healing Orchestrator - Master automation command
Provides single-command access to all healing operations.

Usage:
    python scripts/healing_orchestrator.py [command] [options]

Commands:
    status           - Show current system health (dashboard)
    diagnose         - Run full diagnostic scan
    heal             - Execute auto-healing cycle
    validate         - Run test validation
    process-quests   - Process next quest items
    complete         - Full healing completion check
    automate         - Set up automated scheduling
    help             - Show available commands
"""

import json
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: list[str], label: str = "", timeout: int = 120) -> tuple[int, str]:
    """Run command with nice output."""
    try:
        if label:
            print(f"  ⚙️  {label}...")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=Path(__file__).parent.parent)

        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return 124, f"Command timed out after {timeout}s"
    except Exception as e:
        return 1, str(e)


def cmd_status():
    """Show current system health."""
    print("\n📊 SYSTEM HEALTH STATUS\n")
    ret, out = run_cmd(["python", "scripts/healing_dashboard.py"], "Loading dashboard")
    print(out)
    return ret


def cmd_diagnose():
    """Run diagnostic scan."""
    print("\n🔍 RUNNING DIAGNOSTIC SCAN\n")
    ret, out = run_cmd(["python", "scripts/system_pain_points_finder.py"], "Scanning system")
    print(out)
    return ret


def cmd_heal():
    """Execute healing operations."""
    print("\n🏥 EXECUTING HEALING CYCLE\n")
    ret, out = run_cmd(["python", "scripts/integration_health_check.py", "--mode", "full"], "Running health check")
    print(out)
    return ret


def cmd_validate():
    """Run tests and validation."""
    print("\n✅ VALIDATING SYSTEM\n")

    # Run minimal tests
    ret, out = run_cmd(["python", "-m", "pytest", "tests/test_minimal.py", "-q"], "Running validation tests")

    if ret == 0:
        print("✅ Minimal tests PASSED\n")
    else:
        print("⚠️  Some tests failed:\n")
        print(out)

    return ret


def cmd_process_quests():
    """Show and process quest items."""
    print("\n📋 QUEST MANAGEMENT\n")

    quest_file = Path("src/Rosetta_Quest_System/quest_log.jsonl")
    if not quest_file.exists():
        print("❌ No quest log found")
        return 1

    quests = []
    try:
        with open(quest_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    quests.append(json.loads(line))
    except Exception as e:
        print(f"❌ Error reading quests: {e}")
        return 1

    if not quests:
        print("Info: No quests yet. Create some with: python scripts/todos_to_quests.py")
        return 0

    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    quests.sort(key=lambda q: priority_order.get(q.get("priority", "medium"), 99))

    print(f"📊 Total Quests: {len(quests)}\n")
    print("Top 10 Quests by Priority:")
    print("─" * 80)

    for i, quest in enumerate(quests[:10], 1):
        priority = quest.get("priority", "unknown").upper()
        effort = quest.get("estimated_effort", "unknown")
        title = quest.get("title", "unknown")

        icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(priority, "⚪")

        print(f"{i:2}. {icon} [{priority:8}] {effort:15} | {title[:50]}")

    print("─" * 80)

    return 0


def cmd_complete():
    """Full healing completion check."""
    print("\n✅ HEALING COMPLETION CHECK\n")
    ret, out = run_cmd(["python", "scripts/complete_healing.py"], "Checking completion status")
    print(out)
    return ret


def cmd_automate():
    """Set up automated scheduling."""
    print("\n⏰ SETTING UP AUTOMATION\n")

    if sys.platform == "win32":
        print("Windows Detected - Use Task Scheduler")
        print("\n1. Open Task Scheduler")
        print("2. Create Basic Task")
        print("3. Name: 'NuSyQ Daily Healing'")
        print("4. Trigger: Daily at 2:00 AM")
        print("5. Action: Run program")
        print("6. Program: python")
        print("7. Arguments: scripts/integration_health_check.py --mode full")
        print(f"8. Start in: {Path.cwd()}")
    else:
        print("Linux/Mac Detected - Use cron")
        print("\nAdd to crontab with: crontab -e")
        print("0 2 * * * cd /path/to/NuSyQ-Hub && python scripts/integration_health_check.py --mode full")

    return 0


def cmd_help():
    """Show help."""
    print(__doc__)
    return 0


COMMANDS = {
    "status": (cmd_status, "Show system health dashboard"),
    "diagnose": (cmd_diagnose, "Run full diagnostic scan"),
    "heal": (cmd_heal, "Execute auto-healing cycle"),
    "validate": (cmd_validate, "Run test validation"),
    "process-quests": (cmd_process_quests, "Show and process quests"),
    "complete": (cmd_complete, "Full healing completion check"),
    "automate": (cmd_automate, "Set up automated scheduling"),
    "help": (cmd_help, "Show this help message"),
}


def main():
    """Main entry point."""
    if len(sys.argv) < 2 or sys.argv[1] in ["help", "-h", "--help"]:
        print("🏥 NUSYQ HEALING ORCHESTRATOR\n")
        print("Available Commands:")
        print("─" * 60)
        for name, (_, desc) in COMMANDS.items():
            print(f"  {name:20} {desc}")
        print("\nUsage: python scripts/healing_orchestrator.py <command>")
        return 0

    cmd = sys.argv[1]

    if cmd not in COMMANDS:
        print(f"❌ Unknown command: {cmd}")
        print(f"\nValid commands: {', '.join(COMMANDS.keys())}")
        return 1

    handler, _ = COMMANDS[cmd]
    return handler()


if __name__ == "__main__":
    sys.exit(main())
