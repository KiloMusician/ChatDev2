#!/usr/bin/env python3
"""Tests for AgentTaskRouter — covering uncovered blocks in lines 2390-3961.

Targets:
- _route_to_lmstudio (lines ~2390-2528): LM Studio routing including httpx import error,
  timeout parsing, empty model error, retry/backoff logic
- _route_to_factory (lines ~3020-3247): Factory routing with all task types
- Generator routing handlers (lines ~3258-3302): graphql/openapi/component/database/project
- _route_to_openclaw (lines ~3323-3389): internal/external channel routing
- _route_to_intermediary (lines ~3391-3470): AI Intermediary routing
- _route_to_skyclaw (lines ~3472-3622): SkyClaw binary routing
- health_check (lines ~3657-3802): System health check
- _route_to_devtool (lines ~3808-3917): DevTool+ routing
- GitKraken helpers (lines ~3919-3961): _looks_like_gitkraken_task,
  _infer_gitkraken_operation, _extract_commit_message, _build_gitkraken_parameters
- _route_to_gitkraken (lines ~4007-4108): GitKraken routing
- _route_to_huggingface (lines ~4110-4179): HuggingFace routing
- _route_to_dbclient (lines ~4181-4246): DBClient routing
- _route_to_neural_ml (lines ~4248-4361): Neural ML routing
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tools.agent_task_router import AgentTaskRouter
from src.orchestration.unified_ai_orchestrator import OrchestrationTask, TaskPriority


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def router(tmp_path: Path) -> AgentTaskRouter:
    router = AgentTaskRouter(repo_root=tmp_path)
    router.quest_log_path = tmp_path / "quest_log.jsonl"
    router.quest_log_path.parent.mkdir(parents=True, exist_ok=True)
    router.quest_log_path.touch()
    return router


def make_task(
    task_type: str = "analyze",
    content: str = "test content",
    context: dict | None = None,
    task_id: str = "test-task-id",
    priority: TaskPriority = TaskPriority.NORMAL,
) -> OrchestrationTask:
    return OrchestrationTask(
        task_id=task_id,
        task_type=task_type,
        content=content,
        context=context or {},
        priority=priority,
        timeout_seconds=30.0,
    )


# ===========================================================================
# _route_to_lmstudio — lines 2390-2528
# ===========================================================================


class TestRouteToLmStudio:
    @pytest.mark.asyncio
    async def test_httpx_import_error_returns_failed(self, router: AgentTaskRouter):
        """When httpx is not available the route should return failed immediately."""
        task = make_task(task_type="analyze", content="hello", context={})
        with patch.dict("sys.modules", {"httpx": None}):
            result = await router._route_to_lmstudio(task)
        assert result["status"] == "failed"
        assert result["system"] == "lmstudio"
        assert "httpx" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_no_model_returns_failed(self, router: AgentTaskRouter):
        """When no model can be resolved the route should return failed."""
        task = make_task(task_type="analyze", content="hello", context={})
        mock_httpx = MagicMock()
        mock_client = AsyncMock()
        mock_httpx.Timeout.return_value = MagicMock()
        mock_httpx.AsyncClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_httpx.AsyncClient.return_value.__aexit__ = AsyncMock(return_value=False)

        with (
            patch.dict("sys.modules", {"httpx": mock_httpx}),
            patch.object(router, "_resolve_lmstudio_model", new=AsyncMock(return_value=None)),
        ):
            result = await router._route_to_lmstudio(task)
        assert result["status"] == "failed"
        assert "model" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_successful_completion(self, router: AgentTaskRouter):
        """A successful LM Studio completion should return status=success."""
        task = make_task(task_type="analyze", content="hello", context={})
        mock_httpx = MagicMock()
        mock_httpx.Timeout.return_value = MagicMock()
        mock_httpx.TimeoutException = Exception
        mock_httpx.HTTPError = Exception
        mock_client = AsyncMock()
        mock_httpx.AsyncClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_httpx.AsyncClient.return_value.__aexit__ = AsyncMock(return_value=False)

        with (
            patch.dict("sys.modules", {"httpx": mock_httpx}),
            patch.object(router, "_resolve_lmstudio_model", new=AsyncMock(return_value="qwen2.5")),
            patch.object(
                router,
                "_lmstudio_chat_completion",
                new=AsyncMock(return_value={"choices": [{"message": {"content": "hi"}}]}),
            ),
            patch.object(router, "_extract_lmstudio_output", return_value="hi"),
        ):
            result = await router._route_to_lmstudio(task)
        assert result["status"] == "success"
        assert result["system"] == "lmstudio"
        assert result["model"] == "qwen2.5"

    @pytest.mark.asyncio
    async def test_timeout_override_from_context(self, router: AgentTaskRouter):
        """Context timeout should be respected when provided."""
        task = make_task(
            task_type="analyze",
            content="hi",
            context={"timeout": "5"},
        )
        mock_httpx = MagicMock()
        mock_httpx.Timeout.return_value = MagicMock()
        mock_httpx.TimeoutException = Exception
        mock_httpx.HTTPError = Exception
        mock_client = AsyncMock()
        mock_httpx.AsyncClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_httpx.AsyncClient.return_value.__aexit__ = AsyncMock(return_value=False)

        with (
            patch.dict("sys.modules", {"httpx": mock_httpx}),
            patch.object(router, "_resolve_lmstudio_model", new=AsyncMock(return_value="test")),
            patch.object(
                router,
                "_lmstudio_chat_completion",
                new=AsyncMock(return_value={"choices": [{"message": {"content": "reply"}}]}),
            ),
            patch.object(router, "_extract_lmstudio_output", return_value="reply"),
        ):
            result = await router._route_to_lmstudio(task)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_request_failure_exhausts_retries(self, router: AgentTaskRouter):
        """All retries exhausted should return failed."""
        import httpx as real_httpx

        task = make_task(task_type="analyze", content="hi", context={})
        mock_httpx = MagicMock()
        mock_httpx.Timeout.return_value = MagicMock()
        mock_httpx.TimeoutException = real_httpx.TimeoutException
        mock_httpx.HTTPError = real_httpx.HTTPError
        mock_client = AsyncMock()
        mock_httpx.AsyncClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_httpx.AsyncClient.return_value.__aexit__ = AsyncMock(return_value=False)

        with (
            patch.dict("sys.modules", {"httpx": mock_httpx}),
            patch.object(router, "_resolve_lmstudio_model", new=AsyncMock(return_value="test")),
            patch.object(
                router,
                "_lmstudio_chat_completion",
                new=AsyncMock(side_effect=real_httpx.TimeoutException("timeout")),
            ),
            patch.object(router, "_lmstudio_timeout_seconds", return_value=3.0),
        ):
            result = await router._route_to_lmstudio(task, reason="test")
        assert result["status"] == "failed"
        assert result["system"] == "lmstudio"


# ===========================================================================
# _route_to_factory — lines 3020-3247
# ===========================================================================


class TestRouteToFactory:
    @pytest.mark.asyncio
    async def test_factory_none_returns_failed(self, router: AgentTaskRouter):
        """When ProjectFactory is not importable, return failed."""
        task = make_task(task_type="factory_health")
        with patch("src.tools.agent_task_router.ProjectFactory", None):
            result = await router._route_to_factory(task)
        assert result["status"] == "failed"
        assert "Factory unavailable" in result["error"]

    @pytest.mark.asyncio
    async def test_factory_health_success(self, router: AgentTaskRouter):
        """factory_health with healthy=True should return success."""
        task = make_task(task_type="factory_health", context={})
        mock_factory_cls = MagicMock()
        mock_factory = MagicMock()
        mock_factory.run_health_check.return_value = {"healthy": True, "checks": []}
        mock_factory_cls.return_value = mock_factory

        with patch("src.tools.agent_task_router.ProjectFactory", mock_factory_cls):
            result = await router._route_to_factory(task)
        assert result["status"] == "success"
        assert result["system"] == "factory"

    @pytest.mark.asyncio
    async def test_factory_health_unhealthy(self, router: AgentTaskRouter):
        """factory_health with healthy=False should return failed."""
        task = make_task(task_type="factory_health", context={})
        mock_factory_cls = MagicMock()
        mock_factory = MagicMock()
        mock_factory.run_health_check.return_value = {"healthy": False}
        mock_factory_cls.return_value = mock_factory

        with patch("src.tools.agent_task_router.ProjectFactory", mock_factory_cls):
            result = await router._route_to_factory(task)
        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_factory_doctor(self, router: AgentTaskRouter):
        """factory_doctor should call run_doctor and return result."""
        task = make_task(task_type="factory_doctor", context={})
        mock_factory_cls = MagicMock()
        mock_factory = MagicMock()
        mock_factory.run_doctor.return_value = {"healthy": True}
        mock_factory_cls.return_value = mock_factory

        with patch("src.tools.agent_task_router.ProjectFactory", mock_factory_cls):
            result = await router._route_to_factory(task)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_factory_doctor_fix(self, router: AgentTaskRouter):
        """factory_doctor_fix should read post_fix.healthy for status."""
        task = make_task(task_type="factory_doctor_fix", context={})
        mock_factory_cls = MagicMock()
        mock_factory = MagicMock()
        mock_factory.run_doctor_fix.return_value = {"post_fix": {"healthy": True}}
        mock_factory_cls.return_value = mock_factory

        with patch("src.tools.agent_task_router.ProjectFactory", mock_factory_cls):
            result = await router._route_to_factory(task)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_factory_autopilot(self, router: AgentTaskRouter):
        """factory_autopilot should invoke run_autopilot."""
        task = make_task(task_type="factory_autopilot", context={"fix": True})
        mock_factory_cls = MagicMock()
        mock_factory = MagicMock()
        mock_factory.run_autopilot.return_value = {"healthy": True}
        mock_factory_cls.return_value = mock_factory

        with patch("src.tools.agent_task_router.ProjectFactory", mock_factory_cls):
            result = await router._route_to_factory(task)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_factory_inspect_examples(self, router: AgentTaskRouter):
        """factory_inspect_examples should invoke inspect_reference_games."""
        task = make_task(task_type="factory_inspect_examples", context={})
        mock_factory_cls = MagicMock()
        mock_factory = MagicMock()
        mock_factory.inspect_reference_games.return_value = {"games": []}
        mock_factory_cls.return_value = mock_factory

        with patch("src.tools.agent_task_router.ProjectFactory", mock_factory_cls):
            result = await router._route_to_factory(task)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_unsupported_task_type_returns_failed(self, router: AgentTaskRouter):
        """Unsupported factory task type should return descriptive failure."""
        task = make_task(task_type="unsupported_type", context={})
        mock_factory_cls = MagicMock()
        with patch("src.tools.agent_task_router.ProjectFactory", mock_factory_cls):
            result = await router._route_to_factory(task)
        assert result["status"] == "failed"
        assert "Factory supports" in result["error"]

    @pytest.mark.asyncio
    async def test_create_project_success(self, router: AgentTaskRouter):
        """create_project should return project info on success."""
        task = make_task(
            task_type="create_project",
            content="A new game",
            context={"project_name": "MyGame", "template": "default_game"},
        )
        mock_result = MagicMock()
        mock_result.name = "MyGame"
        mock_result.type = "game"
        mock_result.version = "1.0.0"
        mock_result.output_path = Path("/tmp/MyGame")
        mock_result.ai_provider = "ollama"
        mock_result.model_used = "qwen2.5"
        mock_result.token_cost = 0
        mock_result.chatdev_warehouse_path = None

        mock_factory_cls = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_result
        mock_factory_cls.return_value = mock_factory

        with patch("src.tools.agent_task_router.ProjectFactory", mock_factory_cls):
            result = await router._route_to_factory(task)
        assert result["status"] == "success"
        assert result["system"] == "factory"
        assert "MyGame" in result["note"]

    @pytest.mark.asyncio
    async def test_factory_runtime_error_returns_failed(self, router: AgentTaskRouter):
        """RuntimeError from factory.run_health_check should return failed."""
        task = make_task(task_type="factory_health", context={})
        mock_factory_cls = MagicMock()
        mock_factory = MagicMock()
        mock_factory.run_health_check.side_effect = RuntimeError("boom")
        mock_factory_cls.return_value = mock_factory

        with patch("src.tools.agent_task_router.ProjectFactory", mock_factory_cls):
            result = await router._route_to_factory(task)
        assert result["status"] == "failed"
        assert "boom" in result["error"]


# ===========================================================================
# Phase 3 Generator Routing Handlers — lines 3258-3302
# ===========================================================================


class TestPhase3GeneratorRouting:
    @pytest.mark.asyncio
    async def test_route_graphql_generator(self, router: AgentTaskRouter):
        task = make_task(context={"description": "blog API"})
        mock_gen = AsyncMock(return_value={"status": "success", "schema": "..."})
        with patch(
            "src.orchestration.generator_integration.generate_graphql_api", mock_gen
        ):
            result = await router._route_to_graphql_generator(task)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_route_openapi_generator(self, router: AgentTaskRouter):
        task = make_task(context={"description": "REST API"})
        mock_gen = AsyncMock(return_value={"status": "success", "spec": "..."})
        with patch(
            "src.orchestration.generator_integration.generate_openapi_spec", mock_gen
        ):
            result = await router._route_to_openapi_generator(task)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_route_component_generator(self, router: AgentTaskRouter):
        task = make_task(context={"description": "Button component"})
        mock_gen = AsyncMock(return_value={"status": "success", "code": "..."})
        with patch(
            "src.orchestration.generator_integration.generate_react_component", mock_gen
        ):
            result = await router._route_to_component_generator(task)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_route_database_generator(self, router: AgentTaskRouter):
        task = make_task(context={"description": "User schema"})
        mock_gen = AsyncMock(return_value={"status": "success", "schema": "..."})
        with patch(
            "src.orchestration.generator_integration.generate_database_schema", mock_gen
        ):
            result = await router._route_to_database_generator(task)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_route_project_generator(self, router: AgentTaskRouter):
        task = make_task(context={"description": "game engine"})
        mock_gen = AsyncMock(return_value={"status": "success", "output": "..."})
        with patch(
            "src.orchestration.generator_integration.generate_universal_project", mock_gen
        ):
            result = await router._route_to_project_generator(task)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_generator_non_dict_output_wrapped(self, router: AgentTaskRouter):
        """Non-dict generator output should be wrapped in {'output': ...}."""
        task = make_task(context={})
        mock_gen = AsyncMock(return_value="raw string")
        with patch(
            "src.orchestration.generator_integration.generate_graphql_api", mock_gen
        ):
            result = await router._route_to_graphql_generator(task)
        # Non-dict outputs are wrapped and normalized with canonical schema keys
        assert result["output"] == "raw string"
        assert result["system"] == "graphql_generator"
        assert result["task_id"] == task.task_id
        assert "execution_path" in result


# ===========================================================================
# _route_to_openclaw — lines 3323-3389
# ===========================================================================


class TestRouteToOpenclaw:
    @pytest.mark.asyncio
    async def test_internal_channel_returns_success(self, router: AgentTaskRouter):
        task = make_task(context={"channel": "internal", "message": "hello"})
        mock_bridge_cls = MagicMock()
        with patch(
            "src.integrations.openclaw_gateway_bridge.OpenClawGatewayBridge", mock_bridge_cls
        ):
            result = await router._route_to_openclaw(task)
        assert result["status"] == "success"
        assert result["agent"] == "openclaw"
        assert result["channel"] == "internal"

    @pytest.mark.asyncio
    async def test_loopback_channel_returns_success(self, router: AgentTaskRouter):
        task = make_task(context={"channel": "loopback"})
        mock_bridge_cls = MagicMock()
        with patch(
            "src.integrations.openclaw_gateway_bridge.OpenClawGatewayBridge", mock_bridge_cls
        ):
            result = await router._route_to_openclaw(task)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_external_channel_connect_failure(self, router: AgentTaskRouter):
        task = make_task(context={"channel": "slack"})
        mock_bridge_cls = MagicMock()
        mock_bridge = AsyncMock()
        mock_bridge.connect = AsyncMock(return_value=False)
        mock_bridge_cls.return_value = mock_bridge
        with patch(
            "src.integrations.openclaw_gateway_bridge.OpenClawGatewayBridge", mock_bridge_cls
        ):
            result = await router._route_to_openclaw(task)
        assert result["status"] == "failed"
        assert "connect" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_external_channel_send_success(self, router: AgentTaskRouter):
        task = make_task(context={"channel": "discord", "message": "hi"})
        mock_bridge_cls = MagicMock()
        mock_bridge = AsyncMock()
        mock_bridge.connect = AsyncMock(return_value=True)
        mock_bridge.send_result = AsyncMock(return_value=True)
        mock_bridge.disconnect = AsyncMock()
        mock_bridge_cls.return_value = mock_bridge
        with patch(
            "src.integrations.openclaw_gateway_bridge.OpenClawGatewayBridge", mock_bridge_cls
        ):
            result = await router._route_to_openclaw(task)
        assert result["status"] == "success"
        assert result["sent"] is True

    @pytest.mark.asyncio
    async def test_import_error_returns_failed(self, router: AgentTaskRouter):
        task = make_task(context={"channel": "slack"})
        with patch.dict("sys.modules", {"src.integrations.openclaw_gateway_bridge": None}):
            result = await router._route_to_openclaw(task)
        assert result["status"] == "failed"
        assert result["agent"] == "openclaw"

    @pytest.mark.asyncio
    async def test_generic_exception_returns_failed(self, router: AgentTaskRouter):
        task = make_task(context={"channel": "slack"})
        mock_bridge_cls = MagicMock(side_effect=RuntimeError("unexpected"))
        with patch(
            "src.integrations.openclaw_gateway_bridge.OpenClawGatewayBridge", mock_bridge_cls
        ):
            result = await router._route_to_openclaw(task)
        assert result["status"] == "failed"
        assert "unexpected" in result["error"]


# ===========================================================================
# _route_to_intermediary — lines 3391-3470
# ===========================================================================


class TestRouteToIntermediary:
    @pytest.mark.asyncio
    async def test_success_path(self, router: AgentTaskRouter):
        task = make_task(content="analyze this", context={"paradigm": "natural_language"})

        mock_event = MagicMock()
        mock_event.event_id = "evt-1"
        mock_event.paradigm = MagicMock(value="natural_language")
        mock_event.payload = {"result": "ok"}
        mock_event.tags = ["tag1"]

        mock_intermediary = AsyncMock()
        mock_intermediary.handle = AsyncMock(return_value=mock_event)

        mock_paradigm = MagicMock()
        mock_paradigm.NATURAL_LANGUAGE = "natural_language"

        def mock_paradigm_constructor(val):
            return val

        mock_cognitive_paradigm = MagicMock(side_effect=mock_paradigm_constructor)
        mock_cognitive_paradigm.NATURAL_LANGUAGE = "natural_language"

        mock_intermediary_cls = MagicMock(return_value=mock_intermediary)

        with patch.dict(
            "sys.modules",
            {
                "src.ai.ai_intermediary": MagicMock(
                    AIIntermediary=mock_intermediary_cls,
                    CognitiveParadigm=mock_cognitive_paradigm,
                )
            },
        ):
            result = await router._route_to_intermediary(task)
        assert result["status"] == "success"
        assert result["agent"] == "intermediary"

    @pytest.mark.asyncio
    async def test_import_error_returns_failed(self, router: AgentTaskRouter):
        task = make_task(context={})
        with patch.dict("sys.modules", {"src.ai.ai_intermediary": None}):
            result = await router._route_to_intermediary(task)
        assert result["status"] == "failed"
        assert result["agent"] == "intermediary"


# ===========================================================================
# _route_to_skyclaw — lines 3472-3622
# ===========================================================================


class TestRouteToSkyClaw:
    @pytest.mark.asyncio
    async def test_no_binary_falls_back_to_ollama(self, router: AgentTaskRouter, tmp_path: Path):
        """When SkyClaw binary not found, should fall back to Ollama."""
        router.repo_root = tmp_path
        task = make_task(content="analyze this", context={})

        mock_ollama_result = {"status": "success", "system": "ollama", "output": "result"}
        with (
            patch.object(router, "_route_to_ollama", new=AsyncMock(return_value=mock_ollama_result)),
            patch("sys.platform", "linux"),
        ):
            result = await router._route_to_skyclaw(task)
        assert result["status"] == "success"
        assert result["system"] == "ollama"

    @pytest.mark.asyncio
    async def test_binary_found_success_json(self, router: AgentTaskRouter, tmp_path: Path):
        """SkyClaw binary present + successful json output."""
        skyclaw_dir = tmp_path / "state" / "runtime" / "skyclaw" / "target" / "debug"
        skyclaw_dir.mkdir(parents=True)
        binary = skyclaw_dir / "skyclaw"
        binary.write_text("#!/bin/bash\necho '{\"result\": \"ok\"}'")

        router.repo_root = tmp_path
        task = make_task(content="analyze this", context={"action": "analyze", "output_format": "json"})

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b'{"result": "ok"}', b""))

        with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=mock_proc)):
            result = await router._route_to_skyclaw(task)
        assert result["status"] == "success"
        assert result["agent"] == "skyclaw"
        assert result["result"] == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_binary_nonzero_exit_returns_failed(self, router: AgentTaskRouter, tmp_path: Path):
        skyclaw_dir = tmp_path / "state" / "runtime" / "skyclaw" / "target" / "debug"
        skyclaw_dir.mkdir(parents=True)
        binary = skyclaw_dir / "skyclaw"
        binary.write_text("stub")

        router.repo_root = tmp_path
        task = make_task(content="test", context={})

        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(b"", b"error msg"))

        with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=mock_proc)):
            result = await router._route_to_skyclaw(task)
        assert result["status"] == "failed"
        assert "error msg" in result["error"]

    @pytest.mark.asyncio
    async def test_timeout_returns_failed(self, router: AgentTaskRouter, tmp_path: Path):
        skyclaw_dir = tmp_path / "state" / "runtime" / "skyclaw" / "target" / "debug"
        skyclaw_dir.mkdir(parents=True)
        (skyclaw_dir / "skyclaw").write_text("stub")

        router.repo_root = tmp_path
        task = make_task(content="test", context={"timeout_s": 1})

        mock_proc = AsyncMock()
        mock_proc.returncode = None
        mock_proc.communicate = AsyncMock(side_effect=TimeoutError())

        with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=mock_proc)):
            result = await router._route_to_skyclaw(task)
        assert result["status"] == "failed"
        assert "timed out" in result["error"].lower()


# ===========================================================================
# health_check — lines 3657-3802
# ===========================================================================


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_returns_systems_dict(self, router: AgentTaskRouter):
        result = await router.health_check()
        assert "systems" in result
        assert "timestamp" in result
        assert "ollama" in result["systems"]
        assert "factory" in result["systems"]
        assert "orchestration" in result["systems"]

    @pytest.mark.asyncio
    async def test_health_check_metadata_mode_ollama(self, router: AgentTaskRouter, monkeypatch):
        monkeypatch.delenv("NUSYQ_ROUTER_HEALTH_NETWORK", raising=False)
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
        result = await router.health_check()
        assert result["systems"]["ollama"]["check_mode"] == "metadata"

    @pytest.mark.asyncio
    async def test_health_check_factory_metadata_mode(self, router: AgentTaskRouter, monkeypatch):
        monkeypatch.delenv("NUSYQ_ROUTER_FACTORY_HEALTH_MODE", raising=False)
        result = await router.health_check()
        factory_status = result["systems"]["factory"]
        if factory_status.get("check_mode"):
            assert factory_status["check_mode"] == "metadata"

    @pytest.mark.asyncio
    async def test_health_check_consciousness_bridge_import_error(
        self, router: AgentTaskRouter
    ):
        with patch.dict("sys.modules", {"src.integration.consciousness_bridge": None}):
            result = await router.health_check()
        assert "consciousness_bridge" in result["systems"]


# ===========================================================================
# _route_to_devtool — lines 3808-3917
# ===========================================================================


class TestRouteToDevtool:
    @pytest.mark.asyncio
    async def test_import_error_returns_failed(self, router: AgentTaskRouter):
        task = make_task(context={})
        with patch.dict("sys.modules", {"src.integrations.devtool_bridge": None}):
            result = await router._route_to_devtool(task)
        assert result["status"] == "failed"
        assert result["agent"] == "devtool"

    @pytest.mark.asyncio
    async def test_not_operational_returns_failed(self, router: AgentTaskRouter):
        task = make_task(context={"action": "navigate"})
        mock_bridge = MagicMock()
        mock_bridge.is_operational.return_value = False
        mock_bridge_cls = MagicMock(return_value=mock_bridge)
        mock_mod = MagicMock()
        mock_mod.DevToolBridge = mock_bridge_cls
        mock_mod.DEVTOOL_MCP_TOOLS = []
        with patch.dict("sys.modules", {"src.integrations.devtool_bridge": mock_mod}):
            result = await router._route_to_devtool(task)
        assert result["status"] == "failed"
        assert "browser" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_operational_returns_success(self, router: AgentTaskRouter):
        task = make_task(context={"action": "screenshot"})
        mock_bridge = MagicMock()
        mock_bridge.is_operational.return_value = True
        mock_bridge.probe_browser.return_value = MagicMock(path="/usr/bin/chromium")
        mock_bridge.probe_edge_fallback.return_value = MagicMock(path=None)
        mock_status = MagicMock()
        mock_status.chrome_available = True
        mock_status.categories = ["navigation", "dom"]
        mock_bridge.get_status.return_value = mock_status
        mock_bridge_cls = MagicMock(return_value=mock_bridge)
        mock_mod = MagicMock()
        mock_mod.DevToolBridge = mock_bridge_cls
        mock_mod.DEVTOOL_MCP_TOOLS = ["t1", "t2", "t3"]
        with patch.dict("sys.modules", {"src.integrations.devtool_bridge": mock_mod}):
            result = await router._route_to_devtool(task)
        assert result["status"] == "success"
        assert result["agent"] == "devtool"
        assert result["tool_count"] == 3


# ===========================================================================
# GitKraken helpers — lines 3919-3961
# ===========================================================================


class TestGitKrakenHelpers:
    def test_looks_like_gitkraken_task_operation_field(self, router: AgentTaskRouter):
        task = make_task(context={"operation": "commit"})
        assert router._looks_like_gitkraken_task(task) is True

    def test_looks_like_gitkraken_task_content_marker(self, router: AgentTaskRouter):
        task = make_task(content="git status of the repo", context={})
        assert router._looks_like_gitkraken_task(task) is True

    def test_looks_like_gitkraken_task_no_markers(self, router: AgentTaskRouter):
        task = make_task(content="analyze performance", context={})
        assert router._looks_like_gitkraken_task(task) is False

    def test_infer_gitkraken_operation_explicit(self, router: AgentTaskRouter):
        task = make_task(context={"operation": "blame"})
        assert router._infer_gitkraken_operation(task) == "blame"

    def test_infer_gitkraken_operation_push_from_content(self, router: AgentTaskRouter):
        task = make_task(content="push changes to origin", context={})
        assert router._infer_gitkraken_operation(task) == "push"

    def test_infer_gitkraken_operation_commit_from_content(self, router: AgentTaskRouter):
        task = make_task(content="stage and commit my files", context={})
        assert router._infer_gitkraken_operation(task) == "commit"

    def test_infer_gitkraken_operation_default_status(self, router: AgentTaskRouter):
        task = make_task(content="what is going on?", context={})
        assert router._infer_gitkraken_operation(task) == "status"

    def test_extract_commit_message_double_quoted(self, router: AgentTaskRouter):
        msg = router._extract_commit_message('commit with message "fix: update tests"')
        assert msg == "fix: update tests"

    def test_extract_commit_message_single_quoted(self, router: AgentTaskRouter):
        msg = router._extract_commit_message("message 'feat: add feature'")
        assert msg == "feat: add feature"

    def test_extract_commit_message_none(self, router: AgentTaskRouter):
        msg = router._extract_commit_message("no message here")
        assert msg == ""

    def test_build_gitkraken_parameters_status(self, router: AgentTaskRouter):
        task = make_task(context={})
        params = router._build_gitkraken_parameters(task, "status")
        assert "short" in params
        assert "porcelain" in params

    def test_build_gitkraken_parameters_commit(self, router: AgentTaskRouter):
        task = make_task(content='commit "fix: test"', context={"files": ["a.py"]})
        params = router._build_gitkraken_parameters(task, "commit")
        assert params["files"] == ["a.py"]
        assert params["message"] == "fix: test"

    def test_build_gitkraken_parameters_push(self, router: AgentTaskRouter):
        task = make_task(content="push branch 'main' to remote 'origin'", context={})
        params = router._build_gitkraken_parameters(task, "push")
        assert params["branch"] == "main"
        assert params["remote"] == "origin"

    def test_build_gitkraken_parameters_unknown(self, router: AgentTaskRouter):
        task = make_task(context={})
        params = router._build_gitkraken_parameters(task, "unknown_op")
        assert "repo_path" in params


# ===========================================================================
# _route_to_gitkraken — lines 4007-4108
# ===========================================================================


class TestRouteToGitKraken:
    @pytest.mark.asyncio
    async def test_import_error_returns_failed(self, router: AgentTaskRouter):
        task = make_task(context={})
        with patch.dict("sys.modules", {"src.integrations.gitkraken_bridge": None}):
            result = await router._route_to_gitkraken(task)
        assert result["status"] == "failed"
        assert result["agent"] == "gitkraken"

    @pytest.mark.asyncio
    async def test_unavailable_bridge_returns_failed(self, router: AgentTaskRouter):
        task = make_task(context={"operation": "status"})
        mock_bridge = MagicMock()
        mock_status = MagicMock()
        mock_status.available = False
        mock_status.message = "GitKraken not found"
        mock_bridge.probe.return_value = mock_status
        mock_bridge_cls = MagicMock(return_value=mock_bridge)
        mock_mod = MagicMock()
        mock_mod.GitKrakenBridge = mock_bridge_cls
        mock_mod.GITKRAKEN_MCP_TOOLS = []
        with patch.dict("sys.modules", {"src.integrations.gitkraken_bridge": mock_mod}):
            result = await router._route_to_gitkraken(task)
        assert result["status"] == "failed"
        assert "GitKraken not found" in result["error"]

    @pytest.mark.asyncio
    async def test_status_operation_executes(self, router: AgentTaskRouter):
        task = make_task(context={"operation": "status"})
        mock_bridge = MagicMock()
        mock_status = MagicMock()
        mock_status.available = True
        mock_status.providers_detected = ["github"]
        mock_status.gitlens_available = True
        mock_bridge.probe.return_value = mock_status
        mock_bridge.execute_git_operation = MagicMock(return_value={"status": "success"})
        mock_bridge_cls = MagicMock(return_value=mock_bridge)
        mock_mod = MagicMock()
        mock_mod.GitKrakenBridge = mock_bridge_cls
        mock_mod.GITKRAKEN_MCP_TOOLS = ["t1", "t2"]
        with patch.dict("sys.modules", {"src.integrations.gitkraken_bridge": mock_mod}):
            result = await router._route_to_gitkraken(task)
        assert result["agent"] == "gitkraken"

    @pytest.mark.asyncio
    async def test_non_executable_operation_returns_ready(self, router: AgentTaskRouter):
        task = make_task(content="start code review", context={"operation": "start_review"})
        mock_bridge = MagicMock()
        mock_status = MagicMock()
        mock_status.available = True
        mock_status.providers_detected = []
        mock_status.gitlens_available = False
        mock_bridge.probe.return_value = mock_status
        mock_bridge_cls = MagicMock(return_value=mock_bridge)
        mock_mod = MagicMock()
        mock_mod.GitKrakenBridge = mock_bridge_cls
        mock_mod.GITKRAKEN_MCP_TOOLS = []
        with patch.dict("sys.modules", {"src.integrations.gitkraken_bridge": mock_mod}):
            result = await router._route_to_gitkraken(task)
        assert result["status"] == "ready"


# ===========================================================================
# _route_to_huggingface — lines 4110-4179
# ===========================================================================


class TestRouteToHuggingFace:
    @pytest.mark.asyncio
    async def test_import_error_returns_failed(self, router: AgentTaskRouter):
        task = make_task(context={})
        with patch.dict("sys.modules", {"src.integrations.huggingface_bridge": None}):
            result = await router._route_to_huggingface(task)
        assert result["status"] == "failed"
        assert result["agent"] == "huggingface"

    @pytest.mark.asyncio
    async def test_ready_status_returned(self, router: AgentTaskRouter):
        task = make_task(context={"search_type": "model"})
        mock_bridge = MagicMock()
        mock_status = MagicMock()
        mock_status.available = True
        mock_status.authenticated = True
        mock_status.username = "testuser"
        mock_bridge.probe.return_value = mock_status
        mock_bridge_cls = MagicMock(return_value=mock_bridge)
        mock_mod = MagicMock()
        mock_mod.HuggingFaceBridge = mock_bridge_cls
        mock_mod.HUGGINGFACE_MCP_TOOLS = ["t1", "t2"]
        with patch.dict("sys.modules", {"src.integrations.huggingface_bridge": mock_mod}):
            result = await router._route_to_huggingface(task)
        assert result["status"] == "ready"
        assert result["agent"] == "huggingface"
        assert result["suggested_mcp_tool"] == "mcp_evalstate_hf-_model_search"


# ===========================================================================
# _route_to_dbclient — lines 4181-4246
# ===========================================================================


class TestRouteToDbClient:
    @pytest.mark.asyncio
    async def test_import_error_returns_failed(self, router: AgentTaskRouter):
        task = make_task(context={})
        with patch.dict("sys.modules", {"src.integrations.dbclient_bridge": None}):
            result = await router._route_to_dbclient(task)
        assert result["status"] == "failed"
        assert result["agent"] == "dbclient"

    @pytest.mark.asyncio
    async def test_ready_status_with_query(self, router: AgentTaskRouter):
        task = make_task(context={"query": "SELECT 1", "database": "nusyq_state"})
        mock_bridge = MagicMock()
        mock_status = MagicMock()
        mock_status.available = True
        mock_status.nusyq_state_db = MagicMock(size_bytes=1024 * 1024)
        mock_bridge.probe.return_value = mock_status
        mock_bridge.get_common_queries.return_value = []
        mock_bridge_cls = MagicMock(return_value=mock_bridge)
        mock_mod = MagicMock()
        mock_mod.DBClientBridge = mock_bridge_cls
        mock_mod.DBCLIENT_MCP_TOOLS = ["t1", "t2", "t3"]
        with patch.dict("sys.modules", {"src.integrations.dbclient_bridge": mock_mod}):
            result = await router._route_to_dbclient(task)
        assert result["status"] == "ready"
        assert result["suggested_mcp_tool"] == "dbclient-execute-query"
        assert result["state_db_size_mb"] == pytest.approx(1.0)

    @pytest.mark.asyncio
    async def test_ready_status_no_query_suggests_tables(self, router: AgentTaskRouter):
        task = make_task(context={})
        mock_bridge = MagicMock()
        mock_status = MagicMock()
        mock_status.available = True
        mock_status.nusyq_state_db = None
        mock_bridge.probe.return_value = mock_status
        mock_bridge.get_common_queries.return_value = ["SELECT * FROM tasks"]
        mock_bridge_cls = MagicMock(return_value=mock_bridge)
        mock_mod = MagicMock()
        mock_mod.DBClientBridge = mock_bridge_cls
        mock_mod.DBCLIENT_MCP_TOOLS = []
        with patch.dict("sys.modules", {"src.integrations.dbclient_bridge": mock_mod}):
            result = await router._route_to_dbclient(task)
        assert result["suggested_mcp_tool"] == "dbclient-get-tables"


# ===========================================================================
# _route_to_neural_ml — lines 4248-4361
# ===========================================================================


class TestRouteToNeuralMl:
    @pytest.mark.asyncio
    async def test_import_error_returns_failed(self, router: AgentTaskRouter):
        task = make_task(context={})
        with patch.dict("sys.modules", {"src.ml": None}):
            result = await router._route_to_neural_ml(task)
        assert result["status"] == "failed"
        assert result["agent"] == "neural_ml"

    @pytest.mark.asyncio
    async def test_status_operation(self, router: AgentTaskRouter):
        task = make_task(context={"operation": "status"})
        mock_mod = MagicMock()
        with patch.dict("sys.modules", {"src.ml": mock_mod}):
            result = await router._route_to_neural_ml(task)
        assert result["status"] == "ready"
        assert result["agent"] == "neural_ml"
        assert "operations" in result

    @pytest.mark.asyncio
    async def test_train_operation(self, router: AgentTaskRouter):
        task = make_task(context={"operation": "train", "data": {"x": [1, 2]}, "model_type": "test"})
        mock_ml_system = AsyncMock()
        mock_ml_system.train_consciousness_enhanced_model = AsyncMock(return_value={"trained": True})
        mock_mod = MagicMock()
        mock_mod.ConsciousnessEnhancedMLSystem = MagicMock(return_value=mock_ml_system)
        with patch.dict("sys.modules", {"src.ml": mock_mod}):
            result = await router._route_to_neural_ml(task)
        assert result["status"] == "success"
        assert result["operation"] == "train"

    @pytest.mark.asyncio
    async def test_predict_operation(self, router: AgentTaskRouter):
        task = make_task(context={"operation": "predict", "data": {"x": [1]}, "use_quantum": False})
        mock_ml_system = AsyncMock()
        mock_ml_system.predict_with_consciousness = AsyncMock(return_value={"prediction": 42})
        mock_mod = MagicMock()
        mock_mod.ConsciousnessEnhancedMLSystem = MagicMock(return_value=mock_ml_system)
        with patch.dict("sys.modules", {"src.ml": mock_mod}):
            result = await router._route_to_neural_ml(task)
        assert result["status"] == "success"
        assert result["operation"] == "predict"

    @pytest.mark.asyncio
    async def test_analyze_operation(self, router: AgentTaskRouter):
        task = make_task(content="dataset", context={"operation": "analyze"})
        mock_analyzer = AsyncMock()
        mock_analyzer.analyze_patterns_with_consciousness = AsyncMock(
            return_value={"patterns": ["p1"]}
        )
        mock_mod = MagicMock()
        mock_mod.PatternConsciousnessAnalyzer = MagicMock(return_value=mock_analyzer)
        with patch.dict("sys.modules", {"src.ml": mock_mod}):
            result = await router._route_to_neural_ml(task)
        assert result["status"] == "success"
        assert result["operation"] == "analyze"

    @pytest.mark.asyncio
    async def test_unknown_operation_returns_failed(self, router: AgentTaskRouter):
        task = make_task(context={"operation": "explode"})
        mock_mod = MagicMock()
        with patch.dict("sys.modules", {"src.ml": mock_mod}):
            result = await router._route_to_neural_ml(task)
        assert result["status"] == "failed"
        assert "Unknown operation" in result["error"]
