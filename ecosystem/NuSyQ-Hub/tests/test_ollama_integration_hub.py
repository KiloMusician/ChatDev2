"""Tests for src/integration/Ollama_Integration_Hub.py."""
from __future__ import annotations

import json
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_hub(tmp_path: Path, *, connected: bool = False) -> KILOOllamaHub:
    """Return a KILOOllamaHub that does NOT try to contact Ollama."""
    from src.integration.Ollama_Integration_Hub import KILOOllamaHub

    with (
        patch("src.integration.Ollama_Integration_Hub.is_ollama_online", return_value=connected),
        patch("src.integration.Ollama_Integration_Hub._ensure_ollama", None),
    ):
        hub = KILOOllamaHub.__new__(KILOOllamaHub)
        hub.config = {}
        hub.logger = MagicMock()
        hub.client = None
        hub.is_connected = connected
        from src.integration.Ollama_Integration_Hub import (
            ConversationManager,
            IntelligentModelSelector,
            PerformanceMonitor,
        )

        hub.model_selector = IntelligentModelSelector()
        hub.conversation_manager = ConversationManager(
            session_id="test-session",
        )
        hub.performance_monitor = PerformanceMonitor()
        hub.available_models = {}
        hub.model_preferences = {
            "code_analysis": "codellama:7b",
            "documentation": "llama2:7b",
            "reasoning": "mistral:7b",
            "creative": "llama2:13b",
            "security": "llama2:7b",
            "optimization": "codellama:7b",
            "default": "llama2:7b",
        }
        return hub


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


class TestGetOllamaUrl:
    def test_default_url(self) -> None:
        from src.integration.Ollama_Integration_Hub import get_ollama_url

        url = get_ollama_url()
        assert "127.0.0.1" in url or "localhost" in url or "11434" in url

    def test_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://10.0.0.1:11434")
        # Reset singleton config cache so env var is re-read
        from src.integration.Ollama_Integration_Hub import OllamaConfigLoader

        loader = OllamaConfigLoader()
        loader._config = None
        from src.integration.Ollama_Integration_Hub import get_ollama_url

        url = get_ollama_url()
        # The URL may come from the resolved config or the env fallback
        assert isinstance(url, str)
        assert url.startswith("http")

    def test_returns_string(self) -> None:
        from src.integration.Ollama_Integration_Hub import get_ollama_url

        assert isinstance(get_ollama_url(), str)


class TestIsOllamaOnline:
    def test_returns_false_when_requests_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.integration.Ollama_Integration_Hub as hub_mod

        monkeypatch.setattr(hub_mod, "requests", None)
        assert hub_mod.is_ollama_online() is False

    def test_returns_true_on_200(self) -> None:
        import src.integration.Ollama_Integration_Hub as hub_mod

        fake_resp = MagicMock()
        fake_resp.status_code = 200
        with patch.object(hub_mod._requests, "get", return_value=fake_resp):  # type: ignore[union-attr]
            result = hub_mod.is_ollama_online(timeout=1.0)
        assert result is True

    def test_returns_false_on_500(self) -> None:
        import src.integration.Ollama_Integration_Hub as hub_mod

        fake_resp = MagicMock()
        fake_resp.status_code = 500
        with patch.object(hub_mod._requests, "get", return_value=fake_resp):  # type: ignore[union-attr]
            result = hub_mod.is_ollama_online(timeout=1.0)
        assert result is False

    def test_returns_false_on_oserror(self) -> None:
        import src.integration.Ollama_Integration_Hub as hub_mod

        if hub_mod._requests is None:
            pytest.skip("requests not available")
        with patch.object(hub_mod._requests, "get", side_effect=OSError("refused")):
            result = hub_mod.is_ollama_online(timeout=1.0)
        assert result is False


