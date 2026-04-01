"""Tests for src/orchestration/bridges/orchestration_bridges.py.

All external calls are stubbed via unittest.mock. No network or subprocess
access occurs during these tests.
"""

import asyncio
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_hub(mocker=None):
    """Return a MagicMock that behaves like AgentOrchestrationHub."""
    from unittest.mock import AsyncMock, MagicMock

    hub = MagicMock()
    hub.route_task = AsyncMock(return_value={"status": "ok", "result": "mock"})
    hub.route_to_chatdev = AsyncMock(return_value={"status": "ok", "project": "mock"})
    hub.orchestrate_multi_agent_task = AsyncMock(return_value={"status": "ok", "votes": []})
    return hub


# ---------------------------------------------------------------------------
# __all__ / public API surface
# ---------------------------------------------------------------------------


def test_all_exports_present():
    from src.orchestration.bridges.orchestration_bridges import (
        AgentTaskRouterBridge,
        BridgeRegistry,
        ChatDevBridge,
        ConsciousnessBridge,
        ConsensusBridge,
        ContinueBridge,
        CopilotBridge,
        OllamaBridge,
        QuantumHealingBridge,
    )

    expected = {
        "AgentTaskRouterBridge",
        "BridgeRegistry",
        "ChatDevBridge",
        "ConsciousnessBridge",
        "ConsensusBridge",
        "ContinueBridge",
        "CopilotBridge",
        "OllamaBridge",
        "QuantumHealingBridge",
    }
    import src.orchestration.bridges.orchestration_bridges as mod

    assert expected.issubset(set(mod.__all__))


# ---------------------------------------------------------------------------
# BridgeRegistry — instantiation and registry mechanics
# ---------------------------------------------------------------------------


def test_bridge_registry_instantiation():
    from src.orchestration.bridges.orchestration_bridges import BridgeRegistry

    hub = _make_hub()
    registry = BridgeRegistry(hub)
    assert registry.hub is hub
    assert registry._bridges == {}


def test_bridge_registry_list_bridges():
    from src.orchestration.bridges.orchestration_bridges import BridgeRegistry

    registry = BridgeRegistry(_make_hub())
    bridges = registry.list_bridges()
    expected = {
        "ollama",
        "chatdev",
        "consciousness",
        "consensus",
        "continue",
        "copilot",
        "agent_router",
        "quantum_healing",
    }
    assert expected == set(bridges)


def test_bridge_registry_get_returns_correct_type():
    from src.orchestration.bridges.orchestration_bridges import BridgeRegistry, OllamaBridge

    registry = BridgeRegistry(_make_hub())
    bridge = registry.get("ollama")
    assert isinstance(bridge, OllamaBridge)


def test_bridge_registry_get_caches_instance():
    from src.orchestration.bridges.orchestration_bridges import BridgeRegistry

    registry = BridgeRegistry(_make_hub())
    b1 = registry.get("ollama")
    b2 = registry.get("ollama")
    assert b1 is b2


def test_bridge_registry_get_unknown_raises_key_error():
    from src.orchestration.bridges.orchestration_bridges import BridgeRegistry

    registry = BridgeRegistry(_make_hub())
    with pytest.raises(KeyError, match="Unknown bridge"):
        registry.get("nonexistent_bridge")


def test_bridge_registry_error_message_lists_available():
    from src.orchestration.bridges.orchestration_bridges import BridgeRegistry

    registry = BridgeRegistry(_make_hub())
    with pytest.raises(KeyError) as exc_info:
        registry.get("bad_name")
    assert "Available" in str(exc_info.value)


def test_bridge_registry_convenience_property_ollama():
    from src.orchestration.bridges.orchestration_bridges import BridgeRegistry, OllamaBridge

    registry = BridgeRegistry(_make_hub())
    assert isinstance(registry.ollama, OllamaBridge)


def test_bridge_registry_convenience_property_chatdev():
    from src.orchestration.bridges.orchestration_bridges import BridgeRegistry, ChatDevBridge

    registry = BridgeRegistry(_make_hub())
    assert isinstance(registry.chatdev, ChatDevBridge)


