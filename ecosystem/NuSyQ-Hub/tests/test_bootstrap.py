"""Tests for src/core/bootstrap.py - Unified Bootstrap System.

Coverage targets:
- SystemComponent dataclass
- BootResult dataclass
- SystemBootstrap class:
  - register() - registers components with options
  - boot() - boots all components, tracks timing/errors
  - get() - retrieves initialized components
  - is_ready() - checks component readiness
  - status() - returns status dictionary
"""

from unittest.mock import MagicMock

from src.core.bootstrap import SystemComponent, BootResult, SystemBootstrap


class TestSystemComponent:
    """Tests for SystemComponent dataclass."""

    def test_default_values(self):
        """Verify default values for SystemComponent."""
        component = SystemComponent(
            name="TestComponent",
            init_fn=lambda: "initialized",
        )
        assert component.name == "TestComponent"
        assert component.instance is None
        assert component.status == "pending"
        assert component.error is None
        assert component.boot_time_ms == 0.0
        assert component.required is False

    def test_custom_values(self):
        """Verify custom values are set correctly."""
        mock_fn = MagicMock()
        component = SystemComponent(
            name="RequiredComponent",
            init_fn=mock_fn,
            instance="already_set",
            status="ready",
            error="some error",
            boot_time_ms=123.45,
            required=True,
        )
        assert component.name == "RequiredComponent"
        assert component.init_fn is mock_fn
        assert component.instance == "already_set"
        assert component.status == "ready"
        assert component.error == "some error"
        assert component.boot_time_ms == 123.45
        assert component.required is True


class TestBootResult:
    """Tests for BootResult dataclass."""

    def test_success_result(self):
        """Verify successful BootResult construction."""
        result = BootResult(
            success=True,
            systems_ready=3,
            systems_failed=0,
            systems_disabled=1,
            total_boot_time_ms=100.5,
            components={},
        )
        assert result.success is True
        assert result.systems_ready == 3
        assert result.systems_failed == 0
        assert result.systems_disabled == 1
        assert result.total_boot_time_ms == 100.5
        assert result.errors == []  # default factory

    def test_failure_result_with_errors(self):
        """Verify failed BootResult with errors list."""
        result = BootResult(
            success=False,
            systems_ready=1,
            systems_failed=2,
            systems_disabled=0,
            total_boot_time_ms=50.0,
            components={"comp1": MagicMock()},
            errors=["Component1: failed", "Component2: timeout"],
        )
        assert result.success is False
        assert result.systems_failed == 2
        assert len(result.errors) == 2
        assert "Component1: failed" in result.errors


class TestSystemBootstrapRegister:
    """Tests for SystemBootstrap.register() method."""

    def test_register_basic_component(self):
        """Register a basic component."""
        bootstrap = SystemBootstrap(name="TestSystem")
        result = bootstrap.register("MyComponent", lambda: "instance")

        # Returns self for chaining
        assert result is bootstrap
        assert "MyComponent" in bootstrap.components
        assert bootstrap.components["MyComponent"].status == "pending"
        assert bootstrap.components["MyComponent"].required is False

    def test_register_required_component(self):
        """Register a required component."""
        bootstrap = SystemBootstrap()
        bootstrap.register("Required", lambda: None, required=True)

        assert bootstrap.components["Required"].required is True

    def test_register_disabled_component(self):
        """Register a disabled component."""
        bootstrap = SystemBootstrap()
        bootstrap.register("Disabled", lambda: None, enabled=False)

        assert bootstrap.components["Disabled"].status == "disabled"

    def test_register_chaining(self):
        """Verify method chaining works."""
        bootstrap = SystemBootstrap()
        bootstrap.register("A", lambda: 1).register("B", lambda: 2).register("C", lambda: 3)

        assert len(bootstrap.components) == 3
        assert "A" in bootstrap.components
        assert "B" in bootstrap.components
        assert "C" in bootstrap.components