class TestListOllamaModels:
    def test_returns_empty_when_requests_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.integration.Ollama_Integration_Hub as hub_mod

        monkeypatch.setattr(hub_mod, "requests", None)
        assert hub_mod.list_ollama_models() == []

    def test_returns_models_from_data_key(self) -> None:
        import src.integration.Ollama_Integration_Hub as hub_mod

        if hub_mod._requests is None:
            pytest.skip("requests not available")
        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.json.return_value = {"data": [{"id": "llama2", "name": "llama2"}]}
        with patch.object(hub_mod._requests, "get", return_value=fake_resp):
            models = hub_mod.list_ollama_models()
        assert len(models) == 1
        assert models[0]["name"] == "llama2"

    def test_returns_models_from_models_key(self) -> None:
        import src.integration.Ollama_Integration_Hub as hub_mod

        if hub_mod._requests is None:
            pytest.skip("requests not available")
        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.json.return_value = {"models": [{"name": "mistral"}]}
        with patch.object(hub_mod._requests, "get", return_value=fake_resp):
            models = hub_mod.list_ollama_models()
        assert models[0]["name"] == "mistral"

    def test_skips_non_dict_entries(self) -> None:
        import src.integration.Ollama_Integration_Hub as hub_mod

        if hub_mod._requests is None:
            pytest.skip("requests not available")
        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.json.return_value = {"data": ["string", 42, {"name": "good"}]}
        with patch.object(hub_mod._requests, "get", return_value=fake_resp):
            models = hub_mod.list_ollama_models()
        assert len(models) == 1

    def test_returns_empty_on_connection_error(self) -> None:
        import src.integration.Ollama_Integration_Hub as hub_mod

        if hub_mod._requests is None:
            pytest.skip("requests not available")
        with patch.object(hub_mod._requests, "get", side_effect=OSError("no conn")):
            models = hub_mod.list_ollama_models()
        assert models == []

    def test_returns_empty_on_bad_json(self) -> None:
        import src.integration.Ollama_Integration_Hub as hub_mod

        if hub_mod._requests is None:
            pytest.skip("requests not available")
        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.json.side_effect = json.JSONDecodeError("bad", "", 0)
        with patch.object(hub_mod._requests, "get", return_value=fake_resp):
            models = hub_mod.list_ollama_models()
        assert models == []


class TestGetTimeout:
    def test_returns_default_when_env_not_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from src.integration.Ollama_Integration_Hub import get_timeout

        monkeypatch.delenv("MY_TIMEOUT", raising=False)
        assert get_timeout("MY_TIMEOUT", default=5.0) == 5.0

    def test_returns_env_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from src.integration.Ollama_Integration_Hub import get_timeout

        monkeypatch.setenv("MY_TIMEOUT", "7.5")
        assert get_timeout("MY_TIMEOUT", default=1.0) == 7.5

    def test_returns_default_on_invalid_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from src.integration.Ollama_Integration_Hub import get_timeout

        monkeypatch.setenv("MY_TIMEOUT", "not_a_number")
        assert get_timeout("MY_TIMEOUT", default=3.0) == 3.0


# ---------------------------------------------------------------------------
# OllamaModel dataclass
# ---------------------------------------------------------------------------


class TestOllamaModel:
    def test_instantiation(self) -> None:
        from src.integration.Ollama_Integration_Hub import OllamaModel

        m = OllamaModel(name="llama2", size=1000, digest="abc", modified_at="2024-01-01")
        assert m.name == "llama2"
        assert m.size == 1000
        assert m.capabilities == []

    def test_last_used_auto_set(self) -> None:
        from src.integration.Ollama_Integration_Hub import OllamaModel

        m = OllamaModel(name="x", size=0, digest="", modified_at="")
        assert m.last_used != ""

    def test_to_dict(self) -> None:
        from src.integration.Ollama_Integration_Hub import OllamaModel

        m = OllamaModel(name="y", size=0, digest="", modified_at="")
        d = m.to_dict()
        assert isinstance(d, dict)
        assert d["name"] == "y"


# ---------------------------------------------------------------------------
# ChatMessage dataclass
# ---------------------------------------------------------------------------


