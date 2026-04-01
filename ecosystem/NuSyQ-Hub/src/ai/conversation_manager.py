"""Simple conversation management utilities.

This module intentionally keeps the feature set minimal so it can be used by
lightweight components that only need basic conversation state tracking. The
manager stores conversations in memory and can optionally persist them to disk
using a JSON file.

OmniTag: {
    "purpose": "Cross-session conversation persistence and context management",
    "dependencies": ["json", "pathlib", "datetime"],
    "context": "Conversation state, message history, task context, memory recall",
    "evolution_stage": "v2.0.enhanced-context-persistence"
}
MegaTag: {
    "type": "ConversationPersistenceManager",
    "integration_points": ["ai_coordinator", "consciousness_bridge", "context_monitor"],
    "related_tags": ["Zeta04", "ContextPersistence", "MemoryRecall", "TaskAwareness"]
}
RSHTS: ⟨CONVERSATION⟩↔⟨CONTEXT⟩→⟨MEMORY⟩
"""

from __future__ import annotations

import importlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


_analytics_module: Any | None
try:
    _analytics_module = importlib.import_module("src.analytics.model_selection_analytics")
except ImportError:
    _analytics_module = None

_ModelSelectionAnalytics: Any | None = (
    getattr(_analytics_module, "ModelSelectionAnalytics", None) if _analytics_module else None
)


