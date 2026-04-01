"""Tests for src/tools/mode_declaration.py (WorkMode state tracker)."""

import pytest
from src.tools.mode_declaration import (
    WorkMode,
    declare_mode,
    end_mode,
    with_mode,
    analyze,
    build,
    heal,
    test,
)
import src.tools.mode_declaration as _md


def _reset():
    """Reset global mode state between tests."""
    _md._CURRENT_MODE = None
    _md._MODE_START_TIME = None
    _md._MODE_PURPOSE = None


def test_workmode_enum_values():
    """WorkMode enum has expected string values."""
    assert WorkMode.ANALYSIS.value == "analysis"
    assert WorkMode.BUILD.value == "build"
    assert WorkMode.TEST.value == "test"
    assert WorkMode.EVOLVE.value == "evolve"


def test_workmode_emoji_property():
    """WorkMode.emoji returns a non-empty string."""
    for mode in WorkMode:
        assert isinstance(mode.emoji, str)
        assert len(mode.emoji) > 0


def test_workmode_description_property():
    """WorkMode.description returns a non-empty string."""
    for mode in WorkMode:
        assert isinstance(mode.description, str)
        assert len(mode.description) > 0


def test_declare_mode_sets_state():
    """declare_mode sets global mode state."""
    _reset()
    declare_mode(WorkMode.ANALYSIS, purpose="test run", log=False)
    assert _md._CURRENT_MODE == WorkMode.ANALYSIS
    assert _md._MODE_PURPOSE == "test run"
    assert _md._MODE_START_TIME is not None
    _reset()


def test_end_mode_clears_state():
    """end_mode resets global state to None."""
    _reset()
    declare_mode(WorkMode.BUILD, log=False)
    end_mode(log=False)
    assert _md._CURRENT_MODE is None
    assert _md._MODE_PURPOSE is None


def test_end_mode_when_no_mode_is_noop():
    """end_mode when no mode is active does nothing (no error)."""
    _reset()
    end_mode(log=False)  # should not raise


def test_with_mode_context_manager():
    """with_mode yields mode and resets state after block."""
    _reset()
    with with_mode(WorkMode.TEST, "context test") as m:
        assert m == WorkMode.TEST
        assert _md._CURRENT_MODE == WorkMode.TEST
    assert _md._CURRENT_MODE is None


def test_convenience_functions_return_context_managers():
    """analyze/build/heal/test convenience functions return context managers."""
    _reset()
    for fn in (analyze, build, heal, test):
        ctx = fn("purpose")
        # Each should be a context manager usable with 'with'
        with ctx:
            pass
    _reset()
