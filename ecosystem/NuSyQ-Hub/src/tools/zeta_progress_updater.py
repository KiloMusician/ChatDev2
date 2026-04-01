"""ZETA Progress Auto-Updater.

Automatically synchronizes quest_log.jsonl with ZETA_PROGRESS_TRACKER.json
to reduce manual documentation overhead.

OmniTag: {'purpose': 'automation', 'type': 'progress_tracking', 'evolution_stage': 'v1.0'}
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, cast

logger = logging.getLogger(__name__)


class ZETAProgressUpdater:
    """Automatically updates ZETA progress tracker from quest log."""

    def __init__(
        self,
        quest_log_path: Path | None = None,
        tracker_path: Path | None = None,
    ) -> None:
        """Initialize ZETAProgressUpdater with quest_log_path, tracker_path."""
        self.quest_log_path = quest_log_path or Path("src/Rosetta_Quest_System/quest_log.jsonl")
        self.tracker_path = tracker_path or Path("config/ZETA_PROGRESS_TRACKER.json")
        self.quests: list[dict[str, Any]] = []
        self.tracker: dict[str, Any] = {}

    def load_quest_log(self) -> None:
        """Load quests from JSONL file."""
        if not self.quest_log_path.exists():
            logger.warning(f"⚠️  Quest log not found: {self.quest_log_path}")
            return

        with open(self.quest_log_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        # Extract quest from details field if present
                        quest = (
                            entry["details"]
                            if "details" in entry and "title" in entry["details"]
                            else entry
                        )
                        self.quests.append(quest)
                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️  Skipping invalid JSON line: {e}")

        logger.info(f"✅ Loaded {len(self.quests)} quests from quest log")

    def load_tracker(self) -> None:
        """Load existing ZETA progress tracker."""
        if not self.tracker_path.exists():
            logger.warning(f"⚠️  Tracker not found: {self.tracker_path}")
            return

        with open(self.tracker_path, encoding="utf-8") as f:
            self.tracker = json.load(f)

        logger.info(f"✅ Loaded ZETA progress tracker from {self.tracker_path}")

    def map_quest_to_zeta(self, quest: dict[str, Any]) -> str | None:
        """Map a quest to its corresponding ZETA task ID."""
        # Extract ZETA ID from quest title or tags
        title = str(quest.get("title", ""))
        raw_tags = quest.get("tags", [])
        tags: list[str] = [str(t) for t in raw_tags]

        # Check for explicit ZETA reference
        for tag in tags:
            if tag.startswith("Zeta") or tag.startswith("zeta"):
                return str(tag)

        # Check title for ZETA pattern
        if "Zeta" in title or "zeta" in title:
            # Extract Zeta\d+ pattern
            import re

            match = re.search(r"[Zz]eta(\d+)", title)
            if match:
                return f"Zeta{match.group(1).zfill(2)}"

        return None

    def get_status_symbol(self, status: str) -> str:
        """Map quest status to ZETA status symbol."""
        status_map = {
            "completed": "✓",
            "in-progress": "◐",
            "in_progress": "◐",
            "pending": "○",
            "blocked": "⊗",
            "mastered": "●",
        }
        return status_map.get(status.lower(), "○")

    def update_zeta_task(self, zeta_id: str, quest: dict[str, Any]) -> None:
        """Update a ZETA task with quest information."""
        # Find the task in tracker
        for _phase_key, phase_data in self.tracker.get("phases", {}).items():
            for task in phase_data.get("tasks", []):
                if task.get("id") == zeta_id:
                    # Update status
                    quest_status = quest.get("status", "pending")
                    task["status"] = self.get_status_symbol(quest_status)

                    # Update state
                    if quest_status == "completed":
                        task["state"] = "COMPLETED"
                    elif quest_status in ["in-progress", "in_progress"]:
                        task["state"] = "IN-PROGRESS"

                    # Add completion date if completed
                    if quest_status == "completed" and "completion_date" not in task:
                        task["completion_date"] = datetime.now().strftime("%Y-%m-%d")

                    # Add progress note
                    if "progress" in quest:
                        task["progress_note"] = quest["progress"]

                    logger.info(f"  ✅ Updated {zeta_id}: {task['status']} {task['state']}")
                    return

        logger.warning(f"  ⚠️  ZETA task {zeta_id} not found in tracker")

    def sync_quests_to_tracker(self) -> None:
        """Synchronize all quests with ZETA tracker."""
        logger.info("\n🔄 Synchronizing quests to ZETA tracker...")

        updated_count = 0
        for quest in self.quests:
            zeta_id = self.map_quest_to_zeta(quest)
            if zeta_id:
                self.update_zeta_task(zeta_id, quest)
                updated_count += 1

        logger.info(f"\n✅ Updated {updated_count} ZETA tasks from {len(self.quests)} quests")

    def save_tracker(self) -> None:
        """Save updated tracker back to file."""
        # Create backup
        backup_path = self.tracker_path.with_suffix(".json.bak")
        if self.tracker_path.exists():
            with open(self.tracker_path, encoding="utf-8") as f:
                backup_data = f.read()
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(backup_data)
            logger.info(f"📦 Backup created: {backup_path}")

        # Save updated tracker
        with open(self.tracker_path, "w", encoding="utf-8") as f:
            json.dump(self.tracker, f, indent=4, ensure_ascii=False)

        logger.info(f"💾 Saved updated tracker to {self.tracker_path}")

    def generate_summary(self) -> dict[str, Any]:
        """Generate a summary of ZETA progress."""
        summary = {
            "total_quests": len(self.quests),
            "zeta_tasks_updated": 0,
            "completion_by_phase": {},
            "overall_completion": 0.0,
        }

        # Count tasks by status
        total_tasks = 0
        completed_tasks = 0

        completion_by_phase = cast(dict[str, Any], summary["completion_by_phase"])
        for phase_key, phase_data in self.tracker.get("phases", {}).items():
            tasks = phase_data.get("tasks", [])
            total_tasks += len(tasks)

            phase_completed = sum(1 for task in tasks if task.get("status") == "✓")
            completed_tasks += phase_completed

            completion_by_phase[phase_key] = {
                "name": phase_data.get("name", "Unknown"),
                "total": len(tasks),
                "completed": phase_completed,
                "percentage": (round((phase_completed / len(tasks)) * 100, 1) if tasks else 0.0),
            }

        if total_tasks > 0:
            summary["overall_completion"] = round((completed_tasks / total_tasks) * 100, 1)

        return summary

    def run(self) -> None:
        """Execute full synchronization workflow."""
        logger.info("=" * 80)
        logger.info("🚀 ZETA PROGRESS AUTO-UPDATER")
        logger.info("=" * 80)

        self.load_quest_log()
        self.load_tracker()
        self.sync_quests_to_tracker()
        self.save_tracker()

        summary = self.generate_summary()

        logger.info("\n" + "=" * 80)
        logger.info("📊 ZETA PROGRESS SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Quests Analyzed: {summary['total_quests']}")
        logger.info(f"Overall Completion: {summary['overall_completion']}%")
        logger.info("\nCompletion by Phase:")
        for _phase, data in summary["completion_by_phase"].items():
            logger.info(
                f"  {data['name']}: {data['completed']}/{data['total']} ({data['percentage']}%)"
            )

        logger.info("\n✅ Synchronization complete!")
        logger.info("=" * 80)


def main() -> None:
    """CLI entry point."""
    updater = ZETAProgressUpdater()
    updater.run()


if __name__ == "__main__":
    main()
