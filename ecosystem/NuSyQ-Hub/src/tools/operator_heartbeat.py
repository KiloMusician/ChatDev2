#!/usr/bin/env python3
"""Operator Heartbeat - Progress Updates for Long Operations.

Provides periodic "still working on X" updates during long-running operations
to reduce anxiety and enable early course correction.

Implements suggestion: operator_heartbeat (line 359, suggestion_catalog_expanded.py)

Usage:
    from src.tools.operator_heartbeat import heartbeat_wrapper

    @heartbeat_wrapper(interval=5.0, description="Processing files")
    def long_operation() -> None:
        # Your code here
        pass

Or manual:
    from src.tools.operator_heartbeat import Heartbeat

    with Heartbeat("Analyzing codebase", interval=3.0):
        # Your long-running operation
        analyze_all_files()
"""

import logging
import threading
import time
from collections.abc import Callable
from contextlib import contextmanager
from functools import wraps
from typing import Literal

logger = logging.getLogger(__name__)


class Heartbeat:
    """Emits periodic progress messages during long operations."""

    def __init__(
        self,
        description: str,
        interval: float = 5.0,
        prefix: str = "💓",
        enable_logging: bool = True,
    ) -> None:
        """Initialize the OperatorHeartbeat.

        Args:
            description: What operation is happening (e.g., "Scanning repository")
            interval: Seconds between heartbeat messages.
            prefix: Emoji/symbol prefix for heartbeat messages.
            enable_logging: Whether to emit log messages (vs just print).
        """
        self.description = description
        self.interval = interval
        self.prefix = prefix
        self.enable_logging = enable_logging
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._start_time: float | None = None
        self._heartbeat_count = 0

    def _emit_heartbeat(self) -> None:
        """Emit a single heartbeat message."""
        elapsed = time.time() - self._start_time if self._start_time else 0.0
        self._heartbeat_count += 1

        message = (
            f"{self.prefix} Still working: {self.description} "
            f"(elapsed: {elapsed:.1f}s, heartbeat #{self._heartbeat_count})"
        )

        if self.enable_logging:
            logger.info(message)
        else:
            logger.info(message, flush=True)

    def _heartbeat_loop(self) -> None:
        """Background loop emitting heartbeats."""
        while not self._stop_event.wait(timeout=self.interval):
            self._emit_heartbeat()

    def start(self) -> None:
        """Start emitting heartbeats in background thread."""
        if self._thread and self._thread.is_alive():
            return  # Already running

        self._start_time = time.time()
        self._heartbeat_count = 0
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._thread.start()

        # Emit first heartbeat immediately
        start_msg = f"{self.prefix} Started: {self.description}"
        if self.enable_logging:
            logger.info(start_msg)
        else:
            logger.info(start_msg, flush=True)

    def stop(self) -> None:
        """Stop emitting heartbeats and emit final summary."""
        if not self._thread:
            return

        self._stop_event.set()
        self._thread.join(timeout=1.0)

        elapsed = time.time() - self._start_time if self._start_time else 0
        finish_msg = f"✅ Completed: {self.description} (total time: {elapsed:.1f}s, {self._heartbeat_count} heartbeats)"

        if self.enable_logging:
            logger.info(finish_msg)
        else:
            logger.info(finish_msg, flush=True)

    def __enter__(self) -> "Heartbeat":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> "Literal[False]":
        """Context manager exit."""
        self.stop()
        return False  # Don't suppress exceptions


@contextmanager
def heartbeat(description: str, interval: float = 5.0, prefix: str = "💓"):
    """Convenience context manager for heartbeats.

    Example:
        with heartbeat("Processing 1000 files"):
            for file in files:
                process(file)
    """
    hb = Heartbeat(description, interval, prefix)
    hb.start()
    try:
        yield hb
    finally:
        hb.stop()


def heartbeat_wrapper(
    interval: float = 5.0,
    description: str | None = None,
    prefix: str = "💓",
):
    """Decorator to add heartbeats to long-running functions.

    Args:
        interval: Seconds between heartbeats
        description: Override description (defaults to function name)
        prefix: Emoji/symbol prefix

    Example:
        @heartbeat_wrapper(interval=3.0)
        def analyze_repository():
            # Long operation
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            desc = description or f"{func.__name__}"
            with heartbeat(desc, interval, prefix):
                return func(*args, **kwargs)

        return wrapper

    return decorator


# Example usage and test
if __name__ == "__main__":
    # Test 1: Context manager
    logger.info("Test 1: Context manager")
    with heartbeat("Simulating long operation", interval=2.0):
        time.sleep(7)

    # Test 2: Decorator
    logger.info("\nTest 2: Decorator")

    @heartbeat_wrapper(interval=1.5, description="Heavy computation")
    def slow_function() -> str:
        time.sleep(5)
        return "Done!"

    result = slow_function()
    logger.info(f"Result: {result}")

    # Test 3: Manual control
    logger.info("\nTest 3: Manual control")
    hb = Heartbeat("Custom heartbeat", interval=1.0)
    hb.start()
    time.sleep(4)
    hb.stop()

    logger.info("\n✅ All heartbeat tests passed!")
    # end of script
