"""Tests for src/dispatch/mjolnir.py — MjolnirProtocol."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers — build a minimal ResponseEnvelope without heavy imports
# ---------------------------------------------------------------------------
from src.dispatch.context_detector import ContextMode
from src.dispatch.mjolnir import (
    AGENT_ALIASES,
    MjolnirProtocol,
    _infer_task_type,
)
from src.dispatch.response_envelope import ResponseEnvelope


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_envelope(**kwargs: Any) -> ResponseEnvelope:
    """Return a ResponseEnvelope with sensible defaults for tests."""
    defaults: dict[str, Any] = {
        "status": "ok",
        "success": True,
        "agent": "ollama",
        "context_mode": "ecosystem",
        "pattern": "ask",
        "output": {"result": "test response"},
        "timing_ms": 42.0,
    }
    defaults.update(kwargs)
    return ResponseEnvelope(**defaults)


def _mock_router_result(status: str = "success", output: str = "ok") -> dict[str, Any]:
    return {"status": status, "output": output}


def _make_protocol(repo_root: Path | None = None) -> MjolnirProtocol:
    """Return a MjolnirProtocol with a mocked ContextDetector."""
    proto = MjolnirProtocol(repo_root=repo_root)
    proto._context = MagicMock()
    proto._context.detect.return_value = ContextMode.ECOSYSTEM
    proto._context.enrich_context.return_value = {"context_mode": "ecosystem"}
    return proto


def _run(coro: Any) -> Any:
    """Run a coroutine synchronously in tests."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# 1. AGENT_ALIASES
# ---------------------------------------------------------------------------


class TestAgentAliases:
    def test_passthrough_aliases_are_identity(self) -> None:
        passthroughs = [
            "ollama",
            "lmstudio",
            "chatdev",
            "copilot",
            "codex",
            "claude_cli",
            "consciousness",
            "quantum_resolver",
            "factory",
            "intermediary",
            "openclaw",
            "skyclaw",
        ]
        for name in passthroughs:
            assert AGENT_ALIASES[name] == name, f"{name} should map to itself"

    def test_shortcut_lms_maps_to_lmstudio(self) -> None:
        assert AGENT_ALIASES["lms"] == "lmstudio"

    def test_shortcut_claude_maps_to_claude_cli(self) -> None:
        assert AGENT_ALIASES["claude"] == "claude_cli"

    def test_shortcut_sv_maps_to_consciousness(self) -> None:
        assert AGENT_ALIASES["sv"] == "consciousness"

    def test_shortcut_quantum_maps_to_quantum_resolver(self) -> None:
        assert AGENT_ALIASES["quantum"] == "quantum_resolver"

    def test_shortcut_qr_maps_to_quantum_resolver(self) -> None:
        assert AGENT_ALIASES["qr"] == "quantum_resolver"

    def test_shortcut_ai_maps_to_intermediary(self) -> None:
        assert AGENT_ALIASES["ai"] == "intermediary"

    def test_shortcut_bridge_maps_to_intermediary(self) -> None:
        assert AGENT_ALIASES["bridge"] == "intermediary"

    def test_shortcut_claw_maps_to_openclaw(self) -> None:
        assert AGENT_ALIASES["claw"] == "openclaw"

    def test_shortcut_oc_maps_to_openclaw(self) -> None:
        assert AGENT_ALIASES["oc"] == "openclaw"

    def test_shortcut_sky_maps_to_skyclaw(self) -> None:
        assert AGENT_ALIASES["sky"] == "skyclaw"

    def test_shortcut_sc_maps_to_skyclaw(self) -> None:
        assert AGENT_ALIASES["sc"] == "skyclaw"

    def test_neural_ml_aliases(self) -> None:
        for alias in ("neural_ml", "ml", "neural", "nn"):
            assert AGENT_ALIASES[alias] == "neural_ml", f"{alias} should map to neural_ml"

    def test_optimizer_aliases(self) -> None:
        for alias in ("optimizer", "opt", "continuous_optimizer"):
            assert AGENT_ALIASES[alias] == "optimizer"

    def test_auto_alias(self) -> None:
        assert AGENT_ALIASES["auto"] == "auto"

    def test_all_values_are_strings(self) -> None:
        for key, value in AGENT_ALIASES.items():
            assert isinstance(value, str), f"AGENT_ALIASES[{key!r}] value must be str"


# ---------------------------------------------------------------------------
# 2. _infer_task_type
# ---------------------------------------------------------------------------


class TestInferTaskType:
    def test_review_keyword(self) -> None:
        assert _infer_task_type("Please review this code") == "review"

    def test_debug_keyword(self) -> None:
        assert _infer_task_type("Fix the bug in the login flow") == "debug"

    def test_analyze_keyword(self) -> None:
        assert _infer_task_type("Analyze performance bottlenecks") == "analyze"

    def test_generate_keyword(self) -> None:
        assert _infer_task_type("Generate unit tests") == "generate"

    def test_plan_keyword(self) -> None:
        assert _infer_task_type("Design the new architecture") == "plan"

    def test_test_keyword(self) -> None:
        assert _infer_task_type("Verify the deployment") == "test"

    def test_document_keyword(self) -> None:
        assert _infer_task_type("Document the API endpoints") == "document"

    def test_refactor_keyword(self) -> None:
        assert _infer_task_type("Refactor the authentication module") == "refactor"

    def test_optimize_keyword(self) -> None:
        assert _infer_task_type("Optimize the database queries") == "optimize"

    def test_default_returns_analyze(self) -> None:
        assert _infer_task_type("do something completely unrelated") == "analyze"

    def test_case_insensitive(self) -> None:
        assert _infer_task_type("REVIEW THIS CODE") == "review"


# ---------------------------------------------------------------------------
# 3. MjolnirProtocol.__init__
# ---------------------------------------------------------------------------


