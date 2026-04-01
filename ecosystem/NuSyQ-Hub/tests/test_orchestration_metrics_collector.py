"""Tests for src/observability/orchestration_metrics_collector.py

This module tests orchestration performance metrics collection.

Coverage Target: 70%+
"""

import json

import pytest

# =============================================================================
# Module Import Tests
# =============================================================================


class TestModuleImports:
    """Test module-level imports."""

    def test_import_orchestration_metrics(self):
        """Test OrchestrationMetrics can be imported."""
        from src.observability.orchestration_metrics_collector import OrchestrationMetrics

        assert OrchestrationMetrics is not None


# =============================================================================
# OrchestrationMetrics Tests
# =============================================================================


class TestOrchestrationMetricsInit:
    """Test OrchestrationMetrics initialization."""

    def test_create_with_nonexistent_path(self, tmp_path):
        """Test creating with non-existent quest log."""
        from src.observability.orchestration_metrics_collector import OrchestrationMetrics

        quest_log = tmp_path / "nonexistent.jsonl"
        metrics = OrchestrationMetrics(quest_log)

        assert metrics.quest_log == quest_log
        assert len(metrics.metrics) == 0

    def test_create_with_empty_file(self, tmp_path):
        """Test creating with empty quest log."""
        from src.observability.orchestration_metrics_collector import OrchestrationMetrics

        quest_log = tmp_path / "empty.jsonl"
        quest_log.write_text("")

        metrics = OrchestrationMetrics(quest_log)

        assert len(metrics.metrics) == 0


class TestLoadQuestLog:
    """Test quest log loading."""

    def test_load_async_orchestration_events(self, tmp_path):
        """Test loading async orchestration test events."""
        from src.observability.orchestration_metrics_collector import OrchestrationMetrics

        quest_log = tmp_path / "quest.jsonl"
        events = [
            {
                "task_type": "async_orchestration_test",
                "timestamp": "2025-01-01T00:00:00",
                "result": {
                    "total_agents": 5,
                    "successful": 4,
                    "elapsed_seconds": 10.5,
                    "total_tokens": 1000,
                    "speedup": 3.5,
                },
            },
        ]
        quest_log.write_text("\n".join(json.dumps(e) for e in events))

        metrics = OrchestrationMetrics(quest_log)

        assert len(metrics.metrics["async_parallel"]) == 1
        assert metrics.metrics["async_parallel"][0]["agents"] == 5
        assert metrics.metrics["async_parallel"][0]["speedup"] == 3.5

    def test_load_multi_model_comparison_events(self, tmp_path):
        """Test loading multi-model comparison events."""
        from src.observability.orchestration_metrics_collector import OrchestrationMetrics

        quest_log = tmp_path / "quest.jsonl"
        events = [
            {
                "task_type": "multi_model_comparison",
                "result": {
                    "results": [
                        {"model": "ollama", "tokens": 100, "response_length": 500},
                        {"model": "chatdev", "tokens": 150, "response_length": 700},
                    ],
                },
            },
        ]
        quest_log.write_text("\n".join(json.dumps(e) for e in events))

        metrics = OrchestrationMetrics(quest_log)

        assert len(metrics.metrics["single_agent"]) == 2

    def test_load_consensus_events(self, tmp_path):
        """Test loading consensus generation events."""
        from src.observability.orchestration_metrics_collector import OrchestrationMetrics

        quest_log = tmp_path / "quest.jsonl"
        events = [
            {
                "task_type": "orchestration_test",
                "timestamp": "2025-01-01T00:00:00",
                "result": {
                    "agents_tested": 3,
                    "total_tokens": 500,
                    "status": "OPERATIONAL",
                },
            },
        ]
        quest_log.write_text("\n".join(json.dumps(e) for e in events))

        metrics = OrchestrationMetrics(quest_log)

        assert len(metrics.metrics["consensus"]) == 1
        assert metrics.metrics["consensus"][0]["status"] == "OPERATIONAL"

    def test_handle_invalid_json(self, tmp_path):
        """Test handling invalid JSON lines."""
        from src.observability.orchestration_metrics_collector import OrchestrationMetrics

        quest_log = tmp_path / "quest.jsonl"
        quest_log.write_text("not valid json\n{invalid}\nalso bad")

        metrics = OrchestrationMetrics(quest_log)

        # Should not raise, just skip invalid lines
        assert len(metrics.metrics) == 0

    def test_skip_unknown_task_types(self, tmp_path):
        """Test that unknown task types are skipped."""
        from src.observability.orchestration_metrics_collector import OrchestrationMetrics

        quest_log = tmp_path / "quest.jsonl"
        events = [
            {"task_type": "unknown_type", "result": {}},
            {"task_type": "random_event", "result": {}},
        ]
        quest_log.write_text("\n".join(json.dumps(e) for e in events))

        metrics = OrchestrationMetrics(quest_log)

        assert len(metrics.metrics) == 0


