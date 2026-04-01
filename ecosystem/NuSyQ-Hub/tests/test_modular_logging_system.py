"""Comprehensive tests for src/LOGGING/modular_logging_system.py."""

import logging
import os
import time


class TestDuplicateMessageFilterInstantiation:
    """Tests for DuplicateMessageFilter instantiation and defaults."""

    def test_default_instantiation(self):
        from src.LOGGING.modular_logging_system import DuplicateMessageFilter

        f = DuplicateMessageFilter()
        assert f.window_seconds == 2.0
        assert f.logger_name == "root"

    def test_custom_window(self):
        from src.LOGGING.modular_logging_system import DuplicateMessageFilter

        f = DuplicateMessageFilter(window_seconds=10.0, logger_name="mylogger")
        assert f.window_seconds == 10.0
        assert f.logger_name == "mylogger"

    def test_cache_starts_empty(self):
        from src.LOGGING.modular_logging_system import DuplicateMessageFilter

        f = DuplicateMessageFilter()
        assert f._cache == {}

    def test_is_logging_filter_subclass(self):
        from src.LOGGING.modular_logging_system import DuplicateMessageFilter

        assert issubclass(DuplicateMessageFilter, logging.Filter)


class TestDuplicateMessageFilterBehavior:
    """Tests for DuplicateMessageFilter.filter() logic."""

    def _make_record(self, name="test", level=logging.INFO, msg="hello"):
        return logging.LogRecord(name, level, "", 0, msg, (), None)

    def test_first_message_always_passes(self):
        from src.LOGGING.modular_logging_system import DuplicateMessageFilter

        f = DuplicateMessageFilter(window_seconds=5.0)
        record = self._make_record(msg="first message")
        assert f.filter(record) is True

    def test_duplicate_within_window_blocked(self):
        from src.LOGGING.modular_logging_system import DuplicateMessageFilter

        f = DuplicateMessageFilter(window_seconds=10.0)
        record = self._make_record(msg="repeated message")
        assert f.filter(record) is True
        assert f.filter(record) is False

    def test_different_messages_both_pass(self):
        from src.LOGGING.modular_logging_system import DuplicateMessageFilter

        f = DuplicateMessageFilter(window_seconds=10.0)
        r1 = self._make_record(msg="message A")
        r2 = self._make_record(msg="message B")
        assert f.filter(r1) is True
        assert f.filter(r2) is True

    def test_different_levels_tracked_separately(self):
        from src.LOGGING.modular_logging_system import DuplicateMessageFilter

        f = DuplicateMessageFilter(window_seconds=10.0)
        r_info = self._make_record(level=logging.INFO, msg="same text")
        r_warn = self._make_record(level=logging.WARNING, msg="same text")
        assert f.filter(r_info) is True
        assert f.filter(r_warn) is True

    def test_different_loggers_tracked_separately(self):
        from src.LOGGING.modular_logging_system import DuplicateMessageFilter

        f = DuplicateMessageFilter(window_seconds=10.0)
        r1 = self._make_record(name="logger_a", msg="shared msg")
        r2 = self._make_record(name="logger_b", msg="shared msg")
        assert f.filter(r1) is True
        assert f.filter(r2) is True

    def test_zero_window_allows_repeat_after_sleep(self):
        from src.LOGGING.modular_logging_system import DuplicateMessageFilter

        f = DuplicateMessageFilter(window_seconds=0.0)
        record = self._make_record(msg="repeat after zero")
        f.filter(record)
        time.sleep(0.02)
        assert f.filter(record) is True

    def test_cache_populated_after_filter(self):
        from src.LOGGING.modular_logging_system import DuplicateMessageFilter

        f = DuplicateMessageFilter(window_seconds=5.0)
        record = self._make_record(msg="cached msg")
        f.filter(record)
        assert len(f._cache) == 1

    def test_multiple_messages_all_cached(self):
        from src.LOGGING.modular_logging_system import DuplicateMessageFilter

        f = DuplicateMessageFilter(window_seconds=5.0)
        for i in range(5):
            record = self._make_record(msg=f"unique message {i}")
            f.filter(record)
        assert len(f._cache) == 5

    def test_args_expanded_in_message_key(self):
        from src.LOGGING.modular_logging_system import DuplicateMessageFilter

        f = DuplicateMessageFilter(window_seconds=5.0)
        r1 = logging.LogRecord("test", logging.INFO, "", 0, "val=%s", ("a",), None)
        r2 = logging.LogRecord("test", logging.INFO, "", 0, "val=%s", ("b",), None)
        # Different formatted messages — both should pass
        assert f.filter(r1) is True
        assert f.filter(r2) is True


