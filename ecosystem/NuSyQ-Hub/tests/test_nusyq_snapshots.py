#!/usr/bin/env python3
"""
tests/test_nusyq_snapshots.py — Unit tests for snapshot module

Tests for Phase 1 extracted snapshot classes and functions.
"""

from pathlib import Path

import pytest
from scripts.nusyq_snapshots import (
    QuestSnapshot,
    RepoSnapshot,
    git_snapshot,
    is_git_repo,
    read_quest_log,
    run,
)


class TestIsGitRepo:
    """Tests for is_git_repo() function."""

    def test_is_git_repo_valid_repo(self, tmp_path: Path) -> None:
        """Test detection of valid git repository."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        assert is_git_repo(tmp_path) is True

    def test_is_git_repo_missing_git_dir(self, tmp_path: Path) -> None:
        """Test non-git directory."""
        assert is_git_repo(tmp_path) is False

    def test_is_git_repo_nonexistent_path(self, tmp_path: Path) -> None:
        """Test nonexistent path."""
        missing = tmp_path / "missing" / "repo"
        assert is_git_repo(missing) is False


class TestRunCommand:
    """Tests for run() subprocess function."""

    def test_run_success(self) -> None:
        """Test successful command execution."""
        rc, stdout, _stderr = run(["echo", "hello"])
        assert rc == 0
        assert "hello" in stdout

    def test_run_nonzero_exit(self) -> None:
        """Test command with nonzero exit code."""
        rc, _stdout, _stderr = run(["sh", "-c", "exit 42"])
        assert rc == 42

    def test_run_timeout(self) -> None:
        """Test command timeout handling."""
        rc, _stdout, stderr = run(["sh", "-c", "sleep 5"], timeout_s=1)
        assert rc != 0
        assert "TimeoutExpired" in stderr or "timed out" in stderr.lower()


class TestRepoSnapshot:
    """Tests for RepoSnapshot dataclass."""

    def test_repo_snapshot_creation(self, tmp_path: Path) -> None:
        """Test snapshot dataclass creation."""
        snap = RepoSnapshot(
            name="test-repo",
            path=tmp_path,
            is_present=True,
            is_git=False,
        )
        assert snap.name == "test-repo"
        assert snap.path == tmp_path
        assert snap.is_present is True
        assert snap.is_git is False
        assert snap.notes == []

    def test_repo_snapshot_with_notes(self, tmp_path: Path) -> None:
        """Test snapshot with notes."""
        snap = RepoSnapshot(
            name="test-repo",
            path=tmp_path,
            is_present=True,
            is_git=False,
            notes=["Note 1", "Note 2"],
        )
        assert len(snap.notes) == 2
        assert "Note 1" in snap.notes

    def test_repo_snapshot_to_markdown_not_present(self, tmp_path: Path) -> None:
        """Test markdown output for missing repo."""
        snap = RepoSnapshot(
            name="missing-repo",
            path=tmp_path / "missing",
            is_present=False,
            is_git=False,
        )
        md = snap.to_markdown()
        assert "missing-repo" in md
        assert "NOT FOUND" in md

    def test_repo_snapshot_to_markdown_with_values(self, tmp_path: Path) -> None:
        """Test markdown output with actual values."""
        snap = RepoSnapshot(
            name="real-repo",
            path=tmp_path,
            is_present=True,
            is_git=True,
            branch="main",
            head="abc123def456",
            dirty="clean",
            ahead_behind="0 0",
        )
        md = snap.to_markdown()
        assert "real-repo" in md
        assert "main" in md
        assert "abc123de" in md  # First 8 chars
        assert "clean" in md


class TestGitSnapshot:
    """Tests for git_snapshot() function."""

    def test_git_snapshot_missing_repo(self, tmp_path: Path) -> None:
        """Test snapshot of missing repo."""
        snap = git_snapshot("missing", tmp_path / "missing")
        assert snap.is_present is False
        assert snap.is_git is False
        assert len(snap.notes) > 0
        assert "not found" in snap.notes[0].lower()

    def test_git_snapshot_non_git_folder(self, tmp_path: Path) -> None:
        """Test snapshot of non-git folder."""
        snap = git_snapshot("non-git", tmp_path)
        assert snap.is_present is True
        assert snap.is_git is False
        assert len(snap.notes) > 0

    def test_git_snapshot_valid_repo(self, tmp_path: Path) -> None:
        """Test snapshot of valid git repo."""
        # Create minimal git repo structure
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Initialize minimal git config
        config = git_dir / "config"
        config.write_text("[core]\n\trepositoryformatversion = 0\n")

        # Create HEAD reference
        head_file = git_dir / "HEAD"
        head_file.write_text("ref: refs/heads/main\n")

        snap = git_snapshot("test-repo", tmp_path)
        assert snap.is_present is True
        assert snap.is_git is True
        # May have notes about git operations (expected)


class TestQuestSnapshot:
    """Tests for QuestSnapshot dataclass."""

    def test_quest_snapshot_creation(self) -> None:
        """Test snapshot dataclass creation."""
        snap = QuestSnapshot(source_path=None)
        assert snap.source_path is None
        assert snap.last_line == ""
        assert snap.last_nonempty_line == ""
        assert snap.notes == []

    def test_quest_snapshot_with_data(self, tmp_path: Path) -> None:
        """Test snapshot with data."""
        quest_file = tmp_path / "quest.jsonl"
        snap = QuestSnapshot(
            source_path=quest_file,
            last_line='{"quest": "test"}',
            notes=["Sample quest"],
        )
        assert snap.source_path == quest_file
        assert "test" in snap.last_line

    def test_quest_snapshot_to_markdown(self, tmp_path: Path) -> None:
        """Test markdown output."""
        snap = QuestSnapshot(
            source_path=tmp_path / "quest.jsonl",
            last_line='{"quest": "example"}',
            notes=["Note 1"],
        )
        md = snap.to_markdown()
        assert "quest.jsonl" in md
        assert "example" in md
        assert "Note 1" in md


class TestReadQuestLog:
    """Tests for read_quest_log() function."""

    def test_read_quest_log_missing_path(self, tmp_path: Path) -> None:
        """Test with missing path."""
        qs = read_quest_log(None)
        assert qs.source_path is None
        assert len(qs.notes) > 0

    def test_read_quest_log_missing_quest_log_file(self, tmp_path: Path) -> None:
        """Test with missing quest_log.jsonl."""
        qs = read_quest_log(tmp_path)
        assert qs.source_path is None
        assert len(qs.notes) > 0
        assert "not found" in qs.notes[0].lower()

    def test_read_quest_log_valid_jsonl(self, tmp_path: Path) -> None:
        """Test reading valid quest_log.jsonl."""
        # Create canonical directory structure
        quest_dir = tmp_path / "src" / "Rosetta_Quest_System"
        quest_dir.mkdir(parents=True)

        # Create quest_log.jsonl
        quest_file = quest_dir / "quest_log.jsonl"
        quest_file.write_text(
            '{"quest": "first", "status": "done"}\n{"quest": "second", "status": "in-progress"}\n'
        )

        qs = read_quest_log(tmp_path)
        assert qs.source_path == quest_file
        assert "second" in qs.last_nonempty_line
        assert "in-progress" in qs.last_nonempty_line

    def test_read_quest_log_with_empty_lines(self, tmp_path: Path) -> None:
        """Test reading quest_log with empty lines."""
        # Create canonical directory structure
        quest_dir = tmp_path / "src" / "Rosetta_Quest_System"
        quest_dir.mkdir(parents=True)

        # Create quest_log with empty lines
        quest_file = quest_dir / "quest_log.jsonl"
        quest_file.write_text(
            '{"quest": "first", "status": "done"}\n'
            "\n"
            "\n"
            '{"quest": "second", "status": "in-progress"}\n'
            "\n"
        )

        qs = read_quest_log(tmp_path)
        assert qs.source_path == quest_file
        # Should skip empty lines and find the real last entry
        assert "second" in qs.last_nonempty_line

    def test_read_quest_log_invalid_json(self, tmp_path: Path) -> None:
        """Test reading quest_log with non-JSON last line."""
        # Create canonical directory structure
        quest_dir = tmp_path / "src" / "Rosetta_Quest_System"
        quest_dir.mkdir(parents=True)

        # Create quest_log with invalid JSON
        quest_file = quest_dir / "quest_log.jsonl"
        quest_file.write_text('{"quest": "first", "status": "done"}\ninvalid json line\n')

        qs = read_quest_log(tmp_path)
        assert qs.source_path == quest_file
        assert "invalid" in qs.last_nonempty_line.lower()
        # Should note that last line is not valid JSON
        assert len(qs.notes) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
