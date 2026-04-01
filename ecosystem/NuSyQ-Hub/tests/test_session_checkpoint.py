"""Tests for src/utils/session_checkpoint.py - Session state persistence.

Tests CheckpointMetadata dataclass, SessionCheckpoint class, and auto_checkpoint function.
"""

import json
from typing import Any

from src.utils.session_checkpoint import (
    CheckpointMetadata,
    SessionCheckpoint,
    auto_checkpoint,
)

# =============================================================================
# Test CheckpointMetadata Dataclass
# =============================================================================


class TestCheckpointMetadata:
    """Tests for CheckpointMetadata dataclass."""

    def test_all_fields_stored(self) -> None:
        """All fields are stored correctly."""
        metadata = CheckpointMetadata(
            checkpoint_id="id_001",
            timestamp="2025-01-01T00:00:00",
            description="Test checkpoint",
            session_id="session_001",
            agent_name="copilot",
            file_path="/path/to/checkpoint.json",
            size_bytes=1024,
        )
        assert metadata.checkpoint_id == "id_001"
        assert metadata.timestamp == "2025-01-01T00:00:00"
        assert metadata.description == "Test checkpoint"
        assert metadata.session_id == "session_001"
        assert metadata.agent_name == "copilot"
        assert metadata.file_path == "/path/to/checkpoint.json"
        assert metadata.size_bytes == 1024

    def test_dataclass_equality(self) -> None:
        """Dataclass equality works correctly."""
        m1 = CheckpointMetadata("a", "t", "d", "s", "agent", "path", 100)
        m2 = CheckpointMetadata("a", "t", "d", "s", "agent", "path", 100)
        assert m1 == m2


# =============================================================================
# Test SessionCheckpoint Initialization
# =============================================================================


class TestSessionCheckpointInit:
    """Tests for SessionCheckpoint initialization."""

    def test_default_checkpoint_dir(self) -> None:
        """Default checkpoint_dir is .checkpoints in cwd."""
        manager = SessionCheckpoint()
        assert manager.checkpoint_dir.name == ".checkpoints"

    def test_custom_checkpoint_dir(self, tmp_path: Any) -> None:
        """Custom checkpoint_dir is used."""
        custom_dir = tmp_path / "my_checkpoints"
        manager = SessionCheckpoint(checkpoint_dir=custom_dir)
        assert manager.checkpoint_dir == custom_dir
        assert custom_dir.exists()

    def test_default_agent_name(self) -> None:
        """Default agent_name is 'copilot'."""
        manager = SessionCheckpoint()
        assert manager.agent_name == "copilot"

    def test_custom_agent_name(self, tmp_path: Any) -> None:
        """Custom agent_name is used."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path, agent_name="claude")
        assert manager.agent_name == "claude"

    def test_default_max_checkpoints(self, tmp_path: Any) -> None:
        """Default max_checkpoints is 10."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path)
        assert manager.max_checkpoints == 10

    def test_custom_max_checkpoints(self, tmp_path: Any) -> None:
        """Custom max_checkpoints is used."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path, max_checkpoints=5)
        assert manager.max_checkpoints == 5

    def test_session_id_generated(self, tmp_path: Any) -> None:
        """session_id is generated on init."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path)
        assert manager.session_id is not None
        # Format: YYYYMMDD_HHMMSS
        assert len(manager.session_id) == 15

    def test_checkpoint_dir_created(self, tmp_path: Any) -> None:
        """checkpoint_dir is created if it doesn't exist."""
        new_dir = tmp_path / "new_checkpoints"
        assert not new_dir.exists()
        SessionCheckpoint(checkpoint_dir=new_dir)
        assert new_dir.exists()


# =============================================================================
# Test save() method
# =============================================================================


