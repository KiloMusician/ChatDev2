"""Quest Priority Reorganizer for ZETA Phase 1 Focus.
[ROUTE AGENTS] 🤖

OmniTag: {
    "purpose": "quest_prioritization",
    "tags": ["quest_system", "zeta", "prioritization"],
    "category": "automation",
    "evolution_stage": "v1.0"
}

Reorganizes quest priorities to focus on ZETA Phase 1 completion (20 tasks).
Pauses non-essential quests until foundation is solid.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class QuestPrioritizer:
    """Reorganize quest priorities to focus on ZETA Phase 1."""

    # ZETA Phase 1 tasks (Z01-Z20: Foundation Quantum-States)
    PHASE1_ZETA_TASKS = {
        "Zeta01": "Ollama Hub - ESTABLISHED",
        "Zeta02": "Config Management - SECURED",
        "Zeta03": "Intelligent Model Selection - IN-PROGRESS",
        "Zeta04": "Conversation Management - ENHANCED",
        "Zeta05": "Performance Monitoring - MASTERED",
        "Zeta06": "Terminal Management - MASTERED",
        "Zeta07": "Timeout Configuration - MASTERED",
        "Zeta08": "Error Recovery System",
        "Zeta09": "Context Awareness Engine",
        "Zeta10": "Logging Infrastructure",
        "Zeta11": "Testing Framework",
        "Zeta12": "Documentation Generator",
        "Zeta13": "Code Quality Tools",
        "Zeta14": "Import Health System",
        "Zeta15": "Path Intelligence",
        "Zeta16": "Repository Coordination",
        "Zeta17": "Healing Automation",
        "Zeta18": "Quest System Core",
        "Zeta19": "Semantic Tagging",
        "Zeta20": "Integration Bridge",
    }

    # Map existing quests to ZETA tasks
    QUEST_TO_ZETA_MAPPING = {
        "Install Ollama & models": "Zeta01",
        "Test AI integration": "Zeta01",
        "Gather system information": "Zeta02",
        "Maintain classify_python_files.py": "Zeta14",
        "Maintain quick_import_fix.py": "Zeta14",
        "Maintain ImportHealthCheck.ps1": "Zeta14",
        "Maintain ArchitectureWatcher.py": "Zeta16",
        "Maintain RepositoryCoordinator.ps1/py": "Zeta16",
        "Maintain PathIntelligence.ps1/py": "Zeta15",
        "Maintain heal_repository.py": "Zeta17",
        "Maintain copilot_enhancement_bridge.py": "Zeta20",
    }

    def __init__(self, project_root: Path | None = None):
        """Initialize quest prioritizer.

        Args:
            project_root: Path to project root. Auto-detects if None.
        """
        self.project_root = project_root or Path(__file__).parent.parent
        self.quest_log_file = self.project_root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        self.quests_file = self.project_root / "src" / "Rosetta_Quest_System" / "quests.json"

    def load_quests(self) -> list[dict[str, Any]]:
        """Load all quests from quest_log.jsonl.

        Returns:
            List of quest dictionaries.
        """
        quests = []

        if not self.quest_log_file.exists():
            print(f"Quest log not found: {self.quest_log_file}")
            return quests

        try:
            for line in self.quest_log_file.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    quests.append(json.loads(line))
        except Exception as e:
            print(f"Error loading quests: {e}")

        return quests

    def categorize_quests(self, quests: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """Categorize quests by ZETA phase alignment.

        Args:
            quests: List of quest dictionaries.

        Returns:
            Dict with categories: "phase1_critical", "phase1_supporting", "future_phases", "general"
        """
        categories = {
            "phase1_critical": [],  # Directly maps to incomplete ZETA 1-20 tasks
            "phase1_supporting": [],  # Supports ZETA 1-20 completion
            "future_phases": [],  # ZETA 21+ tasks
            "general": [],  # Non-ZETA aligned tasks
        }

        for quest in quests:
            title = quest.get("title", "")
            status = quest.get("status", "pending")

            # Skip completed quests
            if status == "completed":
                continue

            # Check if directly maps to ZETA task
            zeta_task = self.QUEST_TO_ZETA_MAPPING.get(title)

            if zeta_task and zeta_task in self.PHASE1_ZETA_TASKS:
                categories["phase1_critical"].append(quest)
            elif any(
                keyword in title.lower()
                for keyword in [
                    "test",
                    "coverage",
                    "documentation",
                    "import",
                    "path",
                    "config",
                    "monitor",
                ]
            ):
                categories["phase1_supporting"].append(quest)
            elif any(keyword in title.lower() for keyword in ["game", "godot", "chatdev launcher", "quantum"]):
                categories["future_phases"].append(quest)
            else:
                categories["general"].append(quest)

        return categories

    def create_phase1_focus_plan(self) -> dict[str, Any]:
        """Create a focused plan for ZETA Phase 1 completion.

        Returns:
            Structured plan with prioritized tasks.
        """
        quests = self.load_quests()
        categorized = self.categorize_quests(quests)

        # Identify incomplete ZETA Phase 1 tasks
        incomplete_zeta = []
        completed_zeta = ["Zeta01", "Zeta02", "Zeta05", "Zeta06", "Zeta07"]  # Mastered

        for zeta_id, description in self.PHASE1_ZETA_TASKS.items():
            if zeta_id not in completed_zeta:
                incomplete_zeta.append({"id": zeta_id, "description": description})

        plan = {
            "created_at": datetime.now(UTC).isoformat(),
            "objective": "Complete ZETA Phase 1 (Z01-Z20) Foundation Quantum-States",
            "current_progress": {
                "completed": len(completed_zeta),
                "total": 20,
                "percentage": len(completed_zeta) / 20 * 100,
            },
            "strategy": "Focus on incomplete ZETA 1-20 tasks, pause non-essential work",
            "priority_levels": {
                "P0_immediate": [
                    "Zeta03",
                    "Zeta11",
                    "Zeta12",
                ],  # Model selection, Testing, Docs
                "P1_critical": [
                    "Zeta08",
                    "Zeta09",
                    "Zeta13",
                ],  # Error recovery, Context, Quality
                "P2_important": [
                    "Zeta14",
                    "Zeta15",
                    "Zeta17",
                ],  # Import health, Path, Healing
                "P3_foundation": [
                    "Zeta10",
                    "Zeta16",
                    "Zeta18",
                    "Zeta19",
                    "Zeta20",
                ],  # Logging, Repo, Quest, Tags, Bridge
            },
            "incomplete_tasks": incomplete_zeta,
            "existing_quests": {
                "phase1_critical": len(categorized["phase1_critical"]),
                "phase1_supporting": len(categorized["phase1_supporting"]),
                "paused_future_phases": len(categorized["future_phases"]),
                "paused_general": len(categorized["general"]),
            },
            "recommendations": [
                "Complete Zeta03 (Model Selection) - already in progress",
                "Implement Zeta11 (Testing Framework) - critical for 37% → 70% coverage goal",
                "Build Zeta12 (Documentation Generator) - addresses 407 missing tags",
                "Create Zeta08 (Error Recovery) - handles 234 VS Code errors",
                "Develop Zeta13 (Code Quality Tools) - automates ruff/mypy fixes",
                "Pause new game dev quests until Phase 1 complete",
                "Pause new package creation quests until Phase 1 complete",
            ],
        }

        return plan

    def generate_prioritized_quest_list(self) -> list[dict[str, Any]]:
        """Generate prioritized quest list focused on ZETA Phase 1.

        Returns:
            List of quests ordered by priority.
        """
        self.create_phase1_focus_plan()  # Call for side effects
        prioritized = []

        # P0: Immediate (Testing, Docs, Model Selection)
        prioritized.extend(
            [
                {
                    "quest_id": "ZETA_P0_001",
                    "title": "Complete Zeta11: Testing Framework (37% → 70% coverage)",
                    "description": "Implement comprehensive testing framework with 50/30/20 split",
                    "priority": "P0_immediate",
                    "zeta_task": "Zeta11",
                    "estimated_effort": "high",
                    "dependencies": [],
                },
                {
                    "quest_id": "ZETA_P0_002",
                    "title": "Complete Zeta12: Documentation Generator (407 missing tags)",
                    "description": "Build automated semantic tagging and API doc generation",
                    "priority": "P0_immediate",
                    "zeta_task": "Zeta12",
                    "estimated_effort": "medium",
                    "dependencies": [],
                },
                {
                    "quest_id": "ZETA_P0_003",
                    "title": "Complete Zeta03: Intelligent Model Selection",
                    "description": "Finish model selection enhancement (already in-progress)",
                    "priority": "P0_immediate",
                    "zeta_task": "Zeta03",
                    "estimated_effort": "low",
                    "dependencies": [],
                },
            ]
        )

        # P1: Critical (Error recovery, Context, Quality)
        prioritized.extend(
            [
                {
                    "quest_id": "ZETA_P1_001",
                    "title": "Implement Zeta08: Error Recovery System",
                    "description": "Automated error detection and recovery for 234 VS Code errors",
                    "priority": "P1_critical",
                    "zeta_task": "Zeta08",
                    "estimated_effort": "high",
                    "dependencies": ["Zeta13"],
                },
                {
                    "quest_id": "ZETA_P1_002",
                    "title": "Build Zeta09: Context Awareness Engine",
                    "description": "Real-time context monitoring and awareness system",
                    "priority": "P1_critical",
                    "zeta_task": "Zeta09",
                    "estimated_effort": "medium",
                    "dependencies": [],
                },
                {
                    "quest_id": "ZETA_P1_003",
                    "title": "Create Zeta13: Code Quality Tools",
                    "description": "Automated ruff/mypy/black integration and auto-fix",
                    "priority": "P1_critical",
                    "zeta_task": "Zeta13",
                    "estimated_effort": "medium",
                    "dependencies": [],
                },
            ]
        )

        return prioritized

    def save_prioritized_plan(self, output_file: Path | None = None) -> bool:
        """Save prioritized plan to file.

        Args:
            output_file: Path to save plan. Defaults to config/PHASE1_FOCUS_PLAN.json

        Returns:
            True if save successful.
        """
        if output_file is None:
            output_file = self.project_root / "config" / "PHASE1_FOCUS_PLAN.json"

        try:
            plan = self.create_phase1_focus_plan()
            plan["prioritized_quests"] = self.generate_prioritized_quest_list()

            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(json.dumps(plan, indent=2), encoding="utf-8")

            print(f"✅ Phase 1 focus plan saved to {output_file}")
            return True

        except Exception as e:
            print(f"❌ Error saving plan: {e}")
            return False

    def generate_report(self) -> str:
        """Generate human-readable prioritization report.

        Returns:
            Formatted report.
        """
        plan = self.create_phase1_focus_plan()

        report = ["=" * 70]
        report.append("QUEST PRIORITIZATION REPORT - ZETA PHASE 1 FOCUS")
        report.append("=" * 70)
        report.append(f"\nObjective: {plan['objective']}")
        report.append(
            f"Progress: {plan['current_progress']['completed']}/20 tasks "
            f"({plan['current_progress']['percentage']:.1f}%)"
        )
        report.append(f"\nStrategy: {plan['strategy']}")

        report.append("\n\n📋 PRIORITY LEVELS:")
        for level, tasks in plan["priority_levels"].items():
            report.append(f"\n{level}:")
            for task in tasks:
                description = self.PHASE1_ZETA_TASKS.get(task, "Unknown")
                report.append(f"  • {task}: {description}")

        report.append("\n\n🎯 TOP RECOMMENDATIONS:")
        for i, rec in enumerate(plan["recommendations"][:5], 1):
            report.append(f"{i}. {rec}")

        report.append("\n\n📊 EXISTING QUEST STATUS:")
        for category, count in plan["existing_quests"].items():
            status = "🟢 Active" if "phase1" in category else "⏸️ Paused"
            report.append(f"{status} {category}: {count} quests")

        report.append("\n" + "=" * 70)
        return "\n".join(report)


if __name__ == "__main__":
    prioritizer = QuestPrioritizer()

    # Generate and display report
    print(prioritizer.generate_report())

    # Save plan
    prioritizer.save_prioritized_plan()

    print("\n✅ Quest prioritization complete. Focus on ZETA Phase 1 tasks (Z01-Z20)!")