class TestSystemBootstrapBoot:
    """Tests for SystemBootstrap.boot() method."""

    def test_boot_single_component_success(self):
        """Boot a single component successfully."""
        bootstrap = SystemBootstrap()
        mock_instance = {"key": "value"}
        bootstrap.register("TestComp", lambda: mock_instance)

        result = bootstrap.boot()

        assert result.success is True
        assert result.systems_ready == 1
        assert result.systems_failed == 0
        assert result.systems_disabled == 0
        assert result.total_boot_time_ms > 0
        assert bootstrap.components["TestComp"].status == "ready"
        assert bootstrap.components["TestComp"].instance == mock_instance

    def test_boot_multiple_components(self):
        """Boot multiple components."""
        bootstrap = SystemBootstrap()
        bootstrap.register("A", lambda: "a_instance")
        bootstrap.register("B", lambda: "b_instance")
        bootstrap.register("C", lambda: "c_instance")

        result = bootstrap.boot()

        assert result.success is True
        assert result.systems_ready == 3
        assert bootstrap.get("A") == "a_instance"
        assert bootstrap.get("B") == "b_instance"
        assert bootstrap.get("C") == "c_instance"

    def test_boot_skips_disabled_components(self):
        """Verify disabled components are skipped."""
        bootstrap = SystemBootstrap()
        bootstrap.register("Enabled", lambda: "enabled")
        bootstrap.register("Disabled", lambda: "disabled", enabled=False)

        result = bootstrap.boot()

        assert result.success is True
        assert result.systems_ready == 1
        assert result.systems_disabled == 1
        assert bootstrap.components["Disabled"].status == "disabled"
        assert bootstrap.components["Disabled"].instance is None

    def test_boot_handles_component_failure(self):
        """Verify non-required component failure doesn't fail boot."""
        bootstrap = SystemBootstrap()
        bootstrap.register("Good", lambda: "good")
        bootstrap.register("Bad", lambda: (_ for _ in ()).throw(ValueError("init failed")))

        result = bootstrap.boot()

        # Boot still succeeds because Bad is not required
        assert result.success is True
        assert result.systems_ready == 1
        assert result.systems_failed == 1
        assert "Bad: init failed" in result.errors

    def test_boot_fails_on_required_component_failure(self):
        """Verify required component failure fails the boot."""
        bootstrap = SystemBootstrap()
        bootstrap.register("Good", lambda: "good")
        bootstrap.register(
            "RequiredBad",
            lambda: (_ for _ in ()).throw(RuntimeError("critical failure")),
            required=True,
        )

        result = bootstrap.boot()

        assert result.success is False
        assert result.systems_ready == 1
        assert result.systems_failed == 1
        assert bootstrap.components["RequiredBad"].error == "critical failure"

    def test_boot_records_timing(self):
        """Verify boot timing is recorded."""
        import time

        bootstrap = SystemBootstrap()
        bootstrap.register("SlowComponent", lambda: time.sleep(0.01) or "slow")

        result = bootstrap.boot()

        assert result.total_boot_time_ms >= 10  # At least 10ms
        assert bootstrap.components["SlowComponent"].boot_time_ms >= 10


class TestSystemBootstrapGet:
    """Tests for SystemBootstrap.get() method."""

    def test_get_ready_component(self):
        """Get a ready component returns instance."""
        bootstrap = SystemBootstrap()
        bootstrap.register("Comp", lambda: {"data": 123})
        bootstrap.boot()

        result = bootstrap.get("Comp")

        assert result == {"data": 123}

    def test_get_nonexistent_component(self):
        """Get non-existent component returns None."""
        bootstrap = SystemBootstrap()
        bootstrap.boot()

        result = bootstrap.get("DoesNotExist")

        assert result is None

    def test_get_pending_component(self):
        """Get component before boot returns None."""
        bootstrap = SystemBootstrap()
        bootstrap.register("Comp", lambda: "instance")

        # Before boot
        result = bootstrap.get("Comp")

        assert result is None

    def test_get_failed_component(self):
        """Get failed component returns None."""
        bootstrap = SystemBootstrap()
        bootstrap.register("Bad", lambda: (_ for _ in ()).throw(Exception("fail")))
        bootstrap.boot()

        result = bootstrap.get("Bad")

        assert result is None

    def test_get_disabled_component(self):
        """Get disabled component returns None."""
        bootstrap = SystemBootstrap()
        bootstrap.register("Disabled", lambda: "instance", enabled=False)
        bootstrap.boot()

        result = bootstrap.get("Disabled")

        assert result is None