class TestSave:
    """Tests for save() method."""

    def test_save_creates_file(self, tmp_path: Any) -> None:
        """Save creates a checkpoint file."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path)
        state = {"todo_list": [{"id": 1, "status": "done"}]}
        checkpoint_id = manager.save(state, description="Test save")

        checkpoint_file = tmp_path / f"{checkpoint_id}.json"
        assert checkpoint_file.exists()

    def test_save_returns_checkpoint_id(self, tmp_path: Any) -> None:
        """Save returns the checkpoint ID."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path, agent_name="test")
        checkpoint_id = manager.save({"key": "value"})

        assert manager.agent_name in checkpoint_id
        assert manager.session_id in checkpoint_id

    def test_save_stores_state(self, tmp_path: Any) -> None:
        """Save stores the state data correctly."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path)
        state = {"modified_files": ["a.py", "b.py"], "context": {"mode": "test"}}
        checkpoint_id = manager.save(state)

        checkpoint_file = tmp_path / f"{checkpoint_id}.json"
        with open(checkpoint_file) as f:
            data = json.load(f)

        assert data["state"] == state

    def test_save_stores_metadata(self, tmp_path: Any) -> None:
        """Save stores metadata correctly."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path, agent_name="assistant")
        checkpoint_id = manager.save({}, description="My description")

        checkpoint_file = tmp_path / f"{checkpoint_id}.json"
        with open(checkpoint_file) as f:
            data = json.load(f)

        metadata = data["metadata"]
        assert metadata["checkpoint_id"] == checkpoint_id
        assert metadata["description"] == "My description"
        assert metadata["agent_name"] == "assistant"
        assert metadata["session_id"] == manager.session_id
        assert "timestamp" in metadata

    def test_save_default_description(self, tmp_path: Any) -> None:
        """Save uses 'Auto-checkpoint' as default description."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path)
        checkpoint_id = manager.save({})

        checkpoint_file = tmp_path / f"{checkpoint_id}.json"
        with open(checkpoint_file) as f:
            data = json.load(f)

        assert data["metadata"]["description"] == "Auto-checkpoint"


# =============================================================================
# Test restore() method
# =============================================================================


class TestRestore:
    """Tests for restore() method."""

    def test_restore_returns_state(self, tmp_path: Any) -> None:
        """Restore returns the saved state."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path)
        original_state = {"todo_list": [1, 2, 3], "context": "test"}
        checkpoint_id = manager.save(original_state)

        restored = manager.restore(checkpoint_id)
        assert restored == original_state

    def test_restore_latest_when_no_id(self, tmp_path: Any) -> None:
        """Restore returns latest checkpoint when no ID provided."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path)

        manager.save({"order": 1}, description="First")
        manager.save({"order": 2}, description="Second")
        manager.save({"order": 3}, description="Third")

        restored = manager.restore()
        assert restored == {"order": 3}

    def test_restore_nonexistent_returns_none(self, tmp_path: Any) -> None:
        """Restore returns None for nonexistent checkpoint."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path)
        result = manager.restore("nonexistent_id")
        assert result is None

    def test_restore_no_checkpoints_returns_none(self, tmp_path: Any) -> None:
        """Restore returns None when no checkpoints exist."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path)
        result = manager.restore()
        assert result is None


# =============================================================================
# Test list_checkpoints() method
# =============================================================================


class TestListCheckpoints:
    """Tests for list_checkpoints() method."""

    def test_list_empty_initially(self, tmp_path: Any) -> None:
        """list_checkpoints returns empty list initially."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path)
        checkpoints = manager.list_checkpoints()
        assert checkpoints == []

    def test_list_after_saves(self, tmp_path: Any) -> None:
        """list_checkpoints returns all saved checkpoints."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path)

        manager.save({"a": 1})
        manager.save({"b": 2})
        manager.save({"c": 3})

        checkpoints = manager.list_checkpoints()
        assert len(checkpoints) == 3

    def test_list_sorted_newest_first(self, tmp_path: Any) -> None:
        """list_checkpoints sorts by timestamp (newest first)."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path)

        id1 = manager.save({"first": True})
        manager.save({"second": True})
        id3 = manager.save({"third": True})

        checkpoints = manager.list_checkpoints()
        # Newest first
        assert checkpoints[0].checkpoint_id == id3
        assert checkpoints[2].checkpoint_id == id1

    def test_list_returns_metadata(self, tmp_path: Any) -> None:
        """list_checkpoints returns CheckpointMetadata objects."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path, agent_name="myagent")
        checkpoint_id = manager.save({"key": "value"}, description="Test desc")

        checkpoints = manager.list_checkpoints()
        assert len(checkpoints) == 1

        metadata = checkpoints[0]
        assert isinstance(metadata, CheckpointMetadata)
        assert metadata.checkpoint_id == checkpoint_id
        assert metadata.description == "Test desc"
        assert metadata.agent_name == "myagent"
        assert metadata.size_bytes > 0


# =============================================================================
# Test _cleanup_old_checkpoints() method
# =============================================================================


class TestCleanupOldCheckpoints:
    """Tests for _cleanup_old_checkpoints() method."""

    def test_cleanup_removes_excess(self, tmp_path: Any) -> None:
        """_cleanup_old_checkpoints removes checkpoints beyond max."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path, max_checkpoints=3)

        # Create 5 checkpoints
        for i in range(5):
            manager.save({"index": i})

        checkpoints = manager.list_checkpoints()
        # Should have only 3 (oldest removed)
        assert len(checkpoints) <= 3

    def test_cleanup_keeps_newest(self, tmp_path: Any) -> None:
        """_cleanup_old_checkpoints keeps newest checkpoints."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path, max_checkpoints=2)

        manager.save({"index": 1})
        manager.save({"index": 2})
        id3 = manager.save({"index": 3})

        checkpoints = manager.list_checkpoints()
        checkpoint_ids = [c.checkpoint_id for c in checkpoints]
        assert id3 in checkpoint_ids  # Newest should remain


# =============================================================================
# Test delete_checkpoint() method
# =============================================================================


class TestDeleteCheckpoint:
    """Tests for delete_checkpoint() method."""

    def test_delete_removes_file(self, tmp_path: Any) -> None:
        """delete_checkpoint removes the checkpoint file."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path)
        checkpoint_id = manager.save({"data": "test"})

        checkpoint_file = tmp_path / f"{checkpoint_id}.json"
        assert checkpoint_file.exists()

        result = manager.delete_checkpoint(checkpoint_id)
        assert result is True
        assert not checkpoint_file.exists()

    def test_delete_returns_true_on_success(self, tmp_path: Any) -> None:
        """delete_checkpoint returns True on success."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path)
        checkpoint_id = manager.save({})

        result = manager.delete_checkpoint(checkpoint_id)
        assert result is True

    def test_delete_nonexistent_returns_false(self, tmp_path: Any) -> None:
        """delete_checkpoint returns False for nonexistent checkpoint."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path)
        result = manager.delete_checkpoint("nonexistent_id")
        assert result is False


