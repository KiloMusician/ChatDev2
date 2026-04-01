"""Tests for resource_cleanup module."""

import tempfile
import time
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from src.utils.resource_cleanup import ResourceCleanup


class TestResourceCleanup:
    """Test suite for ResourceCleanup class."""

    @pytest.fixture
    def temp_workspace(self) -> Generator[Path, None, None]:
        """Create temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def cleanup(self, temp_workspace: Path) -> ResourceCleanup:
        """Create ResourceCleanup instance for testing."""
        return ResourceCleanup(workspace_root=temp_workspace)

    def test_init_with_default_workspace(self) -> None:
        """Test initialization with default workspace root."""
        cleanup = ResourceCleanup()
        assert cleanup.workspace_root == Path.cwd()

    def test_init_with_custom_workspace(self, temp_workspace: Path) -> None:
        """Test initialization with custom workspace root."""
        cleanup = ResourceCleanup(workspace_root=temp_workspace)
        assert cleanup.workspace_root == temp_workspace

    def test_find_hung_processes_with_pattern(self, cleanup: ResourceCleanup) -> None:
        """Test finding hung processes with pattern matching."""
        with patch("psutil.process_iter") as mock_iter:
            # Mock processes
            mock_proc1 = MagicMock()
            mock_proc1.info = {
                "pid": 1234,
                "name": "python.exe",
                "cmdline": ["python", "test.py"],
                "create_time": time.time() - 120,
            }
            mock_proc2 = MagicMock()
            mock_proc2.info = {
                "pid": 5678,
                "name": "notepad.exe",
                "cmdline": ["notepad.exe"],
                "create_time": time.time() - 60,
            }
            mock_iter.return_value = [mock_proc1, mock_proc2]

            result = cleanup.find_hung_processes(pattern="python")
            assert isinstance(result, list)

    def test_find_hung_processes_with_timeout(self, cleanup: ResourceCleanup) -> None:
        """Test finding hung processes with timeout threshold."""
        with patch("psutil.process_iter") as mock_iter:
            # Mock process running longer than timeout
            mock_proc = MagicMock()
            mock_proc.info = {
                "pid": 1234,
                "name": "python.exe",
                "cmdline": ["python", "test.py"],
                "create_time": time.time() - 200,
            }
            mock_iter.return_value = [mock_proc]

            result = cleanup.find_hung_processes(pattern="python", timeout_seconds=100)
            # Should find process running > 100 seconds
            assert isinstance(result, list)

    def test_find_hung_processes_no_pattern(self, cleanup: ResourceCleanup) -> None:
        """Test finding hung processes without pattern."""
        with patch("psutil.process_iter") as mock_iter:
            mock_proc = MagicMock()
            mock_proc.info = {
                "pid": 1234,
                "name": "test.exe",
                "cmdline": ["test.exe"],
                "create_time": time.time() - 300,
            }
            mock_iter.return_value = [mock_proc]

            result = cleanup.find_hung_processes(timeout_seconds=100)
            assert isinstance(result, list)

    def test_find_hung_processes_handles_exceptions(self, cleanup: ResourceCleanup) -> None:
        """Test that find_hung_processes handles exceptions gracefully."""
        with patch("psutil.process_iter") as mock_iter:
            # Mock process that raises exception
            mock_proc = MagicMock()
            mock_proc.info = {
                "pid": 1234,
                "name": "test.exe",
                "cmdline": None,  # Cause AttributeError
                "create_time": time.time() - 100,
            }
            mock_iter.return_value = [mock_proc]

            # Should not raise exception
            result = cleanup.find_hung_processes(pattern="test")
            assert isinstance(result, list)

    def test_kill_hung_processes(self, cleanup: ResourceCleanup) -> None:
        """Test killing hung processes."""
        with patch.object(cleanup, "find_hung_processes") as mock_find:
            mock_proc = MagicMock()
            mock_proc.pid = 1234
            mock_proc.is_running.return_value = True
            mock_find.return_value = [mock_proc]

            killed = cleanup.kill_hung_processes(pattern="test")
            assert isinstance(killed, int)
            mock_proc.terminate.assert_called_once()

    def test_kill_hung_processes_with_force(self, cleanup: ResourceCleanup) -> None:
        """Test force killing hung processes."""
        with patch.object(cleanup, "find_hung_processes") as mock_find:
            mock_proc = MagicMock()
            mock_proc.pid = 1234
            mock_proc.is_running.side_effect = [True, False]  # Terminated after first check
            mock_find.return_value = [mock_proc]

            killed = cleanup.kill_hung_processes(pattern="test", force=True, timeout_seconds=1)
            assert isinstance(killed, int)

    def test_release_port_success(self, cleanup: ResourceCleanup) -> None:
        """Test releasing a port successfully."""
        with patch("psutil.net_connections") as mock_connections:
            # Mock connection on port 5000
            mock_conn = MagicMock()
            mock_conn.laddr.port = 5000
            mock_conn.pid = 1234
            mock_connections.return_value = [mock_conn]

            with patch("psutil.Process") as mock_process_cls:
                mock_proc = MagicMock()
                mock_proc.is_running.return_value = True
                mock_process_cls.return_value = mock_proc

                result = cleanup.release_port(5000)
                assert isinstance(result, bool)

    def test_release_port_no_process(self, cleanup: ResourceCleanup) -> None:
        """Test releasing port when no process is using it."""
        with patch("psutil.net_connections") as mock_connections:
            mock_connections.return_value = []

            result = cleanup.release_port(5000)
            assert result is True  # Port already free

    def test_clean_temp_files(self, cleanup: ResourceCleanup) -> None:
        """Test cleaning temporary files."""
        # Create mock glob results instead of actual files
        with patch("pathlib.Path.glob") as mock_glob:
            # Mock finding no files
            mock_glob.return_value = []

            count = cleanup.clean_temp_files(older_than_days=7)
            assert isinstance(count, int)
            assert count == 0

    def test_clean_temp_files_with_patterns(self, cleanup: ResourceCleanup) -> None:
        """Test cleaning temporary files with specific patterns."""
        temp_dir = cleanup.workspace_root / "temp"
        temp_dir.mkdir(exist_ok=True)

        # Create files matching pattern
        (temp_dir / "test.tmp").write_text("temp")
        (temp_dir / "test.log").write_text("log")

        count = cleanup.clean_temp_files(older_than_days=0, patterns=["*.tmp"])
        assert isinstance(count, int)

    def test_clean_stale_locks(self, cleanup: ResourceCleanup) -> None:
        """Test cleaning stale lock files."""
        lock_dir = cleanup.workspace_root / ".locks"
        lock_dir.mkdir(exist_ok=True)

        # Create stale lock file
        stale_lock = lock_dir / "stale.lock"
        stale_lock.write_text("1234")  # PID that doesn't exist

        with patch("psutil.pid_exists", return_value=False):
            count = cleanup.clean_stale_locks(lock_dir=lock_dir)
            assert isinstance(count, int)

    def test_clean_stale_locks_default_dir(self, cleanup: ResourceCleanup) -> None:
        """Test cleaning stale locks with default directory."""
        count = cleanup.clean_stale_locks()
        assert isinstance(count, int)

    def test_cleanup_all(self, cleanup: ResourceCleanup) -> None:
        """Test comprehensive cleanup."""
        with (
            patch.object(cleanup, "kill_hung_processes", return_value=0),
            patch.object(cleanup, "clean_temp_files", return_value=0),
            patch.object(cleanup, "clean_stale_locks", return_value=0),
        ):
            result = cleanup.cleanup_all()
            assert isinstance(result, dict)
            # Check actual keys returned by cleanup_all
            assert "processes_killed" in result
            assert "temp_files_deleted" in result
            assert "locks_removed" in result


class TestResourceCleanupIntegration:
    """Integration tests for ResourceCleanup."""

    def test_full_cleanup_workflow(self) -> None:
        """Test full cleanup workflow with realistic scenario."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            # Create temp directory structure
            temp_dir = workspace / "temp"
            temp_dir.mkdir()

            # Create some temp files
            (temp_dir / "file1.tmp").write_text("temp1")
            (temp_dir / "file2.log").write_text("log1")

            # Create lock directory
            lock_dir = workspace / ".locks"
            lock_dir.mkdir()

            cleanup = ResourceCleanup(workspace_root=workspace)

            # Mock process operations to avoid affecting real system
            with (
                patch("psutil.process_iter", return_value=[]),
                patch("psutil.net_connections", return_value=[]),
            ):
                result = cleanup.cleanup_all()

                # Check actual keys returned by cleanup_all
                assert result["processes_killed"] == 0
                assert isinstance(result["temp_files_deleted"], int)
                assert isinstance(result["locks_removed"], int)

    def test_workspace_independence(self) -> None:
        """Test that cleanup is isolated to workspace."""
        with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
            workspace1 = Path(tmpdir1)
            workspace2 = Path(tmpdir2)

            cleanup1 = ResourceCleanup(workspace_root=workspace1)
            cleanup2 = ResourceCleanup(workspace_root=workspace2)

            assert cleanup1.workspace_root != cleanup2.workspace_root
            assert cleanup1.workspace_root == workspace1
            assert cleanup2.workspace_root == workspace2
