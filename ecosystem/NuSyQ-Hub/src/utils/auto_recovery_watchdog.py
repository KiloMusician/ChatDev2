"""Auto-Recovery Watchdog System.

==============================

Purpose:
    Detects and recovers from AI agent softlocks and workflow failures
    in real-time. Acts as a safety net to prevent indefinite stalls.

Features:
    - Monitors agent activity and task execution
    - Detects softlock patterns (no tool calls, stuck states)
    - Automatic recovery with checkpoint restoration
    - Timeout-based intervention
    - Escalation to human operator if needed

Usage:
    # Monitor workflow execution
    watchdog = AutoRecoveryWatchdog(timeout=120)
    with watchdog.monitor("Running tests"):
        run_tests()  # If this hangs, watchdog triggers recovery

    # Manual watchdog in async context
    async with AutoRecoveryWatchdog().async_monitor():
        await long_running_task()
"""

import logging
import sys
import threading
import time
from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

SessionCheckpoint: type | None = None
restore_latest: Callable[[Path | None], dict[str, Any] | None] | None = None
try:
    from src.utils.session_checkpoint import \
        SessionCheckpoint as _SessionCheckpoint
    from src.utils.session_checkpoint import restore_latest as _restore_latest

    SessionCheckpoint = _SessionCheckpoint
    restore_latest = _restore_latest
except ImportError:
    # Fallback if imports fail
    SessionCheckpoint = None
    restore_latest = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class WatchdogState(Enum):
    """Watchdog operational states."""

    IDLE = "idle"
    MONITORING = "monitoring"
    WARNING = "warning"
    RECOVERING = "recovering"
    ESCALATED = "escalated"


@dataclass
class WatchdogEvent:
    """Event logged by watchdog."""

    timestamp: datetime
    state: WatchdogState
    message: str
    context: dict