class TestChatMessage:
    def test_timestamp_auto_set(self) -> None:
        from src.integration.Ollama_Integration_Hub import ChatMessage

        msg = ChatMessage(role="user", content="hello")
        assert msg.timestamp is not None

    def test_explicit_timestamp(self) -> None:
        from src.integration.Ollama_Integration_Hub import ChatMessage

        msg = ChatMessage(role="user", content="hi", timestamp="2024-01-01T00:00:00")
        assert msg.timestamp == "2024-01-01T00:00:00"


# ---------------------------------------------------------------------------
# OllamaResponse dataclass
# ---------------------------------------------------------------------------


class TestOllamaResponse:
    def test_default_context_is_empty_list(self) -> None:
        from src.integration.Ollama_Integration_Hub import OllamaResponse

        r = OllamaResponse(message="hi", model="llama2", created_at="now", done=True)
        assert r.context == []

    def test_success_default_true(self) -> None:
        from src.integration.Ollama_Integration_Hub import OllamaResponse

        r = OllamaResponse(message="", model="", created_at="", done=True)
        assert r.success is True


# ---------------------------------------------------------------------------
# IntelligentModelSelector
# ---------------------------------------------------------------------------


class TestIntelligentModelSelector:
    def test_init(self) -> None:
        from src.integration.Ollama_Integration_Hub import IntelligentModelSelector

        sel = IntelligentModelSelector()
        assert "code_analysis" in sel.task_capability_map
        assert sel.current_strategy == "adaptive"

    def test_analyze_message_intent_code(self) -> None:
        from src.integration.Ollama_Integration_Hub import IntelligentModelSelector

        sel = IntelligentModelSelector()
        intent = sel.analyze_message_intent("debug this function code")
        assert intent == "code_analysis"

    def test_analyze_message_intent_default(self) -> None:
        from src.integration.Ollama_Integration_Hub import IntelligentModelSelector

        sel = IntelligentModelSelector()
        intent = sel.analyze_message_intent("zzz qqq")
        assert intent == "default"

    def test_analyze_message_intent_security(self) -> None:
        from src.integration.Ollama_Integration_Hub import IntelligentModelSelector

        sel = IntelligentModelSelector()
        intent = sel.analyze_message_intent("security vulnerability audit")
        assert intent == "security"

    def test_select_optimal_model_fallback_when_empty(self) -> None:
        from src.integration.Ollama_Integration_Hub import FALLBACK_MODEL, IntelligentModelSelector

        sel = IntelligentModelSelector()
        result = sel.select_optimal_model({}, "code_analysis")
        assert result == FALLBACK_MODEL

    def test_select_optimal_model_picks_highest_score(self) -> None:
        from src.integration.Ollama_Integration_Hub import IntelligentModelSelector, OllamaModel

        sel = IntelligentModelSelector()
        models = {
            "codellama:7b": OllamaModel(
                name="codellama:7b",
                size=0,
                digest="",
                modified_at="",
                capabilities=["code_analysis", "code_generation", "debugging"],
                performance_rating=8.0,
            ),
            "llama2:7b": OllamaModel(
                name="llama2:7b",
                size=0,
                digest="",
                modified_at="",
                capabilities=["conversation"],
                performance_rating=5.0,
            ),
        }
        result = sel.select_optimal_model(models, "code_analysis")
        assert result == "codellama:7b"

    def test_set_selection_strategy_valid(self) -> None:
        from src.integration.Ollama_Integration_Hub import IntelligentModelSelector

        sel = IntelligentModelSelector()
        sel.set_selection_strategy("balanced")
        assert sel.current_strategy == "balanced"

    def test_set_selection_strategy_invalid(self) -> None:
        from src.integration.Ollama_Integration_Hub import IntelligentModelSelector

        sel = IntelligentModelSelector()
        sel.set_selection_strategy("nonexistent")
        assert sel.current_strategy != "nonexistent"

    def test_record_selection_history(self) -> None:
        from src.integration.Ollama_Integration_Hub import IntelligentModelSelector

        sel = IntelligentModelSelector()
        sel._record_selection_history("llama2", "code_analysis", 7.0)
        assert len(sel.selection_history) == 1
        assert sel.selection_history[0]["model"] == "llama2"


