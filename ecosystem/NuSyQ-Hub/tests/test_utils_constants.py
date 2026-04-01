"""Tests for src/utils/constants.py — enums, constants, Paths, Defaults."""

import pytest


class TestAIModelEnum:
    """Tests for AIModel enum."""

    def test_has_gpt4(self):
        from src.utils.constants import AIModel
        assert AIModel.GPT_4 is not None

    def test_enum_has_multiple_values(self):
        from src.utils.constants import AIModel
        assert len(list(AIModel)) >= 2

    def test_values_are_strings(self):
        from src.utils.constants import AIModel
        for m in AIModel:
            assert isinstance(m.value, str)


class TestTaskStatusEnum:
    """Tests for TaskStatus enum."""

    def test_has_pending(self):
        from src.utils.constants import TaskStatus
        assert TaskStatus.PENDING is not None

    def test_has_complete_or_done(self):
        from src.utils.constants import TaskStatus
        statuses = {m.name for m in TaskStatus}
        assert statuses & {"COMPLETE", "DONE", "COMPLETED", "FINISHED"}

    def test_enum_count(self):
        from src.utils.constants import TaskStatus
        assert len(list(TaskStatus)) >= 3


class TestLogLevelIntEnum:
    """Tests for LogLevel IntEnum."""

    def test_inherits_int(self):
        from src.utils.constants import LogLevel
        for level in LogLevel:
            assert isinstance(level.value, int)

    def test_ordering(self):
        from src.utils.constants import LogLevel
        levels = sorted(LogLevel, key=lambda x: x.value)
        assert levels[0].value < levels[-1].value


class TestSystemPriorityIntEnum:
    """Tests for SystemPriority."""

    def test_has_values(self):
        from src.utils.constants import SystemPriority
        assert len(list(SystemPriority)) >= 2

    def test_int_values(self):
        from src.utils.constants import SystemPriority
        for p in SystemPriority:
            assert isinstance(p.value, int)


class TestComponentCapabilityFlag:
    """Tests for ComponentCapability Flag."""

    def test_is_flag(self):
        from enum import Flag
        from src.utils.constants import ComponentCapability
        assert issubclass(ComponentCapability, Flag)

    def test_has_capabilities(self):
        from src.utils.constants import ComponentCapability
        assert len(list(ComponentCapability)) >= 1


class TestPathsClass:
    """Tests for Paths class constants."""

    def test_paths_is_class(self):
        from src.utils.constants import Paths
        assert Paths is not None

    def test_has_path_attributes(self):
        from src.utils.constants import Paths
        # Should have at least one Path-like class attribute
        attrs = [k for k in dir(Paths) if not k.startswith("_")]
        assert len(attrs) >= 1


class TestDefaultsClass:
    """Tests for Defaults class constants."""

    def test_defaults_is_class(self):
        from src.utils.constants import Defaults
        assert Defaults is not None

    def test_has_attributes(self):
        from src.utils.constants import Defaults
        attrs = [k for k in dir(Defaults) if not k.startswith("_")]
        assert len(attrs) >= 1


class TestOllamaDefault:
    """Tests for module-level OLLAMA_DEFAULT constant."""

    def test_is_string(self):
        from src.utils.constants import OLLAMA_DEFAULT
        assert isinstance(OLLAMA_DEFAULT, str)

    def test_is_nonempty(self):
        from src.utils.constants import OLLAMA_DEFAULT
        assert len(OLLAMA_DEFAULT) > 0


class TestGetAllConstants:
    """Tests for get_all_constants function."""

    def test_returns_dict(self):
        from src.utils.constants import get_all_constants
        result = get_all_constants()
        assert isinstance(result, dict)

    def test_has_content(self):
        from src.utils.constants import get_all_constants
        result = get_all_constants()
        assert len(result) > 0


class TestErrorCodeEnum:
    """Tests for ErrorCode IntEnum."""

    def test_has_values(self):
        from src.utils.constants import ErrorCode
        assert len(list(ErrorCode)) >= 1

    def test_int_values(self):
        from src.utils.constants import ErrorCode
        for code in ErrorCode:
            assert isinstance(code.value, int)
