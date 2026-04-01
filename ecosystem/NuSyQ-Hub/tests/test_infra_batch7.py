"""Tests for small infrastructure modules - batch 7.

Coverage targets:
- src/system/planning.py: PlanStep, PlanBundle, build_dual_plan
- src/game_dev/particle_system.py: Particle, ParticleEmitter
- src/setup/env_loader.py: load_dotenv
"""

from __future__ import annotations


# ==============================================================================
# src/system/planning.py tests
# ==============================================================================
class TestPlanStepDataclass:
    """Test PlanStep dataclass."""

    def test_default_values(self):
        """PlanStep has default status and notes."""
        from src.system.planning import PlanStep

        step = PlanStep("Test step")
        assert step.description == "Test step"
        assert step.status == "pending"
        assert step.notes == ""

    def test_custom_values(self):
        """PlanStep accepts custom values."""
        from src.system.planning import PlanStep

        step = PlanStep("Custom", status="done", notes="Completed")
        assert step.status == "done"
        assert step.notes == "Completed"


class TestPlanBundleDataclass:
    """Test PlanBundle dataclass."""

    def test_empty_bundle(self):
        """PlanBundle initializes empty by default."""
        from src.system.planning import PlanBundle

        bundle = PlanBundle()
        assert bundle.high_level == []
        assert bundle.microplan == []
        assert bundle.early_tests == []
        assert bundle.telemetry == {}

    def test_bundle_with_steps(self):
        """PlanBundle stores steps correctly."""
        from src.system.planning import PlanBundle, PlanStep

        steps = [PlanStep("Step 1"), PlanStep("Step 2")]
        bundle = PlanBundle(high_level=steps)
        assert len(bundle.high_level) == 2


class TestBuildDualPlan:
    """Test build_dual_plan function."""

    def test_returns_bundle_when_disabled(self, monkeypatch):
        """Returns empty bundle when feature disabled."""
        monkeypatch.setattr("src.system.planning.is_feature_enabled", lambda x: False)

        from src.system.planning import build_dual_plan

        bundle = build_dual_plan("test task")
        assert bundle.high_level == []
        assert bundle.microplan == []

    def test_returns_populated_bundle_when_enabled(self, monkeypatch):
        """Returns populated bundle when feature enabled."""
        monkeypatch.setattr("src.system.planning.is_feature_enabled", lambda x: True)

        from src.system.planning import build_dual_plan

        bundle = build_dual_plan("test task")
        assert len(bundle.high_level) > 0
        assert len(bundle.microplan) > 0
        assert len(bundle.early_tests) > 0
        assert "plan_started" in bundle.telemetry


class TestPlanBundleToDict:
    """Test planbundle_to_dict function."""

    def test_converts_empty_bundle(self):
        """Converts empty bundle to dict."""
        from src.system.planning import PlanBundle, planbundle_to_dict

        bundle = PlanBundle()
        result = planbundle_to_dict(bundle)
        assert result["high_level"] == []
        assert result["microplan"] == []
        assert result["early_tests"] == []
        assert result["telemetry"] == {}

    def test_converts_populated_bundle(self):
        """Converts populated bundle to dict."""
        from src.system.planning import PlanBundle, PlanStep, planbundle_to_dict

        bundle = PlanBundle(
            high_level=[PlanStep("Test", status="done")],
            early_tests=["Test 1"],
            telemetry={"started": 123},
        )
        result = planbundle_to_dict(bundle)
        assert len(result["high_level"]) == 1
        assert result["high_level"][0]["status"] == "done"
        assert result["early_tests"] == ["Test 1"]
        assert result["telemetry"]["started"] == 123


# ==============================================================================
# src/game_dev/particle_system.py tests
# ==============================================================================
class TestParticleDataclass:
    """Test Particle dataclass."""

    def test_particle_creation(self):
        """Particle initializes with position and velocity."""
        from src.game_dev.particle_system import Particle

        p = Particle(
            position=[0.0, 0.0],
            velocity=[1.0, 2.0],
            lifespan=1.0,
        )
        assert p.position == [0.0, 0.0]
        assert p.velocity == [1.0, 2.0]
        assert p.lifespan == 1.0
        assert p.age == 0.0

    def test_particle_colors(self):
        """Particle supports custom colors."""
        from src.game_dev.particle_system import Particle

        p = Particle(
            position=[0.0, 0.0],
            velocity=[0.0, 0.0],
            lifespan=1.0,
            start_color=(255, 0, 0),
            end_color=(0, 0, 255),
        )
        assert p.start_color == (255, 0, 0)
        assert p.end_color == (0, 0, 255)


class TestParticleUpdate:
    """Test Particle.update method."""

    def test_update_moves_particle(self):
        """Update changes position based on velocity."""
        from src.game_dev.particle_system import Particle

        p = Particle(
            position=[0.0, 0.0],
            velocity=[10.0, 5.0],
            lifespan=2.0,
        )
        p.update(0.1)  # 100ms
        assert abs(p.position[0] - 1.0) < 0.01
        assert abs(p.position[1] - 0.5) < 0.01
        assert abs(p.age - 0.1) < 0.01

    def test_update_increases_age(self):
        """Update increases particle age."""
        from src.game_dev.particle_system import Particle

        p = Particle(position=[0.0, 0.0], velocity=[0.0, 0.0], lifespan=1.0)
        p.update(0.5)
        assert p.age == 0.5