class TestOTELNoiseSuppressor:
    """Tests for OTELNoiseSuppressor filter."""

    def test_instantiation(self):
        from src.LOGGING.modular_logging_system import OTELNoiseSuppressor

        f = OTELNoiseSuppressor()
        assert f is not None

    def test_is_logging_filter_subclass(self):
        from src.LOGGING.modular_logging_system import OTELNoiseSuppressor

        assert issubclass(OTELNoiseSuppressor, logging.Filter)

    def test_benign_patterns_is_class_var_list(self):
        from src.LOGGING.modular_logging_system import OTELNoiseSuppressor

        patterns = OTELNoiseSuppressor.BENIGN_PATTERNS
        assert isinstance(patterns, list)
        assert len(patterns) > 0

    def test_normal_log_passes(self):
        from src.LOGGING.modular_logging_system import OTELNoiseSuppressor

        f = OTELNoiseSuppressor()
        record = logging.LogRecord("myapp", logging.ERROR, "", 0, "Database timeout", (), None)
        assert f.filter(record) is True

    def test_suppresses_connection_refused_in_message(self):
        from src.LOGGING.modular_logging_system import OTELNoiseSuppressor

        f = OTELNoiseSuppressor()
        record = logging.LogRecord(
            "some.logger",
            logging.ERROR,
            "",
            0,
            "ConnectionRefusedError while exporting",
            (),
            None,
        )
        assert f.filter(record) is False

    def test_suppresses_otel_logger_name(self):
        from src.LOGGING.modular_logging_system import OTELNoiseSuppressor

        f = OTELNoiseSuppressor()
        record = logging.LogRecord(
            "opentelemetry.sdk._shared_internal",
            logging.WARNING,
            "",
            0,
            "Export failed",
            (),
            None,
        )
        assert f.filter(record) is False

    def test_suppresses_max_retries(self):
        from src.LOGGING.modular_logging_system import OTELNoiseSuppressor

        f = OTELNoiseSuppressor()
        record = logging.LogRecord(
            "urllib3",
            logging.ERROR,
            "",
            0,
            "Max retries exceeded with url: /v1/traces",
            (),
            None,
        )
        assert f.filter(record) is False

    def test_suppresses_failed_to_establish_connection(self):
        from src.LOGGING.modular_logging_system import OTELNoiseSuppressor

        f = OTELNoiseSuppressor()
        record = logging.LogRecord(
            "urllib3",
            logging.ERROR,
            "",
            0,
            "Failed to establish a new connection: localhost:4318",
            (),
            None,
        )
        assert f.filter(record) is False

    def test_exc_info_included_in_check(self):
        from src.LOGGING.modular_logging_system import OTELNoiseSuppressor

        f = OTELNoiseSuppressor()
        try:
            raise ConnectionRefusedError("target machine actively refused it")
        except ConnectionRefusedError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord("otel", logging.ERROR, "", 0, "export error", (), exc_info)
        # The exc_info path exercises traceback formatting — should return bool
        result = f.filter(record)
        assert isinstance(result, bool)


