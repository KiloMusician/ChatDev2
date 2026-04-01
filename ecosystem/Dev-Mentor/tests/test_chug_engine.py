"""Tests for chug_engine.py — dataclasses and ChugEngine state logic."""
import math

import chug_engine as ce
from chug_engine import (
    PHASE_NAMES,
    ChugEngine,
    ChugState,
    CycleResult,
    PhaseResult,
)


# ── PhaseResult ───────────────────────────────────────────────────────────────

class TestPhaseResult:
    def test_required_fields(self):
        pr = PhaseResult(
            phase="ASSESS",
            phase_number=1,
            success=True,
            duration_seconds=0.5,
            summary="all clear",
        )
        assert pr.phase == "ASSESS"
        assert pr.phase_number == 1
        assert pr.success is True
        assert math.isclose(pr.duration_seconds, 0.5)
        assert pr.summary == "all clear"

    def test_optional_list_fields_default_empty(self):
        pr = PhaseResult(
            phase="PLAN",
            phase_number=2,
            success=True,
            duration_seconds=1.0,
            summary="planned",
        )
        assert not pr.actions_taken
        assert not pr.issues_found
        assert not pr.fixes_applied
        assert pr.details == {}

    def test_list_fields_stored(self):
        pr = PhaseResult(
            phase="EXECUTE",
            phase_number=3,
            success=False,
            duration_seconds=2.0,
            summary="partial",
            actions_taken=["edit foo.py"],
            issues_found=["lint error"],
        )
        assert "edit foo.py" in pr.actions_taken
        assert "lint error" in pr.issues_found


# ── CycleResult ───────────────────────────────────────────────────────────────

class TestCycleResult:
    def test_clean_cycle_flag(self):
        cr = CycleResult(
            cycle_number=1,
            timestamp="2026-01-01T00:00:00",
            duration_seconds=10.0,
            phases=[],
            total_issues=0,
            total_fixes=0,
            is_clean=True,
            plan_bullets=[],
            what_improved=[],
            what_remains_risky=[],
            next_best_cycle="ASSESS",
        )
        assert cr.is_clean is True
        assert cr.total_issues == 0

    def test_dirty_cycle_counts(self):
        cr = CycleResult(
            cycle_number=2,
            timestamp="2026-01-02T00:00:00",
            duration_seconds=30.0,
            phases=[],
            total_issues=5,
            total_fixes=3,
            is_clean=False,
            plan_bullets=["fix type errors", "add tests"],
            what_improved=["reduced lint count"],
            what_remains_risky=["missing coverage"],
            next_best_cycle="VERIFY",
        )
        assert cr.is_clean is False
        assert cr.total_issues == 5
        assert cr.total_fixes == 3
        assert len(cr.plan_bullets) == 2


# ── ChugState ────────────────────────────────────────────────────────────────

class TestChugState:
    def test_default_state(self):
        state = ChugState()
        assert state.cycles_completed == 0
        assert state.last_phase == ""
        assert state.total_fixes_applied == 0
        assert state.consecutive_clean_cycles == 0
        assert not state.history
        assert state.phase_stats == {}

    def test_save_and_load_roundtrip(self, tmp_path, monkeypatch):
        state_file = tmp_path / "chug_state.json"
        monkeypatch.setattr(ce, "CHUG_STATE_FILE", state_file)

        state = ChugState(
            cycles_completed=3,
            last_phase="VERIFY",
            total_fixes_applied=7,
        )
        state.save()
        assert state_file.exists()

        loaded = ChugState.load()
        assert loaded.cycles_completed == 3
        assert loaded.last_phase == "VERIFY"
        assert loaded.total_fixes_applied == 7

    def test_load_returns_default_when_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            ce, "CHUG_STATE_FILE", tmp_path / "nonexistent.json"
        )
        state = ChugState.load()
        assert state.cycles_completed == 0

    def test_load_returns_default_on_corrupt_json(
        self, tmp_path, monkeypatch
    ):
        state_file = tmp_path / "chug_state.json"
        state_file.write_text("not valid json", encoding="utf-8")
        monkeypatch.setattr(ce, "CHUG_STATE_FILE", state_file)
        state = ChugState.load()
        assert state.cycles_completed == 0


# ── ChugEngine ───────────────────────────────────────────────────────────────

class TestChugEngine:
    def _make_engine(self, tmp_path, monkeypatch):
        monkeypatch.setattr(ce, "CHUG_STATE_FILE", tmp_path / "state.json")
        monkeypatch.setattr(ce, "REPORTS_DIR", tmp_path / "reports")
        monkeypatch.setattr(ce, "EXPORTS_DIR", tmp_path / "exports")
        return ChugEngine()

    def test_instantiates(self, tmp_path, monkeypatch):
        engine = self._make_engine(tmp_path, monkeypatch)
        assert engine.state is not None
        assert not engine.current_plan

    def test_show_status_does_not_raise(self, tmp_path, monkeypatch):
        engine = self._make_engine(tmp_path, monkeypatch)
        # show_status writes via logger — just assert it does not raise
        engine.show_status()

    def test_phase_names_are_seven(self):
        assert len(PHASE_NAMES) == 7
        assert PHASE_NAMES[0] == "ASSESS"
        assert PHASE_NAMES[-1] == "EXPORT"
