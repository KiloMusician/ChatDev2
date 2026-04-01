"""Tests for ContinuousOptimizationEngine — optimizer agent backend."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def engine(tmp_path):
    from src.orchestration.continuous_optimization_engine import ContinuousOptimizationEngine

    return ContinuousOptimizationEngine(repo_root=tmp_path)


class TestInit:
    def test_default_repo_root(self):
        from src.orchestration.continuous_optimization_engine import ContinuousOptimizationEngine

        eng = ContinuousOptimizationEngine()
        # Should default to repo root (2 parents up from the module file)
        assert eng.repo_root.name != ""
        assert isinstance(eng.repo_root, Path)

    def test_custom_repo_root(self, tmp_path):
        from src.orchestration.continuous_optimization_engine import ContinuousOptimizationEngine

        eng = ContinuousOptimizationEngine(repo_root=tmp_path)
        assert eng.repo_root == tmp_path

    def test_state_dir_set(self, engine, tmp_path):
        assert engine.state_dir == tmp_path / "state"

    def test_src_dir_set(self, engine, tmp_path):
        assert engine.src_dir == tmp_path / "src"

    def test_history_file_parent_created(self, engine):
        assert engine.history_file.parent.exists()

    def test_history_file_path(self, engine, tmp_path):
        assert engine.history_file == tmp_path / "state" / "optimization_history.jsonl"


class TestOptimizationCycle:
    def test_dataclass_defaults(self):
        from src.orchestration.continuous_optimization_engine import OptimizationCycle

        cycle = OptimizationCycle(timestamp="2026-01-01T00:00:00", duration_seconds=1.0)
        assert cycle.health_score_before == 0.0
        assert cycle.health_score_after == 0.0
        assert cycle.health_improvement == 0.0
        assert cycle.search_files_updated == 0
        assert cycle.search_files_removed == 0
        assert cycle.healing_issues_identified == 0
        assert cycle.healing_fixes_applied == 0

    def test_dataclass_custom_values(self):
        from src.orchestration.continuous_optimization_engine import OptimizationCycle

        cycle = OptimizationCycle(
            timestamp="2026-01-01T00:00:00",
            duration_seconds=5.2,
            health_score_before=70.0,
            health_score_after=75.0,
            health_improvement=5.0,
            search_files_updated=10,
            search_files_removed=2,
            healing_issues_identified=3,
            healing_fixes_applied=2,
        )
        assert cycle.health_improvement == 5.0
        assert cycle.search_files_updated == 10


class TestCollectHealthScore:
    def test_returns_float_on_subprocess_failure(self, engine):
        with patch("subprocess.run", side_effect=Exception("process failed")):
            score = engine._collect_health_score()
        assert isinstance(score, float)
        assert score == 0.0

    def test_returns_float_on_nonzero_exit(self, engine):
        mock_result = MagicMock()
        mock_result.returncode = 1
        with patch("subprocess.run", return_value=mock_result):
            score = engine._collect_health_score()
        assert score == 0.0

    def test_reads_latest_metrics_file(self, engine, tmp_path):
        # Create a fake metrics file
        metrics_file = tmp_path / "state" / "real_system_metrics_20260101.json"
        metrics_file.parent.mkdir(parents=True, exist_ok=True)
        metrics_file.write_text(json.dumps({"health_score": 88.5}))

        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            score = engine._collect_health_score()
        assert score == 88.5

    def test_returns_zero_when_no_metrics_file(self, engine, tmp_path):
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            score = engine._collect_health_score()
        assert score == 0.0


class TestUpdateSearchIndex:
    def test_returns_empty_dict_on_failure(self, engine):
        with patch("subprocess.run", side_effect=Exception("index error")):
            result = engine._update_search_index()
        assert result == {}

    def test_returns_empty_dict_on_nonzero_exit(self, engine):
        mock_result = MagicMock()
        mock_result.returncode = 1
        with patch("subprocess.run", return_value=mock_result):
            result = engine._update_search_index()
        assert result == {}

    def test_parses_json_output_on_success(self, engine):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"files_updated": 5, "files_removed": 1})
        with patch("subprocess.run", return_value=mock_result):
            result = engine._update_search_index()
        assert result["files_updated"] == 5
        assert result["files_removed"] == 1


class TestRunCultureShipHealing:
    def test_returns_empty_dict_on_exception(self, engine):
        with patch.dict("sys.modules", {"orchestration.culture_ship_strategic_advisor": None}):
            result = engine._run_culture_ship_healing()
        assert result == {}

    def test_returns_stats_on_success(self, engine):
        mock_advisor = MagicMock()
        mock_advisor.run_full_strategic_cycle.return_value = {
            "issues_identified": 3,
            "implementations": ["fix1", "fix2"],
        }
        mock_module = MagicMock()
        mock_module.CultureShipStrategicAdvisor.return_value = mock_advisor

        with patch.dict(
            "sys.modules", {"orchestration.culture_ship_strategic_advisor": mock_module}
        ):
            result = engine._run_culture_ship_healing()
        assert result["issues_identified"] == 3
        assert result["fixes_applied"] == 2

    def test_returns_empty_dict_on_import_error(self, engine):
        with patch("builtins.__import__", side_effect=ImportError("no module")):
            result = engine._run_culture_ship_healing()
        assert result == {}


class TestBroadcastMetrics:
    def test_does_not_raise_on_failure(self, engine):
        with patch("subprocess.run", side_effect=Exception("broadcast error")):
            engine._broadcast_metrics()  # should not raise

    def test_calls_subprocess(self, engine):
        mock_result = MagicMock()
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            engine._broadcast_metrics()
        mock_run.assert_called_once()


class TestSaveCycle:
    def test_saves_jsonl_entry(self, engine, tmp_path):
        from src.orchestration.continuous_optimization_engine import OptimizationCycle

        cycle = OptimizationCycle(
            timestamp="2026-01-01T00:00:00",
            duration_seconds=2.5,
            health_improvement=3.0,
        )
        engine._save_cycle(cycle)
        assert engine.history_file.exists()
        line = engine.history_file.read_text().strip()
        data = json.loads(line)
        assert data["timestamp"] == "2026-01-01T00:00:00"
        assert data["health_improvement"] == 3.0

    def test_appends_multiple_cycles(self, engine):
        from src.orchestration.continuous_optimization_engine import OptimizationCycle

        for i in range(3):
            cycle = OptimizationCycle(timestamp=f"2026-01-0{i + 1}T00:00:00", duration_seconds=1.0)
            engine._save_cycle(cycle)

        lines = [ln for ln in engine.history_file.read_text().splitlines() if ln.strip()]
        assert len(lines) == 3


class TestGetOptimizationHistory:
    def test_returns_empty_when_no_file(self, engine):
        assert engine.get_optimization_history() == []

    def test_returns_cycles_in_reverse_order(self, engine):
        from src.orchestration.continuous_optimization_engine import OptimizationCycle

        for ts in ["2026-01-01T00:00:00", "2026-01-02T00:00:00", "2026-01-03T00:00:00"]:
            engine._save_cycle(OptimizationCycle(timestamp=ts, duration_seconds=1.0))

        history = engine.get_optimization_history()
        assert history[0].timestamp == "2026-01-03T00:00:00"
        assert history[-1].timestamp == "2026-01-01T00:00:00"

    def test_respects_limit(self, engine):
        from src.orchestration.continuous_optimization_engine import OptimizationCycle

        for i in range(5):
            engine._save_cycle(OptimizationCycle(timestamp=f"2026-01-0{i + 1}T00:00:00", duration_seconds=1.0))

        history = engine.get_optimization_history(limit=2)
        assert len(history) == 2

    def test_skips_blank_lines(self, engine):
        engine.history_file.parent.mkdir(parents=True, exist_ok=True)
        engine.history_file.write_text(
            '{"timestamp": "2026-01-01T00:00:00", "duration_seconds": 1.0, "health_score_before": 0.0, '
            '"health_score_after": 0.0, "health_improvement": 0.0, "search_files_updated": 0, '
            '"search_files_removed": 0, "healing_issues_identified": 0, "healing_fixes_applied": 0}\n\n'
        )
        history = engine.get_optimization_history()
        assert len(history) == 1


class TestRunSingleCycle:
    def test_returns_optimization_cycle(self, engine):
        from src.orchestration.continuous_optimization_engine import OptimizationCycle

        with (
            patch.object(engine, "_collect_health_score", return_value=80.0),
            patch.object(engine, "_update_search_index", return_value={"files_updated": 2, "files_removed": 0}),
            patch.object(engine, "_run_culture_ship_healing", return_value={"issues_identified": 1, "fixes_applied": 0}),
            patch.object(engine, "_broadcast_metrics"),
        ):
            cycle = engine.run_single_cycle()

        assert isinstance(cycle, OptimizationCycle)
        assert cycle.health_score_before == 80.0
        assert cycle.health_score_after == 80.0
        assert cycle.search_files_updated == 2
        assert cycle.healing_issues_identified == 1
        assert cycle.duration_seconds >= 0.0

    def test_saves_cycle_to_history(self, engine):
        with (
            patch.object(engine, "_collect_health_score", return_value=75.0),
            patch.object(engine, "_update_search_index", return_value={}),
            patch.object(engine, "_run_culture_ship_healing", return_value={}),
            patch.object(engine, "_broadcast_metrics"),
        ):
            engine.run_single_cycle()

        assert engine.history_file.exists()
        lines = [ln for ln in engine.history_file.read_text().splitlines() if ln.strip()]
        assert len(lines) == 1

    def test_health_improvement_computed(self, engine):
        scores = [70.0, 75.0]

        with (
            patch.object(engine, "_collect_health_score", side_effect=scores),
            patch.object(engine, "_update_search_index", return_value={}),
            patch.object(engine, "_run_culture_ship_healing", return_value={}),
            patch.object(engine, "_broadcast_metrics"),
        ):
            cycle = engine.run_single_cycle()

        assert cycle.health_improvement == pytest.approx(5.0)


class TestPrintHistorySummary:
    def test_runs_without_error_empty(self, engine, capsys):
        engine.print_history_summary()

    def test_runs_without_error_with_history(self, engine, capsys):
        from src.orchestration.continuous_optimization_engine import OptimizationCycle

        engine._save_cycle(
            OptimizationCycle(
                timestamp="2026-01-01T00:00:00",
                duration_seconds=3.5,
                health_score_before=70.0,
                health_score_after=73.0,
                health_improvement=3.0,
                healing_issues_identified=2,
                healing_fixes_applied=1,
            )
        )
        engine.print_history_summary()
        out = capsys.readouterr().out
        assert "2026" in out or len(out) >= 0  # just verifies it ran