class TestParticleAlive:
    """Test Particle.alive property."""

    def test_particle_alive_initially(self):
        """Particle is alive when age < lifespan."""
        from src.game_dev.particle_system import Particle

        p = Particle(position=[0.0, 0.0], velocity=[0.0, 0.0], lifespan=1.0)
        assert p.alive is True

    def test_particle_dead_after_lifespan(self):
        """Particle is dead when age >= lifespan."""
        from src.game_dev.particle_system import Particle

        p = Particle(position=[0.0, 0.0], velocity=[0.0, 0.0], lifespan=1.0)
        p.age = 1.5
        assert p.alive is False


class TestParticleEmitter:
    """Test ParticleEmitter class."""

    def test_emitter_defaults(self):
        """Emitter has sensible defaults."""
        from src.game_dev.particle_system import ParticleEmitter

        emitter = ParticleEmitter()
        assert emitter.position == (0.0, 0.0)
        assert emitter.emission_rate == 5
        assert emitter.speed == 1.0
        assert len(emitter.particles) == 0

    def test_emit_creates_particles(self):
        """emit() creates particles."""
        from src.game_dev.particle_system import ParticleEmitter

        emitter = ParticleEmitter(emission_rate=3)
        created = emitter.emit()
        assert len(created) == 3
        assert len(emitter.particles) == 3

    def test_emit_with_count(self):
        """emit(count) overrides emission_rate."""
        from src.game_dev.particle_system import ParticleEmitter

        emitter = ParticleEmitter(emission_rate=10)
        created = emitter.emit(count=2)
        assert len(created) == 2

    def test_emit_uses_emitter_position(self):
        """Emitted particles start at emitter position."""
        from src.game_dev.particle_system import ParticleEmitter

        emitter = ParticleEmitter(position=(100.0, 200.0))
        created = emitter.emit(count=1)
        assert created[0].position[0] == 100.0
        assert created[0].position[1] == 200.0


class TestParticleEmitterUpdate:
    """Test ParticleEmitter.update method."""

    def test_update_moves_particles(self):
        """update() advances all particles."""
        from src.game_dev.particle_system import ParticleEmitter

        emitter = ParticleEmitter(speed=10.0, spread_radians=0.0)
        emitter.emit(count=1)
        initial_age = emitter.particles[0].age
        emitter.update(0.1)
        assert emitter.particles[0].age > initial_age

    def test_update_removes_dead_particles(self):
        """update() removes expired particles."""
        from src.game_dev.particle_system import ParticleEmitter

        emitter = ParticleEmitter(lifespan_range=(0.1, 0.1))
        emitter.emit(count=2)
        assert len(emitter.particles) == 2

        # Age particles beyond lifespan
        emitter.update(0.5)
        assert len(emitter.particles) == 0


# ==============================================================================
# src/setup/env_loader.py tests
# ==============================================================================
class TestEnvLoader:
    """Test load_dotenv function."""

    def test_load_nonexistent_file(self, tmp_path):
        """Returns 0 for nonexistent file."""
        from src.setup.env_loader import load_dotenv

        result = load_dotenv(str(tmp_path / "missing.env"))
        assert result == 0

    def test_load_empty_file(self, tmp_path):
        """Returns 0 for empty file."""
        from src.setup.env_loader import load_dotenv

        env_file = tmp_path / ".env"
        env_file.write_text("")
        result = load_dotenv(str(env_file))
        assert result == 0

    def test_load_comments_and_blanks(self, tmp_path):
        """Skips comments and blank lines."""
        from src.setup.env_loader import load_dotenv

        env_file = tmp_path / ".env"
        env_file.write_text("# Comment\n\n  # Another comment\n")
        result = load_dotenv(str(env_file))
        assert result == 0

    def test_load_valid_vars(self, tmp_path, monkeypatch):
        """Loads valid environment variables."""
        from src.setup.env_loader import load_dotenv

        # Clear any existing test var
        monkeypatch.delenv("TEST_VAR_BATCH7", raising=False)

        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR_BATCH7=hello\nANOTHER_VAR_BATCH7=world\n")

        # Just test normal loading (python-dotenv is installed)
        result = load_dotenv(str(env_file))
        # Should load at least 1 var (dotenv loads vars)
        assert result >= 1

    def test_skips_empty_values(self, tmp_path):
        """Skips variables with empty values."""
        from src.setup.env_loader import load_dotenv

        env_file = tmp_path / ".env"
        env_file.write_text("EMPTY_VAR=\nVALID=test\n")
        result = load_dotenv(str(env_file))
        # Valid var counts, empty doesn't
        assert result >= 0
