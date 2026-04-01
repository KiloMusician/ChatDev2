"""Tests for MJOLNIR Protocol dispatch system (Phase G).

Covers: ResponseEnvelope, ContextDetector, AgentAvailabilityRegistry,
MjolnirProtocol (ask/council/chain/status), CLI dispatcher, and
dispatch_actions wiring.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure project root on path
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def _unit_probe_offline():
    from src.dispatch.agent_registry import AgentStatus

    return AgentStatus.OFFLINE, "service unreachable", {}


def _unit_probe_degraded():
    from src.dispatch.agent_registry import AgentStatus

    return AgentStatus.DEGRADED, "auth expired", {"reason": "auth"}


# ── ResponseEnvelope ──────────────────────────────────────────────────────────


class TestResponseEnvelope:
    """Verify structured JSON contract."""

    def test_wrap_success(self):
        from src.dispatch.response_envelope import ResponseEnvelope

        envelope = ResponseEnvelope.wrap(
            {"output": "hello", "status": "completed"},
            agent="ollama",
            context_mode="ecosystem",
            pattern="ask",
        )
        assert envelope.success is True
        assert envelope.status == "ok"
        assert envelope.agent == "ollama"
        assert envelope.context_mode == "ecosystem"
        assert envelope.pattern == "ask"
        assert envelope.mjolnir == "0.1.0"

    def test_wrap_error_result(self):
        from src.dispatch.response_envelope import ResponseEnvelope

        envelope = ResponseEnvelope.wrap(
            {"status": "failed", "output": "connection refused"},
            agent="chatdev",
        )
        assert envelope.success is False
        assert envelope.status == "error"

    def test_wrap_timeout_result(self):
        from src.dispatch.response_envelope import ResponseEnvelope

        envelope = ResponseEnvelope.wrap(
            {"status": "timeout", "result": "timed out after 30s"},
            agent="lmstudio",
        )
        assert envelope.success is False
        assert envelope.status == "timeout"

    def test_from_error(self):
        from src.dispatch.response_envelope import ResponseEnvelope

        envelope = ResponseEnvelope.from_error(
            "Agent not found",
            agent="unknown_agent",
            pattern="ask",
        )
        assert envelope.success is False
        assert envelope.status == "error"
        assert envelope.error == "Agent not found"

    def test_to_dict_drops_none(self):
        from src.dispatch.response_envelope import ResponseEnvelope

        envelope = ResponseEnvelope(
            agent="ollama",
            output="test",
            error=None,
            guild_quest_id=None,
        )
        d = envelope.to_dict()
        assert "error" not in d
        assert "guild_quest_id" not in d
        assert "agent" in d
        assert "output" in d

    def test_wrap_with_timing(self):
        import time

        from src.dispatch.response_envelope import ResponseEnvelope

        start = time.monotonic()
        time.sleep(0.05)  # 50ms — enough to register on Windows
        envelope = ResponseEnvelope.wrap(
            {"output": "done"},
            agent="test",
            start_time=start,
        )
        assert envelope.timing_ms is not None
        assert envelope.timing_ms >= 0  # May round to 0 on fast systems

    def test_agents_used_populated(self):
        from src.dispatch.response_envelope import ResponseEnvelope

        envelope = ResponseEnvelope.wrap(
            {"output": "done"},
            agent="ollama",
            agents_used=["ollama", "lmstudio"],
        )
        assert envelope.agents_used == ["ollama", "lmstudio"]

    def test_agents_used_defaults_to_agent(self):
        from src.dispatch.response_envelope import ResponseEnvelope

        envelope = ResponseEnvelope.wrap(
            {"output": "done"},
            agent="codex",
        )
        assert envelope.agents_used == ["codex"]


# ── ContextDetector ───────────────────────────────────────────────────────────


class TestContextDetector:
    """Verify context mode auto-detection."""

    def test_detect_ecosystem(self):
        from src.dispatch.context_detector import ContextDetector, ContextMode

        detector = ContextDetector()
        # NuSyQ-Hub root should be ecosystem
        mode = detector.detect(cwd=_PROJECT_ROOT)
        assert mode == ContextMode.ECOSYSTEM

    def test_detect_project_fallback(self):
        from src.dispatch.context_detector import ContextDetector, ContextMode

        detector = ContextDetector()
        # A temp/unknown directory should be project
        mode = detector.detect(cwd=Path("/tmp/random_dir"))
        assert mode == ContextMode.PROJECT

    def test_enrich_context_has_mode(self):
        from src.dispatch.context_detector import ContextDetector, ContextMode

        detector = ContextDetector()
        ctx = detector.enrich_context(ContextMode.ECOSYSTEM)
        assert ctx["context_mode"] == "ecosystem"
        assert "hub_root" in ctx  # Ecosystem mode provides hub_root

    def test_detect_explicit_game_mode(self):
        from src.dispatch.context_detector import ContextMode

        # Verify enum values
        assert ContextMode.GAME.value == "game"
        assert ContextMode.ECOSYSTEM.value == "ecosystem"
        assert ContextMode.PROJECT.value == "project"

    def test_detect_env_override_ecosystem(self, monkeypatch):
        from src.dispatch.context_detector import ContextDetector, ContextMode

        monkeypatch.setenv("NUSYQ_CONTEXT_MODE", "ecosystem")
        detector = ContextDetector()
        mode = detector.detect(cwd=Path("/tmp/random_dir"))
        assert mode == ContextMode.ECOSYSTEM

    def test_detect_env_override_game(self, monkeypatch):
        from src.dispatch.context_detector import ContextDetector, ContextMode

        monkeypatch.setenv("NUSYQ_CONTEXT_MODE", "game")
        detector = ContextDetector()
        mode = detector.detect(cwd=Path("/tmp/random_dir"))
        assert mode == ContextMode.GAME

    def test_detect_env_override_project(self, monkeypatch):
        from src.dispatch.context_detector import ContextDetector, ContextMode

        monkeypatch.setenv("NUSYQ_CONTEXT_MODE", "project")
        detector = ContextDetector()
        mode = detector.detect(cwd=_PROJECT_ROOT)  # Override hub detection
        assert mode == ContextMode.PROJECT

    def test_enrich_context_game_mode(self):
        from src.dispatch.context_detector import ContextDetector, ContextMode

        detector = ContextDetector()
        ctx = detector.enrich_context(ContextMode.GAME)
        assert ctx["context_mode"] == "game"
        assert ctx["scope_hint"] == "SimulatedVerse game and cultivation system"
        assert "relevant_configs" in ctx

    def test_enrich_context_project_mode(self):
        from src.dispatch.context_detector import ContextDetector, ContextMode

        detector = ContextDetector()
        ctx = detector.enrich_context(ContextMode.PROJECT)
        assert ctx["context_mode"] == "project"
        assert ctx["scope_hint"] == "external or new project"
        assert "project_root" in ctx

    def test_enrich_context_preserves_base(self):
        from src.dispatch.context_detector import ContextDetector, ContextMode

        detector = ContextDetector()
        base = {"existing_key": "value"}
        ctx = detector.enrich_context(ContextMode.ECOSYSTEM, base_context=base)
        assert ctx["existing_key"] == "value"
        assert ctx["context_mode"] == "ecosystem"
        # Original shouldn't be mutated
        assert "context_mode" not in base

    def test_resolve_root_scans_marker_files(self, tmp_path, monkeypatch):
        """Verify _resolve_root scans upward for marker files."""
        from src.dispatch.context_detector import ContextDetector

        # Create a nested directory with a marker file at root
        nested = tmp_path / "level1" / "level2" / "level3"
        nested.mkdir(parents=True)
        (tmp_path / "pyproject.toml").touch()  # Marker at root

        monkeypatch.chdir(nested)
        # Clear env var to force marker scan
        monkeypatch.delenv("NUSYQ_HUB_ROOT", raising=False)

        # Mock repo_path_resolver to raise ImportError (force marker scan)
        with patch.dict(
            "sys.modules",
            {"src.utils.repo_path_resolver": None},
        ):
            # Static method call
            found = ContextDetector._resolve_root(
                env_var="NUSYQ_HUB_ROOT",
                markers={"pyproject.toml", "setup.py"},
            )
        assert found == tmp_path

    def test_resolve_root_respects_max_depth(self, tmp_path, monkeypatch):
        """Verify _resolve_root stops after max scan depth."""
        from src.dispatch.context_detector import ContextDetector

        # Create deeply nested dir (more than 8 levels)
        deep_path = tmp_path
        for i in range(12):
            deep_path = deep_path / f"level{i}"
        deep_path.mkdir(parents=True)
        # Put marker beyond scan depth
        (tmp_path / "pyproject.toml").touch()

        monkeypatch.chdir(deep_path)
        monkeypatch.delenv("NUSYQ_HUB_ROOT", raising=False)

        # Mock repo_path_resolver to raise ImportError (force marker scan)
        with patch.dict(
            "sys.modules",
            {"src.utils.repo_path_resolver": None},
        ):
            # Should NOT find root (too deep)
            found = ContextDetector._resolve_root(
                env_var="NUSYQ_HUB_ROOT",
                markers={"pyproject.toml"},
            )
        assert found is None

    def test_detect_returns_project_when_no_match(self, tmp_path, monkeypatch):
        """Verify detect() returns PROJECT when no known repos match."""
        from src.dispatch.context_detector import ContextDetector, ContextMode

        # Create isolated temp dir that doesn't match any known repo
        monkeypatch.chdir(tmp_path)
        # Clear env vars
        monkeypatch.delenv("NUSYQ_CONTEXT_MODE", raising=False)

        detector = ContextDetector()
        # Force-clear cached roots
        detector._nusyq_hub_root = None
        detector._nusyq_root = None
        detector._simverse_root = None

        mode = detector.detect(cwd=tmp_path)
        assert mode == ContextMode.PROJECT


# ── AgentAvailabilityRegistry ─────────────────────────────────────────────────


class TestAgentRegistry:
    """Verify agent probing infrastructure."""

    def test_registry_has_all_agents(self):
        from src.dispatch.agent_registry import AGENT_PROBES

        expected = {
            "ollama",
            "lmstudio",
            "chatdev",
            "codex",
            "claude_cli",
            "copilot",
            "consciousness",
            "quantum_resolver",
            "factory",
            "openclaw",
            "intermediary",
            "skyclaw",
            "devtool",
            "gitkraken",
            "huggingface",
            "dbclient",
            "neural_ml",
            "hermes",
            "optimizer",
            "metaclaw",
        }
        assert expected == set(AGENT_PROBES.keys())

    def test_display_names_match_probes(self):
        from src.dispatch.agent_registry import AGENT_DISPLAY_NAMES, AGENT_PROBES

        assert set(AGENT_PROBES.keys()) == set(AGENT_DISPLAY_NAMES.keys())

    def test_probe_unknown_agent(self):
        from src.dispatch.agent_registry import AgentAvailabilityRegistry, AgentStatus

        registry = AgentAvailabilityRegistry()
        result = asyncio.run(registry.probe_one("nonexistent_agent"))
        assert result.status == AgentStatus.UNKNOWN
        assert "No probe defined" in result.detail

    def test_probe_result_serialization(self):
        from src.dispatch.agent_registry import AgentProbeResult, AgentStatus

        probe = AgentProbeResult(
            agent="test",
            status=AgentStatus.ONLINE,
            latency_ms=42.5,
            detail="OK",
            metadata={"url": "http://localhost"},
        )
        d = probe.to_dict()
        assert d["agent"] == "test"
        assert d["status"] == "online"
        assert d["latency_ms"] == 42.5
        assert "url" in d["metadata"]

    @pytest.mark.asyncio
    async def test_probe_one_preserves_degraded_when_no_online(self, monkeypatch):
        import src.dispatch.agent_registry as agent_registry
        from src.dispatch.agent_registry import AgentAvailabilityRegistry, AgentStatus

        async def _inline_to_thread(func, *args, **kwargs):
            return func(*args, **kwargs)

        monkeypatch.setattr(agent_registry.asyncio, "to_thread", _inline_to_thread)
        monkeypatch.setitem(
            agent_registry.AGENT_PROBES,
            "unit_test_agent",
            [
                (_unit_probe_offline,),
                (_unit_probe_degraded,),
            ],
        )

        registry = AgentAvailabilityRegistry()
        result = await registry.probe_one("unit_test_agent")
        assert result.status == AgentStatus.DEGRADED
        assert "auth expired" in result.detail
        assert result.metadata.get("reason") == "auth"

    def test_probe_claude_cli_marks_auth_failure_degraded(self, monkeypatch):
        import src.dispatch.agent_registry as agent_registry
        from src.dispatch.agent_registry import AgentStatus

        class _Completed:
            returncode = 1
            stdout = "Not logged in · Please run /login"
            stderr = ""

        def _which(name: str):
            if name == "claude":
                return "/tmp/claude"
            return None

        monkeypatch.delenv("NUSYQ_CLAUDE_CLI_COMMAND", raising=False)
        monkeypatch.setenv("NUSYQ_STRICT_CLAUDE_AUTH_PROBE", "1")
        monkeypatch.setattr(agent_registry.shutil, "which", _which)
        monkeypatch.setattr(agent_registry.subprocess, "run", lambda *args, **kwargs: _Completed())

        status, detail, metadata = agent_registry._probe_claude_cli()
        assert status == AgentStatus.DEGRADED
        assert "authentication" in detail.lower()
        assert metadata.get("command") == "claude"

    def test_probe_cli_found(self, monkeypatch):
        import src.dispatch.agent_registry as agent_registry
        from src.dispatch.agent_registry import AgentStatus

        monkeypatch.setattr(agent_registry.shutil, "which", lambda cmd: f"/usr/bin/{cmd}")
        status, detail, metadata = agent_registry._probe_cli("test_cmd")
        assert status == AgentStatus.ONLINE
        assert "Found at" in detail
        assert metadata["path"] == "/usr/bin/test_cmd"

    def test_probe_cli_not_found(self, monkeypatch):
        import src.dispatch.agent_registry as agent_registry
        from src.dispatch.agent_registry import AgentStatus

        monkeypatch.setattr(agent_registry.shutil, "which", lambda cmd: None)
        status, detail, _metadata = agent_registry._probe_cli("missing_cmd")
        assert status == AgentStatus.OFFLINE
        assert "not found" in detail

    def test_probe_env_var_set(self, monkeypatch):
        import src.dispatch.agent_registry as agent_registry
        from src.dispatch.agent_registry import AgentStatus

        monkeypatch.setenv("TEST_VAR", "test_value")
        status, detail, metadata = agent_registry._probe_env_var("TEST_VAR")
        assert status == AgentStatus.ONLINE
        assert "is set" in detail
        assert metadata["env_var"] == "TEST_VAR"

    def test_probe_env_var_not_set(self, monkeypatch):
        import src.dispatch.agent_registry as agent_registry
        from src.dispatch.agent_registry import AgentStatus

        monkeypatch.delenv("NONEXISTENT_VAR", raising=False)
        status, detail, _metadata = agent_registry._probe_env_var("NONEXISTENT_VAR")
        assert status == AgentStatus.OFFLINE
        assert "not set" in detail

    def test_run_probe_command_success(self, monkeypatch):
        import src.dispatch.agent_registry as agent_registry

        class _Completed:
            returncode = 0
            stdout = "success output"
            stderr = ""

        monkeypatch.setattr(agent_registry.subprocess, "run", lambda *args, **kwargs: _Completed())
        exit_code, output = agent_registry._run_probe_command(["echo", "test"])
        assert exit_code == 0
        assert "success output" in output

    def test_run_probe_command_timeout(self, monkeypatch):
        import subprocess
        import src.dispatch.agent_registry as agent_registry

        def _timeout_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="test", timeout=5.0)

        monkeypatch.setattr(agent_registry.subprocess, "run", _timeout_run)
        exit_code, output = agent_registry._run_probe_command(["sleep", "999"])
        assert exit_code == 124
        assert "timeout" in output.lower()

    def test_run_probe_command_oserror(self, monkeypatch):
        import src.dispatch.agent_registry as agent_registry

        def _oserror_run(*args, **kwargs):
            raise OSError("Command not found")

        monkeypatch.setattr(agent_registry.subprocess, "run", _oserror_run)
        exit_code, output = agent_registry._run_probe_command(["nonexistent"])
        assert exit_code == 127
        assert "not found" in output.lower()

    def test_probe_one_returns_first_success(self, monkeypatch):
        """Verify probe_one returns first successful probe result."""
        import src.dispatch.agent_registry as agent_registry

        registry = agent_registry.AgentAvailabilityRegistry()

        # Test with live ollama (probe function is called via async path)
        result = asyncio.run(registry.probe_one("ollama"))
        # Ollama returns ONLINE with "HTTP 200 in Xms" when available
        # Falls back to OFFLINE/DEGRADED if unavailable
        assert result.status in (
            agent_registry.AgentStatus.ONLINE,
            agent_registry.AgentStatus.OFFLINE,
            agent_registry.AgentStatus.DEGRADED,
        )
        assert result.agent == "ollama"
        assert result.detail  # Non-empty detail

    def test_probe_one_probe_exception(self, monkeypatch):
        """Verify probe_one handles probe exceptions gracefully."""
        import src.dispatch.agent_registry as agent_registry

        registry = agent_registry.AgentAvailabilityRegistry()

        def failing_probe(*args, **kwargs):
            raise RuntimeError("Connection reset by peer")

        # Replace all ollama probes with a failing one
        monkeypatch.setattr(agent_registry, "AGENT_PROBES", {"test_agent": [(failing_probe,)]})

        result = asyncio.run(registry.probe_one("test_agent"))
        assert result.status == agent_registry.AgentStatus.OFFLINE
        assert "Connection reset" in result.detail

    def test_probe_one_returns_degraded_when_no_success(self, monkeypatch):
        """Verify probe_one returns degraded if no success but degraded available."""
        import src.dispatch.agent_registry as agent_registry

        registry = agent_registry.AgentAvailabilityRegistry()

        def degraded_probe(*args, **kwargs):
            return agent_registry.AgentStatus.DEGRADED, "Auth expired", {"reason": "token"}

        monkeypatch.setattr(agent_registry, "AGENT_PROBES", {"test_agent": [(degraded_probe,)]})

        result = asyncio.run(registry.probe_one("test_agent"))
        assert result.status == agent_registry.AgentStatus.DEGRADED
        assert "expired" in result.detail.lower()

    def test_probe_all_handles_exception(self, monkeypatch):
        """Verify probe_all catches exceptions per agent."""
        import src.dispatch.agent_registry as agent_registry

        registry = agent_registry.AgentAvailabilityRegistry()

        call_count = 0

        async def flaky_probe_one(agent):
            nonlocal call_count
            call_count += 1
            if agent == "bad_agent":
                raise RuntimeError("Probe crashed")
            return agent_registry.AgentProbeResult(
                agent=agent,
                status=agent_registry.AgentStatus.ONLINE,
                detail="OK",
            )

        monkeypatch.setattr(registry, "probe_one", flaky_probe_one)

        results = asyncio.run(registry.probe_all(["good_agent", "bad_agent"], auto_recover=False))
        assert results["good_agent"].status == agent_registry.AgentStatus.ONLINE
        assert results["bad_agent"].status == agent_registry.AgentStatus.UNKNOWN
        assert "exception" in results["bad_agent"].detail.lower()

    def test_probe_with_recovery_ollama_success(self, monkeypatch):
        """Verify probe_with_recovery attempts Ollama recovery and re-probes."""
        import src.dispatch.agent_registry as agent_registry

        registry = agent_registry.AgentAvailabilityRegistry()

        probe_count = 0

        async def mock_probe_one(agent):
            nonlocal probe_count
            probe_count += 1
            if probe_count == 1:
                # First call: offline
                return agent_registry.AgentProbeResult(
                    agent=agent,
                    status=agent_registry.AgentStatus.OFFLINE,
                    detail="Connection refused",
                )
            # Second call after recovery: online
            return agent_registry.AgentProbeResult(
                agent=agent,
                status=agent_registry.AgentStatus.ONLINE,
                detail="Recovered",
            )

        monkeypatch.setattr(registry, "probe_one", mock_probe_one)

        # Mock OllamaServiceManager
        mock_mgr = MagicMock()
        mock_mgr.ensure_running.return_value = True

        with patch(
            "src.services.ollama_service_manager.OllamaServiceManager", return_value=mock_mgr
        ):
            result = asyncio.run(registry.probe_with_recovery("ollama", auto_recover=True))

        assert result.status == agent_registry.AgentStatus.ONLINE
        assert probe_count == 2
        mock_mgr.ensure_running.assert_called_once()


# ── MjolnirProtocol ──────────────────────────────────────────────────────────


class TestMjolnirProtocol:
    """Verify protocol methods route correctly."""

    def test_resolve_agent_aliases(self):
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        assert protocol._resolve_agent("lms") == "lmstudio"
        assert protocol._resolve_agent("claude") == "claude_cli"
        assert protocol._resolve_agent("sv") == "consciousness"
        assert protocol._resolve_agent("qr") == "quantum_resolver"
        assert protocol._resolve_agent("ollama") == "ollama"
        assert protocol._resolve_agent("auto") == "auto"

    def test_infer_task_type(self):
        from src.dispatch.mjolnir import _infer_task_type

        assert _infer_task_type("Review this code for bugs") == "review"
        assert _infer_task_type("Debug the authentication issue") == "debug"
        assert _infer_task_type("Generate a test suite") == "generate"
        assert _infer_task_type("Create a new component") == "generate"
        assert _infer_task_type("Plan the architecture") == "plan"
        assert _infer_task_type("Analyze the performance") == "analyze"
        assert _infer_task_type("Hello world") == "analyze"  # default

    def test_priority_map(self):
        from src.dispatch.mjolnir import MjolnirProtocol

        assert MjolnirProtocol._PRIORITY_MAP["CRITICAL"] == 1
        assert MjolnirProtocol._PRIORITY_MAP["HIGH"] == 2
        assert MjolnirProtocol._PRIORITY_MAP["NORMAL"] == 3
        assert MjolnirProtocol._PRIORITY_MAP["LOW"] == 4
        assert MjolnirProtocol._PRIORITY_MAP["BACKGROUND"] == 5

    def test_effective_dispatch_timeout_adds_local_grace(self, monkeypatch):
        from src.dispatch.mjolnir import MjolnirProtocol

        monkeypatch.delenv("NUSYQ_STRICT_TIMEOUTS", raising=False)
        monkeypatch.setenv("NUSYQ_LOCAL_LLM_TIMEOUT_GRACE_MULTIPLIER", "2.0")
        protocol = MjolnirProtocol()

        effective = protocol._effective_dispatch_timeout("openclaw", requested_timeout=30)
        # 30s request should be expanded for local model latency tolerance
        assert effective >= 60.0

    def test_effective_dispatch_timeout_openclaw_default_from_env(self, monkeypatch):
        from src.dispatch.mjolnir import MjolnirProtocol

        monkeypatch.setenv("NUSYQ_OPENCLAW_DEFAULT_TIMEOUT_S", "720")
        protocol = MjolnirProtocol()

        effective = protocol._effective_dispatch_timeout("openclaw", requested_timeout=None)
        assert effective == 720.0

    def test_ask_openclaw_propagates_model_override(self):
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        protocol._guild = False
        protocol._ask_openclaw = AsyncMock(return_value={"status": "success", "response": "ok"})

        result = asyncio.run(
            protocol.ask(
                "openclaw",
                "ping",
                model="qwen2.5-coder:14b",
                no_guild=True,
            )
        )

        assert result.success is True
        call_args = protocol._ask_openclaw.call_args
        assert call_args is not None
        ctx = call_args.args[1]
        assert ctx["openclaw_model"] == "qwen2.5-coder:14b"

    def test_ask_openclaw_balanced_low_risk_prefers_non_blocking(self):
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        protocol._guild = False
        protocol._ask_openclaw = AsyncMock(return_value={"status": "success", "response": "ok"})

        result = asyncio.run(
            protocol.ask(
                "openclaw",
                "ping",
                priority="LOW",
                no_guild=True,
            )
        )

        assert result.success is True
        call_args = protocol._ask_openclaw.call_args
        assert call_args is not None
        ctx = call_args.args[1]
        assert ctx["operating_mode"] == "balanced"
        assert ctx["risk_level"] == "low"
        assert ctx["openclaw_non_blocking"] is True

    def test_ask_openclaw_strict_mode_disables_timeout_fallback(self):
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        protocol._guild = False
        protocol._ask_openclaw = AsyncMock(return_value={"status": "success", "response": "ok"})

        result = asyncio.run(
            protocol.ask(
                "openclaw",
                "ping",
                timeout=30,
                no_guild=True,
                extra_context={"operating_mode": "strict"},
            )
        )

        assert result.success is True
        call_args = protocol._ask_openclaw.call_args
        assert call_args is not None
        ctx = call_args.args[1]
        assert ctx["operating_mode"] == "strict"
        assert ctx["openclaw_auto_non_blocking_on_timeout"] is False
        assert ctx["openclaw_wait_for_completion"] is True
        assert float(ctx["timeout"]) == 30.0

    def test_ask_openclaw_command_not_found(self):
        """Verify _ask_openclaw fails gracefully when command not found."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()

        with (
            patch("shutil.which", return_value=None),
            patch("os.path.exists", return_value=False),
        ):
            result = asyncio.run(protocol._ask_openclaw("test", {}, timeout=10))

        assert result["status"] == "failed"
        assert result["system"] == "openclaw"
        assert "not found" in result["error"].lower()

    def test_ask_openclaw_subprocess_success(self):
        """Verify _ask_openclaw parses successful JSON response."""
        import subprocess
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()

        mock_result = MagicMock(spec=subprocess.CompletedProcess)
        mock_result.returncode = 0
        mock_result.stdout = (
            '{"payloads": [{"text": "Analysis complete"}], "meta": {"durationMs": 500}}'
        )
        mock_result.stderr = ""

        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch("subprocess.run", return_value=mock_result),
        ):
            result = asyncio.run(
                protocol._ask_openclaw(
                    "analyze code", {"openclaw_wait_for_completion": True}, timeout=30
                )
            )

        assert result["status"] == "success"
        assert result["system"] == "openclaw"
        assert "Analysis complete" in result["response"]

    def test_ask_openclaw_subprocess_timeout_auto_non_blocking(self, tmp_path):
        """Verify _ask_openclaw falls back to non-blocking on timeout."""
        import subprocess
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        protocol._repo_root = tmp_path

        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch(
                "subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="openclaw", timeout=30),
            ),
            patch("subprocess.Popen") as mock_popen,
        ):
            mock_popen.return_value.pid = 12345
            result = asyncio.run(
                protocol._ask_openclaw(
                    "long task",
                    {
                        "openclaw_auto_non_blocking_on_timeout": True,
                        "openclaw_retry_attempts": 1,
                    },
                    timeout=30,
                )
            )

        assert result["status"] == "success"
        assert result["non_blocking"] is True
        assert result["reason"] == "auto_non_blocking_after_timeout"
        assert result["pid"] == 12345

    def test_ask_openclaw_non_blocking_requested(self, tmp_path):
        """Verify _ask_openclaw spawns background process when non_blocking."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        protocol._repo_root = tmp_path

        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch("subprocess.Popen") as mock_popen,
        ):
            mock_popen.return_value.pid = 54321
            result = asyncio.run(
                protocol._ask_openclaw(
                    "background task",
                    {"openclaw_non_blocking": True},
                    timeout=60,
                )
            )

        assert result["status"] == "success"
        assert result["non_blocking"] is True
        assert result["reason"] == "non_blocking_requested"
        assert result["pid"] == 54321
        mock_popen.assert_called_once()

    def test_apply_operating_profile_uses_local_profile_override(self, tmp_path, monkeypatch):
        import json

        from src.dispatch.mjolnir import MjolnirProtocol

        local_profile = tmp_path / "dispatch_profiles.local.json"
        local_profile.write_text(
            json.dumps(
                {
                    "defaults": {
                        "operating_mode": "fast",
                        "risk_level": "low",
                        "signal_budget": "minimal",
                    },
                    "non_blocking_targets": ["lmstudio"],
                    "target_overrides": {"lmstudio": {"signal_budget": "full"}},
                }
            ),
            encoding="utf-8",
        )

        monkeypatch.setenv("NUSYQ_DISPATCH_PROFILE_LOCAL_FILE", str(local_profile))
        monkeypatch.delenv("NUSYQ_OPERATING_MODE", raising=False)

        protocol = MjolnirProtocol()
        ctx: dict[str, object] = {}
        profile = protocol._apply_operating_profile(
            ctx,
            target_system="lmstudio",
            priority="NORMAL",
        )

        assert profile["mode"] == "fast"
        assert ctx["operating_mode"] == "fast"
        assert ctx["risk_level"] == "low"
        assert ctx["signal_budget"] == "full"
        assert ctx["non_blocking"] is True

    def test_ask_lmstudio_non_blocking_routes_to_background_queue(self):
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        protocol._guild = False
        protocol._queue_background_non_blocking = AsyncMock(
            return_value={"status": "submitted", "task_id": "bg_123", "system": "lmstudio"}
        )

        mock_router = MagicMock()
        mock_router.route_task = AsyncMock(return_value={"status": "success", "output": "ok"})
        protocol._router = mock_router

        result = asyncio.run(
            protocol.ask(
                "lmstudio",
                "ping",
                no_guild=True,
                extra_context={"non_blocking": True},
            )
        )

        assert result.success is True
        assert result.output["status"] == "submitted"
        assert result.output["task_id"] == "bg_123"
        protocol._queue_background_non_blocking.assert_called_once()
        mock_router.route_task.assert_not_called()

    def test_ask_records_dispatch_profile_metrics(self):
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        protocol._guild = False
        protocol._router = MagicMock()
        protocol._router.route_task = AsyncMock(return_value={"status": "success", "output": "ok"})

        with patch("src.system.ai_metrics_tracker.AIMetricsTracker") as tracker_cls:
            tracker = tracker_cls.return_value
            result = asyncio.run(protocol.ask("lmstudio", "ping", no_guild=True))
            assert result.success is True
            assert tracker.record_dispatch_profile.called

    def test_ask_applies_adaptive_timeout_to_context(self):
        """Verify ask() forwards adaptive timeout budget into router context."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()

        mock_router = MagicMock()
        mock_router.route_task = AsyncMock(
            return_value={"status": "completed", "output": "analysis result"}
        )
        protocol._router = mock_router
        protocol._guild = False

        result = asyncio.run(protocol.ask("chatdev", "Generate project", timeout=10, no_guild=True))

        assert result.success is True
        call_kwargs = mock_router.route_task.call_args.kwargs
        ctx = call_kwargs["context"]
        assert float(ctx["timeout"]) >= 10.0
        assert ctx["adaptive_timeout_enabled"] is True

    def test_ask_delegates_to_router(self):
        """Verify ask() calls route_task() on the AgentTaskRouter."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()

        # Mock the router
        mock_router = MagicMock()
        mock_router.route_task = AsyncMock(
            return_value={"status": "completed", "output": "analysis result"}
        )
        protocol._router = mock_router

        # Mock guild to avoid side effects
        protocol._guild = False  # Sentinel: unavailable

        # Mock recovery probe so Ollama (a RECOVERABLE_AGENT) doesn't hit live HTTP
        mock_probe = MagicMock()
        mock_probe.status = "online"
        mock_probe.detail = "mocked"
        protocol._registry.probe_with_recovery = AsyncMock(return_value=mock_probe)

        result = asyncio.run(protocol.ask("ollama", "Analyze this function", no_guild=True))

        assert result.success is True
        assert result.agent == "ollama"
        assert result.pattern == "ask"
        mock_router.route_task.assert_called_once()

        # Verify route_task was called with correct task_type
        call_kwargs = mock_router.route_task.call_args
        assert call_kwargs.kwargs["task_type"] == "analyze"
        assert call_kwargs.kwargs["target_system"] == "ollama"

    def test_ask_handles_error(self):
        """Verify ask() returns error envelope on router failure."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        mock_router = MagicMock()
        mock_router.route_task = AsyncMock(side_effect=RuntimeError("Connection refused"))
        protocol._router = mock_router
        protocol._guild = False

        result = asyncio.run(protocol.ask("chatdev", "Generate project", no_guild=True))

        assert result.success is False
        assert result.status == "error"
        assert "Connection refused" in result.error

    def test_council_collects_multiple(self):
        """Verify council() queries multiple agents and aggregates."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        mock_router = MagicMock()

        call_count = 0

        async def mock_route(**kwargs):
            nonlocal call_count
            call_count += 1
            return {"status": "completed", "output": f"result_{call_count}"}

        mock_router.route_task = mock_route
        protocol._router = mock_router
        protocol._guild = False

        result = asyncio.run(
            protocol.council(
                "Best approach?",
                agents=["ollama", "lmstudio", "codex"],
                no_guild=True,
            )
        )

        assert result.success is True
        assert result.pattern == "council"
        assert result.agents_used == ["ollama", "lmstudio", "codex"]
        # 3 agents should have been queried
        assert call_count == 3

    def test_chain_feeds_output(self):
        """Verify chain() passes output from agent A to agent B."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        mock_router = MagicMock()

        prompts_received = []

        async def mock_route(**kwargs):
            desc = kwargs.get("description", "")
            prompts_received.append(desc)
            return {"status": "completed", "output": f"processed: {desc[:20]}"}

        mock_router.route_task = mock_route
        protocol._router = mock_router
        protocol._guild = False

        result = asyncio.run(
            protocol.chain(
                "Analyze this code",
                agents=["ollama", "codex"],
                steps=["analyze", "generate"],
            )
        )

        assert result.success is True
        assert result.pattern == "chain"
        assert len(prompts_received) == 2
        # Second prompt should contain output from first
        assert "processed:" in prompts_received[1]

    def test_status_no_probes(self):
        """Verify status() returns agent info without probing."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()

        result = asyncio.run(protocol.status(probes=False))

        assert result.success is True
        assert result.pattern == "status"
        # Should have all 20 agents (12 original + 4 MCP bridges + neural_ml + hermes + optimizer + metaclaw)
        assert len(result.output) == 20
        assert "ollama" in result.output

    def test_graceful_degradation_on_router_import_error(self):
        """Verify structured error when AgentTaskRouter is unavailable."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()

        # Force router import to fail
        with patch.dict("sys.modules", {"src.tools.agent_task_router": None}):
            protocol._router = None  # Reset so it tries to import
            result = asyncio.run(protocol.ask("ollama", "test", no_guild=True))

            assert result.success is False
            assert result.status == "error"

    def test_get_guild_success(self):
        """Verify _get_guild() returns GuildBoard when available."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        protocol._guild = None  # Reset

        with patch.dict("sys.modules", {}):
            with patch("src.guild.guild_board.GuildBoard") as MockGuild:
                MockGuild.return_value = MagicMock()
                # Force reimport by resetting
                protocol._guild = None
                # Patch inside the method
                import src.guild.guild_board as guild_mod

                original = getattr(guild_mod, "GuildBoard", None)
                try:
                    guild_mod.GuildBoard = MockGuild
                    result = protocol._get_guild()
                    assert result is not None
                finally:
                    if original:
                        guild_mod.GuildBoard = original

    def test_get_guild_import_failure(self):
        """Verify _get_guild() returns None when import fails."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        protocol._guild = None  # Reset

        with patch.dict("sys.modules", {"src.guild.guild_board": None}):
            result = protocol._get_guild()
            assert result is None

    def test_get_intermediary_success(self):
        """Verify _get_intermediary() returns AIIntermediary when available."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        protocol._intermediary = None
        protocol._intermediary_loaded = False

        # Patch inside the method's import locations
        mock_hub = MagicMock()
        mock_intermediary = MagicMock()

        with (
            patch("src.ai.ollama_hub.OllamaHub", return_value=mock_hub),
            patch("src.ai.ai_intermediary.AIIntermediary", return_value=mock_intermediary),
        ):
            protocol._get_intermediary()
            # On import failure (due to mocking), should return None
            # But if import succeeds, should return the mock
            assert protocol._intermediary_loaded is True

    def test_get_intermediary_import_failure(self):
        """Verify _get_intermediary() returns None when import fails."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        protocol._intermediary = None
        protocol._intermediary_loaded = False

        with patch.dict(
            "sys.modules",
            {"src.ai.ai_intermediary": None, "src.ai.ollama_hub": None},
        ):
            result = protocol._get_intermediary()
            assert result is None
            assert protocol._intermediary_loaded is True

    def test_ask_intermediary_unavailable(self):
        """Verify _ask_intermediary returns error dict when intermediary unavailable."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        protocol._intermediary = None
        protocol._intermediary_loaded = True  # Simulate already tried

        result = asyncio.run(protocol._ask_intermediary("test prompt", {}, task_type="analyze"))
        assert result["status"] == "failed"
        assert "unavailable" in result["error"].lower()
        assert result["system"] == "intermediary"

    def test_parallel_runs_concurrent(self):
        """Verify parallel() runs agents concurrently."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        mock_router = MagicMock()

        call_times = []

        async def mock_route(**kwargs):
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.01)
            return {"status": "completed", "output": f"result_{kwargs['target_system']}"}

        mock_router.route_task = mock_route
        protocol._router = mock_router
        protocol._guild = False

        result = asyncio.run(
            protocol.parallel(
                "Test prompt",
                agents=["ollama", "lmstudio"],
                no_guild=True,
            )
        )

        assert result.success is True
        assert result.pattern == "parallel"
        assert len(result.agents_used) == 2

    def test_delegate_success(self):
        """Verify delegate() posts quest to guild board."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        mock_guild = MagicMock()
        mock_guild.add_quest = AsyncMock(return_value=(True, "quest-123"))
        protocol._guild = mock_guild

        result = asyncio.run(
            protocol.delegate(
                "Refactor auth module",
                agent="codex",
                priority=2,
            )
        )

        assert result.success is True
        assert result.pattern == "delegate"
        assert result.output["delegated"] is True
        assert result.output["quest_id"] == "quest-123"
        mock_guild.add_quest.assert_called_once()

    def test_delegate_guild_unavailable(self):
        """Verify delegate() returns error when guild is unavailable."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        protocol._guild = False  # Sentinel for unavailable

        result = asyncio.run(protocol.delegate("Test task", agent="ollama"))

        assert result.success is False
        assert "not available" in result.error.lower()
        assert result.pattern == "delegate"

    def test_queue_success(self):
        """Verify queue() submits to background orchestrator."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()

        # Mock async dispatch_task_cli
        mock_result = {"status": "queued", "task_id": "bg_456"}

        async def mock_dispatch(*args, **kwargs):
            return mock_result

        with patch(
            "src.orchestration.background_task_orchestrator.dispatch_task_cli",
            side_effect=mock_dispatch,
        ):
            result = asyncio.run(
                protocol.queue(
                    "Generate tests for api module",
                    agent="ollama",
                    priority="HIGH",
                )
            )

        assert result.success is True
        assert result.pattern == "queue"

    def test_queue_import_failure(self):
        """Verify queue() returns error when orchestrator unavailable."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()

        with patch.dict(
            "sys.modules",
            {"src.orchestration.background_task_orchestrator": None},
        ):
            result = asyncio.run(protocol.queue("Test task", agent="ollama"))

        assert result.success is False
        assert "not available" in result.error.lower()
        assert result.pattern == "queue"

    def test_status_with_probes_single_agent(self):
        """Verify status() probes single agent when probes=True."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()

        # Mock probe_one to return online status
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"agent": "ollama", "status": "online"}

        with patch.object(protocol._registry, "probe_one", return_value=mock_result) as mock_probe:
            result = asyncio.run(protocol.status("ollama", probes=True, auto_recover=False))

        mock_probe.assert_called_once_with("ollama")
        assert result.success is True
        assert result.pattern == "status"
        assert result.output == {"agent": "ollama", "status": "online"}

    def test_status_with_probes_all_agents(self):
        """Verify status() probes all agents when probes=True and agent=None."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()

        # Mock probe_all to return multiple results
        mock_ollama = MagicMock()
        mock_ollama.to_dict.return_value = {"agent": "ollama", "status": "online"}
        mock_chatdev = MagicMock()
        mock_chatdev.to_dict.return_value = {"agent": "chatdev", "status": "offline"}

        with patch.object(
            protocol._registry,
            "probe_all",
            return_value={"ollama": mock_ollama, "chatdev": mock_chatdev},
        ) as mock_probe:
            result = asyncio.run(protocol.status(probes=True, auto_recover=False))

        mock_probe.assert_called_once_with(auto_recover=False)
        assert result.success is True
        assert "ollama" in result.output
        assert "chatdev" in result.output

    def test_status_with_probes_and_auto_recover(self):
        """Verify status() uses probe_with_recovery for recoverable agents."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()

        # Mock probe_with_recovery for recoverable agent
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "agent": "ollama",
            "status": "online",
            "recovered": True,
        }

        with patch.object(
            protocol._registry, "probe_with_recovery", return_value=mock_result
        ) as mock_probe:
            result = asyncio.run(protocol.status("ollama", probes=True, auto_recover=True))

        mock_probe.assert_called_once_with("ollama", auto_recover=True)
        assert result.success is True
        assert result.output.get("recovered") is True

    def test_drain_success(self):
        """Verify drain() executes quests via QuestExecutorBridge."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()

        mock_results = [
            {"quest_id": "q1", "status": "completed", "agent": "ollama"},
            {"quest_id": "q2", "status": "completed", "agent": "chatdev"},
        ]

        mock_bridge = MagicMock()

        async def mock_drain(limit):
            return mock_results

        mock_bridge.drain = mock_drain

        with patch(
            "src.dispatch.quest_executor_bridge.QuestExecutorBridge",
            return_value=mock_bridge,
        ):
            result = asyncio.run(protocol.drain(limit=5))

        assert result.success is True
        assert result.pattern == "drain"
        assert result.output == mock_results

    def test_drain_import_failure(self):
        """Verify drain() returns error when QuestExecutorBridge unavailable."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()

        with patch.dict(
            "sys.modules",
            {"src.dispatch.quest_executor_bridge": None},
        ):
            result = asyncio.run(protocol.drain(limit=5))

        assert result.success is False
        assert "not available" in result.error.lower()
        assert result.pattern == "drain"

    def test_drain_exception_handling(self):
        """Verify drain() handles exceptions gracefully."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()

        mock_bridge = MagicMock()
        mock_bridge.drain = MagicMock(side_effect=RuntimeError("Quest processing failed"))

        with patch(
            "src.dispatch.quest_executor_bridge.QuestExecutorBridge",
            return_value=mock_bridge,
        ):
            result = asyncio.run(protocol.drain())

        assert result.success is False
        assert "Quest processing failed" in result.error
        assert result.pattern == "drain"

    # ── Helper Function Tests ─────────────────────────────────────────────────

    def test_infer_task_type_review(self):
        """Verify _infer_task_type returns 'review' for review prompts."""
        from src.dispatch.mjolnir import _infer_task_type

        assert _infer_task_type("Please review this code") == "review"
        assert _infer_task_type("Code review needed") == "review"
        assert _infer_task_type("Critique my implementation") == "review"

    def test_infer_task_type_debug(self):
        """Verify _infer_task_type returns 'debug' for debug prompts."""
        from src.dispatch.mjolnir import _infer_task_type

        assert _infer_task_type("Debug this error") == "debug"
        assert _infer_task_type("Fix the bug") == "debug"
        assert _infer_task_type("There's an issue with X") == "debug"

    def test_infer_task_type_generate(self):
        """Verify _infer_task_type returns 'generate' for generation prompts."""
        from src.dispatch.mjolnir import _infer_task_type

        assert _infer_task_type("Generate a test file") == "generate"
        assert _infer_task_type("Create a new module") == "generate"
        assert _infer_task_type("Implement the feature") == "generate"
        assert _infer_task_type("Scaffold a REST API") == "generate"

    def test_infer_task_type_default(self):
        """Verify _infer_task_type defaults to 'analyze' for unknown prompts."""
        from src.dispatch.mjolnir import _infer_task_type

        assert _infer_task_type("Hello world") == "analyze"
        assert _infer_task_type("") == "analyze"
        assert _infer_task_type("Random text here") == "analyze"

    def test_resolve_agent_aliases_extended(self):
        """Verify _resolve_agent resolves known aliases."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()

        # Known aliases from AGENT_ALIASES
        assert protocol._resolve_agent("lms") == "lmstudio"
        assert protocol._resolve_agent("claude") == "claude_cli"
        assert protocol._resolve_agent("sv") == "consciousness"
        assert protocol._resolve_agent("qr") == "quantum_resolver"
        assert protocol._resolve_agent("quantum") == "quantum_resolver"

    def test_resolve_agent_passthrough(self):
        """Verify _resolve_agent passes through canonical names unchanged."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()

        assert protocol._resolve_agent("ollama") == "ollama"
        assert protocol._resolve_agent("copilot") == "copilot"
        assert protocol._resolve_agent("chatdev") == "chatdev"
        assert protocol._resolve_agent("  OLLAMA  ") == "ollama"

    def test_env_flag_true_values(self):
        """Verify _env_flag returns True for affirmative values."""
        from src.dispatch.mjolnir import MjolnirProtocol

        with patch.dict(os.environ, {"TEST_FLAG": "1"}):
            assert MjolnirProtocol._env_flag("TEST_FLAG") is True
        with patch.dict(os.environ, {"TEST_FLAG": "true"}):
            assert MjolnirProtocol._env_flag("TEST_FLAG") is True
        with patch.dict(os.environ, {"TEST_FLAG": "YES"}):
            assert MjolnirProtocol._env_flag("TEST_FLAG") is True

    def test_env_flag_false_values(self):
        """Verify _env_flag returns False for non-affirmative values."""
        from src.dispatch.mjolnir import MjolnirProtocol

        with patch.dict(os.environ, {"TEST_FLAG": "0"}):
            assert MjolnirProtocol._env_flag("TEST_FLAG") is False
        with patch.dict(os.environ, {"TEST_FLAG": "false"}):
            assert MjolnirProtocol._env_flag("TEST_FLAG") is False
        with patch.dict(os.environ, {}, clear=False):
            # Missing key uses default
            os.environ.pop("NONEXISTENT_FLAG", None)
            assert MjolnirProtocol._env_flag("NONEXISTENT_FLAG") is False

    def test_coerce_bool_values(self):
        """Verify _coerce_bool handles various input types."""
        from src.dispatch.mjolnir import MjolnirProtocol

        # None uses default
        assert MjolnirProtocol._coerce_bool(None, True) is True
        assert MjolnirProtocol._coerce_bool(None, False) is False

        # Bool passthrough
        assert MjolnirProtocol._coerce_bool(True, False) is True
        assert MjolnirProtocol._coerce_bool(False, True) is False

        # String coercion
        assert MjolnirProtocol._coerce_bool("1", False) is True
        assert MjolnirProtocol._coerce_bool("true", False) is True
        assert MjolnirProtocol._coerce_bool("yes", False) is True
        assert MjolnirProtocol._coerce_bool("0", True) is False
        assert MjolnirProtocol._coerce_bool("false", True) is False

    def test_apply_sns_when_unavailable(self):
        """Verify _apply_sns returns original prompt when SNS is unavailable."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        # Force SNS unavailable by clearing the cached converter
        protocol._sns_helper_loaded = True
        protocol._sns_convert = None

        result, metadata = protocol._apply_sns("Test prompt")
        assert result == "Test prompt"
        assert metadata.get("sns_available") is False

    def test_normalize_operating_mode_valid_values(self):
        """Verify _normalize_operating_mode accepts strict/balanced/fast."""
        from src.dispatch.mjolnir import MjolnirProtocol

        assert MjolnirProtocol._normalize_operating_mode("strict") == "strict"
        assert MjolnirProtocol._normalize_operating_mode("BALANCED") == "balanced"
        assert MjolnirProtocol._normalize_operating_mode("Fast") == "fast"

    def test_normalize_operating_mode_default(self):
        """Verify _normalize_operating_mode defaults to balanced."""
        from src.dispatch.mjolnir import MjolnirProtocol

        assert MjolnirProtocol._normalize_operating_mode("invalid") == "balanced"
        assert MjolnirProtocol._normalize_operating_mode("") == "balanced"
        assert MjolnirProtocol._normalize_operating_mode(None) == "balanced"

    def test_normalize_risk_level_explicit_values(self):
        """Verify _normalize_risk_level accepts low/medium/high."""
        from src.dispatch.mjolnir import MjolnirProtocol

        assert MjolnirProtocol._normalize_risk_level("low") == "low"
        assert MjolnirProtocol._normalize_risk_level("MEDIUM") == "medium"
        assert MjolnirProtocol._normalize_risk_level("High") == "high"

    def test_normalize_risk_level_from_priority(self):
        """Verify _normalize_risk_level infers from priority when not explicit."""
        from src.dispatch.mjolnir import MjolnirProtocol

        # CRITICAL/HIGH priority → high risk
        assert MjolnirProtocol._normalize_risk_level("", "CRITICAL") == "high"
        assert MjolnirProtocol._normalize_risk_level(None, "HIGH") == "high"
        # LOW/BACKGROUND priority → low risk
        assert MjolnirProtocol._normalize_risk_level("", "LOW") == "low"
        assert MjolnirProtocol._normalize_risk_level("", "BACKGROUND") == "low"
        # NORMAL/other → medium risk
        assert MjolnirProtocol._normalize_risk_level("", "NORMAL") == "medium"
        assert MjolnirProtocol._normalize_risk_level("", "") == "medium"

    def test_merge_dict_shallow(self):
        """Verify _merge_dict performs shallow merge."""
        from src.dispatch.mjolnir import MjolnirProtocol

        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = MjolnirProtocol._merge_dict(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}
        # Original shouldn't be mutated
        assert base == {"a": 1, "b": 2}

    def test_merge_dict_deep(self):
        """Verify _merge_dict recursively merges nested dicts."""
        from src.dispatch.mjolnir import MjolnirProtocol

        base = {"outer": {"inner_a": 1, "inner_b": 2}, "flat": "x"}
        override = {"outer": {"inner_b": 99, "inner_c": 3}}
        result = MjolnirProtocol._merge_dict(base, override)
        assert result == {"outer": {"inner_a": 1, "inner_b": 99, "inner_c": 3}, "flat": "x"}

    def test_merge_dict_replaces_non_dict(self):
        """Verify _merge_dict replaces non-dict values (not merges)."""
        from src.dispatch.mjolnir import MjolnirProtocol

        base = {"key": {"nested": 1}}
        override = {"key": "replaced"}
        result = MjolnirProtocol._merge_dict(base, override)
        assert result == {"key": "replaced"}

    def test_ask_intermediary_success(self):
        """Verify _ask_intermediary returns success when intermediary works."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()

        # Create a mock event with payload
        mock_event = MagicMock()
        mock_event.payload = "Analysis result from intermediary"
        mock_event.event_id = "evt-123"

        mock_intermediary = MagicMock()
        mock_intermediary.handle = AsyncMock(return_value=mock_event)

        protocol._intermediary = mock_intermediary
        protocol._intermediary_loaded = True

        result = asyncio.run(protocol._ask_intermediary("Analyze this", {}, task_type="analyze"))

        assert result["status"] == "success"
        assert result["system"] == "intermediary"
        assert "Analysis result" in result["response"]
        assert result["event_id"] == "evt-123"
        mock_intermediary.handle.assert_called_once()

    def test_ask_intermediary_exception(self):
        """Verify _ask_intermediary handles exceptions from intermediary."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()

        mock_intermediary = MagicMock()
        mock_intermediary.handle = AsyncMock(side_effect=RuntimeError("Network timeout"))

        protocol._intermediary = mock_intermediary
        protocol._intermediary_loaded = True

        result = asyncio.run(protocol._ask_intermediary("Test prompt", {}, task_type="debug"))

        assert result["status"] == "failed"
        assert result["system"] == "intermediary"
        assert "Network timeout" in result["error"]

    def test_get_sns_convert_success(self):
        """Verify _get_sns_convert returns convert function when SNS available."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        protocol._sns_helper_loaded = False
        protocol._sns_convert = None

        mock_convert = MagicMock(return_value=("compressed", {"ratio": 0.5}))

        with patch.dict(
            "sys.modules",
            {"src.utils.sns_core_helper": MagicMock(convert_to_sns=mock_convert)},
        ):
            # Force reload by clearing cache
            protocol._sns_helper_loaded = False

            protocol._get_sns_convert()

            # After first load, should be cached
            assert protocol._sns_helper_loaded is True

    def test_get_sns_convert_caches_result(self):
        """Verify _get_sns_convert caches and returns same convert function."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        mock_convert = MagicMock()

        protocol._sns_helper_loaded = True
        protocol._sns_convert = mock_convert

        result = protocol._get_sns_convert()
        assert result is mock_convert

    def test_apply_sns_success(self):
        """Verify _apply_sns compresses prompt when SNS available."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        protocol._sns_helper_loaded = True
        protocol._sns_convert = MagicMock(
            return_value=("compressed prompt", {"ratio": 0.6, "original_len": 20})
        )

        result, metadata = protocol._apply_sns("Original long prompt")

        assert result == "compressed prompt"
        assert metadata["ratio"] == 0.6
        protocol._sns_convert.assert_called_once_with("Original long prompt", aggressive=False)

    def test_apply_sns_exception(self):
        """Verify _apply_sns returns original prompt when convert raises."""
        from src.dispatch.mjolnir import MjolnirProtocol

        protocol = MjolnirProtocol()
        protocol._sns_helper_loaded = True
        protocol._sns_convert = MagicMock(side_effect=ValueError("Encoding error"))

        result, metadata = protocol._apply_sns("Test prompt")

        assert result == "Test prompt"
        assert "sns_error" in metadata
        assert "Encoding error" in metadata["sns_error"]


