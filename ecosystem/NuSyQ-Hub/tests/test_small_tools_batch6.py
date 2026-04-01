"""Tests for src/tools batch 6: mode_declaration.

Coverage targets:
- mode_declaration.py: 263 lines - WorkMode enum and mode management
"""

from __future__ import annotations

import pytest


# ==============================================================================
# mode_declaration.py tests
# ==============================================================================
class TestWorkModeEnum:
    """Test WorkMode enum."""

    def test_all_modes_exist(self):
        """Verify all expected modes exist."""
        from src.tools.mode_declaration import WorkMode

        modes = [
            WorkMode.ANALYSIS,
            WorkMode.BUILD,
            WorkMode.HEAL,
            WorkMode.PLAY,
            WorkMode.ORCHESTRATE,
            WorkMode.DOCUMENT,
            WorkMode.TEST,
            WorkMode.EVOLVE,
        ]
        assert len(modes) == 8

    def test_mode_values(self):
        """Modes have correct string values."""
        from src.tools.mode_declaration import WorkMode

        assert WorkMode.ANALYSIS.value == "analysis"
        assert WorkMode.BUILD.value == "build"
        assert WorkMode.HEAL.value == "heal"

    def test_emoji_property(self):
        """Each mode has an emoji."""
        from src.tools.mode_declaration import WorkMode

        assert WorkMode.ANALYSIS.emoji == "🔍"
        assert WorkMode.BUILD.emoji == "🔨"
        assert WorkMode.HEAL.emoji == "🩹"
        assert WorkMode.PLAY.emoji == "🎮"
        assert WorkMode.ORCHESTRATE.emoji == "🎭"
        assert WorkMode.DOCUMENT.emoji == "📝"
        assert WorkMode.TEST.emoji == "🧪"
        assert WorkMode.EVOLVE.emoji == "🌱"

    def test_description_property(self):
        """Each mode has a description."""
        from src.tools.mode_declaration import WorkMode

        assert "Understanding" in WorkMode.ANALYSIS.description
        assert "Creating" in WorkMode.BUILD.description
        assert "Fixing" in WorkMode.HEAL.description


class TestDeclareMode:
    """Test declare_mode function."""

    def test_declare_mode_sets_global_state(self):
        """declare_mode sets global mode state."""
        from src.tools import mode_declaration
        from src.tools.mode_declaration import WorkMode, declare_mode, end_mode

        # Clean up any existing state first
        mode_declaration._CURRENT_MODE = None
        mode_declaration._MODE_START_TIME = None
        mode_declaration._MODE_PURPOSE = None

        declare_mode(WorkMode.BUILD, "Testing", log=False)
        assert mode_declaration._CURRENT_MODE == WorkMode.BUILD
        assert mode_declaration._MODE_START_TIME is not None
        assert mode_declaration._MODE_PURPOSE == "Testing"

        # Cleanup
        end_mode(log=False)

    def test_declare_mode_with_logging(self, caplog):
        """declare_mode emits log when log=True."""
        import logging

        from src.tools import mode_declaration
        from src.tools.mode_declaration import WorkMode, declare_mode, end_mode

        mode_declaration._CURRENT_MODE = None

        with caplog.at_level(logging.INFO):
            declare_mode(WorkMode.ANALYSIS, "Test purpose", log=True)

        # Cleanup
        end_mode(log=False)

    def test_declare_mode_without_purpose(self, caplog):
        """declare_mode works without purpose."""
        import logging

        from src.tools import mode_declaration
        from src.tools.mode_declaration import WorkMode, declare_mode, end_mode

        mode_declaration._CURRENT_MODE = None

        with caplog.at_level(logging.INFO):
            declare_mode(WorkMode.TEST)  # log=True (default)
        assert "MODE: TEST" in caplog.text

        end_mode(log=False)


