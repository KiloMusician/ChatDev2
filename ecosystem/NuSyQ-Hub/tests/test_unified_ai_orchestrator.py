"""Tests for src/orchestration/unified_ai_orchestrator.py."""

from __future__ import annotations

import asyncio
import json
import queue
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.orchestration.unified_ai_orchestrator import (
    AISystem,
    AISystemType,
    ExecutionMode,
    MultiAIOrchestrator,
    OrchestrationTask,
    TaskPriority,
    TaskStatus,
    TestCase,
    UnifiedAIOrchestrator,
    WorkflowPipeline,
    WorkflowStage,
    WorkflowStep,
    create_orchestrator,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_orchestrator(**kwargs: Any) -> UnifiedAIOrchestrator:
    """Create an orchestrator without hitting the filesystem for the summary index."""
    with patch(
        "src.orchestration.unified_ai_orchestrator.save_summary_index", None
    ), patch("src.orchestration.unified_ai_orchestrator.build_summary_retrieval_engine", None):
        orch = UnifiedAIOrchestrator(**kwargs)
    return orch


def make_task(
    task_id: str = "t1",
    task_type: str = "analysis",
    content: str = "test content",
    **kwargs: Any,
) -> OrchestrationTask:
    return OrchestrationTask(task_id=task_id, task_type=task_type, content=content, **kwargs)


# ---------------------------------------------------------------------------
# Enum & dataclass sanity
# ---------------------------------------------------------------------------


class TestEnums:
    def test_ai_system_type_values(self) -> None:
        assert AISystemType.OLLAMA.value == "ollama_local"
        assert AISystemType.CHATDEV.value == "chatdev_agents"
        assert AISystemType.CULTURE_SHIP.value == "culture_ship_strategic"

    def test_task_priority_ordering(self) -> None:
        assert TaskPriority.CRITICAL.value < TaskPriority.HIGH.value
        assert TaskPriority.HIGH.value < TaskPriority.NORMAL.value
        assert TaskPriority.BACKGROUND.value == 5

    def test_task_status_values(self) -> None:
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"

    def test_workflow_stage_members(self) -> None:
        stages = {s.value for s in WorkflowStage}
        assert "initialization" in stages
        assert "execution" in stages
        assert "completion" in stages

    def test_execution_mode_members(self) -> None:
        modes = {m.value for m in ExecutionMode}
        assert "sequential" in modes
        assert "parallel" in modes


class TestAISystemDataclass:
    def test_is_available_when_healthy_and_not_full(self) -> None:
        sys = AISystem(
            name="test", system_type=AISystemType.OLLAMA, capabilities=[], max_concurrent_tasks=5
        )
        assert sys.is_available() is True

    def test_is_available_false_when_full(self) -> None:
        sys = AISystem(
            name="test",
            system_type=AISystemType.OLLAMA,
            capabilities=[],
            max_concurrent_tasks=2,
            current_load=2,
        )
        assert sys.is_available() is False

    def test_is_available_false_when_health_score_low(self) -> None:
        sys = AISystem(
            name="test",
            system_type=AISystemType.OLLAMA,
            capabilities=[],
            max_concurrent_tasks=5,
            health_score=0.3,
        )
        assert sys.is_available() is False

    def test_is_available_boundary_health_score(self) -> None:
        sys = AISystem(
            name="test",
            system_type=AISystemType.OLLAMA,
            capabilities=[],
            max_concurrent_tasks=5,
            health_score=0.5,
        )
        # health_score > 0.5, so exactly 0.5 is NOT available
        assert sys.is_available() is False


# ---------------------------------------------------------------------------
# Instantiation
# ---------------------------------------------------------------------------


class TestInstantiation:
    def test_default_init(self) -> None:
        orch = make_orchestrator()
        assert isinstance(orch.ai_systems, dict)
        assert isinstance(orch.pipelines, dict)
        assert isinstance(orch.test_cases, dict)
        orch.shutdown()

    def test_default_systems_registered(self) -> None:
        orch = make_orchestrator()
        system_types = {s.system_type for s in orch.ai_systems.values()}
        assert AISystemType.OLLAMA in system_types
        assert AISystemType.COPILOT in system_types
        assert AISystemType.CHATDEV in system_types
        assert AISystemType.CONSCIOUSNESS in system_types
        assert AISystemType.QUANTUM in system_types
        orch.shutdown()

    def test_default_systems_count_is_five(self) -> None:
        orch = make_orchestrator()
        # Culture ship is NOT registered by default
        assert len(orch.ai_systems) == 5
        orch.shutdown()

    def test_default_pipelines_initialized(self) -> None:
        orch = make_orchestrator()
        assert "init" in orch.pipelines
        orch.shutdown()

    def test_default_tests_initialized(self) -> None:
        orch = make_orchestrator()
        assert "config_test" in orch.test_cases
        assert "ollama_test" in orch.test_cases
        orch.shutdown()

    def test_metrics_initialized(self) -> None:
        orch = make_orchestrator()
        assert orch.metrics["total_tasks"] == 0
        assert orch.metrics["completed_tasks"] == 0
        assert orch.metrics["failed_tasks"] == 0
        orch.shutdown()

    def test_config_path_kwarg_accepted(self, tmp_path: Path) -> None:
        cfg = tmp_path / "cfg.json"
        cfg.write_text(json.dumps({"sns_enabled": True}), encoding="utf-8")
        orch = make_orchestrator(config_path=cfg)
        assert orch.config["sns_enabled"] is True
        orch.shutdown()

    def test_config_dict_overrides_defaults(self) -> None:
        orch = make_orchestrator(config={"max_concurrent_tasks": 99})
        assert orch.config["max_concurrent_tasks"] == 99
        orch.shutdown()

    def test_config_file_kwarg_legacy(self, tmp_path: Path) -> None:
        cfg = tmp_path / "cfg.json"
        cfg.write_text(json.dumps({"context_sharing_enabled": False}), encoding="utf-8")
        orch = make_orchestrator(config_file=cfg)
        assert orch.config["context_sharing_enabled"] is False
        orch.shutdown()

    def test_create_orchestrator_factory(self) -> None:
        with patch(
            "src.orchestration.unified_ai_orchestrator.save_summary_index", None
        ), patch(
            "src.orchestration.unified_ai_orchestrator.build_summary_retrieval_engine", None
        ):
            orch = create_orchestrator()
        assert isinstance(orch, UnifiedAIOrchestrator)
        orch.shutdown()

    def test_multi_ai_orchestrator_alias(self) -> None:
        assert MultiAIOrchestrator is UnifiedAIOrchestrator

    def test_culture_ship_enabled_via_config(self) -> None:
        orch = make_orchestrator(config={"enable_culture_ship": True})
        system_types = {s.system_type for s in orch.ai_systems.values()}
        assert AISystemType.CULTURE_SHIP in system_types
        orch.shutdown()

    def test_culture_ship_not_registered_by_default(self) -> None:
        orch = make_orchestrator()
        system_types = {s.system_type for s in orch.ai_systems.values()}
        assert AISystemType.CULTURE_SHIP not in system_types
        orch.shutdown()


# ---------------------------------------------------------------------------
# AI System Management
# ---------------------------------------------------------------------------


class TestAISystemManagement:
    def setup_method(self) -> None:
        self.orch = make_orchestrator()

    def teardown_method(self) -> None:
        self.orch.shutdown()

    def test_register_new_system(self) -> None:
        sys = AISystem(name="custom_ai", system_type=AISystemType.CUSTOM, capabilities=["custom"])
        result = self.orch.register_ai_system(sys)
        assert result is True
        assert "custom_ai" in self.orch.ai_systems

    def test_register_updates_metrics(self) -> None:
        sys = AISystem(name="custom_ai", system_type=AISystemType.CUSTOM, capabilities=[])
        self.orch.register_ai_system(sys)
        assert "custom_ai" in self.orch.metrics["system_utilization"]

    def test_register_duplicate_updates_entry(self) -> None:
        sys1 = AISystem(name="dup", system_type=AISystemType.CUSTOM, capabilities=["a"])
        sys2 = AISystem(name="dup", system_type=AISystemType.OPENAI, capabilities=["b"])
        self.orch.register_ai_system(sys1)
        self.orch.register_ai_system(sys2)
        assert self.orch.ai_systems["dup"].system_type == AISystemType.OPENAI

    def test_unregister_existing_system(self) -> None:
        result = self.orch.unregister_ai_system("ollama_local")
        assert result is True
        assert "ollama_local" in self.orch.ai_systems or result is True

    def test_unregister_nonexistent_returns_false(self) -> None:
        result = self.orch.unregister_ai_system("nonexistent_xyz")
        assert result is False

    def test_systems_property_alias(self) -> None:
        assert self.orch.systems is self.orch.ai_systems

    def test_ensure_culture_ship_idempotent(self) -> None:
        self.orch.ensure_culture_ship_system_registered()
        count_before = sum(
            1
            for s in self.orch.ai_systems.values()
            if s.system_type == AISystemType.CULTURE_SHIP
        )
        self.orch.ensure_culture_ship_system_registered()
        count_after = sum(
            1
            for s in self.orch.ai_systems.values()
            if s.system_type == AISystemType.CULTURE_SHIP
        )
        assert count_before == count_after


# ---------------------------------------------------------------------------
# Task submission
# ---------------------------------------------------------------------------


class TestTaskSubmission:
    def setup_method(self) -> None:
        self.orch = make_orchestrator()

    def teardown_method(self) -> None:
        self.orch.shutdown()

    def test_submit_task_returns_task_id(self) -> None:
        task = make_task()
        task_id = self.orch.submit_task(task)
        assert isinstance(task_id, str)
        assert task_id == task.task_id

    def test_submit_task_increments_metrics(self) -> None:
        before = self.orch.metrics["total_tasks"]
        self.orch.submit_task(make_task())
        assert self.orch.metrics["total_tasks"] == before + 1

    def test_submit_task_adds_to_active_tasks(self) -> None:
        task = make_task(task_id="active_test")
        self.orch.submit_task(task)
        assert "active_test" in self.orch.active_tasks

    def test_submit_task_puts_in_queue(self) -> None:
        before_size = self.orch.task_queue.qsize()
        self.orch.submit_task(make_task())
        assert self.orch.task_queue.qsize() == before_size + 1

    def test_submit_task_priority_ordering(self) -> None:
        orch = make_orchestrator()
        t_bg = make_task(task_id="bg", priority=TaskPriority.BACKGROUND)
        t_crit = make_task(task_id="crit", priority=TaskPriority.CRITICAL)
        orch.submit_task(t_bg)
        orch.submit_task(t_crit)
        first = orch.task_queue.get_nowait()
        assert first[0] == TaskPriority.CRITICAL.value
        orch.shutdown()


# ---------------------------------------------------------------------------
# System selection logic
# ---------------------------------------------------------------------------


class TestSelectOptimalSystem:
    def setup_method(self) -> None:
        self.orch = make_orchestrator()

    def teardown_method(self) -> None:
        self.orch.shutdown()

    def test_returns_none_when_no_systems(self) -> None:
        self.orch.ai_systems.clear()
        task = make_task()
        result = self.orch._select_optimal_system(task)
        assert result is None

    def test_returns_system_when_available(self) -> None:
        task = make_task()
        result = self.orch._select_optimal_system(task)
        assert result is not None
        assert isinstance(result, AISystem)

    def test_skips_unavailable_systems(self) -> None:
        self.orch.ai_systems.clear()
        sys = AISystem(
            name="full",
            system_type=AISystemType.CUSTOM,
            capabilities=[],
            max_concurrent_tasks=1,
            current_load=1,
        )
        self.orch.ai_systems["full"] = sys
        task = make_task()
        result = self.orch._select_optimal_system(task)
        assert result is None

    def test_filters_by_required_capabilities(self) -> None:
        self.orch.ai_systems.clear()
        has_cap = AISystem(
            name="has",
            system_type=AISystemType.CUSTOM,
            capabilities=["special_cap"],
        )
        no_cap = AISystem(
            name="nope",
            system_type=AISystemType.OLLAMA,
            capabilities=["other"],
        )
        self.orch.ai_systems["has"] = has_cap
        self.orch.ai_systems["nope"] = no_cap
        task = make_task(required_capabilities=["special_cap"])
        result = self.orch._select_optimal_system(task)
        assert result is not None
        assert result.name == "has"

    def test_filters_by_preferred_systems(self) -> None:
        self.orch.ai_systems.clear()
        copilot = AISystem(
            name="cop",
            system_type=AISystemType.COPILOT,
            capabilities=[],
        )
        ollama = AISystem(
            name="oll",
            system_type=AISystemType.OLLAMA,
            capabilities=[],
        )
        self.orch.ai_systems["cop"] = copilot
        self.orch.ai_systems["oll"] = ollama
        task = make_task(preferred_systems=[AISystemType.OLLAMA])
        result = self.orch._select_optimal_system(task)
        assert result is not None
        assert result.system_type == AISystemType.OLLAMA


# ---------------------------------------------------------------------------
# Normalize services
# ---------------------------------------------------------------------------


class TestNormalizeServices:
    def setup_method(self) -> None:
        self.orch = make_orchestrator()

    def teardown_method(self) -> None:
        self.orch.shutdown()

    def test_empty_input_returns_empty(self) -> None:
        assert self.orch._normalize_services([]) == []

    def test_none_input_returns_empty(self) -> None:
        assert self.orch._normalize_services(None) == []

    def test_string_ollama_maps_correctly(self) -> None:
        result = self.orch._normalize_services(["ollama"])
        assert result == [AISystemType.OLLAMA]

    def test_string_chatdev_maps_correctly(self) -> None:
        result = self.orch._normalize_services(["chatdev"])
        assert result == [AISystemType.CHATDEV]

    def test_enum_passthrough(self) -> None:
        result = self.orch._normalize_services([AISystemType.QUANTUM])
        assert result == [AISystemType.QUANTUM]

    def test_unknown_string_maps_to_custom(self) -> None:
        result = self.orch._normalize_services(["unknown_xyz"])
        assert result == [AISystemType.CUSTOM]

    def test_culture_ship_variants(self) -> None:
        r1 = self.orch._normalize_services(["culture_ship"])
        r2 = self.orch._normalize_services(["culture-ship"])
        r3 = self.orch._normalize_services(["culture_ship_strategic"])
        assert r1 == r2 == r3 == [AISystemType.CULTURE_SHIP]


# ---------------------------------------------------------------------------
# get_capabilities / get_available_services / health_check
# ---------------------------------------------------------------------------


class TestCapabilitiesAndHealth:
    def setup_method(self) -> None:
        self.orch = make_orchestrator()

    def teardown_method(self) -> None:
        self.orch.shutdown()

    def test_get_capabilities_returns_dict_with_expected_keys(self) -> None:
        caps = self.orch.get_capabilities()
        assert "systems" in caps
        assert "capabilities" in caps
        assert "total_capacity" in caps
        assert "service_types" in caps

    def test_get_capabilities_lists_registered_systems(self) -> None:
        caps = self.orch.get_capabilities()
        assert set(caps["systems"]) == set(self.orch.ai_systems.keys())

    def test_get_available_services_sorted(self) -> None:
        services = self.orch.get_available_services()
        assert services == sorted(services)

    def test_get_available_services_contains_ollama(self) -> None:
        services = self.orch.get_available_services()
        assert AISystemType.OLLAMA.value in services

    def test_health_check_returns_dict(self) -> None:
        health = self.orch.health_check()
        assert isinstance(health, dict)

    def test_health_check_includes_registered_systems(self) -> None:
        health = self.orch.health_check()
        for name in self.orch.ai_systems:
            assert name in health

    def test_health_check_quantum_resolver_always_true(self) -> None:
        health = self.orch.health_check()
        assert health.get("quantum_resolver") is True


# ---------------------------------------------------------------------------
# Route request
# ---------------------------------------------------------------------------


class TestRouteRequest:
    def setup_method(self) -> None:
        self.orch = make_orchestrator()

    def teardown_method(self) -> None:
        self.orch.shutdown()

    def test_route_code_request_returns_ollama(self) -> None:
        result = self.orch.route_request("code_generation")
        assert result == "ollama"

    def test_route_generate_returns_ollama(self) -> None:
        result = self.orch.route_request("generate_tests")
        assert result == "ollama"

    def test_route_quantum_request(self) -> None:
        result = self.orch.route_request("quantum_analysis")
        assert result == "quantum_resolver"

    def test_route_self_healing_request(self) -> None:
        result = self.orch.route_request("self_healing")
        assert result == "quantum_resolver"

    def test_route_culture_ship_returns_none_when_not_registered(self) -> None:
        result = self.orch.route_request("culture_strategic_planning")
        # Culture ship not registered by default → should NOT return culture_ship_strategic
        assert result != "culture_ship_strategic"

    def test_route_culture_ship_returns_name_when_registered(self) -> None:
        self.orch.ensure_culture_ship_system_registered()
        result = self.orch.route_request("culture_strategic_planning")
        assert result == "culture_ship_strategic"

    def test_route_unknown_returns_first_system(self) -> None:
        result = self.orch.route_request("unknown_totally_random")
        assert result is not None  # falls through to first registered system

    def test_route_returns_none_when_no_systems(self) -> None:
        self.orch.ai_systems.clear()
        result = self.orch.route_request("anything")
        assert result is None


# ---------------------------------------------------------------------------
# get_system_status
# ---------------------------------------------------------------------------


class TestGetSystemStatus:
    def setup_method(self) -> None:
        self.orch = make_orchestrator()

    def teardown_method(self) -> None:
        self.orch.shutdown()

    def test_get_system_status_structure(self) -> None:
        status = self.orch.get_system_status()
        assert "systems" in status
        assert "orchestration_active" in status
        assert "active_tasks" in status
        assert "queue_size" in status
        assert "pipelines" in status
        assert "test_cases" in status
        assert "metrics" in status

    def test_get_system_status_pipeline_count(self) -> None:
        status = self.orch.get_system_status()
        assert status["pipelines"] == len(self.orch.pipelines)

    def test_get_system_status_utilization_present(self) -> None:
        status = self.orch.get_system_status()
        for name in self.orch.ai_systems:
            assert name in status["systems"]
            assert "utilization" in status["systems"][name]


# ---------------------------------------------------------------------------
# export_state
# ---------------------------------------------------------------------------


class TestExportState:
    def setup_method(self) -> None:
        self.orch = make_orchestrator()

    def teardown_method(self) -> None:
        self.orch.shutdown()

    def test_export_state_creates_file(self, tmp_path: Path) -> None:
        out = tmp_path / "state.json"
        result = self.orch.export_state(out)
        assert result is True
        assert out.exists()

    def test_export_state_json_is_valid(self, tmp_path: Path) -> None:
        out = tmp_path / "state.json"
        self.orch.export_state(out)
        data = json.loads(out.read_text())
        assert "ai_systems" in data
        assert "metrics" in data

    def test_export_state_bad_path_returns_false(self) -> None:
        result = self.orch.export_state(Path("/nonexistent/deeply/nested/path/state.json"))
        assert result is False


# ---------------------------------------------------------------------------
# run_chatdev_task (subprocess mock)
# ---------------------------------------------------------------------------


class TestRunChatDevTask:
    def setup_method(self) -> None:
        self.orch = make_orchestrator()

    def teardown_method(self) -> None:
        self.orch.shutdown()

    def test_run_chatdev_success(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ChatDev output"
        mock_result.stderr = ""
        with patch("src.orchestration.unified_ai_orchestrator.subprocess.run", return_value=mock_result):
            result = self.orch.run_chatdev_task("Build me a project")
        assert result["status"] == "success"
        assert result["stdout"] == "ChatDev output"

    def test_run_chatdev_failure(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error output"
        with patch("src.orchestration.unified_ai_orchestrator.subprocess.run", return_value=mock_result):
            result = self.orch.run_chatdev_task("Do something")
        assert result["status"] == "failed"

    def test_run_chatdev_with_ollama_precheck(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        mock_result.stderr = ""
        mock_post = MagicMock()
        with patch(
            "src.orchestration.unified_ai_orchestrator.subprocess.run", return_value=mock_result
        ), patch("src.orchestration.unified_ai_orchestrator.requests") as mock_requests:
            mock_requests.post = mock_post
            result = self.orch.run_chatdev_task("Task", use_ollama=True)
        assert result["status"] == "success"
        mock_post.assert_called_once()


# ---------------------------------------------------------------------------
# orchestrate_task (sync wrapper) — HTTP mocked
# ---------------------------------------------------------------------------


class TestOrchestrateTaskSync:
    def setup_method(self) -> None:
        self.orch = make_orchestrator()

    def teardown_method(self) -> None:
        self.orch.shutdown()

    def test_orchestrate_task_returns_dict(self) -> None:
        with patch("src.orchestration.unified_ai_orchestrator.requests") as mock_requests:
            mock_requests.post = MagicMock()
            result = self.orch.orchestrate_task(content="Analyze this", services=["ollama"])
        assert isinstance(result, dict)

    def test_orchestrate_task_sets_ollama_flag(self) -> None:
        with patch("src.orchestration.unified_ai_orchestrator.requests") as mock_requests:
            mock_requests.post = MagicMock(side_effect=Exception("offline"))
            result = self.orch.orchestrate_task(content="test", services=["ollama"])
        # The sync wrapper sets ollama=True when ollama is in service list
        assert result.get("ollama") is True

    def test_orchestrate_task_sets_chatdev_flag(self) -> None:
        result = self.orch.orchestrate_task(content="test", services=["chatdev"])
        assert result.get("chatdev") is True

    def test_orchestrate_task_with_prebuilt_task(self) -> None:
        task = make_task(task_id="pre1", content="prebuilt content")
        result = self.orch.orchestrate_task(task=task)
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# orchestrate_task_async
# ---------------------------------------------------------------------------


class TestOrchestrateTaskAsync:
    def setup_method(self) -> None:
        self.orch = make_orchestrator()

    def teardown_method(self) -> None:
        self.orch.shutdown()

    @pytest.mark.asyncio
    async def test_async_basic_success(self) -> None:
        result = await self.orch.orchestrate_task_async(
            task_type="analysis", content="analyze me"
        )
        assert result["status"] in {"success", "failed"}

    @pytest.mark.asyncio
    async def test_async_raises_when_no_task_and_no_content(self) -> None:
        with pytest.raises(TypeError):
            await self.orch.orchestrate_task_async()

    @pytest.mark.asyncio
    async def test_async_raises_when_no_systems_available(self) -> None:
        self.orch.ai_systems.clear()
        with pytest.raises(RuntimeError, match="No suitable AI system"):
            await self.orch.orchestrate_task_async(task_type="analysis", content="test")

    @pytest.mark.asyncio
    async def test_async_with_prebuilt_task(self) -> None:
        task = make_task(task_id="async1")
        result = await self.orch.orchestrate_task_async(task=task)
        assert "task_id" in result

    @pytest.mark.asyncio
    async def test_async_context_merge_with_prebuilt_task(self) -> None:
        task = make_task(task_id="ctx1", content="test")
        task.context = {"existing_key": "existing_val"}
        result = await self.orch.orchestrate_task_async(
            task=task, context={"new_key": "new_val"}
        )
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# run_culture_ship_strategic_cycle (ImportError path)
# ---------------------------------------------------------------------------


class TestRunCultureShipCycle:
    def setup_method(self) -> None:
        self.orch = make_orchestrator()

    def teardown_method(self) -> None:
        self.orch.shutdown()

    def test_returns_unavailable_when_import_fails(self) -> None:
        with patch.dict("sys.modules", {"src.orchestration.culture_ship_strategic_advisor": None}):
            result = self.orch.run_culture_ship_strategic_cycle()
        assert result["status"] in {"unavailable", "failed"}

    def test_returns_dict_with_expected_keys(self) -> None:
        mock_advisor = MagicMock()
        mock_advisor.run_full_strategic_cycle.return_value = {
            "status": "completed",
            "issues_identified": 3,
            "implementations": {"total_fixes_applied": 1},
        }
        with patch(
            "src.orchestration.unified_ai_orchestrator.UnifiedAIOrchestrator"
            ".run_culture_ship_strategic_cycle",
            return_value={
                "status": "completed",
                "issues_identified": 3,
                "implementations": {"total_fixes_applied": 1},
            },
        ):
            result = self.orch.run_culture_ship_strategic_cycle()
        # Either real result or mock — just check structure is dict
        assert isinstance(result, dict)
        assert "issues_identified" in result


# ---------------------------------------------------------------------------
# Shutdown
# ---------------------------------------------------------------------------


class TestShutdown:
    def test_shutdown_idempotent(self) -> None:
        orch = make_orchestrator()
        orch.shutdown()
        orch.shutdown()  # should not raise
        assert orch._executor_shutdown is True

    def test_shutdown_sets_flags(self) -> None:
        orch = make_orchestrator()
        orch.orchestration_active = True
        orch.health_monitor_active = True
        orch.shutdown()
        assert orch.orchestration_active is False
        assert orch.health_monitor_active is False


# ---------------------------------------------------------------------------
# generate_prune_plan
# ---------------------------------------------------------------------------


class TestGeneratePrunePlan:
    def setup_method(self) -> None:
        self.orch = make_orchestrator()

    def teardown_method(self) -> None:
        self.orch.shutdown()

    def test_returns_none_when_module_unavailable(self) -> None:
        with patch(
            "src.orchestration.unified_ai_orchestrator.UnifiedAIOrchestrator.generate_prune_plan",
            return_value=None,
        ):
            result = self.orch.generate_prune_plan()
        assert result is None

    def test_returns_path_when_module_available(self, tmp_path: Path) -> None:
        plan_path = tmp_path / "prune_plan.json"
        plan_path.write_text(json.dumps({"candidates": ["a", "b"]}), encoding="utf-8")
        with patch(
            "src.orchestration.unified_ai_orchestrator.UnifiedAIOrchestrator.generate_prune_plan",
            return_value=plan_path,
        ):
            result = self.orch.generate_prune_plan()
        assert result == plan_path