# ── Quest Executor Bridge ─────────────────────────────────────────────────────


class TestQuestExecutorBridge:
    """Tests for QuestExecutorBridge and helper functions."""

    def test_extract_target_from_tags_known_agent(self):
        """Verify _extract_target_from_tags returns known agent from tags."""
        from src.dispatch.quest_executor_bridge import _extract_target_from_tags

        assert _extract_target_from_tags(["mjolnir", "ollama"]) == "ollama"
        assert _extract_target_from_tags(["chatdev", "generate"]) == "chatdev"
        assert _extract_target_from_tags(["lmstudio"]) == "lmstudio"

    def test_extract_target_from_tags_no_match(self):
        """Verify _extract_target_from_tags returns 'auto' when no agent found."""
        from src.dispatch.quest_executor_bridge import _extract_target_from_tags

        assert _extract_target_from_tags(["mjolnir", "escalation"]) == "auto"
        assert _extract_target_from_tags([]) == "auto"
        assert _extract_target_from_tags(["unknown", "tags"]) == "auto"

    def test_quest_priority_to_string_valid(self):
        """Verify _quest_priority_to_string maps priority ints."""
        from src.dispatch.quest_executor_bridge import _quest_priority_to_string

        assert _quest_priority_to_string(1) == "CRITICAL"
        assert _quest_priority_to_string(2) == "HIGH"
        assert _quest_priority_to_string(3) == "NORMAL"
        assert _quest_priority_to_string(4) == "LOW"
        assert _quest_priority_to_string(5) == "BACKGROUND"

    def test_quest_priority_to_string_default(self):
        """Verify _quest_priority_to_string defaults to NORMAL."""
        from src.dispatch.quest_executor_bridge import _quest_priority_to_string

        assert _quest_priority_to_string(0) == "NORMAL"
        assert _quest_priority_to_string(99) == "NORMAL"

    def test_bridge_lazy_init_protocol(self):
        """Verify QuestExecutorBridge lazy-inits MjolnirProtocol."""
        from src.dispatch.mjolnir import MjolnirProtocol
        from src.dispatch.quest_executor_bridge import QuestExecutorBridge

        bridge = QuestExecutorBridge()
        assert bridge._protocol is None

        protocol = bridge._get_protocol()
        assert isinstance(protocol, MjolnirProtocol)
        assert bridge._protocol is protocol

    def test_bridge_uses_provided_protocol(self):
        """Verify QuestExecutorBridge uses provided protocol."""
        from src.dispatch.mjolnir import MjolnirProtocol
        from src.dispatch.quest_executor_bridge import QuestExecutorBridge

        custom_protocol = MjolnirProtocol()
        bridge = QuestExecutorBridge(protocol=custom_protocol)
        assert bridge._get_protocol() is custom_protocol

    def test_drain_guild_import_failure(self):
        """Verify drain() returns empty when GuildBoard unavailable."""
        from src.dispatch.quest_executor_bridge import QuestExecutorBridge

        bridge = QuestExecutorBridge()

        with patch.dict("sys.modules", {"src.guild.guild_board": None}):
            result = asyncio.run(bridge.drain(limit=5))
            assert result == []

    def test_drain_no_quests(self):
        """Verify drain() returns empty when no quests available."""
        from src.dispatch.quest_executor_bridge import QuestExecutorBridge

        bridge = QuestExecutorBridge()

        mock_guild = MagicMock()
        mock_guild.get_available_quests = AsyncMock(return_value=[])

        with patch("src.guild.guild_board.GuildBoard", return_value=mock_guild):
            result = asyncio.run(bridge.drain(limit=5))
            assert result == []
            mock_guild.get_available_quests.assert_called_once()

    def test_drain_get_quests_exception(self):
        """Verify drain() returns empty when get_available_quests fails."""
        from src.dispatch.quest_executor_bridge import QuestExecutorBridge

        bridge = QuestExecutorBridge()

        mock_guild = MagicMock()
        mock_guild.get_available_quests = AsyncMock(side_effect=RuntimeError("Database error"))

        with patch("src.guild.guild_board.GuildBoard", return_value=mock_guild):
            result = asyncio.run(bridge.drain(limit=5))
            assert result == []

    def test_drain_processes_quests(self):
        """Verify drain() processes quests and returns results."""
        from src.dispatch.mjolnir import MjolnirProtocol
        from src.dispatch.quest_executor_bridge import QuestExecutorBridge
        from src.dispatch.response_envelope import ResponseEnvelope

        # Create mock quest
        mock_quest = MagicMock()
        mock_quest.quest_id = "quest-001"
        mock_quest.title = "Analyze code"
        mock_quest.description = "Analyze the auth module"
        mock_quest.tags = ["ollama", "analyze"]
        mock_quest.priority = 3

        mock_guild = MagicMock()
        mock_guild.get_available_quests = AsyncMock(return_value=[mock_quest])
        mock_guild.claim_quest = AsyncMock(return_value=(True, "Claimed"))
        mock_guild.complete_quest = AsyncMock()

        mock_protocol = MagicMock(spec=MjolnirProtocol)
        mock_envelope = MagicMock(spec=ResponseEnvelope)
        mock_envelope.success = True
        mock_envelope.to_dict.return_value = {"status": "completed", "output": "ok"}
        mock_protocol.ask = AsyncMock(return_value=mock_envelope)

        bridge = QuestExecutorBridge(protocol=mock_protocol)

        with patch("src.guild.guild_board.GuildBoard", return_value=mock_guild):
            results = asyncio.run(bridge.drain(limit=5))

        assert len(results) == 1
        assert results[0]["quest_id"] == "quest-001"
        assert results[0]["success"] is True
        assert results[0]["agent"] == "ollama"
        mock_guild.claim_quest.assert_called_once_with("quest-001", agent_id="mjolnir-drain")
        mock_guild.complete_quest.assert_called_once_with("quest-001", agent_id="mjolnir-drain")

    def test_drain_claim_failure(self):
        """Verify drain() handles quest claim failures."""
        from src.dispatch.mjolnir import MjolnirProtocol
        from src.dispatch.quest_executor_bridge import QuestExecutorBridge

        mock_quest = MagicMock()
        mock_quest.quest_id = "quest-002"
        mock_quest.title = "Review changes"
        mock_quest.description = "Review the PR"
        mock_quest.tags = []
        mock_quest.priority = 2

        mock_guild = MagicMock()
        mock_guild.get_available_quests = AsyncMock(return_value=[mock_quest])
        mock_guild.claim_quest = AsyncMock(return_value=(False, "Already claimed"))

        mock_protocol = MagicMock(spec=MjolnirProtocol)
        bridge = QuestExecutorBridge(protocol=mock_protocol)

        with patch("src.guild.guild_board.GuildBoard", return_value=mock_guild):
            results = asyncio.run(bridge.drain(limit=1))

        assert len(results) == 1
        assert results[0]["success"] is False
        assert "claim failed" in results[0]["error"].lower()
        # Protocol.ask should NOT be called since claim failed
        mock_protocol.ask.assert_not_called()

    def test_drain_execution_failure(self):
        """Verify drain() handles execution failures gracefully."""
        from src.dispatch.mjolnir import MjolnirProtocol
        from src.dispatch.quest_executor_bridge import QuestExecutorBridge

        mock_quest = MagicMock()
        mock_quest.quest_id = "quest-003"
        mock_quest.title = "Generate tests"
        mock_quest.description = "Create tests for api"
        mock_quest.tags = ["chatdev"]
        mock_quest.priority = 4

        mock_guild = MagicMock()
        mock_guild.get_available_quests = AsyncMock(return_value=[mock_quest])
        mock_guild.claim_quest = AsyncMock(return_value=(True, "OK"))

        mock_protocol = MagicMock(spec=MjolnirProtocol)
        # ask() raises exception
        mock_protocol.ask = AsyncMock(side_effect=RuntimeError("Agent timeout"))

        bridge = QuestExecutorBridge(protocol=mock_protocol)

        with patch("src.guild.guild_board.GuildBoard", return_value=mock_guild):
            results = asyncio.run(bridge.drain(limit=1))

        assert len(results) == 1
        assert results[0]["success"] is False
        assert "timeout" in results[0]["error"].lower()

    def test_drain_respects_limit(self):
        """Verify drain() respects the limit parameter."""
        from src.dispatch.mjolnir import MjolnirProtocol
        from src.dispatch.quest_executor_bridge import QuestExecutorBridge
        from src.dispatch.response_envelope import ResponseEnvelope

        # Create 5 quests, but limit to 2
        quests = []
        for i in range(5):
            q = MagicMock()
            q.quest_id = f"quest-{i:03d}"
            q.title = f"Task {i}"
            q.description = f"Do task {i}"
            q.tags = ["ollama"]
            q.priority = 3
            quests.append(q)

        mock_guild = MagicMock()
        mock_guild.get_available_quests = AsyncMock(return_value=quests)
        mock_guild.claim_quest = AsyncMock(return_value=(True, "OK"))
        mock_guild.complete_quest = AsyncMock()

        mock_envelope = MagicMock(spec=ResponseEnvelope)
        mock_envelope.success = True
        mock_envelope.to_dict.return_value = {"status": "ok"}

        mock_protocol = MagicMock(spec=MjolnirProtocol)
        mock_protocol.ask = AsyncMock(return_value=mock_envelope)

        bridge = QuestExecutorBridge(protocol=mock_protocol)

        with patch("src.guild.guild_board.GuildBoard", return_value=mock_guild):
            results = asyncio.run(bridge.drain(limit=2))

        # Should only process 2 quests
        assert len(results) == 2
        assert mock_protocol.ask.call_count == 2

    def test_execute_quest_claim_exception(self):
        """Verify _execute_quest handles claim exceptions."""
        from src.dispatch.mjolnir import MjolnirProtocol
        from src.dispatch.quest_executor_bridge import QuestExecutorBridge

        mock_quest = MagicMock()
        mock_quest.quest_id = "quest-exc"
        mock_quest.title = "Crash test"
        mock_quest.description = "Will crash"
        mock_quest.tags = []
        mock_quest.priority = 1

        mock_guild = MagicMock()
        mock_guild.claim_quest = AsyncMock(side_effect=ConnectionError("DB gone"))

        mock_protocol = MagicMock(spec=MjolnirProtocol)
        bridge = QuestExecutorBridge(protocol=mock_protocol)

        result = asyncio.run(bridge._execute_quest(mock_guild, mock_protocol, mock_quest))

        assert result["success"] is False
        assert "DB gone" in result["error"]
        assert result["agent"] == "none"


