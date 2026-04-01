#!/usr/bin/env python3
"""Culture Ship Feedback Loop - Learn from Strategic Decisions

This script creates a feedback loop that:
1. Monitors Culture Ship healing history for completed fixes
2. Extracts patterns from successful fix applications
3. Feeds patterns back to evolution_patterns.jsonl
4. Updates quest status when patterns are learned
5. Enables Culture Ship to improve future strategic decisions

Usage:
    python scripts/culture_ship_feedback_loop.py [--analyze-cycle N] [--continuous]
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).parent.parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class CultureShipFeedbackLoop:
    """Extracts learnings from Culture Ship fix applications and feeds them back."""

    def __init__(self):
        """Initialize feedback loop."""
        self.healing_history_path = REPO_ROOT / "state" / "culture_ship_healing_history.json"
        self.evolution_patterns_path = REPO_ROOT / "data" / "knowledge_bases" / "evolution_patterns.jsonl"
        self.quest_log_path = REPO_ROOT / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"

        # Ensure evolution patterns file exists
        self.evolution_patterns_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.evolution_patterns_path.exists():
            self.evolution_patterns_path.write_text("", encoding="utf-8")

    def run_feedback_cycle(self, cycle_index: int | None = None) -> dict[str, Any]:
        """Extract learnings from a specific cycle or latest cycle.

        Args:
            cycle_index: Index of cycle to analyze (None for latest)

        Returns:
            Feedback cycle results
        """
        logger.info("=" * 70)
        logger.info("CULTURE SHIP FEEDBACK LOOP - PATTERN EXTRACTION")
        logger.info("=" * 70)

        if not self.healing_history_path.exists():
            logger.warning(f"Healing history not found: {self.healing_history_path}")
            return {"status": "no_history", "patterns_extracted": 0}

        # Load healing history
        with open(self.healing_history_path, encoding="utf-8") as f:
            history = json.load(f)

        cycles = history.get("cycles", [])
        if not cycles:
            logger.warning("No cycles found in healing history")
            return {"status": "no_cycles", "patterns_extracted": 0}

        # Select cycle to analyze
        if cycle_index is not None:
            if cycle_index >= len(cycles):
                logger.error(f"Cycle {cycle_index} not found (only {len(cycles)} cycles exist)")
                return {"status": "invalid_cycle", "patterns_extracted": 0}
            cycle = cycles[cycle_index]
            logger.info(f"Analyzing cycle {cycle_index} from {cycle.get('timestamp')}")
        else:
            cycle = cycles[-1]
            logger.info(f"Analyzing latest cycle from {cycle.get('timestamp')}")

        # Extract patterns from strategic decisions
        patterns_extracted = []
        decisions = cycle.get("strategic_decisions", [])

        logger.info(f"Processing {len(decisions)} strategic decisions\n")

        for decision in decisions:
            pattern_data = self._extract_pattern_from_decision(decision)
            if pattern_data:
                patterns_extracted.append(pattern_data)
                self._save_pattern(pattern_data)
                logger.info(f"✅ Pattern extracted: {pattern_data['patterns'][0][:60]}...")

        # Update quest statuses
        quests_updated = self._update_quest_statuses(decisions)

        logger.info(f"\n{'=' * 70}")
        logger.info(f"Patterns extracted: {len(patterns_extracted)}")
        logger.info(f"Quests updated: {quests_updated}")
        logger.info(f"{'=' * 70}")

        return {
            "status": "completed",
            "cycle_timestamp": cycle.get("timestamp"),
            "patterns_extracted": len(patterns_extracted),
            "quests_updated": quests_updated,
            "patterns": patterns_extracted,
        }

    def _extract_pattern_from_decision(self, decision: dict[str, Any]) -> dict[str, Any] | None:
        """Extract learning pattern from a strategic decision.

        Args:
            decision: Strategic decision dictionary

        Returns:
            Pattern data for evolution_patterns.jsonl, or None if not applicable
        """
        category = decision.get("category", "unknown")
        priority = decision.get("priority", 0)
        status = decision.get("status", "unknown")
        fixes_applied = decision.get("fixes_applied", 0)

        # Only extract patterns from decisions with fixes applied
        if fixes_applied == 0 and status != "analyzed":
            return None

        # Build pattern based on category
        patterns = []
        tags = []
        xp = 0

        if category == "architecture":
            patterns.append(f"Pattern: Culture Ship strategic integration enables autonomous {category} improvements")
            patterns.append(
                "Learning: Automated strategic analysis identifies integration gaps before they become critical"
            )
            patterns.append("Insight: Self-analysis tools (audit CLIs) accelerate adoption of strategic frameworks")
            tags.append("ARCHITECTURE")
            tags.append("DESIGN_PATTERN")
            xp = 60

        elif category == "correctness":
            patterns.append(f"Pattern: Type safety and linting automation prevent {fixes_applied} classes of bugs")
            patterns.append("Learning: Ruff + Black + Mypy pipeline catches errors before runtime")
            patterns.append("Insight: Automated fix application (--fix flags) reduces manual toil")
            tags.append("TYPE_SAFETY")
            tags.append("BUGFIX")
            xp = 45 if priority >= 8 else 30

        elif category == "efficiency":
            patterns.append("Pattern: Async functions without await create unnecessary event loop overhead")
            patterns.append("Learning: AST analysis can identify 280+ optimization opportunities in seconds")
            patterns.append("Insight: Local LLM processing (Ollama) enables zero-cost code analysis at scale")
            tags.append("EFFICIENCY")
            tags.append("REFACTOR")
            xp = 40

        elif category == "quality":
            patterns.append(f"Pattern: Test infrastructure readiness enables {category} improvements")
            patterns.append("Learning: Pytest collection verifies test suite health before writing new tests")
            patterns.append("Insight: Test coverage analysis guides strategic testing investments")
            tags.append("QUALITY")
            tags.append("DESIGN_PATTERN")
            xp = 35

        # Add priority-based insight
        if priority >= 8:
            patterns.append(f"Meta-insight: Priority {priority}/10 issues deserve automated fix application")
            xp += 15

        # Award XP via unified router (best-effort)
        if xp > 0:
            try:
                from src.system.rpg_inventory import award_xp

                award_xp("ai_coordination", xp, award_game_fn=None)
            except Exception:
                pass

        return {
            "timestamp": datetime.now().isoformat(),
            "commit": "culture_ship_feedback",
            "patterns": patterns,
            "tags": tags,
            "xp": xp,
            "source": "culture_ship_strategic_cycle",
            "decision_category": category,
            "decision_priority": priority,
        }

    def _save_pattern(self, pattern_data: dict[str, Any]) -> None:
        """Save pattern to evolution_patterns.jsonl.

        Args:
            pattern_data: Pattern dictionary to append
        """
        with open(self.evolution_patterns_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(pattern_data) + "\n")

    def _update_quest_statuses(self, decisions: list[dict[str, Any]]) -> int:
        """Update quest statuses based on decision outcomes.

        Args:
            decisions: List of strategic decisions

        Returns:
            Number of quests updated
        """
        if not self.quest_log_path.exists():
            logger.warning(f"Quest log not found: {self.quest_log_path}")
            return 0

        # Load quest log
        quests = []
        with open(self.quest_log_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    quests.append(json.loads(line))

        updated_count = 0

        # Update quests linked to decisions with fixes
        for decision in decisions:
            quest_id = decision.get("quest_id")
            fixes_applied = decision.get("fixes_applied", 0)

            if not quest_id or fixes_applied == 0:
                continue

            for quest in quests:
                if quest.get("quest_id") == quest_id:
                    # Update quest status to reflect fix application
                    if quest.get("status") != "completed":
                        quest["status"] = "in_progress"
                        quest["progress"] = fixes_applied
                        quest["updated_at"] = datetime.now().isoformat()
                        updated_count += 1
                        logger.info(f"   Updated quest {quest_id}: progress = {fixes_applied}")

        # Rewrite quest log with updates
        if updated_count > 0:
            with open(self.quest_log_path, "w", encoding="utf-8") as f:
                for quest in quests:
                    f.write(json.dumps(quest) + "\n")

        return updated_count

    def analyze_learning_history(self) -> dict[str, Any]:
        """Analyze the full evolution patterns history.

        Returns:
            Analysis of learning patterns over time
        """
        logger.info("\n" + "=" * 70)
        logger.info("EVOLUTION PATTERNS ANALYSIS")
        logger.info("=" * 70)

        if not self.evolution_patterns_path.exists():
            logger.warning("No evolution patterns file found")
            return {"status": "no_patterns"}

        patterns = []
        with open(self.evolution_patterns_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    patterns.append(json.loads(line))

        logger.info(f"\nTotal patterns learned: {len(patterns)}")

        # Analyze by tag
        tag_counts: dict[str, int] = {}
        tag_xp: dict[str, int] = {}

        for pattern in patterns:
            for tag in pattern.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
                tag_xp[tag] = tag_xp.get(tag, 0) + pattern.get("xp", 0)

        logger.info("\nPattern Distribution by Tag:")
        for tag in sorted(tag_counts.keys(), key=lambda t: tag_counts[t], reverse=True):
            logger.info(f"  {tag}: {tag_counts[tag]} patterns, {tag_xp[tag]} XP")

        # Analyze recent patterns (last 5)
        logger.info("\nRecent Patterns (last 5):")
        for pattern in patterns[-5:]:
            timestamp = pattern.get("timestamp", "unknown")
            main_pattern = pattern.get("patterns", ["No pattern"])[0]
            xp = pattern.get("xp", 0)
            logger.info(f"  [{timestamp[:10]}] {main_pattern[:60]}... ({xp} XP)")

        total_xp = sum(p.get("xp", 0) for p in patterns)
        logger.info(f"\nTotal XP earned from learning: {total_xp}")

        return {
            "total_patterns": len(patterns),
            "total_xp": total_xp,
            "tag_distribution": tag_counts,
            "tag_xp": tag_xp,
            "recent_patterns": patterns[-5:],
        }


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Culture Ship Feedback Loop - Extract learnings from strategic cycles")
    parser.add_argument(
        "--analyze-cycle",
        type=int,
        help="Analyze specific cycle by index (default: latest)",
    )
    parser.add_argument(
        "--analyze-history",
        action="store_true",
        help="Analyze full evolution patterns history",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format",
    )

    args = parser.parse_args()

    try:
        loop = CultureShipFeedbackLoop()

        if args.analyze_history:
            results = loop.analyze_learning_history()
        else:
            results = loop.run_feedback_cycle(cycle_index=args.analyze_cycle)

        if args.json:
            print(json.dumps(results, indent=2, default=str))
        else:
            print("\n" + "=" * 70)
            print("FEEDBACK LOOP COMPLETE")
            print("=" * 70)
            if "patterns_extracted" in results:
                print(f"Patterns extracted: {results['patterns_extracted']}")
                print(f"Quests updated: {results.get('quests_updated', 0)}")
            print("=" * 70)

        return 0

    except Exception as e:
        logger.error(f"Feedback loop failed: {e}")
        if args.json:
            print(json.dumps({"status": "error", "error": str(e)}, indent=2))
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
