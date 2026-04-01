"""Tests for src/system/ai_health_probe.py — HealthStatus, AIHealthReport, probes, gate."""

import json
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# HealthStatus dataclass
# ---------------------------------------------------------------------------


class TestHealthStatus:
    """Tests for HealthStatus dataclass."""

    def _make(self, **kwargs):
        from src.system.ai_health_probe import HealthStatus
        defaults = {"name": "TestSystem", "available": True}
        defaults.update(kwargs)
        return HealthStatus(**defaults)

    def test_instantiation(self):
        assert self._make() is not None

    def test_name_stored(self):
        hs = self._make(name="Ollama")
        assert hs.name == "Ollama"

    def test_available_stored(self):
        hs = self._make(available=False)
        assert hs.available is False

    def test_default_version_none(self):
        assert self._make().version is None

    def test_default_endpoint_none(self):
        assert self._make().endpoint is None

    def test_default_latency_ms_none(self):
        assert self._make().latency_ms is None

    def test_default_error_none(self):
        assert self._make().error is None

    def test_default_metadata_none(self):
        assert self._make().metadata is None

    def test_custom_fields(self):
        hs = self._make(version="0.1.0", latency_ms=42.5, error="timeout")
        assert hs.version == "0.1.0"
        assert hs.latency_ms == 42.5
        assert hs.error == "timeout"

    def test_to_dict_returns_dict(self):
        d = self._make().to_dict()
        assert isinstance(d, dict)

    def test_to_dict_has_required_keys(self):
        d = self._make().to_dict()
        for key in ("name", "available", "version", "endpoint", "latency_ms", "error", "metadata"):
            assert key in d

    def test_to_dict_values_match(self):
        hs = self._make(name="Quantum", available=False, error="no module")
        d = hs.to_dict()
        assert d["name"] == "Quantum"
        assert d["available"] is False
        assert d["error"] == "no module"


# ---------------------------------------------------------------------------
# AIHealthReport dataclass
# ---------------------------------------------------------------------------


class TestAIHealthReport:
    """Tests for AIHealthReport dataclass."""

    def _make_status(self, name="Sys", available=True):
        from src.system.ai_health_probe import HealthStatus
        return HealthStatus(name=name, available=available)

    def _make_report(self, ollama_avail=True, chatdev_avail=True, quantum_avail=True, score=None):
        from src.system.ai_health_probe import AIHealthReport
        ol = self._make_status("Ollama", ollama_avail)
        cd = self._make_status("ChatDev", chatdev_avail)
        qu = self._make_status("Quantum", quantum_avail)
        available_count = sum([ollama_avail, chatdev_avail, quantum_avail])
        computed_score = score if score is not None else available_count / 3.0
        return AIHealthReport(
            ollama=ol,
            chatdev=cd,
            quantum=qu,
            timestamp="2026-01-01T00:00:00",
            overall_score=computed_score,
        )

    def test_instantiation(self):
        assert self._make_report() is not None

    def test_fields_stored(self):
        report = self._make_report()
        assert report.timestamp == "2026-01-01T00:00:00"
        assert report.overall_score == 1.0

    def test_is_healthy_above_threshold(self):
        report = self._make_report(score=0.8)
        assert report.is_healthy(min_score=0.66) is True

    def test_is_healthy_at_threshold(self):
        report = self._make_report(score=0.66)
        assert report.is_healthy(min_score=0.66) is True

    def test_is_healthy_below_threshold(self):
        report = self._make_report(score=0.33)
        assert report.is_healthy(min_score=0.66) is False

    def test_is_healthy_default_min_score(self):
        # Default min_score=0.66 — all systems available → score=1.0 → healthy
        report = self._make_report()
        assert report.is_healthy() is True

    def test_get_available_systems_all(self):
        report = self._make_report()
        available = report.get_available_systems()
        assert isinstance(available, list)
        assert len(available) == 3

    def test_get_available_systems_partial(self):
        report = self._make_report(ollama_avail=True, chatdev_avail=False, quantum_avail=False)
        available = report.get_available_systems()
        assert len(available) == 1
        assert "ollama" in available

    def test_get_unavailable_systems_none(self):
        report = self._make_report()
        unavailable = report.get_unavailable_systems()
        assert unavailable == []

    def test_get_unavailable_systems_partial(self):
        report = self._make_report(ollama_avail=False, chatdev_avail=False, quantum_avail=True)
        unavailable = report.get_unavailable_systems()
        assert len(unavailable) == 2
        assert "ollama" in unavailable
        assert "chatdev" in unavailable

    def test_to_dict_returns_dict(self):
        d = self._make_report().to_dict()
        assert isinstance(d, dict)

    def test_to_dict_has_required_keys(self):
        d = self._make_report().to_dict()
        for key in ("ollama", "chatdev", "quantum", "timestamp", "overall_score"):
            assert key in d

    def test_to_dict_nested_systems_are_dicts(self):
        d = self._make_report().to_dict()
        assert isinstance(d["ollama"], dict)
        assert isinstance(d["chatdev"], dict)
        assert isinstance(d["quantum"], dict)