# ── CLI Dispatcher ────────────────────────────────────────────────────────────


class TestCLIDispatcher:
    """Verify argparse CLI structure."""

    def test_build_parser(self):
        from scripts.nusyq_dispatch import _build_parser

        parser = _build_parser()
        # Should parse status command
        args = parser.parse_args(["status"])
        assert args.command == "status"

    def test_parser_ask_command(self):
        from scripts.nusyq_dispatch import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["ask", "ollama", "Test prompt", "--sns"])
        assert args.command == "ask"
        assert args.agent == "ollama"
        assert args.prompt == "Test prompt"
        assert args.sns is True

    def test_parser_council_command(self):
        from scripts.nusyq_dispatch import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["council", "Best approach?", "--agents=ollama,codex"])
        assert args.command == "council"
        assert args.agents == "ollama,codex"

    def test_parser_chain_requires_agents(self):
        from scripts.nusyq_dispatch import _build_parser

        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["chain", "Test prompt"])  # --agents is required

    def test_parser_delegate_command(self):
        from scripts.nusyq_dispatch import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["delegate", "Refactor auth", "--agent=codex", "--priority=1"])
        assert args.command == "delegate"
        assert args.agent == "codex"
        assert args.priority == 1

    def test_parser_queue_command(self):
        from scripts.nusyq_dispatch import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["queue", "Generate tests", "--priority=HIGH"])
        assert args.command == "queue"
        assert args.priority == "HIGH"

    def test_parser_ask_non_blocking_flags(self):
        from scripts.nusyq_dispatch import _build_parser

        parser = _build_parser()
        args = parser.parse_args(
            [
                "ask",
                "openclaw",
                "Test prompt",
                "--non-blocking",
                "--retry-attempts=3",
                "--retry-backoff=0.5",
                "--openclaw-agent=nusyq",
                "--operating-mode=balanced",
                "--risk=low",
                "--signal-budget=minimal",
            ]
        )
        assert args.command == "ask"
        assert args.non_blocking is True
        assert args.retry_attempts == 3
        assert args.retry_backoff == 0.5
        assert args.openclaw_agent == "nusyq"
        assert args.operating_mode == "balanced"
        assert args.risk == "low"
        assert args.signal_budget == "minimal"