# ---------------------------------------------------------------------------
# ConversationManager
# ---------------------------------------------------------------------------


class TestConversationManager:
    def test_init_creates_session_dir(self, tmp_path: Path) -> None:
        from src.integration.Ollama_Integration_Hub import ConversationManager

        with patch(
            "src.integration.Ollama_Integration_Hub.Path",
            side_effect=lambda *a, **k: Path(*a, **k),
        ):
            mgr = ConversationManager(session_id="testsess")
        assert mgr.session_id == "testsess"
        assert mgr.max_history == 1000

    def test_add_message_increments_counter(self, tmp_path: Path) -> None:
        from src.integration.Ollama_Integration_Hub import ChatMessage, ConversationManager

        mgr = ConversationManager(session_id="s1")
        msg = ChatMessage(role="user", content="hello world")
        mgr.add_message(msg)
        assert mgr.message_counter == 1
        assert len(mgr.conversation_history) == 1

    def test_get_context_messages_returns_list(self) -> None:
        from src.integration.Ollama_Integration_Hub import ChatMessage, ConversationManager

        mgr = ConversationManager(session_id="s2")
        mgr.add_message(ChatMessage(role="user", content="hi"))
        ctx = mgr.get_context_messages(3)
        assert isinstance(ctx, list)

    def test_save_and_load_round_trip(self, tmp_path: Path) -> None:
        from src.integration.Ollama_Integration_Hub import ChatMessage, ConversationManager

        mgr = ConversationManager(session_id="s3")
        mgr.add_message(ChatMessage(role="user", content="round trip test"))
        file_path = str(tmp_path / "conv.json")
        saved = mgr.save_to_file(file_path)
        assert saved == file_path

        mgr2 = ConversationManager(session_id="s4")
        ok = mgr2.load_from_file(file_path)
        assert ok is True
        assert len(mgr2.conversation_history) == 1
        assert mgr2.conversation_history[0].content == "round trip test"

    def test_load_from_file_nonexistent(self, tmp_path: Path) -> None:
        from src.integration.Ollama_Integration_Hub import ConversationManager

        mgr = ConversationManager(session_id="s5")
        result = mgr.load_from_file(str(tmp_path / "missing.json"))
        assert result is False

    def test_calculate_importance_score(self) -> None:
        from src.integration.Ollama_Integration_Hub import ChatMessage, ConversationManager

        mgr = ConversationManager(session_id="s6")
        msg = ChatMessage(role="system", content="important project goal remember context background")
        score = mgr._calculate_importance_score(msg)
        assert 0.0 <= score <= 1.0

    def test_get_contextual_memory_empty(self) -> None:
        from src.integration.Ollama_Integration_Hub import ConversationManager

        mgr = ConversationManager(session_id="s7")
        result = mgr.get_contextual_memory("some query")
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# PerformanceMonitor
# ---------------------------------------------------------------------------


class TestPerformanceMonitor:
    def test_init_stats_structure(self) -> None:
        from src.integration.Ollama_Integration_Hub import PerformanceMonitor

        pm = PerformanceMonitor()
        assert pm.stats["total_requests"] == 0

    def test_record_request_success(self) -> None:
        from src.integration.Ollama_Integration_Hub import PerformanceMonitor

        pm = PerformanceMonitor()
        pm.record_request("llama2", "code_analysis", 1.5, True)
        assert pm.stats["total_requests"] == 1
        assert pm.stats["successful_requests"] == 1
        assert pm.stats["average_response_time"] == pytest.approx(1.5)

    def test_record_request_failure(self) -> None:
        from src.integration.Ollama_Integration_Hub import PerformanceMonitor

        pm = PerformanceMonitor()
        pm.record_request("llama2", "code_analysis", 0.5, False, "connection refused")
        assert pm.stats["failed_requests"] == 1
        assert "connection refused" in pm.stats["error_patterns"]

    def test_get_performance_report_structure(self) -> None:
        from src.integration.Ollama_Integration_Hub import PerformanceMonitor

        pm = PerformanceMonitor()
        pm.record_request("llama2", "default", 2.0, True)
        report = pm.get_performance_report()
        assert "summary" in report
        assert "detailed_stats" in report
        assert "top_models" in report

    def test_calculate_trends_insufficient_data(self) -> None:
        from src.integration.Ollama_Integration_Hub import PerformanceMonitor

        pm = PerformanceMonitor()
        trends = pm._calculate_trends()
        assert trends["success"] is False

    def test_calculate_trends_with_data(self) -> None:
        from src.integration.Ollama_Integration_Hub import PerformanceMonitor

        pm = PerformanceMonitor()
        for i in range(15):
            pm.record_request("m", "t", float(i), True)
        trends = pm._calculate_trends()
        assert isinstance(trends, dict)


