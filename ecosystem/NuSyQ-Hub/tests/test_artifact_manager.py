"""Tests for src/tools/artifact_manager.py - Artifact Trust Layer.

Tests ArtifactMetadata, RunManifest, and ArtifactManager classes.
"""

import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from src.tools.artifact_manager import (
    ArtifactManager,
    ArtifactMetadata,
    RunManifest,
)

# =============================================================================
# Test ArtifactMetadata Dataclass
# =============================================================================


class TestArtifactMetadata:
    """Tests for ArtifactMetadata dataclass."""

    def test_create_metadata(self) -> None:
        """ArtifactMetadata can be created with required fields."""
        metadata = ArtifactMetadata(
            run_id="run_123",
            timestamp="2024-01-01T00:00:00",
            action="analyze",
            repo="NuSyQ-Hub",
            branch="master",
            commit="abc123",
            agent="copilot",
            model="gpt-4",
        )
        assert metadata.run_id == "run_123"
        assert metadata.action == "analyze"
        assert metadata.status == "pending"

    def test_metadata_default_values(self) -> None:
        """ArtifactMetadata has expected default values."""
        metadata = ArtifactMetadata(
            run_id="run_123",
            timestamp="now",
            action="test",
            repo="test",
            branch="main",
            commit="x",
            agent="test",
            model="test",
        )
        assert metadata.user is None
        assert metadata.cost_estimate == 0.0
        assert metadata.touched_files == []
        assert metadata.status == "pending"
        assert metadata.exit_code == 0


# =============================================================================
# Test RunManifest Dataclass
# =============================================================================


class TestRunManifest:
    """Tests for RunManifest dataclass."""

    def test_create_manifest(self) -> None:
        """RunManifest can be created with metadata."""
        metadata = ArtifactMetadata(
            run_id="run_123",
            timestamp="now",
            action="test",
            repo="test",
            branch="main",
            commit="x",
            agent="test",
            model="test",
        )
        manifest = RunManifest(metadata=metadata)
        assert manifest.metadata == metadata
        assert manifest.environment == {}
        assert manifest.flags == {}

    def test_compute_hash(self) -> None:
        """RunManifest.compute_hash generates SHA256."""
        metadata = ArtifactMetadata(
            run_id="run_123",
            timestamp="now",
            action="test",
            repo="test",
            branch="main",
            commit="x",
            agent="test",
            model="test",
        )
        manifest = RunManifest(metadata=metadata)
        hash_result = manifest.compute_hash()
        assert len(hash_result) == 64  # SHA256 hex length
        assert all(c in "0123456789abcdef" for c in hash_result)

    def test_compute_hash_deterministic(self) -> None:
        """Same manifest produces same hash."""
        metadata = ArtifactMetadata(
            run_id="run_123",
            timestamp="now",
            action="test",
            repo="test",
            branch="main",
            commit="x",
            agent="test",
            model="test",
        )
        manifest = RunManifest(metadata=metadata)
        hash1 = manifest.compute_hash()
        hash2 = manifest.compute_hash()
        assert hash1 == hash2


# =============================================================================
# Test ArtifactManager Initialization
# =============================================================================


class TestArtifactManagerInit:
    """Tests for ArtifactManager initialization."""

    def test_init_creates_directories(self, tmp_path: Any) -> None:
        """ArtifactManager creates artifact directories."""
        with patch("src.tools.artifact_manager.subprocess.run"):
            manager = ArtifactManager(tmp_path, action="test", agent="test")
            assert manager.artifacts_dir.exists()
            assert manager.diffs_dir.exists()
            assert manager.logs_dir.exists()

    def test_init_generates_run_id(self, tmp_path: Any) -> None:
        """ArtifactManager generates unique run_id."""
        with patch("src.tools.artifact_manager.subprocess.run"):
            manager = ArtifactManager(tmp_path, action="test")
            assert manager.run_id.startswith("run_")
            assert len(manager.run_id) > 20  # Has timestamp and uuid

    def test_init_sets_action(self, tmp_path: Any) -> None:
        """ArtifactManager stores action."""
        with patch("src.tools.artifact_manager.subprocess.run"):
            manager = ArtifactManager(tmp_path, action="analyze")
            assert manager.action == "analyze"
            assert manager.metadata.action == "analyze"

    def test_init_sets_agent(self, tmp_path: Any) -> None:
        """ArtifactManager stores agent."""
        with patch("src.tools.artifact_manager.subprocess.run"):
            manager = ArtifactManager(tmp_path, action="test", agent="claude")
            assert manager.agent == "claude"
            assert manager.metadata.agent == "claude"

    def test_detect_repo_nusyq_hub(self, tmp_path: Any) -> None:
        """_detect_repo identifies NuSyQ-Hub."""
        hub_path = tmp_path / "NuSyQ-Hub"
        hub_path.mkdir()
        with patch("src.tools.artifact_manager.subprocess.run"):
            manager = ArtifactManager(hub_path, action="test")
            assert manager.metadata.repo == "NuSyQ-Hub"

    def test_detect_repo_simulatedverse(self, tmp_path: Any) -> None:
        """_detect_repo identifies SimulatedVerse."""
        sv_path = tmp_path / "SimulatedVerse"
        sv_path.mkdir()
        with patch("src.tools.artifact_manager.subprocess.run"):
            manager = ArtifactManager(sv_path, action="test")
            assert manager.metadata.repo == "SimulatedVerse"

    def test_detect_repo_unknown(self, tmp_path: Any) -> None:
        """_detect_repo returns unknown for other paths."""
        with patch("src.tools.artifact_manager.subprocess.run"):
            manager = ArtifactManager(tmp_path, action="test")
            assert manager.metadata.repo == "unknown"


