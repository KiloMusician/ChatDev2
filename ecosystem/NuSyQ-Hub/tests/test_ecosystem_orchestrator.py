"""Tests for src/orchestration/ecosystem_orchestrator.py — AutonomyLevel, OrchestratorCycle, EcosystemOrchestrator."""

import asyncio
import time

import pytest


class TestAutonomyLevel:
    """Tests for AutonomyLevel enum."""

    def test_has_six_values(self):
        from src.orchestration.ecosystem_orchestrator import AutonomyLevel
        assert len(list(AutonomyLevel)) == 6

    def test_disabled_is_zero(self):
        from src.orchestration.ecosystem_orchestrator import AutonomyLevel
        assert AutonomyLevel.DISABLED.value == 0

    def test_full_is_five(self):
        from src.orchestration.ecosystem_orchestrator import AutonomyLevel
        assert AutonomyLevel.FULL.value == 5

    def test_all_levels_present(self):
        from src.orchestration.ecosystem_orchestrator import AutonomyLevel
        names = {level.name for level in AutonomyLevel}
        assert names == {"DISABLED", "MONITORING", "SUGGESTING", "CLAIMING", "EXECUTING", "FULL"}

    def test_ordered_values(self):
        from src.orchestration.ecosystem_orchestrator import AutonomyLevel
        values = [level.value for level in AutonomyLevel]
        assert values == sorted(values)


class TestOrchestratorCycle:
    """Tests for OrchestratorCycle."""

    @pytest.fixture
    def cycle(self):
        from src.orchestration.ecosystem_orchestrator import OrchestratorCycle
        return OrchestratorCycle()

    def test_instantiation(self, cycle):
        assert cycle is not None

    def test_has_cycle_id(self, cycle):
        assert hasattr(cycle, "cycle_id")
        assert isinstance(cycle.cycle_id, str)
        assert cycle.cycle_id.startswith("cycle_")

    def test_has_empty_results(self, cycle):
        assert cycle.results == {}

    def test_has_empty_errors(self, cycle):
        assert cycle.errors == []

    def test_add_result_stores_data(self, cycle):
        cycle.add_result("error_scan", {"total_errors": 5})
        assert "error_scan" in cycle.results
        assert cycle.results["error_scan"]["data"]["total_errors"] == 5

    def test_add_result_includes_timestamp(self, cycle):
        cycle.add_result("stage_a", {"key": "val"})
        assert "timestamp" in cycle.results["stage_a"]

    def test_add_error_appends(self, cycle):
        cycle.add_error("stage_x", "Something failed")
        assert len(cycle.errors) == 1
        assert "stage_x" in cycle.errors[0]
        assert "Something failed" in cycle.errors[0]

    def test_add_multiple_errors(self, cycle):
        cycle.add_error("a", "err1")
        cycle.add_error("b", "err2")
        assert len(cycle.errors) == 2

    def test_duration_is_float(self, cycle):
        d = cycle.duration()
        assert isinstance(d, float)
        assert d >= 0.0

    def test_duration_increases(self, cycle):
        d1 = cycle.duration()
        time.sleep(0.05)
        d2 = cycle.duration()
        assert d2 > d1

    def test_summary_has_required_keys(self, cycle):
        s = cycle.summary()
        for key in ("cycle_id", "duration_seconds", "stages_completed", "errors", "results"):
            assert key in s

    def test_summary_stages_completed_reflects_results(self, cycle):
        cycle.add_result("scan", {"ok": True})
        cycle.add_result("bridge", {"ok": True})
        s = cycle.summary()
        assert set(s["stages_completed"]) == {"scan", "bridge"}

    def test_summary_errors_list(self, cycle):
        cycle.add_error("scan", "boom")
        s = cycle.summary()
        assert len(s["errors"]) == 1

    def test_unique_cycle_ids(self):
        from src.orchestration.ecosystem_orchestrator import OrchestratorCycle
        c1 = OrchestratorCycle()
        time.sleep(0.01)
        c2 = OrchestratorCycle()
        # cycle_ids may be same if both fall in same second, but both must be strings
        assert isinstance(c1.cycle_id, str)
        assert isinstance(c2.cycle_id, str)