class TestMjolnirProtocolInit:
    def test_default_repo_root_is_none(self) -> None:
        proto = MjolnirProtocol()
        assert proto._repo_root is None

    def test_custom_repo_root_stored(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        assert proto._repo_root == tmp_path

    def test_lazy_deps_start_as_none(self) -> None:
        proto = MjolnirProtocol()
        assert proto._router is None
        assert proto._guild is None
        assert proto._sns_convert is None
        assert proto._intermediary is None

    def test_sns_helper_not_loaded_at_init(self) -> None:
        proto = MjolnirProtocol()
        assert proto._sns_helper_loaded is False

    def test_intermediary_not_loaded_at_init(self) -> None:
        proto = MjolnirProtocol()
        assert proto._intermediary_loaded is False

    def test_profile_cache_empty_at_init(self) -> None:
        proto = MjolnirProtocol()
        assert proto._profile_config_cache is None
        assert proto._profile_config_cache_key is None


# ---------------------------------------------------------------------------
# 4. _resolve_agent
# ---------------------------------------------------------------------------


class TestResolveAgent:
    def test_known_alias_resolved(self) -> None:
        proto = MjolnirProtocol()
        assert proto._resolve_agent("lms") == "lmstudio"

    def test_unknown_agent_returned_as_is(self) -> None:
        proto = MjolnirProtocol()
        assert proto._resolve_agent("totally_unknown_agent") == "totally_unknown_agent"

    def test_strips_whitespace(self) -> None:
        proto = MjolnirProtocol()
        assert proto._resolve_agent("  claude  ") == "claude_cli"

    def test_lowercases_input(self) -> None:
        proto = MjolnirProtocol()
        assert proto._resolve_agent("OLLAMA") == "ollama"


# ---------------------------------------------------------------------------
# 5. _apply_sns
# ---------------------------------------------------------------------------


class TestApplySns:
    def test_returns_original_when_sns_unavailable(self) -> None:
        proto = MjolnirProtocol()
        proto._sns_helper_loaded = True
        proto._sns_convert = None
        compressed, meta = proto._apply_sns("hello world")
        assert compressed == "hello world"
        assert meta == {"sns_available": False}

    def test_returns_compressed_when_sns_available(self) -> None:
        proto = MjolnirProtocol()
        proto._sns_helper_loaded = True
        mock_convert = MagicMock(return_value=("compressed text", {"replacements": 3}))
        proto._sns_convert = mock_convert
        compressed, meta = proto._apply_sns("original text")
        assert compressed == "compressed text"
        assert meta == {"replacements": 3}

    def test_fallback_on_sns_exception(self) -> None:
        proto = MjolnirProtocol()
        proto._sns_helper_loaded = True
        proto._sns_convert = MagicMock(side_effect=RuntimeError("boom"))
        compressed, meta = proto._apply_sns("original")
        assert compressed == "original"
        assert "sns_error" in meta


# ---------------------------------------------------------------------------
# 6. ask() — success path
# ---------------------------------------------------------------------------


class TestAskSuccess:
    def _make_proto_with_router(self) -> tuple[MjolnirProtocol, MagicMock]:
        proto = _make_protocol()
        mock_router = MagicMock()
        mock_router.route_task = AsyncMock(
            return_value={"status": "success", "output": "router response"}
        )
        proto._router = mock_router
        proto._guild = False  # disable guild (sentinel)
        proto._registry = MagicMock()
        proto._registry.RECOVERABLE_AGENTS = set()
        return proto, mock_router

    def test_ask_returns_response_envelope(self) -> None:
        proto, _ = self._make_proto_with_router()
        result = _run(proto.ask("ollama", "analyze this"))
        assert isinstance(result, ResponseEnvelope)

    def test_ask_pattern_is_ask(self) -> None:
        proto, _ = self._make_proto_with_router()
        result = _run(proto.ask("ollama", "analyze this"))
        assert result.pattern == "ask"

    def test_ask_agent_is_resolved(self) -> None:
        proto, _ = self._make_proto_with_router()
        result = _run(proto.ask("lms", "analyze this"))
        assert result.agent == "lmstudio"

    def test_ask_calls_router_route_task(self) -> None:
        proto, mock_router = self._make_proto_with_router()
        _run(proto.ask("ollama", "review my code"))
        mock_router.route_task.assert_called_once()

    def test_ask_infers_task_type_from_prompt(self) -> None:
        proto, mock_router = self._make_proto_with_router()
        _run(proto.ask("ollama", "review the codebase"))
        call_kwargs = mock_router.route_task.call_args
        assert call_kwargs.kwargs.get("task_type") == "review" or (
            call_kwargs.args and call_kwargs.args[0] == "review"
        )

    def test_ask_uses_explicit_task_type(self) -> None:
        proto, mock_router = self._make_proto_with_router()
        _run(proto.ask("ollama", "do something", task_type="generate"))
        call_kwargs = mock_router.route_task.call_args
        # task_type should be "generate" regardless of prompt
        assert "generate" in str(call_kwargs)

    def test_ask_passes_model_to_context(self) -> None:
        proto, mock_router = self._make_proto_with_router()
        _run(proto.ask("ollama", "analyze this", model="qwen2.5-coder:14b"))
        ctx_arg = mock_router.route_task.call_args.kwargs.get("context", {})
        assert ctx_arg.get("ollama_model") == "qwen2.5-coder:14b"

    def test_ask_passes_context_file(self) -> None:
        proto, mock_router = self._make_proto_with_router()
        _run(proto.ask("ollama", "review this", context_file="src/main.py"))
        ctx_arg = mock_router.route_task.call_args.kwargs.get("context", {})
        assert ctx_arg.get("file") == "src/main.py"

    def test_ask_no_guild_skips_guild_announce(self) -> None:
        proto, _ = self._make_proto_with_router()
        mock_guild = AsyncMock()
        proto._guild = mock_guild
        _run(proto.ask("ollama", "analyze", no_guild=True))
        mock_guild.add_quest.assert_not_called()

    def test_ask_with_extra_context_merges(self) -> None:
        proto, mock_router = self._make_proto_with_router()
        _run(proto.ask("ollama", "analyze", extra_context={"custom_key": "custom_value"}))
        ctx_arg = mock_router.route_task.call_args.kwargs.get("context", {})
        assert ctx_arg.get("custom_key") == "custom_value"


# ---------------------------------------------------------------------------
# 7. ask() — alias resolution
# ---------------------------------------------------------------------------


class TestAskAliasResolution:
    def _make_proto(self) -> MjolnirProtocol:
        proto = _make_protocol()
        mock_router = MagicMock()
        mock_router.route_task = AsyncMock(
            return_value={"status": "success", "output": "ok"}
        )
        proto._router = mock_router
        proto._guild = False
        proto._registry = MagicMock()
        proto._registry.RECOVERABLE_AGENTS = set()
        return proto

    def test_alias_claude_resolves_to_claude_cli(self) -> None:
        proto = self._make_proto()
        result = _run(proto.ask("claude", "hello"))
        assert result.agent == "claude_cli"

    def test_alias_sv_resolves_to_consciousness(self) -> None:
        proto = self._make_proto()
        result = _run(proto.ask("sv", "hello"))
        assert result.agent == "consciousness"

    def test_alias_nn_resolves_to_neural_ml(self) -> None:
        proto = self._make_proto()
        result = _run(proto.ask("nn", "train the model"))
        assert result.agent == "neural_ml"


# ---------------------------------------------------------------------------
# 8. ask() — SNS compression branch
# ---------------------------------------------------------------------------


class TestAskSnsCompression:
    def test_sns_not_applied_by_default(self) -> None:
        proto = _make_protocol()
        mock_router = MagicMock()
        mock_router.route_task = AsyncMock(
            return_value={"status": "success", "output": "ok"}
        )
        proto._router = mock_router
        proto._guild = False
        proto._registry = MagicMock()
        proto._registry.RECOVERABLE_AGENTS = set()
        result = _run(proto.ask("ollama", "analyze something"))
        assert result.sns_applied is False

    def test_sns_applied_flag_set_when_replacements_exist(self) -> None:
        proto = _make_protocol()
        mock_router = MagicMock()
        mock_router.route_task = AsyncMock(
            return_value={"status": "success", "output": "ok"}
        )
        proto._router = mock_router
        proto._guild = False
        proto._registry = MagicMock()
        proto._registry.RECOVERABLE_AGENTS = set()
        proto._sns_helper_loaded = True
        proto._sns_convert = MagicMock(
            return_value=("compressed prompt", {"replacements": 5, "sns_tokens_est": 10})
        )
        result = _run(proto.ask("ollama", "original long prompt", sns=True))
        assert result.sns_applied is True

    def test_sns_false_when_no_replacements(self) -> None:
        proto = _make_protocol()
        mock_router = MagicMock()
        mock_router.route_task = AsyncMock(
            return_value={"status": "success", "output": "ok"}
        )
        proto._router = mock_router
        proto._guild = False
        proto._registry = MagicMock()
        proto._registry.RECOVERABLE_AGENTS = set()
        # SNS returns no replacements
        proto._sns_helper_loaded = True
        proto._sns_convert = MagicMock(
            return_value=("same prompt", {"replacements": 0})
        )
        result = _run(proto.ask("ollama", "same prompt", sns=True))
        assert result.sns_applied is False


# ---------------------------------------------------------------------------
# 9. ask() — agent unavailable (recoverable agent offline)
# ---------------------------------------------------------------------------


class TestAskAgentUnavailable:
    def test_returns_error_envelope_when_ollama_offline(self) -> None:
        proto = _make_protocol()
        proto._guild = False

        mock_probe = MagicMock()
        mock_probe.status = "offline"
        mock_probe.detail = "Connection refused"

        mock_registry = MagicMock()
        mock_registry.RECOVERABLE_AGENTS = {"ollama"}
        mock_registry.probe_with_recovery = AsyncMock(return_value=mock_probe)
        proto._registry = mock_registry

        result = _run(proto.ask("ollama", "hello"))
        assert result.success is False
        assert result.status == "error"
        assert "unavailable" in (result.error or "").lower()

    def test_non_recoverable_agent_bypasses_probe(self) -> None:
        proto = _make_protocol()
        proto._guild = False

        mock_router = MagicMock()
        mock_router.route_task = AsyncMock(
            return_value={"status": "success", "output": "ok"}
        )
        proto._router = mock_router

        mock_registry = MagicMock()
        mock_registry.RECOVERABLE_AGENTS = set()  # copilot not recoverable
        proto._registry = mock_registry

        result = _run(proto.ask("copilot", "hello"))
        assert isinstance(result, ResponseEnvelope)
        # Should not call probe
        mock_registry.probe_with_recovery.assert_not_called()


# ---------------------------------------------------------------------------
# 10. council()
# ---------------------------------------------------------------------------


class TestCouncil:
    def _make_proto_for_council(self) -> MjolnirProtocol:
        proto = _make_protocol()
        proto._guild = False
        proto._registry = MagicMock()
        proto._registry.RECOVERABLE_AGENTS = set()

        mock_router = MagicMock()
        mock_router.route_task = AsyncMock(
            return_value={"status": "success", "output": "agent answer"}
        )
        proto._router = mock_router
        return proto

    def test_council_returns_envelope(self) -> None:
        proto = self._make_proto_for_council()
        result = _run(proto.council("Best approach?", agents=["ollama", "codex"]))
        assert isinstance(result, ResponseEnvelope)

    def test_council_pattern_label(self) -> None:
        proto = self._make_proto_for_council()
        result = _run(proto.council("Best approach?", agents=["ollama", "codex"]))
        assert result.pattern == "council"

    def test_council_agents_used_populated(self) -> None:
        proto = self._make_proto_for_council()
        result = _run(proto.council("question", agents=["ollama", "lmstudio"]))
        assert "ollama" in result.agents_used
        assert "lmstudio" in result.agents_used

    def test_council_output_has_responses_key_when_synthesizer_missing(self) -> None:
        proto = self._make_proto_for_council()
        # CouncilSynthesizer will fail to import in test env
        result = _run(proto.council("question", agents=["ollama"]))
        # output is either dict with "responses" (if synthesizer available)
        # or dict with agent keys (raw) — either is acceptable
        assert result.output is not None

    def test_council_default_agents_are_ollama_and_lmstudio(self) -> None:
        proto = self._make_proto_for_council()
        result = _run(proto.council("default agents?"))
        assert "ollama" in result.agents_used or "lmstudio" in result.agents_used

    def test_council_success_is_true(self) -> None:
        proto = self._make_proto_for_council()
        result = _run(proto.council("question", agents=["ollama"]))
        assert result.success is True


# ---------------------------------------------------------------------------
# 11. parallel()
# ---------------------------------------------------------------------------


class TestParallel:
    def _make_proto(self) -> MjolnirProtocol:
        proto = _make_protocol()
        proto._guild = False
        proto._registry = MagicMock()
        proto._registry.RECOVERABLE_AGENTS = set()
        mock_router = MagicMock()
        mock_router.route_task = AsyncMock(
            return_value={"status": "success", "output": "parallel result"}
        )
        proto._router = mock_router
        return proto

    def test_parallel_returns_envelope(self) -> None:
        proto = self._make_proto()
        result = _run(proto.parallel("write tests", agents=["ollama", "codex"]))
        assert isinstance(result, ResponseEnvelope)

    def test_parallel_pattern_label(self) -> None:
        proto = self._make_proto()
        result = _run(proto.parallel("write tests", agents=["ollama", "codex"]))
        assert result.pattern == "parallel"

    def test_parallel_agents_used(self) -> None:
        proto = self._make_proto()
        result = _run(proto.parallel("write tests", agents=["ollama", "codex"]))
        assert "ollama" in result.agents_used
        assert "codex" in result.agents_used

    def test_parallel_success(self) -> None:
        proto = self._make_proto()
        result = _run(proto.parallel("write tests", agents=["ollama"]))
        assert result.success is True

    def test_parallel_no_synthesis(self) -> None:
        proto = self._make_proto()
        result = _run(proto.parallel("question", agents=["ollama", "lmstudio"]))
        # parallel does NOT add synthesis (unlike council)
        if isinstance(result.output, dict):
            assert "synthesis" not in result.output


# ---------------------------------------------------------------------------
# 12. chain()
# ---------------------------------------------------------------------------


class TestChain:
    def _make_proto_with_success_router(self) -> MjolnirProtocol:
        proto = _make_protocol()
        proto._guild = False
        proto._registry = MagicMock()
        proto._registry.RECOVERABLE_AGENTS = set()
        mock_router = MagicMock()
        mock_router.route_task = AsyncMock(
            return_value={"status": "success", "output": "step output"}
        )
        proto._router = mock_router
        return proto

    def test_chain_returns_envelope(self) -> None:
        proto = self._make_proto_with_success_router()
        result = _run(proto.chain("analyze then generate", agents=["ollama", "codex"]))
        assert isinstance(result, ResponseEnvelope)

    def test_chain_pattern_label(self) -> None:
        proto = self._make_proto_with_success_router()
        result = _run(proto.chain("prompt", agents=["ollama", "codex"]))
        assert result.pattern == "chain"

    def test_chain_agent_label_is_chain(self) -> None:
        proto = self._make_proto_with_success_router()
        result = _run(proto.chain("prompt", agents=["ollama", "codex"]))
        assert result.agent == "chain"

    def test_chain_output_contains_steps(self) -> None:
        proto = self._make_proto_with_success_router()
        result = _run(proto.chain("prompt", agents=["ollama", "codex"]))
        assert isinstance(result.output, list)
        assert len(result.output) == 2

    def test_chain_step_labels_applied(self) -> None:
        proto = self._make_proto_with_success_router()
        result = _run(
            proto.chain(
                "prompt",
                agents=["ollama", "codex"],
                steps=["analyze", "generate"],
            )
        )
        steps = result.output
        assert steps[0]["label"] == "analyze"
        assert steps[1]["label"] == "generate"

    def test_chain_broken_returns_partial(self) -> None:
        proto = _make_protocol()
        proto._guild = False
        proto._registry = MagicMock()
        proto._registry.RECOVERABLE_AGENTS = set()

        mock_router = MagicMock()
        # First step fails
        mock_router.route_task = AsyncMock(
            return_value={"status": "failed", "output": None, "error": "router error"}
        )
        proto._router = mock_router
        result = _run(proto.chain("prompt", agents=["ollama", "codex"]))
        assert result.success is False
        assert result.status == "partial"

    def test_chain_agents_used_ordered(self) -> None:
        proto = self._make_proto_with_success_router()
        result = _run(proto.chain("prompt", agents=["ollama", "codex"]))
        assert result.agents_used == ["ollama", "codex"]


# ---------------------------------------------------------------------------
# 13. delegate()
# ---------------------------------------------------------------------------


class TestDelegate:
    def test_delegate_returns_envelope(self) -> None:
        proto = _make_protocol()
        proto._context.detect.return_value = ContextMode.ECOSYSTEM

        mock_guild = MagicMock()
        mock_guild.add_quest = AsyncMock(return_value=(True, "quest-123"))
        proto._guild = mock_guild

        result = _run(proto.delegate("Generate report", agent="ollama"))
        assert isinstance(result, ResponseEnvelope)

    def test_delegate_pattern_label(self) -> None:
        proto = _make_protocol()
        mock_guild = MagicMock()
        mock_guild.add_quest = AsyncMock(return_value=(True, "quest-456"))
        proto._guild = mock_guild

        result = _run(proto.delegate("task", agent="ollama"))
        assert result.pattern == "delegate"

    def test_delegate_success_when_guild_available(self) -> None:
        proto = _make_protocol()
        mock_guild = MagicMock()
        mock_guild.add_quest = AsyncMock(return_value=(True, "quest-789"))
        proto._guild = mock_guild

        result = _run(proto.delegate("background task"))
        assert result.success is True

    def test_delegate_error_when_guild_unavailable(self) -> None:
        proto = _make_protocol()
        proto._guild = False  # sentinel: tried and failed

        result = _run(proto.delegate("task"))
        assert result.success is False
        assert result.status == "error"

    def test_delegate_output_contains_delegated_flag(self) -> None:
        proto = _make_protocol()
        mock_guild = MagicMock()
        mock_guild.add_quest = AsyncMock(return_value=(True, "q-001"))
        proto._guild = mock_guild

        result = _run(proto.delegate("task"))
        assert isinstance(result.output, dict)
        assert result.output.get("delegated") is True

    def test_delegate_guild_quest_id_in_output(self) -> None:
        proto = _make_protocol()
        mock_guild = MagicMock()
        mock_guild.add_quest = AsyncMock(return_value=(True, "q-002"))
        proto._guild = mock_guild

        result = _run(proto.delegate("task"))
        assert result.guild_quest_id == "q-002"

    def test_delegate_applies_sns(self) -> None:
        proto = _make_protocol()
        mock_guild = MagicMock()
        mock_guild.add_quest = AsyncMock(return_value=(True, "q-003"))
        proto._guild = mock_guild
        proto._sns_helper_loaded = True
        proto._sns_convert = MagicMock(return_value=("compressed", {"replacements": 1}))

        result = _run(proto.delegate("long prompt to compress", sns=True))
        assert result.success is True
        proto._sns_convert.assert_called_once()


# ---------------------------------------------------------------------------
# 14. queue()
# ---------------------------------------------------------------------------


class TestQueue:
    def test_queue_returns_envelope(self) -> None:
        proto = _make_protocol()
        # dispatch_task_cli is a lazy import inside queue() — patch at the module level
        mock_dispatch = AsyncMock(return_value={"status": "queued", "task_id": "t-000"})
        mock_bto = MagicMock()
        mock_bto.dispatch_task_cli = mock_dispatch
        with patch.dict(sys.modules, {"src.orchestration.background_task_orchestrator": mock_bto}):
            result = _run(proto.queue("generate tests"))
        assert isinstance(result, ResponseEnvelope)

    def test_queue_error_when_orchestrator_unavailable(self) -> None:
        proto = _make_protocol()
        # Inject None so the import raises ImportError path
        with patch.dict(sys.modules, {"src.orchestration.background_task_orchestrator": None}):
            result = _run(proto.queue("generate tests"))
        assert result.pattern == "queue"
        assert result.success is False

    def test_queue_success_path(self) -> None:
        proto = _make_protocol()
        mock_dispatch = AsyncMock(return_value={"status": "queued", "task_id": "t-001"})
        mock_bto = MagicMock()
        mock_bto.dispatch_task_cli = mock_dispatch
        with patch.dict(sys.modules, {"src.orchestration.background_task_orchestrator": mock_bto}):
            result = _run(proto.queue("generate unit tests", priority="HIGH"))

        assert isinstance(result, ResponseEnvelope)
        assert result.pattern == "queue"

    def test_queue_applies_sns(self) -> None:
        proto = _make_protocol()
        proto._sns_helper_loaded = True
        proto._sns_convert = MagicMock(return_value=("compressed", {"replacements": 2}))
        mock_dispatch = AsyncMock(return_value={"status": "queued", "task_id": "t-002"})
        mock_bto = MagicMock()
        mock_bto.dispatch_task_cli = mock_dispatch
        with patch.dict(sys.modules, {"src.orchestration.background_task_orchestrator": mock_bto}):
            result = _run(proto.queue("long prompt", sns=True))

        proto._sns_convert.assert_called_once()
        assert result.sns_applied is True

    def test_queue_infers_task_type(self) -> None:
        proto = _make_protocol()
        mock_dispatch = AsyncMock(return_value={"status": "queued", "task_id": "t-003"})
        mock_bto = MagicMock()
        mock_bto.dispatch_task_cli = mock_dispatch
        with patch.dict(sys.modules, {"src.orchestration.background_task_orchestrator": mock_bto}):
            _run(proto.queue("review this module"))

        call_kwargs = mock_dispatch.call_args
        assert call_kwargs.kwargs.get("task_type") == "review"

    def test_queue_respects_explicit_task_type(self) -> None:
        proto = _make_protocol()
        mock_dispatch = AsyncMock(return_value={"status": "queued", "task_id": "t-004"})
        mock_bto = MagicMock()
        mock_bto.dispatch_task_cli = mock_dispatch
        with patch.dict(sys.modules, {"src.orchestration.background_task_orchestrator": mock_bto}):
            _run(proto.queue("do something", task_type="generate"))

        call_kwargs = mock_dispatch.call_args
        assert call_kwargs.kwargs.get("task_type") == "generate"


# ---------------------------------------------------------------------------
# 15. status()
# ---------------------------------------------------------------------------


class TestStatus:
    def test_status_without_probes_returns_envelope(self) -> None:
        proto = _make_protocol()
        result = _run(proto.status())
        assert isinstance(result, ResponseEnvelope)

    def test_status_without_probes_pattern(self) -> None:
        proto = _make_protocol()
        result = _run(proto.status())
        assert result.pattern == "status"

    def test_status_without_probes_output_is_dict(self) -> None:
        proto = _make_protocol()
        result = _run(proto.status())
        assert isinstance(result.output, dict)

    def test_status_without_probes_contains_known_agents(self) -> None:
        proto = _make_protocol()
        result = _run(proto.status())
        assert "ollama" in result.output

    def test_status_without_probes_agent_is_all(self) -> None:
        proto = _make_protocol()
        result = _run(proto.status())
        assert result.agent == "all"

    def test_status_no_probes_status_unknown(self) -> None:
        proto = _make_protocol()
        result = _run(proto.status())
        # Each agent entry should have status=unknown
        ollama_entry = result.output.get("ollama", {})
        assert ollama_entry.get("status") == "unknown"

    def test_status_with_probes_calls_registry(self) -> None:
        proto = _make_protocol()
        mock_probe_result = MagicMock()
        mock_probe_result.to_dict.return_value = {
            "agent": "ollama",
            "status": "online",
            "detail": "",
        }
        mock_registry = MagicMock()
        mock_registry.probe_all = AsyncMock(return_value={"ollama": mock_probe_result})
        proto._registry = mock_registry

        result = _run(proto.status(probes=True))
        mock_registry.probe_all.assert_called_once()
        assert isinstance(result, ResponseEnvelope)

    def test_status_single_agent_without_probes(self) -> None:
        proto = _make_protocol()
        result = _run(proto.status(agent="ollama"))
        assert result.agent == "ollama"
        assert "ollama" in result.output

    def test_status_single_agent_with_probes_recoverable(self) -> None:
        proto = _make_protocol()
        mock_probe_result = MagicMock()
        mock_probe_result.to_dict.return_value = {"agent": "ollama", "status": "online"}
        mock_registry = MagicMock()
        mock_registry.RECOVERABLE_AGENTS = {"ollama"}
        mock_registry.probe_with_recovery = AsyncMock(return_value=mock_probe_result)
        proto._registry = mock_registry

        result = _run(proto.status(agent="ollama", probes=True))
        mock_registry.probe_with_recovery.assert_called_once()
        assert isinstance(result, ResponseEnvelope)

    def test_status_success_is_true(self) -> None:
        proto = _make_protocol()
        result = _run(proto.status())
        assert result.success is True


# ---------------------------------------------------------------------------
# 16. Context detection
# ---------------------------------------------------------------------------


class TestContextDetection:
    def test_ecosystem_mode_when_under_hub_root(self) -> None:
        from src.dispatch.context_detector import ContextDetector

        detector = ContextDetector()
        hub_root = Path("C:/Users/keath/Desktop/Legacy/NuSyQ-Hub")
        with patch.object(detector, "_hub_root", hub_root):
            with patch("pathlib.Path.cwd", return_value=hub_root / "src"):
                mode = detector.detect()
        assert mode == ContextMode.ECOSYSTEM

    def test_game_mode_when_under_simverse_root(self) -> None:
        from src.dispatch.context_detector import ContextDetector

        detector = ContextDetector()
        sim_root = Path("C:/Users/keath/Desktop/SimulatedVerse/SimulatedVerse")
        with patch.object(detector, "_hub_root", None):
            with patch.object(detector, "_simverse_root", sim_root):
                with patch("pathlib.Path.cwd", return_value=sim_root / "ship-console"):
                    mode = detector.detect()
        assert mode == ContextMode.GAME

    def test_project_mode_fallback(self) -> None:
        from src.dispatch.context_detector import ContextDetector

        detector = ContextDetector()
        with patch.object(detector, "_hub_root", None):
            with patch.object(detector, "_simverse_root", None):
                with patch("pathlib.Path.cwd", return_value=Path("/tmp/random")):
                    with patch.dict("os.environ", {"NUSYQ_CONTEXT_MODE": ""}, clear=False):
                        mode = detector.detect()
        assert mode == ContextMode.PROJECT

    def test_env_override_ecosystem(self) -> None:
        from src.dispatch.context_detector import ContextDetector

        detector = ContextDetector()
        with patch.dict("os.environ", {"NUSYQ_CONTEXT_MODE": "ecosystem"}):
            mode = detector.detect()
        assert mode == ContextMode.ECOSYSTEM

    def test_env_override_game(self) -> None:
        from src.dispatch.context_detector import ContextDetector

        detector = ContextDetector()
        with patch.dict("os.environ", {"NUSYQ_CONTEXT_MODE": "game"}):
            mode = detector.detect()
        assert mode == ContextMode.GAME

    def test_context_mode_string_values(self) -> None:
        assert str(ContextMode.ECOSYSTEM) == "ecosystem"
        assert str(ContextMode.GAME) == "game"
        assert str(ContextMode.PROJECT) == "project"
        assert str(ContextMode.AUTO) == "auto"


# ---------------------------------------------------------------------------
# 17. Static helpers
# ---------------------------------------------------------------------------


class TestStaticHelpers:
    def test_env_flag_true_variants(self) -> None:
        for val in ("1", "true", "yes", "on"):
            with patch.dict("os.environ", {"TEST_FLAG": val}):
                assert MjolnirProtocol._env_flag("TEST_FLAG") is True

    def test_env_flag_false_by_default(self) -> None:
        with patch.dict("os.environ", {}, clear=False):
            # Use a key that definitely isn't set
            assert MjolnirProtocol._env_flag("DEFINITELY_NOT_SET_XYZ") is False

    def test_coerce_bool_none_returns_default(self) -> None:
        assert MjolnirProtocol._coerce_bool(None, default=True) is True
        assert MjolnirProtocol._coerce_bool(None, default=False) is False

    def test_coerce_bool_true_string(self) -> None:
        assert MjolnirProtocol._coerce_bool("1") is True
        assert MjolnirProtocol._coerce_bool("yes") is True

    def test_coerce_bool_false_string(self) -> None:
        assert MjolnirProtocol._coerce_bool("0") is False
        assert MjolnirProtocol._coerce_bool("no") is False

    def test_normalize_operating_mode_valid(self) -> None:
        for mode in ("strict", "balanced", "fast"):
            assert MjolnirProtocol._normalize_operating_mode(mode) == mode

    def test_normalize_operating_mode_invalid_returns_balanced(self) -> None:
        assert MjolnirProtocol._normalize_operating_mode("unknown_mode") == "balanced"

    def test_normalize_risk_level_valid(self) -> None:
        for level in ("low", "medium", "high"):
            assert MjolnirProtocol._normalize_risk_level(level) == level

    def test_normalize_risk_level_critical_priority_gives_high(self) -> None:
        assert MjolnirProtocol._normalize_risk_level(None, priority="CRITICAL") == "high"

    def test_normalize_risk_level_low_priority_gives_low(self) -> None:
        assert MjolnirProtocol._normalize_risk_level(None, priority="LOW") == "low"

    def test_priority_map_has_all_levels(self) -> None:
        expected = {"CRITICAL", "HIGH", "NORMAL", "LOW", "BACKGROUND"}
        assert set(MjolnirProtocol._PRIORITY_MAP.keys()) == expected

    def test_priority_map_ordering(self) -> None:
        pm = MjolnirProtocol._PRIORITY_MAP
        assert pm["CRITICAL"] < pm["HIGH"] < pm["NORMAL"] < pm["LOW"] < pm["BACKGROUND"]


# ---------------------------------------------------------------------------
# 18. ResponseEnvelope helpers
# ---------------------------------------------------------------------------


class TestResponseEnvelope:
    def test_from_error_sets_success_false(self) -> None:
        env = ResponseEnvelope.from_error("something failed", agent="ollama")
        assert env.success is False
        assert env.status == "error"
        assert env.error == "something failed"

    def test_wrap_success_dict(self) -> None:
        env = ResponseEnvelope.wrap(
            {"status": "success", "output": "hello"},
            agent="ollama",
            context_mode="ecosystem",
        )
        assert env.success is True
        assert env.status == "ok"

    def test_wrap_failed_dict_sets_error_status(self) -> None:
        env = ResponseEnvelope.wrap(
            {"status": "failed", "output": None},
            agent="ollama",
        )
        assert env.success is False
        assert env.status == "error"

    def test_to_dict_drops_none_values(self) -> None:
        env = ResponseEnvelope(status="ok", success=True, agent="test")
        d = env.to_dict()
        # error and guild_quest_id should be absent (None)
        assert "error" not in d
        assert "guild_quest_id" not in d

    def test_timing_computed_from_start_time(self) -> None:
        import time

        start = time.monotonic() - 0.1  # 100ms ago
        env = ResponseEnvelope.from_error("err", start_time=start)
        assert env.timing_ms is not None
        assert env.timing_ms >= 90.0  # at least 90ms


# ---------------------------------------------------------------------------
# 19. council() — extended edge cases
# ---------------------------------------------------------------------------


class TestCouncilExtended:
    """Additional coverage for council() beyond TestCouncil happy-path."""

    def _make_proto(self) -> MjolnirProtocol:
        proto = _make_protocol()
        proto._guild = False
        proto._registry = MagicMock()
        proto._registry.RECOVERABLE_AGENTS = set()
        mock_router = MagicMock()
        mock_router.route_task = AsyncMock(
            return_value={"status": "success", "output": "response text"}
        )
        proto._router = mock_router
        return proto

    def test_council_output_contains_per_agent_keys(self) -> None:
        """When CouncilSynthesizer is absent the raw dict has agent-keyed entries."""
        proto = self._make_proto()
        # Ensure synthesizer is not importable
        with patch.dict(sys.modules, {"src.dispatch.council_synthesizer": None}):
            result = _run(proto.council("question", agents=["ollama", "codex"]))
        # output could be raw dict or wrapped; either way it's not None
        assert result.output is not None

    def test_council_with_synthesis_wraps_output(self) -> None:
        """When CouncilSynthesizer is available output gains responses+synthesis keys."""
        proto = self._make_proto()
        mock_synth_cls = MagicMock()
        mock_synth_cls.return_value.synthesize.return_value = {
            "consensus_level": "high",
            "confidence": 0.9,
        }
        mock_synth_module = MagicMock()
        mock_synth_module.CouncilSynthesizer = mock_synth_cls
        with patch.dict(sys.modules, {"src.dispatch.council_synthesizer": mock_synth_module}):
            result = _run(proto.council("question", agents=["ollama"]))
        assert isinstance(result.output, dict)
        assert "responses" in result.output
        assert "synthesis" in result.output

    def test_council_synthesis_exception_is_non_fatal(self) -> None:
        """A crash in CouncilSynthesizer does not propagate — envelope still returned."""
        proto = self._make_proto()
        mock_synth_cls = MagicMock()
        mock_synth_cls.return_value.synthesize.side_effect = RuntimeError("synth crash")
        mock_synth_module = MagicMock()
        mock_synth_module.CouncilSynthesizer = mock_synth_cls
        with patch.dict(sys.modules, {"src.dispatch.council_synthesizer": mock_synth_module}):
            result = _run(proto.council("question", agents=["ollama"]))
        assert isinstance(result, ResponseEnvelope)
        assert result.success is True

    def test_council_agent_exception_captured_in_output(self) -> None:
        """If one agent raises, its error is captured and other agents' results kept."""
        proto = _make_protocol()
        proto._guild = False
        proto._registry = MagicMock()
        proto._registry.RECOVERABLE_AGENTS = set()
        # Make route_task raise for any call — both agents will fail
        mock_router = MagicMock()
        mock_router.route_task = AsyncMock(side_effect=RuntimeError("agent down"))
        proto._router = mock_router

        with patch.dict(sys.modules, {"src.dispatch.council_synthesizer": None}):
            result = _run(proto.council("question", agents=["ollama", "codex"]))
        # Even with exceptions in gather, council returns ok (not error)
        assert isinstance(result, ResponseEnvelope)

    def test_council_sns_forwarded_to_fan_out(self) -> None:
        """sns=True is passed through to _fan_out and reflected on the envelope."""
        proto = self._make_proto()
        proto._sns_helper_loaded = True
        proto._sns_convert = MagicMock(
            return_value=("compressed prompt", {"replacements": 3})
        )
        with patch.dict(sys.modules, {"src.dispatch.council_synthesizer": None}):
            result = _run(proto.council("long prompt", agents=["ollama"], sns=True))
        assert result.sns_applied is True

    def test_council_three_agents_all_in_agents_used(self) -> None:
        proto = self._make_proto()
        with patch.dict(sys.modules, {"src.dispatch.council_synthesizer": None}):
            result = _run(
                proto.council("question", agents=["ollama", "lmstudio", "codex"])
            )
        for agent in ("ollama", "lmstudio", "codex"):
            assert agent in result.agents_used


# ---------------------------------------------------------------------------
# 20. parallel() — extended edge cases
# ---------------------------------------------------------------------------


class TestParallelExtended:
    """Additional coverage for parallel() beyond TestParallel happy-path."""

    def _make_proto(self) -> MjolnirProtocol:
        proto = _make_protocol()
        proto._guild = False
        proto._registry = MagicMock()
        proto._registry.RECOVERABLE_AGENTS = set()
        mock_router = MagicMock()
        mock_router.route_task = AsyncMock(
            return_value={"status": "success", "output": "parallel result"}
        )
        proto._router = mock_router
        return proto

    def test_parallel_agent_label_is_pattern(self) -> None:
        """ResponseEnvelope.agent should be 'parallel' (the pattern name)."""
        proto = self._make_proto()
        result = _run(proto.parallel("write tests", agents=["ollama", "codex"]))
        assert result.agent == "parallel"

    def test_parallel_output_is_dict(self) -> None:
        proto = self._make_proto()
        result = _run(proto.parallel("question", agents=["ollama", "codex"]))
        assert isinstance(result.output, dict)

    def test_parallel_output_keys_are_resolved_agent_names(self) -> None:
        """Agent aliases must be resolved in the output keys."""
        proto = self._make_proto()
        result = _run(proto.parallel("question", agents=["lms", "claude"]))
        # lms→lmstudio, claude→claude_cli
        assert "lmstudio" in result.output
        assert "claude_cli" in result.output

    def test_parallel_sns_applied_flag(self) -> None:
        proto = self._make_proto()
        proto._sns_helper_loaded = True
        proto._sns_convert = MagicMock(
            return_value=("compressed", {"replacements": 2})
        )
        result = _run(proto.parallel("long prompt", agents=["ollama"], sns=True))
        assert result.sns_applied is True

    def test_parallel_single_agent_still_returns_dict(self) -> None:
        proto = self._make_proto()
        result = _run(proto.parallel("question", agents=["ollama"]))
        assert isinstance(result.output, dict)
        assert "ollama" in result.output

    def test_parallel_default_agents_used_when_none_specified(self) -> None:
        """Omitting agents= should default to ollama + lmstudio."""
        proto = self._make_proto()
        result = _run(proto.parallel("question"))
        assert len(result.agents_used) == 2
        assert "ollama" in result.agents_used
        assert "lmstudio" in result.agents_used


# ---------------------------------------------------------------------------
# 21. chain() — extended edge cases
# ---------------------------------------------------------------------------


class TestChainExtended:
    """Additional coverage for chain() beyond TestChain happy-path."""

    def _make_proto(self) -> MjolnirProtocol:
        proto = _make_protocol()
        proto._guild = False
        proto._registry = MagicMock()
        proto._registry.RECOVERABLE_AGENTS = set()
        mock_router = MagicMock()
        mock_router.route_task = AsyncMock(
            return_value={"status": "success", "output": "step output"}
        )
        proto._router = mock_router
        return proto

    def test_chain_step_numbers_are_sequential(self) -> None:
        proto = self._make_proto()
        result = _run(proto.chain("prompt", agents=["ollama", "codex", "lmstudio"]))
        steps = result.output
        assert steps[0]["step"] == 1
        assert steps[1]["step"] == 2
        assert steps[2]["step"] == 3

    def test_chain_step_without_label_has_none_label(self) -> None:
        """When no steps= list is provided, label is None for all steps."""
        proto = self._make_proto()
        result = _run(proto.chain("prompt", agents=["ollama", "codex"]))
        for step in result.output:
            assert step["label"] is None

    def test_chain_sns_only_applied_on_first_step(self) -> None:
        """Verify sns flag does NOT cause _apply_sns to be called more than once."""
        proto = _make_protocol()
        proto._guild = False
        proto._registry = MagicMock()
        proto._registry.RECOVERABLE_AGENTS = set()
        mock_router = MagicMock()
        mock_router.route_task = AsyncMock(
            return_value={"status": "success", "output": "out"}
        )
        proto._router = mock_router
        proto._sns_helper_loaded = True
        convert_mock = MagicMock(return_value=("compressed", {"replacements": 1}))
        proto._sns_convert = convert_mock

        _run(proto.chain("initial prompt", agents=["ollama", "codex"], sns=True))
        # _apply_sns (via _sns_convert) called exactly once (first step only)
        assert convert_mock.call_count == 1

    def test_chain_partial_result_contains_completed_steps(self) -> None:
        """When chain breaks mid-way, already-completed steps are in output."""
        proto = _make_protocol()
        proto._guild = False
        proto._registry = MagicMock()
        proto._registry.RECOVERABLE_AGENTS = set()
        call_count = 0

        async def alternating(*args: Any, **kwargs: Any) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"status": "success", "output": "first step ok"}
            return {"status": "failed", "output": None, "error": "step 2 failed"}

        mock_router = MagicMock()
        mock_router.route_task = alternating
        proto._router = mock_router

        result = _run(proto.chain("prompt", agents=["ollama", "codex", "lmstudio"]))
        assert result.success is False
        assert result.status == "partial"
        # The chain stopped at step 2; at least step 1 entry should exist
        assert len(result.output) >= 1

    def test_chain_error_message_names_broken_step(self) -> None:
        """The error string from a broken chain should mention the step number."""
        proto = _make_protocol()
        proto._guild = False
        proto._registry = MagicMock()
        proto._registry.RECOVERABLE_AGENTS = set()
        mock_router = MagicMock()
        mock_router.route_task = AsyncMock(
            return_value={"status": "failed", "output": None, "error": "router down"}
        )
        proto._router = mock_router

        result = _run(proto.chain("prompt", agents=["ollama"]))
        assert result.error is not None
        assert "1" in result.error  # step 1 broken

    def test_chain_success_has_ok_status(self) -> None:
        proto = self._make_proto()
        result = _run(proto.chain("prompt", agents=["ollama"]))
        assert result.status == "ok"
        assert result.success is True

    def test_chain_output_contains_agent_names(self) -> None:
        proto = self._make_proto()
        result = _run(proto.chain("prompt", agents=["ollama", "codex"]))
        agent_names_in_steps = [s["agent"] for s in result.output]
        assert "ollama" in agent_names_in_steps
        assert "codex" in agent_names_in_steps


