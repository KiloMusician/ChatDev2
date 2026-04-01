#!/usr/bin/env python3
"""Generate quick-wins suggestions from current system state.
Analyzes ZETA tracker, health assessment, and error patterns to suggest low-effort, high-impact tasks.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def load_json_file(path: Path) -> dict[str, Any] | None:
    """Safely load JSON file."""
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def generate_quick_wins() -> list[dict[str, str]]:
    """Generate list of quick-wins based on system analysis."""
    quick_wins: list[dict[str, str]] = []
    repo_root = Path.cwd()

    # Check latest health assessment receipt
    health_receipt_dir = repo_root / "state" / "receipts" / "diagnostics"
    if health_receipt_dir.exists():
        receipts = list(health_receipt_dir.glob("health_*.json"))
        if receipts:
            latest_health = max(receipts, key=lambda f: f.stat().st_mtime)
            health_data = load_json_file(latest_health)
            if health_data:
                # Quick win: Fix enhancement candidates
                enhancement_count = health_data.get("metrics", {}).get("enhancement_candidates", 0)
                if enhancement_count > 0:
                    quick_wins.append(
                        {
                            "title": f"Review {enhancement_count} enhancement candidates",
                            "effort": "Low",
                            "impact": "High",
                            "reasoning": f"{enhancement_count} files are ready for optimization. Run diagnostics for details.",
                            "command": "python src/diagnostics/system_health_assessor.py",
                        }
                    )

                # Quick win: Fix launch pad files
                launch_pad_count = health_data.get("metrics", {}).get("launch_pad_files", 0)
                if launch_pad_count > 0:
                    quick_wins.append(
                        {
                            "title": f"Promote {launch_pad_count} launch-pad files to production",
                            "effort": "Low-Medium",
                            "impact": "Medium",
                            "reasoning": f"{launch_pad_count} files are in launch-pad state. Move to src/ if ready.",
                            "command": "grep -r 'launch_pad' --include='*.json' .",
                        }
                    )

    # Check broken files
    quick_analysis = repo_root / "quick_system_analysis_latest.json"
    if quick_analysis.exists():
        analysis = load_json_file(quick_analysis)
        if analysis and analysis.get("broken_files"):
            broken_count = len(analysis.get("broken_files", []))
            if broken_count > 0:
                quick_wins.append(
                    {
                        "title": f"Fix {broken_count} broken imports/syntax issues",
                        "effort": "Medium",
                        "impact": "Critical",
                        "reasoning": f"System has {broken_count} broken files. Fix will unlock many features.",
                        "command": "python src/healing/repository_health_restorer.py",
                    }
                )

    # Generic quick wins (always available)
    quick_wins.extend(
        [
            {
                "title": "Run full linting pipeline (black + ruff + mypy)",
                "effort": "Low",
                "impact": "High",
                "reasoning": "Prevents technical debt and catches errors early.",
                "command": "python scripts/lint_test_check.py",
            },
            {
                "title": "Verify all imports work (smoke test)",
                "effort": "Low",
                "impact": "High",
                "reasoning": "Quick check that all modules are importable.",
                "command": "python -c 'import src; print(\"✓ All imports OK\")'",
            },
            {
                "title": "Run culture-ship health check",
                "effort": "Low",
                "impact": "High",
                "reasoning": "Validates orchestration system is operational.",
                "command": "python scripts/start_nusyq.py health-only",
            },
            {
                "title": "Generate unified error ground truth report",
                "effort": "Medium",
                "impact": "High",
                "reasoning": "Create canonical error list for all repos (1,228 errors identified).",
                "command": "python scripts/scan_all_repos_errors.py",
            },
            {
                "title": "Wire SimulatedVerse health to Hub",
                "effort": "Medium",
                "impact": "High",
                "reasoning": "Enable cross-repo health checks via unified endpoint.",
                "command": "# See docs/100_STEP_ROADMAP.md step #11-12",
            },
            {
                "title": "Document all 50+ modules in capability matrix",
                "effort": "Medium",
                "impact": "High",
                "reasoning": "Create searchable inventory of what exists.",
                "command": "python scripts/generate_capability_matrix.py",
            },
        ]
    )

    return quick_wins


def save_quick_wins_to_quest_log(quick_wins: list[dict[str, str]]) -> None:
    """Append quick-wins as new quest items to quest log."""
    quest_log_path = Path.cwd() / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"

    if not quest_log_path.exists():
        print(f"❌ Quest log not found at {quest_log_path}")
        return

    # Append each quick-win as a quest entry
    with open(quest_log_path, "a") as f:
        for idx, win in enumerate(quick_wins, 1):
            quest_entry = {
                "timestamp": datetime.now().isoformat(),
                "type": "quick_win",
                "priority": idx,  # Higher index = lower priority
                "title": win["title"],
                "effort": win["effort"],
                "impact": win["impact"],
                "reasoning": win["reasoning"],
                "status": "suggested",
                "source": "generate_quick_wins.py",
            }
            f.write(json.dumps(quest_entry) + "\n")

    print(f"✓ Appended {len(quick_wins)} quick-wins to quest log")
    print(f"  Location: {quest_log_path}")


def print_quick_wins(quick_wins: list[dict[str, str]]) -> None:
    """Print quick-wins in human-readable format."""
    print("\n" + "=" * 80)
    print("QUICK WINS - Low Effort, High Impact Suggestions")
    print("=" * 80 + "\n")

    for idx, win in enumerate(quick_wins, 1):
        print(f"#{idx}. {win['title']}")
        print(f"   Effort: {win['effort']} | Impact: {win['impact']}")
        print(f"   Reasoning: {win['reasoning']}")
        if win.get("command") and win["command"].startswith("#"):
            print(f"   Command: {win['command']}")
        else:
            print(f"   Command: {win['command']}")
        print()


if __name__ == "__main__":
    quick_wins = generate_quick_wins()

    print_quick_wins(quick_wins)
    save_quick_wins_to_quest_log(quick_wins)

    print(f"\n✓ Generated {len(quick_wins)} quick-win suggestions")
