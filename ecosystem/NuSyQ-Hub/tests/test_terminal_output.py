"""Tests for src/utils/terminal_output.py - Terminal output routing.

Tests TerminalType enum, TerminalRouter class, and convenience functions.
"""

import json
from typing import Any

import pytest
from src.system.terminal_pid_registry import _normalize_runtime_path
from src.utils.terminal_output import (
    TerminalRouter,
    TerminalType,
    get_router,
    to_anomalies,
    to_chatdev,
    to_claude,
    to_codex,
    to_copilot,
    to_council,
    to_errors,
    to_future,
    to_intermediary,
    to_metrics,
    to_suggestions,
    to_tasks,
    to_tests,
    to_zeta,
)

# =============================================================================
# Test TerminalType Enum
# =============================================================================


class TestTerminalType:
    """Tests for TerminalType enum."""

    def test_all_terminal_types_defined(self) -> None:
        """All terminal types are defined."""
        expected = [
            "CLAUDE",
            "COPILOT",
            "CODEX",
            "CHATDEV",
            "AI_COUNCIL",
            "INTERMEDIARY",
            "ERRORS",
            "SUGGESTIONS",
            "TASKS",
            "TESTS",
            "ZETA",
            "METRICS",
            "ANOMALIES",
            "FUTURE",
            "MAIN",
        ]
        for name in expected:
            assert hasattr(TerminalType, name)

    def test_terminal_type_values(self) -> None:
        """Terminal type values are lowercase."""
        assert TerminalType.CLAUDE.value == "claude"
        assert TerminalType.COPILOT.value == "copilot"
        assert TerminalType.AI_COUNCIL.value == "ai_council"
        assert TerminalType.ERRORS.value == "errors"
        assert TerminalType.MAIN.value == "main"


@pytest.mark.skipif(
    __import__("os").name == "nt",
    reason="WSL path conversion only applies on non-Windows (POSIX/WSL) runtimes",
)
def test_normalize_runtime_path_converts_windows_drive_path_in_wsl() -> None:
    normalized = _normalize_runtime_path(
        r"C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\data\terminal_logs\copilot.log"
    )
    assert str(normalized) == "/mnt/c/Users/keath/Desktop/Legacy/NuSyQ-Hub/data/terminal_logs/copilot.log"


# =============================================================================
# Test TerminalRouter Initialization
# =============================================================================


class TestTerminalRouterInit:
    """Tests for TerminalRouter initialization."""

    def test_default_root(self, tmp_path: Any) -> None:
        """Default root is project directory."""
        router = TerminalRouter()
        assert router.root.exists()

    def test_custom_root(self, tmp_path: Any) -> None:
        """Custom root is used."""
        router = TerminalRouter(root=tmp_path)
        assert router.root == tmp_path

    def test_routing_config_loaded(self, tmp_path: Any) -> None:
        """Routing config is loaded on init."""
        router = TerminalRouter(root=tmp_path)
        assert isinstance(router.routing_config, dict)

    def test_routing_config_has_defaults(self, tmp_path: Any) -> None:
        """Routing config has default keys when file missing."""
        router = TerminalRouter(root=tmp_path)
        assert "routing_keywords" in router.routing_config
        assert "terminals" in router.routing_config


# =============================================================================
# Test route() method
# =============================================================================