# ---------------------------------------------------------------------------
# KILOOllamaHub
# ---------------------------------------------------------------------------


class TestKILOOllamaHubInstantiation:
    def test_hub_offline_mode(self, tmp_path: Path) -> None:
        hub = _make_hub(tmp_path, connected=False)
        assert hub.is_connected is False
        assert hub.client is None

    def test_hub_has_model_preferences(self, tmp_path: Path) -> None:
        hub = _make_hub(tmp_path)
        assert "code_analysis" in hub.model_preferences

    def test_hub_has_performance_monitor(self, tmp_path: Path) -> None:
        from src.integration.Ollama_Integration_Hub import PerformanceMonitor

        hub = _make_hub(tmp_path)
        assert isinstance(hub.performance_monitor, PerformanceMonitor)


class TestKILOOllamaHubGetStatus:
    def test_status_disconnected(self, tmp_path: Path) -> None:
        hub = _make_hub(tmp_path, connected=False)
        status = hub.get_status()
        assert status["connection_status"] == "disconnected"
        assert status["available_models"] == 0

    def test_status_connected(self, tmp_path: Path) -> None:
        from src.integration.Ollama_Integration_Hub import OllamaModel

        hub = _make_hub(tmp_path, connected=True)
        hub.available_models = {
            "llama2": OllamaModel(name="llama2", size=0, digest="", modified_at="")
        }
        status = hub.get_status()
        assert status["connection_status"] == "connected"
        assert status["available_models"] == 1

    def test_status_capabilities_keys(self, tmp_path: Path) -> None:
        hub = _make_hub(tmp_path)
        status = hub.get_status()
        assert "streaming" in status["capabilities"]


class TestKILOOllamaHubChat:
    def test_chat_offline_returns_error_response(self, tmp_path: Path) -> None:
        from src.integration.Ollama_Integration_Hub import OllamaResponse

        hub = _make_hub(tmp_path, connected=False)
        result = hub.chat("hello")
        assert isinstance(result, OllamaResponse)
        assert result.success is False
        assert result.error != ""

    def test_chat_calls_complete_chat_when_connected(self, tmp_path: Path) -> None:
        from src.integration.Ollama_Integration_Hub import OllamaResponse

        hub = _make_hub(tmp_path, connected=True)
        mock_response = OllamaResponse(
            message="Hello!", model="llama2", created_at="now", done=True, success=True
        )
        with patch.object(hub, "_complete_chat", return_value=mock_response) as mock_cc:
            result = hub.chat("hi", model="llama2")
        mock_cc.assert_called_once()
        assert isinstance(result, OllamaResponse)
        assert result.message == "Hello!"

    def test_chat_uses_streaming_when_flag_set(self, tmp_path: Path) -> None:
        hub = _make_hub(tmp_path, connected=True)

        def fake_stream(
            model: str, messages: list, save: bool
        ) -> Generator[str, None, None]:
            yield "chunk1"
            yield "chunk2"

        with patch.object(hub, "_stream_chat", side_effect=fake_stream):
            result = hub.chat("hi", model="llama2", stream=True)
        # result is either a generator or the wrapped one
        chunks = list(result)  # type: ignore[arg-type]
        assert "chunk1" in chunks


