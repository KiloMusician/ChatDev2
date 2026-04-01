"""Tests for agent_communication_hub."""

import pytest

from src.agents.agent_communication_hub import (
    Agent,
    AgentCommunicationHub,
    AgentRole,
    AgentStats,
    Message,
    MessageType,
    get_agent_hub,
)


def test_agentrole_values():
    assert AgentRole.CLAUDE in AgentRole
    assert AgentRole.OLLAMA in AgentRole


def test_messagetype_values():
    assert MessageType.REQUEST in MessageType
    assert MessageType.RESPONSE in MessageType


def test_agentstats_instantiation():
    stats = AgentStats()
    assert stats.level == 1
    assert stats.experience == 0


def test_agentstats_add_xp():
    stats = AgentStats()
    leveled_up = stats.add_xp(50)
    assert not leveled_up
    assert stats.experience == 50

    leveled_up = stats.add_xp(60)
    assert leveled_up
    assert stats.level == 2
    assert stats.experience == 110


def test_agentstats_add_xp_with_skill():
    stats = AgentStats()
    stats.add_xp(25, skill="coding")
    assert stats.specialization_xp.get("coding") == 25


def test_message_instantiation():
    msg = Message(
        id="msg-1",
        from_agent="ollama",
        to_agent="claude",
        message_type=MessageType.REQUEST,
        content={"prompt": "hello"},
    )
    assert msg.id == "msg-1"
    assert msg.to_agent == "claude"
    assert msg.thread_id is None


def test_agent_instantiation():
    agent = Agent(name="test-agent", role=AgentRole.OLLAMA)
    assert agent.name == "test-agent"
    assert agent.active is True
    assert agent.stats.level == 1


def test_agentcommunicationhub_instantiation(tmp_path):
    hub = AgentCommunicationHub(data_dir=tmp_path / "agents")
    assert hub is not None


def test_agentcommunicationhub_register_agent(tmp_path):
    hub = AgentCommunicationHub(data_dir=tmp_path / "agents")
    agent = hub.register_agent("my-agent", AgentRole.OLLAMA)
    assert agent.name == "my-agent"
    assert agent.role == AgentRole.OLLAMA
    assert "my-agent" in hub.agents


@pytest.mark.asyncio
async def test_agentcommunicationhub_send_message(tmp_path):
    hub = AgentCommunicationHub(data_dir=tmp_path / "agents")
    hub.register_agent("sender", AgentRole.OLLAMA)
    hub.register_agent("receiver", AgentRole.CLAUDE)
    msg = Message(
        id="m1",
        from_agent="sender",
        to_agent="receiver",
        message_type=MessageType.REQUEST,
        content={"task": "review"},
    )
    result = await hub.send_message("sender", msg)
    assert isinstance(result, bool)


def test_get_agent_hub():
    hub = get_agent_hub()
    assert hub is not None
    assert isinstance(hub, AgentCommunicationHub)
