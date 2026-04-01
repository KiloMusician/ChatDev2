#!/usr/bin/env python3
"""Work Mode Declaration - Set Context at Session Start.

Explicitly states work mode (analysis/build/heal/play) before beginning
to set context, enable mode-specific behaviors, and improve focus.

Implements suggestion: mode_declaration (line 305, suggestion_catalog_expanded.py)

Usage:
    from src.tools.mode_declaration import WorkMode, declare_mode, with_mode

    # Option 1: Explicit declaration
    declare_mode(WorkMode.BUILD, "Implementing operator heartbeat")

    # Option 2: Context manager
    with with_mode(WorkMode.ANALYSIS, "Analyzing import structure"):
        # Your work here
        analyze_codebase()

    # Option 3: Decorator
    @with_mode(WorkMode.HEAL, "Fixing import errors")
    def fix_imports() -> None:
        pass
"""

import logging
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class WorkMode(Enum):
    """Possible work modes for NuSyQ operations."""

    ANALYSIS = "analysis"  # Understanding, reading, mapping
    BUILD = "build"  # Creating, implementing, developing
    HEAL = "heal"  # Fixing, restoring, recovering
    PLAY = "play"  # Exploring, experimenting, discovering
    ORCHESTRATE = "orchestrate"  # Coordinating, routing, delegating
    DOCUMENT = "document"  # Writing, explaining, recording
    TEST = "test"  # Validating, verifying, checking
    EVOLVE = "evolve"  # Upgrading, refactoring, modernizing

    @property
    def emoji(self) -> str:
        """Get emoji icon for this mode."""
        icons = {
            WorkMode.ANALYSIS: "🔍",
            WorkMode.BUILD: "🔨",
            WorkMode.HEAL: "🩹",
            WorkMode.PLAY: "🎮",
            WorkMode.ORCHESTRATE: "🎭",
            WorkMode.DOCUMENT: "📝",
            WorkMode.TEST: "🧪",
            WorkMode.EVOLVE: "🌱",
        }
        return icons.get(self, "⚙️")

    @property
    def description(self) -> str:
        """Get human-readable description of this mode."""
        descriptions = {
            WorkMode.ANALYSIS: "Understanding and mapping systems",
            WorkMode.BUILD: "Creating and implementing features",
            WorkMode.HEAL: "Fixing errors and restoring functionality",
            WorkMode.PLAY: "Exploring and experimenting safely",
            WorkMode.ORCHESTRATE: "Coordinating AI systems and workflows",
            WorkMode.DOCUMENT: "Recording knowledge and explaining concepts",
            WorkMode.TEST: "Validating functionality and quality",
            WorkMode.EVOLVE: "Modernizing and improving codebase",
        }
        return descriptions.get(self, "Performing work")


# Global state tracker (optional, for logging/analytics)
_CURRENT_MODE: WorkMode | None = None
_MODE_START_TIME: datetime | None = None
_MODE_PURPOSE: str | None = None


def declare_mode(
    mode: WorkMode,
    purpose: str = "",
    log: bool = True,
) -> None:
    """Declare work mode at start of session.

    Args:
        mode: What mode we're working in
        purpose: Specific goal/task for this session
        log: Whether to emit log message

    Example:
        declare_mode(WorkMode.BUILD, "Implementing operator heartbeat")
    """
    global _CURRENT_MODE, _MODE_START_TIME, _MODE_PURPOSE

    _CURRENT_MODE = mode
    _MODE_START_TIME = datetime.now()
    _MODE_PURPOSE = purpose

    message = f"{mode.emoji} MODE: {mode.value.upper()}"
    if purpose:
        message += f" - {purpose}"
    message += f"\n   Context: {mode.description}"

    if log:
        logger.info(message)