class TestDedupWindowHelpers:
    """Tests for _dedup_window_key and _dedup_window_for_logger."""

    def test_dedup_window_key_format(self):
        from src.LOGGING.modular_logging_system import _dedup_window_key

        key = _dedup_window_key("my.logger")
        assert key.startswith("NU_SYG_LOG_DEDUP_WINDOW_")

    def test_dedup_window_key_sanitizes_dots(self):
        from src.LOGGING.modular_logging_system import _dedup_window_key

        key = _dedup_window_key("src.module.sub")
        assert "." not in key

    def test_dedup_window_key_empty_string_returns_root(self):
        from src.LOGGING.modular_logging_system import _dedup_window_key

        key = _dedup_window_key("")
        assert "ROOT" in key

    def test_dedup_window_key_all_special_chars(self):
        from src.LOGGING.modular_logging_system import _dedup_window_key

        key = _dedup_window_key("---")
        assert "ROOT" in key

    def test_dedup_window_for_logger_returns_float(self):
        from src.LOGGING.modular_logging_system import _dedup_window_for_logger

        window = _dedup_window_for_logger("test.logger")
        assert isinstance(window, float)

    def test_dedup_window_for_logger_default_value(self):
        from src.LOGGING.modular_logging_system import _dedup_window_for_logger

        # Without env override, should return 2.0 (default)
        window = _dedup_window_for_logger("some.unknown.logger.xyz")
        assert window >= 0.0

    def test_dedup_window_for_logger_env_override(self, monkeypatch):
        from src.LOGGING.modular_logging_system import _dedup_window_for_logger, _dedup_window_key

        key = _dedup_window_key("my.test.logger")
        monkeypatch.setenv(key, "7.5")
        window = _dedup_window_for_logger("my.test.logger")
        assert window == 7.5

    def test_dedup_window_for_logger_global_env(self, monkeypatch):
        from src.LOGGING.modular_logging_system import _dedup_window_for_logger

        monkeypatch.setenv("NU_SYG_LOG_DEDUP_WINDOW", "3.5")
        # Use a name that won't have a specific env key set
        window = _dedup_window_for_logger("unique.logger.xyz.abc.no.override")
        assert window == 3.5

    def test_dedup_window_invalid_env_falls_back_to_default(self, monkeypatch):
        from src.LOGGING.modular_logging_system import _dedup_window_for_logger, _dedup_window_key

        key = _dedup_window_key("invalid.env.logger")
        monkeypatch.setenv(key, "not_a_float")
        # Falls back to global NU_SYG_LOG_DEDUP_WINDOW or hardcoded 2.0
        window = _dedup_window_for_logger("invalid.env.logger")
        assert isinstance(window, float)


class TestInstallFilters:
    """Tests for _install_duplicate_filter and _install_otel_suppressor."""

    def test_install_duplicate_filter_adds_filter(self):
        from src.LOGGING.modular_logging_system import (
            DuplicateMessageFilter,
            _install_duplicate_filter,
        )

        lg = logging.getLogger("test.install.dedup.filter")
        lg.filters = []
        _install_duplicate_filter(lg)
        assert any(isinstance(f, DuplicateMessageFilter) for f in lg.filters)

    def test_install_duplicate_filter_idempotent(self):
        from src.LOGGING.modular_logging_system import (
            DuplicateMessageFilter,
            _install_duplicate_filter,
        )

        lg = logging.getLogger("test.install.dedup.idempotent")
        lg.filters = []
        _install_duplicate_filter(lg)
        _install_duplicate_filter(lg)
        count = sum(1 for f in lg.filters if isinstance(f, DuplicateMessageFilter))
        assert count == 1

    def test_install_otel_suppressor_adds_filter(self, monkeypatch):
        from src.LOGGING.modular_logging_system import (
            OTELNoiseSuppressor,
            _install_otel_suppressor,
        )

        monkeypatch.setenv("NUSYG_SUPPRESS_OTEL_ERRORS", "1")
        lg = logging.getLogger("test.install.otel.filter")
        lg.filters = []
        _install_otel_suppressor(lg)
        assert any(isinstance(f, OTELNoiseSuppressor) for f in lg.filters)

    def test_install_otel_suppressor_skipped_when_disabled(self, monkeypatch):
        from src.LOGGING.modular_logging_system import (
            OTELNoiseSuppressor,
            _install_otel_suppressor,
        )

        monkeypatch.setenv("NUSYG_SUPPRESS_OTEL_ERRORS", "0")
        lg = logging.getLogger("test.install.otel.disabled")
        lg.filters = []
        _install_otel_suppressor(lg)
        assert not any(isinstance(f, OTELNoiseSuppressor) for f in lg.filters)

    def test_install_otel_suppressor_idempotent(self, monkeypatch):
        from src.LOGGING.modular_logging_system import (
            OTELNoiseSuppressor,
            _install_otel_suppressor,
        )

        monkeypatch.setenv("NUSYG_SUPPRESS_OTEL_ERRORS", "1")
        lg = logging.getLogger("test.install.otel.idempotent")
        lg.filters = []
        _install_otel_suppressor(lg)
        _install_otel_suppressor(lg)
        count = sum(1 for f in lg.filters if isinstance(f, OTELNoiseSuppressor))
        assert count == 1


