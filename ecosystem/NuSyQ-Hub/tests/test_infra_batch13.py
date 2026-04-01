"""Batch 13 infrastructure tests: storage, attestation, safety, status_helpers."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch


# ============================================================================
# storage.py
# ============================================================================
class TestLoadTasks:
    """Tests for load_tasks function."""

    def test_returns_empty_list_when_file_not_found(self, tmp_path: Path, monkeypatch):
        """When tasks.json doesn't exist, return empty list."""
        monkeypatch.setattr(
            "src.tools.task_manager.storage.TASKS_FILE",
            tmp_path / "nonexistent.json",
        )
        from src.tools.task_manager.storage import load_tasks

        result = load_tasks()
        assert result == []

    def test_loads_existing_tasks(self, tmp_path: Path, monkeypatch):
        """When tasks.json exists, return its contents."""
        tasks_file = tmp_path / "tasks.json"
        tasks_file.write_text('[{"id": 1, "title": "Test"}]')
        monkeypatch.setattr(
            "src.tools.task_manager.storage.TASKS_FILE",
            tasks_file,
        )
        from src.tools.task_manager.storage import load_tasks

        result = load_tasks()
        assert result == [{"id": 1, "title": "Test"}]


class TestSaveTasks:
    """Tests for save_tasks function."""

    def test_writes_tasks_to_file(self, tmp_path: Path, monkeypatch):
        """Save tasks should write JSON to file."""
        tasks_file = tmp_path / "tasks.json"
        monkeypatch.setattr(
            "src.tools.task_manager.storage.TASKS_FILE",
            tasks_file,
        )
        from src.tools.task_manager.storage import save_tasks

        tasks = [{"id": 1, "title": "Task 1"}, {"id": 2, "title": "Task 2"}]
        save_tasks(tasks)

        assert tasks_file.exists()
        loaded = json.loads(tasks_file.read_text())
        assert loaded == tasks

    def test_overwrites_existing_file(self, tmp_path: Path, monkeypatch):
        """Save should overwrite existing content."""
        tasks_file = tmp_path / "tasks.json"
        tasks_file.write_text('[{"old": "data"}]')
        monkeypatch.setattr(
            "src.tools.task_manager.storage.TASKS_FILE",
            tasks_file,
        )
        from src.tools.task_manager.storage import save_tasks

        save_tasks([{"new": "data"}])

        loaded = json.loads(tasks_file.read_text())
        assert loaded == [{"new": "data"}]


# ============================================================================
# attestation.py
# ============================================================================
class TestAttestManifest:
    """Tests for attest_manifest function."""

    def test_returns_manifest_unchanged_when_feature_disabled(self):
        """When attestation disabled, return manifest as-is."""
        with patch("src.system.attestation.is_feature_enabled", return_value=False):
            from src.system.attestation import attest_manifest

            manifest = {"name": "test", "version": "1.0"}
            result = attest_manifest(manifest)

            assert result == manifest
            assert "attestation" not in result

    def test_adds_attestation_when_feature_enabled(self):
        """When attestation enabled, add sha256 digest."""
        with patch("src.system.attestation.is_feature_enabled", return_value=True):
            from src.system.attestation import attest_manifest

            manifest = {"name": "test", "version": "1.0"}
            result = attest_manifest(manifest)

            assert "attestation" in result
            assert "sha256" in result["attestation"]
            assert len(result["attestation"]["sha256"]) == 64  # SHA256 hex

    def test_attestation_is_deterministic(self):
        """Same manifest should produce same attestation."""
        with patch("src.system.attestation.is_feature_enabled", return_value=True):
            from src.system.attestation import attest_manifest

            manifest1 = {"a": 1, "b": 2}
            manifest2 = {"a": 1, "b": 2}
            result1 = attest_manifest(manifest1.copy())
            result2 = attest_manifest(manifest2.copy())

            assert result1["attestation"]["sha256"] == result2["attestation"]["sha256"]


# ============================================================================
# safety.py
# ============================================================================
class TestVoteResponses:
    """Tests for vote_responses function."""

    def test_returns_first_non_error(self):
        """Select first response without error field."""
        from src.system.safety import vote_responses

        responses = [
            {"error": "failed"},
            {"result": "success"},
            {"result": "also good"},
        ]
        result = vote_responses(responses)

        assert result["winner"] == {"result": "success"}
        assert len(result["votes"]) == 3

    def test_returns_first_when_all_errors(self):
        """If all have errors, return first anyway."""
        from src.system.safety import vote_responses

        responses = [
            {"error": "error1"},
            {"error": "error2"},
        ]
        result = vote_responses(responses)

        assert result["winner"] == {"error": "error1"}

    def test_handles_empty_list(self):
        """Empty responses list returns empty dict as winner."""
        from src.system.safety import vote_responses

        result = vote_responses([])
        assert result["winner"] == {}
        assert result["votes"] == []


class TestDiffResponses:
    """Tests for diff_responses function."""

    def test_same_when_equal(self):
        """Same content returns same=True."""
        from src.system.safety import diff_responses

        result = diff_responses("hello", "hello")
        assert result["same"] is True
        assert result["len_a"] == 5
        assert result["len_b"] == 5

    def test_same_ignores_whitespace(self):
        """Strip whitespace before comparing."""
        from src.system.safety import diff_responses

        result = diff_responses("  hello  ", "hello")
        assert result["same"] is True

    def test_different_when_not_equal(self):
        """Different content returns same=False."""
        from src.system.safety import diff_responses

        result = diff_responses("hello", "world")
        assert result["same"] is False
        assert result["len_a"] == 5
        assert result["len_b"] == 5


# ============================================================================
# status_helpers.py
# ============================================================================
class TestNormalizeStatus:
    """Tests for normalize_status function."""

    def test_returns_default_for_none(self):
        """None returns default status."""
        from src.utils.status_helpers import normalize_status

        assert normalize_status(None) == "pending"

    def test_returns_default_for_empty(self):
        """Empty string returns default status."""
        from src.utils.status_helpers import normalize_status

        assert normalize_status("") == "pending"

    def test_normalizes_known_status(self):
        """Known status maps to canonical."""
        from src.utils.status_helpers import normalize_status

        assert normalize_status("complete") == "completed"
        assert normalize_status("COMPLETED") == "completed"
        assert normalize_status("  Active  ") == "active"

    def test_preserves_unknown_status(self):
        """Unknown status returned as-is (lowercased)."""
        from src.utils.status_helpers import normalize_status

        assert normalize_status("custom_status") == "custom_status"


class TestIsCompleted:
    """Tests for is_completed function."""

    def test_true_for_completed(self):
        """Returns True for 'completed' variations."""
        from src.utils.status_helpers import is_completed

        assert is_completed("completed") is True
        assert is_completed("complete") is True
        assert is_completed("COMPLETED") is True

    def test_false_for_other_statuses(self):
        """Returns False for non-completed statuses."""
        from src.utils.status_helpers import is_completed

        assert is_completed("pending") is False
        assert is_completed("active") is False
        assert is_completed(None) is False