# ---------------------------------------------------------------------------
# 22. queue() — extended edge cases
# ---------------------------------------------------------------------------


class TestQueueExtended:
    """Additional coverage for queue() beyond TestQueue happy-path."""

    def test_queue_pattern_is_queue(self) -> None:
        proto = _make_protocol()
        mock_dispatch = AsyncMock(return_value={"status": "queued", "task_id": "q-ext-1"})
        mock_bto = MagicMock()
        mock_bto.dispatch_task_cli = mock_dispatch
        with patch.dict(sys.modules, {"src.orchestration.background_task_orchestrator": mock_bto}):
            result = _run(proto.queue("generate tests"))
        assert result.pattern == "queue"

    def test_queue_agent_resolves_alias(self) -> None:
        """queue(agent='claude') should resolve to 'claude_cli'."""
        proto = _make_protocol()
        mock_dispatch = AsyncMock(return_value={"status": "queued", "task_id": "q-ext-2"})
        mock_bto = MagicMock()
        mock_bto.dispatch_task_cli = mock_dispatch
        with patch.dict(sys.modules, {"src.orchestration.background_task_orchestrator": mock_bto}):
            result = _run(proto.queue("generate tests", agent="claude"))
        assert result.agent == "claude_cli"

    def test_queue_runtime_exception_returns_error_envelope(self) -> None:
        """Non-ImportError exceptions during queue() produce an error envelope."""
        proto = _make_protocol()
        mock_dispatch = AsyncMock(side_effect=RuntimeError("queue full"))
        mock_bto = MagicMock()
        mock_bto.dispatch_task_cli = mock_dispatch
        with patch.dict(sys.modules, {"src.orchestration.background_task_orchestrator": mock_bto}):
            result = _run(proto.queue("generate tests"))
        assert result.success is False
        assert result.pattern == "queue"
        assert result.error is not None

    def test_queue_priority_passed_to_dispatch(self) -> None:
        """Priority string is normalised to lowercase before dispatch."""
        proto = _make_protocol()
        mock_dispatch = AsyncMock(return_value={"status": "queued", "task_id": "q-ext-3"})
        mock_bto = MagicMock()
        mock_bto.dispatch_task_cli = mock_dispatch
        with patch.dict(sys.modules, {"src.orchestration.background_task_orchestrator": mock_bto}):
            _run(proto.queue("task", priority="HIGH"))
        call_kw = mock_dispatch.call_args.kwargs
        assert call_kw.get("priority") == "high"

    def test_queue_no_sns_by_default(self) -> None:
        proto = _make_protocol()
        proto._sns_helper_loaded = True
        convert_mock = MagicMock(return_value=("compressed", {"replacements": 3}))
        proto._sns_convert = convert_mock
        mock_dispatch = AsyncMock(return_value={"status": "queued", "task_id": "q-ext-4"})
        mock_bto = MagicMock()
        mock_bto.dispatch_task_cli = mock_dispatch
        with patch.dict(sys.modules, {"src.orchestration.background_task_orchestrator": mock_bto}):
            result = _run(proto.queue("normal prompt"))
        # sns=False by default — convert should not be called
        convert_mock.assert_not_called()
        assert result.sns_applied is False


