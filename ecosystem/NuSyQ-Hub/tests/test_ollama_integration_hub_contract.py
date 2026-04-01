"""Contract tests for legacy Ollama Integration Hub response envelopes."""

from __future__ import annotations

from src.integration.Ollama_Integration_Hub import PerformanceMonitor


def test_performance_monitor_insufficient_data_has_success_flag() -> None:
    monitor = PerformanceMonitor()
    result = monitor._calculate_trends()
    assert result["success"] is False
    assert result["status"] == "insufficient_data"
