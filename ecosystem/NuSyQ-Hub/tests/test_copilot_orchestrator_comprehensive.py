"""
Tests for ClaudeCopilotOrchestrator (src.core.claude_copilot_orchestrator).

Tests the stub-mode route/analyze API and MJOLNIR delegation behaviour.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.claude_copilot_orchestrator import ClaudeCopilotOrchestrator


class TestClaudeCopilotOrchestratorInit:
    """Test ClaudeCopilotOrchestrator initialisation."""

    def test_instantiation(self):
        orch = ClaudeCopilotOrchestrator()
        assert orch is not None

    def test_initial_status_is_idle(self):
        orch = ClaudeCopilotOrchestrator()
        assert orch.status == "idle"

    def test_get_protocol_returns_none_when_mjolnir_unavailable(self):
        orch = ClaudeCopilotOrchestrator()
        with patch("src.dispatch.mjolnir.MjolnirProtocol", side_effect=ImportError):
            with patch.dict("sys.modules", {"src.dispatch.mjolnir": None}):
                result = orch._get_protocol()
        assert result is None


class TestClaudeCopilotOrchestratorRoute:
    """Test route() method."""

    def test_route_stub_mode_returns_not_implemented(self):
        orch = ClaudeCopilotOrchestrator()
        with patch.object(orch, "_get_protocol", return_value=None):
            result = orch.route("analyze code")
        assert result["status"] == "not_implemented"
        assert result["task"] == "analyze code"

    def test_route_stub_mode_includes_empty_context(self):
        orch = ClaudeCopilotOrchestrator()
        with patch.object(orch, "_get_protocol", return_value=None):
            result = orch.route("do something")
        assert isinstance(result["context"], dict)

    def test_route_passes_context_through(self):
        orch = ClaudeCopilotOrchestrator()
        with patch.object(orch, "_get_protocol", return_value=None):
            result = orch.route("fix bug", context={"file": "main.py", "line": 42})
        assert result["context"]["file"] == "main.py"
        assert result["context"]["line"] == 42

    def test_route_with_mock_protocol_returns_success(self):
        orch = ClaudeCopilotOrchestrator()
        mock_envelope = MagicMock()
        mock_envelope.status = "success"
        mock_envelope.agent = "ollama"
        mock_envelope.output = "analysis complete"

        mock_protocol = MagicMock()
        mock_protocol.ask = AsyncMock(return_value=mock_envelope)

        with patch.object(orch, "_get_protocol", return_value=mock_protocol):
            result = orch.route("test task")

        assert result["status"] == "success"
        assert result["agent"] == "ollama"
        assert result["output"] == "analysis complete"

    def test_route_falls_back_to_error_when_all_agents_raise(self):
        orch = ClaudeCopilotOrchestrator()
        mock_protocol = MagicMock()
        mock_protocol.ask = AsyncMock(side_effect=RuntimeError("unavailable"))

        with patch.object(orch, "_get_protocol", return_value=mock_protocol):
            result = orch.route("task")

        assert result["status"] == "error"
        assert result["task"] == "task"

    def test_route_no_context_arg_gives_empty_dict(self):
        orch = ClaudeCopilotOrchestrator()
        with patch.object(orch, "_get_protocol", return_value=None):
            result = orch.route("check")
        assert result["context"] == {}


class TestClaudeCopilotOrchestratorAnalyze:
    """Test analyze() method."""

    def test_analyze_stub_mode_returns_not_implemented(self):
        orch = ClaudeCopilotOrchestrator()
        with patch.object(orch, "_get_protocol", return_value=None):
            result = orch.analyze("function foo(): pass")
        assert result["status"] == "not_implemented"

    def test_analyze_stub_mode_includes_summary(self):
        orch = ClaudeCopilotOrchestrator()
        text = "def hello(): print('world')"
        with patch.object(orch, "_get_protocol", return_value=None):
            result = orch.analyze(text)
        assert "summary" in result
        assert result["summary"] == text[:200]

    def test_analyze_stub_mode_context_empty_by_default(self):
        orch = ClaudeCopilotOrchestrator()
        with patch.object(orch, "_get_protocol", return_value=None):
            result = orch.analyze("code")
        assert isinstance(result["context"], dict)

    def test_analyze_passes_context_through(self):
        orch = ClaudeCopilotOrchestrator()
        with patch.object(orch, "_get_protocol", return_value=None):
            result = orch.analyze("code", context={"project": "nusyq", "lang": "python"})
        assert result["context"]["project"] == "nusyq"
        assert result["context"]["lang"] == "python"

    def test_analyze_with_mock_protocol_returns_success(self):
        orch = ClaudeCopilotOrchestrator()
        mock_envelope = MagicMock()
        mock_envelope.status = "success"
        mock_envelope.agent = "claude_cli"
        mock_envelope.output = "detailed analysis"

        mock_protocol = MagicMock()
        mock_protocol.ask = AsyncMock(return_value=mock_envelope)

        with patch.object(orch, "_get_protocol", return_value=mock_protocol):
            result = orch.analyze("text to analyze")

        assert result["status"] == "success"
        assert "summary" in result

    def test_analyze_falls_back_to_error_when_all_agents_raise(self):
        orch = ClaudeCopilotOrchestrator()
        mock_protocol = MagicMock()
        mock_protocol.ask = AsyncMock(side_effect=Exception("model offline"))

        with patch.object(orch, "_get_protocol", return_value=mock_protocol):
            result = orch.analyze("some text")

        assert result["status"] == "error"
        assert "summary" in result

    def test_analyze_truncates_long_text_in_prompt(self):
        """Verify analyze() handles very long text without crashing."""
        orch = ClaudeCopilotOrchestrator()
        long_text = "x" * 5000
        with patch.object(orch, "_get_protocol", return_value=None):
            result = orch.analyze(long_text)
        assert result["status"] == "not_implemented"
        assert len(result["summary"]) <= 200


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__, "-v", "--cov=src.core.claude_copilot_orchestrator"])
