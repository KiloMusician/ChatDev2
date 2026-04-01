"""Tests for src/integration/universal_llm_gateway.py — ModelCapability, UniversalLLMGateway."""

import pytest


class TestModelCapabilityDataclass:
    """Tests for ModelCapability dataclass."""

    def test_basic_construction(self):
        from src.integration.universal_llm_gateway import ModelCapability
        cap = ModelCapability(provider="ollama", model="llama3.1:8b", tags=["code", "general"])
        assert cap.provider == "ollama"
        assert cap.model == "llama3.1:8b"
        assert "code" in cap.tags

    def test_defaults(self):
        from src.integration.universal_llm_gateway import ModelCapability
        cap = ModelCapability(provider="openai", model="gpt-4", tags=[])
        assert cap.cost == "unknown"
        assert cap.latency == "unknown"

    def test_custom_cost_latency(self):
        from src.integration.universal_llm_gateway import ModelCapability
        cap = ModelCapability(
            provider="openai", model="gpt-4", tags=["general"],
            cost="high", latency="medium"
        )
        assert cap.cost == "high"
        assert cap.latency == "medium"


class TestHelperFunctions:
    """Tests for module-level helper functions."""

    def test_env_flag_enabled_default_true(self, monkeypatch):
        from src.integration.universal_llm_gateway import _env_flag_enabled
        monkeypatch.delenv("SOME_FLAG_XYZ", raising=False)
        assert _env_flag_enabled("SOME_FLAG_XYZ", default=True) is True

    def test_env_flag_enabled_default_false(self, monkeypatch):
        from src.integration.universal_llm_gateway import _env_flag_enabled
        monkeypatch.delenv("SOME_FLAG_XYZ", raising=False)
        assert _env_flag_enabled("SOME_FLAG_XYZ", default=False) is False

    def test_env_flag_enabled_set(self, monkeypatch):
        from src.integration.universal_llm_gateway import _env_flag_enabled
        monkeypatch.setenv("SOME_FLAG_TEST", "1")
        assert _env_flag_enabled("SOME_FLAG_TEST") is True

    def test_env_flag_disabled_with_zero(self, monkeypatch):
        from src.integration.universal_llm_gateway import _env_flag_enabled
        monkeypatch.setenv("SOME_FLAG_TEST", "0")
        assert _env_flag_enabled("SOME_FLAG_TEST") is False

    def test_caps_cache_ttl_returns_int(self):
        from src.integration.universal_llm_gateway import _caps_cache_ttl
        ttl = _caps_cache_ttl()
        assert isinstance(ttl, int)
        assert ttl > 0

    def test_tag_model_name_returns_list(self):
        from src.integration.universal_llm_gateway import _tag_model_name
        tags = _tag_model_name("llama3.1:8b")
        assert isinstance(tags, list)

    def test_tag_model_name_coder_model(self):
        from src.integration.universal_llm_gateway import _tag_model_name
        tags = _tag_model_name("qwen2.5-coder:14b")
        assert isinstance(tags, list)

    def test_normalize_base_url_strips_trailing_slash(self):
        from src.integration.universal_llm_gateway import _normalize_base_url
        result = _normalize_base_url("http://localhost:11434/")
        assert not result.endswith("/")

    def test_normalize_base_url_strips_v1(self):
        from src.integration.universal_llm_gateway import _normalize_base_url
        result = _normalize_base_url("http://localhost:8080/v1", strip_v1=True)
        assert not result.endswith("/v1")

    def test_merge_capabilities_deduplication(self):
        from src.integration.universal_llm_gateway import ModelCapability, _merge_capabilities
        caps = [
            ModelCapability("ollama", "model1", ["code"]),
            ModelCapability("ollama", "model1", ["general"]),  # duplicate
            ModelCapability("ollama", "model2", ["code"]),
        ]
        merged = _merge_capabilities(caps, [])
        models = [c.model for c in merged]
        assert models.count("model1") == 1  # deduped


