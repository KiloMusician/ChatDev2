"""Coverage boost tests — targeted at modules identified as high-ROI gaps.

Covers:
  - src/core/result.py (Result, Ok, Fail, _OkDescriptor)
  - src/dispatch/council_synthesizer.py (CouncilSynthesizer — pure algorithmic)
  - src/dispatch/context_detector.py (GAME mode, PROJECT mode, enrich_context paths)
  - src/integration/quantum_resolver_adapter.py (QuantumResolverAdapter)
  - src/integration/oldest_house_interface.py (OldestHouseInterface)
  - src/dispatch/agent_registry.py (probe helpers + probe_one/probe_all)
"""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

# ── src/core/result.py ────────────────────────────────────────────────────────


class TestResult:
    def test_ok_class_access_no_args(self):
        from src.core.result import Result

        r = Result.ok()
        assert r.success is True
        assert r.data is None
        assert r.message is None

    def test_ok_class_access_with_data_and_message(self):
        from src.core.result import Result

        r = Result.ok(data={"key": "val"}, message="done")
        assert r.success is True
        assert r.data == {"key": "val"}
        assert r.message == "done"

    def test_ok_instance_access_returns_bool(self):
        from src.core.result import Result

        r = Result(success=True)
        assert r.ok is True
        r2 = Result(success=False)
        assert r2.ok is False

    def test_fail_sets_error_and_code(self):
        from src.core.result import Result

        r = Result.fail("conn refused", code="CONN_ERR")
        assert r.success is False
        assert r.error == "conn refused"
        assert r.code == "CONN_ERR"

    def test_fail_with_data(self):
        from src.core.result import Result

        r = Result.fail("bad", data={"partial": True})
        assert r.data == {"partial": True}

    def test_to_dict_success_no_optionals(self):
        from src.core.result import Result

        r = Result(success=True)
        d = r.to_dict()
        assert d["success"] is True
        assert "timestamp" in d
        assert "data" not in d
        assert "error" not in d

    def test_to_dict_includes_all_optional_fields(self):
        from src.core.result import Result

        r = Result(
            success=False,
            data={"x": 1},
            error="oops",
            code="ERR",
            message="msg",
            meta={"trace": "abc"},
        )
        d = r.to_dict()
        assert d["data"] == {"x": 1}
        assert d["error"] == "oops"
        assert d["code"] == "ERR"
        assert d["message"] == "msg"
        assert d["meta"] == {"trace": "abc"}

    def test_bool_context(self):
        from src.core.result import Result

        assert bool(Result(success=True)) is True
        assert bool(Result(success=False)) is False

    def test_unwrap_success(self):
        from src.core.result import Result

        r = Result.ok(data=42)
        assert r.unwrap() == 42

    def test_unwrap_failure_raises(self):
        from src.core.result import Result

        r = Result.fail("gone", code="GONE")
        with pytest.raises(ValueError, match="gone"):
            r.unwrap()

    def test_unwrap_or_success(self):
        from src.core.result import Result

        assert Result.ok(data="hi").unwrap_or("default") == "hi"

    def test_unwrap_or_failure(self):
        from src.core.result import Result

        assert Result.fail("x").unwrap_or("fallback") == "fallback"

    def test_value_property(self):
        from src.core.result import Result

        r = Result.ok(data=99)
        assert r.value == 99

    def test_ok_fail_module_aliases(self):
        from src.core.result import Fail, Ok

        r = Ok(data="hello")
        assert r.success is True
        r2 = Fail("boom")
        assert r2.success is False


# ── src/dispatch/council_synthesizer.py ──────────────────────────────────────


