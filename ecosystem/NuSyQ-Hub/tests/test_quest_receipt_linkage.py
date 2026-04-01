"""Tests for src/core/quest_receipt_linkage.py

This module tests the Quest-Receipt Linkage System which bridges
action receipts with the quest system.

Coverage Target: 70%+
"""

from unittest.mock import MagicMock

import pytest

# =============================================================================
# Module Import
# =============================================================================


class TestModuleImports:
    """Test module-level imports."""

    def test_import_link_receipt_to_quest(self):
        """Test main function can be imported."""
        from src.core.quest_receipt_linkage import link_receipt_to_quest

        assert link_receipt_to_quest is not None

    def test_import_ensure_link_file(self):
        """Test ensure_link_file can be imported."""
        from src.core.quest_receipt_linkage import ensure_link_file

        assert ensure_link_file is not None

    def test_import_stats(self):
        """Test stats can be imported."""
        from src.core.quest_receipt_linkage import stats

        assert stats is not None


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace with directory structure."""
    quest_dir = tmp_path / "src" / "Rosetta_Quest_System"
    quest_dir.mkdir(parents=True)
    state_dir = tmp_path / "state"
    state_dir.mkdir(parents=True)
    return tmp_path


@pytest.fixture
def sample_receipt():
    """Sample action receipt for testing."""
    return {
        "receipt_id": "receipt-12345678",
        "action_id": "action-87654321",
        "status": "SUCCESS",
        "agent": "ollama",
        "task_type": "analyze",
        "duration_s": 2.5,
        "metadata": {
            "policy_category": "FEATURE",
            "risk_score": 0.3,
        },
    }


@pytest.fixture
def sample_world_state():
    """Sample world state for testing."""
    return {
        "decision_epoch": 42,
        "signals": {"facts": []},
        "coherence": {"contradictions": []},
    }


@pytest.fixture
def mock_quest_engine():
    """Mock QuestEngine for testing."""
    engine = MagicMock()
    engine.quests = {}
    engine.complete_quest = MagicMock()
    return engine


# =============================================================================
# ensure_link_file Tests
# =============================================================================


class TestEnsureLinkFile:
    """Test ensure_link_file function."""

    def test_creates_link_file_if_not_exists(self, temp_workspace):
        """Test that ensure_link_file creates file if not exists."""
        from src.core.quest_receipt_linkage import ensure_link_file

        link_file = ensure_link_file(temp_workspace)

        assert link_file.exists()

    def test_creates_parent_directories(self, tmp_path):
        """Test that ensure_link_file creates parent dirs."""
        from src.core.quest_receipt_linkage import ensure_link_file

        # Use tmp_path that doesn't have the directory structure
        workspace = tmp_path / "new_workspace"
        workspace.mkdir()

        link_file = ensure_link_file(workspace)

        assert link_file.parent.exists()

    def test_returns_path_if_exists(self, temp_workspace):
        """Test that ensure_link_file returns existing file."""
        from src.core.quest_receipt_linkage import ensure_link_file

        # Create file first
        link_file = ensure_link_file(temp_workspace)

        # Call again
        link_file2 = ensure_link_file(temp_workspace)

        assert link_file == link_file2


# =============================================================================
# append_quest_log_event Tests
# =============================================================================


class TestAppendQuestLogEvent:
    """Test append_quest_log_event function."""

    def test_appends_event_to_log(self, temp_workspace):
        """Test that event is appended to quest_log.jsonl."""
        from src.core.quest_receipt_linkage import append_quest_log_event

        result = append_quest_log_event(
            "test_event",
            {"key": "value"},
            workspace_root=temp_workspace,
        )

        assert result["event"] == "test_event"
        assert result["details"]["key"] == "value"
        assert "timestamp" in result

    def test_creates_quest_log_file(self, temp_workspace):
        """Test that quest_log.jsonl is created."""
        from src.core.quest_receipt_linkage import QUEST_LOG_FILE, append_quest_log_event

        append_quest_log_event("test", {}, workspace_root=temp_workspace)

        log_file = temp_workspace / QUEST_LOG_FILE
        assert log_file.exists()

    def test_multiple_events_appended(self, temp_workspace):
        """Test multiple events are appended correctly."""
        from src.core.quest_receipt_linkage import QUEST_LOG_FILE, append_quest_log_event

        append_quest_log_event("event1", {"n": 1}, workspace_root=temp_workspace)
        append_quest_log_event("event2", {"n": 2}, workspace_root=temp_workspace)

        log_file = temp_workspace / QUEST_LOG_FILE
        lines = log_file.read_text().strip().split("\n")

        assert len(lines) == 2


# =============================================================================
# link_receipt_to_quest Tests
# =============================================================================


class TestLinkReceiptToQuest:
    """Test link_receipt_to_quest function."""

    def test_creates_link_record(self, temp_workspace, sample_receipt):
        """Test that link_receipt_to_quest creates a link record."""
        from src.core.quest_receipt_linkage import link_receipt_to_quest

        link = link_receipt_to_quest(
            sample_receipt,
            "quest-123",
            workspace_root=temp_workspace,
        )

        assert link["receipt_id"] == "receipt-12345678"
        assert link["quest_id"] == "quest-123"
        assert link["action_status"] == "SUCCESS"

    def test_includes_agent_and_task_type(self, temp_workspace, sample_receipt):
        """Test that link includes agent and task_type."""
        from src.core.quest_receipt_linkage import link_receipt_to_quest

        link = link_receipt_to_quest(
            sample_receipt,
            "quest-123",
            workspace_root=temp_workspace,
        )

        assert link["agent"] == "ollama"
        assert link["task_type"] == "analyze"

    def test_includes_world_state_metadata(
        self, temp_workspace, sample_receipt, sample_world_state
    ):
        """Test that link includes world state metadata."""
        from src.core.quest_receipt_linkage import link_receipt_to_quest

        link = link_receipt_to_quest(
            sample_receipt,
            "quest-123",
            world_state=sample_world_state,
            workspace_root=temp_workspace,
        )

        assert link["metadata"]["decision_epoch"] == 42

    def test_appends_to_link_file(self, temp_workspace, sample_receipt):
        """Test that link is appended to link file."""
        from src.core.quest_receipt_linkage import ensure_link_file, link_receipt_to_quest

        link_receipt_to_quest(sample_receipt, "quest-1", workspace_root=temp_workspace)
        link_receipt_to_quest(sample_receipt, "quest-2", workspace_root=temp_workspace)

        link_file = ensure_link_file(temp_workspace)
        lines = link_file.read_text().strip().split("\n")

        assert len(lines) == 2

    def test_handles_missing_receipt_fields(self, temp_workspace):
        """Test that link handles receipt with missing fields."""
        from src.core.quest_receipt_linkage import link_receipt_to_quest

        minimal_receipt = {"status": "SUCCESS"}

        link = link_receipt_to_quest(
            minimal_receipt,
            "quest-123",
            workspace_root=temp_workspace,
        )

        assert link["receipt_id"] is None
        assert link["action_status"] == "SUCCESS"


# =============================================================================
# update_quest_from_receipt Tests
# =============================================================================


class TestUpdateQuestFromReceipt:
    """Test update_quest_from_receipt function."""

    def test_completes_active_quest_on_success(self, mock_quest_engine, sample_receipt):
        """Test that successful receipt completes active quest."""
        from src.core.quest_receipt_linkage import update_quest_from_receipt

        mock_quest = MagicMock()
        mock_quest.status = "active"
        mock_quest.history = []
        mock_quest_engine.quests = {"quest-123": mock_quest}

        update_quest_from_receipt(mock_quest_engine, sample_receipt, "quest-123")

        mock_quest_engine.complete_quest.assert_called_once_with("quest-123")

    def test_blocks_quest_on_failure(self, mock_quest_engine):
        """Test that failed receipt blocks quest."""
        from src.core.quest_receipt_linkage import update_quest_from_receipt

        mock_quest = MagicMock()
        mock_quest.status = "active"
        mock_quest.history = []
        mock_quest_engine.quests = {"quest-123": mock_quest}

        failed_receipt = {
            "receipt_id": "r-fail",
            "status": "FAILED",
            "error_message": "Test error",
        }

        update_quest_from_receipt(mock_quest_engine, failed_receipt, "quest-123")

        assert mock_quest.status == "blocked"

    def test_logs_partial_success(self, mock_quest_engine):
        """Test that partial receipt logs to history."""
        from src.core.quest_receipt_linkage import update_quest_from_receipt

        mock_quest = MagicMock()
        mock_quest.status = "active"
        mock_quest.history = []
        mock_quest_engine.quests = {"quest-123": mock_quest}

        partial_receipt = {
            "receipt_id": "r-partial",
            "status": "PARTIAL",
        }

        update_quest_from_receipt(mock_quest_engine, partial_receipt, "quest-123")

        assert len(mock_quest.history) == 1
        assert mock_quest.history[0]["event"] == "action_partial_success"

    def test_handles_missing_quest(self, mock_quest_engine, sample_receipt):
        """Test that missing quest doesn't raise."""
        from src.core.quest_receipt_linkage import update_quest_from_receipt

        mock_quest_engine.quests = {}  # Empty

        # Should not raise
        update_quest_from_receipt(mock_quest_engine, sample_receipt, "nonexistent")


