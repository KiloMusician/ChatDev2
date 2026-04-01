"""Tests for src/utils/graceful_shutdown.py - Graceful shutdown utilities.

Tests shutdown phases, coordination, and monitoring loop shutdown capabilities.
"""

import platform
import signal
import threading
import time
from unittest.mock import MagicMock

import pytest
from src.utils.graceful_shutdown import (
    GracefulShutdownMixin,
    MonitoringLoopMixin,
    ShutdownConfig,
    ShutdownCoordinator,
    ShutdownPhase,
    timeout,
)

# =============================================================================
# Test ShutdownPhase Enum
# =============================================================================


class TestShutdownPhase:
    """Tests for ShutdownPhase enum."""

    def test_running_phase_exists(self) -> None:
        """RUNNING phase exists."""
        assert ShutdownPhase.RUNNING.value == "running"

    def test_shutdown_requested_phase(self) -> None:
        """SHUTDOWN_REQUESTED phase exists."""
        assert ShutdownPhase.SHUTDOWN_REQUESTED.value == "shutdown_requested"

    def test_graceful_stopping_phase(self) -> None:
        """GRACEFUL_STOPPING phase exists."""
        assert ShutdownPhase.GRACEFUL_STOPPING.value == "graceful_stopping"

    def test_force_stopping_phase(self) -> None:
        """FORCE_STOPPING phase exists."""
        assert ShutdownPhase.FORCE_STOPPING.value == "force_stopping"

    def test_stopped_phase(self) -> None:
        """STOPPED phase exists."""
        assert ShutdownPhase.STOPPED.value == "stopped"

    def test_all_phases_count(self) -> None:
        """All 5 phases are defined."""
        assert len(ShutdownPhase) == 5


# =============================================================================
# Test ShutdownConfig
# =============================================================================


class TestShutdownConfig:
    """Tests for ShutdownConfig dataclass."""

    def test_default_graceful_timeout(self) -> None:
        """Default graceful_timeout is 30 seconds."""
        config = ShutdownConfig()
        assert config.graceful_timeout == 30.0

    def test_default_force_timeout(self) -> None:
        """Default force_timeout is 10 seconds."""
        config = ShutdownConfig()
        assert config.force_timeout == 10.0

    def test_default_cleanup_timeout(self) -> None:
        """Default cleanup_timeout is 5 seconds."""
        config = ShutdownConfig()
        assert config.cleanup_timeout == 5.0

    def test_default_save_state_enabled(self) -> None:
        """Default save_state is True."""
        config = ShutdownConfig()
        assert config.save_state is True

    def test_default_log_progress_enabled(self) -> None:
        """Default log_progress is True."""
        config = ShutdownConfig()
        assert config.log_progress is True

    def test_default_signal_handlers(self) -> None:
        """Default signal handlers include SIGINT and SIGTERM."""
        config = ShutdownConfig()
        assert signal.SIGINT in config.signal_handlers
        assert signal.SIGTERM in config.signal_handlers

    def test_custom_graceful_timeout(self) -> None:
        """Custom graceful_timeout can be set."""
        config = ShutdownConfig(graceful_timeout=60.0)
        assert config.graceful_timeout == 60.0

    def test_custom_save_state_disabled(self) -> None:
        """save_state can be disabled."""
        config = ShutdownConfig(save_state=False)
        assert config.save_state is False


# =============================================================================
# Test GracefulShutdownMixin
# =============================================================================


class ConcreteShutdown(GracefulShutdownMixin):
    """Concrete implementation for testing."""

    def __init__(self, shutdown_config: ShutdownConfig | None = None) -> None:
        super().__init__(shutdown_config)
        self.impl_called = False

    def _graceful_shutdown_impl(self) -> None:
        """Implementation of graceful shutdown."""
        self.impl_called = True