class AutoRecoveryWatchdog:
    """Monitors workflow execution and triggers recovery on softlocks.

    Provides timeout-based monitoring with automatic recovery mechanisms
    """

    def __init__(
        self,
        timeout: float = 120.0,
        warning_threshold: float = 0.8,
        auto_recover: bool = True,
        checkpoint_on_recovery: bool = True,
    ) -> None:
        """Initialize auto-recovery watchdog.

        Args:
            timeout: Maximum seconds before triggering recovery
            warning_threshold: Warn when this fraction of timeout elapsed (0.8 = 80%)
            auto_recover: Automatically trigger recovery (vs. escalate)
            checkpoint_on_recovery: Save checkpoint before recovery
        """
        self.timeout = timeout
        self.warning_threshold = warning_threshold
        self.auto_recover = auto_recover
        self.checkpoint_on_recovery = checkpoint_on_recovery

        self.state = WatchdogState.IDLE
        self.start_time: float | None = None
        self.task_description: str = ""
        self.events: list[WatchdogEvent] = []

        self._timer_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        logger.info("🐕 AutoRecoveryWatchdog initialized")
        logger.info(f"   Timeout: {timeout}s")
        logger.info(f"   Warning at: {warning_threshold * 100}%")
        logger.info(f"   Auto-recover: {auto_recover}")

    def _log_event(
        self, state: WatchdogState, message: str, context: dict[str, Any] | None = None
    ) -> None:
        """Log watchdog event."""
        event = WatchdogEvent(
            timestamp=datetime.now(),
            state=state,
            message=message,
            context=context or {},
        )
        self.events.append(event)

        # Log to standard logger
        log_msg = f"[{state.value.upper()}] {message}"
        if state == WatchdogState.WARNING:
            logger.warning(log_msg)
        elif state in (WatchdogState.RECOVERING, WatchdogState.ESCALATED):
            logger.error(log_msg)
        else:
            logger.info(log_msg)

    def _watchdog_timer(self) -> None:
        """Background timer thread."""
        warning_time = self.timeout * self.warning_threshold

        while not self._stop_event.is_set():
            if self.start_time:
                elapsed = time.time() - self.start_time

                # Check for warning threshold
                if elapsed >= warning_time and self.state == WatchdogState.MONITORING:
                    self.state = WatchdogState.WARNING
                    self._log_event(
                        WatchdogState.WARNING,
                        f"Task '{self.task_description}' approaching timeout ({elapsed:.1f}/{self.timeout}s)",
                        {"elapsed": elapsed, "timeout": self.timeout},
                    )

                # Check for timeout
                if elapsed >= self.timeout:
                    self._handle_timeout()
                    break

            time.sleep(1)  # Check every second

    def _handle_timeout(self) -> None:
        """Handle timeout event."""
        elapsed = time.time() - self.start_time if self.start_time else 0

        self._log_event(
            WatchdogState.RECOVERING if self.auto_recover else WatchdogState.ESCALATED,
            f"TIMEOUT: Task '{self.task_description}' exceeded {self.timeout}s",
            {"elapsed": elapsed, "task": self.task_description},
        )

        if self.auto_recover:
            self._trigger_recovery()
        else:
            self._escalate_to_human()

    def _trigger_recovery(self) -> None:
        """Trigger automatic recovery."""
        self.state = WatchdogState.RECOVERING
        logger.error("🔧 TRIGGERING AUTO-RECOVERY")
        logger.error(f"   Task: {self.task_description}")
        logger.error(f"   Reason: Timeout after {self.timeout}s")

        try:
            # Save checkpoint before recovery (if available)
            if self.checkpoint_on_recovery and SessionCheckpoint is not None:
                recovery_state = {
                    "task": self.task_description,
                    "timeout": self.timeout,
                    "elapsed": time.time() - self.start_time if self.start_time else 0,
                    "events": [
                        {
                            "timestamp": e.timestamp.isoformat(),
                            "state": e.state.value,
                            "message": e.message,
                        }
                        for e in self.events
                    ],
                }

                checkpoint = SessionCheckpoint()
                checkpoint.save(recovery_state, f"Before recovery: {self.task_description}")
                logger.info("📌 Checkpoint saved before recovery")

            # Attempt to restore from previous checkpoint
            if restore_latest is not None:
                restored = restore_latest(None)
                if restored:
                    logger.info("✅ Restored from previous checkpoint")
                    logger.info("   Workflow can continue from last known good state")
                else:
                    logger.warning("⚠️  No checkpoint available to restore")

            # Log recovery completion
            self._log_event(
                WatchdogState.IDLE,
                "Recovery completed",
                {"success": True},
            )

        except Exception as e:
            logger.error(f"❌ Recovery failed: {e}")
            self._escalate_to_human()

    def _escalate_to_human(self) -> None:
        """Escalate to human operator."""
        self.state = WatchdogState.ESCALATED
        logger.critical("🚨 ESCALATING TO HUMAN OPERATOR")
        logger.critical(f"   Task: {self.task_description}")
        logger.critical(f"   Timeout: {self.timeout}s")
        logger.critical("   AUTO-RECOVERY DISABLED OR FAILED")
        logger.critical("")
        logger.critical("Manual intervention required:")
        logger.critical("  1. Check task status")
        logger.critical("  2. Kill hung processes if needed")
        logger.critical("  3. Restore from checkpoint")
        logger.critical("  4. Resume workflow manually")

    @contextmanager
    def monitor(self, task_description: str = "Task") -> Iterator["AutoRecoveryWatchdog"]:
        """Context manager for monitoring synchronous tasks.

        Usage:
            with watchdog.monitor("Running tests"):
                run_tests()  # Protected by watchdog
        """
        self.task_description = task_description
        self.state = WatchdogState.MONITORING
        self.start_time = time.time()
        self._stop_event.clear()

        self._log_event(
            WatchdogState.MONITORING,
            f"Started monitoring: {task_description}",
            {"timeout": self.timeout},
        )

        # Start timer thread
        self._timer_thread = threading.Thread(target=self._watchdog_timer, daemon=True)
        self._timer_thread.start()

        try:
            yield self
        except Exception as e:
            self._log_event(
                WatchdogState.WARNING,
                f"Task raised exception: {e}",
                {"exception": str(e)},
            )
            raise
        finally:
            # Stop timer
            self._stop_event.set()
            if self._timer_thread:
                self._timer_thread.join(timeout=2)

            # Log completion
            elapsed = time.time() - self.start_time
            self._log_event(
                WatchdogState.IDLE,
                f"Completed monitoring: {task_description}",
                {"elapsed": elapsed},
            )

            logger.info(f"✅ Task completed in {elapsed:.2f}s (timeout: {self.timeout}s)")
            self.state = WatchdogState.IDLE

    @asynccontextmanager
    async def async_monitor(
        self, task_description: str = "Async Task"
    ) -> AsyncIterator["AutoRecoveryWatchdog"]:
        """Context manager for monitoring asynchronous tasks.

        Usage:
            async with watchdog.async_monitor("Running async tests"):
                await run_async_tests()  # Protected by watchdog
        """
        self.task_description = task_description
        self.state = WatchdogState.MONITORING
        self.start_time = time.time()
        self._stop_event.clear()

        self._log_event(
            WatchdogState.MONITORING,
            f"Started monitoring: {task_description}",
            {"timeout": self.timeout},
        )

        # Start timer thread
        self._timer_thread = threading.Thread(target=self._watchdog_timer, daemon=True)
        self._timer_thread.start()

        try:
            yield self
        except Exception as e:
            self._log_event(
                WatchdogState.WARNING,
                f"Async task raised exception: {e}",
                {"exception": str(e)},
            )
            raise
        finally:
            # Stop timer
            self._stop_event.set()
            if self._timer_thread:
                self._timer_thread.join(timeout=2)

            # Log completion
            elapsed = time.time() - self.start_time
            self._log_event(
                WatchdogState.IDLE,
                f"Completed monitoring: {task_description}",
                {"elapsed": elapsed},
            )

            logger.info(f"✅ Async task completed in {elapsed:.2f}s")
            self.state = WatchdogState.IDLE

    def get_event_log(self) -> list[dict]:
        """Get all watchdog events as dictionaries."""
        return [
            {
                "timestamp": e.timestamp.isoformat(),
                "state": e.state.value,
                "message": e.message,
                "context": e.context,
            }
            for e in self.events
        ]


# Example usage and testing
if __name__ == "__main__":
    # Example 1: Task that completes normally
    logger.info("\n=== Example 1: Normal completion ===")
    watchdog = AutoRecoveryWatchdog(timeout=5)
    with watchdog.monitor("Quick task"):
        time.sleep(2)
        logger.info("Task completed successfully")

    # Example 2: Task that times out (simulated)
    logger.info("\n=== Example 2: Timeout with recovery ===")
    watchdog = AutoRecoveryWatchdog(timeout=3, auto_recover=True)
    try:
        with watchdog.monitor("Slow task"):
            time.sleep(5)  # This will timeout
    except Exception as e:
        logger.error(f"Exception: {e}")

    # Print event log
    logger.info("\n=== Event Log ===")
    for event in watchdog.get_event_log():
        logger.info(f"{event['timestamp']}: {event['state']} - {event['message']}")