# =============================================================================
# get_quest_action_history Tests
# =============================================================================


class TestGetQuestActionHistory:
    """Test get_quest_action_history function."""

    def test_returns_empty_for_new_quest(self, temp_workspace):
        """Test empty history for quest with no actions."""
        from src.core.quest_receipt_linkage import ensure_link_file, get_quest_action_history

        # Create empty link file
        ensure_link_file(temp_workspace)

        history = get_quest_action_history("quest-new", workspace_root=temp_workspace)

        assert history == []

    def test_returns_linked_actions(self, temp_workspace, sample_receipt):
        """Test that linked actions are returned."""
        from src.core.quest_receipt_linkage import (
            get_quest_action_history,
            link_receipt_to_quest,
        )

        link_receipt_to_quest(sample_receipt, "quest-123", workspace_root=temp_workspace)

        history = get_quest_action_history("quest-123", workspace_root=temp_workspace)

        assert len(history) == 1
        assert history[0]["quest_id"] == "quest-123"

    def test_filters_by_quest_id(self, temp_workspace, sample_receipt):
        """Test that only matching quest_id is returned."""
        from src.core.quest_receipt_linkage import (
            get_quest_action_history,
            link_receipt_to_quest,
        )

        link_receipt_to_quest(sample_receipt, "quest-A", workspace_root=temp_workspace)
        link_receipt_to_quest(sample_receipt, "quest-B", workspace_root=temp_workspace)

        history_a = get_quest_action_history("quest-A", workspace_root=temp_workspace)
        history_b = get_quest_action_history("quest-B", workspace_root=temp_workspace)

        assert len(history_a) == 1
        assert len(history_b) == 1

    def test_handles_corrupt_json(self, temp_workspace):
        """Test that corrupt JSON lines are skipped."""
        from src.core.quest_receipt_linkage import (
            ensure_link_file,
            get_quest_action_history,
        )

        link_file = ensure_link_file(temp_workspace)
        with open(link_file, "w") as f:
            f.write('{"quest_id": "quest-123", "timestamp": "2025-01-01"}\n')
            f.write("not valid json\n")
            f.write('{"quest_id": "quest-123", "timestamp": "2025-01-02"}\n')

        history = get_quest_action_history("quest-123", workspace_root=temp_workspace)

        assert len(history) == 2  # Skips corrupted line


