"""Integration tests for agent service bridges."""

from pathlib import Path

import pytest
from src.agents.agent_orchestration_hub import AgentOrchestrationHub, ServiceCapability
from src.agents.bridges import (
    AgentRegistryBridge,
    ConsciousnessBridge,
    GuildBoardBridge,
    MultiAIOrchestrator,
    OllamaIntegrationBridge,
    QuantumProblemResolver,
    UnifiedAIOrchestrator,
)


@pytest.fixture
def hub():
    return AgentOrchestrationHub(
        root_path=Path.cwd(), enable_healing=True, enable_consciousness=True
    )


@pytest.fixture
def hub_with_service(hub):
    hub.register_service(
        service_id="bridge_service",
        name="Bridge Service",
        capabilities=[
            ServiceCapability(name="analysis", description="Bridge analysis", priority=7)
        ],
    )
    return hub


@pytest.mark.asyncio
async def test_unified_ai_orchestrator_bridge_routes_task(hub_with_service):
    bridge = UnifiedAIOrchestrator(hub=hub_with_service)
    result = await bridge.orchestrate_task(
        content="Review module health",
        task_type="analysis",
    )
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_multi_ai_orchestrator_bridge_routes_task(hub_with_service):
    bridge = MultiAIOrchestrator(hub=hub_with_service)
    result = await bridge.orchestrate_task(
        task_type="analysis",
        content="Assess integration points",
    )
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_consciousness_bridge_analysis(hub):
    bridge = ConsciousnessBridge(hub=hub)
    result = await bridge.analyze_task(
        task_type="analysis",
        description="Analyze system health",
    )
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_quantum_problem_resolver_bridge_simulated(hub):
    bridge = QuantumProblemResolver(hub=hub)
    result = await bridge.resolve_problem(
        problem_type="integration",
        problem_data={"description": "Resolve integration drift"},
        context={"simulate": True},
    )
    assert result["status"] == "success"
    assert result["simulated"] is True


@pytest.mark.asyncio
async def test_ollama_integration_bridge_simulated(hub):
    bridge = OllamaIntegrationBridge(hub=hub)
    result = await bridge.generate(
        prompt="Summarize system status",
        context={"simulate": True},
    )
    assert result["success"] is True
    assert result["status"] == "success"
    assert result["simulated"] is True


@pytest.mark.asyncio
async def test_ollama_integration_bridge_normalizes_status_only(hub_with_service):
    class _StatusOnlyHub:
        async def route_task(self, *_args, **_kwargs):
            return {"status": "success", "response": "ok"}

    bridge = OllamaIntegrationBridge(hub=_StatusOnlyHub())
    result = await bridge.generate(
        prompt="Summarize system status",
        context={"fallback_direct": False},
    )
    assert result["success"] is True
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_ollama_integration_bridge_invalid_hub_payload_contract():
    class _InvalidHub:
        async def route_task(self, *_args, **_kwargs):
            return "invalid"

    bridge = OllamaIntegrationBridge(hub=_InvalidHub())
    result = await bridge.generate(
        prompt="Summarize system status",
        context={"fallback_direct": False},
    )
    assert result["success"] is False
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_guild_board_bridge_post(tmp_path):
    bridge = GuildBoardBridge(state_dir=tmp_path / "guild")
    result = await bridge.post_update(
        agent_id="test-agent",
        message="Bridge status ok",
    )
    assert result["message"] == "Bridge status ok"


def test_agent_registry_bridge_registers(tmp_path, hub):
    registry_path = tmp_path / "agent_registry.json"
    bridge = AgentRegistryBridge(registry_path=registry_path, hub=hub)
    registered = bridge.register_agent(
        agent_id="bridge-agent",
        name="Bridge Agent",
        agent_type="test",
        capabilities=["analysis"],
    )
    assert registered is True
    assert bridge.get_agent("bridge-agent") is not None
    assert "bridge-agent" in hub._services
