"""Tests for autonomous_development_agent."""

from src.agents.autonomous_development_agent import AutonomousDevelopmentAgent


def test_autonomousdevelopmentagent_instantiation():
    """Test that AutonomousDevelopmentAgent can be instantiated."""
    instance = AutonomousDevelopmentAgent()
    assert instance is not None


def test_autonomousdevelopmentagent_get_status_structure():
    """Test get_status() returns expected top-level keys."""
    agent = AutonomousDevelopmentAgent()
    status = agent.get_status()
    assert isinstance(status, dict)
    for key in ("timestamp", "systems", "active_projects", "capabilities"):
        assert key in status


def test_autonomousdevelopmentagent_capabilities_is_dict_or_list():
    """Test that capabilities in status is a dict or list."""
    agent = AutonomousDevelopmentAgent()
    status = agent.get_status()
    assert isinstance(status["capabilities"], (dict, list))


def test_main():
    """Test _safe_agent_spawn returns a dict."""
    agent = AutonomousDevelopmentAgent()
    result = agent._safe_agent_spawn("analysis")
    assert isinstance(result, dict)
