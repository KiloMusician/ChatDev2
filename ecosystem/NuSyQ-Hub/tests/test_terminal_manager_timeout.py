"""Tests for TerminalManager (alias for EnhancedTerminalManager)."""

from pathlib import Path
from src.system.terminal_manager import TerminalManager


def test_terminal_manager_instantiation(tmp_path):
    """TerminalManager can be instantiated with a workspace root."""
    manager = TerminalManager(workspace_root=tmp_path)
    assert manager is not None
    assert manager.workspace_root == tmp_path


def test_terminal_manager_create_session(tmp_path):
    """create_session returns a UUID string."""
    manager = TerminalManager(workspace_root=tmp_path)
    session_id = manager.create_session()
    assert isinstance(session_id, str)
    assert len(session_id) > 0
    assert session_id in manager.active_sessions


def test_terminal_manager_get_session_summary(tmp_path):
    """get_session_summary returns a summary dict."""
    manager = TerminalManager(workspace_root=tmp_path)
    manager.create_session()
    summary = manager.get_session_summary()
    assert isinstance(summary, dict)


def test_terminal_manager_get_latest_output_empty(tmp_path):
    """get_latest_output returns a list for a new manager (no commands run)."""
    manager = TerminalManager(workspace_root=tmp_path)
    result = manager.get_latest_output()
    assert isinstance(result, list)
