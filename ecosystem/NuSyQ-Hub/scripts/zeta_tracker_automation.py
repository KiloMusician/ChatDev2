"""ZETA Progress Tracker Automation System.

OmniTag: {
    "purpose": "zeta_tracker_automation",
    "tags": ["automation", "zeta", "tracking", "git_hooks"],
    "category": "infrastructure",
    "evolution_stage": "v1.0"
}

Automates ZETA progress tracker updates via:
1. Git pre-commit hooks for automatic status detection
2. File change analysis for completion tracking
3. Auto-updating of ZETA_PROGRESS_TRACKER.json
"""

import json
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ZETATrackerAutomation:
    """Automate ZETA progress tracker updates based on code changes."""

    def __init__(self, project_root: Path | None = None):
        """Initialize ZETA tracker automation.

        Args:
            project_root: Path to project root. Auto-detects if None.
        """
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.tracker_file = self.project_root / "config" / "ZETA_PROGRESS_TRACKER.json"
        self.tracker_data = self._load_tracker()

    def _load_tracker(self) -> dict[str, Any]:
        """Load ZETA tracker data."""
        if not self.tracker_file.exists():
            return self._create_default_tracker()

        try:
            return json.loads(self.tracker_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in {self.tracker_file}, creating new tracker")
            return self._create_default_tracker()

    def _create_default_tracker(self) -> dict[str, Any]:
        """Create default tracker structure."""
        return {
            "last_updated": datetime.now(UTC).isoformat(),
            "phases": {
                "phase1_foundation": {"completion": 0.3, "tasks": {}},
                "phase2_game_dev": {"completion": 0.0, "tasks": {}},
                "phase3_chatdev": {"completion": 0.05, "tasks": {}},
                "phase4_advanced_ai": {"completion": 0.0, "tasks": {}},
                "phase5_ecosystem": {"completion": 0.0, "tasks": {}},
            },
            "auto_updates_enabled": True,
        }

    def analyze_changes(self) -> dict[str, list[str]]:
        """Analyze git changes to detect ZETA task progress.

        Returns:
            Dict mapping ZETA task IDs to changed files.
        """
        try:
            # Get staged files
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                return {}

            changed_files = result.stdout.strip().split("\n")
            return self._map_files_to_tasks(changed_files)

        except Exception as e:
            print(f"Error analyzing changes: {e}")
            return {}

    def _map_files_to_tasks(self, files: list[str]) -> dict[str, list[str]]:
        """Map changed files to ZETA tasks.

        Args:
            files: List of changed file paths.

        Returns:
            Dict mapping task IDs to file lists.
        """
        task_mapping = {
            "Zeta01": ["src/ai/ollama", "src/orchestration/ollama"],
            "Zeta02": ["config/", "src/config/"],
            "Zeta03": ["src/ai/model_selection", "src/orchestration/model"],
            "Zeta04": ["src/orchestration/conversation", "src/ai/conversation"],
            "Zeta05": ["src/diagnostics/", "src/tools/performance"],
            "Zeta06": ["src/terminal/", "terminal"],
            "Zeta07": ["src/utils/timeout", "src/utils/intelligent_timeout"],
            "Zeta21": ["src/game/", "game_dev/", "pygame", "arcade"],
            "Zeta41": ["ChatDev/", "src/integration/chatdev", "chatdev"],
            "Zeta61": ["src/quantum/", "quantum_neuro"],
            "Zeta81": ["godot/", "src/integration/godot"],
        }

        results: dict[str, list[str]] = {}

        for file in files:
            if not file:
                continue

            for task_id, patterns in task_mapping.items():
                if any(pattern in file.lower() for pattern in patterns):
                    if task_id not in results:
                        results[task_id] = []
                    results[task_id].append(file)

        return results

    def update_task_status(self, task_id: str, status: str = "in_progress", completion: float | None = None) -> bool:
        """Update status of a ZETA task.

        Args:
            task_id: ZETA task ID (e.g., "Zeta01")
            status: New status ("initialized", "in_progress", "mastered")
            completion: Optional completion percentage (0.0-1.0)

        Returns:
            True if update successful.
        """
        # Determine phase from task ID
        task_num = int(re.search(r"\d+", task_id).group())
        if task_num <= 20:
            phase = "phase1_foundation"
        elif task_num <= 40:
            phase = "phase2_game_dev"
        elif task_num <= 60:
            phase = "phase3_chatdev"
        elif task_num <= 80:
            phase = "phase4_advanced_ai"
        else:
            phase = "phase5_ecosystem"

        # Update task
        if phase not in self.tracker_data["phases"]:
            self.tracker_data["phases"][phase] = {"completion": 0.0, "tasks": {}}

        if task_id not in self.tracker_data["phases"][phase]["tasks"]:
            self.tracker_data["phases"][phase]["tasks"][task_id] = {}

        task = self.tracker_data["phases"][phase]["tasks"][task_id]
        task["status"] = status
        task["last_updated"] = datetime.now(UTC).isoformat()

        if completion is not None:
            task["completion"] = completion

        # Update phase completion
        self._recalculate_phase_completion(phase)

        return True

    def _recalculate_phase_completion(self, phase: str) -> None:
        """Recalculate phase completion based on task statuses."""
        tasks = self.tracker_data["phases"][phase]["tasks"]

        if not tasks:
            return

        total_completion = 0.0
        for task in tasks.values():
            if task.get("status") == "mastered":
                total_completion += 1.0
            elif task.get("status") == "in_progress":
                total_completion += task.get("completion", 0.5)
            elif task.get("status") == "initialized":
                total_completion += 0.1

        self.tracker_data["phases"][phase]["completion"] = total_completion / len(tasks)

    def auto_update_from_commit(self) -> dict[str, str]:
        """Auto-update tracker based on staged changes.

        Returns:
            Dict of updated tasks and their new statuses.
        """
        if not self.tracker_data.get("auto_updates_enabled", True):
            return {}

        changes = self.analyze_changes()
        updates = {}

        for task_id, files in changes.items():
            # Determine if this is significant progress
            if len(files) >= 3:
                # Multiple files changed = likely in progress
                self.update_task_status(task_id, "in_progress", completion=0.6)
                updates[task_id] = "in_progress"
            elif len(files) >= 1:
                # Some files changed = at least initialized
                current_status = self._get_task_status(task_id)
                if current_status != "mastered":
                    self.update_task_status(task_id, "in_progress", completion=0.3)
                    updates[task_id] = "in_progress"

        if updates:
            self.save_tracker()

        return updates

    def _get_task_status(self, task_id: str) -> str:
        """Get current status of a task."""
        for phase_data in self.tracker_data["phases"].values():
            if task_id in phase_data["tasks"]:
                return phase_data["tasks"][task_id].get("status", "initialized")
        return "unknown"

    def save_tracker(self) -> bool:
        """Save tracker data to file.

        Returns:
            True if save successful.
        """
        try:
            self.tracker_data["last_updated"] = datetime.now(UTC).isoformat()
            self.tracker_file.parent.mkdir(parents=True, exist_ok=True)
            self.tracker_file.write_text(json.dumps(self.tracker_data, indent=2), encoding="utf-8")
            return True
        except Exception as e:
            print(f"Error saving tracker: {e}")
            return False

    def generate_report(self) -> str:
        """Generate human-readable progress report.

        Returns:
            Formatted progress report.
        """
        report = ["=" * 60]
        report.append("ZETA PROGRESS TRACKER - AUTOMATED REPORT")
        report.append(f"Last Updated: {self.tracker_data['last_updated']}")
        report.append("=" * 60)

        for phase_name, phase_data in self.tracker_data["phases"].items():
            completion = phase_data["completion"] * 100
            report.append(f"\n{phase_name.upper()}: {completion:.1f}% complete")

            tasks = phase_data.get("tasks", {})
            for task_id, task_info in sorted(tasks.items()):
                status = task_info.get("status", "unknown")
                status_icon = {
                    "mastered": "●",
                    "in_progress": "◐",
                    "initialized": "○",
                }.get(status, "?")

                report.append(f"  {status_icon} {task_id}: {status}")

        report.append("\n" + "=" * 60)
        return "\n".join(report)


def install_git_hook():
    """Install pre-commit git hook for automatic ZETA tracking."""
    project_root = Path(__file__).parent.parent.parent
    hook_file = project_root / ".git" / "hooks" / "pre-commit"

    hook_content = """#!/usr/bin/env python3
\"\"\"Pre-commit hook for ZETA tracker auto-updates.\"\"\"

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from scripts.zeta_tracker_automation import ZETATrackerAutomation

    tracker = ZETATrackerAutomation()
    updates = tracker.auto_update_from_commit()

    if updates:
        print("\\n🎯 ZETA Tracker Auto-Updated:")
        for task_id, status in updates.items():
            print(f"  • {task_id}: {status}")
        print()

except Exception as e:
    print(f"Warning: ZETA tracker update failed: {e}")
    # Don't block commit on tracker failure

# Exit successfully
sys.exit(0)
"""

    try:
        hook_file.parent.mkdir(parents=True, exist_ok=True)
        hook_file.write_text(hook_content, encoding="utf-8")
        if os.name != "nt":
            hook_file.chmod(0o755)  # Make executable
        print(f"✅ Git pre-commit hook installed at {hook_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to install git hook: {e}")
        return False


if __name__ == "__main__":
    # Install hook and run initial analysis
    install_git_hook()

    tracker = ZETATrackerAutomation()
    print(tracker.generate_report())
