#!/usr/bin/env python3
"""Auto-Quest Generator from Error Clusters

Implements config decision #99: Auto-convert errors into guild quests.
Takes error scan results and creates guild quests for the top N clusters.
"""

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.terminal_output import to_claude, to_suggestions, to_tasks, to_zeta


class AutoQuestGenerator:
    """Generate guild quests from error clusters."""

    def __init__(self):
        self.root = Path(__file__).parent.parent
        self.config = self._load_config()
        self.error_scan_path = self.root / "state" / "reports" / "ecosystem_scan.json"
        self.quest_templates_path = self.root / "config" / "quest_templates.json"

    def _load_config(self) -> dict:
        """Load ecosystem defaults."""
        config_path = self.root / "config" / "ecosystem_defaults.json"
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {}

    def load_error_scan(self) -> dict:
        """Load latest error scan results."""
        if not self.error_scan_path.exists():
            to_claude("No error scan found - run full_ecosystem_error_scan.py first")
            return {}

        with open(self.error_scan_path) as f:
            return json.load(f)

    def cluster_errors(self, scan_data: dict) -> list[dict]:
        """Group errors by type into clusters."""
        clusters = defaultdict(lambda: {"count": 0, "files": [], "error_type": ""})

        for error_info in scan_data.get("top_error_types", []):
            error_type = error_info["type"]
            count = error_info["count"]

            clusters[error_type]["count"] = count
            clusters[error_type]["error_type"] = error_type

        # Add file info from worst_files
        for _file_info in scan_data.get("worst_files", []):
            # This is approximate - we don't have per-file error types in scan
            # In real implementation, we'd enhance the scanner
            pass

        # Convert to list and sort by count
        cluster_list = [{"error_type": k, **v} for k, v in clusters.items()]
        cluster_list.sort(key=lambda x: x["count"], reverse=True)

        return cluster_list

    def create_quest_from_cluster(self, cluster: dict, priority: int) -> dict:
        """Create a guild quest from an error cluster."""
        error_type = cluster["error_type"]
        count = cluster["count"]

        # Map error types to quest templates
        quest_templates = {
            "invalid-syntax": {
                "title": f"Fix {count} syntax errors across ecosystem",
                "description": "These are broken Python files that won't parse. Likely generated code or incomplete edits.",
                "safety_tier": "safe",
                "tags": ["syntax", "automated"],
                "acceptance_criteria": [
                    "All syntax errors fixed or files excluded",
                    "Remaining files pass AST parsing",
                ],
                "estimated_duration_minutes": count * 2,
                "suggested_agent": "copilot",
            },
            "F405": {
                "title": f"Fix {count} undefined imports (F405)",
                "description": "Star imports or missing module definitions causing undefined names.",
                "safety_tier": "safe",
                "tags": ["imports", "automated"],
                "acceptance_criteria": ["All F405 errors resolved", "Imports properly defined"],
                "estimated_duration_minutes": count * 1,
                "suggested_agent": "claude",
            },
            "F401": {
                "title": f"Remove {count} unused imports (F401)",
                "description": "Cleanup unused imports to reduce noise and improve code quality.",
                "safety_tier": "safe",
                "tags": ["cleanup", "automated"],
                "acceptance_criteria": ["All F401 errors auto-fixed", "No functionality broken"],
                "estimated_duration_minutes": count * 0.5,
                "suggested_agent": "copilot",
            },
            "F841": {
                "title": f"Clean up {count} unused variables (F841)",
                "description": "Remove or rename unused local variables.",
                "safety_tier": "safe",
                "tags": ["cleanup", "refactoring"],
                "acceptance_criteria": ["All F841 warnings resolved", "Logic preserved"],
                "estimated_duration_minutes": count * 1,
                "suggested_agent": "codex",
            },
            "F541": {
                "title": f"Fix {count} f-strings without placeholders (F541)",
                "description": "Convert f-strings to regular strings or add placeholders.",
                "safety_tier": "safe",
                "tags": ["cleanup", "automated"],
                "acceptance_criteria": ["All F541 warnings auto-fixed"],
                "estimated_duration_minutes": count * 0.3,
                "suggested_agent": "copilot",
            },
        }

        # Get template or use default
        template = quest_templates.get(
            error_type,
            {
                "title": f"Fix {count} {error_type} errors",
                "description": f"Address {error_type} errors across the ecosystem.",
                "safety_tier": "standard",
                "tags": ["error_fixing", error_type],
                "acceptance_criteria": [f"All {error_type} errors resolved"],
                "estimated_duration_minutes": count * 2,
                "suggested_agent": "claude",
            },
        )

        # Generate quest ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = error_type.lower().replace("-", "_")
        quest_id = f"quest_{timestamp}_{slug}"

        quest = {
            "quest_id": quest_id,
            "title": template["title"],
            "description": template["description"],
            "priority": priority,  # 1-5, based on cluster rank
            "safety_tier": template["safety_tier"],
            "state": "open",
            "created_at": datetime.now().isoformat(),
            "tags": template["tags"],
            "acceptance_criteria": template["acceptance_criteria"],
            "error_cluster": {
                "type": error_type,
                "count": count,
                "files": cluster.get("files", []),
            },
            "suggested_agent": template.get("suggested_agent", "claude"),
            "estimated_duration_minutes": template["estimated_duration_minutes"],
        }

        return quest

    def generate_quests(self) -> list[dict]:
        """Generate quests from error scan."""
        to_zeta("Auto-quest generation: Analyzing error clusters...")

        # Load error scan
        scan_data = self.load_error_scan()
        if not scan_data:
            return []

        # Cluster errors
        clusters = self.cluster_errors(scan_data)
        to_claude(f"Found {len(clusters)} error clusters")

        # Get top N from config
        max_clusters = self.config.get("guild_board", {}).get("error_to_quest_cluster_count", 10)
        top_clusters = clusters[:max_clusters]

        # Generate quests
        quests = []
        for i, cluster in enumerate(top_clusters):
            # Priority: 1 (highest) for top cluster, decreasing
            priority = min(5, max(1, 5 - (i // 2)))

            quest = self.create_quest_from_cluster(cluster, priority)
            quests.append(quest)

            to_tasks(f"Created quest: {quest['title']} (priority {priority})")

        to_suggestions(f"Generated {len(quests)} quests from error clusters - ready for agent claiming!")

        return quests

    def save_quests(self, quests: list[dict]) -> Path:
        """Save generated quests."""
        output_path = self.root / "state" / "auto_generated_quests.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(
                {
                    "generated_at": datetime.now().isoformat(),
                    "source": "error_cluster_analysis",
                    "quest_count": len(quests),
                    "quests": quests,
                },
                f,
                indent=2,
            )

        to_claude(f"Saved {len(quests)} auto-generated quests to {output_path}")
        return output_path

    def run(self):
        """Run auto-quest generation."""
        print("=" * 70)
        print("🎯 AUTO-QUEST GENERATOR")
        print("=" * 70)
        print()

        quests = self.generate_quests()

        if quests:
            output_path = self.save_quests(quests)

            print(f"\n✅ Generated {len(quests)} quests from error clusters")
            print(f"📁 Saved to: {output_path}")
            print()
            print("📋 Quest Summary:")
            for quest in quests:
                print(f"   [{quest['quest_id']}] {quest['title']}")
                print(
                    f"      Priority: {quest['priority']} | Safety: {quest['safety_tier']} | Agent: {quest['suggested_agent']}"
                )
                print(f"      Errors: {quest['error_cluster']['count']} {quest['error_cluster']['type']}")
                print()

            print("🚀 Next Steps:")
            print("   1. Agents can claim these quests from the guild board")
            print("   2. Use quest templates for consistent execution")
            print("   3. Track progress in guild board")
            print()
        else:
            print("⚠️  No error scan found - run full_ecosystem_error_scan.py first")

        print("=" * 70)


if __name__ == "__main__":
    generator = AutoQuestGenerator()
    generator.run()
