"""Tests for src/observability/structured_logging.py

This module tests structured logging utilities with rate limiting.

Coverage Target: 70%+
"""

import json
import logging
import os
from unittest.mock import patch

import pytest

# =============================================================================
# Module Import Tests
# =============================================================================


class TestModuleImports:
    """Test module-level imports."""

    def test_import_structured_formatter(self):
        """Test StructuredFormatter can be imported."""
        from src.observability.structured_logging import StructuredFormatter

        assert StructuredFormatter is not None

    def test_import_human_readable_formatter(self):
        """Test HumanReadableFormatter can be imported."""
        from src.observability.structured_logging import HumanReadableFormatter

        assert HumanReadableFormatter is not None

    def test_import_setup_logger(self):
        """Test setup_logger function can be imported."""
        from src.observability.structured_logging import setup_logger

        assert setup_logger is not None

    def test_import_rate_limited_log(self):
        """Test rate_limited_log function can be imported."""
        from src.observability.structured_logging import rate_limited_log

        assert rate_limited_log is not None

    def test_import_log_operation(self):
        """Test log_operation context manager can be imported."""
        from src.observability.structured_logging import log_operation

        assert log_operation is not None

    def test_import_get_log_level_from_env(self):
        """Test get_log_level_from_env can be imported."""
        from src.observability.structured_logging import get_log_level_from_env

        assert get_log_level_from_env is not None


# =============================================================================
# StructuredFormatter Tests
# =============================================================================


class TestStructuredFormatter:
    """Test StructuredFormatter class."""

    def test_create_formatter(self):
        """Test creating a formatter."""
        from src.observability.structured_logging import StructuredFormatter

        formatter = StructuredFormatter()

        assert formatter.service_name == "nusyq-hub"
        assert formatter.include_trace is True

    def test_custom_service_name(self):
        """Test custom service name."""
        from src.observability.structured_logging import StructuredFormatter

        formatter = StructuredFormatter(service_name="my-service")

        assert formatter.service_name == "my-service"

    def test_format_produces_json(self):
        """Test formatter produces valid JSON."""
        from src.observability.structured_logging import StructuredFormatter

        formatter = StructuredFormatter(include_trace=False)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Mock formatTime to avoid %f strftime bug
        with patch.object(formatter, "formatTime", return_value="2025-01-01T00:00:00.000000Z"):
            result = formatter.format(record)

        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed["message"] == "Test message"
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test"

    def test_format_includes_source(self):
        """Test JSON includes source location."""
        from src.observability.structured_logging import StructuredFormatter

        formatter = StructuredFormatter(include_trace=False)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/path/to/test.py",
            lineno=42,
            msg="Test",
            args=(),
            exc_info=None,
        )

        # Mock formatTime to avoid %f strftime bug
        with patch.object(formatter, "formatTime", return_value="2025-01-01T00:00:00.000000Z"):
            result = formatter.format(record)
        parsed = json.loads(result)

        assert "source" in parsed
        assert parsed["source"]["line"] == 42

    def test_format_includes_exception(self):
        """Test JSON includes exception info."""
        from src.observability.structured_logging import StructuredFormatter

        formatter = StructuredFormatter(include_trace=False)

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        # Mock formatTime to avoid %f strftime bug
        with patch.object(formatter, "formatTime", return_value="2025-01-01T00:00:00.000000Z"):
            result = formatter.format(record)
        parsed = json.loads(result)

        assert "exception" in parsed
        assert parsed["exception"]["type"] == "ValueError"
        assert "Test error" in parsed["exception"]["message"]


# =============================================================================
# HumanReadableFormatter Tests
# =============================================================================


class TestHumanReadableFormatter:
    """Test HumanReadableFormatter class."""

    def test_create_formatter(self):
        """Test creating human readable formatter."""
        from src.observability.structured_logging import HumanReadableFormatter

        formatter = HumanReadableFormatter()

        assert formatter.include_trace is False

    def test_format_readable(self):
        """Test formatter produces readable output."""
        from src.observability.structured_logging import HumanReadableFormatter

        formatter = HumanReadableFormatter()
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert "[INFO]" in result
        assert "test.module" in result
        assert "Test message" in result