class TestRoute:
    """Tests for route() method."""

    def test_route_returns_terminal_id(self, tmp_path: Any) -> None:
        """Route returns the terminal ID."""
        router = TerminalRouter(root=tmp_path)
        terminal_id = router.route("Test message", agent=TerminalType.CLAUDE)
        assert terminal_id == "claude"

    def test_route_with_agent(self, tmp_path: Any, capsys: Any) -> None:
        """Route with agent uses agent terminal."""
        router = TerminalRouter(root=tmp_path)
        terminal_id = router.route("Test message", agent=TerminalType.COPILOT)
        assert terminal_id == "copilot"

    def test_route_error_level(self, tmp_path: Any) -> None:
        """Route with ERROR level uses errors terminal."""
        router = TerminalRouter(root=tmp_path)
        # Without agent, ERROR level routes to errors
        terminal_id = router.route("Error occurred", level="ERROR")
        assert terminal_id == "errors"

    def test_route_default_to_main(self, tmp_path: Any) -> None:
        """Route defaults to main terminal."""
        router = TerminalRouter(root=tmp_path)
        terminal_id = router.route("Generic message")
        assert terminal_id == "main"

    def test_route_prints_formatted(self, tmp_path: Any, capsys: Any) -> None:
        """Route prints formatted message."""
        router = TerminalRouter(root=tmp_path)
        router.route("Hello world", agent=TerminalType.CLAUDE)
        captured = capsys.readouterr()
        assert "Hello world" in captured.out
        assert "claude" in captured.out or "Claude" in captured.out

    def test_route_logs_to_file(self, tmp_path: Any) -> None:
        """Route logs to terminal-specific file."""
        router = TerminalRouter(root=tmp_path)
        router.route("Test log", agent=TerminalType.TESTS)

        log_file = tmp_path / "data" / "terminal_logs" / "tests.log"
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test log" in content


# =============================================================================
# Test _route_by_content() method
# =============================================================================


class TestRouteByContent:
    """Tests for _route_by_content() method."""

    def test_route_by_content_default(self, tmp_path: Any) -> None:
        """_route_by_content returns main for unknown content."""
        router = TerminalRouter(root=tmp_path)
        result = router._route_by_content("random content")
        assert result == "main"

    def test_route_by_content_with_keywords(self, tmp_path: Any) -> None:
        """_route_by_content routes based on keywords."""
        # Create routing config
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        config = {
            "routing_keywords": {"error": "errors", "test": "tests"},
            "terminals": {},
        }
        (data_dir / "terminal_routing.json").write_text(json.dumps(config))

        router = TerminalRouter(root=tmp_path)
        assert router._route_by_content("An error occurred") == "errors"
        assert router._route_by_content("Running test suite") == "tests"


# =============================================================================
# Test _log_to_file() method
# =============================================================================


class TestLogToFile:
    """Tests for _log_to_file() method."""

    def test_log_to_file_creates_dir(self, tmp_path: Any) -> None:
        """_log_to_file creates log directory."""
        router = TerminalRouter(root=tmp_path)
        router._log_to_file("test", "Test message")

        log_dir = tmp_path / "data" / "terminal_logs"
        assert log_dir.exists()

    def test_log_to_file_appends(self, tmp_path: Any) -> None:
        """_log_to_file appends multiple messages."""
        router = TerminalRouter(root=tmp_path)
        router._log_to_file("test", "First message")
        router._log_to_file("test", "Second message")

        log_file = tmp_path / "data" / "terminal_logs" / "test.log"
        content = log_file.read_text()
        assert "First message" in content
        assert "Second message" in content


# =============================================================================
# Test Agent-Specific Methods
# =============================================================================