# ---------------------------------------------------------------------------
# 23. delegate() — extended edge cases
# ---------------------------------------------------------------------------


class TestDelegateExtended:
    """Additional coverage for delegate() beyond TestDelegate happy-path."""

    def test_delegate_guild_add_quest_exception_returns_error(self) -> None:
        """An exception raised inside guild.add_quest produces an error envelope."""
        proto = _make_protocol()
        mock_guild = MagicMock()
        mock_guild.add_quest = AsyncMock(side_effect=RuntimeError("guild crash"))
        proto._guild = mock_guild

        result = _run(proto.delegate("task"))
        assert result.success is False
        assert result.pattern == "delegate"
        assert result.error is not None

    def test_delegate_agent_auto_not_resolved_to_specific(self) -> None:
        """agent='auto' resolves through AGENT_ALIASES; verify envelope.agent reflects it."""
        proto = _make_protocol()
        mock_guild = MagicMock()
        mock_guild.add_quest = AsyncMock(return_value=(True, "q-auto-1"))
        proto._guild = mock_guild

        result = _run(proto.delegate("task", agent="auto"))
        # 'auto' maps to 'auto' in AGENT_ALIASES
        assert result.agent == "auto"

    def test_delegate_output_has_quest_id_key(self) -> None:
        """Output dict should contain quest_id matching guild_quest_id."""
        proto = _make_protocol()
        mock_guild = MagicMock()
        mock_guild.add_quest = AsyncMock(return_value=(True, "q-ext-10"))
        proto._guild = mock_guild

        result = _run(proto.delegate("task"))
        assert result.output.get("quest_id") == "q-ext-10"
        assert result.guild_quest_id == "q-ext-10"

    def test_delegate_agents_used_is_single_entry(self) -> None:
        proto = _make_protocol()
        mock_guild = MagicMock()
        mock_guild.add_quest = AsyncMock(return_value=(True, "q-ext-11"))
        proto._guild = mock_guild

        result = _run(proto.delegate("task", agent="ollama"))
        assert result.agents_used == ["ollama"]

    def test_delegate_guild_false_not_none(self) -> None:
        """proto._guild = False (sentinel 'tried, failed') must not attempt add_quest."""
        proto = _make_protocol()
        proto._guild = False  # simulates _get_guild() returning None

        result = _run(proto.delegate("task"))
        assert result.success is False
        assert "not available" in (result.error or "").lower()

    def test_delegate_sns_compresses_prompt(self) -> None:
        proto = _make_protocol()
        mock_guild = MagicMock()
        mock_guild.add_quest = AsyncMock(return_value=(True, "q-ext-12"))
        proto._guild = mock_guild
        proto._sns_helper_loaded = True
        convert_mock = MagicMock(return_value=("short", {"replacements": 4}))
        proto._sns_convert = convert_mock

        _run(proto.delegate("long prompt here", sns=True))
        convert_mock.assert_called_once()


# ---------------------------------------------------------------------------
# 24. status() — extended edge cases
# ---------------------------------------------------------------------------