class TestCouncilSynthesizer:
    @pytest.fixture
    def synth(self):
        from src.dispatch.council_synthesizer import CouncilSynthesizer

        return CouncilSynthesizer()

    def test_empty_input_returns_divergent(self, synth):
        result = synth.synthesize({})
        assert result["consensus_level"] == "divergent"
        assert result["agents_consulted"] == 0
        assert result["confidence"] == 0.0

    def test_single_agent_perfect_agreement(self, synth):
        responses = {"ollama": {"status": "ok", "output": "Use dependency injection"}}
        result = synth.synthesize(responses)
        assert result["agents_consulted"] == 1
        assert result["agents_succeeded"] == 1
        # Single agent → agreement_matrix is empty (no pairs to compare)
        assert result["agreement_matrix"] == {}

    def test_strong_consensus_two_identical_outputs(self, synth):
        text = "Use dependency injection for better testability and decoupling"
        responses = {
            "ollama": {"status": "ok", "output": text},
            "lmstudio": {"status": "ok", "output": text},
        }
        result = synth.synthesize(responses)
        assert result["consensus_level"] == "strong"
        assert result["confidence"] > 0.8

    def test_divergent_when_outputs_completely_different(self, synth):
        responses = {
            "agent_a": {"status": "ok", "output": "alpha beta gamma delta epsilon"},
            "agent_b": {"status": "ok", "output": "zeta eta theta iota kappa lambda"},
        }
        result = synth.synthesize(responses)
        assert result["consensus_level"] in ("weak", "divergent")

    def test_non_ok_agents_scored_zero(self, synth):
        responses = {
            "ollama": {"status": "error", "output": "connection failed"},
            "lmstudio": {"status": "ok", "output": "Use async patterns"},
        }
        result = synth.synthesize(responses)
        assert result["response_quality"]["ollama"] == 0.0
        assert result["response_quality"]["lmstudio"] > 0.0

    def test_timing_penalty_applied(self, synth):
        responses = {
            "slow_agent": {
                "status": "ok",
                "output": "some long output about patterns and practices",
                "timing_ms": 60_000,  # >30s threshold
            }
        }
        result = synth.synthesize(responses)
        assert result["response_quality"]["slow_agent"] < 1.0

    def test_short_output_penalty_applied(self, synth):
        responses = {"agent": {"status": "ok", "output": "yes"}}  # <20 chars
        result = synth.synthesize(responses)
        assert result["response_quality"]["agent"] < 1.0

    def test_all_agents_failed_recommendation_message(self, synth):
        responses = {
            "a": {"status": "error", "output": "timeout"},
            "b": {"status": "error", "output": "conn refused"},
        }
        result = synth.synthesize(responses)
        assert "All agents failed" in result["recommendation"]

    def test_dissenting_views_identified(self, synth):
        responses = {
            "a": {
                "status": "ok",
                "output": "alpha beta gamma delta epsilon zeta eta theta iota kappa",
            },
            "b": {
                "status": "ok",
                "output": "totally different words here one two three four five six",
            },
        }
        result = synth.synthesize(responses)
        assert isinstance(result["dissenting_views"], list)

    def test_jaccard_both_empty(self, synth):
        assert synth._jaccard_similarity("", "") == 1.0

    def test_jaccard_one_empty(self, synth):
        assert synth._jaccard_similarity("hello world", "") == 0.0

    def test_jaccard_identical(self, synth):
        assert synth._jaccard_similarity("hello world", "hello world") == 1.0

    def test_compute_confidence_zero_total(self, synth):
        assert synth._compute_confidence(0.5, 0, 0) == 0.0

    def test_to_text_none_returns_empty(self, synth):
        assert synth._to_text(None) == ""

    def test_to_text_str_passthrough(self, synth):
        assert synth._to_text("hello") == "hello"

    def test_to_text_dict_with_output_key(self, synth):
        assert synth._to_text({"output": "the answer"}) == "the answer"

    def test_to_text_dict_without_known_key(self, synth):
        result = synth._to_text({"unknown_key": "data"})
        assert "unknown_key" in result  # falls through to str(output)

    def test_classify_strong(self, synth):
        assert synth._classify_consensus(0.7) == "strong"

    def test_classify_moderate(self, synth):
        assert synth._classify_consensus(0.5) == "moderate"

    def test_classify_weak(self, synth):
        assert synth._classify_consensus(0.3) == "weak"

    def test_classify_divergent(self, synth):
        assert synth._classify_consensus(0.1) == "divergent"