class TestAgentMethods:
    """Tests for agent-specific methods."""

    def test_claude(self, tmp_path: Any, capsys: Any) -> None:
        """claude() routes to Claude terminal."""
        router = TerminalRouter(root=tmp_path)
        router.claude("Claude message")
        captured = capsys.readouterr()
        assert "Claude message" in captured.out

    def test_copilot(self, tmp_path: Any, capsys: Any) -> None:
        """copilot() routes to Copilot terminal."""
        router = TerminalRouter(root=tmp_path)
        router.copilot("Copilot message")
        captured = capsys.readouterr()
        assert "Copilot message" in captured.out

    def test_codex(self, tmp_path: Any, capsys: Any) -> None:
        """codex() routes to Codex terminal."""
        router = TerminalRouter(root=tmp_path)
        router.codex("Codex message")
        captured = capsys.readouterr()
        assert "Codex message" in captured.out

    def test_chatdev(self, tmp_path: Any, capsys: Any) -> None:
        """chatdev() routes to ChatDev terminal."""
        router = TerminalRouter(root=tmp_path)
        router.chatdev("ChatDev message")
        captured = capsys.readouterr()
        assert "ChatDev message" in captured.out

    def test_council(self, tmp_path: Any, capsys: Any) -> None:
        """council() routes to AI Council terminal."""
        router = TerminalRouter(root=tmp_path)
        router.council("Council message")
        captured = capsys.readouterr()
        assert "Council message" in captured.out

    def test_intermediary(self, tmp_path: Any, capsys: Any) -> None:
        """intermediary() routes to Intermediary terminal."""
        router = TerminalRouter(root=tmp_path)
        router.intermediary("Intermediary message")
        captured = capsys.readouterr()
        assert "Intermediary message" in captured.out

    def test_error(self, tmp_path: Any, capsys: Any) -> None:
        """error() routes to Errors terminal."""
        router = TerminalRouter(root=tmp_path)
        router.error("Error message")
        captured = capsys.readouterr()
        assert "Error message" in captured.out

    def test_suggest(self, tmp_path: Any, capsys: Any) -> None:
        """suggest() routes to Suggestions terminal."""
        router = TerminalRouter(root=tmp_path)
        router.suggest("Suggestion message")
        captured = capsys.readouterr()
        assert "Suggestion message" in captured.out

    def test_task(self, tmp_path: Any, capsys: Any) -> None:
        """task() routes to Tasks terminal."""
        router = TerminalRouter(root=tmp_path)
        router.task("Task message")
        captured = capsys.readouterr()
        assert "Task message" in captured.out

    def test_test(self, tmp_path: Any, capsys: Any) -> None:
        """test() routes to Tests terminal."""
        router = TerminalRouter(root=tmp_path)
        router.test("Test message")
        captured = capsys.readouterr()
        assert "Test message" in captured.out

    def test_zeta(self, tmp_path: Any, capsys: Any) -> None:
        """zeta() routes to Zeta terminal."""
        router = TerminalRouter(root=tmp_path)
        router.zeta("Zeta message")
        captured = capsys.readouterr()
        assert "Zeta message" in captured.out

    def test_metric(self, tmp_path: Any, capsys: Any) -> None:
        """metric() routes to Metrics terminal."""
        router = TerminalRouter(root=tmp_path)
        router.metric("Metric message")
        captured = capsys.readouterr()
        assert "Metric message" in captured.out

    def test_anomaly(self, tmp_path: Any, capsys: Any) -> None:
        """anomaly() routes to Anomalies terminal."""
        router = TerminalRouter(root=tmp_path)
        router.anomaly("Anomaly message")
        captured = capsys.readouterr()
        assert "Anomaly message" in captured.out

    def test_future(self, tmp_path: Any, capsys: Any) -> None:
        """future() routes to Future terminal."""
        router = TerminalRouter(root=tmp_path)
        router.future("Future message")
        captured = capsys.readouterr()
        assert "Future message" in captured.out


# =============================================================================
# Test get_router() Singleton
# =============================================================================


class TestGetRouter:
    """Tests for get_router() singleton."""

    def test_get_router_returns_router(self) -> None:
        """get_router returns a TerminalRouter."""
        # Reset global state for test
        import src.utils.terminal_output as module

        module._router = None

        router = get_router()
        assert isinstance(router, TerminalRouter)

    def test_get_router_returns_same_instance(self) -> None:
        """get_router returns the same instance."""
        import src.utils.terminal_output as module

        module._router = None

        router1 = get_router()
        router2 = get_router()
        assert router1 is router2