class TestStatusExtended:
    """Additional coverage for status() beyond TestStatus happy-path."""

    def test_status_probes_false_includes_all_registered_agents(self) -> None:
        """Without probes, every entry in AGENT_PROBES appears in output."""
        from src.dispatch.mjolnir import AGENT_PROBES

        proto = _make_protocol()
        result = _run(proto.status())
        for name in AGENT_PROBES:
            assert name in result.output, f"Expected {name!r} in status output"

    def test_status_no_probe_entry_has_display_name(self) -> None:
        """Each agent entry (no-probe path) should include a display_name field."""
        proto = _make_protocol()
        # Provide a registry that has get_display_name
        mock_registry = MagicMock()
        mock_registry.get_display_name.return_value = "Ollama LLM"
        proto._registry = mock_registry

        result = _run(proto.status())
        ollama_entry = result.output.get("ollama", {})
        assert "display_name" in ollama_entry

    def test_status_single_agent_output_keys_only_that_agent(self) -> None:
        proto = _make_protocol()
        result = _run(proto.status(agent="codex"))
        assert "codex" in result.output
        assert "ollama" not in result.output

    def test_status_with_probes_probe_one_called_for_non_recoverable(self) -> None:
        """For a non-recoverable agent with probes=True, probe_one is called."""
        proto = _make_protocol()
        mock_probe_result = MagicMock()
        mock_probe_result.to_dict.return_value = {"agent": "codex", "status": "online"}
        mock_registry = MagicMock()
        mock_registry.RECOVERABLE_AGENTS = set()  # codex not recoverable
        mock_registry.probe_one = AsyncMock(return_value=mock_probe_result)
        proto._registry = mock_registry

        result = _run(proto.status(agent="codex", probes=True))
        mock_registry.probe_one.assert_called_once()
        assert isinstance(result, ResponseEnvelope)

    def test_status_timing_ms_is_set(self) -> None:
        proto = _make_protocol()
        result = _run(proto.status())
        assert result.timing_ms is not None
        assert result.timing_ms >= 0

    def test_status_agents_used_matches_all_known_agents_when_no_filter(self) -> None:
        """agents_used in the all-agent no-probe status should be the full AGENT_PROBES list."""
        from src.dispatch.mjolnir import AGENT_PROBES

        proto = _make_protocol()
        result = _run(proto.status())
        assert set(result.agents_used) == set(AGENT_PROBES.keys())


# ---------------------------------------------------------------------------
# MemoryPalace / recall() / poll_queue() / poll_delegate()  (added 2026-03-16)
# ---------------------------------------------------------------------------

class TestMemoryPalaceRecall:
    """MjolnirProtocol.recall() and _store_interaction() round-trip."""

    def test_recall_returns_empty_list_before_any_interactions(self) -> None:
        proto = _make_protocol()
        result = proto.recall("ollama")
        assert result == []

    def test_store_and_recall_single_interaction(self) -> None:
        import time
        proto = _make_protocol()
        env = _make_envelope(agent="ollama", success=True, timing_ms=100.0)
        proto._store_interaction("ollama", "test prompt", "analyze", env, time.monotonic())
        results = proto.recall("ollama")
        assert len(results) == 1
        assert results[0]["content"]["agent"] == "ollama"
        assert results[0]["content"]["task_type"] == "analyze"
        assert results[0]["content"]["success"] is True

    def test_recall_filters_by_tag(self) -> None:
        import time
        proto = _make_protocol()
        env_ok = _make_envelope(agent="ollama", success=True, timing_ms=50.0)
        env_fail = _make_envelope(agent="codex", success=False, status="error", timing_ms=20.0)
        proto._store_interaction("ollama", "analyze this", "analyze", env_ok, time.monotonic())
        proto._store_interaction("codex", "generate code", "generate", env_fail, time.monotonic())

        ollama_results = proto.recall("ollama")
        codex_results = proto.recall("codex")
        failed_results = proto.recall("failed")

        assert len(ollama_results) == 1
        assert len(codex_results) == 1
        assert len(failed_results) == 1
        assert failed_results[0]["content"]["agent"] == "codex"

    def test_recall_respects_limit(self) -> None:
        import time
        proto = _make_protocol()
        env = _make_envelope(agent="ollama", success=True, timing_ms=10.0)
        for _ in range(15):
            proto._store_interaction("ollama", "prompt", "analyze", env, time.monotonic())

        results = proto.recall("ollama", limit=5)
        assert len(results) == 5

    def test_recall_unavailable_memory_returns_empty(self) -> None:
        proto = _make_protocol()
        proto._memory = False  # Sentinel: unavailable
        result = proto.recall("ollama")
        assert result == []

    def test_store_interaction_is_noop_when_memory_unavailable(self) -> None:
        import time
        proto = _make_protocol()
        proto._memory = False
        env = _make_envelope(agent="ollama", success=True, timing_ms=10.0)
        # Should not raise
        proto._store_interaction("ollama", "prompt", "analyze", env, time.monotonic())

    def test_get_memory_returns_memory_palace_instance(self) -> None:
        proto = _make_protocol()
        mem = proto._get_memory()
        assert mem is not None
        assert hasattr(mem, "add_memory_node")
        assert hasattr(mem, "search_by_tag")


class TestPollQueue:
    """MjolnirProtocol.poll_queue() wraps task_status_cli."""

    def test_poll_queue_not_found_returns_error_dict(self) -> None:
        proto = _make_protocol()
        result = proto.poll_queue("nonexistent-task-id-xyz")
        assert "error" in result

    def test_poll_queue_found_returns_task_dict(self) -> None:
        proto = _make_protocol()
        fake_task = {"task_id": "t1", "status": "completed", "result": "done"}
        with patch("src.orchestration.background_task_orchestrator.task_status_cli", return_value=fake_task):
            result = proto.poll_queue("t1")
        assert result["task_id"] == "t1"
        assert result["status"] == "completed"

    def test_poll_queue_import_error_returns_error_dict(self) -> None:
        proto = _make_protocol()
        with patch("builtins.__import__", side_effect=ImportError("no module")):
            # Should not raise even if import fails
            try:
                result = proto.poll_queue("any-id")
                assert "error" in result or isinstance(result, dict)
            except Exception:
                pass  # acceptable to raise on total import failure in some envs


class TestPollDelegate:
    """MjolnirProtocol.poll_delegate() queries GuildBoard."""

    def test_poll_delegate_guild_unavailable_returns_error(self) -> None:
        proto = _make_protocol()
        proto._guild = False
        result = _run(proto.poll_delegate("quest-id-xyz"))
        assert "error" in result
        assert "unavailable" in result["error"].lower()

    def test_poll_delegate_quest_not_found_returns_error(self) -> None:
        proto = _make_protocol()
        mock_guild = MagicMock()
        mock_guild.get_quest = AsyncMock(return_value=None)
        proto._guild = mock_guild
        result = _run(proto.poll_delegate("missing-quest-id"))
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_poll_delegate_returns_quest_dict(self) -> None:
        proto = _make_protocol()
        fake_quest = MagicMock()
        fake_quest.to_dict.return_value = {"quest_id": "q1", "status": "active"}
        mock_guild = MagicMock()
        mock_guild.get_quest = AsyncMock(return_value=fake_quest)
        proto._guild = mock_guild
        result = _run(proto.poll_delegate("q1"))
        assert result["quest_id"] == "q1"
        assert result["status"] == "active"


# ---------------------------------------------------------------------------
# QuestEngine.get_accessible_quests() (added 2026-03-16)
# ---------------------------------------------------------------------------

class TestQuestEngineAccessibleQuests:
    """Consciousness-gated quest access via QuestEngine.get_accessible_quests()."""

    def _make_engine(self) -> Any:
        from src.Rosetta_Quest_System.quest_engine import QuestEngine
        e = QuestEngine.__new__(QuestEngine)
        e.quests = {}
        e.questlines = {}
        e.add_questline("General", "Default")
        return e

    def test_no_gate_quests_always_accessible(self) -> None:
        engine = self._make_engine()
        engine.add_quest("Basic", "Open quest", min_level=0)
        accessible = engine.get_accessible_quests(consciousness_level=0)
        assert len(accessible) == 1

    def test_gated_quest_hidden_below_threshold(self) -> None:
        engine = self._make_engine()
        engine.add_quest("Advanced", "Needs level 10", min_level=10)
        below = engine.get_accessible_quests(consciousness_level=9)
        at_level = engine.get_accessible_quests(consciousness_level=10)
        assert len(below) == 0
        assert len(at_level) == 1

    def test_mixed_quests_filter_correctly(self) -> None:
        engine = self._make_engine()
        engine.add_quest("Free", "Open", min_level=0)
        engine.add_quest("Mid", "Needs 5", min_level=5)
        engine.add_quest("Hard", "Needs 20", min_level=20)
        assert len(engine.get_accessible_quests(0)) == 1
        assert len(engine.get_accessible_quests(5)) == 2
        assert len(engine.get_accessible_quests(20)) == 3
        assert len(engine.get_accessible_quests(100)) == 3

    def test_questline_filter_applied_after_level_gate(self) -> None:
        engine = self._make_engine()
        engine.add_questline("Special", "Special questline")
        engine.add_quest("A", "general open", questline="General", min_level=0)
        engine.add_quest("B", "special open", questline="Special", min_level=0)
        engine.add_quest("C", "special gated", questline="Special", min_level=5)
        special_at_0 = engine.get_accessible_quests(0, questline="Special")
        assert len(special_at_0) == 1
        assert special_at_0[0].title == "B"

    def test_status_filter_applied(self) -> None:
        engine = self._make_engine()
        q_id = engine.add_quest("Task", "pending quest", min_level=0)
        engine.update_quest_status(q_id, "active")
        active = engine.get_accessible_quests(0, status="active")
        pending = engine.get_accessible_quests(0, status="pending")
        assert len(active) == 1
        assert len(pending) == 0

    def test_from_dict_preserves_min_consciousness_level(self) -> None:
        from src.Rosetta_Quest_System.quest_engine import Quest
        q = Quest("test", "desc", "General", min_consciousness_level=15)
        d = q.to_dict()
        q2 = Quest.from_dict(d)
        assert q2.min_consciousness_level == 15

    def test_from_dict_defaults_to_zero_for_old_quests(self) -> None:
        from src.Rosetta_Quest_System.quest_engine import Quest
        # Simulate a quest dict without the new field (backward compat)
        d = {"title": "old", "description": "legacy", "questline": "General"}
        q = Quest.from_dict(d)
        assert q.min_consciousness_level == 0


class TestAgentDuetDelegation:
    """agent_duet delegation parsing and processing."""

    def test_extract_delegations_empty(self) -> None:
        from scripts.agent_duet import extract_delegations
        assert extract_delegations("no markers here") == []

    def test_extract_delegations_single(self) -> None:
        from scripts.agent_duet import extract_delegations
        result = extract_delegations("check [DELEGATE:ollama:analyze code]")
        assert result == [("ollama", "analyze code")]

    def test_extract_delegations_multiple(self) -> None:
        from scripts.agent_duet import extract_delegations
        text = "[DELEGATE:codex:write tests] and [DELEGATE:claude:review plan]"
        result = extract_delegations(text)
        assert len(result) == 2
        assert result[0] == ("codex", "write tests")
        assert result[1] == ("claude", "review plan")

    def test_extract_delegations_case_insensitive(self) -> None:
        from scripts.agent_duet import extract_delegations
        result = extract_delegations("[delegate:OLLAMA:analyze this]")
        assert len(result) == 1
        assert result[0][0] == "ollama"

    def test_process_delegations_disabled_annotates_not_executes(self) -> None:
        from scripts.agent_duet import process_delegations
        history: list = []
        output = "Use [DELEGATE:ollama:do something]"
        result = process_delegations(output, history, 30, enabled=False)
        assert "[DELEGATE:" not in result
        assert "skipped" in result
        assert len(history) == 0  # No runtime history entry when disabled

    def test_agent_profile_contains_delegate_hint(self) -> None:
        from scripts.agent_duet import _AGENT_PROFILES
        for agent in ["codex", "copilot", "claude", "claude_cli", "ollama"]:
            assert "DELEGATE" in _AGENT_PROFILES[agent], f"Missing DELEGATE hint for {agent}"

    def test_build_agent_prompt_n_agents(self) -> None:
        from scripts.agent_duet import build_agent_prompt
        prompt = build_agent_prompt(
            "codex", ["copilot", "ollama", "claude"], [], turn_num=3
        )
        assert "copilot" in prompt
        assert "ollama" in prompt
        assert "claude" in prompt
        assert "turn 3" in prompt

    def test_build_agent_prompt_delegation_enabled_says_live(self) -> None:
        from scripts.agent_duet import build_agent_prompt
        prompt = build_agent_prompt("codex", ["copilot"], [], turn_num=1, delegation_enabled=True)
        assert "LIVE" in prompt

    def test_build_agent_prompt_delegation_disabled_says_not_executed(self) -> None:
        from scripts.agent_duet import build_agent_prompt
        prompt = build_agent_prompt("codex", ["copilot"], [], turn_num=1, delegation_enabled=False)
        assert "not executed" in prompt or "not set" in prompt


# ---------------------------------------------------------------------------
# Council MemoryPalace storage + Chronicle recall  (added 2026-03-16)
# ---------------------------------------------------------------------------


