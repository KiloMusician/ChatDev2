"""Tests for agent_registry_bridge.

Auto-generated smoke tests to establish basic coverage.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from src.agents.bridges.agent_registry_bridge import AgentRegistryBridge


def _make_bridge(tmp_path: Path) -> AgentRegistryBridge:
    """Create an isolated bridge with stub hub (avoids 17s hub init)."""
    stub_hub = MagicMock()
    stub_hub.register_agent = MagicMock(return_value=None)
    return AgentRegistryBridge(
        root_path=tmp_path,
        registry_path=tmp_path / "registry.json",
        hub=stub_hub,
    )


def test_agentregistrybridge_instantiation(tmp_path):
    """Test that AgentRegistryBridge can be instantiated."""
    bridge = _make_bridge(tmp_path)
    assert bridge is not None


def test_agentregistrybridge_register_agent(tmp_path):
    """Test AgentRegistryBridge.register_agent() registers and returns True."""
    bridge = _make_bridge(tmp_path)
    result = bridge.register_agent(
        agent_id="test-agent-001",
        name="Test Agent",
        agent_type="ollama",
        capabilities=["code_review", "analyze"],
        endpoint="http://localhost:11434",
    )
    assert result is True


def test_agentregistrybridge_get_agent(tmp_path):
    """Test AgentRegistryBridge.get_agent() returns registered agent."""
    bridge = _make_bridge(tmp_path)
    bridge.register_agent(
        agent_id="test-agent-002",
        name="Get Agent",
        agent_type="lmstudio",
        capabilities=["generate"],
    )
    agent = bridge.get_agent("test-agent-002")
    assert agent is not None
    assert agent.agent_id == "test-agent-002"
    assert agent.name == "Get Agent"


def test_agentregistrybridge_get_agent_missing(tmp_path):
    """Test get_agent returns None for unknown ID."""
    bridge = _make_bridge(tmp_path)
    result = bridge.get_agent("nonexistent-id")
    assert result is None


def test_agentregistrybridge_find_by_capability(tmp_path):
    """Test find_agents_by_capability returns matching agents."""
    bridge = _make_bridge(tmp_path)
    bridge.register_agent(
        agent_id="coder-01",
        name="Coder",
        agent_type="codex",
        capabilities=["code_review"],
    )
    bridge.register_agent(
        agent_id="writer-01",
        name="Writer",
        agent_type="ollama",
        capabilities=["summarize"],
    )
    coders = bridge.find_agents_by_capability("code_review")
    assert any(a.agent_id == "coder-01" for a in coders)
    assert not any(a.agent_id == "writer-01" for a in coders)


def test_agentregistrybridge_register_with_dict_capabilities(tmp_path):
    """register_agent normalizes dict capabilities (covers dict branch in _normalize_capabilities)."""
    from src.agents.bridges.agent_registry_bridge import AgentCapability

    bridge = _make_bridge(tmp_path)
    dict_cap = {"name": "debug", "description": "debug capability", "tags": ["dev"]}
    result = bridge.register_agent(
        agent_id="dict-cap-agent",
        name="Dict Cap Agent",
        agent_type="ollama",
        capabilities=[dict_cap],
    )
    assert result is True
    agent = bridge.get_agent("dict-cap-agent")
    assert agent is not None
    assert any(c.name == "debug" for c in agent.capabilities)


def test_agentregistrybridge_register_with_agentcapability_objects(tmp_path):
    """register_agent accepts AgentCapability objects (covers AgentCapability branch)."""
    from src.agents.bridges.agent_registry_bridge import AgentCapability

    bridge = _make_bridge(tmp_path)
    cap_obj = AgentCapability(name="embed", description="embedding", tags=["ml"])
    result = bridge.register_agent(
        agent_id="cap-obj-agent",
        name="Cap Obj Agent",
        agent_type="huggingface",
        capabilities=[cap_obj],
    )
    assert result is True


def test_agentregistrybridge_register_duplicate_returns_false(tmp_path):
    """register_agent with override=False returns False on duplicate ID."""
    bridge = _make_bridge(tmp_path)
    bridge.register_agent(
        agent_id="dup-agent",
        name="Dup Agent",
        agent_type="ollama",
        capabilities=["analyze"],
    )
    # Second registration without override should return False
    result = bridge.register_agent(
        agent_id="dup-agent",
        name="Dup Agent 2",
        agent_type="ollama",
        capabilities=["analyze"],
        override=False,
    )
    assert result is False