class TestGetLogger:
    """Tests for get_logger()."""

    def test_returns_logger_instance(self):
        from src.LOGGING.modular_logging_system import get_logger

        lg = get_logger("test.get_logger.a")
        assert isinstance(lg, logging.Logger)

    def test_same_name_same_instance(self):
        from src.LOGGING.modular_logging_system import get_logger

        l1 = get_logger("test.get_logger.same")
        l2 = get_logger("test.get_logger.same")
        assert l1 is l2

    def test_logger_has_duplicate_filter(self):
        from src.LOGGING.modular_logging_system import DuplicateMessageFilter, get_logger

        lg = get_logger("test.get_logger.filters")
        assert any(isinstance(f, DuplicateMessageFilter) for f in lg.filters)

    def test_different_names_different_loggers(self):
        from src.LOGGING.modular_logging_system import get_logger

        l1 = get_logger("test.get_logger.alpha")
        l2 = get_logger("test.get_logger.beta")
        assert l1 is not l2


class TestGetDedupStatus:
    """Tests for get_dedup_status()."""

    def test_returns_dict(self):
        from src.LOGGING.modular_logging_system import get_dedup_status

        status = get_dedup_status()
        assert isinstance(status, dict)

    def test_required_keys_present(self):
        from src.LOGGING.modular_logging_system import get_dedup_status

        status = get_dedup_status()
        for key in (
            "root",
            "handler_count",
            "handlers_with_filters",
            "handler_details",
            "logger_filter_count",
            "total_filter_count",
            "window_default",
            "logger_windows",
            "status",
        ):
            assert key in status, f"Missing key: {key}"

    def test_status_is_string(self):
        from src.LOGGING.modular_logging_system import get_dedup_status

        status = get_dedup_status()
        assert isinstance(status["status"], str)
        assert status["status"] in ("active", "inactive")

    def test_handler_details_is_list(self):
        from src.LOGGING.modular_logging_system import get_dedup_status

        status = get_dedup_status()
        assert isinstance(status["handler_details"], list)

    def test_logger_windows_is_dict(self):
        from src.LOGGING.modular_logging_system import get_dedup_status

        status = get_dedup_status()
        assert isinstance(status["logger_windows"], dict)

    def test_counts_are_ints(self):
        from src.LOGGING.modular_logging_system import get_dedup_status

        status = get_dedup_status()
        assert isinstance(status["handler_count"], int)
        assert isinstance(status["logger_filter_count"], int)
        assert isinstance(status["total_filter_count"], int)