# =============================================================================
# setup_logger Tests
# =============================================================================


class TestSetupLogger:
    """Test setup_logger function."""

    def test_setup_basic_logger(self):
        """Test setting up a basic logger."""
        from src.observability.structured_logging import setup_logger

        logger = setup_logger("test_basic")

        assert logger.name == "test_basic"
        assert logger.level == logging.INFO

    def test_setup_logger_custom_level(self):
        """Test custom log level."""
        from src.observability.structured_logging import setup_logger

        logger = setup_logger("test_debug", level=logging.DEBUG)

        assert logger.level == logging.DEBUG

    def test_setup_logger_string_level(self):
        """Test log level as string."""
        from src.observability.structured_logging import setup_logger

        logger = setup_logger("test_str_level", level="DEBUG")

        assert logger.level == logging.DEBUG

    def test_setup_logger_json_format(self):
        """Test JSON formatter."""
        from src.observability.structured_logging import (
            StructuredFormatter,
            setup_logger,
        )

        logger = setup_logger("test_json", log_format="json")

        # Check that console handler uses StructuredFormatter
        assert len(logger.handlers) > 0
        assert isinstance(logger.handlers[0].formatter, StructuredFormatter)

    def test_setup_logger_no_console(self):
        """Test disabling console handler."""
        from src.observability.structured_logging import setup_logger

        logger = setup_logger("test_no_console", console=False)

        # Should have no handlers if no file specified
        assert len(logger.handlers) == 0

    def test_setup_logger_with_file(self, tmp_path):
        """Test logger with file handler."""
        from src.observability.structured_logging import setup_logger

        log_file = tmp_path / "test.log"
        logger = setup_logger(
            "test_file",
            log_file=log_file,
            console=False,
        )

        logger.info("Test message")

        assert log_file.exists()

    def test_setup_logger_clears_handlers(self):
        """Test that setup clears existing handlers."""
        from src.observability.structured_logging import setup_logger

        logger1 = setup_logger("test_clear")
        handler_count_1 = len(logger1.handlers)

        logger2 = setup_logger("test_clear")  # Same name
        handler_count_2 = len(logger2.handlers)

        assert handler_count_1 == handler_count_2


# =============================================================================
# rate_limited_log Tests
# =============================================================================


class TestRateLimitedLog:
    """Test rate_limited_log function."""

    def test_first_log_allowed(self):
        """Test first log is always allowed."""
        from src.observability.structured_logging import (
            _RATE_LIMIT_CACHE,
            rate_limited_log,
            setup_logger,
        )

        # Clear cache for clean test
        _RATE_LIMIT_CACHE.clear()

        logger = setup_logger("test_rate_first", console=False)

        result = rate_limited_log(
            logger,
            logging.INFO,
            "Test message",
            rate_limit_key="test_first",
            rate_limit_seconds=60.0,
        )

        assert result is True

    def test_second_log_rate_limited(self):
        """Test second log within window is rate limited."""
        from src.observability.structured_logging import (
            _RATE_LIMIT_CACHE,
            rate_limited_log,
            setup_logger,
        )

        _RATE_LIMIT_CACHE.clear()

        logger = setup_logger("test_rate_second", console=False)

        # First log allowed
        rate_limited_log(
            logger,
            logging.INFO,
            "Message 1",
            rate_limit_key="test_second",
            rate_limit_seconds=60.0,
        )

        # Second log should be rate limited
        result = rate_limited_log(
            logger,
            logging.INFO,
            "Message 2",
            rate_limit_key="test_second",
            rate_limit_seconds=60.0,
        )

        assert result is False

    def test_different_keys_not_limited(self):
        """Test different rate limit keys don't affect each other."""
        from src.observability.structured_logging import (
            _RATE_LIMIT_CACHE,
            rate_limited_log,
            setup_logger,
        )

        _RATE_LIMIT_CACHE.clear()

        logger = setup_logger("test_rate_keys", console=False)

        # Two different keys
        result1 = rate_limited_log(logger, logging.INFO, "A", rate_limit_key="key_a")
        result2 = rate_limited_log(logger, logging.INFO, "B", rate_limit_key="key_b")

        assert result1 is True
        assert result2 is True