# =============================================================================
# Test start() method
# =============================================================================


class TestStart:
    """Tests for start() method."""

    def test_start_sets_status(self, tmp_path: Any) -> None:
        """start() sets status to running."""
        with patch("src.tools.artifact_manager.subprocess.run"):
            manager = ArtifactManager(tmp_path, action="test")
            manager.start()
            assert manager.metadata.status == "running"

    def test_start_captures_environment(self, tmp_path: Any) -> None:
        """start() captures environment variables."""
        with patch("src.tools.artifact_manager.subprocess.run"):
            with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
                manager = ArtifactManager(tmp_path, action="test")
                manager.start()
                assert "TEST_VAR" in manager.manifest.environment


# =============================================================================
# Test add_ methods
# =============================================================================


class TestAddMethods:
    """Tests for add_* methods."""

    def test_add_flag(self, tmp_path: Any) -> None:
        """add_flag stores flag value."""
        with patch("src.tools.artifact_manager.subprocess.run"):
            manager = ArtifactManager(tmp_path, action="test")
            manager.add_flag("verbose", True)
            assert manager.manifest.flags["verbose"] is True

    def test_add_touched_file(self, tmp_path: Any) -> None:
        """add_touched_file tracks files."""
        with patch("src.tools.artifact_manager.subprocess.run"):
            manager = ArtifactManager(tmp_path, action="test")
            manager.add_touched_file("src/test.py")
            assert "src/test.py" in manager.metadata.touched_files

    def test_add_dependency(self, tmp_path: Any) -> None:
        """add_dependency tracks tool versions."""
        with patch("src.tools.artifact_manager.subprocess.run"):
            manager = ArtifactManager(tmp_path, action="test")
            manager.add_dependency("python", "3.12.0")
            assert manager.manifest.dependencies["python"] == "3.12.0"

    def test_add_artifact(self, tmp_path: Any) -> None:
        """add_artifact registers artifact."""
        with patch("src.tools.artifact_manager.subprocess.run"):
            manager = ArtifactManager(tmp_path, action="test")
            manager.add_artifact("logs", "/path/to/logs")
            assert manager.manifest.artifacts["logs"] == "/path/to/logs"


# =============================================================================
# Test capture_file_diff
# =============================================================================


class TestCaptureFileDiff:
    """Tests for capture_file_diff method."""

    def test_capture_file_diff_creates_file(self, tmp_path: Any) -> None:
        """capture_file_diff creates diff file."""
        with patch("src.tools.artifact_manager.subprocess.run"):
            manager = ArtifactManager(tmp_path, action="test")
            target = Path("test.py")
            manager.capture_file_diff(target, "before", "after")

            diff_file = manager.diffs_dir / "test.py.diff"
            assert diff_file.exists()

    def test_capture_file_diff_registers_artifact(self, tmp_path: Any) -> None:
        """capture_file_diff registers as artifact."""
        with patch("src.tools.artifact_manager.subprocess.run"):
            manager = ArtifactManager(tmp_path, action="test")
            target = Path("test.py")
            manager.capture_file_diff(target, "a", "b")

            assert "diff_test.py" in manager.manifest.artifacts


# =============================================================================
# Test complete() method
# =============================================================================


