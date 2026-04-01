"""Tests for AgentContextManager (basic operations)."""

from pathlib import Path

from src.tools.agent_context_manager import AgentContextManager


def test_agent_context_manager_basic(tmp_path: Path):
    """Basic register/load/merge/save behavior for AgentContextManager."""
    repo = tmp_path / "repo"
    repo.mkdir()
    mgr = AgentContextManager(repo_root=repo, filename="contexts.json")

    # register and load
    mgr.register("kilo", {"files": ["a.py"]})
    loaded = mgr.load("kilo")
    assert loaded is not None
    assert loaded["files"] == ["a.py"]

    # merge
    merged = mgr.merge("kilo", {"extra": 1})
    assert merged["files"] == ["a.py"]
    assert merged["extra"] == 1

    # save and reload manager
    mgr.save()
    mgr2 = AgentContextManager(repo_root=repo, filename="contexts.json")
    assert "kilo" in mgr2.list()