class TestSystemBootstrapIsReady:
    """Tests for SystemBootstrap.is_ready() method."""

    def test_is_ready_true_for_ready_component(self):
        """is_ready returns True for ready components."""
        bootstrap = SystemBootstrap()
        bootstrap.register("Comp", lambda: "instance")
        bootstrap.boot()

        assert bootstrap.is_ready("Comp") is True

    def test_is_ready_false_for_nonexistent(self):
        """is_ready returns False for non-existent components."""
        bootstrap = SystemBootstrap()
        bootstrap.boot()

        assert bootstrap.is_ready("DoesNotExist") is False

    def test_is_ready_false_for_pending(self):
        """is_ready returns False for pending components."""
        bootstrap = SystemBootstrap()
        bootstrap.register("Comp", lambda: "instance")

        # Before boot
        assert bootstrap.is_ready("Comp") is False

    def test_is_ready_false_for_failed(self):
        """is_ready returns False for failed components."""
        bootstrap = SystemBootstrap()
        bootstrap.register("Bad", lambda: (_ for _ in ()).throw(Exception()))
        bootstrap.boot()

        assert bootstrap.is_ready("Bad") is False

    def test_is_ready_false_for_disabled(self):
        """is_ready returns False for disabled components."""
        bootstrap = SystemBootstrap()
        bootstrap.register("Disabled", lambda: "instance", enabled=False)
        bootstrap.boot()

        assert bootstrap.is_ready("Disabled") is False


class TestSystemBootstrapStatus:
    """Tests for SystemBootstrap.status() method."""

    def test_status_before_boot(self):
        """Status before boot shows booted=False."""
        bootstrap = SystemBootstrap()
        bootstrap.register("Comp", lambda: "instance")

        status = bootstrap.status()

        assert status["booted"] is False
        assert "Comp" in status["components"]
        assert status["components"]["Comp"]["status"] == "pending"

    def test_status_after_boot(self):
        """Status after boot shows component states."""
        bootstrap = SystemBootstrap()
        bootstrap.register("Good", lambda: "good")
        bootstrap.register("Disabled", lambda: "disabled", enabled=False)
        bootstrap.boot()

        status = bootstrap.status()

        assert status["booted"] is True
        assert status["components"]["Good"]["status"] == "ready"
        assert status["components"]["Disabled"]["status"] == "disabled"

    def test_status_includes_imports(self):
        """Status includes imports registry status."""
        bootstrap = SystemBootstrap()
        bootstrap.boot()

        status = bootstrap.status()

        assert "imports" in status


class TestSystemBootstrapIntegration:
    """Integration tests for SystemBootstrap."""

    def test_full_workflow(self):
        """Test full bootstrap workflow."""
        bootstrap = SystemBootstrap(name="IntegrationTest")

        # Register components
        bootstrap.register("Database", lambda: {"connected": True}, required=True)
        bootstrap.register("Cache", lambda: {"size": 100})
        bootstrap.register("Analytics", lambda: None, enabled=False)

        # Boot
        result = bootstrap.boot()

        # Verify result
        assert result.success is True
        assert result.systems_ready == 2
        assert result.systems_disabled == 1

        # Verify components accessible
        assert bootstrap.get("Database") == {"connected": True}
        assert bootstrap.get("Cache") == {"size": 100}
        assert bootstrap.get("Analytics") is None

        # Verify status
        status = bootstrap.status()
        assert status["booted"] is True

    def test_boot_idempotency(self):
        """Boot can be called multiple times safely."""
        bootstrap = SystemBootstrap()
        call_count = 0

        def counting_init():
            nonlocal call_count
            call_count += 1
            return call_count

        bootstrap.register("Counter", counting_init)

        # First boot
        result1 = bootstrap.boot()
        assert result1.success is True
        assert bootstrap.get("Counter") == 1

        # Second boot - re-initializes
        result2 = bootstrap.boot()
        assert result2.success is True
        # Instance is updated
        assert bootstrap.get("Counter") == 2
        assert call_count == 2
