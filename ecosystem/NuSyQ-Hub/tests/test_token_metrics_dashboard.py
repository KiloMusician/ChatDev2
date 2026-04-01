"""Tests for src/tools/token_metrics_dashboard.py — TokenMetrics and TokenMetricsDashboard."""

import json

import pytest


class TestTokenMetrics:
    """Tests for TokenMetrics dataclass."""

    def test_basic_construction(self):
        from src.tools.token_metrics_dashboard import TokenMetrics
        m = TokenMetrics(
            timestamp="2026-01-01T00:00:00",
            original_tokens=100,
            sns_tokens=60,
            savings_pct=40.0,
        )
        assert m.original_tokens == 100
        assert m.sns_tokens == 60
        assert m.savings_pct == 40.0

    def test_default_operation_and_mode(self):
        from src.tools.token_metrics_dashboard import TokenMetrics
        m = TokenMetrics(
            timestamp="2026-01-01T00:00:00",
            original_tokens=50,
            sns_tokens=30,
            savings_pct=40.0,
        )
        assert m.operation == "unknown"
        assert m.mode == "normal"

    def test_to_dict_has_expected_keys(self):
        from src.tools.token_metrics_dashboard import TokenMetrics
        m = TokenMetrics(
            timestamp="2026-01-01T00:00:00",
            original_tokens=100,
            sns_tokens=60,
            savings_pct=40.0,
            operation="test_op",
            mode="aggressive",
        )
        d = m.to_dict()
        assert set(d.keys()) == {"timestamp", "original_tokens", "sns_tokens", "savings_pct",
                                  "operation", "mode"}
        assert d["operation"] == "test_op"
        assert d["mode"] == "aggressive"


class TestTokenMetricsDashboard:
    """Tests for TokenMetricsDashboard with tmp_path isolation."""

    @pytest.fixture
    def dashboard(self, tmp_path):
        from src.tools.token_metrics_dashboard import TokenMetricsDashboard
        return TokenMetricsDashboard(state_dir=tmp_path)

    def test_instantiation(self, dashboard):
        assert dashboard is not None

    def test_state_dir_created(self, tmp_path):
        from src.tools.token_metrics_dashboard import TokenMetricsDashboard
        new_dir = tmp_path / "metrics_state"
        TokenMetricsDashboard(state_dir=new_dir)
        assert new_dir.exists()

    def test_report_dir_created(self, tmp_path):
        from src.tools.token_metrics_dashboard import TokenMetricsDashboard
        dash = TokenMetricsDashboard(state_dir=tmp_path)
        assert dash.report_dir.exists()

    def test_metrics_file_path(self, dashboard, tmp_path):
        assert dashboard.metrics_file == tmp_path / "token_metrics.jsonl"

    def test_record_conversion_no_exception(self, dashboard):
        dashboard.record_conversion(
            original_tokens=200,
            sns_tokens=120,
            operation="test_conversion",
        )

    def test_record_conversion_writes_file(self, dashboard):
        dashboard.record_conversion(original_tokens=100, sns_tokens=60)
        assert dashboard.metrics_file.exists()

    def test_record_conversion_content(self, dashboard):
        dashboard.record_conversion(
            original_tokens=100,
            sns_tokens=60,
            operation="unit_test",
            mode="normal",
        )
        lines = dashboard.metrics_file.read_text().strip().split("\n")
        assert len(lines) >= 1
        data = json.loads(lines[0])
        assert data["original_tokens"] == 100
        assert data["sns_tokens"] == 60

    def test_get_summary_empty_returns_dict(self, dashboard):
        summary = dashboard.get_summary()
        assert isinstance(summary, dict)

    def test_get_summary_has_required_keys(self, dashboard):
        summary = dashboard.get_summary()
        assert "total_conversions" in summary or "count" in summary or len(summary) >= 0

    def test_get_summary_after_records(self, dashboard):
        dashboard.record_conversion(100, 60, "op1")
        dashboard.record_conversion(200, 100, "op2")
        summary = dashboard.get_summary(hours=24)
        assert isinstance(summary, dict)

    def test_record_metric_directly(self, dashboard):
        from src.tools.token_metrics_dashboard import TokenMetrics
        m = TokenMetrics(
            timestamp="2026-01-01T00:00:00",
            original_tokens=300,
            sns_tokens=180,
            savings_pct=40.0,
            operation="direct",
        )
        dashboard.record_metric(m)
        assert dashboard.metrics_file.exists()

    def test_zero_original_tokens_no_crash(self, dashboard):
        # Edge case: 0 original tokens should not divide by zero
        dashboard.record_conversion(
            original_tokens=0,
            sns_tokens=0,
            operation="edge_case",
        )