# =============================================================================
# get_quests_for_epoch Tests
# =============================================================================


class TestGetQuestsForEpoch:
    """Test get_quests_for_epoch function."""

    def test_returns_empty_for_no_links(self, temp_workspace):
        """Test empty result for epoch with no links."""
        from src.core.quest_receipt_linkage import ensure_link_file, get_quests_for_epoch

        ensure_link_file(temp_workspace)

        result = get_quests_for_epoch({"decision_epoch": 99}, workspace_root=temp_workspace)

        assert result == []

    def test_returns_quests_for_epoch(self, temp_workspace, sample_receipt, sample_world_state):
        """Test that quests for epoch are returned."""
        from src.core.quest_receipt_linkage import (
            get_quests_for_epoch,
            link_receipt_to_quest,
        )

        link_receipt_to_quest(sample_receipt, "quest-A", sample_world_state, temp_workspace)
        link_receipt_to_quest(sample_receipt, "quest-B", sample_world_state, temp_workspace)

        result = get_quests_for_epoch(sample_world_state, workspace_root=temp_workspace)

        assert "quest-A" in result
        assert "quest-B" in result

    def test_deduplicates_quest_ids(self, temp_workspace, sample_receipt, sample_world_state):
        """Test that duplicate quest IDs are deduplicated."""
        from src.core.quest_receipt_linkage import (
            get_quests_for_epoch,
            link_receipt_to_quest,
        )

        link_receipt_to_quest(sample_receipt, "quest-X", sample_world_state, temp_workspace)
        link_receipt_to_quest(sample_receipt, "quest-X", sample_world_state, temp_workspace)

        result = get_quests_for_epoch(sample_world_state, workspace_root=temp_workspace)

        assert len(result) == 1


