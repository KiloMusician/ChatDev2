"""Tests for AgentTaskRouter routing paths — covering lines 420-1003."""
from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.orchestration.unified_ai_orchestrator import OrchestrationTask, TaskPriority
from src.tools.agent_task_router import AgentTaskRouter, TARGET_SYSTEM_ALIASES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_task(
    task_type: str = "analyze",
    content: str = "test content",
    context: dict[str, Any] | None = None,
    task_id: str = "task-001",
) -> OrchestrationTask:
    return OrchestrationTask(
        task_id=task_id,
        task_type=task_type,
        content=content,
        context=context if context is not None else {},
    )


def _make_router(tmp_path: Path | None = None) -> AgentTaskRouter:
    root = tmp_path if tmp_path is not None else Path(__file__).resolve().parents[1]
    router = AgentTaskRouter(repo_root=root)
    # Pin orchestrator so submit_task doesn't do real work
    router.orchestrator = MagicMock()
    router.orchestrator.submit_task.return_value = "submitted-id"
    return router


# ---------------------------------------------------------------------------
# _adaptive_timeout (lines 410-421)
# ---------------------------------------------------------------------------

class TestAdaptiveTimeout:
    def test_default_multiplier_returns_base(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("NUSYQ_ROUTER_TIMEOUT_MULT", None)
            result = router._adaptive_timeout(100)
        assert result == 100

    def test_multiplier_doubles_timeout(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        with patch.dict(os.environ, {"NUSYQ_ROUTER_TIMEOUT_MULT": "2.0"}):
            result = router._adaptive_timeout(100)
        assert result == 200

    def test_minimum_is_30(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        with patch.dict(os.environ, {"NUSYQ_ROUTER_TIMEOUT_MULT": "0.01"}):
            result = router._adaptive_timeout(100)
        assert result == 30

    def test_invalid_multiplier_returns_base(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        with patch.dict(os.environ, {"NUSYQ_ROUTER_TIMEOUT_MULT": "not_a_number"}):
            result = router._adaptive_timeout(60)
        assert result == 60

    def test_fractional_multiplier(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        with patch.dict(os.environ, {"NUSYQ_ROUTER_TIMEOUT_MULT": "1.5"}):
            result = router._adaptive_timeout(200)
        assert result == 300


# ---------------------------------------------------------------------------
# _warn_with_cooldown (lines 390-403)
# ---------------------------------------------------------------------------

class TestWarnWithCooldown:
    def test_first_call_emits_warning(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        with patch("src.tools.agent_task_router.logger") as mock_logger:
            router._warn_with_cooldown("test-key", "Test warning message")
            mock_logger.warning.assert_called_once()

    def test_repeat_within_cooldown_emits_debug(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        # Seed the last_warning time to "now" so next call is within cooldown
        router._last_warning_at["test-key"] = time.monotonic()
        with patch("src.tools.agent_task_router.logger") as mock_logger:
            router._warn_with_cooldown("test-key", "Test warning message")
            mock_logger.warning.assert_not_called()
            mock_logger.debug.assert_called()

    def test_after_cooldown_emits_warning_again(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        # Set last_warning far in the past (beyond cooldown)
        router._last_warning_at["test-key"] = time.monotonic() - 99999
        with patch("src.tools.agent_task_router.logger") as mock_logger:
            router._warn_with_cooldown("test-key", "Test warning message")
            mock_logger.warning.assert_called_once()

    def test_different_keys_are_independent(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        # Pin key-a to now, but key-b is fresh
        router._last_warning_at["key-a"] = time.monotonic()
        with patch("src.tools.agent_task_router.logger") as mock_logger:
            router._warn_with_cooldown("key-b", "New warning")
            mock_logger.warning.assert_called_once()


# ---------------------------------------------------------------------------
# _resolve_target_alias (lines 406-408)
# ---------------------------------------------------------------------------

class TestResolveTargetAlias:
    def test_known_alias_vscode_copilot(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        assert router._resolve_target_alias("vscode_copilot") == "copilot"

    def test_known_alias_claude(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        assert router._resolve_target_alias("claude") == "claude_cli"

    def test_known_alias_git(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        assert router._resolve_target_alias("git") == "gitkraken"

    def test_known_alias_browser(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        assert router._resolve_target_alias("browser") == "devtool"

    def test_known_alias_hf(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        assert router._resolve_target_alias("hf") == "huggingface"

    def test_known_alias_db(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        assert router._resolve_target_alias("db") == "dbclient"

    def test_unknown_target_returns_itself(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        assert router._resolve_target_alias("totally_unknown") == "totally_unknown"

    def test_case_insensitive_and_stripped(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        assert router._resolve_target_alias("  CLAUDE  ") == "claude_cli"

    def test_direct_target_unchanged(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        assert router._resolve_target_alias("ollama") == "ollama"


# ---------------------------------------------------------------------------
# _build_workspace_awareness (lines 471-577)
# ---------------------------------------------------------------------------

class TestBuildWorkspaceAwareness:
    def test_returns_empty_when_no_files(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        result = router._build_workspace_awareness("ollama", "analyze code", {})
        assert result == {}

    def test_returns_dict_when_awareness_file_exists(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        # Create minimal awareness file
        awareness_dir = tmp_path / "state" / "reports"
        awareness_dir.mkdir(parents=True)
        awareness_file = awareness_dir / "terminal_awareness_latest.json"
        awareness_file.write_text(
            '{"active_session": "test", "terminals": [], "agent_registry": [], "output_surfaces": []}',
            encoding="utf-8",
        )
        router.terminal_awareness_path = awareness_file
        # Even with a snapshot that doesn't exist, should return non-empty result
        result = router._build_workspace_awareness("ollama", "analyze code", {})
        assert isinstance(result, dict)
        assert "active_session" in result

    def test_matches_agent_in_registry(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        awareness_dir = tmp_path / "state" / "reports"
        awareness_dir.mkdir(parents=True)
        awareness_file = awareness_dir / "terminal_awareness_latest.json"
        awareness_file.write_text(
            '{"active_session": "main", "terminals": [], '
            '"agent_registry": [{"agent": "Ollama", "terminals": ["term1"], "purposes": ["analysis"]}], '
            '"output_surfaces": []}',
            encoding="utf-8",
        )
        router.terminal_awareness_path = awareness_file
        result = router._build_workspace_awareness("ollama", "ollama analysis", {})
        assert isinstance(result, dict)
        relevant = result.get("relevant_agents", [])
        assert any(a.get("agent") == "Ollama" for a in relevant)

    def test_hinted_agent_added_even_if_no_match(self, tmp_path: Path) -> None:
        """When hinted agent found via _TARGET_AGENT_LABELS but not in registry, it's still added."""
        router = _make_router(tmp_path)
        awareness_dir = tmp_path / "state" / "reports"
        awareness_dir.mkdir(parents=True)
        awareness_file = awareness_dir / "terminal_awareness_latest.json"
        awareness_file.write_text(
            '{"active_session": "main", "terminals": [], "agent_registry": [], "output_surfaces": []}',
            encoding="utf-8",
        )
        router.terminal_awareness_path = awareness_file
        # "copilot" is in _TARGET_AGENT_LABELS mapping to "Copilot"
        result = router._build_workspace_awareness("copilot", "do something", {})
        relevant = result.get("relevant_agents", [])
        assert any(a.get("agent") == "Copilot" for a in relevant)


# ---------------------------------------------------------------------------
# _route_to_copilot (lines 624-717)
# ---------------------------------------------------------------------------

class TestRouteToCopilot:
    @pytest.mark.asyncio
    async def test_disabled_mode_returns_failed(self, tmp_path: Path) -> None:
        # BRIDGE_MODE check is only reached when copilot CLI binary is absent.
        router = _make_router(tmp_path)
        task = _make_task(content="Review code")
        with patch("shutil.which", return_value=None), patch.dict(os.environ, {"NUSYQ_COPILOT_BRIDGE_MODE": "disabled"}):
            result = await router._route_to_copilot(task)
        assert result["status"] == "failed"
        assert result["system"] == "copilot"
        assert "NUSYQ_COPILOT_BRIDGE_MODE" in result["error"]

    @pytest.mark.asyncio
    async def test_mock_mode_returns_success(self, tmp_path: Path) -> None:
        # BRIDGE_MODE check is only reached when copilot CLI binary is absent.
        router = _make_router(tmp_path)
        task = _make_task(content="Review code")
        with patch("shutil.which", return_value=None), patch.dict(os.environ, {"NUSYQ_COPILOT_BRIDGE_MODE": "mock"}):
            result = await router._route_to_copilot(task)
        assert result["status"] == "success"
        assert result["system"] == "copilot"
        assert result["output"]["mode"] == "mock"
        assert result["output"]["echo"] == "Review code"

    @pytest.mark.asyncio
    async def test_live_mode_import_error_returns_failed(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(content="Review code")
        with patch.dict(os.environ, {"NUSYQ_COPILOT_BRIDGE_MODE": "live"}):
            with patch.dict("sys.modules", {"src.copilot.extension.copilot_extension": None}):
                result = await router._route_to_copilot(task)
        # Should fail gracefully — either import error or extension error
        assert result["system"] == "copilot"
        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_gitkraken_delegation_for_git_tasks(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(content="commit staged changes to git", context={})

        gitkraken_result = {
            "status": "success",
            "system": "gitkraken",
            "task_id": task.task_id,
        }
        router._route_to_gitkraken = AsyncMock(return_value=gitkraken_result)
        router._looks_like_gitkraken_task = MagicMock(return_value=True)

        with patch.dict(os.environ, {"NUSYQ_COPILOT_BRIDGE_MODE": "disabled"}):
            result = await router._route_to_copilot(task)

        assert result["system"] == "copilot"
        assert result.get("delegate_target") == "gitkraken"
        assert result.get("delegated_from") == "copilot"

    @pytest.mark.asyncio
    async def test_live_mode_extension_exception_returns_failed(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(content="Review code")
        mock_ext = MagicMock()
        mock_ext.activate = AsyncMock(side_effect=RuntimeError("connection refused"))
        mock_ext.close = AsyncMock()
        mock_ext_class = MagicMock(return_value=mock_ext)

        with patch.dict(os.environ, {"NUSYQ_COPILOT_BRIDGE_MODE": "live"}):
            with patch("src.tools.agent_task_router.AgentTaskRouter._route_to_copilot.__wrapped__", None, create=True):
                with patch.dict("sys.modules", {}):
                    import sys
                    fake_module = MagicMock()
                    fake_module.CopilotExtension = mock_ext_class
                    sys.modules["src.copilot.extension.copilot_extension"] = fake_module
                    try:
                        result = await router._route_to_copilot(task)
                    finally:
                        del sys.modules["src.copilot.extension.copilot_extension"]
        assert result["status"] == "failed"
        assert result["system"] == "copilot"


# ---------------------------------------------------------------------------
# _route_to_codex (lines 719-803)
# ---------------------------------------------------------------------------

class TestRouteToCodex:
    @pytest.mark.asyncio
    async def test_codex_not_found_returns_failed(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(content="analyze file")
        with patch.dict(os.environ, {"NUSYQ_CODEX_FALLBACK": "off"}):
            with patch("src.utils.rate_limit_guard.RateLimitGuard.is_rate_limited", return_value=False):
                with patch("shutil.which", return_value=None):
                    result = await router._route_to_codex(task)
        assert result["status"] == "failed"
        assert result["system"] == "codex"
        assert result["error"] == "codex_cli_not_found"

    @pytest.mark.asyncio
    async def test_codex_success_path(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(content="analyze file", context={})

        with patch("src.utils.rate_limit_guard.RateLimitGuard.is_rate_limited", return_value=False):
            with patch("shutil.which", return_value="/usr/bin/codex"):
                with patch.object(router, "_run_cli_command", new=AsyncMock(return_value=(0, "output text", ""))):
                    with patch.object(router, "_adaptive_timeout", return_value=300):
                        result = await router._route_to_codex(task)

        assert result["status"] == "success"
        assert result["system"] == "codex"

    @pytest.mark.asyncio
    async def test_codex_timeout_returns_failed(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(content="analyze file", context={})

        async def raise_timeout(*args: Any, **kwargs: Any) -> Any:
            raise TimeoutError()

        with patch.dict(os.environ, {"NUSYQ_CODEX_FALLBACK": "off"}):
            with patch("src.utils.rate_limit_guard.RateLimitGuard.is_rate_limited", return_value=False):
                with patch.object(router, "_route_to_ollama", new=AsyncMock(return_value={"status": "failed"})):
                    with patch.object(router, "_route_to_lmstudio", new=AsyncMock(return_value={"status": "failed"})):
                        with patch("shutil.which", return_value="/usr/bin/codex"):
                            with patch.object(router, "_run_cli_command", new=AsyncMock(side_effect=raise_timeout)):
                                with patch.object(router, "_adaptive_timeout", return_value=10):
                                    result = await router._route_to_codex(task)

        assert result["status"] == "failed"
        assert "timeout" in result["error"]

    @pytest.mark.asyncio
    async def test_codex_oserror_returns_failed(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(content="analyze file", context={})

        with patch.dict(os.environ, {"NUSYQ_CODEX_FALLBACK": "off"}):
            with patch("src.utils.rate_limit_guard.RateLimitGuard.is_rate_limited", return_value=False):
                with patch.object(router, "_route_to_ollama", new=AsyncMock(return_value={"status": "failed"})):
                    with patch.object(router, "_route_to_lmstudio", new=AsyncMock(return_value={"status": "failed"})):
                        with patch("shutil.which", return_value="/usr/bin/codex"):
                            with patch.object(router, "_run_cli_command", new=AsyncMock(side_effect=OSError("exec failed"))):
                                with patch.object(router, "_adaptive_timeout", return_value=10):
                                    result = await router._route_to_codex(task)

        assert result["status"] == "failed"
        assert result["system"] == "codex"
        assert "exec_error" in result["error"]

    @pytest.mark.asyncio
    async def test_codex_nonzero_rc_returns_failed(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(content="analyze file", context={})

        with patch.dict(os.environ, {"NUSYQ_CODEX_FALLBACK": "off"}):
            with patch("src.utils.rate_limit_guard.RateLimitGuard.is_rate_limited", return_value=False):
                with patch("shutil.which", return_value="/usr/bin/codex"):
                    with patch.object(router, "_run_cli_command", new=AsyncMock(return_value=(1, "", "some error"))):
                        with patch.object(router, "_adaptive_timeout", return_value=10):
                            result = await router._route_to_codex(task)

        assert result["status"] == "failed"
        assert "rc=1" in result["error"]


# ---------------------------------------------------------------------------
# _route_to_claude_cli (lines 805-1021)
# ---------------------------------------------------------------------------

class TestRouteToClaudeCli:
    @pytest.mark.asyncio
    async def test_empty_custom_cmd_returns_failed(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(content="review code", context={})
        # Provide a custom command that shlex.split produces empty list
        with patch.dict(os.environ, {"NUSYQ_CLAUDE_CLI_COMMAND": ""}):
            # No binary either
            with patch("shutil.which", return_value=None):
                with patch("src.tools.agent_task_router.AgentTaskRouter._is_wsl_runtime", return_value=False):
                    # No vscode extension binary
                    with patch("pathlib.Path.home", return_value=tmp_path):
                        # Orchestrator import fails
                        with patch.dict("sys.modules", {"src.orchestration.claude_orchestrator": None}):
                            result = await router._route_to_claude_cli(task)
        assert result["system"] == "claude_cli"
        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_custom_cmd_success(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(content="review code", context={})

        with patch.dict(os.environ, {"NUSYQ_CLAUDE_CLI_COMMAND": "echo hello"}):
            with patch.object(router, "_run_cli_command", new=AsyncMock(return_value=(0, "hello", ""))):
                with patch.object(router, "_adaptive_timeout", return_value=300):
                    result = await router._route_to_claude_cli(task)

        assert result["status"] == "success"
        assert result["system"] == "claude_cli"
        assert result["mode"] == "cli"

    @pytest.mark.asyncio
    async def test_custom_cmd_timeout_returns_failed(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(content="review code", context={})

        with patch.dict(os.environ, {"NUSYQ_CLAUDE_CLI_COMMAND": "echo hello"}):
            with patch.object(router, "_run_cli_command", new=AsyncMock(side_effect=TimeoutError())):
                with patch.object(router, "_adaptive_timeout", return_value=5):
                    result = await router._route_to_claude_cli(task)

        assert result["status"] == "failed"
        assert "timeout" in result["error"]

    @pytest.mark.asyncio
    async def test_custom_cmd_oserror_returns_failed(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(content="review code", context={})

        with patch.dict(os.environ, {"NUSYQ_CLAUDE_CLI_COMMAND": "echo hello"}):
            with patch.object(router, "_run_cli_command", new=AsyncMock(side_effect=OSError("bad exec"))):
                with patch.object(router, "_adaptive_timeout", return_value=5):
                    result = await router._route_to_claude_cli(task)

        assert result["status"] == "failed"
        assert "exec_error" in result["error"]

    @pytest.mark.asyncio
    async def test_no_bin_falls_through_to_orchestrator_import_error(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(content="review code", context={})

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("NUSYQ_CLAUDE_CLI_COMMAND", None)
            with patch("shutil.which", return_value=None):
                with patch.object(router, "_is_wsl_runtime", return_value=False):
                    with patch("pathlib.Path.home", return_value=tmp_path):
                        import sys
                        sys.modules.pop("src.orchestration.claude_orchestrator", None)
                        # Inject a module that raises ImportError when accessed
                        fake = MagicMock()
                        fake.ClaudeOrchestrator = None
                        # Force import to fail
                        sys.modules["src.orchestration.claude_orchestrator"] = None  # type: ignore[assignment]
                        try:
                            result = await router._route_to_claude_cli(task)
                        finally:
                            sys.modules.pop("src.orchestration.claude_orchestrator", None)

        assert result["system"] == "claude_cli"
        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_orchestrator_success_path(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(content="review code", context={"max_tokens": "256"})

        mock_orchestrator_class = MagicMock()
        mock_orch_instance = MagicMock()
        mock_orch_instance.ask_claude = AsyncMock(
            return_value={"response": "Here is my analysis", "model": "claude-3"}
        )
        mock_orchestrator_class.return_value = mock_orch_instance

        import sys
        fake_mod = MagicMock()
        fake_mod.ClaudeOrchestrator = mock_orchestrator_class
        sys.modules["src.orchestration.claude_orchestrator"] = fake_mod
        try:
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("NUSYQ_CLAUDE_CLI_COMMAND", None)
                with patch("shutil.which", return_value=None):
                    with patch.object(router, "_is_wsl_runtime", return_value=False):
                        with patch("pathlib.Path.home", return_value=tmp_path):
                            result = await router._route_to_claude_cli(task)
        finally:
            sys.modules.pop("src.orchestration.claude_orchestrator", None)

        assert result["status"] == "success"
        assert result["system"] == "claude_cli"
        assert result["mode"] == "api"

    @pytest.mark.asyncio
    async def test_auth_failure_in_stderr_returns_auth_error(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(content="review code", context={})

        # Simulate a candidate that fails with auth error text
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("NUSYQ_CLAUDE_CLI_COMMAND", None)
            with patch("shutil.which", side_effect=lambda x: "/usr/bin/claude" if x == "claude" else None):
                with patch.object(router, "_is_wsl_runtime", return_value=False):
                    with patch.object(
                        router,
                        "_run_cli_command",
                        new=AsyncMock(return_value=(1, "", "oauth token has expired"))
                    ):
                        with patch.object(router, "_adaptive_timeout", return_value=5):
                            result = await router._route_to_claude_cli(task)

        assert result["status"] == "failed"
        assert result["system"] == "claude_cli"
        # Should contain auth-related info
        assert any(
            marker in result.get("error", "").lower()
            for marker in ("auth", "oauth", "expired", "login")
        )


# ---------------------------------------------------------------------------
# _route_to_consciousness (lines 2795-2842)
# ---------------------------------------------------------------------------

class TestRouteToConsciousness:
    @pytest.mark.asyncio
    async def test_import_error_returns_heuristic_fallback(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(content="analyze consciousness", context={"key": "value"})

        import sys
        sys.modules["src.integration.consciousness_bridge"] = None  # type: ignore[assignment]
        try:
            result = await router._route_to_consciousness(task)
        finally:
            sys.modules.pop("src.integration.consciousness_bridge", None)

        assert result["status"] == "success"
        assert result["system"] == "consciousness"
        assert result["mode"] == "heuristic_fallback"
        assert result["task_id"] == task.task_id

    @pytest.mark.asyncio
    async def test_bridge_success_returns_hint(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(content="analyze consciousness", context={"key": "value"})

        mock_bridge = MagicMock()
        mock_bridge.initialize = MagicMock()
        mock_bridge.enhance_contextual_memory = MagicMock()
        mock_bridge.retrieve_contextual_memory = MagicMock(return_value="Some insight")
        mock_bridge.contextual_memory = {"ctx": "data"}
        mock_bridge.get_initialization_time = MagicMock(return_value="2026-01-01")

        import sys
        fake_mod = MagicMock()
        fake_mod.ConsciousnessBridge = MagicMock(return_value=mock_bridge)
        sys.modules["src.integration.consciousness_bridge"] = fake_mod
        try:
            result = await router._route_to_consciousness(task)
        finally:
            sys.modules.pop("src.integration.consciousness_bridge", None)

        assert result["status"] == "success"
        assert result["system"] == "consciousness"
        assert "hint" in result
        assert result["hint"]["confidence"] == 0.7

    @pytest.mark.asyncio
    async def test_bridge_runtime_error_returns_heuristic_fallback(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(content="analyze consciousness", context={})

        import sys
        fake_mod = MagicMock()
        fake_mod.ConsciousnessBridge = MagicMock(side_effect=RuntimeError("bridge failed"))
        sys.modules["src.integration.consciousness_bridge"] = fake_mod
        try:
            result = await router._route_to_consciousness(task)
        finally:
            sys.modules.pop("src.integration.consciousness_bridge", None)

        assert result["status"] == "success"
        assert result["mode"] == "heuristic_fallback"


# ---------------------------------------------------------------------------
# _route_to_quantum_resolver (lines 2950-3012)
# ---------------------------------------------------------------------------

class TestRouteToQuantumResolver:
    @pytest.mark.asyncio
    async def test_success_with_explicit_problem_type(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(
            task_type="analyze",
            content="optimize something",
            context={"quantum_problem_type": "optimization"},
        )

        mock_resolver = MagicMock()
        mock_resolver.resolve_problem = MagicMock(return_value={"status": "resolved", "fixes": []})

        import sys
        fake_mod = MagicMock()
        fake_mod.QuantumProblemResolver = MagicMock(return_value=mock_resolver)
        sys.modules["src.healing.quantum_problem_resolver"] = fake_mod
        try:
            result = await router._route_to_quantum_resolver(task)
        finally:
            sys.modules.pop("src.healing.quantum_problem_resolver", None)

        assert result["status"] == "success"
        assert result["system"] == "quantum_resolver"
        assert result["problem_type"] == "optimization"

    @pytest.mark.asyncio
    async def test_task_type_maps_to_problem_type(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(task_type="debug", content="fix bug", context={})

        mock_resolver = MagicMock()
        mock_resolver.resolve_problem = MagicMock(return_value={"status": "resolved"})

        import sys
        fake_mod = MagicMock()
        fake_mod.QuantumProblemResolver = MagicMock(return_value=mock_resolver)
        sys.modules["src.healing.quantum_problem_resolver"] = fake_mod
        try:
            result = await router._route_to_quantum_resolver(task)
        finally:
            sys.modules.pop("src.healing.quantum_problem_resolver", None)

        # "debug" maps to "optimization"
        assert result["problem_type"] == "optimization"

    @pytest.mark.asyncio
    async def test_unknown_task_type_defaults_to_simulation(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(task_type="review_pr", content="review pull request", context={})

        mock_resolver = MagicMock()
        mock_resolver.resolve_problem = MagicMock(return_value={"status": "resolved"})

        import sys
        fake_mod = MagicMock()
        fake_mod.QuantumProblemResolver = MagicMock(return_value=mock_resolver)
        sys.modules["src.healing.quantum_problem_resolver"] = fake_mod
        try:
            result = await router._route_to_quantum_resolver(task)
        finally:
            sys.modules.pop("src.healing.quantum_problem_resolver", None)

        assert result["problem_type"] == "simulation"

    @pytest.mark.asyncio
    async def test_resolver_returns_failed_status(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(task_type="analyze", content="analyze", context={})

        mock_resolver = MagicMock()
        mock_resolver.resolve_problem = MagicMock(
            return_value={"status": "error", "error_message": "quantum state collapsed"}
        )

        import sys
        fake_mod = MagicMock()
        fake_mod.QuantumProblemResolver = MagicMock(return_value=mock_resolver)
        sys.modules["src.healing.quantum_problem_resolver"] = fake_mod
        try:
            result = await router._route_to_quantum_resolver(task)
        finally:
            sys.modules.pop("src.healing.quantum_problem_resolver", None)

        assert result["status"] == "failed"
        assert result["system"] == "quantum_resolver"
        assert "quantum state collapsed" in result["error"]

    @pytest.mark.asyncio
    async def test_import_error_propagates(self, tmp_path: Path) -> None:
        """ImportError from quantum_problem_resolver is NOT caught (only RuntimeError/ValueError are).

        Setting sys.modules[...] = None triggers ModuleNotFoundError (subclass of ImportError),
        which propagates out of _route_to_quantum_resolver uncaught by design.
        """
        router = _make_router(tmp_path)
        task = _make_task(task_type="analyze", content="analyze", context={})

        import sys
        sys.modules["src.healing.quantum_problem_resolver"] = None  # type: ignore[assignment]
        try:
            with pytest.raises((ImportError, ModuleNotFoundError)):
                await router._route_to_quantum_resolver(task)
        finally:
            sys.modules.pop("src.healing.quantum_problem_resolver", None)

    @pytest.mark.asyncio
    async def test_runtime_error_returns_failed(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(task_type="analyze", content="analyze", context={})

        import sys
        fake_mod = MagicMock()
        fake_mod.QuantumProblemResolver = MagicMock(side_effect=RuntimeError("resolver crash"))
        sys.modules["src.healing.quantum_problem_resolver"] = fake_mod
        try:
            result = await router._route_to_quantum_resolver(task)
        finally:
            sys.modules.pop("src.healing.quantum_problem_resolver", None)

        assert result["status"] == "failed"
        assert "resolver crash" in result["error"]

    @pytest.mark.asyncio
    async def test_quantum_problem_type_in_context_takes_priority(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        # task_type = "analyze" would map to "simulation", but context overrides to "search"
        task = _make_task(
            task_type="analyze",
            content="search for patterns",
            context={"quantum_problem_type": "search"},
        )

        mock_resolver = MagicMock()
        mock_resolver.resolve_problem = MagicMock(return_value={"status": "resolved"})

        import sys
        fake_mod = MagicMock()
        fake_mod.QuantumProblemResolver = MagicMock(return_value=mock_resolver)
        sys.modules["src.healing.quantum_problem_resolver"] = fake_mod
        try:
            result = await router._route_to_quantum_resolver(task)
        finally:
            sys.modules.pop("src.healing.quantum_problem_resolver", None)

        assert result["problem_type"] == "search"

    @pytest.mark.asyncio
    async def test_resolver_failure_status_returns_failed(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(task_type="analyze", content="analyze", context={})

        mock_resolver = MagicMock()
        mock_resolver.resolve_problem = MagicMock(
            return_value={"status": "failure", "message": "out of qubits"}
        )

        import sys
        fake_mod = MagicMock()
        fake_mod.QuantumProblemResolver = MagicMock(return_value=mock_resolver)
        sys.modules["src.healing.quantum_problem_resolver"] = fake_mod
        try:
            result = await router._route_to_quantum_resolver(task)
        finally:
            sys.modules.pop("src.healing.quantum_problem_resolver", None)

        assert result["status"] == "failed"
        assert "out of qubits" in result["error"]


# ---------------------------------------------------------------------------
# _route_to_ollama (lines 2232-2245) — integration path via adapter
# ---------------------------------------------------------------------------

class TestRouteToOllama:
    @pytest.mark.asyncio
    async def test_ollama_adapter_success(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(task_type="analyze", content="analyze code", context={"ollama_model": "llama3"})

        # Mock the integrator to return None (skip integrator path)
        router._try_ollama_integrator = AsyncMock(return_value=None)
        # Mock the adapter call
        router._query_ollama_adapter = MagicMock(return_value=("success", {"output": "analysis result"}, None))

        result = await router._route_to_ollama(task)

        assert result["status"] == "success"
        assert result["system"] == "ollama"
        assert result["model"] == "llama3"

    @pytest.mark.asyncio
    async def test_ollama_adapter_failure_with_lmstudio_fallback(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(task_type="analyze", content="analyze code", context={"ollama_model": "llama3"})

        router._try_ollama_integrator = AsyncMock(return_value=None)
        router._query_ollama_adapter = MagicMock(
            return_value=("failed", {"error": "connection refused"}, "connection refused")
        )
        lmstudio_result = {
            "status": "success",
            "system": "lmstudio",
            "task_id": task.task_id,
            "output": "fallback output",
        }
        router._maybe_lmstudio_fallback = AsyncMock(return_value=lmstudio_result)

        result = await router._route_to_ollama(task)

        assert result["status"] == "success"
        assert result["system"] == "lmstudio"

    @pytest.mark.asyncio
    async def test_ollama_integrator_result_returned_directly(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(task_type="generate", content="generate code", context={})

        integrator_result = {
            "status": "success",
            "system": "ollama",
            "task_id": task.task_id,
            "output": "generated by integrator",
        }
        router._try_ollama_integrator = AsyncMock(return_value=integrator_result)

        result = await router._route_to_ollama(task)

        assert result is integrator_result

    @pytest.mark.asyncio
    async def test_ollama_adapter_exception_triggers_lmstudio_fallback(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(task_type="analyze", content="analyze code", context={"ollama_model": "llama3"})

        router._try_ollama_integrator = AsyncMock(return_value=None)
        router._query_ollama_adapter = MagicMock(side_effect=ConnectionError("ollama down"))
        router._maybe_lmstudio_fallback = AsyncMock(return_value=None)

        result = await router._route_to_ollama(task)

        # No fallback available — should return failed result from format_ollama_result
        assert result["status"] == "failed"
        assert result["system"] == "ollama"


# ---------------------------------------------------------------------------
# _route_to_lmstudio — httpx import failure
# ---------------------------------------------------------------------------

class TestRouteToLmStudio:
    @pytest.mark.asyncio
    async def test_httpx_import_error_returns_failed(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(task_type="analyze", content="analyze code", context={})

        import sys
        sys.modules["httpx"] = None  # type: ignore[assignment]
        try:
            result = await router._route_to_lmstudio(task)
        finally:
            sys.modules.pop("httpx", None)

        assert result["status"] == "failed"
        assert result["system"] == "lmstudio"
        assert "httpx" in result["error"]

    @pytest.mark.asyncio
    async def test_model_not_resolved_returns_failed(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        task = _make_task(task_type="analyze", content="analyze code", context={})

        import httpx

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("LMSTUDIO_DEFAULT_MODEL", None)
            os.environ.pop("LMSTUDIO_BASE_URL", None)
            with patch.object(router, "_resolve_lmstudio_model", new=AsyncMock(return_value=None)):
                with patch("httpx.AsyncClient", return_value=mock_client):
                    result = await router._route_to_lmstudio(task)

        assert result["status"] == "failed"
        assert result["system"] == "lmstudio"
        assert "model not configured" in result["error"].lower()


# ---------------------------------------------------------------------------
# _build_workspace_awareness — output artifacts included in result
# ---------------------------------------------------------------------------

class TestBuildWorkspaceAwarenessArtifacts:
    def test_terminal_log_paths_appear_in_artifacts(self, tmp_path: Path) -> None:
        router = _make_router(tmp_path)
        awareness_dir = tmp_path / "state" / "reports"
        awareness_dir.mkdir(parents=True)

        awareness_file = awareness_dir / "terminal_awareness_latest.json"
        awareness_file.write_text(
            '{"active_session": "main", '
            '"terminals": [{"display_name": "Ollama", "purpose": "inference", '
            '"agents": ["Ollama"], "log_path": "/tmp/ollama.log", "watcher_path": null}], '
            '"agent_registry": [{"agent": "Ollama", "terminals": ["Ollama"], "purposes": ["inference"]}], '
            '"output_surfaces": []}',
            encoding="utf-8",
        )
        router.terminal_awareness_path = awareness_file
        result = router._build_workspace_awareness("ollama", "run inference", {})

        artifacts = result.get("relevant_output_artifacts", [])
        assert "ollama.log" in artifacts