def end_mode(log: bool = True) -> None:
    """End current mode and emit summary.

    Args:
        log: Whether to emit log message
    """
    global _CURRENT_MODE, _MODE_START_TIME, _MODE_PURPOSE

    if _CURRENT_MODE is None:
        return

    elapsed = (datetime.now() - _MODE_START_TIME).total_seconds() if _MODE_START_TIME else 0

    message = f"✅ Completed {_CURRENT_MODE.value.upper()} mode (duration: {elapsed:.1f}s)"
    if _MODE_PURPOSE:
        message += f"\n   Purpose: {_MODE_PURPOSE}"

    if log:
        logger.info(message)

    _CURRENT_MODE = None
    _MODE_START_TIME = None
    _MODE_PURPOSE = None


@contextmanager
def with_mode(mode: WorkMode, purpose: str = ""):
    """Context manager for scoped mode declaration.

    Example:
        with with_mode(WorkMode.ANALYSIS, "Scanning repository"):
            analyze_all_files()
    """
    declare_mode(mode, purpose, log=False)  # Use print for clarity
    try:
        yield mode
    finally:
        end_mode(log=False)


def mode_decorator(mode: WorkMode, purpose: str | None = None):
    """Decorator to wrap function in mode declaration.

    Args:
        mode: Work mode for this function
        purpose: Override purpose (defaults to function name)

    Example:
        @mode_decorator(WorkMode.HEAL)
        def fix_imports():
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            desc = purpose or f"{func.__name__}"
            with with_mode(mode, desc):
                return func(*args, **kwargs)

        return wrapper

    return decorator


# Convenience aliases (using def instead of lambda per E731)
def analyze(purpose: str = "") -> Any:
    """Declare analysis mode with optional purpose."""
    return with_mode(WorkMode.ANALYSIS, purpose)


def build(purpose: str = "") -> Any:
    """Declare build mode with optional purpose."""
    return with_mode(WorkMode.BUILD, purpose)


def heal(purpose: str = "") -> Any:
    """Declare heal mode with optional purpose."""
    return with_mode(WorkMode.HEAL, purpose)


def play(purpose: str = "") -> Any:
    """Declare play mode with optional purpose."""
    return with_mode(WorkMode.PLAY, purpose)


def orchestrate(purpose: str = "") -> Any:
    """Declare orchestrate mode with optional purpose."""
    return with_mode(WorkMode.ORCHESTRATE, purpose)


def document(purpose: str = "") -> Any:
    """Declare document mode with optional purpose."""
    return with_mode(WorkMode.DOCUMENT, purpose)


def test(purpose: str = "") -> Any:
    """Declare test mode with optional purpose."""
    return with_mode(WorkMode.TEST, purpose)


def evolve(purpose: str = "") -> Any:
    """Declare evolve mode with optional purpose."""
    return with_mode(WorkMode.EVOLVE, purpose)


# Example usage and test
if __name__ == "__main__":
    import time

    logger.info("🧪 Mode Declaration Tests")
    logger.info("=" * 60)

    # Test 1: Explicit declaration
    logger.info("\nTest 1: Explicit declaration")
    declare_mode(WorkMode.BUILD, "Creating new feature", log=False)
    time.sleep(0.5)
    end_mode(log=False)

    # Test 2: Context manager
    logger.info("\nTest 2: Context manager")
    with with_mode(WorkMode.ANALYSIS, "Analyzing codebase"):
        time.sleep(0.5)
        logger.info("   → Analyzing files...")

    # Test 3: Decorator
    logger.info("\nTest 3: Decorator")

    @mode_decorator(WorkMode.HEAL, "Fixing import errors")
    def fix_something() -> None:
        time.sleep(0.5)
        logger.info("   → Applying fixes...")
        return "Fixed!"

    result = fix_something()
    logger.info(f"   Result: {result}")

    # Test 4: Convenience aliases
    logger.info("\nTest 4: Convenience aliases")
    with build("Implementing suggestion"):
        time.sleep(0.5)
        logger.info("   → Building implementation...")

    logger.info("\n✅ All mode declaration tests passed!")
