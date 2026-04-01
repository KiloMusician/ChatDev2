#!/usr/bin/env python3
"""🛑 Graceful Shutdown Utility for Long-Running Tasks.

Provides centralized graceful shutdown patterns for:
- Background monitoring loops
- Worker threads
- Async task coordination
- Resource cleanup
- Signal handling

OmniTag: {
    "purpose": "graceful_shutdown_system",
    "type": "process_lifecycle_management",
    "evolution_stage": "v1.0_foundation"
}
MegaTag: {
    "scope": "shutdown_coordination",
    "integration_points": ["monitoring_systems", "background_processes", "resource_cleanup"],
    "quantum_context": "lifecycle_consciousness"
}
RSHTS: ΞΨΩ∞⟨GRACEFUL_SHUTDOWN⟩→ΦΣΣ
"""

import logging
import platform
import signal
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import NoReturn

logger = logging.getLogger(__name__)


class ShutdownPhase(Enum):
    """Phases of graceful shutdown process."""

    RUNNING = "running"
    SHUTDOWN_REQUESTED = "shutdown_requested"
    GRACEFUL_STOPPING = "graceful_stopping"
    FORCE_STOPPING = "force_stopping"
    STOPPED = "stopped"


@dataclass
class ShutdownConfig:
    """Configuration for graceful shutdown behavior."""

    graceful_timeout: float = 30.0  # Seconds to wait for graceful shutdown
    force_timeout: float = 10.0  # Additional seconds before force kill
    cleanup_timeout: float = 5.0  # Seconds for cleanup operations
    save_state: bool = True  # Whether to save state during shutdown
    log_progress: bool = True  # Whether to log shutdown progress
    signal_handlers: list[int] = field(default_factory=lambda: [signal.SIGINT, signal.SIGTERM])


