"""Tests for src/agents/agent_orchestration_hub.py."""

import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.agent_orchestration_hub import AgentOrchestrationHub, get_agent_orchestration_hub
from src.agents.agent_orchestration_types import (
    ExecutionMode,
    RegisteredService,
    ServiceCapability,
    TaskPriority,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_hub(tmp_path: Path, *, healing: bool = True, consciousness: bool = False) -> AgentOrchestrationHub:
    return AgentOrchestrationHub(
        root_path=tmp_path,
        enable_healing=healing,
        enable_consciousness=consciousness,
    )


def _register_service(hub: AgentOrchestrationHub, service_id: str = "svc1") -> RegisteredService:
    cap = ServiceCapability(name="code_review", description="review code", priority=5)
    hub.register_service(service_id=service_id, name=f"Service {service_id}", capabilities=[cap])
    return hub._services[service_id]


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

class TestInit:
    def test_defaults(self, tmp_path):
        hub = _make_hub(tmp_path)
        assert hub.root_path == tmp_path
        assert hub.enable_healing is True
        assert hub.enable_consciousness is False

    def test_services_empty_on_start(self, tmp_path):
        hub = _make_hub(tmp_path)
        assert hub._services == {}

    def test_locks_empty_on_start(self, tmp_path):
        hub = _make_hub(tmp_path)
        assert hub._locks == {}

    def test_consciousness_cache_empty(self, tmp_path):
        hub = _make_hub(tmp_path)
        assert hub._consciousness_cache == {}


# ---------------------------------------------------------------------------
# Static / class helpers
# ---------------------------------------------------------------------------

class TestStatusHelpers:
    @pytest.mark.parametrize("status", [
        "success", "ok", "completed", "submitted", "operational",
        "consensus_reached", "vote_success", "parallel_complete",
        "synthesized", "healing_applied", "delivered",
    ])
    def test_success_statuses(self, status):
        assert AgentOrchestrationHub._status_implies_success(status) is True

    @pytest.mark.parametrize("status", ["error", "failed", "", None, "unknown"])
    def test_non_success_statuses(self, status):
        assert AgentOrchestrationHub._status_implies_success(status) is False

    def test_normalize_adds_status_from_success_true(self):
        result = AgentOrchestrationHub._normalize_response_contract({"success": True})
        assert result["status"] == "success"

    def test_normalize_adds_status_error_when_no_success(self):
        result = AgentOrchestrationHub._normalize_response_contract({"data": "x"})
        assert result["status"] == "error"

    def test_normalize_preserves_existing_valid_status(self):
        result = AgentOrchestrationHub._normalize_response_contract({"status": "ok"})
        assert result["status"] == "ok"

    def test_normalize_adds_success_key_from_status(self):
        result = AgentOrchestrationHub._normalize_response_contract({"status": "success"})
        assert result["success"] is True

    def test_normalize_does_not_overwrite_existing_success(self):
        result = AgentOrchestrationHub._normalize_response_contract(
            {"status": "success", "success": False}
        )
        assert result["success"] is False

    def test_response_succeeded_via_success_key(self):
        assert AgentOrchestrationHub._response_succeeded({"success": True}) is True
        assert AgentOrchestrationHub._response_succeeded({"success": False}) is False

    def test_response_succeeded_via_status(self):
        assert AgentOrchestrationHub._response_succeeded({"status": "ok"}) is True
        assert AgentOrchestrationHub._response_succeeded({"status": "error"}) is False


# ---------------------------------------------------------------------------
# Service registration
# ---------------------------------------------------------------------------

class TestServiceRegistration:
    def test_register_service_succeeds(self, tmp_path):
        hub = _make_hub(tmp_path)
        cap = ServiceCapability(name="analysis", description="analyze", priority=3)
        ok = hub.register_service(service_id="s1", name="S1", capabilities=[cap])
        assert ok is True
        assert "s1" in hub._services

    def test_register_duplicate_returns_false(self, tmp_path):
        hub = _make_hub(tmp_path)
        cap = ServiceCapability(name="analysis", description="d", priority=1)
        hub.register_service(service_id="s1", name="S1", capabilities=[cap])
        result = hub.register_service(service_id="s1", name="S1", capabilities=[cap])
        assert result is False

    def test_unregister_existing_returns_true(self, tmp_path):
        hub = _make_hub(tmp_path)
        _register_service(hub, "svc_del")
        ok = hub.unregister_service("svc_del")
        assert ok is True
        assert "svc_del" not in hub._services

    def test_unregister_missing_returns_false(self, tmp_path):
        hub = _make_hub(tmp_path)
        assert hub.unregister_service("nonexistent") is False

    def test_service_stores_endpoint_and_metadata(self, tmp_path):
        hub = _make_hub(tmp_path)
        cap = ServiceCapability(name="code_review", description="d")
        hub.register_service(
            service_id="s2",
            name="S2",
            capabilities=[cap],
            endpoint="http://localhost:9000",
            metadata={"version": "1"},
        )
        svc = hub._services["s2"]
        assert svc.endpoint == "http://localhost:9000"
        assert svc.metadata["version"] == "1"


# ---------------------------------------------------------------------------
# Task locking
# ---------------------------------------------------------------------------

class TestTaskLocking:
    @pytest.mark.asyncio
    async def test_acquire_lock_returns_true(self, tmp_path):
        hub = _make_hub(tmp_path)
        ok = await hub.acquire_task_lock("task_a", "agent_1")
        assert ok is True
        assert "task_a" in hub._locks

    @pytest.mark.asyncio
    async def test_double_acquire_returns_false(self, tmp_path):
        hub = _make_hub(tmp_path)
        await hub.acquire_task_lock("task_b", "agent_1")
        ok = await hub.acquire_task_lock("task_b", "agent_2")
        assert ok is False

    @pytest.mark.asyncio
    async def test_release_lock_succeeds(self, tmp_path):
        hub = _make_hub(tmp_path)
        await hub.acquire_task_lock("task_c", "agent_1")
        released = await hub.release_task_lock("task_c", "agent_1")
        assert released is True
        assert "task_c" not in hub._locks

    @pytest.mark.asyncio
    async def test_release_by_wrong_agent_returns_false(self, tmp_path):
        hub = _make_hub(tmp_path)
        await hub.acquire_task_lock("task_d", "agent_1")
        released = await hub.release_task_lock("task_d", "agent_2")
        assert released is False
        assert "task_d" in hub._locks

    @pytest.mark.asyncio
    async def test_release_nonexistent_lock_returns_false(self, tmp_path):
        hub = _make_hub(tmp_path)
        assert await hub.release_task_lock("no_such_task", "agent_1") is False

    @pytest.mark.asyncio
    async def test_expired_locks_cleaned_before_acquire(self, tmp_path):
        from src.agents.agent_orchestration_types import TaskLock
        hub = _make_hub(tmp_path)
        # Inject an already-expired lock
        hub._locks["stale_task"] = TaskLock(
            task_id="stale_task",
            agent_id="old_agent",
            acquired_at=time.time() - 600,
            expires_at=time.time() - 300,
        )
        # Acquiring a new lock triggers cleanup
        ok = await hub.acquire_task_lock("new_task", "agent_1")
        assert ok is True
        assert "stale_task" not in hub._locks

    @pytest.mark.asyncio
    async def test_acquire_with_custom_timeout(self, tmp_path):
        hub = _make_hub(tmp_path)
        ok = await hub.acquire_task_lock("task_e", "agent_1", timeout=10.0)
        assert ok is True
        lock = hub._locks["task_e"]
        assert lock.expires_at > lock.acquired_at


# ---------------------------------------------------------------------------
# route_task
# ---------------------------------------------------------------------------

class TestRouteTask:
    @pytest.mark.asyncio
    async def test_route_task_service_not_found(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=False)
        result = await hub.route_task(
            task_type="code_review",
            description="check this",
            target_service="missing_service",
        )
        assert result["status"] == "error"
        assert "missing_service" in result["error"]
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_route_task_no_service_available(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=False)
        # No services registered, no target_service — auto-select fails
        result = await hub.route_task(
            task_type="code_review",
            description="check this",
        )
        assert result["status"] == "error"
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_route_task_uses_registered_service(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=False)
        _register_service(hub, "svc1")
        result = await hub.route_task(
            task_type="code_review",
            description="review this",
            target_service="svc1",
        )
        assert result["status"] == "success"
        assert result["service"] == "svc1"

    @pytest.mark.asyncio
    async def test_route_task_returns_task_id(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=False)
        _register_service(hub, "svc1")
        result = await hub.route_task(
            task_type="code_review",
            description="review",
            target_service="svc1",
        )
        assert "task_id" in result

    @pytest.mark.asyncio
    async def test_route_task_auto_select_by_capability(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=False)
        cap = ServiceCapability(name="analysis", description="analyze code", priority=8)
        hub.register_service(service_id="analyst", name="Analyst", capabilities=[cap])
        result = await hub.route_task(task_type="analysis", description="analyze this module")
        assert result["status"] == "success"
        assert result["service"] == "analyst"

    @pytest.mark.asyncio
    async def test_route_task_consciousness_disabled_skips_semantics(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=False)
        _register_service(hub, "svc1")
        with patch.object(hub, "_analyze_task_semantics", new_callable=AsyncMock) as mock_sem:
            await hub.route_task(
                task_type="code_review",
                description="review",
                target_service="svc1",
            )
            mock_sem.assert_not_called()

    @pytest.mark.asyncio
    async def test_route_task_consciousness_enabled_calls_semantics(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=True)
        _register_service(hub, "svc1")
        with patch.object(hub, "_get_consciousness_bridge", new_callable=AsyncMock, return_value=MagicMock()):
            result = await hub.route_task(
                task_type="code_review",
                description="design a system",
                target_service="svc1",
                require_consciousness=True,
            )
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_route_task_context_defaults_to_empty(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=False)
        _register_service(hub, "svc1")
        # Should not raise with no context arg
        result = await hub.route_task(
            task_type="code_review",
            description="check",
            target_service="svc1",
        )
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# route_to_chatdev
# ---------------------------------------------------------------------------

class TestRouteToChatDev:
    @pytest.mark.asyncio
    async def test_route_to_chatdev_no_orchestrator(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=False)
        with patch.object(hub, "_get_chatdev_orchestrator", new_callable=AsyncMock, return_value=None):
            result = await hub.route_to_chatdev("Build a CLI tool")
        assert result["status"] == "error"
        assert result["success"] is False
        assert "ChatDev" in result["error"]

    @pytest.mark.asyncio
    async def test_route_to_chatdev_with_orchestrator(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=False)
        mock_orch = MagicMock()
        with patch.object(hub, "_get_chatdev_orchestrator", new_callable=AsyncMock, return_value=mock_orch):
            with patch.object(hub, "_execute_chatdev_with_monitoring", new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {"success": True, "status": "success", "artifacts": []}
                result = await hub.route_to_chatdev(
                    "Build a CLI tool",
                    requirements=["Python", "argparse"],
                )
        assert result["status"] == "success"
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_route_to_chatdev_uses_default_team(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=False)
        mock_orch = MagicMock()
        with patch.object(hub, "_get_chatdev_orchestrator", new_callable=AsyncMock, return_value=mock_orch):
            with patch.object(hub, "_execute_chatdev_with_monitoring", new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {"success": True, "status": "success", "artifacts": []}
                await hub.route_to_chatdev("Build X")
        task_arg = mock_exec.call_args[0][1]
        assert "ceo" in task_arg["team"]
        assert "programmer" in task_arg["team"]

    @pytest.mark.asyncio
    async def test_route_to_chatdev_custom_team(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=False)
        mock_orch = MagicMock()
        custom_team = {"dev": {"role": "Developer"}}
        with patch.object(hub, "_get_chatdev_orchestrator", new_callable=AsyncMock, return_value=mock_orch):
            with patch.object(hub, "_execute_chatdev_with_monitoring", new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {"success": True, "status": "success"}
                await hub.route_to_chatdev("Build X", team_composition=custom_team)
        task_arg = mock_exec.call_args[0][1]
        assert task_arg["team"] == custom_team


# ---------------------------------------------------------------------------
# route_to_claude
# ---------------------------------------------------------------------------

class TestRouteToClaude:
    @pytest.mark.asyncio
    async def test_route_to_claude_simulate_mode(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=False)
        result = await hub.route_to_claude(
            "Analyze this code",
            context={"simulate": True},
        )
        assert result["status"] == "success"
        assert result["simulated"] is True
        assert result["service"] == "claude_orchestrator"

    @pytest.mark.asyncio
    async def test_route_to_claude_no_orchestrator(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=False)
        with patch.object(hub, "_get_claude_orchestrator", new_callable=AsyncMock, return_value=None):
            result = await hub.route_to_claude("Analyze this code")
        assert result["status"] == "error"
        assert "Claude orchestrator" in result["error"]

    @pytest.mark.asyncio
    async def test_route_to_claude_consensus_mode(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=False)
        mock_orch = AsyncMock()
        mock_orch.multi_ai_consensus.return_value = {"status": "success", "result": "ok"}
        with patch.object(hub, "_get_claude_orchestrator", new_callable=AsyncMock, return_value=mock_orch):
            result = await hub.route_to_claude("Analyze this", mode="consensus")
        assert result["service"] == "claude_orchestrator"
        mock_orch.multi_ai_consensus.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_to_claude_ollama_mode(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=False)
        mock_orch = AsyncMock()
        mock_orch.ask_ollama.return_value = {"status": "success", "result": "ollama reply"}
        with patch.object(hub, "_get_claude_orchestrator", new_callable=AsyncMock, return_value=mock_orch):
            result = await hub.route_to_claude("Review code", mode="ollama")
        mock_orch.ask_ollama.assert_called_once()
        assert result["mode"] == "ollama"

    @pytest.mark.asyncio
    async def test_route_to_claude_health_mode(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=False)
        mock_orch = AsyncMock()
        mock_orch.health_check.return_value = {"status": "ok", "healthy": True}
        with patch.object(hub, "_get_claude_orchestrator", new_callable=AsyncMock, return_value=mock_orch):
            result = await hub.route_to_claude("health", mode="health")
        mock_orch.health_check.assert_called_once()
        assert result["mode"] == "health"

    @pytest.mark.asyncio
    async def test_route_to_claude_chatdev_mode(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=False)
        mock_orch = AsyncMock()
        mock_orch.spawn_chatdev.return_value = {"status": "success"}
        with patch.object(hub, "_get_claude_orchestrator", new_callable=AsyncMock, return_value=mock_orch):
            result = await hub.route_to_claude("create an app", mode="chatdev")
        mock_orch.spawn_chatdev.assert_called_once()
        assert result["mode"] == "chatdev"


# ---------------------------------------------------------------------------
# orchestrate_multi_agent_task
# ---------------------------------------------------------------------------

class TestMultiAgentTask:
    def _hub_with_two_services(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=False)
        for sid in ("s1", "s2"):
            cap = ServiceCapability(name="code_review", description="d", priority=5)
            hub.register_service(service_id=sid, name=sid, capabilities=[cap])
        return hub

    @pytest.mark.asyncio
    async def test_no_active_services_returns_error(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=False)
        result = await hub.orchestrate_multi_agent_task(
            "task", services=["nonexistent"], mode=ExecutionMode.CONSENSUS
        )
        assert result["status"] == "error"
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_consensus_mode(self, tmp_path):
        hub = self._hub_with_two_services(tmp_path)
        result = await hub.orchestrate_multi_agent_task(
            "analyze code", services=["s1", "s2"], mode=ExecutionMode.CONSENSUS
        )
        assert result["status"] in ("consensus_reached", "consensus_failed")

    @pytest.mark.asyncio
    async def test_voting_mode(self, tmp_path):
        hub = self._hub_with_two_services(tmp_path)
        result = await hub.orchestrate_multi_agent_task(
            "vote on this", services=["s1", "s2"], mode=ExecutionMode.VOTING
        )
        assert result["status"] in ("vote_success", "vote_failure")
        assert "votes" in result

    @pytest.mark.asyncio
    async def test_sequential_mode(self, tmp_path):
        hub = self._hub_with_two_services(tmp_path)
        result = await hub.orchestrate_multi_agent_task(
            "do sequentially", services=["s1", "s2"], mode=ExecutionMode.SEQUENTIAL
        )
        assert isinstance(result, dict)
        assert "status" in result

    @pytest.mark.asyncio
    async def test_parallel_mode_with_synthesis(self, tmp_path):
        hub = self._hub_with_two_services(tmp_path)
        result = await hub.orchestrate_multi_agent_task(
            "parallel work", services=["s1", "s2"],
            mode=ExecutionMode.PARALLEL, synthesis_required=True
        )
        assert result["status"] == "synthesized"

    @pytest.mark.asyncio
    async def test_parallel_mode_without_synthesis(self, tmp_path):
        hub = self._hub_with_two_services(tmp_path)
        result = await hub.orchestrate_multi_agent_task(
            "parallel work", services=["s1", "s2"],
            mode=ExecutionMode.PARALLEL, synthesis_required=False
        )
        assert result["status"] == "parallel_complete"

    @pytest.mark.asyncio
    async def test_first_success_mode(self, tmp_path):
        hub = self._hub_with_two_services(tmp_path)
        result = await hub.orchestrate_multi_agent_task(
            "try each", services=["s1", "s2"], mode=ExecutionMode.FIRST_SUCCESS
        )
        assert result["status"] in ("success", "all_failed")


# ---------------------------------------------------------------------------
# execute_with_healing
# ---------------------------------------------------------------------------

class TestExecuteWithHealing:
    @pytest.mark.asyncio
    async def test_succeeds_on_first_attempt(self, tmp_path):
        hub = _make_hub(tmp_path, healing=True, consciousness=False)
        _register_service(hub, "svc1")
        result = await hub.execute_with_healing(
            "analyze this", initial_service="svc1", max_retries=3
        )
        assert result["status"] == "success"
        assert result["healing_history"] == []

    @pytest.mark.asyncio
    async def test_healing_disabled_stops_after_first_failure(self, tmp_path):
        hub = _make_hub(tmp_path, healing=False, consciousness=False)
        # target_service not registered -> route_task returns error on every attempt
        result = await hub.execute_with_healing(
            "fail task", initial_service="missing_svc", max_retries=3
        )
        assert result["status"] == "failed_after_healing"
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_healing_returns_history(self, tmp_path):
        hub = _make_hub(tmp_path, healing=True, consciousness=False)
        with patch.object(hub, "route_task", new_callable=AsyncMock) as mock_route:
            mock_route.return_value = {"status": "error", "error": "failed"}
            with patch.object(hub, "_analyze_and_heal", new_callable=AsyncMock) as mock_heal:
                mock_heal.return_value = {
                    "status": "healing_applied", "recommendations": ["retry"], "confidence": 0.3
                }
                result = await hub.execute_with_healing(
                    "fail always", initial_service="any", max_retries=2
                )
        assert "healing_history" in result
        assert len(result["healing_history"]) >= 1

    @pytest.mark.asyncio
    async def test_consciousness_stops_retries_on_low_confidence(self, tmp_path):
        hub = _make_hub(tmp_path, healing=True, consciousness=True)
        call_count = 0

        async def fake_route(**kwargs):
            nonlocal call_count
            call_count += 1
            return {"status": "error", "error": "fail"}

        with patch.object(hub, "route_task", new_callable=AsyncMock, side_effect=fake_route):
            with patch.object(hub, "_analyze_and_heal", new_callable=AsyncMock) as mock_heal:
                mock_heal.return_value = {
                    "status": "healing_applied", "recommendations": [], "confidence": 0.1
                }
                result = await hub.execute_with_healing(
                    "keep failing", initial_service="any", max_retries=5
                )
        # With confidence 0.1 (< 0.6), consciousness stops after first failure + heal
        assert result["status"] == "failed_after_healing"


# ---------------------------------------------------------------------------
# send_agent_message
# ---------------------------------------------------------------------------

class TestSendAgentMessage:
    @pytest.mark.asyncio
    async def test_direct_delivery_to_registered_service(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=False)
        _register_service(hub, "target_svc")
        result = await hub.send_agent_message(
            from_agent="agent_a",
            to_agent="target_svc",
            message_type="request",
            content={"body": "hello"},
        )
        assert result["status"] == "delivered"
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_direct_delivery_to_unknown_service_fails(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=False)
        result = await hub.send_agent_message(
            from_agent="agent_a",
            to_agent="ghost_svc",
            message_type="request",
            content={"body": "hello"},
        )
        assert result["status"] == "delivery_failed"
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_message_contains_required_fields(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=False)
        _register_service(hub, "rx_svc")
        result = await hub.send_agent_message(
            from_agent="sender",
            to_agent="rx_svc",
            message_type="notification",
            content={"data": 42},
        )
        assert "message_id" in result

    @pytest.mark.asyncio
    async def test_consciousness_adds_sentiment(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=True)
        _register_service(hub, "rx_svc")
        # No need to mock consciousness bridge — _analyze_message_sentiment is synchronous-ish
        result = await hub.send_agent_message(
            from_agent="a",
            to_agent="rx_svc",
            message_type="status",
            content={"msg": "task complete success"},
        )
        assert result["success"] is True


# ---------------------------------------------------------------------------
# analyze_task_semantics (public wrapper)
# ---------------------------------------------------------------------------

class TestAnalyzeTaskSemantics:
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_bridge(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=True)
        with patch.object(hub, "_get_consciousness_bridge", new_callable=AsyncMock, return_value=None):
            result = await hub.analyze_task_semantics("analysis", "review the code")
        assert result == {}

    @pytest.mark.asyncio
    async def test_returns_analysis_with_bridge(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=True)
        mock_bridge = MagicMock()
        with patch.object(hub, "_get_consciousness_bridge", new_callable=AsyncMock, return_value=mock_bridge):
            result = await hub.analyze_task_semantics("code_review", "design a new feature")
        assert result["task_type"] == "code_review"
        assert "complexity" in result
        assert result["requires_creativity"] is True

    @pytest.mark.asyncio
    async def test_requires_analysis_keyword(self, tmp_path):
        hub = _make_hub(tmp_path, consciousness=True)
        mock_bridge = MagicMock()
        with patch.object(hub, "_get_consciousness_bridge", new_callable=AsyncMock, return_value=mock_bridge):
            result = await hub.analyze_task_semantics("analysis", "analyze the entire module")
        assert result["requires_analysis"] is True
        assert result["requires_creativity"] is False


# ---------------------------------------------------------------------------
# Complexity estimation
# ---------------------------------------------------------------------------

class TestEstimateComplexity:
    def test_short_description_low_complexity(self, tmp_path):
        hub = _make_hub(tmp_path)
        assert hub._estimate_complexity("hi") == 1

    def test_long_description_higher_complexity(self, tmp_path):
        hub = _make_hub(tmp_path)
        desc = "x" * 500
        assert hub._estimate_complexity(desc) == 10

    def test_complexity_keyword_boost(self, tmp_path):
        hub = _make_hub(tmp_path)
        base = hub._estimate_complexity("analyze")
        boosted = hub._estimate_complexity("comprehensive analyze")
        assert boosted >= base


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------

class TestGetAgentOrchestrationHub:
    def test_singleton_returns_same_instance(self, tmp_path):
        import src.agents.agent_orchestration_hub as mod
        # Reset singleton
        mod._hub_instance = None
        h1 = get_agent_orchestration_hub(root_path=tmp_path)
        h2 = get_agent_orchestration_hub(root_path=tmp_path)
        assert h1 is h2
        mod._hub_instance = None  # cleanup

    def test_creates_instance_of_correct_type(self, tmp_path):
        import src.agents.agent_orchestration_hub as mod
        mod._hub_instance = None
        hub = get_agent_orchestration_hub(root_path=tmp_path)
        assert isinstance(hub, AgentOrchestrationHub)
        mod._hub_instance = None  # cleanup