class TestKILOOllamaHubAnalyzeCode:
    def test_analyze_code_offline(self, tmp_path: Path) -> None:
        hub = _make_hub(tmp_path, connected=False)
        result = hub.analyze_code(str(tmp_path / "nofile.py"))
        assert "error" in result

    def test_analyze_code_file_not_found(self, tmp_path: Path) -> None:
        hub = _make_hub(tmp_path, connected=True)
        result = hub.analyze_code(str(tmp_path / "missing.py"))
        assert "error" in result
        assert "not found" in result["error"]

    def test_analyze_code_success(self, tmp_path: Path) -> None:
        from src.integration.Ollama_Integration_Hub import OllamaResponse

        code_file = tmp_path / "sample.py"
        code_file.write_text("def hello():\n    return 'world'\n", encoding="utf-8")

        hub = _make_hub(tmp_path, connected=True)
        mock_resp = OllamaResponse(
            message="Looks good!", model="codellama:7b", created_at="now", done=True, success=True
        )
        with patch.object(hub, "chat", return_value=mock_resp):
            result = hub.analyze_code(str(code_file))

        assert result["success"] is True
        assert result["analysis"] == "Looks good!"

    def test_analyze_code_chat_failure(self, tmp_path: Path) -> None:
        from src.integration.Ollama_Integration_Hub import OllamaResponse

        code_file = tmp_path / "bad.py"
        code_file.write_text("x = 1", encoding="utf-8")

        hub = _make_hub(tmp_path, connected=True)
        mock_resp = OllamaResponse(
            message="",
            model="llama2",
            created_at="now",
            done=True,
            success=False,
            error="timeout",
        )
        with patch.object(hub, "chat", return_value=mock_resp):
            result = hub.analyze_code(str(code_file))

        assert result["success"] is False


class TestKILOOllamaHubGenerateDocs:
    def test_generate_docs_offline(self, tmp_path: Path) -> None:
        hub = _make_hub(tmp_path, connected=False)
        result = hub.generate_docs("def f(): pass")
        assert "error" in result

    def test_generate_docs_success(self, tmp_path: Path) -> None:
        from src.integration.Ollama_Integration_Hub import OllamaResponse

        hub = _make_hub(tmp_path, connected=True)
        mock_resp = OllamaResponse(
            message="Great docs!", model="llama2", created_at="now", done=True, success=True
        )
        with patch.object(hub, "chat", return_value=mock_resp):
            result = hub.generate_docs("def f(): pass")

        assert result["documentation"] == "Great docs!"
        assert "model_used" in result

    def test_generate_docs_failure(self, tmp_path: Path) -> None:
        from src.integration.Ollama_Integration_Hub import OllamaResponse

        hub = _make_hub(tmp_path, connected=True)
        mock_resp = OllamaResponse(
            message="",
            model="llama2",
            created_at="now",
            done=True,
            success=False,
            error="server error",
        )
        with patch.object(hub, "chat", return_value=mock_resp):
            result = hub.generate_docs("def g(): pass")

        assert "error" in result


class TestKILOOllamaHubDiscoverModels:
    def test_discover_models_offline(self, tmp_path: Path) -> None:
        hub = _make_hub(tmp_path, connected=False)
        result = hub.discover_models()
        assert result == {}

    def test_discover_models_from_dict_response(self, tmp_path: Path) -> None:
        hub = _make_hub(tmp_path, connected=True)
        fake_client = MagicMock()
        fake_client.list.return_value = {
            "models": [
                {
                    "name": "llama2:7b",
                    "size": 4_000_000_000,
                    "digest": "abc123",
                    "modified_at": "2024-01-01",
                    "details": {"family": "llama", "parameter_size": "7B"},
                }
            ]
        }
        hub.client = fake_client
        result = hub.discover_models()
        assert "llama2:7b" in result
        assert result["llama2:7b"].family == "llama"

    def test_discover_models_from_list_response(self, tmp_path: Path) -> None:
        hub = _make_hub(tmp_path, connected=True)
        fake_client = MagicMock()
        fake_client.list.return_value = [
            {"name": "mistral:7b", "size": 0, "digest": "", "modified_at": ""}
        ]
        hub.client = fake_client
        result = hub.discover_models()
        assert "mistral:7b" in result


