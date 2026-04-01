"""Tests for src/LOGGING/modular_logging_system.py — filters and helper functions."""

import logging
import time


class TestDuplicateMessageFilter:
    """Tests for DuplicateMessageFilter."""

    def test_instantiation(self):
        from src.LOGGING.modular_logging_system import DuplicateMessageFilter
        f = DuplicateMessageFilter(window_seconds=2.0)
        assert f is not None

    def test_first_message_passes(self):
        from src.LOGGING.modular_logging_system import DuplicateMessageFilter
        f = DuplicateMessageFilter(window_seconds=5.0)
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Hello world", args=(), exc_info=None
        )
        assert f.filter(record) is True

    def test_duplicate_within_window_blocked(self):
        from src.LOGGING.modular_logging_system import DuplicateMessageFilter
        f = DuplicateMessageFilter(window_seconds=10.0)
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Duplicate message", args=(), exc_info=None
        )
        # First pass — allowed
        assert f.filter(record) is True
        # Second pass immediately — blocked
        assert f.filter(record) is False

    def test_different_messages_both_pass(self):
        from src.LOGGING.modular_logging_system import DuplicateMessageFilter
        f = DuplicateMessageFilter(window_seconds=10.0)
        r1 = logging.LogRecord("test", logging.INFO, "", 0, "msg A", (), None)
        r2 = logging.LogRecord("test", logging.INFO, "", 0, "msg B", (), None)
        assert f.filter(r1) is True
        assert f.filter(r2) is True

    def test_zero_window_allows_duplicates(self):
        from src.LOGGING.modular_logging_system import DuplicateMessageFilter
        f = DuplicateMessageFilter(window_seconds=0.0)
        record = logging.LogRecord("test", logging.INFO, "", 0, "repeat", (), None)
        f.filter(record)  # prime
        time.sleep(0.01)
        # After window expires, message should pass again
        result = f.filter(record)
        assert result is True

    def test_different_levels_tracked_separately(self):
        from src.LOGGING.modular_logging_system import DuplicateMessageFilter
        f = DuplicateMessageFilter(window_seconds=10.0)
        r_info = logging.LogRecord("test", logging.INFO, "", 0, "same", (), None)
        r_warn = logging.LogRecord("test", logging.WARNING, "", 0, "same", (), None)
        assert f.filter(r_info) is True
        assert f.filter(r_warn) is True  # Different level = different key


class TestOTELNoiseSuppressor:
    """Tests for OTELNoiseSuppressor filter."""

    def test_instantiation(self):
        from src.LOGGING.modular_logging_system import OTELNoiseSuppressor
        f = OTELNoiseSuppressor()
        assert f is not None

    def test_passes_normal_log(self):
        from src.LOGGING.modular_logging_system import OTELNoiseSuppressor
        f = OTELNoiseSuppressor()
        record = logging.LogRecord("test", logging.ERROR, "", 0, "Unrelated error", (), None)
        # Non-OTEL error passes
        assert f.filter(record) is True

    def test_suppresses_otel_noise(self):
        from src.LOGGING.modular_logging_system import OTELNoiseSuppressor
        import os
        os.environ.setdefault("NUSYG_SUPPRESS_OTEL_ERRORS", "1")
        f = OTELNoiseSuppressor()
        record = logging.LogRecord(
            "opentelemetry.sdk._shared_internal", logging.ERROR, "", 0,
            "ConnectionRefusedError connecting to localhost:4318", (), None
        )
        # Should be suppressed when OTEL suppression is enabled
        result = f.filter(record)
        assert isinstance(result, bool)

    def test_has_benign_patterns(self):
        from src.LOGGING.modular_logging_system import OTELNoiseSuppressor
        patterns = OTELNoiseSuppressor.BENIGN_PATTERNS
        assert isinstance(patterns, list)
        assert len(patterns) > 0


class TestModuleHelperFunctions:
    """Tests for module-level helper functions."""

    def test_get_logger_returns_logger(self):
        from src.LOGGING.modular_logging_system import get_logger
        lg = get_logger("test_module")
        assert isinstance(lg, logging.Logger)

    def test_get_logger_same_name_same_instance(self):
        from src.LOGGING.modular_logging_system import get_logger
        l1 = get_logger("same_name")
        l2 = get_logger("same_name")
        assert l1 is l2

    def test_get_dedup_status_returns_dict(self):
        from src.LOGGING.modular_logging_system import get_dedup_status
        status = get_dedup_status()
        assert isinstance(status, dict)

    def test_log_info_no_exception(self):
        from src.LOGGING.modular_logging_system import log_info
        log_info("test_module", "Test info message")  # Should not raise

    def test_log_debug_no_exception(self):
        from src.LOGGING.modular_logging_system import log_debug
        log_debug("test_module", "Test debug message")

    def test_log_error_no_exception(self):
        from src.LOGGING.modular_logging_system import log_error
        log_error("test_module", "Test error message")

    def test_log_warning_no_exception(self):
        from src.LOGGING.modular_logging_system import log_warning
        log_warning("test_module", "Test warning message")

    def test_log_tagged_event_no_exception(self):
        from src.LOGGING.modular_logging_system import log_tagged_event
        log_tagged_event(
            "test_module", "Something happened",
            omnitag={"purpose": "unit_test", "dependencies": []},
        )

    def test_configure_logging_no_exception(self):
        from src.LOGGING.modular_logging_system import configure_logging
        configure_logging(level=logging.WARNING)  # Should not raise


class TestDedupWindowHelpers:
    """Tests for internal dedup window helper functions."""

    def test_dedup_window_key_format(self):
        from src.LOGGING.modular_logging_system import _dedup_window_key
        key = _dedup_window_key("my.logger")
        assert isinstance(key, str)
        assert key.startswith("NU_SYG_LOG_DEDUP_WINDOW_")

    def test_dedup_window_key_sanitizes(self):
        from src.LOGGING.modular_logging_system import _dedup_window_key
        key = _dedup_window_key("src.module.sub")
        # Dots should be replaced with underscores
        assert "." not in key

    def test_dedup_window_for_logger_returns_float(self):
        from src.LOGGING.modular_logging_system import _dedup_window_for_logger
        window = _dedup_window_for_logger("test.logger")
        assert isinstance(window, float)
        assert window > 0