class ConversationManager:
    """In-memory conversation store with optional persistence and task-aware context."""

    def __init__(self, storage_path: str | Path = "conversations.json") -> None:
        """Initialise the manager and load persisted conversations if present."""
        self.storage_path = Path(storage_path)
        self.conversations: dict[str, dict[str, Any]] = {}
        self.context_cache: dict[str, dict[str, Any]] = {}

        if self.storage_path.exists():
            self.load()

    def create_conversation(
        self,
        conversation_id: str,
        task_type: str = "general",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Create a new empty conversation with task type awareness.

        Args:
            conversation_id: Unique identifier for conversation
            task_type: Type of task (coding, general, creative, analysis)
            metadata: Additional context metadata
        """
        self.conversations[conversation_id] = {
            "messages": [],
            "context": metadata or {},
            "task_type": task_type,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "summary": None,
        }

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a message to a conversation, creating it if necessary.

        Args:
            conversation_id: Conversation identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional message metadata
        """
        if conversation_id not in self.conversations:
            self.create_conversation(conversation_id)

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        if metadata:
            message.update(metadata)

        self.conversations[conversation_id]["messages"].append(message)
        self.conversations[conversation_id]["last_updated"] = datetime.now().isoformat()
        self.save()

        # Check if conversation should be archived to Temple
        self._check_temple_auto_archive(conversation_id)
        self._record_model_selection_metrics(conversation_id, message, metadata or {})
        self._rebuild_context_cache(conversation_id)

    def get_history(self, conversation_id: str, limit: int | None = None) -> list[dict[str, Any]]:
        """Return message history for a conversation.

        Args:
            conversation_id: Conversation identifier
            limit: Maximum number of messages to return (most recent)

        Returns:
            List of message dictionaries
        """
        messages: list[dict[str, Any]] = self.conversations.get(conversation_id, {}).get(
            "messages", []
        )
        if limit and len(messages) > limit:
            return messages[-limit:]
        return messages

    def get_context(self, conversation_id: str) -> dict[str, Any]:
        """Get conversation context including task type and metadata.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Dictionary containing context information
        """
        conv = self.conversations.get(conversation_id, {})
        return {
            "task_type": conv.get("task_type", "general"),
            "created_at": conv.get("created_at"),
            "last_updated": conv.get("last_updated"),
            "message_count": len(conv.get("messages", [])),
            "metadata": conv.get("context", {}),
            "summary": conv.get("summary"),
        }

    def set_conversation_summary(self, conversation_id: str, summary: str) -> None:
        """Set a summary of the conversation for quick recall.

        Args:
            conversation_id: Conversation identifier
            summary: Summary text
        """
        if conversation_id in self.conversations:
            self.conversations[conversation_id]["summary"] = summary
            self.conversations[conversation_id]["last_updated"] = datetime.now().isoformat()
            self.save()

    def get_recent_conversations(self, count: int = 5) -> list[tuple[str, dict[str, Any]]]:
        """Get most recent conversations sorted by last update.

        Args:
            count: Number of conversations to return

        Returns:
            List of (conversation_id, context) tuples
        """
        sorted_convs = sorted(
            self.conversations.items(),
            key=lambda x: x[1].get("last_updated", ""),
            reverse=True,
        )
        return [(cid, self.get_context(cid)) for cid, _ in sorted_convs[:count]]

    def save(self) -> None:
        """Persist all conversations to ``storage_path``."""
        with self.storage_path.open("w", encoding="utf-8") as f:
            json.dump(self.conversations, f, indent=2)

    def load(self) -> None:
        """Load conversation data from ``storage_path``."""
        with self.storage_path.open("r", encoding="utf-8") as f:
            self.conversations = json.load(f)

    def _check_temple_auto_archive(self, conversation_id: str) -> None:
        """Check if conversation should be auto-archived to Temple.

        Args:
            conversation_id: Conversation to check
        """
        try:
            from src.integration.temple_auto_storage import temple_auto_storage
        except (ImportError, FileNotFoundError):
            # Graceful fallback if Temple not available
            return

        try:
            if temple_auto_storage.should_archive_conversation(conversation_id):
                result = temple_auto_storage.archive_conversation(conversation_id, floor=1)
                if result.get("success") and conversation_id in self.conversations:
                    # Mark conversation as archived
                    self.conversations[conversation_id]["archived_to_temple"] = True
                    self.conversations[conversation_id]["archive_timestamp"] = result.get(
                        "timestamp"
                    )
        except (FileNotFoundError, RuntimeError):
            # Graceful fallback if Temple operation fails
            logger.debug("Suppressed FileNotFoundError/RuntimeError", exc_info=True)

    def _rebuild_context_cache(self, conversation_id: str) -> None:
        """Rebuild cached context analytics for quick retrieval."""
        conversation = self.conversations.get(conversation_id, {})
        messages = conversation.get("messages", [])
        summary = conversation.get("summary")
        self.context_cache[conversation_id] = {
            "message_count": len(messages),
            "last_updated": conversation.get("last_updated"),
            "task_type": conversation.get("task_type", "general"),
            "summary": summary,
            "recent_roles": list({msg.get("role") for msg in messages[-5:]}),
        }

    def _record_model_selection_metrics(
        self,
        conversation_id: str,
        message: dict[str, Any],
        metadata: dict[str, Any],
    ) -> None:
        """Send lightweight telemetry into the model selection analytics engine."""
        analytics = _get_model_selection_analytics()
        if not analytics:
            return

        conversation = self.conversations.get(conversation_id, {})
        task_type = conversation.get("task_type", "general")
        model_name = metadata.get("model_name") or metadata.get("model") or "conversation_manager"
        response_time = float(metadata.get("response_time", 0.0))
        chars = len(message.get("content", "")) if message.get("content") else 0
        token_rate = float(metadata.get("token_rate") or (chars / max(response_time, 0.125)))
        accuracy = float(metadata.get("accuracy_score", 1.0))
        satisfaction = float(metadata.get("user_satisfaction", 0.9))
        memory = float(metadata.get("memory_efficiency", 0.95))

        try:
            analytics.record_model_performance(
                model_name=model_name,
                task_type=task_type,
                response_time=max(response_time, 0.001),
                token_rate=token_rate,
                accuracy_score=accuracy,
                user_satisfaction=satisfaction,
                memory_efficiency=memory,
            )
        except Exception:  # pragma: no cover - telemetry best-effort
            logging.getLogger(__name__).warning(
                "Telemetry capture failed for conversation %s", conversation_id
            )


_model_selection_analytics: Any | None = None


def _get_model_selection_analytics() -> Any | None:
    global _model_selection_analytics
    if _model_selection_analytics is None and _ModelSelectionAnalytics is not None:
        try:
            _model_selection_analytics = _ModelSelectionAnalytics()
        except Exception as exc:  # pragma: no cover - best-effort telemetry
            logging.getLogger(__name__).warning(
                "Unable to initialize ModelSelectionAnalytics: %s", exc
            )
    return _model_selection_analytics


conversation_manager = ConversationManager()


class ContextualMemoryRecall:
    """Implements context-aware memory recall for conversation continuity.

    Provides semantic similarity-based retrieval of relevant context from
    previous conversations and exchanges within the same conversation.
    """

    def __init__(self, manager: ConversationManager | None = None) -> None:
        """Initialize memory recall system.

        Args:
            manager: ConversationManager instance to use for context
        """
        self.manager = manager or conversation_manager
        self.semantic_anchors: dict[str, list[str]] = {}

    def extract_semantic_anchors(self, content: str) -> list[str]:
        """Extract key semantic anchors from content.

        This is a simple implementation using keyword extraction.
        In production, this could use ML-based embedding models.

        Args:
            content: Text to extract anchors from

        Returns:
            List of semantic anchor keywords
        """
        # Simple anchor extraction: nouns, verbs, key terms
        import re

        # Remove common words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "is",
            "are",
            "be",
            "been",
            "being",
        }

        # Extract words longer than 3 chars, not stop words
        words = re.findall(r"\b\w{4,}\b", content.lower())
        anchors = [w for w in words if w not in stop_words]

        return list(set(anchors))  # Deduplicate

    def recall_similar_context(
        self, conversation_id: str, query: str, similarity_threshold: float = 0.3
    ) -> list[dict[str, Any]]:
        """Recall contextually similar messages from conversation history.

        Args:
            conversation_id: Conversation to search
            query: Query text to find similar context
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of relevant historical messages
        """
        history = self.manager.get_history(conversation_id)
        if not history:
            return []

        query_anchors = set(self.extract_semantic_anchors(query))
        if not query_anchors:
            return []

        similar_messages: list[Any] = []
        for msg in history:
            msg_anchors = set(self.extract_semantic_anchors(msg.get("content", "")))
            if msg_anchors:
                # Calculate Jaccard similarity
                intersection = len(query_anchors & msg_anchors)
                union = len(query_anchors | msg_anchors)
                similarity = intersection / union if union > 0 else 0

                if similarity >= similarity_threshold:
                    similar_messages.append(
                        {
                            "message": msg,
                            "similarity": similarity,
                        }
                    )

        # Sort by similarity descending
        return sorted(similar_messages, key=lambda x: x["similarity"], reverse=True)

    def get_cross_session_context(self, task_type: str, limit: int = 3) -> list[dict[str, Any]]:
        """Get relevant context from recent conversations of same task type.

        Args:
            task_type: Task type to search for
            limit: Maximum number of conversations to include

        Returns:
            List of contextual information from similar past conversations
        """
        recent_convs = self.manager.get_recent_conversations(count=10)
        relevant_convs = [
            (conv_id, conv) for conv_id, conv in recent_convs if conv.get("task_type") == task_type
        ][:limit]

        context_list: list[Any] = []
        for conv_id, conv_context in relevant_convs:
            context_list.append(
                {
                    "conversation_id": conv_id,
                    "context": conv_context,
                    "summary": self.manager.conversations.get(conv_id, {}).get("summary"),
                }
            )

        return context_list

    def _check_temple_auto_archive(self, conversation_id: str) -> None:
        """Check if conversation should be auto-archived to Temple.

        Args:
            conversation_id: Conversation to check
        """
        try:
            from src.integration.temple_auto_storage import temple_auto_storage

            if temple_auto_storage.should_archive_conversation(conversation_id):
                result = temple_auto_storage.archive_conversation(conversation_id, floor=1)
                if result.get("success") and conversation_id in self.manager.conversations:
                    # Mark conversation as archived
                    self.manager.conversations[conversation_id]["archived_to_temple"] = True
                    self.manager.conversations[conversation_id]["archive_timestamp"] = result.get(
                        "timestamp"
                    )
        except (ImportError, ModuleNotFoundError, AttributeError):
            # Graceful fallback if Temple not available
            logger.debug("Suppressed AttributeError/ImportError/ModuleNotFoundError", exc_info=True)