# ── src/dispatch/context_detector.py ─────────────────────────────────────────


class TestContextDetectorExtended:
    def test_detect_game_mode_from_simverse_cwd(self, tmp_path, monkeypatch):
        from src.dispatch.context_detector import ContextDetector, ContextMode

        # Simulate CWD under a simverse-like directory
        simverse_root = tmp_path / "SimulatedVerse"
        simverse_root.mkdir()
        nested = simverse_root / "src"
        nested.mkdir()

        monkeypatch.delenv("NUSYQ_CONTEXT_MODE", raising=False)
        monkeypatch.delenv("NUSYQ_HUB_ROOT", raising=False)
        monkeypatch.delenv("SIMULATEDVERSE_ROOT", raising=False)

        detector = ContextDetector()
        detector._hub_root = None
        detector._simverse_root = simverse_root.resolve()

        result = detector.detect(cwd=nested)
        assert result == ContextMode.GAME

    def test_detect_project_fallback_when_no_roots(self, tmp_path, monkeypatch):
        from src.dispatch.context_detector import ContextDetector, ContextMode

        monkeypatch.delenv("NUSYQ_CONTEXT_MODE", raising=False)
        detector = ContextDetector()
        detector._hub_root = None
        detector._simverse_root = None

        result = detector.detect(cwd=tmp_path)
        assert result == ContextMode.PROJECT

    def test_enrich_context_game_mode(self, tmp_path):
        from src.dispatch.context_detector import ContextDetector, ContextMode

        detector = ContextDetector()
        detector._simverse_root = tmp_path / "sv"

        ctx = detector.enrich_context(ContextMode.GAME)
        assert ctx["context_mode"] == "game"
        assert "scope_hint" in ctx
        assert "relevant_configs" in ctx

    def test_enrich_context_project_mode(self):
        from src.dispatch.context_detector import ContextDetector, ContextMode

        detector = ContextDetector()
        ctx = detector.enrich_context(ContextMode.PROJECT)
        assert ctx["context_mode"] == "project"
        assert "project_root" in ctx

    def test_enrich_context_merges_base_context(self):
        from src.dispatch.context_detector import ContextDetector, ContextMode

        detector = ContextDetector()
        ctx = detector.enrich_context(ContextMode.PROJECT, base_context={"extra": "val"})
        assert ctx["extra"] == "val"
        assert ctx["context_mode"] == "project"

    def test_env_override_takes_priority(self, monkeypatch):
        from src.dispatch.context_detector import ContextDetector, ContextMode

        monkeypatch.setenv("NUSYQ_CONTEXT_MODE", "game")
        detector = ContextDetector()
        assert detector.detect() == ContextMode.GAME


# ── src/integration/quantum_resolver_adapter.py ──────────────────────────────


class TestQuantumResolverAdapter:
    @pytest.fixture
    def adapter(self):
        from src.integration.quantum_resolver_adapter import QuantumResolverAdapter

        return QuantumResolverAdapter()

    def test_init_empty_lists(self, adapter):
        assert adapter.omni_tags == []
        assert adapter.mega_tags == []

    def test_add_omni_tag(self, adapter):
        adapter.add_omni_tag("quantum")
        assert "quantum" in adapter.omni_tags

    def test_add_mega_tag(self, adapter):
        adapter.add_mega_tag("healing")
        assert "healing" in adapter.mega_tags

    def test_resolve_context_basic(self, adapter):
        result = adapter.resolve_context("test query")
        assert result["query"] == "test query"
        assert "omni_tags" in result
        assert "mega_tags" in result
        assert "contextual_insights" in result

    def test_resolve_context_matching_omni_tag(self, adapter):
        adapter.add_omni_tag("quantum")
        result = adapter.resolve_context("quantum healing process")
        assert any("OmniTag" in i for i in result["contextual_insights"])

    def test_resolve_context_matching_mega_tag(self, adapter):
        adapter.add_mega_tag("healing")
        result = adapter.resolve_context("healing ceremony")
        assert any("MegaTag" in i for i in result["contextual_insights"])

    def test_resolve_context_no_matches(self, adapter):
        adapter.add_omni_tag("alpha")
        result = adapter.resolve_context("unrelated query xyz")
        assert result["contextual_insights"] == []

    def test_clear_tags(self, adapter):
        adapter.add_omni_tag("x")
        adapter.add_mega_tag("y")
        adapter.clear_tags()
        assert adapter.omni_tags == []
        assert adapter.mega_tags == []


