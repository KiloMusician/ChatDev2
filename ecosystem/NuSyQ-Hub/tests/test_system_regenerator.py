"""Tests for src.healing.system_regenerator module."""


class TestModuleImports:
    """Test module imports."""

    def test_import_module(self):
        from src.healing import system_regenerator

        assert system_regenerator is not None

    def test_import_environment(self):
        from src.healing.system_regenerator import Environment

        assert Environment is not None

    def test_import_society(self):
        from src.healing.system_regenerator import Society

        assert Society is not None

    def test_import_resource_management(self):
        from src.healing.system_regenerator import ResourceManagement

        assert ResourceManagement is not None

    def test_import_healing_system(self):
        from src.healing.system_regenerator import HealingSystem

        assert HealingSystem is not None

    def test_import_optimization_engine(self):
        from src.healing.system_regenerator import OptimizationEngine

        assert OptimizationEngine is not None


class TestEnvironmentInit:
    """Test Environment initialization."""

    def test_init_with_basic_resources(self):
        from src.healing.system_regenerator import Environment

        resources = {"water": 100, "air": 200}
        env = Environment(resources, health_index=0.5)

        assert env.resources["water"] == 100.0
        assert env.resources["air"] == 200.0
        assert env.health_index == 0.5

    def test_init_converts_ints_to_floats(self):
        from src.healing.system_regenerator import Environment

        resources = {"energy": 500}
        env = Environment(resources, health_index=0.8)

        assert isinstance(env.resources["energy"], float)

    def test_init_empty_resources(self):
        from src.healing.system_regenerator import Environment

        env = Environment({}, health_index=1.0)

        assert env.resources == {}
        assert env.health_index == 1.0


class TestEnvironmentOptimizeResources:
    """Test Environment.optimize_resources method."""

    def test_optimize_low_health(self, capsys):
        from src.healing.system_regenerator import Environment

        resources = {"water": 1000.0}
        env = Environment(resources, health_index=0.3)

        env.optimize_resources()

        # Low health means resources conserved (multiplied by 0.95)
        assert env.resources["water"] == 1000.0 * 0.95

    def test_optimize_high_health(self, capsys):
        from src.healing.system_regenerator import Environment

        resources = {"water": 1000.0}
        env = Environment(resources, health_index=0.8)

        env.optimize_resources()

        # High health: efficiency factor = 0.95 + (0.8 * 0.1) = 1.03
        expected = 1000.0 * 1.03
        assert abs(env.resources["water"] - expected) < 0.01

    def test_optimize_prints_efficiency(self, capsys):
        from src.healing.system_regenerator import Environment

        env = Environment({"water": 100.0}, health_index=0.5)
        env.optimize_resources()

        captured = capsys.readouterr()
        assert "efficiency factor" in captured.out


class TestEnvironmentHealEnvironment:
    """Test Environment.heal_environment method."""

    def test_heal_increases_health(self, capsys):
        from src.healing.system_regenerator import Environment

        env = Environment({"energy": 5000.0}, health_index=0.3)
        initial_health = env.health_index

        env.heal_environment()

        assert env.health_index > initial_health

    def test_heal_caps_at_one(self, capsys):
        from src.healing.system_regenerator import Environment

        env = Environment({"energy": 100000.0}, health_index=0.99)
        env.heal_environment()

        assert env.health_index <= 1.0

    def test_heal_at_max_health(self, capsys):
        from src.healing.system_regenerator import Environment

        env = Environment({"energy": 1000.0}, health_index=1.0)
        env.heal_environment()

        captured = capsys.readouterr()
        assert "optimal health" in captured.out

    def test_heal_prints_result(self, capsys):
        from src.healing.system_regenerator import Environment

        env = Environment({"energy": 1000.0}, health_index=0.5)
        env.heal_environment()

        captured = capsys.readouterr()
        assert "healed" in captured.out


class TestSocietyInit:
    """Test Society initialization."""

    def test_init_basic(self):
        from src.healing.system_regenerator import Society

        society = Society(population=1000000, technology_level=5)

        assert society.population == 1000000
        assert society.technology_level == 5

    def test_init_small_population(self):
        from src.healing.system_regenerator import Society

        society = Society(population=100, technology_level=1)

        assert society.population == 100
        assert society.technology_level == 1