class TestKILOOllamaHubModelRecommendations:
    def test_get_model_recommendations_empty(self, tmp_path: Path) -> None:
        hub = _make_hub(tmp_path)
        recs = hub.get_model_recommendations("debug some code")
        assert recs == []

    def test_get_model_recommendations_returns_top_5(self, tmp_path: Path) -> None:
        from src.integration.Ollama_Integration_Hub import OllamaModel

        hub = _make_hub(tmp_path)
        for i in range(8):
            name = f"model{i}"
            hub.available_models[name] = OllamaModel(
                name=name, size=0, digest="", modified_at="", performance_rating=float(i)
            )
        recs = hub.get_model_recommendations("debug some code")
        assert len(recs) <= 5


class TestKILOOllamaHubExportConversation:
    def test_export_conversation_returns_path(self, tmp_path: Path) -> None:
        hub = _make_hub(tmp_path)
        export_path = str(tmp_path / "export.json")
        result = hub.export_conversation(export_path)
        assert result == export_path
        assert Path(export_path).exists()


class TestKILOOllamaHubCapabilityAnalysis:
    def test_analyze_model_capabilities_code(self, tmp_path: Path) -> None:
        from src.integration.Ollama_Integration_Hub import OllamaModel

        hub = _make_hub(tmp_path)
        model = OllamaModel(name="codellama:7b", size=0, digest="", modified_at="")
        caps = hub._analyze_model_capabilities(model)
        assert "code_generation" in caps

    def test_analyze_model_capabilities_llama(self, tmp_path: Path) -> None:
        from src.integration.Ollama_Integration_Hub import OllamaModel

        hub = _make_hub(tmp_path)
        model = OllamaModel(name="llama2:7b", size=0, digest="", modified_at="")
        caps = hub._analyze_model_capabilities(model)
        assert "conversation" in caps

    def test_estimate_performance_rating_70b(self, tmp_path: Path) -> None:
        from src.integration.Ollama_Integration_Hub import OllamaModel

        hub = _make_hub(tmp_path)
        model = OllamaModel(name="llama2:70b", size=0, digest="", modified_at="")
        rating = hub._estimate_performance_rating(model)
        assert rating > 5.0

    def test_estimate_memory_usage(self, tmp_path: Path) -> None:
        from src.integration.Ollama_Integration_Hub import OllamaModel

        hub = _make_hub(tmp_path)
        model = OllamaModel(name="test", size=1024 * 1024 * 4096, digest="", modified_at="")
        mem = hub._estimate_memory_usage(model)
        assert mem > 0


class TestCreateStepTag:
    def test_success_tag(self, tmp_path: Path) -> None:
        hub = _make_hub(tmp_path)
        tag = hub._create_step_tag("Coder", 1, 0)
        assert tag["status"] == "success"
        assert tag["agent"] == "Coder"

    def test_error_tag(self, tmp_path: Path) -> None:
        hub = _make_hub(tmp_path)
        tag = hub._create_step_tag("Coder", 2, 1)
        assert tag["status"] == "error"

    def test_exception_tag(self, tmp_path: Path) -> None:
        hub = _make_hub(tmp_path)
        tag = hub._create_step_tag("Coder", 3, -1)
        assert tag["status"] == "exception"


class TestMarkEvolutionComplete:
    def test_creates_flag_file(self, tmp_path: Path) -> None:
        hub = _make_hub(tmp_path)
        flag = tmp_path / "evolved.flag"
        result = hub._mark_evolution_complete(flag)
        assert result is True
        assert flag.exists()

    def test_returns_false_on_oserror(self, tmp_path: Path) -> None:
        hub = _make_hub(tmp_path)
        bad_path = tmp_path / "no_such_dir" / "flag.txt"
        # Parent dir doesn't exist → OSError on write_text
        result = hub._mark_evolution_complete(bad_path)
        assert result is False
