"""Tests for src/tools batch 5: operator_heartbeat, performance_optimizer, token_metrics_dashboard.

Coverage targets:
- operator_heartbeat.py: 203 lines - Heartbeat class and decorator
- performance_optimizer.py: 229 lines - subprocess and encoding safety
- token_metrics_dashboard.py: 255 lines - token usage tracking
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import pytest


# ==============================================================================
# operator_heartbeat.py tests
# ==============================================================================
class TestHeartbeatInit:
    """Test Heartbeat class initialization."""

    def test_init_defaults(self):
        """Verify default initialization."""
        from src.tools.operator_heartbeat import Heartbeat

        hb = Heartbeat("Test operation")
        assert hb.description == "Test operation"
        assert hb.interval == 5.0
        assert hb.prefix == "💓"
        assert hb.enable_logging is True
        assert hb._thread is None
        assert hb._heartbeat_count == 0

    def test_init_custom_values(self):
        """Custom initialization values."""
        from src.tools.operator_heartbeat import Heartbeat

        hb = Heartbeat("Custom", interval=2.0, prefix="⏰", enable_logging=False)
        assert hb.interval == 2.0
        assert hb.prefix == "⏰"
        assert hb.enable_logging is False


class TestHeartbeatStartStop:
    """Test Heartbeat start/stop methods."""

    def test_start_initializes_thread(self):
        """Start creates background thread."""
        from src.tools.operator_heartbeat import Heartbeat

        hb = Heartbeat("Test", interval=1.0)
        hb.start()
        try:
            assert hb._thread is not None
            assert hb._thread.is_alive()
            assert hb._start_time is not None
        finally:
            hb.stop()

    def test_stop_terminates_thread(self):
        """Stop terminates background thread."""
        from src.tools.operator_heartbeat import Heartbeat

        hb = Heartbeat("Test", interval=0.5)
        hb.start()
        time.sleep(0.1)
        hb.stop()

        # Thread should terminate after stop
        time.sleep(0.2)
        assert not hb._thread.is_alive()

    def test_start_twice_noop(self):
        """Starting twice doesn't create duplicate threads."""
        from src.tools.operator_heartbeat import Heartbeat

        hb = Heartbeat("Test", interval=1.0)
        hb.start()
        thread1 = hb._thread
        hb.start()  # Second start should be no-op
        assert hb._thread is thread1
        hb.stop()

    def test_stop_without_start_noop(self):
        """Stopping without start is safe."""
        from src.tools.operator_heartbeat import Heartbeat

        hb = Heartbeat("Test")
        hb.stop()  # Should not raise


class TestHeartbeatContextManager:
    """Test Heartbeat context manager."""

    def test_context_manager_starts_and_stops(self):
        """Context manager properly starts and stops heartbeat."""
        from src.tools.operator_heartbeat import Heartbeat

        with Heartbeat("Context test", interval=0.5) as hb:
            assert hb._thread is not None
            assert hb._thread.is_alive()

        # After exit, thread should be stopped
        time.sleep(0.2)
        assert not hb._thread.is_alive()

    def test_exit_returns_false(self):
        """__exit__ returns False to not suppress exceptions."""
        from src.tools.operator_heartbeat import Heartbeat

        hb = Heartbeat("Test")
        result = hb.__exit__(None, None, None)
        assert result is False


class TestHeartbeatFunction:
    """Test heartbeat context manager function."""

    def test_heartbeat_function(self):
        """Test heartbeat() convenience function."""
        from src.tools.operator_heartbeat import heartbeat

        with heartbeat("Function test", interval=0.5) as hb:
            assert hb.description == "Function test"
            assert hb._thread.is_alive()