def test_bridge_registry_convenience_property_consciousness():
    from src.orchestration.bridges.orchestration_bridges import (
        BridgeRegistry,
        ConsciousnessBridge,
    )

    registry = BridgeRegistry(_make_hub())
    assert isinstance(registry.consciousness, ConsciousnessBridge)


def test_bridge_registry_convenience_property_consensus():
    from src.orchestration.bridges.orchestration_bridges import BridgeRegistry, ConsensusBridge

    registry = BridgeRegistry(_make_hub())
    assert isinstance(registry.consensus, ConsensusBridge)


def test_bridge_classes_class_var_is_dict():
    from src.orchestration.bridges.orchestration_bridges import BridgeRegistry

    assert isinstance(BridgeRegistry.BRIDGE_CLASSES, dict)
    assert len(BridgeRegistry.BRIDGE_CLASSES) == 8


# ---------------------------------------------------------------------------
# Individual bridge instantiation
# ---------------------------------------------------------------------------


def test_ollama_bridge_stores_hub():
    from src.orchestration.bridges.orchestration_bridges import OllamaBridge

    hub = _make_hub()
    bridge = OllamaBridge(hub)
    assert bridge.hub is hub


def test_chatdev_bridge_stores_hub():
    from src.orchestration.bridges.orchestration_bridges import ChatDevBridge

    hub = _make_hub()
    bridge = ChatDevBridge(hub)
    assert bridge.hub is hub


def test_consciousness_bridge_stores_hub():
    from src.orchestration.bridges.orchestration_bridges import ConsciousnessBridge

    hub = _make_hub()
    bridge = ConsciousnessBridge(hub)
    assert bridge.hub is hub


def test_consensus_bridge_stores_hub():
    from src.orchestration.bridges.orchestration_bridges import ConsensusBridge

    hub = _make_hub()
    bridge = ConsensusBridge(hub)
    assert bridge.hub is hub


def test_continue_bridge_stores_hub():
    from src.orchestration.bridges.orchestration_bridges import ContinueBridge

    hub = _make_hub()
    bridge = ContinueBridge(hub)
    assert bridge.hub is hub


def test_copilot_bridge_stores_hub():
    from src.orchestration.bridges.orchestration_bridges import CopilotBridge

    hub = _make_hub()
    bridge = CopilotBridge(hub)
    assert bridge.hub is hub


def test_agent_task_router_bridge_stores_hub():
    from src.orchestration.bridges.orchestration_bridges import AgentTaskRouterBridge

    hub = _make_hub()
    bridge = AgentTaskRouterBridge(hub)
    assert bridge.hub is hub


def test_quantum_healing_bridge_stores_hub():
    from src.orchestration.bridges.orchestration_bridges import QuantumHealingBridge

    hub = _make_hub()
    bridge = QuantumHealingBridge(hub)
    assert bridge.hub is hub


# ---------------------------------------------------------------------------
# Async method behaviour — arguments forwarded to hub
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ollama_bridge_analyze_passes_content():
    from src.orchestration.bridges.orchestration_bridges import OllamaBridge

    hub = _make_hub()
    bridge = OllamaBridge(hub)
    await bridge.analyze_with_ollama("hello world")
    hub.route_task.assert_awaited_once()
    call_kwargs = hub.route_task.call_args.kwargs
    assert call_kwargs["content"] == "hello world"
    assert call_kwargs["task_type"] == "analyze"
    assert call_kwargs["target_system"] == "ollama"


@pytest.mark.asyncio
async def test_ollama_bridge_analyze_injects_model_into_context():
    from src.orchestration.bridges.orchestration_bridges import OllamaBridge

    hub = _make_hub()
    bridge = OllamaBridge(hub)
    await bridge.analyze_with_ollama("text", model="llama3")
    call_kwargs = hub.route_task.call_args.kwargs
    assert call_kwargs["context"]["model"] == "llama3"