class TestComplete:
    """Tests for complete() method."""

    def test_complete_sets_status(self, tmp_path: Any) -> None:
        """complete() sets status to completed."""
        with patch("src.tools.artifact_manager.subprocess.run"):
            manager = ArtifactManager(tmp_path, action="test")
            manager.complete(0)
            assert manager.metadata.status == "completed"
            assert manager.metadata.exit_code == 0

    def test_complete_creates_manifest(self, tmp_path: Any) -> None:
        """complete() creates manifest.json."""
        with patch("src.tools.artifact_manager.subprocess.run"):
            manager = ArtifactManager(tmp_path, action="test")
            manager.complete()
            assert manager.manifest_path.exists()
            content = json.loads(manager.manifest_path.read_text())
            assert "metadata" in content

    def test_complete_creates_replay(self, tmp_path: Any) -> None:
        """complete() creates replay.sh."""
        with patch("src.tools.artifact_manager.subprocess.run"):
            manager = ArtifactManager(tmp_path, action="test")
            manager.complete()
            assert manager.replay_path.exists()
            content = manager.replay_path.read_text()
            assert "#!/bin/bash" in content

    def test_complete_creates_handoff(self, tmp_path: Any) -> None:
        """complete() creates handoff.md."""
        with patch("src.tools.artifact_manager.subprocess.run"):
            manager = ArtifactManager(tmp_path, action="test")
            manager.complete()
            assert manager.handoff_path.exists()
            content = manager.handoff_path.read_text()
            assert "# Handoff Report" in content


# =============================================================================
# Test failed() method
# =============================================================================


class TestFailed:
    """Tests for failed() method."""

    def test_failed_sets_status(self, tmp_path: Any) -> None:
        """failed() sets status to failed."""
        with patch("src.tools.artifact_manager.subprocess.run"):
            manager = ArtifactManager(tmp_path, action="test")
            manager.failed(1, "Error message")
            assert manager.metadata.status == "failed"
            assert manager.metadata.exit_code == 1

    def test_failed_creates_error_file(self, tmp_path: Any) -> None:
        """failed() creates error.txt."""
        with patch("src.tools.artifact_manager.subprocess.run"):
            manager = ArtifactManager(tmp_path, action="test")
            manager.failed(1, "Test error")
            error_file = manager.logs_dir / "error.txt"
            assert error_file.exists()
            assert "Test error" in error_file.read_text()


# =============================================================================
# Test summary() method
# =============================================================================


class TestSummary:
    """Tests for summary() method."""

    def test_summary_returns_dict(self, tmp_path: Any) -> None:
        """summary() returns dict with expected keys."""
        with patch("src.tools.artifact_manager.subprocess.run"):
            manager = ArtifactManager(tmp_path, action="test")
            summary = manager.summary()
            assert "run_id" in summary
            assert "action" in summary
            assert "status" in summary
            assert "manifest" in summary
            assert "handoff" in summary
            assert "replay" in summary

    def test_summary_values_correct(self, tmp_path: Any) -> None:
        """summary() returns correct values."""
        with patch("src.tools.artifact_manager.subprocess.run"):
            manager = ArtifactManager(tmp_path, action="analyze")
            summary = manager.summary()
            assert summary["action"] == "analyze"
            assert summary["run_id"] == manager.run_id


# =============================================================================
# Test edge cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_git_branch_failure(self, tmp_path: Any) -> None:
        """ArtifactManager handles git branch failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        with patch("src.tools.artifact_manager.subprocess.run", return_value=mock_result):
            manager = ArtifactManager(tmp_path, action="test")
            assert manager.metadata.branch == "unknown"

    def test_git_commit_failure(self, tmp_path: Any) -> None:
        """ArtifactManager handles git commit failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        with patch("src.tools.artifact_manager.subprocess.run", return_value=mock_result):
            manager = ArtifactManager(tmp_path, action="test")
            assert manager.metadata.commit == "unknown"

    def test_multiple_touched_files(self, tmp_path: Any) -> None:
        """ArtifactManager tracks multiple touched files."""
        with patch("src.tools.artifact_manager.subprocess.run"):
            manager = ArtifactManager(tmp_path, action="test")
            for i in range(15):
                manager.add_touched_file(f"file_{i}.py")
            assert len(manager.metadata.touched_files) == 15

    def test_model_from_env(self, tmp_path: Any) -> None:
        """ArtifactManager reads model from CURRENT_MODEL env."""
        with patch("src.tools.artifact_manager.subprocess.run"):
            with patch.dict(os.environ, {"CURRENT_MODEL": "claude-3"}):
                manager = ArtifactManager(tmp_path, action="test")
                assert manager.model == "claude-3"