class TestHeartbeatWrapper:
    """Test heartbeat_wrapper decorator."""

    def test_wrapper_preserves_return_value(self):
        """Decorator preserves function return value."""
        from src.tools.operator_heartbeat import heartbeat_wrapper

        @heartbeat_wrapper(interval=0.5)
        def test_func() -> str:
            return "result"

        result = test_func()
        assert result == "result"

    def test_wrapper_uses_function_name(self):
        """Decorator uses function name as default description."""
        from src.tools.operator_heartbeat import heartbeat_wrapper

        @heartbeat_wrapper(interval=0.5)
        def my_long_operation():
            pass

        # Just verify it runs without error
        my_long_operation()

    def test_wrapper_custom_description(self):
        """Decorator accepts custom description."""
        from src.tools.operator_heartbeat import heartbeat_wrapper

        @heartbeat_wrapper(interval=0.5, description="Custom desc")
        def func():
            pass

        func()  # Should not raise


# ==============================================================================
# performance_optimizer.py tests
# ==============================================================================
class TestEncodingSafeOutputHandler:
    """Test EncodingSafeOutputHandler class."""

    def test_init(self):
        """Verify initialization."""
        from src.tools.performance_optimizer import EncodingSafeOutputHandler

        handler = EncodingSafeOutputHandler()
        assert handler.terminal_encoding is not None

    def test_safe_print_normal(self, capsys):
        """safe_print outputs text normally."""
        from src.tools.performance_optimizer import EncodingSafeOutputHandler

        handler = EncodingSafeOutputHandler()
        handler.safe_print("Hello world")
        captured = capsys.readouterr()
        assert "Hello world" in captured.out

    def test_safe_print_unicode_fallback(self, capsys):
        """safe_print handles encoding errors gracefully."""
        from src.tools.performance_optimizer import EncodingSafeOutputHandler

        handler = EncodingSafeOutputHandler()
        # This should work without raising
        handler.safe_print("Unicode: 💓 ✅ ❌")

    def test_format_progress_percentage(self):
        """format_progress calculates correct percentage."""
        from src.tools.performance_optimizer import EncodingSafeOutputHandler

        handler = EncodingSafeOutputHandler()
        result = handler.format_progress(50, 100, "Test")
        assert "50" in result
        assert "100" in result
        assert "50.0%" in result

    def test_format_progress_zero_total(self):
        """format_progress handles zero total."""
        from src.tools.performance_optimizer import EncodingSafeOutputHandler

        handler = EncodingSafeOutputHandler()
        result = handler.format_progress(0, 0, "Test")
        assert "0.0%" in result


class TestSubprocessOptimizer:
    """Test SubprocessOptimizer class."""

    def test_init(self):
        """Verify initialization."""
        from src.tools.performance_optimizer import SubprocessOptimizer

        optimizer = SubprocessOptimizer()
        assert optimizer.process_count == 0
        assert optimizer.performance_metrics == {}

    def test_run_with_progress_success(self):
        """run_with_progress executes command successfully."""
        from src.tools.performance_optimizer import SubprocessOptimizer

        optimizer = SubprocessOptimizer()
        result = optimizer.run_with_progress(["python", "--version"], show_progress=False)
        assert result.returncode == 0
        assert optimizer.process_count == 1

    def test_run_with_progress_tracks_metrics(self):
        """run_with_progress tracks performance metrics."""
        from src.tools.performance_optimizer import SubprocessOptimizer

        optimizer = SubprocessOptimizer()
        optimizer.run_with_progress(["python", "--version"], show_progress=False)

        assert 1 in optimizer.performance_metrics
        metrics = optimizer.performance_metrics[1]
        assert "elapsed" in metrics
        assert "returncode" in metrics
        assert "stdout_length" in metrics

    def test_run_with_progress_timeout(self):
        """run_with_progress raises on timeout."""
        from src.tools.performance_optimizer import SubprocessOptimizer

        optimizer = SubprocessOptimizer()
        with pytest.raises(subprocess.TimeoutExpired):
            # This should timeout quickly
            optimizer.run_with_progress(
                ["python", "-c", "import time; time.sleep(10)"],
                timeout=1,
                show_progress=False,
            )

    def test_get_performance_summary_empty(self):
        """get_performance_summary handles empty metrics."""
        from src.tools.performance_optimizer import SubprocessOptimizer

        optimizer = SubprocessOptimizer()
        summary = optimizer.get_performance_summary()
        assert summary["message"] == "No processes executed yet"

    def test_get_performance_summary_with_metrics(self):
        """get_performance_summary calculates statistics."""
        from src.tools.performance_optimizer import SubprocessOptimizer

        optimizer = SubprocessOptimizer()
        optimizer.run_with_progress(["python", "--version"], show_progress=False)
        optimizer.run_with_progress(["python", "-c", "pass"], show_progress=False)

        summary = optimizer.get_performance_summary()
        assert summary["total_processes"] == 2
        assert "total_time" in summary
        assert "average_time" in summary
        assert "success_rate" in summary
        assert "fastest" in summary
        assert "slowest" in summary