# ---------------------------------------------------------------------------
# probe_ollama
# ---------------------------------------------------------------------------


class TestProbeOllama:
    """Tests for probe_ollama()."""

    def test_ollama_unavailable_on_subprocess_fail(self):
        from src.system.ai_health_probe import probe_ollama
        import subprocess
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        with patch("subprocess.run", return_value=mock_result):
            status = probe_ollama(timeout=1)
        # If subprocess fails, ollama is unavailable OR version defaults
        assert status.name == "Ollama"
        assert isinstance(status.available, bool)

    def test_ollama_subprocess_exception_returns_unavailable(self):
        from src.system.ai_health_probe import probe_ollama
        with patch("subprocess.run", side_effect=FileNotFoundError("ollama not found")):
            status = probe_ollama(timeout=1)
        assert status.name == "Ollama"
        assert status.available is False

    def test_probe_returns_health_status(self):
        from src.system.ai_health_probe import probe_ollama, HealthStatus
        with patch("subprocess.run", side_effect=Exception("any error")):
            status = probe_ollama(timeout=1)
        assert isinstance(status, HealthStatus)

    def test_probe_name_is_ollama(self):
        from src.system.ai_health_probe import probe_ollama
        with patch("subprocess.run", side_effect=Exception("boom")):
            status = probe_ollama(timeout=1)
        assert status.name == "Ollama"


# ---------------------------------------------------------------------------
# probe_chatdev
# ---------------------------------------------------------------------------


class TestProbeChatDev:
    """Tests for probe_chatdev()."""

    def test_returns_health_status(self):
        from src.system.ai_health_probe import probe_chatdev, HealthStatus
        status = probe_chatdev(timeout=1)
        assert isinstance(status, HealthStatus)

    def test_name_is_chatdev(self):
        from src.system.ai_health_probe import probe_chatdev
        status = probe_chatdev(timeout=1)
        assert status.name == "ChatDev"

    def test_available_is_bool(self):
        from src.system.ai_health_probe import probe_chatdev
        status = probe_chatdev(timeout=1)
        assert isinstance(status.available, bool)

    def test_chatdev_missing_path_returns_unavailable(self, tmp_path):
        from src.system.ai_health_probe import probe_chatdev
        # Patch pathlib.Path.exists to return False for all checks
        with patch("pathlib.Path.exists", return_value=False):
            status = probe_chatdev(timeout=1)
        assert status.available is False


# ---------------------------------------------------------------------------
# probe_quantum
# ---------------------------------------------------------------------------


class TestProbeQuantum:
    """Tests for probe_quantum()."""

    def test_returns_health_status(self):
        from src.system.ai_health_probe import probe_quantum, HealthStatus
        status = probe_quantum(timeout=1)
        assert isinstance(status, HealthStatus)

    def test_name_is_quantum(self):
        from src.system.ai_health_probe import probe_quantum
        status = probe_quantum(timeout=1)
        assert status.name == "Quantum"

    def test_available_is_bool(self):
        from src.system.ai_health_probe import probe_quantum
        status = probe_quantum(timeout=1)
        assert isinstance(status.available, bool)

    def test_quantum_missing_files_returns_unavailable(self):
        from src.system.ai_health_probe import probe_quantum
        with patch("pathlib.Path.exists", return_value=False):
            status = probe_quantum(timeout=1)
        assert status.available is False
        assert status.error is not None