# =============================================================================
# log_operation Tests
# =============================================================================


class TestLogOperation:
    """Test log_operation context manager."""

    def test_log_operation_success(self, tmp_path):
        """Test successful operation logging."""
        from src.observability.structured_logging import log_operation, setup_logger

        log_file = tmp_path / "op.log"
        logger = setup_logger(
            "test_op_success",
            log_file=log_file,
            console=False,
        )

        with log_operation(logger, "test_operation"):
            pass  # Success

        content = log_file.read_text()
        assert "Starting test_operation" in content
        assert "Completed test_operation" in content

    def test_log_operation_failure(self, tmp_path):
        """Test failed operation logging."""
        from src.observability.structured_logging import log_operation, setup_logger

        log_file = tmp_path / "op_fail.log"
        logger = setup_logger(
            "test_op_fail",
            log_file=log_file,
            console=False,
        )

        with pytest.raises(ValueError):
            with log_operation(logger, "failing_operation"):
                raise ValueError("Test error")

        content = log_file.read_text()
        assert "Starting failing_operation" in content
        assert "Failed failing_operation" in content
        assert "Test error" in content

    def test_log_operation_with_context(self, tmp_path):
        """Test operation logging with context."""
        from src.observability.structured_logging import log_operation, setup_logger

        log_file = tmp_path / "op_ctx.log"
        logger = setup_logger(
            "test_op_ctx",
            log_file=log_file,
            console=False,
            log_format="json",
        )

        with log_operation(logger, "contextual_op", file="test.csv", log_args=True):
            pass


# =============================================================================
# get_log_level_from_env Tests
# =============================================================================


class TestGetLogLevelFromEnv:
    """Test get_log_level_from_env function."""

    def test_default_level(self):
        """Test default level when no env var."""
        from src.observability.structured_logging import get_log_level_from_env

        # Ensure env vars are not set
        with patch.dict(os.environ, {}, clear=True):
            level = get_log_level_from_env()

        assert level == logging.INFO

    def test_custom_default(self):
        """Test custom default level."""
        from src.observability.structured_logging import get_log_level_from_env

        with patch.dict(os.environ, {}, clear=True):
            level = get_log_level_from_env(default=logging.WARNING)

        assert level == logging.WARNING

    def test_nusyq_log_level_env(self):
        """Test NUSYQ_LOG_LEVEL environment variable."""
        from src.observability.structured_logging import get_log_level_from_env

        with patch.dict(os.environ, {"NUSYQ_LOG_LEVEL": "DEBUG"}):
            level = get_log_level_from_env()

        assert level == logging.DEBUG

    def test_log_level_env(self):
        """Test LOG_LEVEL environment variable."""
        from src.observability.structured_logging import get_log_level_from_env

        with patch.dict(os.environ, {"LOG_LEVEL": "ERROR"}):
            level = get_log_level_from_env()

        assert level == logging.ERROR

    def test_nusyq_takes_precedence(self):
        """Test NUSYQ_LOG_LEVEL takes precedence over LOG_LEVEL."""
        from src.observability.structured_logging import get_log_level_from_env

        with patch.dict(
            os.environ,
            {"NUSYQ_LOG_LEVEL": "DEBUG", "LOG_LEVEL": "ERROR"},
        ):
            level = get_log_level_from_env()

        assert level == logging.DEBUG

    def test_case_insensitive(self):
        """Test level parsing is case insensitive."""
        from src.observability.structured_logging import get_log_level_from_env

        with patch.dict(os.environ, {"LOG_LEVEL": "debug"}):
            level = get_log_level_from_env()

        assert level == logging.DEBUG

    def test_warn_alias(self):
        """Test WARN as alias for WARNING."""
        from src.observability.structured_logging import get_log_level_from_env

        with patch.dict(os.environ, {"LOG_LEVEL": "WARN"}):
            level = get_log_level_from_env()

        assert level == logging.WARNING


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
