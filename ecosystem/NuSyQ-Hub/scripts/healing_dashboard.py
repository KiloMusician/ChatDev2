#!/usr/bin/env python3
"""Healing Dashboard - Real-time system health overview.

This script generates a comprehensive health dashboard showing:
1. Current system status
2. Recent improvements (before/after metrics)
3. Active quests and TODOs
4. Health history trends
5. Recommendations for next steps

Usage:
    python scripts/healing_dashboard.py [--format text|json|html]
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.LOGGING.modular_logging_system import get_logger

logger = get_logger(__name__)


def load_health_history() -> list[dict]:
    """Load health history from JSONL log."""
    history_file = Path("state/reports/health_history.jsonl")

    if not history_file.exists():
        return []

    history = []
    try:
        with open(history_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    history.append(json.loads(line))
    except Exception as e:
        logger.error("dashboard", f"Failed to load health history: {e}")

    return history


def load_pain_points() -> dict[str, Any]:
    """Load current pain points report."""
    pain_file = Path("state/reports/pain_points.json")

    if not pain_file.exists():
        return {}

    try:
        return json.loads(pain_file.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error("dashboard", f"Failed to load pain points: {e}")
        return {}


def count_quest_items() -> int:
    """Count quest items in quest log."""
    quest_file = Path("src/Rosetta_Quest_System/quest_log.jsonl")

    if not quest_file.exists():
        return 0

    count = 0
    try:
        with open(quest_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    count += 1
    except Exception:
        pass

    return count


def get_git_metrics() -> dict[str, Any]:
    """Get git repository metrics."""
    import subprocess

    try:
        # Count commits
        commits_result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"], capture_output=True, text=True, timeout=10
        )
        total_commits = int(commits_result.stdout.strip()) if commits_result.returncode == 0 else 0

        # Count uncommitted
        status_result = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, timeout=10)
        uncommitted = len(status_result.stdout.strip().split("\n")) if status_result.stdout.strip() else 0

        return {"total_commits": total_commits, "uncommitted_files": uncommitted}
    except Exception as e:
        logger.error("dashboard", f"Failed to get git metrics: {e}")
        return {}


def generate_text_dashboard() -> str:
    """Generate text-format dashboard."""
    health_history = load_health_history()
    pain_points = load_pain_points()
    quests = count_quest_items()
    git_metrics = get_git_metrics()

    latest_health = health_history[-1] if health_history else None

    dashboard = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                    NUSYQ-HUB HEALING DASHBOARD                             ║
║                                                                            ║
║                    🏥 SYSTEM HEALTH MONITORING                            ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 CURRENT STATUS
─────────────────────────────────────────────────────────────────────────────
Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}

Latest Health Check: {latest_health["timestamp"] if latest_health else "Never"}
Status: {latest_health["overall_status"].upper() if latest_health else "UNKNOWN"}

🔍 SYSTEM DIAGNOSTICS
─────────────────────────────────────────────────────────────────────────────
TODOs/FIXMEs: {pain_points.get("pain_points", {}).get("todos", {}).get("count", 0) if pain_points else "Unknown"}
Type Suppressions: {pain_points.get("pain_points", {}).get("type_ignores", {}).get("count", 0) if pain_points else "Unknown"}
Lint Errors: {pain_points.get("pain_points", {}).get("lint_errors", {}).get("count", 0) if pain_points else "Unknown"}
Config Issues: {pain_points.get("pain_points", {}).get("redacted_placeholders", {}).get("count", 0) if pain_points else "Unknown"}

📋 TECHNICAL DEBT
─────────────────────────────────────────────────────────────────────────────
Quest Items: {quests}
Git Commits: {git_metrics.get("total_commits", "Unknown")}
Uncommitted Files: {git_metrics.get("uncommitted_files", "Unknown")}

📈 HEALING HISTORY
─────────────────────────────────────────────────────────────────────────────
Total Health Checks: {len(health_history)}
Healthy Cycles: {sum(1 for h in health_history if h.get("overall_status") == "healthy")}
Attention Needed: {sum(1 for h in health_history if h.get("overall_status") != "healthy")}

{"Last 5 Cycles:" if health_history else "No health history yet"}
"""

    if health_history:
        for report in health_history[-5:]:
            ts = report["timestamp"]
            status = "✅" if report["overall_status"] == "healthy" else "⚠️"
            dashboard += f"\n  {status} {ts} - {report['overall_status']}"

    dashboard += """

💡 QUICK ACTIONS
─────────────────────────────────────────────────────────────────────────────
Next Steps:
    1. Run health check: python scripts/integration_health_check.py --mode full
  2. Process quests: python scripts/todos_to_quests.py --limit 10
  3. Check details: python scripts/system_pain_points_finder.py
  4. Review history: cat state/reports/health_history.jsonl

📚 DOCUMENTATION
─────────────────────────────────────────────────────────────────────────────
- Quick Start: QUICK_START_HEALING.md
- Full Results: HEALING_SESSION_RESULTS.md
- Progress: HEALING_PROGRESS_REPORT.md
- Restoration Plan: docs/SYSTEM_HEALTH_RESTORATION_PLAN.md

═════════════════════════════════════════════════════════════════════════════
Generated by NuSyQ Healing System
Dashboard Version: 1.0
═════════════════════════════════════════════════════════════════════════════
"""

    return dashboard


def main():
    """Generate and display healing dashboard."""
    import argparse

    parser = argparse.ArgumentParser(description="Healing dashboard")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    if args.format == "json":
        dashboard_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "health_history": load_health_history(),
            "pain_points": load_pain_points(),
            "quests": count_quest_items(),
            "git_metrics": get_git_metrics(),
        }
        print(json.dumps(dashboard_data, indent=2))
    else:
        print(generate_text_dashboard())

    return 0


if __name__ == "__main__":
    sys.exit(main())