class TestSocietyEvolveSociety:
    """Test Society.evolve_society method."""

    def test_evolve_large_population_advances(self, capsys):
        from src.healing.system_regenerator import Society

        society = Society(population=2000000, technology_level=5)
        society.evolve_society()

        assert society.technology_level == 6

    def test_evolve_small_population_below_threshold(self, capsys):
        from src.healing.system_regenerator import Society

        society = Society(population=100, technology_level=5)
        initial_level = society.technology_level

        society.evolve_society()

        # Small population means low evolution chance
        assert society.technology_level == initial_level

    def test_evolve_max_technology(self, capsys):
        from src.healing.system_regenerator import Society

        society = Society(population=1000000, technology_level=10)
        society.evolve_society()

        captured = capsys.readouterr()
        assert "maximum technology" in captured.out
        assert society.technology_level == 10


class TestResourceManagementInit:
    """Test ResourceManagement initialization."""

    def test_init_with_environment(self):
        from src.healing.system_regenerator import Environment, ResourceManagement

        env = Environment({"water": 100.0}, health_index=0.5)
        rm = ResourceManagement(env)

        assert rm.environment is env


class TestResourceManagementAllocateResources:
    """Test ResourceManagement.allocate_resources method."""

    def test_allocate_healthy_environment(self, capsys):
        from src.healing.system_regenerator import Environment, ResourceManagement

        env = Environment({"water": 1000.0}, health_index=0.8)
        rm = ResourceManagement(env)

        rm.allocate_resources()

        captured = capsys.readouterr()
        assert "allocated" in captured.out

    def test_allocate_critical_health_heals_first(self, capsys):
        from src.healing.system_regenerator import Environment, ResourceManagement

        env = Environment({"water": 1000.0}, health_index=0.2)
        rm = ResourceManagement(env)

        rm.allocate_resources()

        captured = capsys.readouterr()
        assert "critical" in captured.out.lower() or "heal" in captured.out.lower()


class TestHealingSystemInit:
    """Test HealingSystem initialization."""

    def test_init_with_environment(self):
        from src.healing.system_regenerator import Environment, HealingSystem

        env = Environment({"energy": 500.0}, health_index=0.7)
        hs = HealingSystem(env)

        assert hs.environment is env


class TestHealingSystemInitiateHealing:
    """Test HealingSystem.initiate_healing method."""

    def test_initiate_calls_heal(self, capsys):
        from src.healing.system_regenerator import Environment, HealingSystem

        env = Environment({"energy": 1000.0}, health_index=0.5)
        hs = HealingSystem(env)
        initial_health = env.health_index

        hs.initiate_healing()

        assert env.health_index > initial_health


class TestOptimizationEngineInit:
    """Test OptimizationEngine initialization."""

    def test_init_with_society_and_environment(self):
        from src.healing.system_regenerator import (
            Environment,
            OptimizationEngine,
            Society,
        )

        env = Environment({"water": 100.0}, health_index=0.5)
        society = Society(population=1000, technology_level=3)
        engine = OptimizationEngine(society, env)

        assert engine.society is society
        assert engine.environment is env


class TestOptimizationEngineRunCycle:
    """Test OptimizationEngine.run_optimization_cycle method."""

    def test_run_cycle_evolves_and_heals(self, capsys):
        from src.healing.system_regenerator import (
            Environment,
            OptimizationEngine,
            Society,
        )

        env = Environment({"water": 1000.0, "food": 500.0}, health_index=0.6)
        society = Society(population=2000000, technology_level=5)
        engine = OptimizationEngine(society, env)

        initial_tech = society.technology_level

        engine.run_optimization_cycle()

        # Should have advanced technology and modified health
        assert society.technology_level >= initial_tech
        captured = capsys.readouterr()
        assert len(captured.out) > 0  # Should have printed progress


class TestMainFunction:
    """Test main function."""

    def test_main_runs_without_error(self, capsys):
        from src.healing.system_regenerator import main

        # Should run 10 optimization cycles without error
        main()

        captured = capsys.readouterr()
        assert len(captured.out) > 0
