"""Tests for observability subsystem modules.

Covers:
- StructuredFormatter / HumanReadableFormatter / setup_logger / rate_limited_log / log_operation
- LightweightTracer span creation, context propagation, timing
- SnapshotDeltaTracker diff computation, change detection, trend summary
- MetricsCollector init, record_event, aggregate_metrics
- MetricsCollector.generate_text_dashboard
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Structured Logging
# ---------------------------------------------------------------------------
from src.observability.structured_logging import (
    HumanReadableFormatter,
    StructuredFormatter,
    clear_rate_limit_cache,
    get_application_logger,
    get_health_check_logger,
    get_import_logger,
    get_log_level_from_env,
    get_webhook_logger,
    log_operation,
    rate_limited_log,
    setup_logger,
)

# ---------------------------------------------------------------------------
# Lightweight Tracer
# ---------------------------------------------------------------------------
from src.observability.lightweight_tracer import LightweightTracer, Span

# ---------------------------------------------------------------------------
# Snapshot Delta
# ---------------------------------------------------------------------------
from src.observability.snapshot_delta import (
    SnapshotDelta,
    SnapshotDeltaTracker,
    SnapshotMetrics,
)

# ---------------------------------------------------------------------------
# Autonomy Dashboard
# ---------------------------------------------------------------------------
from src.observability.autonomy_dashboard import (
    DashboardMetrics,
    MetricEvent,
    MetricType,
    MetricsCollector,
    get_metrics_collector,
)


# ===========================================================================
# Helpers
# ===========================================================================

def _make_snapshot(
    timestamp: str = "2026-01-01T00:00:00",
    dirty: int = 5,
    commits_ahead: int = 2,
    commits_behind: int = 0,
    quest_status: str = "active",
    quest_title: str = "Quest A",
    import_failures: int = 3,
    test_failures: int = 1,
    agent_activity: dict | None = None,
) -> SnapshotMetrics:
    return SnapshotMetrics(
        timestamp=timestamp,
        dirty_file_count=dirty,
        commits_ahead=commits_ahead,
        commits_behind=commits_behind,
        quest_status=quest_status,
        quest_title=quest_title,
        import_failures=import_failures,
        test_failures=test_failures,
        agent_activity=agent_activity or {"ollama": 1, "chatdev": 0},
    )


# ===========================================================================
# StructuredFormatter
# ===========================================================================

def _make_log_record(
    name: str = "test",
    level: int = logging.INFO,
    pathname: str = "",
    lineno: int = 0,
    msg: str = "test message",
    exc_info=None,
) -> logging.LogRecord:
    return logging.LogRecord(
        name=name, level=level, pathname=pathname, lineno=lineno,
        msg=msg, args=(), exc_info=exc_info,
    )


def _format_patched(fmt: StructuredFormatter, record: logging.LogRecord) -> dict:
    """Call fmt.format() with formatTime patched to work on Windows (no %f)."""
    with patch.object(
        fmt, "formatTime", return_value="2026-01-01T00:00:00.000000Z"
    ):
        return json.loads(fmt.format(record))


class TestStructuredFormatter:
    def test_format_returns_json(self):
        fmt = StructuredFormatter(service_name="test-svc", include_trace=False)
        record = _make_log_record(name="test", level=logging.INFO, msg="hello world")
        data = _format_patched(fmt, record)
        assert data["message"] == "hello world"
        assert data["service"] == "test-svc"
        assert data["level"] == "INFO"

    def test_format_contains_timestamp_and_logger(self):
        fmt = StructuredFormatter(include_trace=False)
        record = _make_log_record(name="mylogger", level=logging.WARNING, msg="warn msg")
        data = _format_patched(fmt, record)
        assert "timestamp" in data
        assert data["logger"] == "mylogger"

    def test_format_contains_source_block(self):
        fmt = StructuredFormatter(include_trace=False)
        record = _make_log_record(pathname="/a/b.py", lineno=42, msg="dbg")
        data = _format_patched(fmt, record)
        assert data["source"]["line"] == 42
        assert data["source"]["file"] == "/a/b.py"

    def test_format_with_exception_info(self):
        fmt = StructuredFormatter(include_trace=False)
        try:
            raise ValueError("boom")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        record = _make_log_record(name="x", level=logging.ERROR, msg="err",
                                  exc_info=exc_info)
        data = _format_patched(fmt, record)
        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"

    def test_format_with_extra_fields(self):
        fmt = StructuredFormatter(include_trace=False)
        record = _make_log_record(name="x", msg="extra")
        record.user_id = "u123"  # type: ignore[attr-defined]
        data = _format_patched(fmt, record)
        assert data.get("user_id") == "u123"

    def test_format_no_trace_when_disabled(self):
        fmt = StructuredFormatter(include_trace=False)
        record = _make_log_record(name="x", msg="no trace")
        data = _format_patched(fmt, record)
        assert "trace_id" not in data


# ===========================================================================
# HumanReadableFormatter
# ===========================================================================

class TestHumanReadableFormatter:
    def test_format_contains_message(self):
        fmt = HumanReadableFormatter(include_trace=False)
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="human readable", args=(), exc_info=None,
        )
        output = fmt.format(record)
        assert "human readable" in output

    def test_format_contains_level(self):
        fmt = HumanReadableFormatter(include_trace=False)
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="", lineno=0,
            msg="err", args=(), exc_info=None,
        )
        output = fmt.format(record)
        assert "ERROR" in output

    def test_include_trace_false_no_trace_id(self):
        fmt = HumanReadableFormatter(include_trace=False)
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="msg", args=(), exc_info=None,
        )
        output = fmt.format(record)
        assert "trace_id" not in output


# ===========================================================================
# setup_logger
# ===========================================================================

class TestSetupLogger:
    def test_returns_logger_with_name(self):
        logger = setup_logger("test.setup.human", console=False)
        assert logger.name == "test.setup.human"

    def test_json_format_attaches_structured_formatter(self):
        logger = setup_logger("test.setup.json", log_format="json", console=True)
        assert any(isinstance(h.formatter, StructuredFormatter) for h in logger.handlers)

    def test_human_format_attaches_human_formatter(self):
        logger = setup_logger("test.setup.human2", log_format="human", console=True)
        assert any(isinstance(h.formatter, HumanReadableFormatter) for h in logger.handlers)

    def test_log_level_applied(self):
        logger = setup_logger("test.setup.level", level=logging.DEBUG, console=False)
        assert logger.level == logging.DEBUG

    def test_no_console_no_stream_handler(self):
        logger = setup_logger("test.setup.noconsole", console=False)
        stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)
                           and not isinstance(h, logging.handlers.RotatingFileHandler)]
        assert len(stream_handlers) == 0

    def test_file_handler_created(self, tmp_path):
        log_file = tmp_path / "test.log"
        logger = setup_logger("test.setup.file", log_file=log_file, console=False)
        rotating = [h for h in logger.handlers
                    if isinstance(h, logging.handlers.RotatingFileHandler)]
        assert len(rotating) == 1
        assert log_file.exists()

    def test_string_level_accepted(self):
        logger = setup_logger("test.setup.str_level", level="WARNING", console=False)
        assert logger.level == logging.WARNING


# ===========================================================================
# rate_limited_log
# ===========================================================================

class TestRateLimitedLog:
    def setup_method(self):
        clear_rate_limit_cache()

    def teardown_method(self):
        clear_rate_limit_cache()

    def test_first_call_logs(self):
        logger = setup_logger("test.ratelimit", level=logging.DEBUG, console=False)
        result = rate_limited_log(logger, logging.INFO, "msg", "key1", rate_limit_seconds=60)
        assert result is True

    def test_second_call_within_window_suppressed(self):
        logger = setup_logger("test.ratelimit2", level=logging.DEBUG, console=False)
        rate_limited_log(logger, logging.INFO, "msg", "key2", rate_limit_seconds=60)
        result = rate_limited_log(logger, logging.INFO, "msg", "key2", rate_limit_seconds=60)
        assert result is False

    def test_call_after_window_logs(self):
        logger = setup_logger("test.ratelimit3", level=logging.DEBUG, console=False)
        rate_limited_log(logger, logging.INFO, "msg", "key3", rate_limit_seconds=0.0)
        time.sleep(0.01)
        result = rate_limited_log(logger, logging.INFO, "msg", "key3", rate_limit_seconds=0.0)
        assert result is True

    def test_suppressed_count_appended_to_message(self, caplog):
        logger = setup_logger("test.ratelimit4", level=logging.DEBUG, console=False)
        logger.propagate = True
        rate_limited_log(logger, logging.INFO, "msg", "key4", rate_limit_seconds=60)
        rate_limited_log(logger, logging.INFO, "msg", "key4", rate_limit_seconds=60)
        rate_limited_log(logger, logging.INFO, "msg", "key4", rate_limit_seconds=60)
        with caplog.at_level(logging.INFO, logger="test.ratelimit4"):
            result = rate_limited_log(logger, logging.INFO, "msg", "key4", rate_limit_seconds=0)
        assert result is True

    def test_clear_rate_limit_cache_resets(self):
        logger = setup_logger("test.ratelimit5", level=logging.DEBUG, console=False)
        rate_limited_log(logger, logging.INFO, "msg", "key5", rate_limit_seconds=60)
        clear_rate_limit_cache()
        result = rate_limited_log(logger, logging.INFO, "msg", "key5", rate_limit_seconds=60)
        assert result is True


# ===========================================================================
# log_operation context manager
# ===========================================================================

class TestLogOperation:
    def test_success_path_logs_completed(self, caplog):
        logger = setup_logger("test.logop", level=logging.DEBUG, console=False)
        logger.propagate = True
        with caplog.at_level(logging.INFO, logger="test.logop"):
            with log_operation(logger, "my_op"):
                pass
        assert any("Completed my_op" in r.message for r in caplog.records)

    def test_failure_path_raises_and_logs_failed(self, caplog):
        logger = setup_logger("test.logop.err", level=logging.DEBUG, console=False)
        logger.propagate = True
        with caplog.at_level(logging.ERROR, logger="test.logop.err"):
            with pytest.raises(RuntimeError):
                with log_operation(logger, "bad_op"):
                    raise RuntimeError("intentional")
        assert any("Failed bad_op" in r.message for r in caplog.records)

    def test_log_args_true_logs_start(self, caplog):
        logger = setup_logger("test.logop.args", level=logging.DEBUG, console=False)
        logger.propagate = True
        with caplog.at_level(logging.DEBUG, logger="test.logop.args"):
            with log_operation(logger, "start_op", log_args=True, user="alice"):
                pass
        assert any("Starting start_op" in r.message for r in caplog.records)


# ===========================================================================
# get_log_level_from_env
# ===========================================================================

class TestGetLogLevelFromEnv:
    def test_returns_default_when_no_env(self, monkeypatch):
        monkeypatch.delenv("NUSYQ_LOG_LEVEL", raising=False)
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        assert get_log_level_from_env(logging.WARNING) == logging.WARNING

    def test_reads_nusyq_log_level(self, monkeypatch):
        monkeypatch.setenv("NUSYQ_LOG_LEVEL", "DEBUG")
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        assert get_log_level_from_env() == logging.DEBUG

    def test_reads_log_level_fallback(self, monkeypatch):
        monkeypatch.delenv("NUSYQ_LOG_LEVEL", raising=False)
        monkeypatch.setenv("LOG_LEVEL", "ERROR")
        assert get_log_level_from_env() == logging.ERROR

    def test_case_insensitive(self, monkeypatch):
        monkeypatch.setenv("NUSYQ_LOG_LEVEL", "warning")
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        assert get_log_level_from_env() == logging.WARNING

    def test_unknown_value_returns_default(self, monkeypatch):
        monkeypatch.setenv("NUSYQ_LOG_LEVEL", "NONSENSE")
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        assert get_log_level_from_env(logging.INFO) == logging.INFO


# ===========================================================================
# Factory logger functions
# ===========================================================================

class TestFactoryLoggers:
    def test_get_import_logger(self):
        lgr = get_import_logger()
        assert lgr.name == "nusyq.imports"

    def test_get_health_check_logger(self):
        lgr = get_health_check_logger()
        assert lgr.name == "nusyq.health"

    def test_get_webhook_logger(self):
        lgr = get_webhook_logger()
        assert lgr.name == "nusyq.webhooks"

    def test_get_application_logger(self):
        lgr = get_application_logger("nusyq.mymodule")
        assert lgr.name == "nusyq.mymodule"

    def test_get_application_logger_with_file(self, tmp_path):
        log_file = tmp_path / "app.log"
        lgr = get_application_logger("nusyq.app.file", log_file=log_file)
        rotating = [h for h in lgr.handlers
                    if isinstance(h, logging.handlers.RotatingFileHandler)]
        assert len(rotating) == 1


# ===========================================================================
# Span
# ===========================================================================

class TestSpan:
    def test_duration_ms_none_when_not_ended(self):
        span = Span(span_id="a", trace_id="t", name="op", start_time=time.time())
        assert span.duration_ms is None

    def test_duration_ms_after_end(self):
        t0 = time.time()
        span = Span(span_id="a", trace_id="t", name="op", start_time=t0,
                    end_time=t0 + 0.5)
        assert abs(span.duration_ms - 500.0) < 1.0

    def test_add_event(self):
        span = Span(span_id="a", trace_id="t", name="op", start_time=time.time())
        span.add_event("checkpoint", {"k": "v"})
        assert len(span.events) == 1
        assert span.events[0]["name"] == "checkpoint"
        assert span.events[0]["attributes"]["k"] == "v"

    def test_to_dict_includes_duration_ms(self):
        t0 = time.time()
        span = Span(span_id="a", trace_id="t", name="op", start_time=t0,
                    end_time=t0 + 1.0)
        d = span.to_dict()
        assert "duration_ms" in d
        assert d["duration_ms"] is not None


# ===========================================================================
# LightweightTracer
# ===========================================================================

class TestLightweightTracer:
    def test_start_trace_returns_uuid(self, tmp_path):
        tracer = LightweightTracer(output_dir=tmp_path)
        trace_id = tracer.start_trace("test_op")
        assert len(trace_id) == 36  # UUID length

    def test_start_trace_registers_root_span(self, tmp_path):
        tracer = LightweightTracer(output_dir=tmp_path)
        trace_id = tracer.start_trace("root")
        assert trace_id in tracer.active_spans
        span_id = tracer.active_spans[trace_id]
        assert span_id in tracer.spans
        assert tracer.spans[span_id].name == "root"

    def test_start_span_creates_child(self, tmp_path):
        tracer = LightweightTracer(output_dir=tmp_path)
        trace_id = tracer.start_trace("root")
        root_span_id = tracer.active_spans[trace_id]
        child_span_id = tracer.start_span(trace_id, "child")
        assert tracer.spans[child_span_id].parent_id == root_span_id

    def test_end_span_sets_end_time(self, tmp_path):
        tracer = LightweightTracer(output_dir=tmp_path)
        trace_id = tracer.start_trace("op")
        span_id = tracer.active_spans[trace_id]
        tracer.end_span(span_id)
        assert tracer.spans[span_id].end_time is not None

    def test_add_event_on_valid_span(self, tmp_path):
        tracer = LightweightTracer(output_dir=tmp_path)
        trace_id = tracer.start_trace("op")
        span_id = tracer.active_spans[trace_id]
        tracer.add_event(span_id, "my_event", {"x": 1})
        assert len(tracer.spans[span_id].events) == 1

    def test_set_attribute_on_valid_span(self, tmp_path):
        tracer = LightweightTracer(output_dir=tmp_path)
        trace_id = tracer.start_trace("op")
        span_id = tracer.active_spans[trace_id]
        tracer.set_attribute(span_id, "env", "production")
        assert tracer.spans[span_id].attributes["env"] == "production"

    def test_end_trace_writes_json_file(self, tmp_path):
        tracer = LightweightTracer(output_dir=tmp_path)
        trace_id = tracer.start_trace("traced_op")
        tracer.end_trace(trace_id)
        files = list(tmp_path.glob("trace_*.json"))
        assert len(files) == 1
        data = json.loads(files[0].read_text())
        assert data["trace_id"] == trace_id

    def test_end_trace_cleans_up_spans(self, tmp_path):
        tracer = LightweightTracer(output_dir=tmp_path)
        trace_id = tracer.start_trace("cleanup_op")
        tracer.end_trace(trace_id)
        assert trace_id not in tracer.active_spans

    def test_end_trace_summary_has_span_count(self, tmp_path):
        tracer = LightweightTracer(output_dir=tmp_path)
        trace_id = tracer.start_trace("sum_op")
        tracer.start_span(trace_id, "child")
        tracer.end_trace(trace_id)
        files = list(tmp_path.glob("trace_*.json"))
        data = json.loads(files[0].read_text())
        assert data["summary"]["span_count"] == 2

    def test_trace_context_manager(self, tmp_path):
        tracer = LightweightTracer(output_dir=tmp_path)
        with tracer.trace("ctx_op") as trace_id:
            assert trace_id in tracer.active_spans
        files = list(tmp_path.glob("trace_*.json"))
        assert len(files) == 1

    def test_span_context_manager(self, tmp_path):
        tracer = LightweightTracer(output_dir=tmp_path)
        trace_id = tracer.start_trace("op")
        with tracer.span(trace_id, "child_ctx") as span_id:
            assert span_id in tracer.spans
        assert tracer.spans[span_id].end_time is not None
        tracer.end_trace(trace_id)

    def test_build_summary_empty_spans(self, tmp_path):
        tracer = LightweightTracer(output_dir=tmp_path)
        summary = tracer._build_summary([])
        assert summary == {}

    def test_generate_obsidian_note(self, tmp_path):
        tracer = LightweightTracer(output_dir=tmp_path)
        trace_id = tracer.start_trace("obsidian_op")
        filepath = tracer.end_trace(trace_id)
        vault_path = tmp_path / "vault"
        vault_path.mkdir()
        note_path = tracer.generate_obsidian_note(filepath, vault_path)
        assert note_path.exists()
        content = note_path.read_text(encoding="utf-8")
        assert "obsidian_op" in content or trace_id[:8] in content

    def test_noop_for_unknown_span_in_end_span(self, tmp_path):
        """end_span on unknown span_id should not raise."""
        tracer = LightweightTracer(output_dir=tmp_path)
        tracer.end_span("nonexistent")  # no exception

    def test_noop_for_unknown_span_in_add_event(self, tmp_path):
        tracer = LightweightTracer(output_dir=tmp_path)
        tracer.add_event("nonexistent", "ev")  # no exception

    def test_noop_for_unknown_span_in_set_attribute(self, tmp_path):
        tracer = LightweightTracer(output_dir=tmp_path)
        tracer.set_attribute("nonexistent", "k", "v")  # no exception


# ===========================================================================
# SnapshotMetrics
# ===========================================================================

class TestSnapshotMetrics:
    def test_to_dict_and_from_dict_roundtrip(self):
        snap = _make_snapshot()
        d = snap.to_dict()
        restored = SnapshotMetrics.from_dict(d)
        assert restored == snap

    def test_to_dict_contains_all_fields(self):
        snap = _make_snapshot()
        d = snap.to_dict()
        assert "dirty_file_count" in d
        assert "agent_activity" in d


# ===========================================================================
# SnapshotDelta
# ===========================================================================

class TestSnapshotDelta:
    def _make_delta(self, **kwargs) -> SnapshotDelta:
        defaults: dict = {
            "previous_timestamp": "2026-01-01T00:00:00",
            "current_timestamp": "2026-01-01T02:00:00",
            "time_delta_hours": 2.0,
            "dirty_file_delta": 0,
            "commits_ahead_delta": 0,
            "quest_changed": False,
            "import_failures_delta": 0,
            "test_failures_delta": 0,
            "agent_activity_delta": {},
            "insights": [],
        }
        defaults.update(kwargs)
        return SnapshotDelta(**defaults)

    def test_to_markdown_contains_header(self):
        delta = self._make_delta()
        md = delta.to_markdown()
        assert "## Snapshot Delta" in md

    def test_to_markdown_dirty_increase_shows_up(self):
        delta = self._make_delta(dirty_file_delta=3)
        md = delta.to_markdown()
        assert "↑" in md

    def test_to_markdown_dirty_decrease_shows_down(self):
        delta = self._make_delta(dirty_file_delta=-2)
        md = delta.to_markdown()
        assert "↓" in md

    def test_to_markdown_quest_changed(self):
        delta = self._make_delta(quest_changed=True)
        md = delta.to_markdown()
        assert "CHANGED" in md

    def test_to_markdown_import_failures_better(self):
        delta = self._make_delta(import_failures_delta=-5)
        md = delta.to_markdown()
        assert "BETTER" in md

    def test_to_markdown_import_failures_worse(self):
        delta = self._make_delta(import_failures_delta=2)
        md = delta.to_markdown()
        assert "WORSE" in md

    def test_to_markdown_agent_activity(self):
        delta = self._make_delta(agent_activity_delta={"ollama": 5})
        md = delta.to_markdown()
        assert "ollama" in md
        assert "+5" in md

    def test_to_markdown_insights(self):
        delta = self._make_delta(insights=["Test insight"])
        md = delta.to_markdown()
        assert "Test insight" in md


# ===========================================================================
# SnapshotDeltaTracker
# ===========================================================================

class TestSnapshotDeltaTracker:
    def test_save_and_load_snapshot(self, tmp_path):
        tracker = SnapshotDeltaTracker(hub_path=tmp_path)
        snap = _make_snapshot()
        tracker.save_snapshot(snap)
        loaded = tracker.load_previous_snapshot()
        assert loaded is not None
        assert loaded.dirty_file_count == snap.dirty_file_count

    def test_load_previous_snapshot_returns_none_when_no_file(self, tmp_path):
        tracker = SnapshotDeltaTracker(hub_path=tmp_path)
        assert tracker.load_previous_snapshot() is None

    def test_compute_delta_dirty_increase(self, tmp_path):
        tracker = SnapshotDeltaTracker(hub_path=tmp_path)
        prev = _make_snapshot(timestamp="2026-01-01T00:00:00", dirty=2)
        curr = _make_snapshot(timestamp="2026-01-01T01:00:00", dirty=8)
        delta = tracker.compute_delta(prev, curr)
        assert delta.dirty_file_delta == 6

    def test_compute_delta_time_hours(self, tmp_path):
        tracker = SnapshotDeltaTracker(hub_path=tmp_path)
        prev = _make_snapshot(timestamp="2026-01-01T00:00:00")
        curr = _make_snapshot(timestamp="2026-01-01T06:00:00")
        delta = tracker.compute_delta(prev, curr)
        assert abs(delta.time_delta_hours - 6.0) < 0.01

    def test_compute_delta_quest_changed_on_title_change(self, tmp_path):
        tracker = SnapshotDeltaTracker(hub_path=tmp_path)
        prev = _make_snapshot(timestamp="2026-01-01T00:00:00", quest_title="Old Quest")
        curr = _make_snapshot(timestamp="2026-01-01T01:00:00", quest_title="New Quest")
        delta = tracker.compute_delta(prev, curr)
        assert delta.quest_changed is True

    def test_compute_delta_quest_not_changed_same(self, tmp_path):
        tracker = SnapshotDeltaTracker(hub_path=tmp_path)
        prev = _make_snapshot(timestamp="2026-01-01T00:00:00")
        curr = _make_snapshot(timestamp="2026-01-01T01:00:00")
        delta = tracker.compute_delta(prev, curr)
        assert delta.quest_changed is False

    def test_compute_delta_import_improvement_insight(self, tmp_path):
        tracker = SnapshotDeltaTracker(hub_path=tmp_path)
        prev = _make_snapshot(timestamp="2026-01-01T00:00:00", import_failures=10)
        curr = _make_snapshot(timestamp="2026-01-01T01:00:00", import_failures=4)
        delta = tracker.compute_delta(prev, curr)
        assert delta.import_failures_delta == -6
        assert any("Import health improved" in i for i in delta.insights)

    def test_compute_delta_stalled_insight(self, tmp_path):
        tracker = SnapshotDeltaTracker(hub_path=tmp_path)
        prev = _make_snapshot(timestamp="2026-01-01T00:00:00", commits_ahead=5)
        curr = _make_snapshot(timestamp="2026-01-02T06:00:00", commits_ahead=5)
        delta = tracker.compute_delta(prev, curr)
        assert any("Stalled" in i for i in delta.insights)

    def test_compute_delta_commit_velocity_insight(self, tmp_path):
        tracker = SnapshotDeltaTracker(hub_path=tmp_path)
        prev = _make_snapshot(timestamp="2026-01-01T00:00:00", commits_ahead=0)
        curr = _make_snapshot(timestamp="2026-01-01T02:00:00", commits_ahead=4)
        delta = tracker.compute_delta(prev, curr)
        assert any("Commit velocity" in i for i in delta.insights)

    def test_compute_delta_agent_activity_delta(self, tmp_path):
        tracker = SnapshotDeltaTracker(hub_path=tmp_path)
        prev = _make_snapshot(
            timestamp="2026-01-01T00:00:00",
            agent_activity={"ollama": 2, "chatdev": 0},
        )
        curr = _make_snapshot(
            timestamp="2026-01-01T01:00:00",
            agent_activity={"ollama": 7, "chatdev": 1},
        )
        delta = tracker.compute_delta(prev, curr)
        assert delta.agent_activity_delta.get("ollama") == 5
        assert delta.agent_activity_delta.get("chatdev") == 1

    def test_get_trend_summary_no_history(self, tmp_path):
        tracker = SnapshotDeltaTracker(hub_path=tmp_path)
        result = tracker.get_trend_summary()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_trend_summary_with_snapshots(self, tmp_path):
        tracker = SnapshotDeltaTracker(hub_path=tmp_path)
        for i in range(3):
            snap = _make_snapshot(
                timestamp=f"2026-01-01T0{i}:00:00",
                commits_ahead=i * 2,
            )
            tracker.save_snapshot(snap)
        result = tracker.get_trend_summary(window_hours=72 * 365)  # large window
        assert any("snapshots" in r.lower() for r in result)

    def test_save_snapshot_appends_to_history(self, tmp_path):
        tracker = SnapshotDeltaTracker(hub_path=tmp_path)
        tracker.save_snapshot(_make_snapshot(timestamp="2026-01-01T00:00:00"))
        tracker.save_snapshot(_make_snapshot(timestamp="2026-01-01T01:00:00"))
        lines = tracker.history_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2

    def test_compute_delta_quest_completed_insight(self, tmp_path):
        tracker = SnapshotDeltaTracker(hub_path=tmp_path)
        prev = _make_snapshot(
            timestamp="2026-01-01T00:00:00",
            quest_status="active",
            quest_title="Big Quest",
        )
        curr = _make_snapshot(
            timestamp="2026-01-01T01:00:00",
            quest_status="completed",
            quest_title="Big Quest",
        )
        delta = tracker.compute_delta(prev, curr)
        assert any("completed" in i for i in delta.insights)


# ===========================================================================
# MetricsCollector
# ===========================================================================

class TestMetricsCollector:
    def test_init_creates_storage_dir(self, tmp_path):
        storage = tmp_path / "metrics"
        MetricsCollector(storage_path=storage)
        assert storage.exists()

    def test_get_current_snapshot_default(self, tmp_path):
        collector = MetricsCollector(storage_path=tmp_path / "m")
        snap = collector.get_current_snapshot()
        assert isinstance(snap, DashboardMetrics)
        assert snap.total_tasks == 0

    @pytest.mark.asyncio
    async def test_record_event_adds_to_buffer(self, tmp_path):
        collector = MetricsCollector(
            storage_path=tmp_path / "m",
            aggregation_interval_minutes=999,  # prevent auto-aggregate
        )
        event = MetricEvent(
            metric_type=MetricType.TASK_COMPLETION,
            timestamp=datetime.now(),
            data={"success": True, "duration_seconds": 5.0, "category": "TEST"},
        )
        await collector.record_event(event)
        assert len(collector.event_buffer) == 1

    @pytest.mark.asyncio
    async def test_record_task_completion(self, tmp_path):
        collector = MetricsCollector(
            storage_path=tmp_path / "m",
            aggregation_interval_minutes=999,
        )
        await collector.record_task_completion(1, True, 10.0, "BUGFIX")
        assert len(collector.event_buffer) == 1
        assert collector.event_buffer[0].metric_type == MetricType.TASK_COMPLETION

    @pytest.mark.asyncio
    async def test_record_pr_created(self, tmp_path):
        collector = MetricsCollector(
            storage_path=tmp_path / "m",
            aggregation_interval_minutes=999,
        )
        await collector.record_pr_created(42, 1, 0.2, "AUTO", "auto_merge")
        assert collector.event_buffer[0].metric_type == MetricType.PR_CREATED
        assert collector.event_buffer[0].pr_number == 42

    @pytest.mark.asyncio
    async def test_record_pr_merged(self, tmp_path):
        collector = MetricsCollector(
            storage_path=tmp_path / "m",
            aggregation_interval_minutes=999,
        )
        await collector.record_pr_merged(42, auto_merged=True, merge_time_hours=1.5)
        assert collector.event_buffer[0].metric_type == MetricType.PR_MERGED

    @pytest.mark.asyncio
    async def test_record_model_invocation(self, tmp_path):
        collector = MetricsCollector(
            storage_path=tmp_path / "m",
            aggregation_interval_minutes=999,
        )
        await collector.record_model_invocation("ollama-llama3", task_id=7)
        assert collector.event_buffer[0].data["model"] == "ollama-llama3"

    @pytest.mark.asyncio
    async def test_record_risk_assessment(self, tmp_path):
        collector = MetricsCollector(
            storage_path=tmp_path / "m",
            aggregation_interval_minutes=999,
        )
        await collector.record_risk_assessment(1, 0.15, "AUTO")
        assert collector.event_buffer[0].metric_type == MetricType.RISK_ASSESSMENT

    @pytest.mark.asyncio
    async def test_aggregate_metrics_task_completions(self, tmp_path):
        collector = MetricsCollector(
            storage_path=tmp_path / "m",
            aggregation_interval_minutes=999,
        )
        await collector.record_task_completion(1, True, 30.0, "TEST")
        await collector.record_task_completion(2, False, 20.0, "BUGFIX")
        snap = await collector.aggregate_metrics()
        assert snap.completed_tasks == 2
        assert snap.failed_tasks == 1

    @pytest.mark.asyncio
    async def test_aggregate_metrics_risk_distribution(self, tmp_path):
        collector = MetricsCollector(
            storage_path=tmp_path / "m",
            aggregation_interval_minutes=999,
        )
        await collector.record_risk_assessment(1, 0.1, "AUTO")
        await collector.record_risk_assessment(2, 0.5, "REVIEW")
        await collector.record_risk_assessment(3, 0.7, "PROPOSAL")
        await collector.record_risk_assessment(4, 0.9, "BLOCKED")
        snap = await collector.aggregate_metrics()
        assert snap.risk_auto_count == 1
        assert snap.risk_review_count == 1
        assert snap.risk_proposal_count == 1
        assert snap.risk_blocked_count == 1

    @pytest.mark.asyncio
    async def test_aggregate_metrics_model_invocations(self, tmp_path):
        collector = MetricsCollector(
            storage_path=tmp_path / "m",
            aggregation_interval_minutes=999,
        )
        await collector.record_model_invocation("ollama-llama3")
        await collector.record_model_invocation("ollama-qwen")
        await collector.record_model_invocation("chatdev-gpt4")
        snap = await collector.aggregate_metrics()
        assert snap.ollama_invocations == 2
        assert snap.chatdev_invocations == 1

    @pytest.mark.asyncio
    async def test_aggregate_metrics_pr_success_rate(self, tmp_path):
        collector = MetricsCollector(
            storage_path=tmp_path / "m",
            aggregation_interval_minutes=999,
        )
        await collector.record_pr_created(1, 1, 0.1, "AUTO", "auto_merge")
        await collector.record_pr_created(2, 2, 0.2, "AUTO", "auto_merge")
        await collector.record_pr_merged(1, True, 0.5)
        snap = await collector.aggregate_metrics()
        assert snap.pr_success_rate == pytest.approx(0.5)

    @pytest.mark.asyncio
    async def test_aggregate_metrics_persists_snapshot(self, tmp_path):
        storage = tmp_path / "m"
        collector = MetricsCollector(storage_path=storage, aggregation_interval_minutes=999)
        await collector.aggregate_metrics()
        files = list(storage.glob("snapshot_*.json"))
        assert len(files) == 1

    @pytest.mark.asyncio
    async def test_aggregate_metrics_category_distribution(self, tmp_path):
        collector = MetricsCollector(
            storage_path=tmp_path / "m",
            aggregation_interval_minutes=999,
        )
        await collector.record_task_completion(1, True, 5.0, "TEST")
        await collector.record_task_completion(2, True, 5.0, "TEST")
        await collector.record_task_completion(3, True, 5.0, "BUGFIX")
        snap = await collector.aggregate_metrics()
        assert snap.category_distribution.get("TEST") == 2
        assert snap.category_distribution.get("BUGFIX") == 1

    def test_generate_text_dashboard_no_data(self, tmp_path):
        collector = MetricsCollector(storage_path=tmp_path / "m")
        dashboard = collector.generate_text_dashboard()
        assert "NuSyQ Autonomy Dashboard" in dashboard
        assert "Task Queue Status" in dashboard

    def test_generate_text_dashboard_contains_pr_section(self, tmp_path):
        collector = MetricsCollector(storage_path=tmp_path / "m")
        dashboard = collector.generate_text_dashboard()
        assert "PR Metrics" in dashboard

    def test_generate_text_dashboard_contains_model_section(self, tmp_path):
        collector = MetricsCollector(storage_path=tmp_path / "m")
        dashboard = collector.generate_text_dashboard()
        assert "Model Utilization" in dashboard

    def test_generate_text_dashboard_contains_advanced_ai(self, tmp_path):
        collector = MetricsCollector(storage_path=tmp_path / "m")
        dashboard = collector.generate_text_dashboard()
        assert "Advanced AI" in dashboard

    @pytest.mark.asyncio
    async def test_get_historical_snapshots_empty(self, tmp_path):
        collector = MetricsCollector(storage_path=tmp_path / "m")
        result = await collector.get_historical_snapshots(hours=24)
        assert isinstance(result, list)

    def test_apply_advanced_ai_intelligence_no_files(self, tmp_path):
        """Should not raise when report files are absent."""
        collector = MetricsCollector(storage_path=tmp_path / "m")
        snap = DashboardMetrics()
        collector._apply_advanced_ai_intelligence(snap)
        assert snap.advanced_ai_ready_count == 0

    def test_apply_advanced_ai_intelligence_with_ai_status(self, tmp_path):
        storage = tmp_path / "m"
        collector = MetricsCollector(storage_path=storage)
        reports = storage.parent / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        ai_status = {
            "capability_intelligence": {
                "advanced_ai_readiness": {
                    "capabilities": {
                        "cap1": {"status": "ready"},
                        "cap2": {"status": "partial"},
                        "cap3": {"status": "missing"},
                    }
                }
            }
        }
        collector.ai_status_report.parent.mkdir(parents=True, exist_ok=True)
        collector.ai_status_report.write_text(json.dumps(ai_status), encoding="utf-8")
        snap = DashboardMetrics()
        collector._apply_advanced_ai_intelligence(snap)
        assert snap.advanced_ai_ready_count == 1
        assert snap.advanced_ai_partial_count == 1
        assert snap.advanced_ai_missing_count == 1

    def test_apply_advanced_ai_intelligence_with_meta_learning(self, tmp_path):
        storage = tmp_path / "m"
        collector = MetricsCollector(storage_path=storage)
        meta = {
            "snapshot": {
                "total_events": 100,
                "error_events": 5,
                "routed_events": 90,
                "max_recursion_depth": 3,
            }
        }
        collector.meta_learning_report.parent.mkdir(parents=True, exist_ok=True)
        collector.meta_learning_report.write_text(json.dumps(meta), encoding="utf-8")
        snap = DashboardMetrics()
        collector._apply_advanced_ai_intelligence(snap)
        assert snap.meta_learning_total_events == 100
        assert snap.meta_learning_error_events == 5
        assert snap.meta_learning_routed_events == 90
        assert snap.meta_learning_max_recursion_depth == 3


# ===========================================================================
# MetricType Enum
# ===========================================================================

class TestMetricTypeEnum:
    def test_all_expected_values_exist(self):
        expected = {
            "TASK_COMPLETION", "PR_CREATED", "PR_MERGED", "PR_REJECTED",
            "RISK_ASSESSMENT", "MODEL_INVOCATION", "SCHEDULER_DECISION", "SYSTEM_HEALTH",
        }
        actual = {m.name for m in MetricType}
        assert expected == actual


# ===========================================================================
# get_metrics_collector (global singleton)
# ===========================================================================

class TestGetMetricsCollector:
    def test_returns_metrics_collector_instance(self):
        import src.observability.autonomy_dashboard as dash_mod
        # Reset singleton for isolation
        dash_mod._collector = None
        collector = get_metrics_collector()
        assert isinstance(collector, MetricsCollector)
        dash_mod._collector = None  # cleanup