class TestOptimizeForLargeRepositories:
    """Test optimize_for_large_repositories function."""

    def test_returns_recommendations(self):
        """Function returns optimization recommendations."""
        from src.tools.performance_optimizer import optimize_for_large_repositories

        result = optimize_for_large_repositories()
        assert "recommended_max_depth" in result
        assert "recommended_max_files" in result
        assert "skip_directories" in result
        assert ".git" in result["skip_directories"]
        assert "batch_size" in result

    def test_accepts_custom_params(self):
        """Function accepts custom parameters."""
        from src.tools.performance_optimizer import optimize_for_large_repositories

        result = optimize_for_large_repositories(max_files=500, max_depth=5)
        assert result["recommended_max_files"] == 500
        assert result["recommended_max_depth"] == 5


# ==============================================================================
# token_metrics_dashboard.py tests
# ==============================================================================
class TestTokenMetrics:
    """Test TokenMetrics dataclass."""

    def test_to_dict(self):
        """to_dict returns proper dictionary."""
        from src.tools.token_metrics_dashboard import TokenMetrics

        metric = TokenMetrics(
            timestamp="2025-01-01T00:00:00",
            original_tokens=1000,
            sns_tokens=600,
            savings_pct=40.0,
            operation="test",
            mode="normal",
        )

        result = metric.to_dict()
        assert result["timestamp"] == "2025-01-01T00:00:00"
        assert result["original_tokens"] == 1000
        assert result["sns_tokens"] == 600
        assert result["savings_pct"] == 40.0


