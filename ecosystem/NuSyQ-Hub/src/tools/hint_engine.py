"""Hint Engine: AI-powered quest suggestion system.

Analyzes quest dependencies, current progress, and contextual factors to suggest
the next most actionable quests for the user. Uses scoring algorithms to rank
quests by priority, effort, and strategic alignment.

[OmniTag: "tool⨳hinting⦾suggestion_system→optimization", "v1.0", "async-ready"]
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    import networkx as nx
except ImportError:
    nx = None


@dataclass
class QuestScore:
    """Score breakdown for a quest."""

    quest_id: str
    quest_title: str
    base_priority: int = 1
    zeta_stage_boost: float = 1.0
    blocked_penalty: float = 1.0
    effort_factor: float = 1.0
    dependency_factor: float = 1.0
    final_score: float = 0.0
    rationale: str = ""

    def calculate(self) -> float:
        """Calculate composite score."""
        self.final_score = (
            self.base_priority
            * self.zeta_stage_boost
            / self.blocked_penalty
            * self.effort_factor
            * self.dependency_factor
        )
        return self.final_score


@dataclass
class HintResult:
    """Result of hint engine analysis."""

    suggested_quests: list = field(default_factory=list)
    reasoning: str = ""
    timestamp: str = ""
    metrics: dict = field(default_factory=dict)


class HintEngine:
    """Quest suggestion engine with dependency analysis."""

    def __init__(
        self,
        quest_log_path: Path | None = None,
        zeta_tracker_path: Path | None = None,
    ) -> None:
        """Initialize hint engine.

        Args:
            quest_log_path: Path to quest_log.jsonl
            zeta_tracker_path: Path to ZETA_PROGRESS_TRACKER.json
        """
        self.quest_log_path = quest_log_path or Path("src/Rosetta_Quest_System/quest_log.jsonl")
        self.zeta_tracker_path = zeta_tracker_path or Path("config/ZETA_PROGRESS_TRACKER.json")

        self.quests: dict = {}
        self.zeta_data: dict = {}
        self.dependency_graph: Any = None
        self.actionable_quests: list = []
        self.blocked_quests: list = []

    def load_quests(self) -> bool:
        """Load quest log from JSONL file.

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.quest_log_path.exists():
                logger.warning(f"⚠️  Quest log not found: {self.quest_log_path}")
                return False

            self.quests = {}
            with open(self.quest_log_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        quest_data = json.loads(line)
                        quest_id = quest_data.get("id", quest_data.get("title", ""))
                        self.quests[quest_id] = quest_data
                    except json.JSONDecodeError:
                        continue

            logger.info(f"✅ Loaded {len(self.quests)} quests")
            return True
        except (FileNotFoundError, PermissionError, json.JSONDecodeError) as e:
            logger.error(f"❌ Error loading quests: {e}")
            return False

    def load_zeta_tracker(self) -> bool:
        """Load ZETA progress tracker.

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.zeta_tracker_path.exists():
                logger.warning(f"⚠️  ZETA tracker not found: {self.zeta_tracker_path}")
                return False

            with open(self.zeta_tracker_path, encoding="utf-8") as f:
                self.zeta_data = json.load(f)

            logger.info("✅ Loaded ZETA tracker")
            return True
        except (FileNotFoundError, PermissionError, json.JSONDecodeError) as e:
            logger.error(f"❌ Error loading ZETA tracker: {e}")
            return False

    def build_dependency_graph(self) -> None:
        """Build network graph of quest dependencies."""
        if nx is None:
            logger.warning("⚠️  NetworkX not available, skipping dependency graph")
            return

        self.dependency_graph = nx.DiGraph()

        # Add all quests as nodes
        for quest_id in self.quests:
            self.dependency_graph.add_node(quest_id)

        # Add dependencies as edges
        for quest_id, quest_data in self.quests.items():
            dependencies = quest_data.get("dependencies", [])
            if isinstance(dependencies, str):
                dependencies = [d.strip() for d in dependencies.split(",")]

            for dep in dependencies:
                if dep in self.quests:
                    self.dependency_graph.add_edge(dep, quest_id)

        if self.dependency_graph is not None:
            logger.info(f"✅ Built dependency graph ({len(self.dependency_graph.nodes)} nodes)")

    def categorize_quests(self) -> None:
        """Categorize quests as actionable or blocked."""
        self.actionable_quests = []
        self.blocked_quests = []

        for quest_id, quest_data in self.quests.items():
            # Check if quest is already completed
            zeta_id = None
            if "zeta_tags" in quest_data:
                tags = quest_data.get("zeta_tags", [])
                if tags:
                    zeta_id = tags[0]

            if zeta_id and zeta_id in self.zeta_data.get("tasks", {}):
                task_data = self.zeta_data["tasks"][zeta_id]
                if task_data.get("status") == "completed":
                    continue

            # Check dependencies
            dependencies = quest_data.get("dependencies", [])
            if isinstance(dependencies, str):
                dependencies = [d.strip() for d in dependencies.split(",")]

            blocked = False
            for dep in dependencies:
                if dep in self.quests:
                    dep_quest = self.quests[dep]
                    dep_zeta = None
                    if "zeta_tags" in dep_quest:
                        tags = dep_quest.get("zeta_tags", [])
                        if tags:
                            dep_zeta = tags[0]

                    if dep_zeta and dep_zeta in self.zeta_data.get("tasks", {}):
                        task_data = self.zeta_data["tasks"][dep_zeta]
                        if task_data.get("status") != "completed":
                            blocked = True
                            break

            if blocked:
                self.blocked_quests.append(quest_id)
            else:
                self.actionable_quests.append(quest_id)

        logger.info(
            f"✅ Categorized: {len(self.actionable_quests)} actionable, {len(self.blocked_quests)} blocked"
        )

    def score_quest(self, quest_id: str) -> QuestScore:
        """Calculate score for a quest.

        Args:
            quest_id: The quest ID

        Returns:
            QuestScore with detailed breakdown
        """
        quest_data = self.quests.get(quest_id, {})
        score = QuestScore(quest_id=quest_id, quest_title=quest_data.get("title", ""))

        # Base priority from quest data
        priority_tags = quest_data.get("priority_tags", [])
        if "critical" in priority_tags:
            score.base_priority = 10
        elif "high" in priority_tags:
            score.base_priority = 7
        elif "medium" in priority_tags:
            score.base_priority = 4
        elif "low" in priority_tags:
            score.base_priority = 2

        # ZETA stage boost
        zeta_tags = quest_data.get("zeta_tags", [])
        if zeta_tags:
            zeta_id = zeta_tags[0]
            zeta_phase = int(zeta_id.split("_")[1]) if "_" in zeta_id else 0
            score.zeta_stage_boost = 1.0 + (zeta_phase * 0.5)

        # Blocked penalty
        if quest_id in self.blocked_quests:
            score.blocked_penalty = 3.0

        # Effort factor (lower effort = higher score)
        effort = quest_data.get("effort_estimate", "medium")
        if effort == "low":
            score.effort_factor = 1.2
        elif effort == "medium":
            score.effort_factor = 1.0
        elif effort == "high":
            score.effort_factor = 0.8
        else:
            score.effort_factor = 1.0

        # Dependency factor
        dependencies = quest_data.get("dependencies", [])
        if isinstance(dependencies, str):
            dependencies = [d.strip() for d in dependencies.split(",")]
        if not dependencies:
            score.dependency_factor = 1.2

        score.calculate()
        return score

    def suggest_next_quests(self, count: int = 5) -> HintResult:
        """Suggest next quests to work on.

        Args:
            count: Number of suggestions to return

        Returns:
            HintResult with suggested quests
        """
        result = HintResult()

        # Score all actionable quests
        scored_quests: list[Any] = []
        for quest_id in self.actionable_quests:
            score = self.score_quest(quest_id)
            scored_quests.append(score)

        # Sort by score descending
        scored_quests.sort(key=lambda s: s.final_score, reverse=True)

        # Build result
        result.suggested_quests = scored_quests[:count]

        # Build reasoning
        reasoning_lines = [
            f"📋 Analyzing {len(self.actionable_quests)} actionable quests...",
            f"🚫 {len(self.blocked_quests)} quests are blocked by dependencies",
        ]

        if result.suggested_quests:
            reasoning_lines.append("\n💡 Top Suggestions:")
            for i, score in enumerate(result.suggested_quests, 1):
                quest = self.quests.get(score.quest_id, {})
                status = quest.get("status", "unknown")
                reasoning_lines.append(
                    f"  {i}. [{score.quest_id}] {score.quest_title} (score: {score.final_score:.2f}, status: {status})"
                )
        else:
            reasoning_lines.append("\n⚠️  No actionable quests found")

        result.reasoning = "\n".join(reasoning_lines)
        result.metrics = {
            "actionable_count": len(self.actionable_quests),
            "blocked_count": len(self.blocked_quests),
            "total_quests": len(self.quests),
            "suggestions_count": len(result.suggested_quests),
        }

        return result

    def run(self, count: int = 5) -> HintResult:
        """Run complete hint engine analysis.

        Args:
            count: Number of suggestions to return

        Returns:
            HintResult with suggestions and analysis
        """
        logger.info("\n🧠 Hint Engine Analysis")
        logger.info("=" * 70)

        # Load data
        if not self.load_quests():
            return HintResult(reasoning="Failed to load quests")

        if not self.load_zeta_tracker():
            logger.warning("⚠️  Continuing without ZETA tracker...")

        # Build dependency graph
        self.build_dependency_graph()

        # Categorize quests
        self.categorize_quests()

        # Generate suggestions
        result = self.suggest_next_quests(count)

        # Print results
        logger.info(result.reasoning)
        logger.info("=" * 70)

        return result


def main():
    """Run hint engine analysis."""
    engine = HintEngine()
    result = engine.run(count=5)

    # Save result
    output_path = Path("Reports/hint_engine_suggestions.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "suggestions": [
                    {
                        "quest_id": s.quest_id,
                        "title": s.quest_title,
                        "score": s.final_score,
                        "rationale": s.rationale,
                    }
                    for s in result.suggested_quests
                ],
                "metrics": result.metrics,
                "reasoning": result.reasoning,
            },
            f,
            indent=2,
        )

    logger.info(f"\n✅ Saved suggestions to {output_path}")


if __name__ == "__main__":
    main()