@pytest.mark.asyncio
async def test_ollama_bridge_analyze_preserves_extra_context():
    from src.orchestration.bridges.orchestration_bridges import OllamaBridge

    hub = _make_hub()
    bridge = OllamaBridge(hub)
    await bridge.analyze_with_ollama("text", context={"extra": "value"})
    call_kwargs = hub.route_task.call_args.kwargs
    assert call_kwargs["context"]["extra"] == "value"


@pytest.mark.asyncio
async def test_ollama_bridge_code_analysis_sets_type():
    from src.orchestration.bridges.orchestration_bridges import OllamaBridge

    hub = _make_hub()
    bridge = OllamaBridge(hub)
    await bridge.code_analysis("def foo(): pass")
    call_kwargs = hub.route_task.call_args.kwargs
    assert call_kwargs["context"]["type"] == "code"


@pytest.mark.asyncio
async def test_ollama_bridge_semantic_search_sets_type():
    from src.orchestration.bridges.orchestration_bridges import OllamaBridge

    hub = _make_hub()
    bridge = OllamaBridge(hub)
    await bridge.semantic_search("find me X")
    call_kwargs = hub.route_task.call_args.kwargs
    assert call_kwargs["context"]["type"] == "semantic"


@pytest.mark.asyncio
async def test_chatdev_bridge_generate_calls_route_to_chatdev():
    from src.orchestration.bridges.orchestration_bridges import ChatDevBridge

    hub = _make_hub()
    bridge = ChatDevBridge(hub)
    await bridge.generate_with_chatdev("build a calculator", project_name="calc")
    hub.route_to_chatdev.assert_awaited_once()
    kwargs = hub.route_to_chatdev.call_args.kwargs
    assert kwargs["task"] == "build a calculator"
    assert kwargs["project_name"] == "calc"


@pytest.mark.asyncio
async def test_chatdev_bridge_generate_default_model():
    from src.orchestration.bridges.orchestration_bridges import ChatDevBridge

    hub = _make_hub()
    bridge = ChatDevBridge(hub)
    await bridge.generate_with_chatdev("task")
    kwargs = hub.route_to_chatdev.call_args.kwargs
    assert kwargs["model"] == "gpt-3.5-turbo"


@pytest.mark.asyncio
async def test_chatdev_bridge_multi_agent_uses_orchestrate():
    from src.orchestration.bridges.orchestration_bridges import ChatDevBridge

    hub = _make_hub()
    bridge = ChatDevBridge(hub)
    await bridge.orchestrate_multi_agent_development("design a system")
    hub.orchestrate_multi_agent_task.assert_awaited_once()
    kwargs = hub.orchestrate_multi_agent_task.call_args.kwargs
    assert kwargs["task_type"] == "generate"
    assert "chatdev" in kwargs["systems"]


@pytest.mark.asyncio
async def test_consciousness_bridge_sets_consciousness_level():
    from src.orchestration.bridges.orchestration_bridges import ConsciousnessBridge

    hub = _make_hub()
    bridge = ConsciousnessBridge(hub)
    await bridge.consciousness_aware_route("sense data", consciousness_level=5)
    call_kwargs = hub.route_task.call_args.kwargs
    assert call_kwargs["context"]["consciousness_level"] == 5
    assert call_kwargs["task_type"] == "consciousness"


@pytest.mark.asyncio
async def test_consciousness_bridge_default_consciousness_level():
    from src.orchestration.bridges.orchestration_bridges import ConsciousnessBridge

    hub = _make_hub()
    bridge = ConsciousnessBridge(hub)
    await bridge.consciousness_aware_route("test")
    call_kwargs = hub.route_task.call_args.kwargs
    assert call_kwargs["context"]["consciousness_level"] == 1


@pytest.mark.asyncio
async def test_consensus_bridge_uses_orchestrate_multi_agent():
    from src.orchestration.bridges.orchestration_bridges import ConsensusBridge

    hub = _make_hub()
    bridge = ConsensusBridge(hub)
    await bridge.request_consensus("should we refactor?", voters=["ollama", "claude"])
    hub.orchestrate_multi_agent_task.assert_awaited_once()
    kwargs = hub.orchestrate_multi_agent_task.call_args.kwargs
    assert kwargs["task_type"] == "vote"
    assert set(kwargs["systems"]) == {"ollama", "claude"}