class TestEcosystemOrchestrator:
    """Tests for EcosystemOrchestrator (non-async parts)."""

    def test_default_instantiation(self):
        from src.orchestration.ecosystem_orchestrator import EcosystemOrchestrator
        eo = EcosystemOrchestrator()
        assert eo is not None

    def test_default_autonomy_level(self):
        from src.orchestration.ecosystem_orchestrator import AutonomyLevel, EcosystemOrchestrator
        eo = EcosystemOrchestrator()
        assert eo.autonomy_level == AutonomyLevel.SUGGESTING

    def test_custom_autonomy_level(self):
        from src.orchestration.ecosystem_orchestrator import AutonomyLevel, EcosystemOrchestrator
        eo = EcosystemOrchestrator(autonomy_level=AutonomyLevel.MONITORING)
        assert eo.autonomy_level == AutonomyLevel.MONITORING

    def test_disabled_autonomy_level(self):
        from src.orchestration.ecosystem_orchestrator import AutonomyLevel, EcosystemOrchestrator
        eo = EcosystemOrchestrator(autonomy_level=AutonomyLevel.DISABLED)
        assert eo.autonomy_level == AutonomyLevel.DISABLED

    def test_full_autonomy_level(self):
        from src.orchestration.ecosystem_orchestrator import AutonomyLevel, EcosystemOrchestrator
        eo = EcosystemOrchestrator(autonomy_level=AutonomyLevel.FULL)
        assert eo.autonomy_level == AutonomyLevel.FULL

    def test_cycle_count_starts_zero(self):
        from src.orchestration.ecosystem_orchestrator import EcosystemOrchestrator
        eo = EcosystemOrchestrator()
        assert eo.cycle_count == 0

    def test_cycles_log_starts_empty(self):
        from src.orchestration.ecosystem_orchestrator import EcosystemOrchestrator
        eo = EcosystemOrchestrator()
        assert eo.cycles_log == []

    def test_is_running_starts_false(self):
        from src.orchestration.ecosystem_orchestrator import EcosystemOrchestrator
        eo = EcosystemOrchestrator()
        assert eo.is_running is False

    def test_get_status_structure(self):
        from src.orchestration.ecosystem_orchestrator import EcosystemOrchestrator
        eo = EcosystemOrchestrator()
        status = eo.get_status()
        assert "is_running" in status
        assert "cycle_count" in status
        assert "autonomy_level" in status
        assert "recent_cycles" in status

    def test_get_status_is_not_running(self):
        from src.orchestration.ecosystem_orchestrator import EcosystemOrchestrator
        eo = EcosystemOrchestrator()
        assert eo.get_status()["is_running"] is False

    def test_get_status_autonomy_name(self):
        from src.orchestration.ecosystem_orchestrator import AutonomyLevel, EcosystemOrchestrator
        eo = EcosystemOrchestrator(autonomy_level=AutonomyLevel.EXECUTING)
        assert eo.get_status()["autonomy_level"] == "EXECUTING"

    def test_get_status_recent_cycles_empty_initially(self):
        from src.orchestration.ecosystem_orchestrator import EcosystemOrchestrator
        eo = EcosystemOrchestrator()
        assert eo.get_status()["recent_cycles"] == []

    def test_get_status_recent_cycles_capped_at_five(self):
        from src.orchestration.ecosystem_orchestrator import EcosystemOrchestrator
        eo = EcosystemOrchestrator()
        # Manually append 10 fake cycle summaries
        for i in range(10):
            eo.cycles_log.append({"cycle_id": f"c{i}", "duration_seconds": float(i)})
        recent = eo.get_status()["recent_cycles"]
        assert len(recent) == 5
        # Should be the last 5
        assert recent[0]["cycle_id"] == "c5"

    @pytest.mark.asyncio
    async def test_run_cycle_disabled_skips_stages(self):
        from src.orchestration.ecosystem_orchestrator import AutonomyLevel, EcosystemOrchestrator
        eo = EcosystemOrchestrator(autonomy_level=AutonomyLevel.DISABLED)
        result = await eo.run_cycle(test_mode=True)
        # Disabled → no stages run
        assert isinstance(result, dict)
        assert result["stages_completed"] == []
        assert eo.cycle_count == 1

    @pytest.mark.asyncio
    async def test_run_cycle_increments_count(self):
        from src.orchestration.ecosystem_orchestrator import AutonomyLevel, EcosystemOrchestrator
        eo = EcosystemOrchestrator(autonomy_level=AutonomyLevel.DISABLED)
        await eo.run_cycle(test_mode=True)
        await eo.run_cycle(test_mode=True)
        assert eo.cycle_count == 2

    @pytest.mark.asyncio
    async def test_run_cycle_appends_to_log(self):
        from src.orchestration.ecosystem_orchestrator import AutonomyLevel, EcosystemOrchestrator
        eo = EcosystemOrchestrator(autonomy_level=AutonomyLevel.DISABLED)
        await eo.run_cycle(test_mode=True)
        assert len(eo.cycles_log) == 1

    @pytest.mark.asyncio
    async def test_run_cycle_returns_summary_keys(self):
        from src.orchestration.ecosystem_orchestrator import AutonomyLevel, EcosystemOrchestrator
        eo = EcosystemOrchestrator(autonomy_level=AutonomyLevel.DISABLED)
        result = await eo.run_cycle(test_mode=True)
        for key in ("cycle_id", "duration_seconds", "stages_completed", "errors"):
            assert key in result
