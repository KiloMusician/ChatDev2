#!/usr/bin/env python3
"""Unified Quest Viewer - View quests from all repos in single interface."""

import json
from pathlib import Path
from typing import Any


class UnifiedQuestViewer:
    """View and manage quests across all repositories."""

    def __init__(self) -> None:
        self.quest_sources = {
            "NuSyQ-Hub": Path("C:/Users/keath/Desktop/Legacy/NuSyQ-Hub/src/Rosetta_Quest_System/quest_log.jsonl"),
            "SimulatedVerse": Path("C:/Users/keath/Desktop/SimulatedVerse/SimulatedVerse/quest_log.jsonl"),
            "NuSyQ": Path("C:/Users/keath/NuSyQ/quest_log.jsonl"),
        }
        self.quests: list[dict[str, Any]] = []

    def load_quests(self) -> None:
        """Load all quests from all repos."""
        for repo_name, quest_file in self.quest_sources.items():
            if not quest_file.exists():
                continue

            try:
                with open(quest_file) as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            quest = json.loads(line)
                            quest["_source_repo"] = repo_name
                            self.quests.append(quest)
                        except json.JSONDecodeError:
                            pass
            except Exception as e:
                print(f"⚠ Error loading {repo_name} quests: {e}")

    def filter_quests(
        self,
        repo: str | None = None,
        quest_type: str | None = None,
        status: str | None = None,
        priority: int | None = None,
    ) -> list[dict[str, Any]]:
        """Filter quests by criteria."""
        filtered = self.quests

        if repo:
            filtered = [q for q in filtered if q.get("_source_repo") == repo]

        if quest_type:
            filtered = [q for q in filtered if q.get("type") == quest_type]

        if status:
            filtered = [q for q in filtered if q.get("status") == status]

        if priority is not None:
            filtered = [q for q in filtered if q.get("priority") == priority]

        return filtered

    def get_stats(self) -> dict[str, Any]:
        """Get quest statistics."""
        return {
            "total_quests": len(self.quests),
            "by_repo": {
                repo: len([q for q in self.quests if q.get("_source_repo") == repo])
                for repo in self.quest_sources.keys()
            },
            "by_type": self._count_by_field("type"),
            "by_status": self._count_by_field("status"),
        }

    def _count_by_field(self, field: str) -> dict[str, int]:
        """Count quests by field value."""
        counts: dict[str, int] = {}
        for quest in self.quests:
            value = quest.get(field, "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts

    def print_quests(
        self,
        quests: list[dict[str, Any]] | None = None,
        limit: int = 20,
    ) -> None:
        """Print quests in human-readable format."""
        if quests is None:
            quests = self.quests

        print("\n" + "=" * 100)
        print("UNIFIED QUEST LOG VIEWER")
        print("=" * 100)

        stats = self.get_stats()
        print(f"\nTotal Quests: {stats['total_quests']}")
        print("\nBy Repository:")
        for repo, count in stats["by_repo"].items():
            print(f"  {repo}: {count}")

        print("\nBy Type:")
        for qtype, count in sorted(stats["by_type"].items(), key=lambda x: -x[1]):
            print(f"  {qtype}: {count}")

        print("\nBy Status:")
        for status, count in sorted(stats["by_status"].items(), key=lambda x: -x[1]):
            print(f"  {status}: {count}")

        print("\n" + "-" * 100)
        print(f"Recent Quests (showing {min(limit, len(quests))} of {len(quests)}):")
        print("-" * 100)

        # Sort by timestamp (most recent first)
        sorted_quests = sorted(
            quests,
            key=lambda q: q.get("timestamp", ""),
            reverse=True,
        )

        for idx, quest in enumerate(sorted_quests[:limit], 1):
            repo = quest.get("_source_repo", "Unknown")
            qtype = quest.get("type", "unknown")
            status = quest.get("status", "unknown")
            title = quest.get("title", quest.get("description", "No title"))[:70]
            timestamp = quest.get("timestamp", "")[:19]  # Truncate to datetime

            status_icon = {
                "completed": "✓",
                "in_progress": "⏳",
                "suggested": "💡",
                "pending": "○",
            }.get(status, "?")

            print(f"\n{idx}. {status_icon} [{repo}] {title}")
            print(f"   Type: {qtype} | Status: {status} | Time: {timestamp}")

            if quest.get("priority"):
                print(f"   Priority: {quest['priority']}")

            if quest.get("effort"):
                print(f"   Effort: {quest['effort']} | Impact: {quest.get('impact', 'N/A')}")


def main() -> None:
    """Main entry point."""
    import sys

    viewer = UnifiedQuestViewer()
    viewer.load_quests()

    # Parse command line args
    if len(sys.argv) > 1:
        if sys.argv[1] == "--type" and len(sys.argv) > 2:
            quests = viewer.filter_quests(quest_type=sys.argv[2])
            viewer.print_quests(quests)
        elif sys.argv[1] == "--repo" and len(sys.argv) > 2:
            quests = viewer.filter_quests(repo=sys.argv[2])
            viewer.print_quests(quests)
        elif sys.argv[1] == "--status" and len(sys.argv) > 2:
            quests = viewer.filter_quests(status=sys.argv[2])
            viewer.print_quests(quests)
        else:
            print("Usage: python unified_quest_viewer.py [--type TYPE | --repo REPO | --status STATUS]")
    else:
        viewer.print_quests()


if __name__ == "__main__":
    main()