# =============================================================================
# Test clear_all() method
# =============================================================================


class TestClearAll:
    """Tests for clear_all() method."""

    def test_clear_all_removes_all(self, tmp_path: Any) -> None:
        """clear_all removes all checkpoints."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path)

        manager.save({"a": 1})
        manager.save({"b": 2})
        manager.save({"c": 3})

        assert len(manager.list_checkpoints()) == 3

        manager.clear_all()

        assert len(manager.list_checkpoints()) == 0

    def test_clear_all_on_empty(self, tmp_path: Any) -> None:
        """clear_all works when no checkpoints exist."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path)
        # Should not raise
        manager.clear_all()
        assert len(manager.list_checkpoints()) == 0


# =============================================================================
# Test auto_checkpoint() function
# =============================================================================


class TestAutoCheckpoint:
    """Tests for auto_checkpoint() convenience function."""

    def test_auto_checkpoint_creates_file(self, tmp_path: Any) -> None:
        """auto_checkpoint creates a checkpoint file."""
        checkpoint_id = auto_checkpoint(
            {"state": "data"},
            description="Quick save",
            checkpoint_dir=tmp_path,
        )

        checkpoint_file = tmp_path / f"{checkpoint_id}.json"
        assert checkpoint_file.exists()

    def test_auto_checkpoint_returns_id(self, tmp_path: Any) -> None:
        """auto_checkpoint returns checkpoint ID."""
        checkpoint_id = auto_checkpoint(
            {"key": "value"},
            checkpoint_dir=tmp_path,
        )

        assert isinstance(checkpoint_id, str)
        assert len(checkpoint_id) > 0

    def test_auto_checkpoint_default_description(self, tmp_path: Any) -> None:
        """auto_checkpoint uses default description."""
        checkpoint_id = auto_checkpoint(
            {"data": 123},
            checkpoint_dir=tmp_path,
        )

        checkpoint_file = tmp_path / f"{checkpoint_id}.json"
        with open(checkpoint_file) as f:
            data = json.load(f)

        assert data["metadata"]["description"] == "Auto-checkpoint"


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_unicode_in_state(self, tmp_path: Any) -> None:
        """Unicode characters in state are preserved."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path)
        state = {"message": "Hello 世界 🌍"}
        checkpoint_id = manager.save(state)

        restored = manager.restore(checkpoint_id)
        assert restored["message"] == "Hello 世界 🌍"

    def test_large_state(self, tmp_path: Any) -> None:
        """Large state can be saved and restored."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path)
        state = {"data": list(range(10000))}
        checkpoint_id = manager.save(state)

        restored = manager.restore(checkpoint_id)
        assert restored == state

    def test_nested_state(self, tmp_path: Any) -> None:
        """Nested state structures are preserved."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path)
        state = {"level1": {"level2": {"level3": {"value": "deep"}}}}
        checkpoint_id = manager.save(state)

        restored = manager.restore(checkpoint_id)
        assert restored == state
        assert restored["level1"]["level2"]["level3"]["value"] == "deep"

    def test_invalid_json_file_skipped(self, tmp_path: Any) -> None:
        """Invalid JSON files are skipped in list_checkpoints."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path)

        # Create valid checkpoint
        manager.save({"valid": True})

        # Create invalid JSON file
        invalid_file = tmp_path / "invalid_checkpoint.json"
        invalid_file.write_text("not valid json {{{")

        # Should not raise, should skip invalid
        checkpoints = manager.list_checkpoints()
        assert len(checkpoints) == 1
        assert checkpoints[0].description != "invalid"

    def test_empty_state(self, tmp_path: Any) -> None:
        """Empty state can be saved and restored."""
        manager = SessionCheckpoint(checkpoint_dir=tmp_path)
        checkpoint_id = manager.save({})

        restored = manager.restore(checkpoint_id)
        assert restored == {}