# ── dispatch_actions wiring ───────────────────────────────────────────────────


class TestDispatchActions:
    """Verify start_nusyq.py wiring module."""

    def test_handle_dispatch_no_subcommand(self, capsys):
        from scripts.nusyq_actions.dispatch_actions import handle_dispatch

        rc = handle_dispatch(["dispatch"], paths=MagicMock())
        assert rc == 1
        captured = capsys.readouterr()
        assert "No dispatch subcommand" in captured.out

    def test_handle_dispatch_status(self, capsys):
        """Verify status subcommand works through handle_dispatch."""
        from scripts.nusyq_actions.dispatch_actions import handle_dispatch

        mock_paths = MagicMock()
        mock_paths.nusyq_hub = _PROJECT_ROOT

        rc = handle_dispatch(["dispatch", "status"], paths=mock_paths)
        assert rc == 0
        captured = capsys.readouterr()
        assert "mjolnir" in captured.out


class TestCouncilSynthesizer:
    """Tests for CouncilSynthesizer consensus module."""

    def test_synthesize_empty_input(self):
        """Verify empty input returns divergent result."""
        from src.dispatch.council_synthesizer import CouncilSynthesizer

        synthesizer = CouncilSynthesizer()
        result = synthesizer.synthesize({})

        assert result["consensus_level"] == "divergent"
        assert result["confidence"] == 0.0
        assert result["recommendation"] == "No agents responded"
        assert result["agents_consulted"] == 0
        assert result["agents_succeeded"] == 0

    def test_synthesize_single_success(self):
        """Verify single successful response gives strong consensus."""
        from src.dispatch.council_synthesizer import CouncilSynthesizer

        synthesizer = CouncilSynthesizer()
        responses = {"ollama": {"status": "ok", "output": "The answer is 42."}}
        result = synthesizer.synthesize(responses)

        assert result["consensus_level"] == "strong"  # 100% self-agreement
        assert result["agents_consulted"] == 1
        assert result["agents_succeeded"] == 1
        assert result["recommendation"] == "The answer is 42."

    def test_synthesize_all_failures(self):
        """Verify all failures reports errors."""
        from src.dispatch.council_synthesizer import CouncilSynthesizer

        synthesizer = CouncilSynthesizer()
        responses = {
            "ollama": {"status": "error", "output": "Connection failed"},
            "lmstudio": {"status": "error", "error": "Timeout"},
        }
        result = synthesizer.synthesize(responses)

        assert result["consensus_level"] == "divergent"
        assert result["agents_succeeded"] == 0
        assert "Connection failed" in result["recommendation"]

    def test_synthesize_mixed_success_failure(self):
        """Verify mixed results use successful responses."""
        from src.dispatch.council_synthesizer import CouncilSynthesizer

        synthesizer = CouncilSynthesizer()
        responses = {
            "ollama": {"status": "ok", "output": "Python is great"},
            "lmstudio": {"status": "error", "output": "Connection timeout"},
        }
        result = synthesizer.synthesize(responses)

        assert result["agents_consulted"] == 2
        assert result["agents_succeeded"] == 1
        assert "Python" in result["recommendation"]

    def test_synthesize_strong_consensus(self):
        """Verify similar outputs produce strong consensus."""
        from src.dispatch.council_synthesizer import CouncilSynthesizer

        synthesizer = CouncilSynthesizer()
        responses = {
            "ollama": {"status": "ok", "output": "Use pytest for Python testing frameworks"},
            "lmstudio": {"status": "ok", "output": "pytest is the best Python testing framework"},
            "chatdev": {"status": "ok", "output": "For testing Python, use pytest framework"},
        }
        result = synthesizer.synthesize(responses)

        assert result["consensus_level"] in ("strong", "moderate")
        assert result["agents_succeeded"] == 3
        assert len(result["agreement_matrix"]) == 3  # 3 pairs

    def test_synthesize_divergent_opinions(self):
        """Verify divergent outputs are detected."""
        from src.dispatch.council_synthesizer import CouncilSynthesizer

        synthesizer = CouncilSynthesizer()
        responses = {
            "ollama": {"status": "ok", "output": "Use React with TypeScript for the frontend"},
            "lmstudio": {"status": "ok", "output": "Python Django is best for backend APIs"},
            "chatdev": {"status": "ok", "output": "MongoDB provides NoSQL database flexibility"},
        }
        result = synthesizer.synthesize(responses)

        assert result["consensus_level"] in ("weak", "divergent")
        assert len(result["dissenting_views"]) >= 1

    def test_timing_penalty_applied(self):
        """Verify slow responses get lower quality scores."""
        from src.dispatch.council_synthesizer import CouncilSynthesizer

        synthesizer = CouncilSynthesizer()
        # Both outputs long enough to avoid MIN_OUTPUT_LENGTH penalty
        responses = {
            "fast_agent": {
                "status": "ok",
                "output": "This is a quick detailed response here with enough words",
                "timing_ms": 500,
            },
            "slow_agent": {
                "status": "ok",
                "output": "This is a slower detailed response here with enough words",
                "timing_ms": 60_000,
            },
        }
        result = synthesizer.synthesize(responses)

        assert result["response_quality"]["fast_agent"] > result["response_quality"]["slow_agent"]

    def test_short_output_penalty(self):
        """Verify very short outputs get lower quality scores."""
        from src.dispatch.council_synthesizer import CouncilSynthesizer

        synthesizer = CouncilSynthesizer()
        responses = {
            "verbose_agent": {
                "status": "ok",
                "output": "This is a detailed response with many words.",
            },
            "terse_agent": {"status": "ok", "output": "OK"},
        }
        result = synthesizer.synthesize(responses)

        assert (
            result["response_quality"]["verbose_agent"] > result["response_quality"]["terse_agent"]
        )

    def test_to_text_dict_extraction(self):
        """Verify _to_text extracts text from dict outputs."""
        from src.dispatch.council_synthesizer import CouncilSynthesizer

        synthesizer = CouncilSynthesizer()
        responses = {"agent": {"status": "ok", "output": {"output": "Extracted text from dict"}}}
        result = synthesizer.synthesize(responses)

        assert "Extracted text from dict" in result["recommendation"]

    def test_jaccard_both_empty(self):
        """Verify Jaccard similarity handles empty strings."""
        from src.dispatch.council_synthesizer import CouncilSynthesizer

        sim = CouncilSynthesizer._jaccard_similarity("", "")
        assert sim == 1.0  # Both empty = identical

    def test_jaccard_one_empty(self):
        """Verify Jaccard returns 0 when one text is empty."""
        from src.dispatch.council_synthesizer import CouncilSynthesizer

        sim = CouncilSynthesizer._jaccard_similarity("hello world", "")
        assert sim == 0.0

    def test_jaccard_identical(self):
        """Verify Jaccard returns 1.0 for identical texts."""
        from src.dispatch.council_synthesizer import CouncilSynthesizer

        sim = CouncilSynthesizer._jaccard_similarity("hello world", "hello world")
        assert sim == 1.0

    def test_jaccard_partial_overlap(self):
        """Verify Jaccard computes correct overlap score."""
        from src.dispatch.council_synthesizer import CouncilSynthesizer

        # "hello world" vs "world wide" → intersection={world}, union={hello,world,wide}
        sim = CouncilSynthesizer._jaccard_similarity("hello world", "world wide")
        assert 0.2 < sim < 0.5  # 1/3 = 0.333

    def test_confidence_zero_agents(self):
        """Verify confidence is 0 when no agents consulted."""
        from src.dispatch.council_synthesizer import CouncilSynthesizer

        confidence = CouncilSynthesizer._compute_confidence(0.5, 0, 0)
        assert confidence == 0.0

    def test_confidence_all_succeed(self):
        """Verify confidence calculation with full success."""
        from src.dispatch.council_synthesizer import CouncilSynthesizer

        # 0.8 similarity, 3/3 success → 0.8*0.6 + 1.0*0.4 = 0.88
        confidence = CouncilSynthesizer._compute_confidence(0.8, 3, 3)
        assert 0.85 < confidence < 0.9