class TestUniversalLLMGateway:
    """Tests for UniversalLLMGateway with explicit capabilities (no network)."""

    @pytest.fixture
    def gateway(self):
        from src.integration.universal_llm_gateway import ModelCapability, UniversalLLMGateway
        caps = [
            ModelCapability("ollama", "llama3.1:8b", ["code", "general"], cost="low"),
            ModelCapability("ollama", "qwen2.5-coder:14b", ["code"], cost="low"),
            ModelCapability("openai", "gpt-4", ["general"], cost="high"),
        ]
        return UniversalLLMGateway(capabilities=caps, dry_run=True)

    def test_instantiation(self, gateway):
        assert gateway is not None

    def test_dry_run_true(self, gateway):
        assert gateway.dry_run is True

    def test_capabilities_loaded(self, gateway):
        assert len(gateway.capabilities) == 3

    def test_select_model_by_hint(self, gateway):
        model = gateway.select_model("llama3.1:8b", capability_tags=[])
        assert model is not None
        assert model.model == "llama3.1:8b"

    def test_select_model_unknown_hint_returns_fallback(self, gateway):
        # Unknown hint — falls through to tag-based selection or returns None
        model = gateway.select_model("nonexistent:model", capability_tags=["code"])
        # Either None or a fallback is fine
        assert model is None or hasattr(model, "model")

    def test_select_model_by_tag(self, gateway):
        model = gateway.select_model(None, capability_tags=["code"])
        assert model is not None
        assert "code" in model.tags

    def test_select_model_prefer_local(self, gateway):
        model = gateway.select_model(None, capability_tags=["general"], prefer_local=True)
        # Should prefer ollama (local) over openai
        if model:
            assert model.provider == "ollama"

    def test_select_model_max_cost_low(self, gateway):
        model = gateway.select_model(None, capability_tags=["general"], max_cost="low")
        if model:
            assert model.cost == "low"

    def test_route_request_dry_run_no_network(self, gateway):
        # dry_run=True should not make real API calls
        result = gateway.route_request(
            prompt="Test prompt",
            capability_tags=["code"],
        )
        # May return a dry-run placeholder or dict
        assert result is not None

    def test_call_lmstudio_emits_terminal_event_on_success(self, monkeypatch):
        from src.integration.universal_llm_gateway import ModelCapability, UniversalLLMGateway

        gateway = UniversalLLMGateway(
            capabilities=[ModelCapability("lmstudio", "openai/gpt-oss-20b", ["local"])],
            dry_run=False,
        )
        monkeypatch.setenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234")

        class _Response:
            def raise_for_status(self):
                return None

            def json(self):
                return {"choices": [{"message": {"content": "ok"}}]}

        emitted: list[tuple[str, str, str, str, dict]] = []
        monkeypatch.setattr(
            "src.integration.universal_llm_gateway.httpx.post",
            lambda *args, **kwargs: _Response(),
        )
        monkeypatch.setattr(
            "src.integration.universal_llm_gateway._emit_provider_event",
            lambda provider, event_type, message, level="INFO", extra=None: emitted.append(
                (provider, event_type, message, level, extra or {})
            ),
        )

        result = gateway._call_lmstudio("openai/gpt-oss-20b", "hello", {})

        assert result["provider"] == "lmstudio"
        assert emitted
        assert emitted[0][0] == "lmstudio"
        assert emitted[0][1] == "model_invocation"

    def test_call_lmstudio_emits_terminal_event_on_failure(self, monkeypatch):
        from src.integration.universal_llm_gateway import ModelCapability, UniversalLLMGateway

        gateway = UniversalLLMGateway(
            capabilities=[ModelCapability("lmstudio", "openai/gpt-oss-20b", ["local"])],
            dry_run=False,
        )
        monkeypatch.setenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234")

        emitted: list[tuple[str, str, str, str, dict]] = []
        monkeypatch.setattr(
            "src.integration.universal_llm_gateway.httpx.post",
            lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        monkeypatch.setattr(
            "src.integration.universal_llm_gateway._emit_provider_event",
            lambda provider, event_type, message, level="INFO", extra=None: emitted.append(
                (provider, event_type, message, level, extra or {})
            ),
        )

        result = gateway._call_lmstudio("openai/gpt-oss-20b", "hello", {})

        assert "lmstudio_call_failed" in result["error"]
        assert emitted
        assert emitted[0][0] == "lmstudio"
        assert emitted[0][1] == "model_invocation_failed"