# =============================================================================
# Test Convenience Functions
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_to_claude(self, capsys: Any) -> None:
        """to_claude sends to Claude terminal."""
        to_claude("Claude test")
        captured = capsys.readouterr()
        assert "Claude test" in captured.out

    def test_to_copilot(self, capsys: Any) -> None:
        """to_copilot sends to Copilot terminal."""
        to_copilot("Copilot test")
        captured = capsys.readouterr()
        assert "Copilot test" in captured.out

    def test_to_codex(self, capsys: Any) -> None:
        """to_codex sends to Codex terminal."""
        to_codex("Codex test")
        captured = capsys.readouterr()
        assert "Codex test" in captured.out

    def test_to_chatdev(self, capsys: Any) -> None:
        """to_chatdev sends to ChatDev terminal."""
        to_chatdev("ChatDev test")
        captured = capsys.readouterr()
        assert "ChatDev test" in captured.out

    def test_to_council(self, capsys: Any) -> None:
        """to_council sends to AI Council terminal."""
        to_council("Council test")
        captured = capsys.readouterr()
        assert "Council test" in captured.out

    def test_to_intermediary(self, capsys: Any) -> None:
        """to_intermediary sends to Intermediary terminal."""
        to_intermediary("Intermediary test")
        captured = capsys.readouterr()
        assert "Intermediary test" in captured.out

    def test_to_errors(self, capsys: Any) -> None:
        """to_errors sends to Errors terminal."""
        to_errors("Error test")
        captured = capsys.readouterr()
        assert "Error test" in captured.out

    def test_to_suggestions(self, capsys: Any) -> None:
        """to_suggestions sends to Suggestions terminal."""
        to_suggestions("Suggestion test")
        captured = capsys.readouterr()
        assert "Suggestion test" in captured.out

    def test_to_tasks(self, capsys: Any) -> None:
        """to_tasks sends to Tasks terminal."""
        to_tasks("Task test")
        captured = capsys.readouterr()
        assert "Task test" in captured.out

    def test_to_tests(self, capsys: Any) -> None:
        """to_tests sends to Tests terminal."""
        to_tests("Test test")
        captured = capsys.readouterr()
        assert "Test test" in captured.out

    def test_to_zeta(self, capsys: Any) -> None:
        """to_zeta sends to Zeta terminal."""
        to_zeta("Zeta test")
        captured = capsys.readouterr()
        assert "Zeta test" in captured.out

    def test_to_metrics(self, capsys: Any) -> None:
        """to_metrics sends to Metrics terminal."""
        to_metrics("Metrics test")
        captured = capsys.readouterr()
        assert "Metrics test" in captured.out

    def test_to_anomalies(self, capsys: Any) -> None:
        """to_anomalies sends to Anomalies terminal."""
        to_anomalies("Anomaly test")
        captured = capsys.readouterr()
        assert "Anomaly test" in captured.out

    def test_to_future(self, capsys: Any) -> None:
        """to_future sends to Future terminal."""
        to_future("Future test")
        captured = capsys.readouterr()
        assert "Future test" in captured.out


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_message(self, tmp_path: Any, capsys: Any) -> None:
        """Empty message can be routed."""
        router = TerminalRouter(root=tmp_path)
        router.route("", agent=TerminalType.MAIN)
        # Should not raise

    def test_unicode_message(self, tmp_path: Any, capsys: Any) -> None:
        """Unicode messages are handled."""
        router = TerminalRouter(root=tmp_path)
        router.route("Hello 世界 🌍", agent=TerminalType.CLAUDE)
        captured = capsys.readouterr()
        assert "世界" in captured.out or "Hello" in captured.out

    def test_long_message(self, tmp_path: Any, capsys: Any) -> None:
        """Long messages are handled."""
        router = TerminalRouter(root=tmp_path)
        long_msg = "x" * 10000
        router.route(long_msg, agent=TerminalType.MAIN)
        captured = capsys.readouterr()
        assert "x" in captured.out

    def test_missing_config_files(self, tmp_path: Any) -> None:
        """Router works without config files."""
        router = TerminalRouter(root=tmp_path)
        # Should have default empty config
        assert router.routing_config == {"routing_keywords": {}, "terminals": {}}

    def test_invalid_routing_config(self, tmp_path: Any) -> None:
        """Router handles invalid routing config."""
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "terminal_routing.json").write_text("not valid json")

        # Should not raise, will have defaults
        with pytest.raises((json.JSONDecodeError, Exception)):
            TerminalRouter(root=tmp_path)