# ── src/integration/oldest_house_interface.py ────────────────────────────────


class TestOldestHouseInterface:
    @pytest.fixture
    def iface(self):
        from src.integration.oldest_house_interface import OldestHouseInterface

        return OldestHouseInterface()

    def test_init_empty(self, iface):
        assert iface.omni_tags == []
        assert iface.mega_tags == []

    def test_create_omni_tag(self, iface):
        iface.create_omni_tag({"id": "t1", "context": "ctx", "created_at": "now"})
        assert len(iface.omni_tags) == 1
        assert iface.omni_tags[0]["id"] == "t1"

    def test_create_omni_tag_defaults_metadata(self, iface):
        iface.create_omni_tag({})
        assert iface.omni_tags[0]["metadata"] == {}

    def test_process_mega_tag(self, iface):
        iface.process_mega_tag({"id": "m1", "attributes": {"level": 5}})
        assert iface.mega_tags[0]["id"] == "m1"
        assert iface.mega_tags[0]["attributes"] == {"level": 5}

    def test_process_mega_tag_defaults_related_tags(self, iface):
        iface.process_mega_tag({})
        assert iface.mega_tags[0]["related_tags"] == []

    def test_get_omni_tags(self, iface):
        iface.create_omni_tag({"id": "a"})
        iface.create_omni_tag({"id": "b"})
        tags = iface.get_omni_tags()
        assert len(tags) == 2

    def test_get_mega_tags(self, iface):
        iface.process_mega_tag({"id": "x"})
        tags = iface.get_mega_tags()
        assert len(tags) == 1

    def test_clear_tags(self, iface):
        iface.create_omni_tag({"id": "t"})
        iface.process_mega_tag({"id": "m"})
        iface.clear_tags()
        assert iface.get_omni_tags() == []
        assert iface.get_mega_tags() == []


# ── src/dispatch/agent_registry.py — probe helpers ───────────────────────────