class TestGracefulShutdownMixin:
    """Tests for GracefulShutdownMixin."""

    def test_initial_phase_is_running(self) -> None:
        """Initial phase is RUNNING."""
        obj = ConcreteShutdown()
        assert obj.shutdown_phase == ShutdownPhase.RUNNING

    def test_shutdown_not_requested_initially(self) -> None:
        """Shutdown not requested initially."""
        obj = ConcreteShutdown()
        assert obj.is_shutdown_requested() is False

    def test_request_shutdown_sets_event(self) -> None:
        """request_shutdown sets shutdown_requested event."""
        obj = ConcreteShutdown()
        obj.request_shutdown()
        assert obj.is_shutdown_requested() is True

    def test_request_shutdown_changes_phase(self) -> None:
        """request_shutdown changes phase to SHUTDOWN_REQUESTED."""
        obj = ConcreteShutdown()
        obj.request_shutdown()
        assert obj.shutdown_phase == ShutdownPhase.SHUTDOWN_REQUESTED

    def test_request_shutdown_with_reason(self) -> None:
        """request_shutdown accepts reason parameter."""
        obj = ConcreteShutdown()
        obj.request_shutdown(reason="Test reason")
        assert obj.is_shutdown_requested()

    def test_request_shutdown_only_once(self) -> None:
        """request_shutdown only works once."""
        obj = ConcreteShutdown()
        obj.request_shutdown()
        obj.shutdown_phase = ShutdownPhase.GRACEFUL_STOPPING
        obj.request_shutdown()  # Should not change phase
        assert obj.shutdown_phase == ShutdownPhase.GRACEFUL_STOPPING

    def test_register_cleanup_task(self) -> None:
        """register_cleanup_task adds task to list."""
        obj = ConcreteShutdown()
        task = MagicMock()
        obj.register_cleanup_task(task)
        assert task in obj.cleanup_tasks

    def test_register_state_saver(self) -> None:
        """register_state_saver adds saver to list."""
        obj = ConcreteShutdown()
        saver = MagicMock()
        obj.register_state_saver(saver)
        assert saver in obj.state_savers

    def test_execute_graceful_shutdown_calls_impl(self) -> None:
        """execute_graceful_shutdown calls _graceful_shutdown_impl."""
        obj = ConcreteShutdown()
        obj.request_shutdown()
        obj.execute_graceful_shutdown()
        assert obj.impl_called is True

    def test_execute_graceful_shutdown_calls_cleanup(self) -> None:
        """execute_graceful_shutdown calls cleanup tasks."""
        obj = ConcreteShutdown()
        task = MagicMock()
        obj.register_cleanup_task(task)
        obj.request_shutdown()
        obj.execute_graceful_shutdown()
        task.assert_called_once()

    def test_execute_graceful_shutdown_calls_state_savers(self) -> None:
        """execute_graceful_shutdown calls state savers when enabled."""
        obj = ConcreteShutdown(ShutdownConfig(save_state=True))
        saver = MagicMock()
        obj.register_state_saver(saver)
        obj.request_shutdown()
        obj.execute_graceful_shutdown()
        saver.assert_called_once()

    def test_execute_graceful_shutdown_skips_savers_when_disabled(self) -> None:
        """execute_graceful_shutdown skips state savers when disabled."""
        obj = ConcreteShutdown(ShutdownConfig(save_state=False))
        saver = MagicMock()
        obj.register_state_saver(saver)
        obj.request_shutdown()
        obj.execute_graceful_shutdown()
        saver.assert_not_called()

    def test_execute_graceful_shutdown_sets_stopped_phase(self) -> None:
        """execute_graceful_shutdown sets phase to STOPPED."""
        obj = ConcreteShutdown()
        obj.request_shutdown()
        obj.execute_graceful_shutdown()
        assert obj.shutdown_phase == ShutdownPhase.STOPPED

    def test_execute_graceful_shutdown_sets_complete_event(self) -> None:
        """execute_graceful_shutdown sets shutdown_complete event."""
        obj = ConcreteShutdown()
        obj.request_shutdown()
        obj.execute_graceful_shutdown()
        assert obj.shutdown_complete.is_set()

    def test_wait_for_shutdown_returns_immediately_when_complete(self) -> None:
        """wait_for_shutdown returns immediately when already complete."""
        obj = ConcreteShutdown()
        obj.request_shutdown()
        obj.execute_graceful_shutdown()
        result = obj.wait_for_shutdown(wait_timeout=0.1)
        assert result is True

    def test_wait_for_shutdown_times_out(self) -> None:
        """wait_for_shutdown times out when not complete."""
        obj = ConcreteShutdown()
        result = obj.wait_for_shutdown(wait_timeout=0.01)
        assert result is False