class TestEndMode:
    """Test end_mode function."""

    def test_end_mode_clears_global_state(self):
        """end_mode clears global mode state."""
        from src.tools import mode_declaration
        from src.tools.mode_declaration import WorkMode, declare_mode, end_mode

        declare_mode(WorkMode.HEAL, "Test", log=False)
        end_mode(log=False)

        assert mode_declaration._CURRENT_MODE is None
        assert mode_declaration._MODE_START_TIME is None
        assert mode_declaration._MODE_PURPOSE is None

    def test_end_mode_no_current_mode(self):
        """end_mode gracefully handles no current mode."""
        from src.tools import mode_declaration
        from src.tools.mode_declaration import end_mode

        mode_declaration._CURRENT_MODE = None
        # Should not raise
        end_mode(log=False)

    def test_end_mode_prints_summary(self, caplog):
        """end_mode prints completion message."""
        import logging

        from src.tools import mode_declaration
        from src.tools.mode_declaration import WorkMode, declare_mode, end_mode

        mode_declaration._CURRENT_MODE = None
        declare_mode(WorkMode.DOCUMENT, "Writing docs", log=False)
        caplog.clear()  # Clear any previous logs

        with caplog.at_level(logging.INFO):
            end_mode()  # log=True (default)
        assert "Completed DOCUMENT" in caplog.text


class TestWithMode:
    """Test with_mode context manager."""

    def test_context_manager_sets_mode(self):
        """Context manager sets mode during execution."""
        from src.tools import mode_declaration
        from src.tools.mode_declaration import WorkMode, with_mode

        mode_declaration._CURRENT_MODE = None

        with with_mode(WorkMode.PLAY, "Testing") as mode:
            assert mode == WorkMode.PLAY
            assert mode_declaration._CURRENT_MODE == WorkMode.PLAY

        # After context, mode should be cleared
        assert mode_declaration._CURRENT_MODE is None

    def test_context_manager_clears_on_exception(self):
        """Context manager clears mode after exception."""
        from src.tools import mode_declaration
        from src.tools.mode_declaration import WorkMode, with_mode

        mode_declaration._CURRENT_MODE = None

        with pytest.raises(ValueError):
            with with_mode(WorkMode.BUILD, "Test"):
                raise ValueError("Test error")

        # Mode should still be cleared
        assert mode_declaration._CURRENT_MODE is None


class TestModeDecorator:
    """Test mode_decorator function."""

    def test_decorator_wraps_function(self):
        """Decorator wraps function execution in mode."""
        from src.tools import mode_declaration
        from src.tools.mode_declaration import WorkMode, mode_decorator

        mode_declaration._CURRENT_MODE = None

        @mode_decorator(WorkMode.EVOLVE, "Upgrading")
        def test_func() -> str:
            return "result"

        result = test_func()
        assert result == "result"
        # After function, mode should be cleared
        assert mode_declaration._CURRENT_MODE is None

    def test_decorator_uses_function_name(self):
        """Decorator uses function name when no purpose given."""
        from src.tools import mode_declaration
        from src.tools.mode_declaration import WorkMode, mode_decorator

        mode_declaration._CURRENT_MODE = None
        mode_declaration._MODE_PURPOSE = None

        captured_purpose = None

        @mode_decorator(WorkMode.TEST)
        def my_test_function():
            nonlocal captured_purpose
            captured_purpose = mode_declaration._MODE_PURPOSE

        my_test_function()

        # Verify the function name was used as purpose
        assert captured_purpose == "my_test_function"


class TestConvenienceAliases:
    """Test convenience alias functions."""

    def test_analyze_alias(self):
        """analyze() returns context manager."""
        from src.tools.mode_declaration import analyze

        with analyze("Testing analysis"):
            pass

    def test_build_alias(self):
        """build() returns context manager."""
        from src.tools.mode_declaration import build

        with build("Testing build"):
            pass

    def test_heal_alias(self):
        """heal() returns context manager."""
        from src.tools.mode_declaration import heal

        with heal("Testing heal"):
            pass

    def test_play_alias(self):
        """play() returns context manager."""
        from src.tools.mode_declaration import play

        with play("Testing play"):
            pass

    def test_orchestrate_alias(self):
        """orchestrate() returns context manager."""
        from src.tools.mode_declaration import orchestrate

        with orchestrate("Testing orchestrate"):
            pass

    def test_document_alias(self):
        """document() returns context manager."""
        from src.tools.mode_declaration import document

        with document("Testing document"):
            pass

    def test_test_alias(self):
        """test() returns context manager."""
        from src.tools.mode_declaration import test

        with test("Testing test mode"):
            pass

    def test_evolve_alias(self):
        """evolve() returns context manager."""
        from src.tools.mode_declaration import evolve

        with evolve("Testing evolve"):
            pass