class TestAgentRegistryProbes:
    def test_probe_http_success(self):
        from unittest.mock import patch

        import src.dispatch.agent_registry as ar

        class _FakeResp:
            status = 200

            def read(self, n):
                return b'{"status":"ok"}'

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        # Must patch at the import site inside agent_registry, not urllib.request
        with patch("src.dispatch.agent_registry.urlopen", return_value=_FakeResp()):
            status, _detail, meta = ar._probe_http("http://127.0.0.1:9999/health")
        assert status == ar.AgentStatus.ONLINE
        assert meta["http_status"] == 200

    def test_probe_http_failure(self):
        import src.dispatch.agent_registry as ar

        # Port 1 is never open — should get OFFLINE
        status, _detail, _meta = ar._probe_http("http://127.0.0.1:1/no-such-path", timeout=0.3)
        assert status == ar.AgentStatus.OFFLINE

    def test_probe_cli_found(self, monkeypatch):
        import src.dispatch.agent_registry as ar

        monkeypatch.setattr(ar.shutil, "which", lambda cmd: f"/usr/bin/{cmd}")
        status, _detail, meta = ar._probe_cli("python")
        assert status == ar.AgentStatus.ONLINE
        assert "/usr/bin/python" in meta["path"]

    def test_probe_cli_not_found(self, monkeypatch):
        import src.dispatch.agent_registry as ar

        monkeypatch.setattr(ar.shutil, "which", lambda cmd: None)
        status, _detail, _meta = ar._probe_cli("nonexistent-cli-xyz")
        assert status == ar.AgentStatus.OFFLINE

    def test_probe_env_var_set(self, monkeypatch):
        import src.dispatch.agent_registry as ar

        monkeypatch.setenv("TEST_PROBE_VAR_XYZ", "active")
        status, _detail, _meta = ar._probe_env_var("TEST_PROBE_VAR_XYZ")
        assert status == ar.AgentStatus.ONLINE

    def test_probe_env_var_not_set(self, monkeypatch):
        import src.dispatch.agent_registry as ar

        monkeypatch.delenv("TEST_PROBE_VAR_XYZ", raising=False)
        status, _detail, _meta = ar._probe_env_var("TEST_PROBE_VAR_XYZ")
        assert status == ar.AgentStatus.OFFLINE

    def test_probe_import_existing_module(self):
        import src.dispatch.agent_registry as ar

        status, _detail, _meta = ar._probe_import("json")
        assert status == ar.AgentStatus.ONLINE

    def test_probe_import_missing_module(self):
        import src.dispatch.agent_registry as ar

        status, _detail, _meta = ar._probe_import("nonexistent.module.xyz.abc")
        assert status == ar.AgentStatus.OFFLINE

    def test_probe_chatdev_local_env_path(self, tmp_path, monkeypatch):
        import src.dispatch.agent_registry as ar

        # Create fake ChatDev dir with run.py
        chatdev_dir = tmp_path / "ChatDev"
        chatdev_dir.mkdir()
        (chatdev_dir / "run.py").write_text("# fake")

        monkeypatch.setenv("CHATDEV_PATH", str(chatdev_dir))
        status, _detail, _meta = ar._probe_chatdev_local()
        assert status == ar.AgentStatus.ONLINE

    def test_probe_chatdev_local_no_path(self, tmp_path, monkeypatch):
        import src.dispatch.agent_registry as ar

        monkeypatch.delenv("CHATDEV_PATH", raising=False)
        # Patch all candidate paths to nonexistent
        with patch.object(ar.Path, "exists", return_value=False):
            status, _detail, _meta = ar._probe_chatdev_local()
        assert status == ar.AgentStatus.OFFLINE

    def test_run_probe_command_success(self):
        import src.dispatch.agent_registry as ar

        code, _output = ar._run_probe_command(["python", "--version"])
        assert code == 0

    def test_run_probe_command_timeout(self):
        import src.dispatch.agent_registry as ar

        # Tiny timeout on a slow command → should get 124
        code, _output = ar._run_probe_command(
            ["python", "-c", "import time; time.sleep(10)"], timeout=0.1
        )
        assert code == 124

    def test_probe_one_unknown_agent(self):
        import src.dispatch.agent_registry as ar

        registry = ar.AgentAvailabilityRegistry()
        result = asyncio.run(registry.probe_one("nonexistent_agent_xyz"))
        assert result.status == ar.AgentStatus.UNKNOWN

    def test_probe_all_returns_all_agents(self):
        import src.dispatch.agent_registry as ar

        registry = ar.AgentAvailabilityRegistry(timeout=0.1)
        results = asyncio.run(registry.probe_all())
        assert set(results.keys()) == set(ar.AGENT_PROBES.keys())

    def test_probe_all_subset(self):
        import src.dispatch.agent_registry as ar

        registry = ar.AgentAvailabilityRegistry(timeout=0.1)
        results = asyncio.run(registry.probe_all(agents=["codex", "ollama"]))
        assert set(results.keys()) == {"codex", "ollama"}

    def test_get_display_name_known(self):
        import src.dispatch.agent_registry as ar

        registry = ar.AgentAvailabilityRegistry()
        assert registry.get_display_name("ollama") == "Ollama (local LLMs)"

    def test_get_display_name_unknown(self):
        import src.dispatch.agent_registry as ar

        registry = ar.AgentAvailabilityRegistry()
        assert registry.get_display_name("mystery_agent") == "mystery_agent"
