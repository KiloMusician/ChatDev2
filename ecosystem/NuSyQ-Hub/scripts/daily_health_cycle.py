#!/usr/bin/env python3
"""Automated daily health monitoring and healing cycle.

This script orchestrates a complete health check and healing cycle:
1. Diagnostic scan
2. Auto-healing fixes
3. Test validation
4. Quest generation
5. Health report

Can be run daily via cron or scheduler.

Usage:
    python scripts/daily_health_cycle.py [--notify] [--auto-heal]
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.LOGGING.modular_logging_system import get_logger

logger = get_logger(__name__)

HEALTH_LOG = Path("state/reports/health_history.jsonl")


def run_diagnostic() -> dict[str, Any]:
    """Run full diagnostic scan."""
    logger.info("health_cycle", "Running diagnostic scan...")

    result = subprocess.run(
        ["python", "scripts/system_pain_points_finder.py"],
        capture_output=True,
        text=True,
        timeout=300,
    )

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "diagnostic": {"returncode": result.returncode, "status": "complete"},
    }


def run_auto_healing() -> dict[str, Any]:
    """Run auto-healing operations."""
    logger.info("health_cycle", "Running auto-healing...")

    healing_steps = [
        ("ruff fix", ["ruff", "check", "src/", "--fix", "--quiet"]),
        ("black format", ["python", "-m", "black", "src/", "--quiet"]),
        ("todo conversion", ["python", "scripts/todos_to_quests.py", "--limit", "5"]),
    ]

    results = {}
    for name, cmd in healing_steps:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            results[name] = {"returncode": result.returncode, "status": "complete"}
            logger.info("health_cycle", f"Completed: {name}")
        except Exception as e:
            results[name] = {"returncode": 1, "error": str(e), "status": "failed"}
            logger.error("health_cycle", f"Failed: {name}: {e}")

    return results


def run_tests() -> dict[str, Any]:
    """Run validation tests."""
    logger.info("health_cycle", "Running test validation...")

    result = subprocess.run(
        ["python", "-m", "pytest", "tests/test_minimal.py", "-q", "--tb=no"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    passed = failed = 0
    if result.returncode == 0:
        passed = 1
    else:
        failed = 1

    return {
        "tests_passed": passed,
        "tests_failed": failed,
        "status": "passed" if result.returncode == 0 else "failed",
    }


def generate_health_report(diagnostic: dict, healing: dict, tests: dict) -> dict[str, Any]:
    """Generate health report."""
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "cycle": "daily_health",
        "diagnostic": diagnostic,
        "healing": healing,
        "tests": tests,
        "overall_status": (
            "healthy"
            if all(
                [
                    diagnostic.get("diagnostic", {}).get("returncode") == 0,
                    all(h.get("returncode") == 0 for h in healing.values() if isinstance(h, dict)),
                    tests.get("status") == "passed",
                ]
            )
            else "needs_attention"
        ),
    }

    return report


def log_health_report(report: dict[str, Any]) -> None:
    """Log health report to history."""
    HEALTH_LOG.parent.mkdir(parents=True, exist_ok=True)

    with open(HEALTH_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(report) + "\n")

    logger.info("health_cycle", f"Logged health report: {report['overall_status']}")


def commit_changes() -> bool:
    """Commit any changes from healing cycle."""
    try:
        # Check if there are changes
        status_result = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, timeout=10)

        if not status_result.stdout.strip():
            logger.info("health_cycle", "No changes to commit")
            return True

        # Stage and commit
        subprocess.run(["git", "add", "-A"], check=True, timeout=10)
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                "chore: daily health cycle maintenance\n\nAuto-generated from daily health cycle",
            ],
            check=True,
            timeout=30,
        )

        logger.info("health_cycle", "Changes committed")
        return True

    except Exception as e:
        logger.error("health_cycle", f"Commit failed: {e}")
        return False


def generate_summary(report: dict[str, Any]) -> str:
    """Generate human-readable summary."""
    summary = f"""
╔════════════════════════════════════════════════════════════╗
║              DAILY HEALTH CYCLE REPORT                     ║
╚════════════════════════════════════════════════════════════╝

Timestamp: {report["timestamp"]}
Status: {report["overall_status"].upper()}

📊 Diagnostic: {report["diagnostic"]["status"]}
🔧 Healing: {len([h for h in report["healing"].values() if isinstance(h, dict) and h.get("status") == "complete"])} completed
✅ Tests: {report["tests"]["status"].upper()}

Detailed Results:
  - Diagnostic returncode: {report["diagnostic"]["returncode"]}
  - Healing operations: {sum(1 for h in report["healing"].values() if isinstance(h, dict))}
  - Test passed: {report["tests"]["tests_passed"]}
  - Test failed: {report["tests"]["tests_failed"]}

Next Steps:
  1. Review health report: cat {HEALTH_LOG}
  2. Check full diagnostics: python scripts/system_pain_points_finder.py
  3. Process quests: cat src/Rosetta_Quest_System/quest_log.jsonl | tail -20
"""

    return summary


def main():
    """Execute daily health cycle."""
    import argparse

    parser = argparse.ArgumentParser(description="Daily health monitoring cycle")
    parser.add_argument("--notify", action="store_true", help="Send notifications")
    parser.add_argument("--auto-heal", action="store_true", default=True, help="Run auto-healing")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("DAILY HEALTH CYCLE")
    print("=" * 60 + "\n")

    start_time = datetime.utcnow()

    # Run diagnostic
    diagnostic = run_diagnostic()

    # Run healing if enabled
    healing = run_auto_healing() if args.auto_heal else {}

    # Run tests
    tests = run_tests()

    # Generate report
    report = generate_health_report(diagnostic, healing, tests)

    # Log report
    log_health_report(report)

    # Commit changes
    commit_changes()

    # Generate summary
    summary = generate_summary(report)
    print(summary)

    elapsed = (datetime.utcnow() - start_time).total_seconds()
    print(f"\n⏱️ Cycle completed in {elapsed:.1f}s\n")

    return 0 if report["overall_status"] == "healthy" else 1


if __name__ == "__main__":
    sys.exit(main())