class GracefulShutdownMixin(ABC):
    """Mixin for classes that need graceful shutdown capabilities."""

    def __init__(self, shutdown_config: ShutdownConfig | None = None) -> None:
        """Initialize GracefulShutdownMixin with shutdown_config."""
        self.shutdown_config = shutdown_config or ShutdownConfig()
        self.shutdown_phase = ShutdownPhase.RUNNING
        self.shutdown_requested = threading.Event()
        self.shutdown_complete = threading.Event()
        self.cleanup_tasks: list[Callable] = []
        self.state_savers: list[Callable] = []
        self._shutdown_start_time: datetime | None = None

    def register_cleanup_task(self, task: Callable) -> None:
        """Register a cleanup task to run during shutdown."""
        self.cleanup_tasks.append(task)

    def register_state_saver(self, saver: Callable) -> None:
        """Register a state saver to run during shutdown."""
        self.state_savers.append(saver)

    def request_shutdown(self, reason: str = "Manual request") -> None:
        """Request graceful shutdown."""
        if self.shutdown_phase == ShutdownPhase.RUNNING:
            self.shutdown_phase = ShutdownPhase.SHUTDOWN_REQUESTED
            self._shutdown_start_time = datetime.now()
            self.shutdown_requested.set()

            if self.shutdown_config.log_progress:
                logger.info(f"🛑 Graceful shutdown requested: {reason}")

    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested."""
        return self.shutdown_requested.is_set()

    def wait_for_shutdown(self, wait_timeout: float | None = None) -> bool:
        """Wait for shutdown to complete."""
        return self.shutdown_complete.wait(wait_timeout)

    @abstractmethod
    def _graceful_shutdown_impl(self) -> None:
        """Implementation-specific graceful shutdown logic."""

    def execute_graceful_shutdown(self) -> None:
        """Execute the complete graceful shutdown sequence."""
        try:
            self.shutdown_phase = ShutdownPhase.GRACEFUL_STOPPING

            # Phase 1: Implementation-specific graceful shutdown
            self._graceful_shutdown_impl()

            # Phase 2: Save state if configured
            if self.shutdown_config.save_state:
                self._execute_state_savers()

            # Phase 3: Execute cleanup tasks
            self._execute_cleanup_tasks()

            self.shutdown_phase = ShutdownPhase.STOPPED
            self.shutdown_complete.set()

            if self.shutdown_config.log_progress and self._shutdown_start_time:
                elapsed = datetime.now() - self._shutdown_start_time
                logger.info("✅ Graceful shutdown completed in %.2fs", elapsed.total_seconds())

        except (OSError, RuntimeError) as e:
            logger.exception(f"❌ Error during graceful shutdown: {e}")
            self.shutdown_phase = ShutdownPhase.FORCE_STOPPING
            self._force_shutdown()

    def _execute_state_savers(self) -> None:
        """Execute all registered state savers."""
        for saver in self.state_savers:
            try:
                with timeout(self.shutdown_config.cleanup_timeout):
                    saver()
            except (OSError, TimeoutError) as e:
                logger.exception(f"❌ State saver failed: {e}")

    def _execute_cleanup_tasks(self) -> None:
        """Execute all registered cleanup tasks."""
        for task in self.cleanup_tasks:
            try:
                with timeout(self.shutdown_config.cleanup_timeout):
                    task()
            except (OSError, TimeoutError) as e:
                logger.exception(f"❌ Cleanup task failed: {e}")

    def _force_shutdown(self) -> None:
        """Force shutdown when graceful shutdown fails."""
        logger.warning("⚠️ Forcing shutdown after graceful shutdown failed")
        self.shutdown_phase = ShutdownPhase.STOPPED
        self.shutdown_complete.set()


class ShutdownCoordinator:
    """Coordinates graceful shutdown across multiple components."""

    def __init__(self, config: ShutdownConfig | None = None) -> None:
        """Initialize ShutdownCoordinator with config."""
        self.config = config or ShutdownConfig()
        self.components: dict[str, GracefulShutdownMixin] = {}
        self.shutdown_order: list[str] = []
        self.signal_handlers_installed = False

    def register_component(
        self, name: str, component: GracefulShutdownMixin, priority: int = 0
    ) -> None:
        """Register a component for coordinated shutdown."""
        self.components[name] = component

        # Insert in priority order (higher priority shuts down first)
        inserted = False
        for i, existing_name in enumerate(self.shutdown_order):
            if priority > getattr(self.components[existing_name], "shutdown_priority", 0):
                self.shutdown_order.insert(i, name)
                inserted = True
                break

        if not inserted:
            self.shutdown_order.append(name)

        # Mark priority on component for reference
        component.shutdown_priority = priority  # type: ignore[attr-defined]

    def install_signal_handlers(self) -> None:
        """Install signal handlers for graceful shutdown."""
        if self.signal_handlers_installed:
            return

        def signal_handler(_signum, _frame) -> None:
            signal_name = signal.Signals(_signum).name
            logger.info(f"🛑 Received signal {signal_name}, initiating graceful shutdown")
            self.shutdown_all(f"Signal {signal_name}")

        for sig in self.config.signal_handlers:
            if hasattr(signal, "signal"):  # Unix-like systems
                signal.signal(sig, signal_handler)

        self.signal_handlers_installed = True

    def shutdown_all(self, reason: str = "Coordinator shutdown") -> None:
        """Shutdown all registered components in order."""
        logger.info(f"🛑 Coordinating shutdown of {len(self.components)} components: {reason}")

        # Request shutdown for all components
        for name in self.shutdown_order:
            if name in self.components:
                self.components[name].request_shutdown(f"Coordinator: {reason}")

        # Wait for graceful shutdown with timeout
        start_time = datetime.now()
        timeout_time = start_time + timedelta(seconds=self.config.graceful_timeout)

        for name in self.shutdown_order:
            if name not in self.components:
                continue

            component = self.components[name]
            remaining_time = (timeout_time - datetime.now()).total_seconds()

            if remaining_time > 0:
                if component.wait_for_shutdown(remaining_time):
                    logger.info(f"✅ Component '{name}' shutdown gracefully")
                else:
                    logger.warning(f"⚠️ Component '{name}' shutdown timeout")
            else:
                logger.warning(f"⚠️ Component '{name}' shutdown skipped (global timeout)")


class MonitoringLoopMixin(GracefulShutdownMixin):
    """Specialized mixin for monitoring loops."""

    def __init__(self, shutdown_config: ShutdownConfig | None = None) -> None:
        """Initialize MonitoringLoopMixin with shutdown_config."""
        super().__init__(shutdown_config)
        self.monitoring_active = False
        self.monitor_threads: list[threading.Thread] = []

    def start_monitoring_with_shutdown(self, monitor_functions: list[Callable]) -> None:
        """Start monitoring threads with graceful shutdown support."""
        self.monitoring_active = True

        for func in monitor_functions:
            thread = threading.Thread(
                target=self._monitored_loop_wrapper, args=(func,), daemon=True
            )
            thread.start()
            self.monitor_threads.append(thread)

    def _monitored_loop_wrapper(self, monitor_function: Callable) -> None:
        """Wrapper that adds shutdown checking to monitoring loops."""
        try:
            monitor_function()
        except (OSError, RuntimeError) as e:
            logger.exception(f"❌ Monitoring function error: {e}")
        finally:
            self.monitoring_active = False

    def _graceful_shutdown_impl(self) -> None:
        """Stop monitoring loops gracefully."""
        self.monitoring_active = False

        # Wait for monitor threads to finish
        for thread in self.monitor_threads:
            thread.join(
                timeout=(self.shutdown_config.graceful_timeout / max(1, len(self.monitor_threads)))
            )

        self.monitor_threads.clear()


@contextmanager
def timeout(seconds: float):
    """Context manager for timing out operations.

    On Windows, SIGALRM is not available; this context manager becomes a no-op.
    """
    # If running on Windows, yield without installing alarm
    if platform.system() == "Windows":
        yield
        return

    # Check if SIGALRM is available (Unix-like systems)
    if not hasattr(signal, "SIGALRM") or not hasattr(signal, "alarm"):
        yield
        return

    def timeout_handler(_signum, _frame) -> NoReturn:
        msg = f"Operation timed out after {seconds} seconds"
        raise TimeoutError(msg)

    # signal.alarm is not available on Windows, skip timeout
    if not hasattr(signal, "alarm"):
        yield
        return

    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(seconds))  # Not available on Windows

    try:
        yield
    finally:
        signal.alarm(0)  # Not available on Windows
        signal.signal(signal.SIGALRM, old_handler)


def create_monitoring_shutdown_pattern(
    monitor_functions: list[Callable], config: ShutdownConfig | None = None
) -> MonitoringLoopMixin:
    """Factory function to create a monitoring system with graceful shutdown."""

    class MonitoringSystem(MonitoringLoopMixin):
        def __init__(self) -> None:
            super().__init__(config)

        def start(self) -> None:
            self.start_monitoring_with_shutdown(monitor_functions)

    return MonitoringSystem()


# Example usage patterns
def example_background_service():
    """Example of how to implement graceful shutdown in a background service."""

    class BackgroundService(GracefulShutdownMixin):
        def __init__(self) -> None:
            super().__init__()
            self.running = True
            self.register_cleanup_task(self._cleanup_resources)
            self.register_state_saver(self._save_current_state)

        def run(self) -> None:
            while self.running and not self.is_shutdown_requested():
                # Do work here
                time.sleep(1)

            # Graceful shutdown when requested
            if self.is_shutdown_requested():
                self.execute_graceful_shutdown()

        def _graceful_shutdown_impl(self) -> None:
            self.running = False
            logger.info("🛑 Background service stopping...")

        def _cleanup_resources(self) -> None:
            logger.info("🧹 Cleaning up resources...")

        def _save_current_state(self) -> None:
            logger.info("💾 Saving current state...")

    return BackgroundService()


if __name__ == "__main__":
    # Demonstration of graceful shutdown patterns
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Create and configure a coordinator
    coordinator = ShutdownCoordinator()
    coordinator.install_signal_handlers()

    # Create example components
    service = example_background_service()
    coordinator.register_component("background_service", service, priority=10)

    logger.info("🚀 Starting graceful shutdown demonstration")
    logger.info("💡 Press Ctrl+C to test graceful shutdown")

    try:
        service.run()
    except KeyboardInterrupt:
        logger.info("\n🛑 Manual shutdown request")
        coordinator.shutdown_all("Manual interrupt")
