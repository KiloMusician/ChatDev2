#!/usr/bin/env python3
"""Quest Replay Engine - Analyze historical quests and extract learning patterns.

This module replays historical quest logs and session logs to identify patterns,
success factors, and recommendations for future autonomous cycles.

Learning outputs:
- Pattern detection (common successful sequences)
- Failure analysis (what causes item failures)
- Time trends (cycle time improvement over time)
- Recommendation engine (suggest next items based on history)
"""

import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class QuestReplayEngine:
    """Replays and learns from historical quest logs."""

    def __init__(self, repo_root: Path | None = None) -> None:
        """Initialize quest replay engine.

        Args:
            repo_root: Repository root (defaults to NuSyQ-Hub location)
        """
        self.repo_root = repo_root or Path(__file__).parent.parent.parent
        self.quest_log_path = self.repo_root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        self.session_logs_dir = self.repo_root / "docs" / "Agent-Sessions"
        self.work_queue_path = self.repo_root / "docs" / "Work-Queue" / "WORK_QUEUE.json"
        self.learning_dir = self.repo_root / "docs" / "Learning"
        self.learning_dir.mkdir(parents=True, exist_ok=True)
        logger.info("🔄 Quest Replay Engine initialized")

    async def replay_recent_quests(self, limit: int = 5) -> dict[str, Any]:
        """Replay recent quest entries and extract learning insights.

        Args:
            limit: Number of recent quests to replay

        Returns:
            Learning report with patterns and recommendations
        """
        logger.info(f"🔄 Replaying last {limit} quests...")

        try:
            # Load recent quest entries
            quests = self._load_recent_quests(limit)

            if not quests:
                logger.info("Info: No quests to replay")
                return {
                    "status": "no_quests",
                    "message": "No quest data available for replay",
                }

            # Analyze patterns
            patterns = self._analyze_patterns(quests)
            success_factors = self._identify_success_factors(quests)
            failure_factors = self._identify_failure_factors(quests)

            # Generate recommendations
            recommendations = self._generate_learning_recommendations(
                patterns, success_factors, failure_factors
            )

            # Generate learning report
            report = {
                "status": "success",
                "quests_analyzed": len(quests),
                "patterns": patterns,
                "success_factors": success_factors,
                "failure_factors": failure_factors,
                "recommendations": recommendations,
                "timestamp": datetime.now().isoformat(),
            }

            # Save learning report
            report_path = (
                self.learning_dir
                / f"learning_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)

            logger.info(f"✅ Learning report saved: {report_path}")
            return report

        except Exception as e:
            logger.error(f"❌ Quest replay failed: {e}")
            return {"status": "error", "error": str(e)}

    async def analyze_work_queue_history(self) -> dict[str, Any]:
        """Analyze work queue completion history."""
        logger.info("📋 Analyzing work queue history...")

        try:
            if not self.work_queue_path.exists():
                return {"status": "no_data", "message": "Work queue not found"}

            with open(self.work_queue_path, encoding="utf-8") as f:
                queue_data = json.load(f)

            items = queue_data.get("items", [])

            # Analyze completion patterns
            completed_items = [i for i in items if i.get("status") == "completed"]
            failed_items = [i for i in items if i.get("status") == "failed"]

            # Group by effort level
            effort_stats: defaultdict[str, dict[str, int]] = defaultdict(
                lambda: {"completed": 0, "failed": 0, "total": 0}
            )

            for item in items:
                effort = item.get("effort", "unknown")
                effort_stats[effort]["total"] += 1

                if item.get("status") == "completed":
                    effort_stats[effort]["completed"] += 1
                elif item.get("status") == "failed":
                    effort_stats[effort]["failed"] += 1

            # Calculate success rates by effort
            effort_analysis = {}
            for effort, stats in effort_stats.items():
                if stats["total"] > 0:
                    success_rate = (stats["completed"] / stats["total"]) * 100
                    effort_analysis[effort] = {
                        "total": stats["total"],
                        "completed": stats["completed"],
                        "failed": stats["failed"],
                        "success_rate": round(success_rate, 1),
                    }

            return {
                "status": "success",
                "total_items": len(items),
                "completed": len(completed_items),
                "failed": len(failed_items),
                "overall_success_rate": (
                    round((len(completed_items) / len(items)) * 100, 1) if items else 0
                ),
                "effort_analysis": effort_analysis,
            }

        except Exception as e:
            logger.error(f"Failed to analyze work queue history: {e}")
            return {"status": "error", "error": str(e)}

    def _load_recent_quests(self, limit: int = 5) -> list[dict[str, Any]]:
        """Load recent quest entries from quest log."""
        try:
            if not self.quest_log_path.exists():
                return []

            quests = []
            with open(self.quest_log_path, encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get("task_type") == "cultivation_intent":
                            quests.append(entry)
                    except json.JSONDecodeError:
                        continue

            # Return most recent entries
            return quests[-limit:] if len(quests) > limit else quests

        except Exception as e:
            logger.error(f"Failed to load quests: {e}")
            return []

    def _analyze_patterns(self, quests: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze patterns in quest data."""
        logger.info("🔍 Analyzing quest patterns...")

        patterns: dict[str, Any] = {
            "intent_type_frequency": defaultdict(int),
            "system_states": [],
            "temporal_patterns": [],
        }

        intent_types: defaultdict[str, int] = defaultdict(int)

        for quest in quests:
            intent_type = quest.get("intent_type", "unknown")
            intent_types[intent_type] += 1

            patterns["system_states"].append(
                {
                    "broken_files": quest.get("state", {}).get("broken_files", 0),
                    "working_files": quest.get("state", {}).get("working_files", 0),
                    "timestamp": quest.get("timestamp", ""),
                }
            )

        patterns["intent_type_frequency"] = dict(intent_types)

        return patterns

    def _identify_success_factors(self, quests: list[dict[str, Any]]) -> list[str]:
        """Identify factors that contribute to successful quests."""
        success_factors = []

        # Analyze quest states
        successful_states = []
        for quest in quests:
            if quest.get("status") == "completed":
                state = quest.get("state", {})
                successful_states.append(state)

        if successful_states:
            # Average successful state
            avg_broken = sum(s.get("broken_files", 0) for s in successful_states) / len(
                successful_states
            )
            avg_working = sum(s.get("working_files", 0) for s in successful_states) / len(
                successful_states
            )

            success_factors.append(f"Successful quests average {avg_working:.0f} working files")

            if avg_broken < 1:
                success_factors.append("✅ Low broken file count correlates with success")

        # Check for patterns in successful quests
        actions_in_successful: defaultdict[str, int] = defaultdict(int)
        for quest in quests:
            if quest.get("status") == "completed":
                actions = quest.get("actions_that_helped", [])
                for action in actions:
                    actions_in_successful[action] += 1

        for action, count in sorted(
            actions_in_successful.items(), key=lambda x: x[1], reverse=True
        )[:3]:
            if count > 0:
                success_factors.append(
                    f"✅ Action '{action}' appears in successful quests ({count}x)"
                )

        return (
            success_factors if success_factors else ["No specific success patterns identified yet"]
        )

    def _identify_failure_factors(self, quests: list[dict[str, Any]]) -> list[str]:
        """Identify factors that contribute to failed quests."""
        failure_factors = []

        # Analyze quest states
        failed_states = []
        for quest in quests:
            if quest.get("status") == "failed":
                state = quest.get("state", {})
                failed_states.append(state)

        if failed_states:
            # Average failed state
            avg_broken = sum(s.get("broken_files", 0) for s in failed_states) / len(failed_states)

            failure_factors.append(f"Failed quests average {avg_broken:.0f} broken files")

            if avg_broken > 5:
                failure_factors.append("⚠️ High broken file count causes quest failures")

        return (
            failure_factors if failure_factors else ["No specific failure patterns identified yet"]
        )

    def _generate_learning_recommendations(
        self,
        patterns: dict[str, Any],
        success_factors: list[str],
        failure_factors: list[str],
    ) -> list[str]:
        """Generate recommendations based on learned patterns."""
        recommendations = []

        # Intent type recommendations
        intent_freq = patterns.get("intent_type_frequency", {})
        if intent_freq:
            most_common = max(intent_freq.items(), key=lambda x: x[1])[0]
            recommendations.append(
                f"📌 Most common intent type: '{most_common}' - optimize for this case"
            )

        # System state recommendations
        states = patterns.get("system_states", [])
        if states:
            avg_working = sum(s.get("working_files", 0) for s in states) / len(states)
            avg_broken = sum(s.get("broken_files", 0) for s in states) / len(states)

            recommendations.append(f"✅ Successful quests average {avg_working:.0f} working files")
            if avg_broken > 0:
                recommendations.append(
                    "🏥 Run heal action regularly to keep broken files near zero"
                )

        # Success-based recommendations
        recommendations.extend([f"✅ {factor}" for factor in success_factors[:2]])

        # Failure-based recommendations
        if failure_factors and "High broken file count" in failure_factors[0]:
            recommendations.append("🔧 Prioritize heal cycles to reduce failures")

        if not recommendations:
            recommendations.append(
                "✅ System is learning - continue autonomous cycles to gather more data"
            )

        return recommendations

    async def predict_next_items(self, count: int = 3) -> dict[str, Any]:
        """Predict next good work items based on history.

        Args:
            count: Number of recommendations to generate

        Returns:
            List of predicted next items with confidence scores
        """
        logger.info(f"🔮 Predicting next {count} work items...")

        try:
            # Analyze history
            history = await self.analyze_work_queue_history()

            if history.get("status") != "success":
                return {
                    "status": "no_data",
                    "message": "Unable to analyze history for prediction",
                }

            # Load current work queue
            if not self.work_queue_path.exists():
                return {"status": "no_queue"}

            with open(self.work_queue_path, encoding="utf-8") as f:
                queue_data = json.load(f)

            items = queue_data.get("items", [])

            # Score items based on history
            effort_rates = history.get("effort_analysis", {})

            scored_items = []
            for item in items:
                if item.get("status") == "queued":
                    effort = item.get("effort", "normal")
                    success_rate = effort_rates.get(effort, {}).get("success_rate", 50)

                    # Confidence = success_rate * (1 - risk_factor)
                    risk_factor = {"low": 0.1, "medium": 0.3, "high": 0.5}.get(
                        item.get("risk", "medium"), 0.3
                    )
                    confidence = (success_rate / 100) * (1 - risk_factor)

                    scored_items.append(
                        {
                            "id": item.get("id"),
                            "title": item.get("title"),
                            "confidence": round(confidence, 2),
                            "estimated_success_rate": round(success_rate, 1),
                            "effort": effort,
                            "risk": item.get("risk", "medium"),
                        }
                    )

            # Sort by confidence
            scored_items.sort(key=lambda x: x["confidence"], reverse=True)

            predictions = scored_items[:count]

            return {
                "status": "success",
                "predictions": predictions,
                "basis": "Historical success rates by effort level",
            }

        except Exception as e:
            logger.error(f"Failed to predict next items: {e}")
            return {"status": "error", "error": str(e)}


if __name__ == "__main__":

    async def main():
        engine = QuestReplayEngine()

        # Replay recent quests
        replay_result = await engine.replay_recent_quests(limit=5)
        logger.info("📖 Replay Result:")
        logger.info(json.dumps(replay_result, indent=2))

        logger.info("\n" + "=" * 50 + "\n")

        # Analyze work queue history
        history = await engine.analyze_work_queue_history()
        logger.info("📊 Work Queue History:")
        logger.info(json.dumps(history, indent=2))

        logger.info("\n" + "=" * 50 + "\n")

        # Predict next items
        predictions = await engine.predict_next_items(count=3)
        logger.info("🔮 Predictions:")
        logger.info(json.dumps(predictions, indent=2))

    asyncio.run(main())