class TestLogFunctions:
    """Tests for log_info, log_debug, log_error, log_warning, log_subprocess_event, etc."""

    def test_log_info_does_not_raise(self):
        from src.LOGGING.modular_logging_system import log_info

        log_info("test.module", "Info message")

    def test_log_debug_does_not_raise(self):
        from src.LOGGING.modular_logging_system import log_debug

        log_debug("test.module", "Debug message")

    def test_log_error_does_not_raise(self):
        from src.LOGGING.modular_logging_system import log_error

        log_error("test.module", "Error message")

    def test_log_error_with_exc_info(self):
        from src.LOGGING.modular_logging_system import log_error

        log_error("test.module", "Error with exc_info", exc_info=True)

    def test_log_warning_does_not_raise(self):
        from src.LOGGING.modular_logging_system import log_warning

        log_warning("test.module", "Warning message")

    def test_log_subprocess_event_minimal(self):
        from src.LOGGING.modular_logging_system import log_subprocess_event

        log_subprocess_event("test.module", "Process started")

    def test_log_subprocess_event_full(self):
        from src.LOGGING.modular_logging_system import log_subprocess_event

        log_subprocess_event(
            "test.module",
            "Process started",
            command="python foo.py",
            pid=1234,
            tags={"env": "test"},
        )

    def test_log_subprocess_event_includes_metadata(self, caplog):
        from src.LOGGING.modular_logging_system import log_subprocess_event

        with caplog.at_level(logging.INFO, logger="test.subprocess.meta"):
            log_subprocess_event(
                "test.subprocess.meta",
                "event",
                command="ls",
                pid=42,
                tags={"key": "val"},
            )
        assert any("Metadata" in r.message for r in caplog.records)

    def test_log_tagged_event_omnitag_only(self):
        from src.LOGGING.modular_logging_system import log_tagged_event

        log_tagged_event("test.module", "Tagged event", omnitag={"purpose": "test"})

    def test_log_tagged_event_megatag_string(self):
        from src.LOGGING.modular_logging_system import log_tagged_event

        log_tagged_event("test.module", "Tagged event", megatag="MEGA_TAG_STRING")

    def test_log_tagged_event_megatag_dict(self):
        from src.LOGGING.modular_logging_system import log_tagged_event

        log_tagged_event("test.module", "Tagged event", megatag={"key": "val"})

    def test_log_tagged_event_rshts(self):
        from src.LOGGING.modular_logging_system import log_tagged_event

        log_tagged_event("test.module", "Tagged event", rshts="RSHTS_SYM")

    def test_log_tagged_event_all_tags(self, caplog):
        from src.LOGGING.modular_logging_system import log_tagged_event

        with caplog.at_level(logging.INFO, logger="test.tagged.all"):
            log_tagged_event(
                "test.tagged.all",
                "Full event",
                omnitag={"a": 1},
                megatag="MTAG",
                rshts="RSYMBOL",
            )
        assert any("Tags" in r.message for r in caplog.records)

    def test_log_tagged_event_no_tags(self):
        from src.LOGGING.modular_logging_system import log_tagged_event

        log_tagged_event("test.module", "No tags event")

    def test_log_consciousness_default_level(self):
        from src.LOGGING.modular_logging_system import log_consciousness

        log_consciousness("test.module", "Awareness rising")

    def test_log_consciousness_custom_level(self, caplog):
        from src.LOGGING.modular_logging_system import log_consciousness

        with caplog.at_level(logging.INFO, logger="test.consciousness"):
            log_consciousness("test.consciousness", "Deep awareness", awareness_level=0.85)
        assert any("0.85" in r.message for r in caplog.records)

    def test_log_cultivation_default_growth(self):
        from src.LOGGING.modular_logging_system import log_cultivation

        log_cultivation("test.module", "Growth event")

    def test_log_cultivation_custom_growth(self, caplog):
        from src.LOGGING.modular_logging_system import log_cultivation

        with caplog.at_level(logging.INFO, logger="test.cultivation"):
            log_cultivation("test.cultivation", "Cultivating", growth_level=0.5)
        assert any("0.50" in r.message for r in caplog.records)


