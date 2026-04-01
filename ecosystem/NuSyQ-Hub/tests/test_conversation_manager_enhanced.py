#!/usr/bin/env python3
"""Test suite for enhanced ConversationManager with context persistence and memory recall.

Tests Zeta04 implementation for cross-session conversation management.
"""

import tempfile
from pathlib import Path

import pytest
from src.ai.conversation_manager import (
    ContextualMemoryRecall,
    ConversationManager,
)


@pytest.fixture
def temp_storage():
    """Create temporary storage path for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "conversations.json"


@pytest.fixture
def manager(temp_storage):
    """Create a ConversationManager with temporary storage."""
    return ConversationManager(storage_path=temp_storage)


class TestConversationManagerEnhanced:
    """Test enhanced ConversationManager features."""

    def test_create_conversation_with_task_type(self, manager):
        """Test creating conversation with task type awareness."""
        manager.create_conversation("conv1", task_type="coding", metadata={"project": "test"})

        context = manager.get_context("conv1")
        assert context["task_type"] == "coding"
        assert context["metadata"]["project"] == "test"
        assert context["message_count"] == 0

    def test_add_message_with_metadata(self, manager):
        """Test adding messages with metadata."""
        manager.create_conversation("conv1", task_type="general")
        manager.add_message("conv1", "user", "Hello", metadata={"source": "test"})

        history = manager.get_history("conv1")
        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert history[0]["source"] == "test"
        assert "timestamp" in history[0]

    def test_conversation_summary(self, manager):
        """Test conversation summary functionality."""
        manager.create_conversation("conv1", task_type="coding")
        manager.add_message("conv1", "user", "How do I write async code?")
        manager.add_message("conv1", "assistant", "Here's an example...")

        summary = "Discussion about async programming in Python"
        manager.set_conversation_summary("conv1", summary)

        context = manager.get_context("conv1")
        assert context["summary"] == summary

    def test_get_recent_conversations(self, manager):
        """Test retrieving recent conversations."""
        import time

        manager.create_conversation("conv1", task_type="coding")
        time.sleep(0.01)  # Ensure different timestamps
        manager.create_conversation("conv2", task_type="general")
        time.sleep(0.01)
        manager.create_conversation("conv3", task_type="creative")

        manager.add_message("conv1", "user", "test")
        time.sleep(0.01)
        manager.add_message("conv3", "user", "test")  # This one most recent

        recent = manager.get_recent_conversations(count=2)
        assert len(recent) == 2
        assert recent[0][0] == "conv3"  # Most recent first

    def test_message_history_limit(self, manager):
        """Test limiting message history retrieval."""
        manager.create_conversation("conv1")
        for i in range(10):
            manager.add_message("conv1", "user", f"Message {i}")

        history = manager.get_history("conv1", limit=3)
        assert len(history) == 3
        assert "9" in history[-1]["content"]  # Most recent

    def test_persistence(self, temp_storage):
        """Test conversation persistence across instances."""
        # Create and save conversations
        manager1 = ConversationManager(storage_path=temp_storage)
        manager1.create_conversation("conv1", task_type="coding")
        manager1.add_message("conv1", "user", "Hello")

        # Load in new instance
        manager2 = ConversationManager(storage_path=temp_storage)
        assert "conv1" in manager2.conversations
        context = manager2.get_context("conv1")
        assert context["task_type"] == "coding"
        assert context["message_count"] == 1


class TestContextualMemoryRecall:
    """Test context-aware memory recall functionality."""

    def test_semantic_anchor_extraction(self):
        """Test semantic anchor extraction."""
        recall = ContextualMemoryRecall()

        anchors = recall.extract_semantic_anchors("The quick brown fox jumps over lazy dogs")
        assert "quick" in anchors
        assert "brown" in anchors
        assert "jumps" in anchors
        # Stop words should not be included
        assert "the" not in anchors
        assert "lazy" in anchors
        assert "dogs" in anchors

    def test_recall_similar_context(self, manager):
        """Test recalling similar context from history."""
        manager.create_conversation("conv1", task_type="coding")
        manager.add_message("conv1", "user", "How do I write async Python code?")
        manager.add_message("conv1", "assistant", "Use asyncio library with async/await")
        manager.add_message("conv1", "user", "What about async debugging?")
        manager.add_message("conv1", "assistant", "Use asyncio.run() or debuggers")

        recall = ContextualMemoryRecall(manager)
        similar = recall.recall_similar_context(
            "conv1", "async programming", similarity_threshold=0.2
        )

        # Should find messages related to "async" and "programming"
        assert len(similar) > 0
        # Check that similarity scores are reasonable
        for item in similar:
            assert 0 <= item["similarity"] <= 1

    def test_cross_session_context_retrieval(self, manager):
        """Test retrieving context from similar task types."""
        # Create conversations of different task types
        manager.create_conversation("coding1", task_type="coding")
        manager.add_message("coding1", "user", "async code")

        manager.create_conversation("general1", task_type="general")
        manager.add_message("general1", "user", "general question")

        manager.create_conversation("coding2", task_type="coding")
        manager.add_message("coding2", "user", "more code")

        recall = ContextualMemoryRecall(manager)
        cross_session = recall.get_cross_session_context("coding", limit=2)

        # Should get recent coding conversations
        assert len(cross_session) <= 2
        for item in cross_session:
            assert item["context"]["task_type"] == "coding"

    def test_memory_recall_with_empty_history(self, manager):
        """Test memory recall with empty conversation."""
        recall = ContextualMemoryRecall(manager)
        manager.create_conversation("empty")

        similar = recall.recall_similar_context("empty", "test query")
        assert similar == []

    def test_memory_recall_with_high_threshold(self, manager):
        """Test memory recall with high similarity threshold."""
        manager.create_conversation("conv1")
        manager.add_message("conv1", "user", "Python")
        manager.add_message("conv1", "user", "Java")
        manager.add_message("conv1", "user", "JavaScript")

        recall = ContextualMemoryRecall(manager)
        # Very high threshold should return nothing
        similar = recall.recall_similar_context("conv1", "Ruby", similarity_threshold=0.9)
        assert len(similar) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