@pytest.mark.asyncio
async def test_consensus_bridge_default_voters():
    from src.orchestration.bridges.orchestration_bridges import ConsensusBridge

    hub = _make_hub()
    bridge = ConsensusBridge(hub)
    await bridge.request_consensus("vote on X")
    kwargs = hub.orchestrate_multi_agent_task.call_args.kwargs
    assert "ollama" in kwargs["systems"]
    assert "claude" in kwargs["systems"]


@pytest.mark.asyncio
async def test_continue_bridge_sets_task_type_complete():
    from src.orchestration.bridges.orchestration_bridges import ContinueBridge

    hub = _make_hub()
    bridge = ContinueBridge(hub)
    await bridge.continue_completion("def foo(")
    call_kwargs = hub.route_task.call_args.kwargs
    assert call_kwargs["task_type"] == "complete"
    assert call_kwargs["target_system"] == "continue"


@pytest.mark.asyncio
async def test_copilot_bridge_sets_task_type_suggest():
    from src.orchestration.bridges.orchestration_bridges import CopilotBridge

    hub = _make_hub()
    bridge = CopilotBridge(hub)
    await bridge.copilot_suggest("# write a sort function")
    call_kwargs = hub.route_task.call_args.kwargs
    assert call_kwargs["task_type"] == "suggest"
    assert call_kwargs["target_system"] == "copilot"


@pytest.mark.asyncio
async def test_agent_task_router_bridge_routes_to_agent():
    from src.orchestration.bridges.orchestration_bridges import AgentTaskRouterBridge

    hub = _make_hub()
    bridge = AgentTaskRouterBridge(hub)
    await bridge.route_to_agent("do something", agent_id="ollama")
    call_kwargs = hub.route_task.call_args.kwargs
    assert call_kwargs["target_system"] == "ollama"
    assert call_kwargs["task_type"] == "execute"
    assert call_kwargs["content"] == "do something"


@pytest.mark.asyncio
async def test_quantum_healing_bridge_converts_error_to_str():
    from src.orchestration.bridges.orchestration_bridges import QuantumHealingBridge

    hub = _make_hub()
    bridge = QuantumHealingBridge(hub)
    error_ctx = {"error": "NullPointerException", "line": 42}
    await bridge.quantum_heal(error_ctx)
    call_kwargs = hub.route_task.call_args.kwargs
    assert call_kwargs["task_type"] == "heal"
    assert call_kwargs["target_system"] == "quantum"
    assert call_kwargs["context"] == error_ctx
    # content must be the string representation of the dict
    assert "NullPointerException" in call_kwargs["content"]


# ---------------------------------------------------------------------------
# BridgeRegistry — all 8 bridge types can be retrieved
# ---------------------------------------------------------------------------


def test_registry_can_get_all_bridge_names():
    from src.orchestration.bridges.orchestration_bridges import BridgeRegistry

    hub = _make_hub()
    registry = BridgeRegistry(hub)
    names = registry.list_bridges()
    for name in names:
        bridge = registry.get(name)
        assert bridge is not None
        assert bridge.hub is hub


def test_registry_lazily_creates_bridges():
    from src.orchestration.bridges.orchestration_bridges import BridgeRegistry

    hub = _make_hub()
    registry = BridgeRegistry(hub)
    assert len(registry._bridges) == 0
    registry.get("ollama")
    assert len(registry._bridges) == 1
    registry.get("chatdev")
    assert len(registry._bridges) == 2


def test_registry_separate_instances_for_different_names():
    from src.orchestration.bridges.orchestration_bridges import BridgeRegistry

    hub = _make_hub()
    registry = BridgeRegistry(hub)
    ollama = registry.get("ollama")
    chatdev = registry.get("chatdev")
    assert ollama is not chatdev