class TestTokenMetricsDashboard:
    """Test TokenMetricsDashboard class."""

    def test_init_creates_directory(self, tmp_path: Path):
        """Init creates state directory."""
        from src.tools.token_metrics_dashboard import TokenMetricsDashboard

        state_dir = tmp_path / "state"
        dashboard = TokenMetricsDashboard(state_dir=state_dir)
        assert state_dir.exists()
        assert dashboard.report_dir.exists()
        assert dashboard.metrics_file == state_dir / "token_metrics.jsonl"

    def test_record_conversion(self, tmp_path: Path):
        """record_conversion saves metric to file."""
        from src.tools.token_metrics_dashboard import TokenMetricsDashboard

        dashboard = TokenMetricsDashboard(state_dir=tmp_path)
        dashboard.record_conversion(
            original_tokens=1000,
            sns_tokens=600,
            operation="test",
            mode="normal",
        )

        assert dashboard.metrics_file.exists()
        content = dashboard.metrics_file.read_text()
        data = json.loads(content.strip())
        assert data["original_tokens"] == 1000
        assert data["savings_pct"] == 40.0
        assert dashboard.report_summary_file.exists()
        assert dashboard.compatibility_summary_file.exists()

    def test_get_summary_empty(self, tmp_path: Path):
        """get_summary returns empty template when no metrics."""
        from src.tools.token_metrics_dashboard import TokenMetricsDashboard

        dashboard = TokenMetricsDashboard(state_dir=tmp_path)
        summary = dashboard.get_summary()

        assert summary["metrics_count"] == 0
        assert summary["total_original_tokens"] == 0

    def test_get_summary_with_metrics(self, tmp_path: Path):
        """get_summary calculates statistics from metrics."""
        from src.tools.token_metrics_dashboard import TokenMetricsDashboard

        dashboard = TokenMetricsDashboard(state_dir=tmp_path)
        dashboard.record_conversion(1000, 600, "op1", "normal")
        dashboard.record_conversion(500, 300, "op2", "aggressive")

        summary = dashboard.get_summary(hours=24)
        assert summary["metrics_count"] == 2
        assert summary["total_original_tokens"] == 1500
        assert summary["total_sns_tokens"] == 900
        assert summary["total_savings_tokens"] == 600

    def test_estimate_cost_savings(self, tmp_path: Path):
        """_estimate_cost_savings calculates USD savings."""
        from src.tools.token_metrics_dashboard import TokenMetricsDashboard

        dashboard = TokenMetricsDashboard(state_dir=tmp_path)
        result = dashboard._estimate_cost_savings(10000, 6000)
        # Savings: 4000 tokens * $0.03/1K = $0.12
        assert result == "$0.12"

    def test_save_summary(self, tmp_path: Path):
        """save_summary writes to file."""
        from src.tools.token_metrics_dashboard import TokenMetricsDashboard

        dashboard = TokenMetricsDashboard(state_dir=tmp_path)
        dashboard.record_conversion(1000, 600, "test")
        dashboard.save_summary()

        assert dashboard.summary_file.exists()
        assert dashboard.report_summary_file.exists()
        assert dashboard.compatibility_summary_file.exists()
        data = json.loads(dashboard.summary_file.read_text())
        assert "metrics_count" in data
        compatibility_data = json.loads(dashboard.compatibility_summary_file.read_text())
        assert compatibility_data["source"] == "token_metrics_dashboard"
        assert "summary" in compatibility_data

    def test_format_dashboard(self, tmp_path: Path):
        """format_dashboard returns formatted string."""
        from src.tools.token_metrics_dashboard import TokenMetricsDashboard

        dashboard = TokenMetricsDashboard(state_dir=tmp_path)
        dashboard.record_conversion(1000, 600, "test")

        output = dashboard.format_dashboard()
        assert "Token Metrics Dashboard" in output
        assert "Token Usage" in output
        assert "Savings" in output

    def test_get_leaderboard_empty(self, tmp_path: Path):
        """get_leaderboard returns empty list when no metrics."""
        from src.tools.token_metrics_dashboard import TokenMetricsDashboard

        dashboard = TokenMetricsDashboard(state_dir=tmp_path)
        result = dashboard.get_leaderboard()
        assert result == []

    def test_get_leaderboard_sorted(self, tmp_path: Path):
        """get_leaderboard returns sorted results."""
        from src.tools.token_metrics_dashboard import TokenMetricsDashboard

        dashboard = TokenMetricsDashboard(state_dir=tmp_path)
        dashboard.record_conversion(100, 90, "low_savings")  # 10% savings
        dashboard.record_conversion(100, 50, "high_savings")  # 50% savings
        dashboard.record_conversion(100, 70, "med_savings")  # 30% savings

        leaderboard = dashboard.get_leaderboard(metric="savings_pct", limit=3)
        assert len(leaderboard) == 3
        assert leaderboard[0]["operation"] == "high_savings"
        assert leaderboard[1]["operation"] == "med_savings"
        assert leaderboard[2]["operation"] == "low_savings"

    def test_record_conversion_zero_original(self, tmp_path: Path):
        """record_conversion handles zero original tokens."""
        from src.tools.token_metrics_dashboard import TokenMetricsDashboard

        dashboard = TokenMetricsDashboard(state_dir=tmp_path)
        dashboard.record_conversion(0, 0, "zero_test")

        content = dashboard.metrics_file.read_text()
        data = json.loads(content.strip())
        assert data["savings_pct"] == 0.0