# =============================================================================
# Test ShutdownCoordinator
# =============================================================================


class TestShutdownCoordinator:
    """Tests for ShutdownCoordinator."""

    def test_create_with_default_config(self) -> None:
        """Create coordinator with default config."""
        coord = ShutdownCoordinator()
        assert coord.config.graceful_timeout == 30.0

    def test_create_with_custom_config(self) -> None:
        """Create coordinator with custom config."""
        config = ShutdownConfig(graceful_timeout=60.0)
        coord = ShutdownCoordinator(config)
        assert coord.config.graceful_timeout == 60.0

    def test_register_component(self) -> None:
        """register_component adds component."""
        coord = ShutdownCoordinator()
        component = ConcreteShutdown()
        coord.register_component("test", component)
        assert "test" in coord.components
        assert coord.components["test"] is component

    def test_register_component_with_priority(self) -> None:
        """register_component respects priority order."""
        coord = ShutdownCoordinator()
        comp1 = ConcreteShutdown()
        comp2 = ConcreteShutdown()
        coord.register_component("low", comp1, priority=1)
        coord.register_component("high", comp2, priority=10)
        # High priority should be first (shuts down first)
        assert coord.shutdown_order[0] == "high"

    def test_shutdown_all_requests_shutdown(self) -> None:
        """shutdown_all requests shutdown for all components."""
        coord = ShutdownCoordinator()
        comp1 = ConcreteShutdown()
        comp2 = ConcreteShutdown()
        coord.register_component("comp1", comp1)
        coord.register_component("comp2", comp2)

        # Execute shutdown in background then trigger complete
        def trigger_complete():
            time.sleep(0.01)
            comp1.execute_graceful_shutdown()
            comp2.execute_graceful_shutdown()

        t = threading.Thread(target=trigger_complete)
        t.start()

        coord.config.graceful_timeout = 0.1
        coord.shutdown_all("Test")

        t.join()
        assert comp1.is_shutdown_requested()
        assert comp2.is_shutdown_requested()

    def test_install_signal_handlers(self) -> None:
        """install_signal_handlers sets flag."""
        coord = ShutdownCoordinator()
        coord.install_signal_handlers()
        assert coord.signal_handlers_installed is True

    def test_install_signal_handlers_only_once(self) -> None:
        """install_signal_handlers only installs once."""
        coord = ShutdownCoordinator()
        coord.install_signal_handlers()
        coord.install_signal_handlers()  # Should be no-op
        assert coord.signal_handlers_installed is True


# =============================================================================
# Test MonitoringLoopMixin
# =============================================================================


class ConcreteMonitor(MonitoringLoopMixin):
    """Concrete implementation for testing."""

    def _graceful_shutdown_impl(self) -> None:
        """Implementation of graceful shutdown."""
        pass