class TestConfigureLogging:
    """Tests for configure_logging()."""

    def test_configure_logging_no_exception(self):
        from src.LOGGING.modular_logging_system import configure_logging

        configure_logging(level=logging.WARNING)

    def test_configure_logging_with_log_file(self, tmp_path):
        from src.LOGGING.modular_logging_system import configure_logging

        log_file = str(tmp_path / "test.log")
        configure_logging(level=logging.DEBUG, log_file=log_file)
        import os as _os

        assert _os.path.exists(log_file)

    def test_configure_logging_env_log_file(self, tmp_path, monkeypatch):
        from src.LOGGING.modular_logging_system import configure_logging

        log_file = str(tmp_path / "env_test.log")
        monkeypatch.setenv("NUSYG_LOG_FILE", log_file)
        configure_logging(level=logging.INFO)
        import os as _os

        assert _os.path.exists(log_file)

    def test_configure_logging_json_format(self, monkeypatch):
        from src.LOGGING.modular_logging_system import configure_logging

        monkeypatch.setenv("NUSYG_LOG_FORMAT", "json")
        # Should not raise regardless of whether StructuredFormatter is available
        configure_logging(level=logging.INFO)

    def test_configure_logging_rotate_env(self, tmp_path, monkeypatch):
        from src.LOGGING.modular_logging_system import configure_logging

        log_file = str(tmp_path / "rotating.log")
        monkeypatch.setenv("NUSYG_LOG_ROTATE", "1")
        configure_logging(level=logging.INFO, log_file=log_file)

    def test_configure_logging_rotate_max_bytes(self, tmp_path, monkeypatch):
        from src.LOGGING.modular_logging_system import configure_logging

        log_file = str(tmp_path / "rotating_bytes.log")
        monkeypatch.setenv("NUSYG_LOG_ROTATE", "1")
        monkeypatch.setenv("NUSYG_LOG_ROTATE_MAX_BYTES", "1048576")
        configure_logging(level=logging.INFO, log_file=log_file)

    def test_configure_logging_rotate_max_mb(self, tmp_path, monkeypatch):
        from src.LOGGING.modular_logging_system import configure_logging

        log_file = str(tmp_path / "rotating_mb.log")
        monkeypatch.setenv("NUSYG_LOG_ROTATE", "1")
        monkeypatch.setenv("NUSYG_LOG_ROTATE_MAX_MB", "5")
        configure_logging(level=logging.INFO, log_file=log_file)

    def test_configure_logging_backup_count_env(self, tmp_path, monkeypatch):
        from src.LOGGING.modular_logging_system import configure_logging

        log_file = str(tmp_path / "rotating_backups.log")
        monkeypatch.setenv("NUSYG_LOG_ROTATE", "1")
        monkeypatch.setenv("NUSYG_LOG_ROTATE_BACKUPS", "3")
        configure_logging(level=logging.INFO, log_file=log_file)

    def test_configure_logging_installs_dedup_filter(self):
        from src.LOGGING.modular_logging_system import DuplicateMessageFilter, configure_logging

        configure_logging(level=logging.INFO)
        root = logging.getLogger()
        assert any(isinstance(f, DuplicateMessageFilter) for f in root.filters)


class TestModuleExports:
    """Tests to ensure __all__ exports are importable."""

    def test_all_exports_importable(self):
        import src.LOGGING.modular_logging_system as mod

        for name in mod.__all__:
            assert hasattr(mod, name), f"Missing export: {name}"

    def test_all_contains_expected_names(self):
        import src.LOGGING.modular_logging_system as mod

        expected = {
            "configure_logging",
            "get_logger",
            "log_consciousness",
            "log_debug",
            "log_error",
            "log_info",
            "log_subprocess_event",
            "log_tagged_event",
            "log_warning",
        }
        assert expected.issubset(set(mod.__all__))