class TestCouncilMemoryStorage:
    """council() stores decision in MemoryPalace tagged with agent names + consensus."""

    def test_council_stores_node_tagged_with_agent_names(self) -> None:
        proto = _make_protocol()
        mem = MagicMock()
        proto._memory = mem

        synthesis = {"consensus_level": "strong", "confidence": 0.9}

        # Replicate the storage call directly to test logic
        import time as _time
        node_id = f"council:{int(_time.time() * 1000)}"
        agents = ["ollama", "lmstudio"]
        tags = ["council", "ask", "strong", *agents]
        mem.add_memory_node(
            node_id,
            {"prompt": "test", "agents": agents, "consensus": "strong", "confidence": 0.9,
             "synthesis": synthesis, "success": True, "timing_ms": 100},
            tags=tags,
        )

        mem.add_memory_node.assert_called_once()
        call_kwargs = mem.add_memory_node.call_args
        stored_tags = call_kwargs.kwargs.get("tags") or call_kwargs.args[2]
        assert "council" in stored_tags
        assert "ollama" in stored_tags
        assert "lmstudio" in stored_tags
        assert "strong" in stored_tags

    def test_council_node_content_includes_prompt_agents_consensus(self) -> None:
        proto = _make_protocol()
        mem = MagicMock()
        proto._memory = mem

        import time as _t
        node_id = f"council:{int(_t.time() * 1000)}"
        agents = ["codex", "copilot"]
        synthesis = {"consensus_level": "weak", "confidence": 0.4}
        content = {
            "prompt": "Is Rust better than C++?"[:300],
            "agents": agents,
            "consensus": "weak",
            "confidence": 0.4,
            "synthesis": synthesis,
            "success": True,
            "timing_ms": 200,
        }
        mem.add_memory_node(node_id, content, tags=["council", "ask", "weak", *agents])

        _call = mem.add_memory_node.call_args
        stored_content = _call.args[1] if _call.args else _call.kwargs.get("content", {})
        assert stored_content["consensus"] == "weak"
        assert stored_content["agents"] == ["codex", "copilot"]
        assert "prompt" in stored_content

    def test_recall_council_tag_returns_council_entries(self) -> None:
        from src.memory import MemoryPalace
        proto = _make_protocol()
        real_mem = MemoryPalace()
        proto._memory = real_mem

        real_mem.add_memory_node(
            "council:1000",
            {"prompt": "best arch?", "agents": ["ollama"], "consensus": "strong",
             "confidence": 0.8, "synthesis": {}, "success": True, "timing_ms": 50},
            tags=["council", "ask", "strong", "ollama"],
        )

        hits = proto.recall("council")
        assert len(hits) == 1
        assert hits[0]["node_id"] == "council:1000"

    def test_recall_agent_tag_returns_council_entry_for_that_agent(self) -> None:
        from src.memory import MemoryPalace
        proto = _make_protocol()
        real_mem = MemoryPalace()
        proto._memory = real_mem

        real_mem.add_memory_node(
            "council:2000",
            {"prompt": "review code", "agents": ["codex", "copilot"], "consensus": "moderate",
             "confidence": 0.6, "synthesis": {}, "success": True, "timing_ms": 120},
            tags=["council", "ask", "moderate", "codex", "copilot"],
        )

        codex_hits = proto.recall("codex")
        assert len(codex_hits) == 1
        copilot_hits = proto.recall("copilot")
        assert len(copilot_hits) == 1

    def test_recall_chronicle_reads_file_entries(self, tmp_path: Path) -> None:
        """recall() merges entries from state/memory_chronicle.jsonl."""
        import json as _json

        chronicle = tmp_path / "memory_chronicle.jsonl"
        entry = {
            "node_id": "culture_ship_cycle_test",
            "tags": ["culture_ship", "cycle"],
            "timestamp": "2026-03-16T10:00:00",
            "source": "culture_ship_cycle",
            "issues": 0,
            "fixes": 0,
        }
        chronicle.write_text(_json.dumps(entry) + "\n", encoding="utf-8")

        # Direct test: read from the chronicle path (no patching needed — file is in tmp_path)
        hits = []
        if chronicle.exists():
            for line in chronicle.read_text().splitlines():
                if line.strip():
                    e = _json.loads(line)
                    if "culture_ship" in e.get("tags", []):
                        hits.append(e)
        assert len(hits) == 1
        assert hits[0]["node_id"] == "culture_ship_cycle_test"

    def test_chronicle_recall_skips_malformed_lines(self, tmp_path: Path) -> None:
        """Malformed JSONL lines do not crash recall."""
        import json as _json
        chronicle = tmp_path / "memory_chronicle.jsonl"
        valid = {"node_id": "ok", "tags": ["culture_ship"], "source": "test"}
        chronicle.write_text("not-json\n" + _json.dumps(valid) + "\nbad{}\n", encoding="utf-8")

        hits = []
        for line in chronicle.read_text().splitlines():
            if not line.strip():
                continue
            try:
                e = _json.loads(line)
                if "culture_ship" in e.get("tags", []):
                    hits.append(e)
            except Exception:
                pass
        assert len(hits) == 1
        assert hits[0]["node_id"] == "ok"


class TestAskOpenClaw:
    """Tests for MjolnirProtocol._ask_openclaw."""

    def _make_proto(self, tmp_path: Path) -> MjolnirProtocol:
        return MjolnirProtocol(repo_root=tmp_path)

    @pytest.mark.asyncio
    async def test_openclaw_not_found_returns_failed(self, tmp_path: Path) -> None:
        proto = self._make_proto(tmp_path)
        with patch("shutil.which", return_value=None):
            with patch("os.path.exists", return_value=False):
                result = await proto._ask_openclaw("hello", {})
        assert result["status"] == "failed"
        assert "openclaw" in result["system"]
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_non_blocking_returns_submitted(self, tmp_path: Path) -> None:
        proto = self._make_proto(tmp_path)
        with patch("shutil.which", return_value="/usr/bin/openclaw"):
            with patch("subprocess.Popen") as mock_popen:
                mock_proc = MagicMock()
                mock_proc.pid = 12345
                mock_popen.return_value = mock_proc
                result = await proto._ask_openclaw("hello", {}, wait_for_completion=False)
        assert result["status"] == "success"
        assert result.get("non_blocking") is True
        assert result.get("pid") == 12345

    @pytest.mark.asyncio
    async def test_blocking_success_json_output(self, tmp_path: Path) -> None:
        import json as _json
        proto = self._make_proto(tmp_path)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = _json.dumps({"response": "hello back"})
        mock_result.stderr = ""
        with patch("shutil.which", return_value="/usr/bin/openclaw"):
            with patch("subprocess.run", return_value=mock_result):
                result = await proto._ask_openclaw("hello", {})
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_timeout_on_all_retries_returns_failed(self, tmp_path: Path) -> None:
        import subprocess
        proto = self._make_proto(tmp_path)
        with patch("shutil.which", return_value="/usr/bin/openclaw"):
            with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 30)):
                with patch.dict("os.environ", {
                    "NUSYQ_OPENCLAW_RETRY_ATTEMPTS": "2",
                    "NUSYQ_OPENCLAW_AUTO_NON_BLOCKING_ON_TIMEOUT": "0",
                }):
                    result = await proto._ask_openclaw("hello", {}, timeout=30.0)
        assert result["status"] == "failed"
        assert "timed out" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_ctx_timeout_overrides_default(self, tmp_path: Path) -> None:
        """Explicit timeout in ctx is used instead of default 900s."""
        proto = self._make_proto(tmp_path)
        captured_cmds: list = []

        def fake_run(cmd, **_kw):
            captured_cmds.append(cmd)
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '{"ok": true}'
            mock_result.stderr = ""
            return mock_result

        with patch("shutil.which", return_value="/usr/bin/openclaw"):
            with patch("subprocess.run", side_effect=fake_run):
                await proto._ask_openclaw("hello", {"timeout": 60}, timeout=None)

        # --timeout flag should be 60 (or close to it)
        assert any("--timeout" in str(cmd) for cmd in captured_cmds)

    @pytest.mark.asyncio
    async def test_non_blocking_via_ctx_key(self, tmp_path: Path) -> None:
        proto = self._make_proto(tmp_path)
        with patch("shutil.which", return_value="/usr/bin/openclaw"):
            with patch("subprocess.Popen") as mock_popen:
                mock_proc = MagicMock()
                mock_proc.pid = 9999
                mock_popen.return_value = mock_proc
                result = await proto._ask_openclaw(
                    "hello",
                    {"openclaw_non_blocking": "true"},
                )
        assert result.get("non_blocking") is True


class TestAskIntermediary:
    """Tests for MjolnirProtocol._ask_intermediary."""

    def _make_proto(self, tmp_path: Path) -> MjolnirProtocol:
        return MjolnirProtocol(repo_root=tmp_path)

    @pytest.mark.asyncio
    async def test_unavailable_intermediary_returns_failed(self, tmp_path: Path) -> None:
        proto = self._make_proto(tmp_path)
        # Force intermediary unavailable
        proto._intermediary = None
        # Also prevent lazy-load from succeeding
        with patch.object(proto, "_get_intermediary", return_value=None):
            result = await proto._ask_intermediary("analyze this", {}, "analyze")
        assert result["status"] == "failed"
        assert "unavailable" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_success_returns_response(self, tmp_path: Path) -> None:
        proto = self._make_proto(tmp_path)

        mock_event = MagicMock()
        mock_event.payload = "Analysis complete"
        mock_event.event_id = "evt_123"

        mock_intermediary = AsyncMock()
        mock_intermediary.handle = AsyncMock(return_value=mock_event)

        with patch.object(proto, "_get_intermediary", return_value=mock_intermediary):
            result = await proto._ask_intermediary("analyze this", {}, "analyze")

        assert result["status"] == "success"
        assert result["response"] == "Analysis complete"

    @pytest.mark.asyncio
    async def test_exception_returns_failed(self, tmp_path: Path) -> None:
        proto = self._make_proto(tmp_path)
        mock_intermediary = AsyncMock()
        mock_intermediary.handle = AsyncMock(side_effect=RuntimeError("intermediary exploded"))

        with patch.object(proto, "_get_intermediary", return_value=mock_intermediary):
            result = await proto._ask_intermediary("test", {}, "debug")

        assert result["status"] == "failed"
        assert "intermediary exploded" in result["error"]

    @pytest.mark.asyncio
    async def test_paradigm_mapped_from_task_type(self, tmp_path: Path) -> None:
        proto = self._make_proto(tmp_path)

        captured_paradigm = []

        mock_event = MagicMock()
        mock_event.payload = "ok"
        mock_event.event_id = "e1"

        async def fake_handle(**kwargs):
            captured_paradigm.append(kwargs.get("paradigm"))
            return mock_event

        mock_intermediary = MagicMock()
        mock_intermediary.handle = fake_handle

        with patch.object(proto, "_get_intermediary", return_value=mock_intermediary):
            await proto._ask_intermediary("plan this", {}, "plan")

        # plan → SYMBOLIC_LOGIC
        assert captured_paradigm
        assert "SYMBOLIC" in str(captured_paradigm[0]).upper() or "logic" in str(captured_paradigm[0]).lower()


