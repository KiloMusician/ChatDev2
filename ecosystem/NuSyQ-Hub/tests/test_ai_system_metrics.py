"""Tests for src/system/ai_metrics_tracker.py and src/system/ai_health_probe.py."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.system.ai_health_probe import (
    AIHealthReport,
    HealthStatus,
    gate_on_health,
    save_health_report,
)
from src.system.ai_metrics_tracker import (
    AIHealthMetric,
    AIMetricsTracker,
    DispatchProfileMetric,
    GateDecision,
    generate_metrics_report,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_health_status(
    name: str = "TestSystem",
    available: bool = True,
    **kwargs,
) -> HealthStatus:
    return HealthStatus(name=name, available=available, **kwargs)


def _make_report(
    ollama_avail: bool = True,
    chatdev_avail: bool = True,
    quantum_avail: bool = True,
) -> AIHealthReport:
    n_available = sum([ollama_avail, chatdev_avail, quantum_avail])
    return AIHealthReport(
        ollama=_make_health_status("Ollama", ollama_avail),
        chatdev=_make_health_status("ChatDev", chatdev_avail),
        quantum=_make_health_status("Quantum", quantum_avail),
        timestamp="2026-01-01T00:00:00",
        overall_score=n_available / 3.0,
    )


# ---------------------------------------------------------------------------
# Package import smoke tests
# ---------------------------------------------------------------------------

class TestPackageImports:
    """Verify that all public symbols can be imported."""

    def test_import_ai_metrics_tracker(self) -> None:
        import src.system.ai_metrics_tracker as m

        assert hasattr(m, "AIMetricsTracker")
        assert hasattr(m, "AIHealthMetric")
        assert hasattr(m, "GateDecision")
        assert hasattr(m, "DispatchProfileMetric")
        assert hasattr(m, "generate_metrics_report")

    def test_import_ai_health_probe(self) -> None:
        import src.system.ai_health_probe as h

        assert hasattr(h, "HealthStatus")
        assert hasattr(h, "AIHealthReport")
        assert hasattr(h, "probe_ollama")
        assert hasattr(h, "probe_chatdev")
        assert hasattr(h, "probe_quantum")
        assert hasattr(h, "run_full_health_check")
        assert hasattr(h, "save_health_report")
        assert hasattr(h, "gate_on_health")


# ---------------------------------------------------------------------------
# Dataclass contracts — ai_metrics_tracker
# ---------------------------------------------------------------------------

class TestDataclassContracts:
    """Verify dataclass field presence and optional fields."""

    def test_ai_health_metric_required_fields(self) -> None:
        m = AIHealthMetric(
            timestamp="2026-01-01T00:00:00+00:00",
            system_name="ollama",
            available=True,
        )
        assert m.timestamp == "2026-01-01T00:00:00+00:00"
        assert m.system_name == "ollama"
        assert m.available is True
        assert m.latency_ms is None
        assert m.error is None
        assert m.metadata is None

    def test_ai_health_metric_optional_fields(self) -> None:
        m = AIHealthMetric(
            timestamp="2026-01-01T00:00:00+00:00",
            system_name="ollama",
            available=False,
            latency_ms=42.5,
            error="connection refused",
            metadata={"key": "value"},
        )
        assert m.latency_ms == 42.5
        assert m.error == "connection refused"
        assert m.metadata == {"key": "value"}

    def test_gate_decision_required_fields(self) -> None:
        d = GateDecision(
            timestamp="2026-01-01T00:00:00+00:00",
            gate_status="open",
            ai_systems_available=2,
            ai_systems_total=3,
        )
        assert d.gate_status == "open"
        assert d.ai_systems_available == 2
        assert d.ai_systems_total == 3
        assert d.hygiene_status is None
        assert d.quests_available is None
        assert d.reason is None

    def test_dispatch_profile_metric_fields(self) -> None:
        dp = DispatchProfileMetric(
            timestamp="2026-01-01T00:00:00+00:00",
            system_name="ollama",
            mode="balanced",
            risk_level="low",
            signal_budget="normal",
            status="ok",
            non_blocking=True,
        )
        assert dp.mode == "balanced"
        assert dp.risk_level == "low"
        assert dp.non_blocking is True
        assert dp.metadata is None

    def test_health_status_required_fields(self) -> None:
        hs = HealthStatus(name="Ollama", available=True)
        assert hs.name == "Ollama"
        assert hs.available is True
        assert hs.version is None
        assert hs.endpoint is None
        assert hs.latency_ms is None
        assert hs.error is None
        assert hs.metadata is None

    def test_health_status_to_dict(self) -> None:
        hs = HealthStatus(
            name="Ollama",
            available=True,
            version="0.1.0",
            endpoint="http://localhost:11434",
            latency_ms=10.5,
            metadata={"models_count": 3},
        )
        d = hs.to_dict()
        assert d["name"] == "Ollama"
        assert d["available"] is True
        assert d["version"] == "0.1.0"
        assert d["latency_ms"] == 10.5
        assert d["metadata"] == {"models_count": 3}

    def test_health_status_to_dict_none_metadata_becomes_empty(self) -> None:
        hs = HealthStatus(name="X", available=False)
        assert hs.to_dict()["metadata"] == {}


# ---------------------------------------------------------------------------
# AIMetricsTracker — initialization & file paths
# ---------------------------------------------------------------------------

class TestAIMetricsTrackerInit:
    """Verify tracker init creates directories and sets correct paths."""

    def test_init_creates_metrics_dir(self, tmp_path: Path) -> None:
        tracker = AIMetricsTracker(repo_root=tmp_path)
        assert tracker.metrics_dir.exists()
        assert tracker.metrics_dir == tmp_path / "state" / "metrics"

    def test_init_health_file_path(self, tmp_path: Path) -> None:
        tracker = AIMetricsTracker(repo_root=tmp_path)
        assert tracker.health_file == tmp_path / "state" / "metrics" / "ai_health_history.jsonl"

    def test_init_gate_file_path(self, tmp_path: Path) -> None:
        tracker = AIMetricsTracker(repo_root=tmp_path)
        assert tracker.gate_file == tmp_path / "state" / "metrics" / "gate_decisions.jsonl"

    def test_init_dispatch_profile_file_path(self, tmp_path: Path) -> None:
        tracker = AIMetricsTracker(repo_root=tmp_path)
        assert tracker.dispatch_profile_file == (
            tmp_path / "state" / "metrics" / "dispatch_profile_history.jsonl"
        )


# ---------------------------------------------------------------------------
# AIMetricsTracker — record_health
# ---------------------------------------------------------------------------

class TestRecordHealth:
    """Test record_health writes valid JSONL entries."""

    def test_record_health_creates_file(self, tmp_path: Path) -> None:
        tracker = AIMetricsTracker(repo_root=tmp_path)
        tracker.record_health("ollama", available=True)
        assert tracker.health_file.exists()

    def test_record_health_jsonl_valid(self, tmp_path: Path) -> None:
        tracker = AIMetricsTracker(repo_root=tmp_path)
        tracker.record_health("chatdev", available=False, error="offline")
        lines = tracker.health_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        row = json.loads(lines[0])
        assert row["system_name"] == "chatdev"
        assert row["available"] is False
        assert row["error"] == "offline"

    def test_record_health_multiple_appends(self, tmp_path: Path) -> None:
        tracker = AIMetricsTracker(repo_root=tmp_path)
        tracker.record_health("a", available=True)
        tracker.record_health("b", available=True)
        tracker.record_health("c", available=False)
        lines = tracker.health_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 3

    def test_record_health_with_latency_and_metadata(self, tmp_path: Path) -> None:
        tracker = AIMetricsTracker(repo_root=tmp_path)
        tracker.record_health("quantum", available=True, latency_ms=12.3, metadata={"x": 1})
        row = json.loads(tracker.health_file.read_text(encoding="utf-8").strip())
        assert row["latency_ms"] == pytest.approx(12.3)
        assert row["metadata"] == {"x": 1}


# ---------------------------------------------------------------------------
# AIMetricsTracker — record_gate_decision
# ---------------------------------------------------------------------------

class TestRecordGateDecision:
    """Test record_gate_decision writes valid JSONL entries."""

    def test_record_gate_decision_creates_file(self, tmp_path: Path) -> None:
        tracker = AIMetricsTracker(repo_root=tmp_path)
        tracker.record_gate_decision("open", 2, 3)
        assert tracker.gate_file.exists()

    def test_record_gate_decision_fields(self, tmp_path: Path) -> None:
        tracker = AIMetricsTracker(repo_root=tmp_path)
        tracker.record_gate_decision(
            "closed", 0, 3, hygiene_status="dirty", quests_available=False, reason="no systems"
        )
        row = json.loads(tracker.gate_file.read_text(encoding="utf-8").strip())
        assert row["gate_status"] == "closed"
        assert row["ai_systems_available"] == 0
        assert row["ai_systems_total"] == 3
        assert row["hygiene_status"] == "dirty"
        assert row["quests_available"] is False
        assert row["reason"] == "no systems"


# ---------------------------------------------------------------------------
# AIMetricsTracker — record_dispatch_profile
# ---------------------------------------------------------------------------

class TestRecordDispatchProfile:
    """Test record_dispatch_profile writes valid JSONL entries."""

    def test_record_dispatch_profile_creates_file(self, tmp_path: Path) -> None:
        tracker = AIMetricsTracker(repo_root=tmp_path)
        tracker.record_dispatch_profile("ollama", "balanced", "low", "normal", "ok", False)
        assert tracker.dispatch_profile_file.exists()

    def test_record_dispatch_profile_fields(self, tmp_path: Path) -> None:
        tracker = AIMetricsTracker(repo_root=tmp_path)
        tracker.record_dispatch_profile(
            "ollama", "aggressive", "high", "large", "success", True, metadata={"t": 2}
        )
        row = json.loads(tracker.dispatch_profile_file.read_text(encoding="utf-8").strip())
        assert row["system_name"] == "ollama"
        assert row["mode"] == "aggressive"
        assert row["risk_level"] == "high"
        assert row["non_blocking"] is True
        assert row["metadata"] == {"t": 2}


# ---------------------------------------------------------------------------
# AIMetricsTracker — get_uptime_stats
# ---------------------------------------------------------------------------

class TestGetUptimeStats:
    """Test get_uptime_stats returns correct aggregates."""

    def test_returns_empty_when_no_file(self, tmp_path: Path) -> None:
        tracker = AIMetricsTracker(repo_root=tmp_path)
        assert tracker.get_uptime_stats() == {}

    def test_uptime_stats_aggregates(self, tmp_path: Path) -> None:
        tracker = AIMetricsTracker(repo_root=tmp_path)
        tracker.record_health("ollama", available=True, latency_ms=10.0)
        tracker.record_health("ollama", available=True, latency_ms=20.0)
        tracker.record_health("ollama", available=False)
        stats = tracker.get_uptime_stats()
        assert "ollama" in stats
        s = stats["ollama"]
        assert s["total_checks"] == 3
        assert s["available_checks"] == 2
        assert s["uptime_percent"] == pytest.approx(200 / 3)
        assert s["avg_latency_ms"] == pytest.approx(15.0)


# ---------------------------------------------------------------------------
# AIMetricsTracker — get_gate_stats
# ---------------------------------------------------------------------------

class TestGetGateStats:
    """Test get_gate_stats returns correct aggregates."""

    def test_returns_zero_counts_when_no_file(self, tmp_path: Path) -> None:
        tracker = AIMetricsTracker(repo_root=tmp_path)
        stats = tracker.get_gate_stats()
        assert stats["total_decisions"] == 0
        assert stats["open_count"] == 0
        assert stats["closed_count"] == 0

    def test_gate_stats_open_closed_counts(self, tmp_path: Path) -> None:
        tracker = AIMetricsTracker(repo_root=tmp_path)
        tracker.record_gate_decision("open", 3, 3, reason="all good")
        tracker.record_gate_decision("open", 2, 3, reason="all good")
        tracker.record_gate_decision("closed", 0, 3, reason="no systems")
        stats = tracker.get_gate_stats()
        assert stats["total_decisions"] == 3
        assert stats["open_count"] == 2
        assert stats["closed_count"] == 1
        assert stats["open_rate_percent"] == pytest.approx(200 / 3)
        assert stats["reasons"]["all good"] == 2
        assert stats["reasons"]["no systems"] == 1


# ---------------------------------------------------------------------------
# AIMetricsTracker — get_dispatch_profile_stats
# ---------------------------------------------------------------------------

class TestGetDispatchProfileStats:
    """Test get_dispatch_profile_stats returns correct aggregates."""

    def test_returns_defaults_when_no_file(self, tmp_path: Path) -> None:
        tracker = AIMetricsTracker(repo_root=tmp_path)
        stats = tracker.get_dispatch_profile_stats()
        assert stats["total_dispatches"] == 0
        assert stats["non_blocking_count"] == 0
        assert stats["blocking_count"] == 0

    def test_dispatch_stats_counts(self, tmp_path: Path) -> None:
        tracker = AIMetricsTracker(repo_root=tmp_path)
        tracker.record_dispatch_profile("ollama", "balanced", "low", "normal", "ok", True)
        tracker.record_dispatch_profile("chatdev", "aggressive", "high", "large", "ok", False)
        stats = tracker.get_dispatch_profile_stats()
        assert stats["total_dispatches"] == 2
        assert stats["non_blocking_count"] == 1
        assert stats["blocking_count"] == 1
        assert stats["by_system"]["ollama"] == 1
        assert stats["by_system"]["chatdev"] == 1
        assert stats["non_blocking_rate_percent"] == pytest.approx(50.0)


# ---------------------------------------------------------------------------
# generate_metrics_report
# ---------------------------------------------------------------------------

class TestGenerateMetricsReport:
    """Test generate_metrics_report produces a non-empty string."""

    def test_report_is_string(self, tmp_path: Path) -> None:
        report = generate_metrics_report(repo_root=tmp_path)
        assert isinstance(report, str)
        assert len(report) > 0

    def test_report_contains_sections(self, tmp_path: Path) -> None:
        tracker = AIMetricsTracker(repo_root=tmp_path)
        tracker.record_health("ollama", available=True)
        tracker.record_gate_decision("open", 1, 1)
        report = generate_metrics_report(repo_root=tmp_path)
        assert "AI System Uptime" in report
        assert "Work Gate Decisions" in report
        assert "Dispatch Profile" in report


# ---------------------------------------------------------------------------
# AIHealthReport — methods
# ---------------------------------------------------------------------------

class TestAIHealthReport:
    """Test AIHealthReport helper methods."""

    def test_is_healthy_above_threshold(self) -> None:
        report = _make_report(True, True, True)
        assert report.is_healthy(min_score=0.66) is True

    def test_is_healthy_below_threshold(self) -> None:
        report = _make_report(False, False, True)
        assert report.is_healthy(min_score=0.66) is False

    def test_get_available_systems(self) -> None:
        report = _make_report(True, False, True)
        available = report.get_available_systems()
        assert "ollama" in available
        assert "quantum" in available
        assert "chatdev" not in available

    def test_get_unavailable_systems(self) -> None:
        report = _make_report(True, False, False)
        unavailable = report.get_unavailable_systems()
        assert "chatdev" in unavailable
        assert "quantum" in unavailable
        assert "ollama" not in unavailable

    def test_to_dict_structure(self) -> None:
        report = _make_report(True, True, False)
        d = report.to_dict()
        assert "ollama" in d
        assert "chatdev" in d
        assert "quantum" in d
        assert "timestamp" in d
        assert "overall_score" in d

    def test_overall_score_all_available(self) -> None:
        report = _make_report(True, True, True)
        assert report.overall_score == pytest.approx(1.0)

    def test_overall_score_none_available(self) -> None:
        report = _make_report(False, False, False)
        assert report.overall_score == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# gate_on_health
# ---------------------------------------------------------------------------

class TestGateOnHealth:
    """Test gate_on_health logic."""

    def test_gate_passes_above_min_score(self) -> None:
        report = _make_report(True, True, True)
        assert gate_on_health(report, min_score=0.66) is True

    def test_gate_fails_below_min_score(self) -> None:
        report = _make_report(False, False, False)
        assert gate_on_health(report, min_score=0.66) is False

    def test_gate_passes_required_systems_present(self) -> None:
        report = _make_report(True, False, False)
        assert gate_on_health(report, required_systems=["ollama"]) is True

    def test_gate_fails_required_systems_missing(self) -> None:
        report = _make_report(False, False, False)
        assert gate_on_health(report, required_systems=["ollama"]) is False


# ---------------------------------------------------------------------------
# save_health_report
# ---------------------------------------------------------------------------

class TestSaveHealthReport:
    """Test save_health_report writes correct JSON to disk."""

    def test_save_creates_file(self, tmp_path: Path) -> None:
        report = _make_report(True, False, True)
        out = tmp_path / "health.json"
        save_health_report(report, out)
        assert out.exists()

    def test_save_content_is_valid_json(self, tmp_path: Path) -> None:
        report = _make_report(True, True, False)
        out = tmp_path / "health.json"
        save_health_report(report, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "overall_score" in data
        assert "timestamp" in data

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        report = _make_report()
        nested = tmp_path / "a" / "b" / "c" / "report.json"
        save_health_report(report, nested)
        assert nested.exists()


# ---------------------------------------------------------------------------
# probe_* functions — mocked (no live network/subprocess)
# ---------------------------------------------------------------------------

class TestProbesMocked:
    """Probe functions tested with mocked subprocess / imports."""

    def test_probe_ollama_not_found(self) -> None:
        from src.system.ai_health_probe import probe_ollama

        with patch("subprocess.run", side_effect=FileNotFoundError):
            status = probe_ollama(timeout=1)
        assert status.available is False
        assert "not found" in (status.error or "").lower()

    def test_probe_ollama_timeout(self) -> None:
        import subprocess

        from src.system.ai_health_probe import probe_ollama

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("ollama", 1)):
            status = probe_ollama(timeout=1)
        assert status.available is False
        assert "timeout" in (status.error or "").lower()

    def test_probe_chatdev_missing_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from src.system.ai_health_probe import probe_chatdev

        # Ensure CWD has no ChatDev dir
        monkeypatch.chdir(tmp_path)
        status = probe_chatdev(timeout=1)
        assert status.available is False
        assert "ChatDev" in (status.error or "")

    def test_probe_quantum_returns_health_status(self) -> None:
        from src.system.ai_health_probe import probe_quantum

        status = probe_quantum(timeout=1)
        # Result type must always be HealthStatus regardless of availability
        assert isinstance(status, HealthStatus)
        assert status.name == "Quantum"
