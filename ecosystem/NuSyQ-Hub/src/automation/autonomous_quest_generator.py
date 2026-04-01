#!/usr/bin/env python3
"""Autonomous Quest Generator - Converts PUs to Agent Quests.

This bridges the gap between:
1. AutonomousMonitor (detects issues, creates PUs)
2. UnifiedPUQueue (manages PUs)
3. Unified Agent Ecosystem (quest system)

**THE MISSING LINK**: Auto-converts PUs → Quests → Assigns to Agents
"""

import asyncio
import contextlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from src.agents.adaptive_timeout_manager import get_timeout_manager
from src.agents.unified_agent_ecosystem import get_ecosystem
from src.automation.unified_pu_queue import PU, UnifiedPUQueue

logger = logging.getLogger(__name__)


class AutonomousQuestGenerator:
    """Automatically converts Processing Units (PUs) into Agent Quests.

    THIS IS THE SELF-CULTIVATION ENGINE!

    Workflow:
    1. Monitor detects issue → Creates PU
    2. PU enters queue
    3. THIS SYSTEM converts PU → Quest
    4. Quest auto-assigned to capable agent
    5. Agent executes quest (using AI tools)
    6. Completion awards XP + Knowledge
    7. System improves itself!
    """

    def __init__(self) -> None:
        """Initialize AutonomousQuestGenerator."""
        self.ecosystem = get_ecosystem()
        self.pu_queue = UnifiedPUQueue()
        self.timeout_manager = get_timeout_manager()

        # PU type → Agent mapping
        self.pu_to_agent_mapping = {
            "RefactorPU": "copilot",  # Copilot handles code refactoring
            "DocPU": "claude",  # Claude writes documentation
            "FeaturePU": "chatdev",  # ChatDev builds features
            "BugFixPU": "copilot",  # Copilot fixes bugs
            "AnalysisPU": "consciousness",  # Consciousness analyzes
            "TestPU": "chatdev",  # ChatDev creates tests
            "OptimizationPU": "culture_ship",  # Culture Ship optimizes
        }

        # PU priority → XP reward mapping
        self.priority_to_xp = {"critical": 100, "high": 50, "medium": 25, "low": 10}

        # PU priority → Complexity mapping for adaptive timeouts
        self.priority_to_complexity = {
            "critical": "very_complex",  # Critical issues are usually complex
            "high": "complex",
            "medium": "medium",
            "low": "simple",
        }

        # PU type → Task type mapping for timeout manager
        self.pu_to_task_type = {
            "RefactorPU": "code_refactoring",
            "DocPU": "documentation",
            "FeaturePU": "feature_development",
            "BugFixPU": "bug_fixing",
            "AnalysisPU": "code_analysis",
            "TestPU": "test_generation",
            "OptimizationPU": "optimization",
        }

        logger.info("🤖 Autonomous Quest Generator initialized with adaptive timeout support")

    def convert_pu_to_quest(self, pu: PU) -> dict[str, Any]:
        """Convert a PU into a Quest.

        Args:
            pu: Processing Unit to convert

        Returns:
            Quest creation result

        """
        # Determine agent
        agent_name = self.pu_to_agent_mapping.get(pu.type, "copilot")

        # Determine XP reward based on priority
        xp_reward = self.priority_to_xp.get(pu.priority, 10)

        # Determine questline based on PU type
        questline_mapping = {
            "RefactorPU": "code_quality",
            "DocPU": "documentation",
            "FeaturePU": "features",
            "BugFixPU": "bug_fixes",
            "AnalysisPU": "analysis",
            "TestPU": "testing",
            "OptimizationPU": "performance",
        }
        questline = questline_mapping.get(pu.type, "maintenance")

        # Extract skill from PU type
        skill_mapping = {
            "RefactorPU": "refactoring",
            "DocPU": "documentation",
            "FeaturePU": "development",
            "BugFixPU": "debugging",
            "AnalysisPU": "analysis",
            "TestPU": "testing",
            "OptimizationPU": "optimization",
        }
        skill_reward = skill_mapping.get(pu.type, "general")

        # Calculate adaptive timeout for this quest
        complexity = self.priority_to_complexity.get(pu.priority, "medium")
        task_type = self.pu_to_task_type.get(pu.type, "general_task")

        # Get recommended timeout for this quest
        estimated_timeout = self.timeout_manager.get_timeout(
            model=agent_name, task_type=task_type, complexity=complexity
        )

        logger.info(f"⏱️ Estimated timeout for {pu.type} ({complexity}): {estimated_timeout:.0f}s")

        # Build quest description with timeout metadata
        proof_list = ", ".join(pu.proof_criteria)
        quest_description = (
            f"{pu.description}\n\n"
            f"Source: {pu.source_repo} | Priority: {pu.priority}\n"
            f"Proof Criteria: {proof_list}\n\n"
            f"Complexity: {complexity} | Estimated Time: {estimated_timeout:.0f}s"
        )

        # Create quest with timeout metadata
        result: dict[str, Any] = dict(
            self.ecosystem.create_quest_for_agent(
                title=pu.title,
                description=quest_description,
                agent_name=agent_name,
                questline=questline,
                xp_reward=xp_reward,
                skill_reward=skill_reward,
                tags=[pu.type, pu.priority, pu.source_repo, complexity],
            )
        )

        if result.get("success"):
            logger.info("✅ PU→Quest: '%s' → %s (%s XP)", pu.title, agent_name, xp_reward)

            # Update PU status
            pu.status = "approved"
            pu.assigned_agents = [agent_name]
            pu.metadata["quest_id"] = result["quest"]["id"]
            pu.metadata["converted_at"] = datetime.now().isoformat()

        return result

    async def process_pending_pus(self) -> dict[str, Any]:
        """Process all pending PUs and convert them to quests.

        Returns:
            Processing summary

        """
        logger.info("\n" + "=" * 60)
        logger.info("🔄 PROCESSING PENDING PUs")
        logger.info("=" * 60)

        pending_pus = [pu for pu in self.pu_queue.queue if pu.status == "queued"]

        if not pending_pus:
            logger.info("✅ No pending PUs found")
            return {"success": True, "processed": 0, "created": 0, "failed": 0}

        logger.info("📋 Found %s pending PUs\n", len(pending_pus))

        created = 0
        failed = 0

        for pu in pending_pus:
            logger.info("Processing: %s (%s, %s)", pu.title, pu.type, pu.priority)

            try:
                result = self.convert_pu_to_quest(pu)

                if result.get("success"):
                    created += 1
                else:
                    failed += 1
                    logger.error(f"  ❌ Failed: {result.get('error', 'Unknown error')}")

            except Exception as e:
                failed += 1
                logger.error(f"  ❌ Error: {e}", exc_info=True)

        # Save updated queue
        self.pu_queue._save_queue()

        logger.info("\n" + "=" * 60)
        logger.info("📊 SUMMARY")
        logger.info("=" * 60)
        logger.info("  Processed: %s", len(pending_pus))
        logger.info("  Created Quests: %s", created)
        logger.info("  Failed: %s", failed)

        return {
            "success": True,
            "processed": len(pending_pus),
            "created": created,
            "failed": failed,
        }

    async def auto_generate_system_improvement_quests(self) -> dict[str, Any]:
        """Automatically generate quests for system self-improvement.

        This scans the codebase for common issues and creates quests.

        Returns:
            Generation summary

        """
        logger.info("\n" + "=" * 60)
        logger.info("🌱 AUTO-GENERATING SYSTEM IMPROVEMENT QUESTS")
        logger.info("=" * 60)

        # Define self-improvement quests
        improvement_quests: list[dict[str, Any]] = [
            {
                "title": "Fix Remaining Import Errors",
                "description": "Resolve all remaining import-related errors to achieve 100% clean imports",
                "agent": "copilot",
                "questline": "code_quality",
                "xp": 30,
                "skill": "debugging",
                "tags": ["imports", "cleanup", "quality"],
            },
            {
                "title": "Document Quest System API",
                "description": "Create comprehensive API documentation for the quest system integration",
                "agent": "claude",
                "questline": "documentation",
                "xp": 25,
                "skill": "documentation",
                "tags": ["docs", "api", "quest-system"],
            },
            {
                "title": "Implement Floor 2: Archives",
                "description": "Build the Archives floor (Floor 2) of the Temple of Knowledge with historical quest tracking",
                "agent": "chatdev",
                "questline": "features",
                "xp": 75,
                "skill": "development",
                "tags": ["temple", "feature", "consciousness"],
            },
            {
                "title": "Create Auto-Healing Tests",
                "description": "Develop tests that verify the autonomous quest generation and execution workflow",
                "agent": "chatdev",
                "questline": "testing",
                "xp": 50,
                "skill": "testing",
                "tags": ["tests", "automation", "self-healing"],
            },
            {
                "title": "Optimize Agent Communication Latency",
                "description": "Profile and optimize the agent messaging system for faster communication",
                "agent": "culture_ship",
                "questline": "performance",
                "xp": 40,
                "skill": "optimization",
                "tags": ["performance", "agents", "messaging"],
            },
        ]

        created = 0
        failed = 0

        for quest_spec in improvement_quests:
            try:
                title = str(quest_spec.get("title", "Untitled Quest"))
                description = str(quest_spec.get("description", ""))
                agent_name = str(quest_spec.get("agent", "ollama"))
                questline = str(quest_spec.get("questline", "development"))
                xp_reward = int(quest_spec.get("xp", 0))
                skill_reward = quest_spec.get("skill")
                tags = quest_spec.get("tags", [])
                tags_list = [str(tag) for tag in tags] if isinstance(tags, list) else []

                result = self.ecosystem.create_quest_for_agent(
                    title=title,
                    description=description,
                    agent_name=agent_name,
                    questline=questline,
                    xp_reward=xp_reward,
                    skill_reward=str(skill_reward) if skill_reward is not None else None,
                    tags=tags_list,
                )

                if result.get("success"):
                    created += 1
                    logger.info(
                        "  ✅ Created: %s → %s",
                        quest_spec["title"],
                        quest_spec["agent"],
                    )
                else:
                    failed += 1
                    logger.error("  ❌ Failed: %s", quest_spec["title"])

            except Exception as e:
                failed += 1
                logger.exception("  ❌ Error creating quest: %s", e)

        logger.info("\n" + "=" * 60)
        logger.info("📊 AUTO-GENERATION SUMMARY")
        logger.info("=" * 60)
        logger.info("  Total Quests: %s", len(improvement_quests))
        logger.info("  Created: %s", created)
        logger.info("  Failed: %s", failed)

        return {
            "success": True,
            "total": len(improvement_quests),
            "created": created,
            "failed": failed,
        }

    def _collect_advanced_ai_readiness(self) -> dict[str, Any]:
        """Read advanced AI readiness from ai_status or direct health audit."""
        ai_status_path = Path("state/reports/ai_status_latest.json")
        if ai_status_path.exists():
            with contextlib.suppress(Exception):
                payload = json.loads(ai_status_path.read_text(encoding="utf-8"))
                capability_intel = payload.get("capability_intelligence", {})
                readiness = capability_intel.get("advanced_ai_readiness", {})
                if isinstance(readiness, dict) and readiness.get("capabilities"):
                    return readiness

        from src.diagnostics.system_health_assessor import \
            SystemHealthAssessment

        assessor = SystemHealthAssessment()
        assessor.repo_root = Path.cwd()
        return {
            "status": "partial",
            "capabilities": assessor._audit_advanced_ai_capabilities(),
        }

    def _quest_exists(self, title: str) -> bool:
        """Detect duplicate active/pending quests by title."""
        for quest in self.ecosystem.quest_engine.quests.values():
            if quest.title == title and quest.status in {"pending", "active", "blocked"}:
                return True
        return False

    async def generate_advanced_ai_capability_quests(self) -> dict[str, Any]:
        """Convert missing advanced-AI readiness gaps into tracked quests."""
        readiness = self._collect_advanced_ai_readiness()
        capabilities = readiness.get("capabilities", {})
        if not isinstance(capabilities, dict):
            return {
                "success": False,
                "created": 0,
                "skipped": 0,
                "failed": 0,
                "error": "invalid_readiness",
            }

        questline = "advanced_ai"
        agent_by_capability = {
            "causal_inference": "consciousness",
            "federated_learning": "culture_ship",
            "graph_learning": "chatdev",
        }
        descriptions = {
            "causal_inference": (
                "Stand up a causal inference execution surface for root-cause reasoning across "
                "failures, telemetry, and orchestration decisions."
            ),
            "federated_learning": (
                "Design and implement a federated learning substrate for cross-repo intelligence "
                "without centralizing sensitive state."
            ),
            "graph_learning": (
                "Create a graph-learning or GNN execution surface for dependency analysis, "
                "impact prediction, and healing workflows."
            ),
        }

        created = 0
        skipped = 0
        failed = 0
        quest_ids: list[str] = []

        for capability, details in capabilities.items():
            if not isinstance(details, dict) or details.get("status") != "missing":
                continue

            title = f"Implement {capability.replace('_', ' ').title()} capability"
            if self._quest_exists(title):
                skipped += 1
                continue

            result = self.ecosystem.create_quest_for_agent(
                title=title,
                description=descriptions.get(
                    capability,
                    f"Implement the missing advanced AI capability: {capability}.",
                ),
                agent_name=agent_by_capability.get(capability, "copilot"),
                questline=questline,
                xp_reward=75,
                skill_reward="research",
                tags=["advanced_ai", capability, "readiness_gap"],
            )

            if result.get("success"):
                created += 1
                quest_ids.append(result["quest"]["id"])
            else:
                failed += 1

        return {
            "success": failed == 0,
            "created": created,
            "skipped": skipped,
            "failed": failed,
            "quest_ids": quest_ids,
        }

    async def start_autonomous_loop(self, interval: int = 300) -> None:
        """Start continuous autonomous quest generation loop.

        Args:
            interval: Seconds between PU processing cycles (default: 300 = 5 min)

        """
        logger.info("\n" + "=" * 60)
        logger.info("🤖 STARTING AUTONOMOUS QUEST GENERATION LOOP")
        logger.info("=" * 60)
        logger.info("  Interval: %ss (%.1f minutes)", interval, interval / 60)
        logger.info("  Press Ctrl+C to stop\n")

        try:
            while True:
                # Process pending PUs
                await self.process_pending_pus()

                # Wait for next cycle
                logger.info("\n⏰ Waiting %ss for next cycle...", interval)
                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            logger.info("\n\n🛑 Autonomous loop stopped by user")
        except Exception as e:
            logger.error(f"\n\n❌ Autonomous loop error: {e}", exc_info=True)


async def main() -> None:
    """Demo the autonomous quest generator."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

    generator = AutonomousQuestGenerator()

    # Process any pending PUs
    await generator.process_pending_pus()

    # Auto-generate some improvement quests
    await generator.auto_generate_system_improvement_quests()

    # Show quest board
    logger.info("\n" + "=" * 60)
    logger.info("📋 CURRENT QUEST BOARD")
    logger.info("=" * 60)

    summary = generator.ecosystem.get_party_quest_summary()
    logger.info("  Total Quests: %s", summary["total_quests"])
    logger.info("  Pending: %s", summary["quests_by_status"]["pending"])
    logger.info("  Active: %s", summary["quests_by_status"]["active"])
    logger.info("  Complete: %s", summary["quests_by_status"]["complete"])


if __name__ == "__main__":
    asyncio.run(main())