class TestMonitoringLoopMixin:
    """Tests for MonitoringLoopMixin."""

    def test_initial_monitoring_inactive(self) -> None:
        """Monitoring inactive initially."""
        obj = ConcreteMonitor()
        assert obj.monitoring_active is False

    def test_start_monitoring_activates(self) -> None:
        """start_monitoring_with_shutdown activates monitoring."""
        obj = ConcreteMonitor()

        # Use a function that keeps running to verify activation
        def long_running() -> None:
            while not obj.is_shutdown_requested():
                time.sleep(0.01)

        obj.start_monitoring_with_shutdown([long_running])
        time.sleep(0.02)  # Let thread start
        assert obj.monitoring_active is True
        obj.request_shutdown()  # Clean exit

    def test_start_monitoring_creates_threads(self) -> None:
        """start_monitoring_with_shutdown creates threads."""
        obj = ConcreteMonitor()
        # Use a function that completes quickly
        obj.start_monitoring_with_shutdown([lambda: None])
        assert len(obj.monitor_threads) == 1
        time.sleep(0.05)  # Let thread complete

    def test_graceful_shutdown_stops_monitoring(self) -> None:
        """Graceful shutdown stops monitoring."""
        obj = ConcreteMonitor(ShutdownConfig(graceful_timeout=0.1))

        # Use a function that checks shutdown flag
        def loop_until_shutdown() -> None:
            while not obj.is_shutdown_requested():
                time.sleep(0.01)

        obj.start_monitoring_with_shutdown([loop_until_shutdown])
        time.sleep(0.02)  # Let it start
        obj.request_shutdown()
        obj.execute_graceful_shutdown()
        assert obj.shutdown_phase == ShutdownPhase.STOPPED


# =============================================================================
# Test timeout context manager
# =============================================================================


class TestTimeoutContextManager:
    """Tests for timeout context manager."""

    def test_timeout_yields_on_windows(self) -> None:
        """Timeout yields without error on Windows."""
        with timeout(1.0):
            pass  # Should not raise

    def test_timeout_does_not_block(self) -> None:
        """Timeout does not block normal execution."""
        start = time.time()
        with timeout(10.0):
            time.sleep(0.01)
        elapsed = time.time() - start
        assert elapsed < 1.0

    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="SIGALRM not available on Windows",
    )
    def test_timeout_raises_on_unix(self) -> None:
        """Timeout raises TimeoutError on Unix when exceeded."""
        with pytest.raises(TimeoutError):
            with timeout(0.01):
                time.sleep(1.0)


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_cleanup_task_exception_handled(self) -> None:
        """Cleanup task exception is handled."""
        obj = ConcreteShutdown()

        def failing_task() -> None:
            raise OSError("Test error")

        obj.register_cleanup_task(failing_task)
        obj.request_shutdown()
        # Should not raise
        obj.execute_graceful_shutdown()
        assert obj.shutdown_phase == ShutdownPhase.STOPPED

    def test_state_saver_exception_handled(self) -> None:
        """State saver exception is handled."""
        obj = ConcreteShutdown(ShutdownConfig(save_state=True))

        def failing_saver() -> None:
            raise OSError("Test error")

        obj.register_state_saver(failing_saver)
        obj.request_shutdown()
        # Should not raise
        obj.execute_graceful_shutdown()
        assert obj.shutdown_phase == ShutdownPhase.STOPPED

    def test_multiple_cleanup_tasks(self) -> None:
        """Multiple cleanup tasks all execute."""
        obj = ConcreteShutdown()
        calls = []
        obj.register_cleanup_task(lambda: calls.append(1))
        obj.register_cleanup_task(lambda: calls.append(2))
        obj.register_cleanup_task(lambda: calls.append(3))
        obj.request_shutdown()
        obj.execute_graceful_shutdown()
        assert calls == [1, 2, 3]

    def test_coordinator_empty_shutdown(self) -> None:
        """Coordinator handles shutdown with no components."""
        coord = ShutdownCoordinator()
        coord.shutdown_all("Test")  # Should not raise

    def test_coordinator_missing_component(self) -> None:
        """Coordinator handles missing component in order."""
        coord = ShutdownCoordinator()
        coord.shutdown_order = ["nonexistent"]
        coord.shutdown_all("Test")  # Should not raise

    def test_shutdown_config_custom_signals(self) -> None:
        """ShutdownConfig accepts custom signal list."""
        config = ShutdownConfig(signal_handlers=[signal.SIGINT])
        assert len(config.signal_handlers) == 1
        assert signal.SIGINT in config.signal_handlers

    def test_force_shutdown_sets_stopped(self) -> None:
        """_force_shutdown sets phase to STOPPED."""
        obj = ConcreteShutdown()
        obj._force_shutdown()
        assert obj.shutdown_phase == ShutdownPhase.STOPPED
        assert obj.shutdown_complete.is_set()