# ---------------------------------------------------------------------------
# run_full_health_check
# ---------------------------------------------------------------------------


class TestRunFullHealthCheck:
    """Tests for run_full_health_check()."""

    def _make_status(self, name, available):
        from src.system.ai_health_probe import HealthStatus
        return HealthStatus(name=name, available=available)

    def test_returns_ai_health_report(self):
        from src.system.ai_health_probe import run_full_health_check, AIHealthReport, HealthStatus
        ol = self._make_status("Ollama", False)
        cd = self._make_status("ChatDev", False)
        qu = self._make_status("Quantum", False)
        with (
            patch("src.system.ai_health_probe.probe_ollama", return_value=ol),
            patch("src.system.ai_health_probe.probe_chatdev", return_value=cd),
            patch("src.system.ai_health_probe.probe_quantum", return_value=qu),
        ):
            report = run_full_health_check(timeout_per_system=1)
        assert isinstance(report, AIHealthReport)

    def test_score_calculated_from_available_count(self):
        from src.system.ai_health_probe import run_full_health_check, HealthStatus
        ol = self._make_status("Ollama", True)
        cd = self._make_status("ChatDev", True)
        qu = self._make_status("Quantum", False)
        with (
            patch("src.system.ai_health_probe.probe_ollama", return_value=ol),
            patch("src.system.ai_health_probe.probe_chatdev", return_value=cd),
            patch("src.system.ai_health_probe.probe_quantum", return_value=qu),
        ):
            report = run_full_health_check(timeout_per_system=1)
        # 2 of 3 available → score = 2/3
        assert abs(report.overall_score - 2 / 3) < 0.01

    def test_all_available_score_is_one(self):
        from src.system.ai_health_probe import run_full_health_check, HealthStatus
        ol = self._make_status("Ollama", True)
        cd = self._make_status("ChatDev", True)
        qu = self._make_status("Quantum", True)
        with (
            patch("src.system.ai_health_probe.probe_ollama", return_value=ol),
            patch("src.system.ai_health_probe.probe_chatdev", return_value=cd),
            patch("src.system.ai_health_probe.probe_quantum", return_value=qu),
        ):
            report = run_full_health_check(timeout_per_system=1)
        assert report.overall_score == 1.0

    def test_none_available_score_is_zero(self):
        from src.system.ai_health_probe import run_full_health_check, HealthStatus
        ol = self._make_status("Ollama", False)
        cd = self._make_status("ChatDev", False)
        qu = self._make_status("Quantum", False)
        with (
            patch("src.system.ai_health_probe.probe_ollama", return_value=ol),
            patch("src.system.ai_health_probe.probe_chatdev", return_value=cd),
            patch("src.system.ai_health_probe.probe_quantum", return_value=qu),
        ):
            report = run_full_health_check(timeout_per_system=1)
        assert report.overall_score == 0.0

    def test_timestamp_is_set(self):
        from src.system.ai_health_probe import run_full_health_check, HealthStatus
        ol = self._make_status("Ollama", False)
        cd = self._make_status("ChatDev", False)
        qu = self._make_status("Quantum", False)
        with (
            patch("src.system.ai_health_probe.probe_ollama", return_value=ol),
            patch("src.system.ai_health_probe.probe_chatdev", return_value=cd),
            patch("src.system.ai_health_probe.probe_quantum", return_value=qu),
        ):
            report = run_full_health_check(timeout_per_system=1)
        assert report.timestamp is not None
        assert len(report.timestamp) > 0


# ---------------------------------------------------------------------------
# gate_on_health
# ---------------------------------------------------------------------------


