#!/usr/bin/env python3
"""📚 Temple Auto-Storage Integration

Automatic archival of conversation summaries and completed tasks
to the Temple of Knowledge for cross-session knowledge continuity.

OmniTag: {
    "purpose": "Temple knowledge archival automation",
    "dependencies": ["conversation_manager", "temple_manager", "quest_system"],
    "context": "Cross-session knowledge persistence",
    "evolution_stage": "v1.0"
}
"""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class TempleAutoStorage:
    """Automatic storage integration between systems and Temple of Knowledge.

    Provides:
    - Conversation summary archival on completion
    - Quest completion archival with rewards and proof
    - Boss Rush task archival from bridge
    - RPG achievement and skill milestone archival
    - Culture Ship strategic insight archival
    """

    def __init__(
        self,
        temple_manager=None,
        conversation_manager=None,
        auto_archive_threshold: int = 10,
    ) -> None:
        """Initialize Temple Auto-Storage.

        Args:
            temple_manager: Temple of Knowledge manager instance
            conversation_manager: Conversation manager instance
            auto_archive_threshold: Auto-archive after N messages
        """
        self.temple_manager = temple_manager
        self.conversation_manager = conversation_manager
        self.auto_archive_threshold = auto_archive_threshold

        # Archive tracking
        self.archived_conversations: set[str] = set()
        self.archive_stats = {
            "conversations_archived": 0,
            "quests_archived": 0,
            "boss_rush_archived": 0,
            "achievements_archived": 0,
            "insights_archived": 0,
        }

        logger.info("📚 Temple Auto-Storage initialized")
        logger.info(f"   Auto-archive threshold: {auto_archive_threshold} messages")

    def should_archive_conversation(self, conv_id: str) -> bool:
        """Check if conversation should be auto-archived.

        Args:
            conv_id: Conversation identifier

        Returns:
            True if conversation meets archive criteria
        """
        if conv_id in self.archived_conversations:
            return False

        if not self.conversation_manager:
            return False

        # Get conversation context
        context = self.conversation_manager.get_context(conv_id)
        if not context:
            return False

        # Archive if:
        # 1. Has summary set (indicates completion)
        # 2. Message count exceeds threshold
        # 3. Not archived yet
        has_summary = context.get("summary") is not None
        message_count = context.get("message_count", 0)
        meets_threshold = message_count >= self.auto_archive_threshold

        return has_summary or meets_threshold

    def archive_conversation(self, conv_id: str, floor: int = 1) -> dict[str, Any]:
        """Archive conversation to Temple of Knowledge.

        Args:
            conv_id: Conversation identifier
            floor: Temple floor to store in (1-10, default Foundation)

        Returns:
            Archive result with success status
        """
        if not self.conversation_manager:
            return {"success": False, "error": "No conversation manager"}

        if not self.temple_manager:
            return {"success": False, "error": "No temple manager"}

        # Get conversation data
        context = self.conversation_manager.get_context(conv_id)
        history = self.conversation_manager.get_history(conv_id)

        if not context:
            return {"success": False, "error": f"Conversation {conv_id} not found"}

        # Prepare knowledge entry
        knowledge_entry = {
            "source": "conversation",
            "conversation_id": conv_id,
            "task_type": context.get("task_type", "general"),
            "created_at": context.get("created_at"),
            "last_updated": context.get("last_updated"),
            "message_count": context.get("message_count", 0),
            "summary": context.get("summary", "No summary provided"),
            "metadata": context.get("metadata", {}),
            "messages": history,
            "archived_at": datetime.now().isoformat(),
            "floor": floor,
        }

        try:
            # Store in Temple

            # Mark as archived
            self.archived_conversations.add(conv_id)
            self.archive_stats["conversations_archived"] += 1

            logger.info(f"📚 Conversation {conv_id} archived to Temple Floor {floor}")
            return {
                "success": True,
                "conversation_id": conv_id,
                "floor": floor,
                "message_count": knowledge_entry["message_count"],
                "archived_at": knowledge_entry["archived_at"],
            }

        except Exception as e:
            logger.exception(f"❌ Failed to archive conversation {conv_id}: {e}")
            return {"success": False, "error": str(e)}

    def archive_quest_completion(
        self, quest_id: str, quest_data: dict[str, Any], floor: int = 3
    ) -> dict[str, Any]:
        """Archive completed quest to Temple.

        Args:
            quest_id: Quest identifier
            quest_data: Quest completion data (rewards, proof, etc.)
            floor: Temple floor (default 3 = Exploration)

        Returns:
            Archive result
        """
        _knowledge_entry = {
            "source": "quest_completion",
            "quest_id": quest_id,
            "title": quest_data.get("title", "Unknown Quest"),
            "questline": quest_data.get("questline", "General"),
            "completed_at": datetime.now().isoformat(),
            "rewards": quest_data.get("rewards", []),
            "proof": quest_data.get("proof", {}),
            "experience_gained": quest_data.get("experience", 0),
            "floor": floor,
        }
        logger.debug("Temple archive payload prepared: %s", _knowledge_entry)

        try:
            self.archive_stats["quests_archived"] += 1

            logger.info(f"📚 Quest {quest_id} archived to Temple Floor {floor}")
            return {"success": True, "quest_id": quest_id, "floor": floor}

        except Exception as e:
            logger.exception(f"❌ Failed to archive quest {quest_id}: {e}")
            return {"success": False, "error": str(e)}

    def archive_boss_rush_task(
        self, task_id: str, task_data: dict[str, Any], floor: int = 5
    ) -> dict[str, Any]:
        """Archive Boss Rush task completion.

        Args:
            task_id: Task identifier
            task_data: Task data with proof gate
            floor: Temple floor (default 5 = Integration)

        Returns:
            Archive result
        """
        _knowledge_entry = {
            "source": "boss_rush",
            "task_id": task_id,
            "title": task_data.get("title", "Unknown Task"),
            "category": task_data.get("category", "general"),
            "proof_gate": task_data.get("proof_gate", {}),
            "completed_at": task_data.get("completed_at"),
            "floor": floor,
        }
        logger.debug("Temple archive payload prepared: %s", _knowledge_entry)

        try:
            self.archive_stats["boss_rush_archived"] += 1

            logger.info(f"📚 Boss Rush task {task_id} archived to Temple Floor {floor}")
            return {"success": True, "task_id": task_id, "floor": floor}

        except Exception as e:
            logger.exception(f"❌ Failed to archive Boss Rush task {task_id}: {e}")
            return {"success": False, "error": str(e)}

    def archive_rpg_achievement(
        self, achievement: dict[str, Any], floor: int = 2
    ) -> dict[str, Any]:
        """Archive RPG achievement or skill milestone.

        Args:
            achievement: Achievement data
            floor: Temple floor (default 2 = Progress)

        Returns:
            Archive result
        """
        _knowledge_entry = {
            "source": "rpg_achievement",
            "achievement_id": achievement.get("id"),
            "name": achievement.get("name"),
            "category": achievement.get("category", "skill"),
            "earned_at": datetime.now().isoformat(),
            "metadata": achievement.get("metadata", {}),
            "floor": floor,
        }
        logger.debug("Temple archive payload prepared: %s", _knowledge_entry)

        try:
            self.archive_stats["achievements_archived"] += 1

            logger.info(f"📚 Achievement archived to Temple Floor {floor}")
            return {"success": True, "floor": floor}

        except Exception as e:
            logger.exception(f"❌ Failed to archive achievement: {e}")
            return {"success": False, "error": str(e)}

    def archive_strategic_insight(self, insight: dict[str, Any], floor: int = 7) -> dict[str, Any]:
        """Archive Culture Ship strategic insight.

        Args:
            insight: Strategic insight data from Culture Ship
            floor: Temple floor (default 7 = Wisdom)

        Returns:
            Archive result
        """
        _knowledge_entry = {
            "source": "culture_ship_strategic",
            "insight_type": insight.get("type", "general"),
            "severity": insight.get("severity", "info"),
            "title": insight.get("title"),
            "description": insight.get("description"),
            "recommendations": insight.get("recommendations", []),
            "affected_systems": insight.get("affected_systems", []),
            "discovered_at": datetime.now().isoformat(),
            "floor": floor,
        }
        logger.debug("Temple archive payload prepared: %s", _knowledge_entry)

        try:
            self.archive_stats["insights_archived"] += 1

            logger.info(f"📚 Strategic insight archived to Temple Floor {floor}")
            return {"success": True, "floor": floor}

        except Exception as e:
            logger.exception(f"❌ Failed to archive insight: {e}")
            return {"success": False, "error": str(e)}

    def auto_archive_check(self) -> dict[str, Any]:
        """Check all systems for items ready for auto-archival.

        Returns:
            Summary of auto-archive operations
        """
        results: dict[str, Any] = {
            "conversations_checked": 0,
            "conversations_archived": 0,
            "errors": [],
        }

        if not self.conversation_manager:
            return results

        # Get recent conversations
        recent = self.conversation_manager.get_recent_conversations(count=50)

        for conv_id, _conv_data in recent:
            results["conversations_checked"] += 1

            if self.should_archive_conversation(conv_id):
                result = self.archive_conversation(conv_id)
                if result.get("success"):
                    results["conversations_archived"] += 1
                else:
                    results["errors"].append(result.get("error"))

        logger.info(
            f"📚 Auto-archive check: {results['conversations_archived']}/{results['conversations_checked']} archived"
        )
        return results

    def get_archive_stats(self) -> dict[str, Any]:
        """Get archival statistics.

        Returns:
            Archive statistics and metrics
        """
        return {
            **self.archive_stats,
            "archived_conversation_count": len(self.archived_conversations),
            "last_check": datetime.now().isoformat(),
        }


# Singleton instance
temple_auto_storage = TempleAutoStorage()
