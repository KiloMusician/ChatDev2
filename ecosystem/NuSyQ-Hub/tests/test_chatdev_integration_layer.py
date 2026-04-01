"""Tests for ChatDev integration layer: service, resilience handler, and MCP integration."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# ChatDevService tests
# ---------------------------------------------------------------------------

from src.integration.chatdev_service import ChatDevService, SubprocessResult


class TestSubprocessResult:
    def test_success_true_when_returncode_zero(self):
        r = SubprocessResult(command=["echo"], returncode=0, stdout="hi", stderr="")
        assert r.success is True

    def test_success_false_when_nonzero(self):
        r = SubprocessResult(command=["false"], returncode=1, stdout="", stderr="err")
        assert r.success is False


class TestChatDevServiceInit:
    def test_default_active_is_false(self):
        svc = ChatDevService()
        assert svc.active is False

    def test_config_merged_with_env(self, monkeypatch):
        monkeypatch.setenv("CHATDEV_API_KEY", "env-key")
        svc = ChatDevService(config={"CHATDEV_API_KEY": "override"})
        assert svc.config["CHATDEV_API_KEY"] == "override"

    def test_chatdev_path_none_when_not_set(self, monkeypatch):
        monkeypatch.delenv("CHATDEV_PATH", raising=False)
        svc = ChatDevService()
        assert svc.chatdev_path is None

    def test_chatdev_path_set_from_config(self, tmp_path):
        svc = ChatDevService(config={"CHATDEV_PATH": str(tmp_path)})
        assert svc.chatdev_path == tmp_path


class TestChatDevServiceStart:
    def test_start_returns_already_running_when_active(self, tmp_path):
        run_py = tmp_path / "run.py"
        run_py.touch()
        svc = ChatDevService(config={"CHATDEV_PATH": str(tmp_path)})
        svc.active = True
        result = svc.start()
        assert result["success"] is True
        assert "already running" in result["message"]

    def test_start_fails_when_no_chatdev_path(self, monkeypatch):
        monkeypatch.delenv("CHATDEV_PATH", raising=False)
        svc = ChatDevService()
        result = svc.start()
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_start_fails_when_entrypoint_missing(self, tmp_path):
        svc = ChatDevService(config={"CHATDEV_PATH": str(tmp_path)})
        result = svc.start()
        assert result["success"] is False

    def test_start_succeeds_with_run_py(self, tmp_path):
        (tmp_path / "run.py").touch()
        svc = ChatDevService(config={"CHATDEV_PATH": str(tmp_path)})
        result = svc.start()
        assert result["success"] is True
        assert svc.active is True

    def test_start_succeeds_with_run_ollama_py(self, tmp_path):
        (tmp_path / "run_ollama.py").touch()
        svc = ChatDevService(config={"CHATDEV_PATH": str(tmp_path)})
        result = svc.start()
        assert result["success"] is True

    def test_start_sets_active_true(self, tmp_path):
        (tmp_path / "run.py").touch()
        svc = ChatDevService(config={"CHATDEV_PATH": str(tmp_path)})
        assert svc.active is False
        svc.start()
        assert svc.active is True


class TestChatDevServiceStop:
    def test_stop_sets_active_false(self, tmp_path):
        (tmp_path / "run.py").touch()
        svc = ChatDevService(config={"CHATDEV_PATH": str(tmp_path)})
        svc.active = True
        svc.stop()
        assert svc.active is False


class TestChatDevServiceSendRequest:
    def test_send_request_no_chatdev_path(self, monkeypatch):
        monkeypatch.delenv("CHATDEV_PATH", raising=False)
        svc = ChatDevService()
        result = svc.send_request(["--task", "hello"])
        assert result.returncode == -1

    def test_send_request_start_fails_returns_error_result(self, tmp_path):
        svc = ChatDevService(config={"CHATDEV_PATH": str(tmp_path)})
        result = svc.send_request(["--task", "hello"])
        assert result.returncode == -1

    def test_send_request_calls_subprocess_run(self, tmp_path):
        (tmp_path / "run.py").touch()
        svc = ChatDevService(config={"CHATDEV_PATH": str(tmp_path)})
        mock_completed = MagicMock()
        mock_completed.returncode = 0
        mock_completed.stdout = "done"
        mock_completed.stderr = ""
        with patch("subprocess.run", return_value=mock_completed) as mock_run:
            result = svc.send_request(["--task", "hello"])
        mock_run.assert_called_once()
        assert result.returncode == 0
        assert result.stdout == "done"

    def test_send_request_uses_run_ollama_when_flag_set(self, tmp_path):
        (tmp_path / "run.py").touch()
        (tmp_path / "run_ollama.py").touch()
        svc = ChatDevService(config={
            "CHATDEV_PATH": str(tmp_path),
            "CHATDEV_USE_OLLAMA": "1",
        })
        mock_completed = MagicMock()
        mock_completed.returncode = 0
        mock_completed.stdout = ""
        mock_completed.stderr = ""
        with patch("subprocess.run", return_value=mock_completed) as mock_run:
            svc.send_request(["--task", "test"])
        called_cmd = mock_run.call_args[0][0]
        assert "run_ollama.py" in called_cmd

    def test_send_request_auto_starts_service(self, tmp_path):
        (tmp_path / "run.py").touch()
        svc = ChatDevService(config={"CHATDEV_PATH": str(tmp_path)})
        assert svc.active is False
        mock_completed = MagicMock(returncode=0, stdout="", stderr="")
        with patch("subprocess.run", return_value=mock_completed):
            svc.send_request([])
        assert svc.active is True


# ---------------------------------------------------------------------------
# ChatDevResilienceHandler tests
# ---------------------------------------------------------------------------

from src.integration.chatdev_resilience_handler import (
    ResilientChatDevHandler,
    execute_chatdev_resilient,
    load_resilience_config,
    create_resilient_handler_with_ollama_fallback,
)
from src.resilience.checkpoint_retry_degraded import (
    DegradedModeConfig,
    RetryPolicy,
)


class TestResilientChatDevHandlerInit:
    def test_default_init(self):
        handler = ResilientChatDevHandler()
        assert handler.retry_policy is not None
        assert handler.degraded_config is not None
        assert handler.audit_log is not None
        assert handler.attestation_mgr is not None

    def test_custom_retry_policy(self):
        policy = RetryPolicy(max_attempts=1)
        handler = ResilientChatDevHandler(retry_policy=policy)
        assert handler.retry_policy.max_attempts == 1


class TestResilientChatDevHandlerExecute:
    @pytest.mark.asyncio
    async def test_execute_with_custom_primary_runner_succeeds(self):
        async def my_primary(task, model, name=None):
            return {"project_name": "test", "files": [], "status": "done"}

        handler = ResilientChatDevHandler(
            primary_runner=my_primary,
            retry_policy=RetryPolicy(max_attempts=1, initial_delay=0),
        )
        result = await handler.execute_generate_project(task="Build something")
        assert result["success"] is True
        assert result["execution_mode"] == "primary"
        assert "attestation_hash" in result

    @pytest.mark.asyncio
    async def test_execute_with_failing_primary_and_degraded_fallback(self):
        async def failing_primary(task, model, name=None):
            raise RuntimeError("primary unavailable")

        async def degraded_fallback(task, model=None, name=None, **kwargs):
            return {"project_name": "fallback", "files": [], "status": "degraded"}

        handler = ResilientChatDevHandler(
            primary_runner=failing_primary,
            degraded_runner=degraded_fallback,
            retry_policy=RetryPolicy(max_attempts=1, initial_delay=0),
            degraded_config=DegradedModeConfig(enabled=True),
        )
        result = await handler.execute_generate_project(task="Build something")
        assert result["success"] is True
        assert result["execution_mode"] == "degraded"
        assert result["fallback_applied"] is True

    @pytest.mark.asyncio
    async def test_execute_all_modes_fail_returns_failure(self):
        async def failing_primary(task, model, name=None):
            raise RuntimeError("broken")

        handler = ResilientChatDevHandler(
            primary_runner=failing_primary,
            degraded_runner=None,
            retry_policy=RetryPolicy(max_attempts=1, initial_delay=0),
            degraded_config=DegradedModeConfig(enabled=False),
        )
        result = await handler.execute_generate_project(task="impossible")
        assert result["success"] is False
        assert "execution_mode" in result

    @pytest.mark.asyncio
    async def test_execute_unexpected_exception_caught(self):
        def sync_bad_primary(**kwargs):
            raise ValueError("explode")

        handler = ResilientChatDevHandler(
            primary_runner=sync_bad_primary,
            retry_policy=RetryPolicy(max_attempts=1, initial_delay=0),
            degraded_config=DegradedModeConfig(enabled=False),
        )
        result = await handler.execute_generate_project(task="boom")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_audit_entries_populated_on_success(self):
        async def my_primary(task, model, name=None):
            return {"status": "ok"}

        handler = ResilientChatDevHandler(
            primary_runner=my_primary,
            retry_policy=RetryPolicy(max_attempts=1, initial_delay=0),
        )
        result = await handler.execute_generate_project(task="audit test")
        assert isinstance(result.get("audit_entries"), list)
        assert len(result["audit_entries"]) > 0

    @pytest.mark.asyncio
    async def test_execute_chatdev_resilient_convenience_wrapper(self):
        async def mock_primary(task, model, name=None):
            return {"status": "complete"}

        with patch.object(ResilientChatDevHandler, "_primary_generate_project", mock_primary):
            result = await execute_chatdev_resilient(task="quick task")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_execute_with_custom_operation_label(self):
        async def my_primary(task, model, name=None):
            return {"status": "ok"}

        handler = ResilientChatDevHandler(
            primary_runner=my_primary,
            retry_policy=RetryPolicy(max_attempts=1, initial_delay=0),
        )
        result = await handler.execute_generate_project(
            task="labeled task", operation="custom_op_label"
        )
        assert result["success"] is True


class TestLoadResilienceConfig:
    def test_returns_dict(self):
        cfg = load_resilience_config()
        assert isinstance(cfg, dict)

    def test_returns_empty_dict_when_open_fails(self):
        with patch("builtins.open", side_effect=OSError("no file")):
            cfg = load_resilience_config()
        assert isinstance(cfg, dict)


class TestCreateResilientHandlerWithOllamaFallback:
    def test_returns_handler_instance(self):
        handler = create_resilient_handler_with_ollama_fallback()
        assert isinstance(handler, ResilientChatDevHandler)
        assert handler.degraded_runner is not None

    def test_handler_has_retry_policy(self):
        handler = create_resilient_handler_with_ollama_fallback()
        assert handler.retry_policy.max_attempts >= 1


# ---------------------------------------------------------------------------
# ChatDevMCPIntegration tests
# ---------------------------------------------------------------------------

from src.integration.chatdev_mcp_integration import (
    ChatDevMCPIntegration,
    get_chatdev_mcp_integration,
)


def _make_integration_initialized():
    integration = ChatDevMCPIntegration()

    tool_mock = MagicMock()
    tool_mock.name = "chatdev_generate"
    tool_mock.description = "Generate project"
    tool_mock.input_schema = {"type": "object"}

    server_mock = MagicMock()
    server_mock.mcp_tools = [tool_mock]
    server_mock.handle_tool_call = MagicMock(return_value={"success": True, "result": "ok"})

    registry_mock = MagicMock()
    run_tests_tool = MagicMock()
    run_tests_tool.name = "run_tests"
    registry_mock.tools = {"run_tests": run_tests_tool}
    registry_mock.export_manifest = MagicMock(return_value=[{"name": "run_tests"}])
    registry_mock.invoke_tool = AsyncMock(return_value={"success": True})

    indexer_mock = MagicMock()
    indexer_mock.indexed_projects = {}
    indexer_mock.documents = []
    indexer_mock.search_projects = MagicMock(return_value=[])
    indexer_mock.index_workspace = MagicMock(return_value=2)

    integration.chatdev_server = server_mock
    integration.tool_registry = registry_mock
    integration.project_indexer = indexer_mock
    integration.is_initialized = True

    return integration


class TestChatDevMCPIntegrationInit:
    def test_not_initialized_on_create(self):
        integration = ChatDevMCPIntegration()
        assert integration.is_initialized is False
        assert integration.registered_tools == []

    def test_get_complete_tool_manifest_empty_when_not_initialized(self):
        integration = ChatDevMCPIntegration()
        assert integration.get_complete_tool_manifest() == []

    def test_list_all_tools_empty_when_not_initialized(self):
        integration = ChatDevMCPIntegration()
        assert integration.list_all_tools() == []


class TestChatDevMCPIntegrationToolManifest:
    def test_get_complete_tool_manifest_includes_chatdev_tools(self):
        integration = _make_integration_initialized()
        manifest = integration.get_complete_tool_manifest()
        names = [t["name"] for t in manifest]
        assert "chatdev_generate" in names

    def test_get_complete_tool_manifest_includes_registry_tools(self):
        integration = _make_integration_initialized()
        manifest = integration.get_complete_tool_manifest()
        names = [t["name"] for t in manifest]
        assert "run_tests" in names

    def test_get_complete_tool_manifest_includes_indexing_tools(self):
        integration = _make_integration_initialized()
        manifest = integration.get_complete_tool_manifest()
        names = [t["name"] for t in manifest]
        for expected in ["chatdev_search_projects", "chatdev_index_workspace", "chatdev_project_summary"]:
            assert expected in names

    def test_list_all_tools_returns_sorted_list(self):
        integration = _make_integration_initialized()
        tools = integration.list_all_tools()
        assert tools == sorted(tools)
        assert "chatdev_search_projects" in tools


class TestChatDevMCPIntegrationHandleToolCall:
    @pytest.mark.asyncio
    async def test_handle_tool_call_not_initialized_returns_error(self):
        integration = ChatDevMCPIntegration()
        result = await integration.handle_tool_call("chatdev_generate", {})
        assert result["success"] is False
        assert "not initialized" in result["error"]

    @pytest.mark.asyncio
    async def test_handle_unknown_tool_returns_error(self):
        integration = _make_integration_initialized()
        result = await integration.handle_tool_call("unknown_tool_xyz", {})
        assert result["success"] is False
        assert "Unknown tool" in result["error"]

    @pytest.mark.asyncio
    async def test_handle_chatdev_server_tool_call(self):
        integration = _make_integration_initialized()
        result = await integration.handle_tool_call("chatdev_generate", {"task": "build x"})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_handle_run_prefix_routes_to_registry(self):
        integration = _make_integration_initialized()
        result = await integration.handle_tool_call("run_tests", {"path": "."})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_handle_search_projects_success(self):
        integration = _make_integration_initialized()
        integration.project_indexer.search_projects.return_value = [{"name": "proj1"}]
        result = await integration.handle_tool_call("chatdev_search_projects", {"query": "cli app"})
        assert result["success"] is True
        assert result["results_count"] == 1

    @pytest.mark.asyncio
    async def test_handle_index_workspace_success(self):
        integration = _make_integration_initialized()
        result = await integration.handle_tool_call("chatdev_index_workspace", {"start_fresh": True})
        assert result["success"] is True
        assert result["indexed_projects"] == 2

    @pytest.mark.asyncio
    async def test_handle_project_summary_not_found(self):
        integration = _make_integration_initialized()
        result = await integration.handle_tool_call(
            "chatdev_project_summary", {"project_name": "ghost"}
        )
        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_handle_project_summary_found(self):
        integration = _make_integration_initialized()

        class SimpleProject:
            def __init__(self):
                self.name = "myproject"
                self.path = "/tmp/myproject"

        proj = SimpleProject()
        # Reset to a fresh MagicMock to avoid state bleed from prior tests
        from unittest.mock import MagicMock
        integration.project_indexer = MagicMock()
        integration.project_indexer.indexed_projects = {"myproject": proj}
        integration.project_indexer.search_projects = MagicMock(return_value=[])
        result = await integration.handle_tool_call(
            "chatdev_project_summary", {"project_name": "myproject"}
        )
        assert result["success"] is True
        assert "project" in result

    @pytest.mark.asyncio
    async def test_handle_search_projects_exception_returns_error(self):
        integration = _make_integration_initialized()
        integration.project_indexer.search_projects.side_effect = RuntimeError("db gone")
        result = await integration.handle_tool_call("chatdev_search_projects", {"query": "x"})
        assert result["success"] is False
        assert "db gone" in result["error"]


class TestGetChatDevMCPIntegrationSingleton:
    def test_returns_same_instance(self):
        import src.integration.chatdev_mcp_integration as mod
        mod._integration = None
        a = get_chatdev_mcp_integration()
        b = get_chatdev_mcp_integration()
        assert a is b
        mod._integration = None

    def test_returns_chatdev_mcp_integration_type(self):
        import src.integration.chatdev_mcp_integration as mod
        mod._integration = None
        inst = get_chatdev_mcp_integration()
        assert isinstance(inst, ChatDevMCPIntegration)
        mod._integration = None