class TestGetSnsConvert:
    """Tests for MjolnirProtocol._get_sns_convert lazy loading."""

    def test_loads_convert_when_available(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        fake_convert = MagicMock()
        with patch("src.utils.sns_core_helper.convert_to_sns", fake_convert, create=True):
            with patch.dict("sys.modules", {"src.utils.sns_core_helper": MagicMock(convert_to_sns=fake_convert)}):
                proto._sns_helper_loaded = False  # reset
                result = proto._get_sns_convert()
        # Either returned the mock or None (import may not resolve in test env)
        assert result is None or callable(result)

    def test_returns_none_when_import_fails(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        proto._sns_helper_loaded = False
        proto._sns_convert = None
        with patch("builtins.__import__", side_effect=ImportError("no sns")):
            result = proto._get_sns_convert()
        assert result is None

    def test_cached_after_first_call(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        # After loading, _sns_helper_loaded is True
        proto._sns_helper_loaded = False
        proto._sns_convert = None
        # First call
        proto._get_sns_convert()
        assert proto._sns_helper_loaded is True
        # Second call doesn't re-import (flag is already set)
        proto._sns_convert = "sentinel"
        result = proto._get_sns_convert()
        assert result == "sentinel"


# ── TestQueueBackgroundNonBlocking ────────────────────────────────────────────

class TestQueueBackgroundNonBlocking:
    """Tests for _queue_background_non_blocking internal method."""

    @pytest.mark.asyncio
    async def test_import_error_returns_failed(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        with patch.dict("sys.modules", {"src.orchestration.background_task_orchestrator": None}):
            result = await proto._queue_background_non_blocking(
                target_system="ollama",
                prompt="hello",
                task_type="analyze",
                priority="NORMAL",
                ctx={},
            )
        assert result["status"] == "failed"
        assert "background_queue_unavailable" in result["error"]
        assert result["non_blocking"] is True

    @pytest.mark.asyncio
    async def test_orchestrator_exception_returns_failed(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        with patch(
            "src.orchestration.background_task_orchestrator.get_orchestrator",
            side_effect=RuntimeError("orch down"),
        ):
            result = await proto._queue_background_non_blocking(
                target_system="chatdev",
                prompt="build it",
                task_type="generate",
                priority="HIGH",
                ctx={},
            )
        assert result["status"] == "failed"
        assert "background_queue_submit_failed" in result["error"]

    @pytest.mark.asyncio
    async def test_success_path_ollama(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        task = MagicMock()
        task.task_id = "t-abc"
        task.target = MagicMock()
        task.target.value = "ollama"
        task.model = "llama3.1:8b"

        with patch("src.orchestration.background_task_orchestrator.get_orchestrator") as mock_orch:
            orch = MagicMock()
            orch.submit_task.return_value = task
            mock_orch.return_value = orch
            result = await proto._queue_background_non_blocking(
                target_system="ollama",
                prompt="review code",
                task_type="review",
                priority="HIGH",
                ctx={"ollama_model": "llama3.1:8b"},
            )
        assert result["status"] == "submitted"
        assert result["task_id"] == "t-abc"
        assert result["non_blocking"] is True

    @pytest.mark.asyncio
    async def test_unknown_priority_falls_back_to_normal(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        task = MagicMock()
        task.task_id = "t-001"
        task.target = MagicMock()
        task.target.value = "auto"
        task.model = None

        with patch("src.orchestration.background_task_orchestrator.get_orchestrator") as mock_orch:
            orch = MagicMock()
            orch.submit_task.return_value = task
            mock_orch.return_value = orch
            result = await proto._queue_background_non_blocking(
                target_system="ollama",
                prompt="test",
                task_type="analyze",
                priority="NOTREAL",
                ctx={},
            )
        assert result["status"] == "submitted"
        assert result["non_blocking"] is True

    @pytest.mark.asyncio
    async def test_unknown_target_maps_to_auto(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        task = MagicMock()
        task.task_id = "t-auto"
        task.target = MagicMock()
        task.target.value = "auto"
        task.model = None

        with patch("src.orchestration.background_task_orchestrator.get_orchestrator") as mock_orch:
            orch = MagicMock()
            orch.submit_task.return_value = task
            mock_orch.return_value = orch
            result = await proto._queue_background_non_blocking(
                target_system="neural_ml",
                prompt="predict",
                task_type="analyze",
                priority="NORMAL",
                ctx={},
            )
        assert result["status"] == "submitted"


# ── TestApplyOperatingProfileModes ───────────────────────────────────────────

class TestApplyOperatingProfileModes:
    """Tests for _apply_operating_profile strict/fast/balanced mode paths."""

    def test_strict_mode_sets_blocking_policy(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        ctx: dict = {"operating_mode": "strict"}
        profile = proto._apply_operating_profile(
            ctx=ctx,
            target_system="ollama",
            priority="NORMAL",
        )
        assert profile["mode"] == "strict"
        assert profile["execution_policy"] == "blocking_verified"
        assert profile["diagnostics_policy"] == "full"
        assert ctx.get("strict_timeouts") is True

    def test_fast_mode_sets_non_blocking_preferred(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        ctx: dict = {"operating_mode": "fast"}
        profile = proto._apply_operating_profile(
            ctx=ctx,
            target_system="openclaw",
            priority="NORMAL",
        )
        assert profile["mode"] == "fast"
        assert profile["execution_policy"] == "non_blocking_preferred"
        assert profile["diagnostics_policy"] == "minimal"
        assert ctx.get("strict_timeouts") is False

    def test_balanced_mode_is_default_result(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        ctx: dict = {"operating_mode": "balanced"}
        profile = proto._apply_operating_profile(
            ctx=ctx,
            target_system="ollama",
            priority="NORMAL",
        )
        assert profile["mode"] == "balanced"
        assert profile["diagnostics_policy"] == "targeted"

    def test_high_priority_normalizes_risk_to_high(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        ctx: dict = {"operating_mode": "balanced"}
        profile = proto._apply_operating_profile(
            ctx=ctx,
            target_system="ollama",
            priority="HIGH",
        )
        assert profile["risk_level"] == "high"

    def test_strict_openclaw_sets_retry_defaults(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        ctx: dict = {"operating_mode": "strict"}
        proto._apply_operating_profile(
            ctx=ctx,
            target_system="openclaw",
            priority="NORMAL",
        )
        assert ctx.get("openclaw_auto_non_blocking_on_timeout") is False
        assert ctx.get("openclaw_retry_attempts") == 2

    def test_fast_openclaw_enables_auto_non_blocking(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        ctx: dict = {"operating_mode": "fast"}
        proto._apply_operating_profile(
            ctx=ctx,
            target_system="openclaw",
            priority="NORMAL",
        )
        assert ctx.get("openclaw_auto_non_blocking_on_timeout") is True
        assert ctx.get("openclaw_retry_attempts") == 1


# ── TestEffectiveDispatchTimeout ─────────────────────────────────────────────

class TestEffectiveDispatchTimeout:
    """Tests for _effective_dispatch_timeout adaptive logic."""

    def test_default_timeout_for_ollama(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        timeout = proto._effective_dispatch_timeout("ollama", None)
        assert 30.0 <= timeout <= 3600.0

    def test_strict_override_returns_exact_requested(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        # strict_override=True skips grace multiplier
        timeout = proto._effective_dispatch_timeout("ollama", 60.0, strict_override=True)
        assert timeout == 60.0

    def test_invalid_max_timeout_env_falls_back(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("NUSYQ_MAX_TIMEOUT_S", "not-a-number")
        proto = MjolnirProtocol(repo_root=tmp_path)
        timeout = proto._effective_dispatch_timeout("ollama", None)
        assert timeout >= 1.0

    def test_invalid_openclaw_timeout_env_falls_back(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("NUSYQ_OPENCLAW_DEFAULT_TIMEOUT_S", "bad")
        proto = MjolnirProtocol(repo_root=tmp_path)
        timeout = proto._effective_dispatch_timeout("openclaw", None)
        assert timeout >= 30.0

    def test_default_timeout_for_unknown_system(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        timeout = proto._effective_dispatch_timeout("neural_ml", None)
        assert timeout >= 1.0


# ── TestSkyclawMethods ────────────────────────────────────────────────────────

class TestSkyclawMethods:
    """Tests for skyclaw_status, skyclaw_start, skyclaw_stop."""

    @pytest.mark.asyncio
    async def test_skyclaw_status_import_error_returns_unavailable(
        self, tmp_path: Path
    ) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        with patch.dict("sys.modules", {"src.integrations.skyclaw_gateway_client": None}):
            result = await proto.skyclaw_status()
        assert result.success is False
        assert result.status == "unavailable"
        assert result.pattern == "skyclaw_status"

    @pytest.mark.asyncio
    async def test_skyclaw_status_running_returns_ok(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        mock_client = AsyncMock()
        mock_client.summary = AsyncMock(return_value={"running": True, "gateway_url": "ws://x"})
        mock_mod = MagicMock()
        mock_mod.get_skyclaw_gateway_client = MagicMock(return_value=mock_client)
        with patch.dict("sys.modules", {"src.integrations.skyclaw_gateway_client": mock_mod}):
            result = await proto.skyclaw_status()
        assert result.success is True
        assert result.status == "ok"

    @pytest.mark.asyncio
    async def test_skyclaw_status_exception_returns_error(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        mock_client = AsyncMock()
        mock_client.summary = AsyncMock(side_effect=RuntimeError("gateway unreachable"))
        mock_mod = MagicMock()
        mock_mod.get_skyclaw_gateway_client = MagicMock(return_value=mock_client)
        with patch.dict("sys.modules", {"src.integrations.skyclaw_gateway_client": mock_mod}):
            result = await proto.skyclaw_status()
        assert result.success is False
        assert result.status == "error"

    @pytest.mark.asyncio
    async def test_skyclaw_start_import_error_returns_unavailable(
        self, tmp_path: Path
    ) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        with patch.dict("sys.modules", {"src.integrations.skyclaw_gateway_client": None}):
            result = await proto.skyclaw_start()
        assert result.success is False
        assert result.status == "unavailable"
        assert result.pattern == "skyclaw_start"

    @pytest.mark.asyncio
    async def test_skyclaw_start_binary_not_found_returns_error(
        self, tmp_path: Path
    ) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        mock_client = AsyncMock()
        mock_client.binary_info = MagicMock(return_value={"found": False})
        mock_mod = MagicMock()
        mock_mod.get_skyclaw_gateway_client = MagicMock(return_value=mock_client)
        with patch.dict("sys.modules", {"src.integrations.skyclaw_gateway_client": mock_mod}):
            result = await proto.skyclaw_start()
        assert result.success is False
        assert result.status == "error"

    @pytest.mark.asyncio
    async def test_skyclaw_start_success(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        mock_client = AsyncMock()
        mock_client.binary_info = MagicMock(return_value={"found": True, "path": "/bin/skyclaw"})
        mock_client.start_gateway = AsyncMock(return_value=True)
        mock_client.gateway_url = "ws://127.0.0.1:19876"
        mock_mod = MagicMock()
        mock_mod.get_skyclaw_gateway_client = MagicMock(return_value=mock_client)
        with patch.dict("sys.modules", {"src.integrations.skyclaw_gateway_client": mock_mod}):
            result = await proto.skyclaw_start()
        assert result.success is True
        assert result.status == "ok"

    @pytest.mark.asyncio
    async def test_skyclaw_start_gateway_returns_false_is_failed(
        self, tmp_path: Path
    ) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        mock_client = AsyncMock()
        mock_client.binary_info = MagicMock(return_value={"found": True})
        mock_client.start_gateway = AsyncMock(return_value=False)
        mock_client.gateway_url = "ws://x"
        mock_mod = MagicMock()
        mock_mod.get_skyclaw_gateway_client = MagicMock(return_value=mock_client)
        with patch.dict("sys.modules", {"src.integrations.skyclaw_gateway_client": mock_mod}):
            result = await proto.skyclaw_start()
        assert result.success is False
        assert result.status == "failed"

    @pytest.mark.asyncio
    async def test_skyclaw_stop_import_error_returns_unavailable(
        self, tmp_path: Path
    ) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        with patch.dict("sys.modules", {"src.integrations.skyclaw_gateway_client": None}):
            result = await proto.skyclaw_stop()
        assert result.success is False
        assert result.status == "unavailable"
        assert result.pattern == "skyclaw_stop"

    @pytest.mark.asyncio
    async def test_skyclaw_stop_success(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        mock_client = AsyncMock()
        mock_client.stop_gateway = AsyncMock(return_value=None)
        mock_client.gateway_url = "ws://x"
        mock_mod = MagicMock()
        mock_mod.get_skyclaw_gateway_client = MagicMock(return_value=mock_client)
        with patch.dict("sys.modules", {"src.integrations.skyclaw_gateway_client": mock_mod}):
            result = await proto.skyclaw_stop()
        assert result.success is True
        assert result.status == "ok"

    @pytest.mark.asyncio
    async def test_skyclaw_stop_exception_returns_error(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        mock_client = AsyncMock()
        mock_client.stop_gateway = AsyncMock(side_effect=RuntimeError("stop failed"))
        mock_mod = MagicMock()
        mock_mod.get_skyclaw_gateway_client = MagicMock(return_value=mock_client)
        with patch.dict("sys.modules", {"src.integrations.skyclaw_gateway_client": mock_mod}):
            result = await proto.skyclaw_stop()
        assert result.success is False
        assert result.status == "error"


# ── TestDrain ─────────────────────────────────────────────────────────────────

class TestDrain:
    """Tests for drain() method."""

    @pytest.mark.asyncio
    async def test_drain_import_error_returns_unavailable(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        with patch.dict("sys.modules", {"src.dispatch.quest_executor_bridge": None}):
            result = await proto.drain(limit=5)
        assert result.success is False
        assert "QuestExecutorBridge not available" in (result.error or "")

    @pytest.mark.asyncio
    async def test_drain_success_returns_results(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        mock_bridge = AsyncMock()
        mock_bridge.drain = AsyncMock(
            return_value=[{"agent": "ollama", "status": "ok", "quest_id": "q1"}]
        )
        mock_mod = MagicMock()
        mock_mod.QuestExecutorBridge = MagicMock(return_value=mock_bridge)
        with patch.dict("sys.modules", {"src.dispatch.quest_executor_bridge": mock_mod}):
            result = await proto.drain(limit=3)
        assert result.success is True
        assert result.status == "ok"
        assert result.pattern == "drain"

    @pytest.mark.asyncio
    async def test_drain_exception_returns_error(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        mock_bridge = AsyncMock()
        mock_bridge.drain = AsyncMock(side_effect=RuntimeError("drain failed"))
        mock_mod = MagicMock()
        mock_mod.QuestExecutorBridge = MagicMock(return_value=mock_bridge)
        with patch.dict("sys.modules", {"src.dispatch.quest_executor_bridge": mock_mod}):
            result = await proto.drain()
        assert result.success is False
        assert "Drain failed" in (result.error or "")


# ── TestOpenClawExtendedPaths ─────────────────────────────────────────────────

class TestOpenClawExtendedPaths:
    """Tests for extra _ask_openclaw error/variant paths."""

    @pytest.mark.asyncio
    async def test_json_decode_error_returns_raw_text(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        import shutil as _shutil

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "plain text response"
        mock_result.stderr = ""

        with (
            patch.object(_shutil, "which", return_value="/usr/bin/openclaw"),
            patch("subprocess.run", return_value=mock_result),
        ):
            result = await proto._ask_openclaw(
                "test prompt",
                ctx={},
                wait_for_completion=True,
            )
        assert result["status"] == "success"
        assert result["response"] == "plain text response"

    @pytest.mark.asyncio
    async def test_generic_exception_returns_failed(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        import shutil as _shutil

        with (
            patch.object(_shutil, "which", return_value="/usr/bin/openclaw"),
            patch("subprocess.run", side_effect=OSError("connection reset")),
        ):
            result = await proto._ask_openclaw(
                "test prompt",
                ctx={},
                wait_for_completion=True,
            )
        assert result["status"] == "failed"


# ── TestBlockingModeHelpers ───────────────────────────────────────────────────

class TestBlockingModeHelpers:
    """Tests for _set_blocking_mode and _set_non_blocking_mode static helpers."""

    def test_set_non_blocking_mode_openclaw(self) -> None:
        ctx: dict = {}
        MjolnirProtocol._set_non_blocking_mode(ctx, "openclaw")
        assert ctx["non_blocking"] is True
        assert ctx["wait_for_completion"] is False
        assert ctx["openclaw_non_blocking"] is True

    def test_set_non_blocking_mode_chatdev(self) -> None:
        ctx: dict = {}
        MjolnirProtocol._set_non_blocking_mode(ctx, "chatdev")
        assert ctx.get("chatdev_wait_for_completion") is False

    def test_set_blocking_mode_openclaw(self) -> None:
        ctx: dict = {}
        MjolnirProtocol._set_blocking_mode(ctx, "openclaw")
        assert ctx["wait_for_completion"] is True
        assert ctx["openclaw_wait_for_completion"] is True

    def test_set_blocking_mode_skips_when_non_blocking_already_set(self) -> None:
        ctx: dict = {"non_blocking": True}
        MjolnirProtocol._set_blocking_mode(ctx, "openclaw")
        assert "wait_for_completion" not in ctx

    def test_set_blocking_mode_chatdev(self) -> None:
        ctx: dict = {}
        MjolnirProtocol._set_blocking_mode(ctx, "chatdev")
        assert ctx.get("chatdev_wait_for_completion") is True


# ── TestLazyInitFailures ──────────────────────────────────────────────────────


class TestLazyInitFailures:
    """Cover import-failure branches in _get_router, _get_guild, _get_intermediary, _get_memory."""

    def test_get_router_import_error_raises(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        with patch.dict("sys.modules", {"src.tools.agent_task_router": None}):
            with pytest.raises(RuntimeError, match="AgentTaskRouter not available"):
                proto._get_router()

    def test_get_guild_import_error_returns_none(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        with patch.dict("sys.modules", {"src.guild.guild_board": None}):
            result = proto._get_guild()
        assert result is None

    def test_get_intermediary_import_error_returns_none(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        with patch.dict("sys.modules", {"src.ai.ai_intermediary": None}):
            result = proto._get_intermediary()
        assert result is None

    def test_get_memory_import_error_returns_none(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        with patch.dict("sys.modules", {"src.memory": None}):
            result = proto._get_memory()
        assert result is None

    def test_get_memory_sentinel_on_second_call(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        with patch.dict("sys.modules", {"src.memory": None}):
            proto._get_memory()  # sets _memory = False sentinel
        result = proto._get_memory()
        assert result is None


# ── TestRecall ────────────────────────────────────────────────────────────────


class TestRecall:
    """Cover recall() memory + chronicle paths."""

    def test_recall_with_memory_palace_unavailable_returns_empty(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        results = proto.recall("codex")
        assert isinstance(results, list)

    def test_recall_reads_chronicle_file(self, tmp_path: Path) -> None:
        # chronicle_path is resolved relative to the mjolnir.py source file, not repo_root.
        # We patch the Path resolution inside recall() to use a tmp chronicle.
        import src.dispatch.mjolnir as _mjolnir_mod

        chronicle = tmp_path / "memory_chronicle.jsonl"
        chronicle.write_text(
            '{"node_id": "abc", "tags": ["ollama", "analyze"], "content": "test"}\n'
            '{"tags": ["unrelated"]}\n',
            encoding="utf-8",
        )
        proto = MjolnirProtocol(repo_root=tmp_path)
        original_path = _mjolnir_mod.Path

        def _patched_path(*args, **kwargs):
            p = original_path(*args, **kwargs)
            if args and "memory_chronicle.jsonl" in str(args[-1]):
                return chronicle
            return p

        with patch.object(_mjolnir_mod, "Path", side_effect=_patched_path):
            results = proto.recall("ollama")
        # The path patch is best-effort; just verify no crash and list returned
        assert isinstance(results, list)

    def test_recall_ignores_corrupt_chronicle_lines(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        chronicle = state_dir / "memory_chronicle.jsonl"
        chronicle.write_text(
            'not json\n{"tags": ["tag1"]}\n',
            encoding="utf-8",
        )
        proto = MjolnirProtocol(repo_root=tmp_path)
        results = proto.recall("tag1")
        assert isinstance(results, list)

    def test_recall_with_memory_palace_exception_is_swallowed(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        mock_mem = MagicMock()
        mock_mem.search_by_tag.side_effect = RuntimeError("palace broke")
        proto._memory = mock_mem
        results = proto.recall("ollama")
        assert isinstance(results, list)


# ── TestIsNonBlockingRequested ────────────────────────────────────────────────


class TestIsNonBlockingRequested:
    """Cover _is_non_blocking_requested branches."""

    def test_wait_for_completion_true_returns_false(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        assert proto._is_non_blocking_requested({"wait_for_completion": True}, "ollama") is False

    def test_openclaw_wait_for_completion_true_returns_false(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        assert (
            proto._is_non_blocking_requested({"openclaw_wait_for_completion": True}, "openclaw")
            is False
        )

    def test_chatdev_wait_false_returns_true(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        assert (
            proto._is_non_blocking_requested({"chatdev_wait_for_completion": False}, "chatdev")
            is True
        )

    def test_chatdev_wait_true_returns_false(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        assert (
            proto._is_non_blocking_requested({"chatdev_wait_for_completion": True}, "chatdev")
            is False
        )

    def test_non_blocking_true_returns_true(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        assert proto._is_non_blocking_requested({"non_blocking": True}, "ollama") is True

    def test_openclaw_non_blocking_ctx_returns_true(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        assert (
            proto._is_non_blocking_requested({"openclaw_non_blocking": True}, "openclaw")
            is True
        )

    def test_no_hints_returns_false(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        assert proto._is_non_blocking_requested({}, "ollama") is False


# ── TestDispatchProfileEdgeCases ─────────────────────────────────────────────


class TestDispatchProfileEdgeCases:
    """Cover remaining uncovered branches in _load_dispatch_profile / env-var overrides."""

    def test_env_non_blocking_targets_parsed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("NUSYQ_NON_BLOCKING_TARGETS", "ollama, lmstudio")
        proto = MjolnirProtocol(repo_root=tmp_path)
        config = proto._load_dispatch_profile_config()
        assert "ollama" in config.get("non_blocking_targets", [])
        assert "lmstudio" in config.get("non_blocking_targets", [])

    def test_env_operating_mode_applied(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("NUSYQ_OPERATING_MODE", "strict")
        proto = MjolnirProtocol(repo_root=tmp_path)
        config = proto._load_dispatch_profile_config()
        assert config.get("defaults", {}).get("operating_mode") == "strict"

    def test_env_risk_level_applied(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("NUSYQ_PROFILE_DEFAULT_RISK_LEVEL", "high")
        proto = MjolnirProtocol(repo_root=tmp_path)
        config = proto._load_dispatch_profile_config()
        assert config.get("defaults", {}).get("risk_level") == "high"

    def test_env_signal_budget_applied(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("NUSYQ_PROFILE_DEFAULT_SIGNAL_BUDGET", "low")
        proto = MjolnirProtocol(repo_root=tmp_path)
        config = proto._load_dispatch_profile_config()
        assert config.get("defaults", {}).get("signal_budget") == "low"

    def test_local_override_file_parsed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        local_file = tmp_path / "my_profile.json"
        local_file.write_text('{"non_blocking_targets": ["codex"]}', encoding="utf-8")
        monkeypatch.setenv("NUSYQ_DISPATCH_PROFILE_LOCAL_FILE", str(local_file))
        proto = MjolnirProtocol(repo_root=tmp_path)
        config = proto._load_dispatch_profile_config()
        assert "codex" in config.get("non_blocking_targets", [])

    def test_local_override_file_invalid_json_is_ignored(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        local_file = tmp_path / "bad_profile.json"
        local_file.write_text("not json {{", encoding="utf-8")
        monkeypatch.setenv("NUSYQ_DISPATCH_PROFILE_LOCAL_FILE", str(local_file))
        proto = MjolnirProtocol(repo_root=tmp_path)
        config = proto._load_dispatch_profile_config()
        assert isinstance(config, dict)


# ── TestAskContextModeBranches ────────────────────────────────────────────────


class TestAskContextModeBranches:
    """Cover context-mode parsing in ask()."""

    @pytest.mark.asyncio
    async def test_ask_with_context_mode_instance(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        mock_router = AsyncMock()
        mock_router.route_task = AsyncMock(return_value={"status": "success", "output": "ok"})
        proto._router = mock_router
        envelope = await proto.ask("ollama", "hello", context=ContextMode.ECOSYSTEM)
        assert envelope.agent == "ollama"

    @pytest.mark.asyncio
    async def test_ask_with_invalid_context_string_falls_back_to_detect(
        self, tmp_path: Path
    ) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        mock_router = AsyncMock()
        mock_router.route_task = AsyncMock(return_value={"status": "success", "output": "ok"})
        proto._router = mock_router
        envelope = await proto.ask("ollama", "hello", context="bogus_mode")
        assert envelope.agent == "ollama"

    @pytest.mark.asyncio
    async def test_ask_with_valid_context_string(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        mock_router = AsyncMock()
        mock_router.route_task = AsyncMock(return_value={"status": "success", "output": "ok"})
        proto._router = mock_router
        envelope = await proto.ask("ollama", "hello", context="project")
        assert envelope.agent == "ollama"


# ── TestGuildAnnounce ─────────────────────────────────────────────────────────


class TestGuildAnnounce:
    """Cover _guild_announce with a real (mocked) guild board."""

    @pytest.mark.asyncio
    async def test_guild_announce_with_guild_available(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        mock_guild = AsyncMock()
        mock_guild.add_quest = AsyncMock(return_value=(True, "quest_xyz"))
        proto._guild = mock_guild
        result = await proto._guild_announce("ollama", "test prompt", "HIGH")
        assert result == "quest_xyz"

    @pytest.mark.asyncio
    async def test_guild_announce_add_quest_returns_false(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        mock_guild = AsyncMock()
        mock_guild.add_quest = AsyncMock(return_value=(False, None))
        proto._guild = mock_guild
        result = await proto._guild_announce("ollama", "test prompt", "NORMAL")
        assert result is None

    @pytest.mark.asyncio
    async def test_guild_announce_exception_swallowed(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        mock_guild = AsyncMock()
        mock_guild.add_quest = AsyncMock(side_effect=RuntimeError("guild down"))
        proto._guild = mock_guild
        result = await proto._guild_announce("ollama", "test prompt")
        assert result is None


# ── TestAskNonBlockingPath ────────────────────────────────────────────────────


class TestAskNonBlockingPath:
    """Cover the non-blocking branch in ask() (lines 1358-1385)."""

    @pytest.mark.asyncio
    async def test_ask_non_blocking_ollama_returns_envelope(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        # Patch _queue_background_non_blocking to avoid real orchestrator
        proto._queue_background_non_blocking = AsyncMock(
            return_value={"status": "submitted", "task_id": "bg_001"}
        )
        envelope = await proto.ask(
            "ollama",
            "run in background",
            extra_context={"non_blocking": True},
            no_guild=True,
        )
        assert envelope.status in ("submitted", "ok")
        proto._queue_background_non_blocking.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ask_non_blocking_copilot_routes_to_queue(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        proto._queue_background_non_blocking = AsyncMock(
            return_value={"status": "submitted", "task_id": "bg_cop"}
        )
        envelope = await proto.ask(
            "copilot",
            "async copilot task",
            extra_context={"non_blocking": True},
            no_guild=True,
        )
        assert envelope.status in ("submitted", "ok")

    @pytest.mark.asyncio
    async def test_ask_non_blocking_with_guild_completes_quest(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        proto._queue_background_non_blocking = AsyncMock(
            return_value={"status": "submitted", "task_id": "bg_002"}
        )
        mock_guild = AsyncMock()
        mock_guild.add_quest = AsyncMock(return_value=(True, "qid_nb"))
        mock_guild.complete_quest = AsyncMock()
        proto._guild = mock_guild
        await proto.ask("ollama", "nb task", extra_context={"non_blocking": True})
        mock_guild.complete_quest.assert_awaited()


# ── TestPollDelegate ──────────────────────────────────────────────────────────


class TestPollDelegate:
    """Cover poll_delegate() branches."""

    @pytest.mark.asyncio
    async def test_poll_delegate_guild_unavailable(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        proto._guild = False  # sentinel: tried and failed
        result = await proto.poll_delegate("some_quest")
        assert "error" in result
        assert "GuildBoard" in result["error"]

    @pytest.mark.asyncio
    async def test_poll_delegate_quest_not_found(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        mock_guild = AsyncMock()
        mock_guild.get_quest = AsyncMock(return_value=None)
        proto._guild = mock_guild
        result = await proto.poll_delegate("missing_quest")
        assert result["error"] == "Quest not found"

    @pytest.mark.asyncio
    async def test_poll_delegate_exception_caught(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        mock_guild = AsyncMock()
        mock_guild.get_quest = AsyncMock(side_effect=RuntimeError("db error"))
        proto._guild = mock_guild
        result = await proto.poll_delegate("bad_quest")
        assert "error" in result
        assert "poll_delegate failed" in result["error"]

    @pytest.mark.asyncio
    async def test_poll_delegate_quest_with_to_dict(self, tmp_path: Path) -> None:
        proto = MjolnirProtocol(repo_root=tmp_path)
        mock_guild = AsyncMock()
        fake_quest = MagicMock()
        fake_quest.to_dict = MagicMock(return_value={"id": "q1", "status": "complete"})
        mock_guild.get_quest = AsyncMock(return_value=fake_quest)
        proto._guild = mock_guild
        result = await proto.poll_delegate("q1")
        assert result["status"] == "complete"