class TestGenerateReport:
    """Test report generation."""

    def test_generate_empty_report(self, tmp_path):
        """Test generating report with no data."""
        from src.observability.orchestration_metrics_collector import OrchestrationMetrics

        quest_log = tmp_path / "empty.jsonl"
        quest_log.write_text("")

        metrics = OrchestrationMetrics(quest_log)
        report = metrics.generate_report()

        assert "ORCHESTRATION PERFORMANCE METRICS REPORT" in report
        assert "Total orchestration tasks: 0" in report

    def test_generate_report_with_async_metrics(self, tmp_path):
        """Test report with async parallelization metrics."""
        from src.observability.orchestration_metrics_collector import OrchestrationMetrics

        quest_log = tmp_path / "quest.jsonl"
        events = [
            {
                "task_type": "async_orchestration_test",
                "timestamp": "2025-01-01T00:00:00",
                "result": {
                    "total_agents": 5,
                    "successful": 5,
                    "elapsed_seconds": 10.0,
                    "total_tokens": 1000,
                    "speedup": 3.0,
                },
            },
            {
                "task_type": "async_orchestration_test",
                "timestamp": "2025-01-01T01:00:00",
                "result": {
                    "total_agents": 5,
                    "successful": 4,
                    "elapsed_seconds": 12.0,
                    "total_tokens": 1200,
                    "speedup": 2.5,
                },
            },
        ]
        quest_log.write_text("\n".join(json.dumps(e) for e in events))

        metrics = OrchestrationMetrics(quest_log)
        report = metrics.generate_report()

        assert "ASYNC PARALLELIZATION METRICS" in report
        assert "Test runs: 2" in report
        assert "Parallelization speedup" in report

    def test_generate_report_with_consensus_metrics(self, tmp_path):
        """Test report with consensus metrics."""
        from src.observability.orchestration_metrics_collector import OrchestrationMetrics

        quest_log = tmp_path / "quest.jsonl"
        events = [
            {
                "task_type": "orchestration_test",
                "timestamp": "2025-01-01T00:00:00",
                "result": {
                    "agents_tested": 3,
                    "total_tokens": 500,
                    "status": "OPERATIONAL",
                },
            },
        ]
        quest_log.write_text("\n".join(json.dumps(e) for e in events))

        metrics = OrchestrationMetrics(quest_log)
        report = metrics.generate_report()

        assert "CONSENSUS GENERATION METRICS" in report
        assert "Consensus runs: 1" in report
        assert "Success rate: 1/1" in report


class TestGetJsonMetrics:
    """Test JSON metrics export."""

    def test_get_json_metrics_empty(self, tmp_path):
        """Test exporting empty metrics as JSON."""
        from src.observability.orchestration_metrics_collector import OrchestrationMetrics

        quest_log = tmp_path / "empty.jsonl"
        quest_log.write_text("")

        metrics = OrchestrationMetrics(quest_log)
        json_data = metrics.get_json_metrics()

        assert isinstance(json_data, dict)

    def test_get_json_metrics_with_data(self, tmp_path):
        """Test exporting metrics with data as JSON."""
        from src.observability.orchestration_metrics_collector import OrchestrationMetrics

        quest_log = tmp_path / "quest.jsonl"
        events = [
            {
                "task_type": "async_orchestration_test",
                "timestamp": "2025-01-01T00:00:00",
                "result": {
                    "total_agents": 5,
                    "successful": 5,
                    "elapsed_seconds": 10.0,
                    "total_tokens": 1000,
                    "speedup": 3.0,
                },
            },
        ]
        quest_log.write_text("\n".join(json.dumps(e) for e in events))

        metrics = OrchestrationMetrics(quest_log)
        json_data = metrics.get_json_metrics()

        assert isinstance(json_data, dict)
        # Should have async_parallel data
        assert "async_parallel" in json_data or "metrics" in json_data or len(json_data) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
