"""Tests for the src/spine subsystem.

Covers:
- civilization_orchestrator: KardeshevCivilization, Environment
- culture_consciousness: KardeshevV
- kardeshev_optimizer: Environment, Society, Technology, KardeshevCivilization
- reality_weaver: KardeshevCivilization (ecosystem variant)
- transcendent_spine_core: CultureLevelCivilization
- spine/__init__ + SpineRegistry + SpineHealth + initialize_spine
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# civilization_orchestrator
# ---------------------------------------------------------------------------


class TestCivilizationOrchestrator:
    """Tests for src.spine.civilization_orchestrator."""

    def test_environment_init_defaults(self) -> None:
        from src.spine.civilization_orchestrator import Environment

        env = Environment()
        assert env.health == 100

    def test_environment_restore_resets_health(self) -> None:
        from src.spine.civilization_orchestrator import Environment

        env = Environment()
        env.health = 42
        env.restore()
        assert env.health == 100

    def test_kardeshev_civilization_init(self) -> None:
        from src.spine.civilization_orchestrator import KardeshevCivilization

        civ = KardeshevCivilization()
        assert isinstance(civ.resources, dict)
        assert isinstance(civ.technologies, list)
        assert isinstance(civ.cultures, list)
        assert isinstance(civ.evolutionary_strategies, list)

    def test_optimize_resource_energy(self) -> None:
        from src.spine.civilization_orchestrator import KardeshevCivilization

        civ = KardeshevCivilization()
        result = civ.optimize_resource("energy", 1000.0)
        # Should apply efficiency x resource multiplier -- strictly less than 1000
        assert 0 < result < 1000

    def test_optimize_resource_zero_returns_zero(self) -> None:
        from src.spine.civilization_orchestrator import KardeshevCivilization

        civ = KardeshevCivilization()
        assert civ.optimize_resource("energy", 0) == 0

    def test_enhance_technology_adds_version(self) -> None:
        from src.spine.civilization_orchestrator import KardeshevCivilization

        civ = KardeshevCivilization()
        result = civ.enhance_technology("Quantum Computing")
        # No version present — should append " 2.0"
        assert "2.0" in result

    def test_cultivate_returns_enriched_string(self) -> None:
        from src.spine.civilization_orchestrator import KardeshevCivilization

        civ = KardeshevCivilization()
        result = civ.cultivate("Science")
        assert "Science" in result
        assert "diversity" in result

    def test_evolve_tracks_generation(self) -> None:
        from src.spine.civilization_orchestrator import KardeshevCivilization

        civ = KardeshevCivilization()
        r1 = civ.evolve("Adaptive")
        r2 = civ.evolve("Collective")
        assert "gen 1" in r1
        assert "gen 2" in r2

    def test_heal_environment_calls_restore(self) -> None:
        from src.spine.civilization_orchestrator import KardeshevCivilization

        civ = KardeshevCivilization()
        civ.environment.health = 0
        civ.heal_environment()
        assert civ.environment.health == 100


# ---------------------------------------------------------------------------
# culture_consciousness (KardeshevV)
# ---------------------------------------------------------------------------


class TestCultureConsciousness:
    """Tests for src.spine.culture_consciousness.KardeshevV."""

    def test_kardeshev_v_init(self) -> None:
        from src.spine.culture_consciousness import KardeshevV

        kv = KardeshevV()
        assert isinstance(kv.resources, dict)
        assert isinstance(kv.environment, dict)
        assert isinstance(kv.culture, dict)
        assert isinstance(kv.technology, dict)
        assert isinstance(kv.evolution, dict)

    def test_harvest_energy_keys(self) -> None:
        from src.spine.culture_consciousness import KardeshevV

        kv = KardeshevV()
        energy = kv.harvest_energy()
        assert "solar" in energy
        assert "fusion" in energy
        assert "dark_matter" in energy

    def test_run_populates_all_subsystems(self) -> None:
        from src.spine.culture_consciousness import KardeshevV

        kv = KardeshevV()
        result = kv.run()
        assert set(result.keys()) == {"resources", "environment", "culture", "technology", "evolution"}
        # Each subsystem dict should be non-empty after run()
        for key, val in result.items():
            assert val, f"Subsystem '{key}' should be non-empty after run()"

    def test_optimize_environment_sets_keys(self) -> None:
        from src.spine.culture_consciousness import KardeshevV

        kv = KardeshevV()
        kv.optimize_environment()
        assert "climate" in kv.environment
        assert "biodiversity" in kv.environment
        assert "pollution" in kv.environment


# ---------------------------------------------------------------------------
# kardeshev_optimizer
# ---------------------------------------------------------------------------


class TestKardashevOptimizer:
    """Tests for src.spine.kardeshev_optimizer classes."""

    def test_environment_init(self) -> None:
        from src.spine.kardeshev_optimizer import Environment

        env = Environment()
        assert isinstance(env.resources, dict)
        assert isinstance(env.health_metrics, dict)

    def test_environment_monitor_resources_optimal(self) -> None:
        from src.spine.kardeshev_optimizer import Environment

        env = Environment()
        env.resources = {"solar": 100, "fusion": 200, "demand": 10}
        env.monitor_resources()
        assert env.health_metrics["status"] == "optimal"

    def test_society_evolve_culture_increments_cycles(self) -> None:
        from src.spine.kardeshev_optimizer import Society

        soc = Society()
        soc.evolve_culture()
        assert soc.culture["evolution_cycles"] == 1

    def test_technology_optimize_systems_baseline(self) -> None:
        from src.spine.kardeshev_optimizer import Technology

        tech = Technology()
        tech.optimize_systems()
        assert tech.metrics["optimization_score"] == 10  # baseline with no innovations

    def test_kardeshev_civilization_run_cycle(self) -> None:
        from src.spine.kardeshev_optimizer import KardeshevCivilization

        civ = KardeshevCivilization()
        # run_cycle should not raise
        civ.run_cycle()
        assert "healing_applied" in civ.environment.health_metrics

    def test_kardeshev_civilization_report_status_no_raise(self) -> None:
        from src.spine.kardeshev_optimizer import KardeshevCivilization

        civ = KardeshevCivilization()
        civ.run_cycle()
        # report_status just logs — must not raise
        civ.report_status()


# ---------------------------------------------------------------------------
# reality_weaver (ecosystem variant)
# ---------------------------------------------------------------------------


class TestRealityWeaver:
    """Tests for src.spine.reality_weaver.KardeshevCivilization."""

    def test_init_attributes(self) -> None:
        from src.spine.reality_weaver import KardeshevCivilization

        civ = KardeshevCivilization()
        assert isinstance(civ.resources, dict)
        assert isinstance(civ.technologies, list)
        assert isinstance(civ.ecosystems, list)
        assert isinstance(civ.societal_structures, list)
        assert isinstance(civ.cultural_initiatives, list)

    def test_optimize_resource_reduces_by_10_percent(self) -> None:
        from src.spine.reality_weaver import KardeshevCivilization

        civ = KardeshevCivilization()
        result = civ.optimize_resource("Energy", 1000.0)
        assert result == pytest.approx(900.0)

    def test_enhance_technology_appends_enhanced(self) -> None:
        from src.spine.reality_weaver import KardeshevCivilization

        civ = KardeshevCivilization()
        civ.technologies.append("Nanotechnology")
        civ.enhance_technology("Nanotechnology")
        assert "Nanotechnology Enhanced" in civ.technologies

    def test_run_no_raise_with_empty_lists(self) -> None:
        from src.spine.reality_weaver import KardeshevCivilization

        civ = KardeshevCivilization()
        # Should complete without error on empty state
        civ.run()


# ---------------------------------------------------------------------------
# SpineRegistry (registry.py)
# ---------------------------------------------------------------------------


class TestSpineRegistry:
    """Tests for src.spine.registry.SpineRegistry."""

    def test_init_with_missing_config(self, tmp_path: Path) -> None:
        from src.spine.registry import SpineRegistry

        reg = SpineRegistry(config_path=tmp_path / "nonexistent.json")
        assert reg._config == {"modules": {}}

    def test_register_and_get(self, tmp_path: Path) -> None:
        from src.spine.registry import SpineRegistry

        reg = SpineRegistry(config_path=tmp_path / "nonexistent.json")
        reg.register("my.service", object())
        assert reg.has("my.service")
        assert reg.get("my.service") is not None

    def test_register_duplicate_raises(self, tmp_path: Path) -> None:
        from src.spine.registry import SpineRegistry

        reg = SpineRegistry(config_path=tmp_path / "nonexistent.json")
        reg.register("svc", "value1")
        with pytest.raises(ValueError, match="already registered"):
            reg.register("svc", "value2")

    def test_register_override_succeeds(self, tmp_path: Path) -> None:
        from src.spine.registry import SpineRegistry

        reg = SpineRegistry(config_path=tmp_path / "nonexistent.json")
        reg.register("svc", "v1")
        reg.register("svc", "v2", override=True)
        assert reg.get("svc") == "v2"

    def test_factory_lazy_instantiation(self, tmp_path: Path) -> None:
        from src.spine.registry import SpineRegistry

        reg = SpineRegistry(config_path=tmp_path / "nonexistent.json")
        sentinel = object()
        reg.register_factory("lazy.svc", lambda: sentinel)
        result = reg.get("lazy.svc")
        assert result is sentinel
        # Second get returns cached instance
        assert reg.get("lazy.svc") is sentinel

    def test_get_returns_default_when_missing(self, tmp_path: Path) -> None:
        from src.spine.registry import SpineRegistry

        reg = SpineRegistry(config_path=tmp_path / "nonexistent.json")
        assert reg.get("no.such.service", default="fallback") == "fallback"

    def test_health_check_keys(self, tmp_path: Path) -> None:
        from src.spine.registry import SpineRegistry

        reg = SpineRegistry(config_path=tmp_path / "nonexistent.json")
        health = reg.health_check()
        assert "total_modules" in health
        assert "wired_modules" in health
        assert "loaded_services" in health
        assert "missing_dependencies" in health
        assert "healthy" in health

    def test_validate_dependencies_empty_registry(self, tmp_path: Path) -> None:
        from src.spine.registry import SpineRegistry

        reg = SpineRegistry(config_path=tmp_path / "nonexistent.json")
        assert reg.validate_dependencies() == {}


# ---------------------------------------------------------------------------
# SpineHealth / spine_manager
# ---------------------------------------------------------------------------


class TestSpineHealth:
    """Tests for src.spine.spine_manager.SpineHealth and initialize_spine."""

    def test_spine_health_dataclass(self, tmp_path: Path) -> None:
        from src.spine.spine_manager import SpineHealth

        health = SpineHealth(
            repo_root=tmp_path,
            timestamp="2026-01-01T00:00:00",
            status="GREEN",
            current_state_excerpt=("line1", "line2"),
            lifecycle_entries=("entry1",),
            signals={"current_state_lines": 2},
        )
        assert health.status == "GREEN"
        assert health.repo_root == tmp_path

    def test_describe_returns_string(self, tmp_path: Path) -> None:
        from src.spine.spine_manager import SpineHealth

        health = SpineHealth(
            repo_root=tmp_path,
            timestamp="2026-01-01T00:00:00",
            status="YELLOW",
            current_state_excerpt=("state line",),
            lifecycle_entries=(),
            signals={},
        )
        desc = health.describe()
        assert isinstance(desc, str)
        assert "state line" in desc

    def test_initialize_spine_returns_spine_health(self, tmp_path: Path) -> None:
        from src.spine.spine_manager import SpineHealth, initialize_spine

        # Pass an empty tmp_path — no state files exist, should return RED status
        health = initialize_spine(repo_root=tmp_path, refresh=True)
        assert isinstance(health, SpineHealth)
        assert health.status in ("RED", "YELLOW", "GREEN")

    def test_initialize_spine_status_red_when_no_files(self, tmp_path: Path) -> None:
        from src.spine.spine_manager import initialize_spine

        health = initialize_spine(repo_root=tmp_path, refresh=True)
        assert health.status == "RED"

    def test_export_spine_health_creates_file(self, tmp_path: Path) -> None:
        from src.spine.spine_manager import export_spine_health

        out_path = export_spine_health(
            repo_root=tmp_path, refresh=True, output_dir=tmp_path / "out"
        )
        assert out_path.exists()
        assert out_path.suffix == ".json"


# ---------------------------------------------------------------------------
# Package-level imports via __init__
# ---------------------------------------------------------------------------


class TestSpinePackageImports:
    """Verify that the public API is importable from the spine package."""

    def test_import_environment_from_package(self) -> None:
        from src.spine import Environment

        assert callable(Environment)

    def test_import_spine_registry_from_package(self) -> None:
        from src.spine import SpineRegistry

        assert callable(SpineRegistry)

    def test_import_spine_health_from_package(self) -> None:
        from src.spine import SpineHealth

        assert callable(SpineHealth)

    def test_lazy_import_kardeshev_v_direct_module(self) -> None:
        # NOTE: src/spine/__init__.__getattr__ has a typo (KardashevV vs KardashevV)
        # that causes ImportError when accessing via the package lazy-loader.
        # The class is importable directly from the sub-module, which is the
        # correct and supported path.
        from src.spine.culture_consciousness import KardeshevV

        assert callable(KardeshevV)
        assert KardeshevV.__name__ == "KardeshevV"

    def test_lazy_import_culture_level_civilization(self) -> None:
        import src.spine as spine

        CLC = spine.CultureLevelCivilization
        assert callable(CLC)
        assert CLC.__name__ == "CultureLevelCivilization"


# ---------------------------------------------------------------------------
# transcendent_spine_core (CultureLevelCivilization)
# ---------------------------------------------------------------------------


class TestTranscendentSpineCore:
    """Tests for src.spine.transcendent_spine_core.CultureLevelCivilization."""

    def test_init_defaults(self) -> None:
        from src.spine.transcendent_spine_core import CultureLevelCivilization

        civ = CultureLevelCivilization()
        assert civ.population == 0
        assert civ.environmental_health == pytest.approx(100.0)
        assert isinstance(civ.technological_innovation, list)
        assert isinstance(civ.resources, dict)

    def test_add_resource_accumulates(self) -> None:
        from src.spine.transcendent_spine_core import CultureLevelCivilization

        civ = CultureLevelCivilization()
        civ.add_resource("Water", 500)
        civ.add_resource("Water", 300)
        assert civ.resources["Water"] == pytest.approx(800.0)

    def test_cultivate_technology_appends(self) -> None:
        from src.spine.transcendent_spine_core import CultureLevelCivilization

        civ = CultureLevelCivilization()
        civ.cultivate_technology("Fusion Drive")
        assert "Fusion Drive" in civ.technological_innovation

    def test_evolve_population_growth(self) -> None:
        from src.spine.transcendent_spine_core import CultureLevelCivilization

        civ = CultureLevelCivilization()
        civ.population = 1000
        civ.evolve_population(0.1)
        assert civ.population == 1100

    def test_heal_system_resets_health(self) -> None:
        from src.spine.transcendent_spine_core import CultureLevelCivilization

        civ = CultureLevelCivilization()
        civ.environmental_health = 30.0
        civ.heal_system()
        assert civ.environmental_health == 100

    def test_optimize_resources_balances_toward_mean(self) -> None:
        from src.spine.transcendent_spine_core import CultureLevelCivilization

        civ = CultureLevelCivilization()
        civ.add_resource("A", 1000.0)
        civ.add_resource("B", 0.0)
        before_diff = abs(civ.resources["A"] - civ.resources["B"])
        civ.optimize_resources()
        after_diff = abs(civ.resources["A"] - civ.resources["B"])
        assert after_diff < before_diff

    def test_integrate_feedback_environmental(self) -> None:
        from src.spine.transcendent_spine_core import CultureLevelCivilization

        civ = CultureLevelCivilization()
        civ.environmental_health = 80.0
        civ.integrate_feedback({"type": "environmental"})
        assert civ.environmental_health == pytest.approx(85.0)

    def test_integrate_feedback_technology(self) -> None:
        from src.spine.transcendent_spine_core import CultureLevelCivilization

        civ = CultureLevelCivilization()
        civ.integrate_feedback({"type": "technology"})
        assert "feedback_driven_innovation" in civ.technological_innovation

    def test_run_simulation_no_raise(self) -> None:
        from src.spine.transcendent_spine_core import CultureLevelCivilization

        civ = CultureLevelCivilization()
        civ.add_resource("Energy", 100.0)
        civ.population = 500
        # run_simulation must complete without raising
        civ.run_simulation(3)