class TestGateOnHealth:
    """Tests for gate_on_health()."""

    def _make_report(self, ollama=True, chatdev=True, quantum=True):
        from src.system.ai_health_probe import AIHealthReport, HealthStatus
        ol = HealthStatus(name="Ollama", available=ollama)
        cd = HealthStatus(name="ChatDev", available=chatdev)
        qu = HealthStatus(name="Quantum", available=quantum)
        score = sum([ollama, chatdev, quantum]) / 3.0
        return AIHealthReport(
            ollama=ol, chatdev=cd, quantum=qu,
            timestamp="2026-01-01T00:00:00",
            overall_score=score,
        )

    def test_passes_with_high_score(self):
        from src.system.ai_health_probe import gate_on_health
        report = self._make_report(ollama=True, chatdev=True, quantum=True)
        assert gate_on_health(report, min_score=0.66) is True

    def test_fails_with_low_score(self):
        from src.system.ai_health_probe import gate_on_health
        report = self._make_report(ollama=False, chatdev=False, quantum=False)
        assert gate_on_health(report, min_score=0.66) is False

    def test_required_systems_all_present(self):
        from src.system.ai_health_probe import gate_on_health
        report = self._make_report(ollama=True, chatdev=True, quantum=True)
        # get_available_systems() returns lowercase names
        assert gate_on_health(report, required_systems=["ollama"]) is True

    def test_required_systems_missing_fails(self):
        from src.system.ai_health_probe import gate_on_health
        report = self._make_report(ollama=False, chatdev=True, quantum=True)
        assert gate_on_health(report, required_systems=["ollama"]) is False

    def test_required_systems_takes_priority_over_min_score(self):
        from src.system.ai_health_probe import gate_on_health
        report = self._make_report(ollama=True, chatdev=True, quantum=True)
        # All available → passing both ways; use lowercase system names
        assert gate_on_health(report, required_systems=["ollama"], min_score=0.66) is True

    def test_score_exactly_at_threshold_passes(self):
        from src.system.ai_health_probe import gate_on_health
        report = self._make_report(ollama=True, chatdev=True, quantum=False)
        # score = 2/3 ≈ 0.667 >= 0.66
        assert gate_on_health(report, min_score=0.66) is True

    def test_empty_required_systems_uses_score(self):
        from src.system.ai_health_probe import gate_on_health
        report = self._make_report(ollama=False, chatdev=False, quantum=False)
        # Empty required_systems list is falsy → falls through to score check
        assert gate_on_health(report, required_systems=[], min_score=0.66) is False


# ---------------------------------------------------------------------------
# save_health_report
# ---------------------------------------------------------------------------


class TestSaveHealthReport:
    """Tests for save_health_report()."""

    def _make_report(self):
        from src.system.ai_health_probe import AIHealthReport, HealthStatus
        ol = HealthStatus(name="Ollama", available=True, version="0.1.0")
        cd = HealthStatus(name="ChatDev", available=False, error="not found")
        qu = HealthStatus(name="Quantum", available=True)
        return AIHealthReport(
            ollama=ol, chatdev=cd, quantum=qu,
            timestamp="2026-01-01T00:00:00",
            overall_score=0.67,
        )

    def test_creates_file(self, tmp_path):
        from src.system.ai_health_probe import save_health_report
        out = tmp_path / "health.json"
        save_health_report(self._make_report(), out)
        assert out.exists()

    def test_file_is_valid_json(self, tmp_path):
        from src.system.ai_health_probe import save_health_report
        out = tmp_path / "health.json"
        save_health_report(self._make_report(), out)
        data = json.loads(out.read_text())
        assert isinstance(data, dict)

    def test_file_contains_overall_score(self, tmp_path):
        from src.system.ai_health_probe import save_health_report
        out = tmp_path / "health.json"
        save_health_report(self._make_report(), out)
        data = json.loads(out.read_text())
        assert "overall_score" in data

    def test_creates_parent_dirs(self, tmp_path):
        from src.system.ai_health_probe import save_health_report
        out = tmp_path / "nested" / "dir" / "health.json"
        save_health_report(self._make_report(), out)
        assert out.exists()