# =============================================================================
# stats Tests
# =============================================================================


class TestStats:
    """Test stats function."""

    def test_returns_empty_stats_for_new_file(self, temp_workspace):
        """Test stats for empty link file."""
        from src.core.quest_receipt_linkage import ensure_link_file, stats

        ensure_link_file(temp_workspace)

        result = stats(workspace_root=temp_workspace)

        assert result["total_links"] == 0
        assert result["unique_quests"] == 0

    def test_counts_successful_actions(self, temp_workspace, sample_receipt):
        """Test that successful actions are counted."""
        from src.core.quest_receipt_linkage import link_receipt_to_quest, stats

        link_receipt_to_quest(sample_receipt, "quest-1", workspace_root=temp_workspace)

        result = stats(workspace_root=temp_workspace)

        assert result["total_links"] == 1
        assert result["successful_actions"] == 1

    def test_counts_failed_actions(self, temp_workspace):
        """Test that failed actions are counted."""
        from src.core.quest_receipt_linkage import link_receipt_to_quest, stats

        failed_receipt = {"receipt_id": "r-fail", "status": "FAILED", "agent": "test"}
        link_receipt_to_quest(failed_receipt, "quest-1", workspace_root=temp_workspace)

        result = stats(workspace_root=temp_workspace)

        assert result["failed_actions"] == 1

    def test_counts_unique_quests(self, temp_workspace, sample_receipt):
        """Test that unique quests are counted."""
        from src.core.quest_receipt_linkage import link_receipt_to_quest, stats

        link_receipt_to_quest(sample_receipt, "quest-A", workspace_root=temp_workspace)
        link_receipt_to_quest(sample_receipt, "quest-A", workspace_root=temp_workspace)
        link_receipt_to_quest(sample_receipt, "quest-B", workspace_root=temp_workspace)

        result = stats(workspace_root=temp_workspace)

        assert result["unique_quests"] == 2
        assert result["total_links"] == 3

    def test_by_agent_breakdown(self, temp_workspace, sample_receipt):
        """Test by_agent breakdown."""
        from src.core.quest_receipt_linkage import link_receipt_to_quest, stats

        link_receipt_to_quest(sample_receipt, "quest-1", workspace_root=temp_workspace)

        result = stats(workspace_root=temp_workspace)

        assert "ollama" in result["by_agent"]
        assert result["by_agent"]["ollama"]["link_count"] == 1
        assert result["by_agent"]["ollama"]["successful"] == 1


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_link_with_none_world_state(self, temp_workspace, sample_receipt):
        """Test link_receipt_to_quest with None world_state."""
        from src.core.quest_receipt_linkage import link_receipt_to_quest

        link = link_receipt_to_quest(
            sample_receipt,
            "quest-123",
            world_state=None,
            workspace_root=temp_workspace,
        )

        assert link["metadata"]["decision_epoch"] is None

    def test_empty_link_file_lines_skipped(self, temp_workspace):
        """Test that empty lines in link file are skipped."""
        from src.core.quest_receipt_linkage import (
            ensure_link_file,
            get_quest_action_history,
        )

        link_file = ensure_link_file(temp_workspace)
        with open(link_file, "w") as f:
            f.write('{"quest_id": "quest-123", "timestamp": "2025-01-01"}\n')
            f.write("\n")  # Empty line
            f.write("   \n")  # Whitespace line

        history = get_quest_action_history("quest-123", workspace_root=temp_workspace)

        assert len(history) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
