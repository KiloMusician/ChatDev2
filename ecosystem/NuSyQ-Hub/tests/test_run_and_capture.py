"""Unit tests for run_and_capture.py output streaming and logging."""

from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.tools.run_and_capture import run_and_capture


def test_run_and_capture_creates_log_dir(tmp_path: Path) -> None:
    """run_and_capture should create logs directory if missing."""
    log_dir = tmp_path / "logs"
    assert not log_dir.exists()

    with patch("src.tools.run_and_capture.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.stdout = StringIO("output line\n")
        mock_proc.poll.return_value = 0
        mock_popen.return_value = mock_proc

        result = run_and_capture(["echo", "test"], cwd=tmp_path, log_dir=log_dir)

        assert log_dir.exists()
        assert result.exists()
        assert "run_capture_" in result.name


def test_run_and_capture_writes_header(tmp_path: Path) -> None:
    """run_and_capture should write command header to log file."""
    log_dir = tmp_path / "logs"

    with patch("src.tools.run_and_capture.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.stdout = StringIO("output\n")
        mock_proc.poll.return_value = 0
        mock_popen.return_value = mock_proc

        log_file = run_and_capture(["test", "cmd"], cwd=tmp_path, log_dir=log_dir)

        content = log_file.read_text()
        assert "# Command: test cmd" in content
        assert "# Cwd:" in content
        assert "# Started:" in content


def test_run_and_capture_captures_output(tmp_path: Path) -> None:
    """run_and_capture should capture process output to log file."""
    log_dir = tmp_path / "logs"

    with patch("src.tools.run_and_capture.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.stdout = StringIO("line 1\nline 2\nline 3\n")
        mock_proc.poll.return_value = 0
        mock_popen.return_value = mock_proc

        log_file = run_and_capture(["test"], cwd=tmp_path, log_dir=log_dir)

        content = log_file.read_text()
        assert "line 1" in content
        assert "line 2" in content
        assert "line 3" in content


def test_run_and_capture_default_log_dir(tmp_path: Path) -> None:
    """run_and_capture should use logs/ in cwd when log_dir not specified."""
    import os

    os.chdir(str(tmp_path))

    with patch("src.tools.run_and_capture.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.stdout = StringIO("test\n")
        mock_proc.poll.return_value = 0
        mock_popen.return_value = mock_proc

        log_file = run_and_capture(["test"])

        assert "logs" in str(log_file)
        assert log_file.parent.name == "logs"


def test_run_and_capture_returns_log_path(tmp_path: Path) -> None:
    """run_and_capture should return Path to log file."""
    log_dir = tmp_path / "logs"

    with patch("src.tools.run_and_capture.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.stdout = StringIO("")
        mock_proc.poll.return_value = 0
        mock_popen.return_value = mock_proc

        result = run_and_capture(["test"], log_dir=log_dir)

        assert isinstance(result, Path)
        assert result.suffix == ".log"
        assert "run_capture_" in result.name


def test_run_and_capture_sets_encoding_utf8(tmp_path: Path) -> None:
    """run_and_capture should set UTF-8 encoding for robustness."""
    log_dir = tmp_path / "logs"

    with patch("src.tools.run_and_capture.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.stdout = StringIO("")
        mock_proc.poll.return_value = 0
        mock_popen.return_value = mock_proc

        run_and_capture(["test"], log_dir=log_dir)

        # Verify Popen was called with UTF-8 encoding
        call_kwargs = mock_popen.call_args[1]
        assert call_kwargs.get("encoding") == "utf-8"
        assert call_kwargs.get("errors") == "replace"
