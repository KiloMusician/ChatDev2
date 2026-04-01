"""Tests for src/observability/lightweight_tracer.py

This module tests the Lightweight Observability Tracer.

Coverage Target: 70%+
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

# =============================================================================
# Module Import Tests
# =============================================================================


class TestModuleImports:
    """Test module-level imports."""

    def test_import_span(self):
        """Test Span dataclass can be imported."""
        from src.observability.lightweight_tracer import Span

        assert Span is not None

    def test_import_lightweight_tracer(self):
        """Test LightweightTracer class can be imported."""
        from src.observability.lightweight_tracer import LightweightTracer

        assert LightweightTracer is not None

    def test_import_get_tracer(self):
        """Test get_tracer function can be imported."""
        from src.observability.lightweight_tracer import get_tracer

        assert get_tracer is not None


# =============================================================================
# Span Tests
# =============================================================================


class TestSpan:
    """Test Span dataclass."""

    def test_create_basic_span(self):
        """Test creating a basic span."""
        from src.observability.lightweight_tracer import Span

        span = Span(
            span_id="span-123",
            trace_id="trace-456",
            name="test_operation",
            start_time=1000.0,
        )

        assert span.span_id == "span-123"
        assert span.trace_id == "trace-456"
        assert span.name == "test_operation"
        assert span.start_time == 1000.0
        assert span.end_time is None
        assert span.parent_id is None

    def test_span_duration_none_without_end(self):
        """Test duration_ms is None without end_time."""
        from src.observability.lightweight_tracer import Span

        span = Span(
            span_id="span-1",
            trace_id="trace-1",
            name="op",
            start_time=1000.0,
        )

        assert span.duration_ms is None

    def test_span_duration_calculated(self):
        """Test duration_ms is calculated correctly."""
        from src.observability.lightweight_tracer import Span

        span = Span(
            span_id="span-1",
            trace_id="trace-1",
            name="op",
            start_time=1000.0,
            end_time=1001.5,
        )

        # 1.5 seconds = 1500 ms
        assert span.duration_ms == 1500.0

    def test_span_add_event(self):
        """Test adding event to span."""
        from src.observability.lightweight_tracer import Span

        span = Span(
            span_id="span-1",
            trace_id="trace-1",
            name="op",
            start_time=1000.0,
        )

        span.add_event("test_event", {"key": "value"})

        assert len(span.events) == 1
        assert span.events[0]["name"] == "test_event"
        assert span.events[0]["attributes"]["key"] == "value"

    def test_span_add_event_without_attributes(self):
        """Test adding event without attributes."""
        from src.observability.lightweight_tracer import Span

        span = Span(
            span_id="span-1",
            trace_id="trace-1",
            name="op",
            start_time=1000.0,
        )

        span.add_event("simple_event")

        assert len(span.events) == 1
        assert span.events[0]["attributes"] == {}

    def test_span_to_dict(self):
        """Test span serialization to dict."""
        from src.observability.lightweight_tracer import Span

        span = Span(
            span_id="span-1",
            trace_id="trace-1",
            name="op",
            start_time=1000.0,
            end_time=1002.0,
        )

        result = span.to_dict()

        assert result["span_id"] == "span-1"
        assert result["trace_id"] == "trace-1"
        assert result["name"] == "op"
        assert result["duration_ms"] == 2000.0


# =============================================================================
# LightweightTracer Initialization Tests
# =============================================================================


class TestLightweightTracerInit:
    """Test LightweightTracer initialization."""

    def test_init_default_output_dir(self, tmp_path):
        """Test initializing with default output dir."""
        from src.observability.lightweight_tracer import LightweightTracer

        with patch.object(Path, "mkdir"):
            tracer = LightweightTracer()

        assert tracer.output_dir == Path("logs/traces")

    def test_init_custom_output_dir(self, tmp_path):
        """Test initializing with custom output dir."""
        from src.observability.lightweight_tracer import LightweightTracer

        output_dir = tmp_path / "custom_traces"
        tracer = LightweightTracer(output_dir=output_dir)

        assert tracer.output_dir == output_dir
        assert output_dir.exists()

    def test_init_creates_output_dir(self, tmp_path):
        """Test that init creates output directory."""
        from src.observability.lightweight_tracer import LightweightTracer

        output_dir = tmp_path / "traces"
        LightweightTracer(output_dir=output_dir)

        assert output_dir.exists()


# =============================================================================
# Trace Lifecycle Tests
# =============================================================================


class TestTracerLifecycle:
    """Test trace lifecycle operations."""

    def test_start_trace(self, tmp_path):
        """Test starting a trace."""
        from src.observability.lightweight_tracer import LightweightTracer

        tracer = LightweightTracer(output_dir=tmp_path)
        trace_id = tracer.start_trace("test_operation")

        assert trace_id is not None
        assert len(trace_id) == 36  # UUID format

    def test_start_trace_creates_span(self, tmp_path):
        """Test that starting a trace creates initial span."""
        from src.observability.lightweight_tracer import LightweightTracer

        tracer = LightweightTracer(output_dir=tmp_path)
        trace_id = tracer.start_trace("test_operation")

        # Should have one span
        assert len(tracer.spans) == 1
        span = next(iter(tracer.spans.values()))
        assert span.trace_id == trace_id
        assert span.name == "test_operation"

    def test_start_span_child(self, tmp_path):
        """Test starting a child span."""
        from src.observability.lightweight_tracer import LightweightTracer

        tracer = LightweightTracer(output_dir=tmp_path)
        trace_id = tracer.start_trace("parent_op")

        child_span_id = tracer.start_span(trace_id, "child_op", {"key": "value"})

        assert child_span_id is not None
        assert len(tracer.spans) == 2
        child_span = tracer.spans[child_span_id]
        assert child_span.name == "child_op"
        assert child_span.parent_id is not None
        assert child_span.attributes["key"] == "value"

    def test_end_span(self, tmp_path):
        """Test ending a span."""
        from src.observability.lightweight_tracer import LightweightTracer

        tracer = LightweightTracer(output_dir=tmp_path)
        trace_id = tracer.start_trace("op")
        span_id = tracer.start_span(trace_id, "child")

        tracer.end_span(span_id)

        assert tracer.spans[span_id].end_time is not None

    def test_end_span_nonexistent(self, tmp_path):
        """Test ending non-existent span does not error."""
        from src.observability.lightweight_tracer import LightweightTracer

        tracer = LightweightTracer(output_dir=tmp_path)
        tracer.end_span("fake-span-id")  # Should not raise


# =============================================================================
# Span Attribute Tests
# =============================================================================


class TestSpanAttributes:
    """Test span attribute operations."""

    def test_add_event_to_span(self, tmp_path):
        """Test adding event to span."""
        from src.observability.lightweight_tracer import LightweightTracer

        tracer = LightweightTracer(output_dir=tmp_path)
        tracer.start_trace("op")
        span_id = next(iter(tracer.spans.keys()))

        tracer.add_event(span_id, "test_event", {"data": "value"})

        assert len(tracer.spans[span_id].events) == 1

    def test_add_event_nonexistent_span(self, tmp_path):
        """Test adding event to non-existent span."""
        from src.observability.lightweight_tracer import LightweightTracer

        tracer = LightweightTracer(output_dir=tmp_path)
        tracer.add_event("fake-span", "event")  # Should not raise

    def test_set_attribute(self, tmp_path):
        """Test setting attribute on span."""
        from src.observability.lightweight_tracer import LightweightTracer

        tracer = LightweightTracer(output_dir=tmp_path)
        tracer.start_trace("op")
        span_id = next(iter(tracer.spans.keys()))

        tracer.set_attribute(span_id, "test_key", "test_value")

        assert tracer.spans[span_id].attributes["test_key"] == "test_value"

    def test_set_attribute_nonexistent(self, tmp_path):
        """Test setting attribute on non-existent span."""
        from src.observability.lightweight_tracer import LightweightTracer

        tracer = LightweightTracer(output_dir=tmp_path)
        tracer.set_attribute("fake-span", "key", "value")  # Should not raise


# =============================================================================
# End Trace Tests
# =============================================================================


class TestEndTrace:
    """Test end_trace operations."""

    def test_end_trace_writes_file(self, tmp_path):
        """Test that ending trace writes JSON file."""
        from src.observability.lightweight_tracer import LightweightTracer

        tracer = LightweightTracer(output_dir=tmp_path)
        trace_id = tracer.start_trace("test_op")

        filepath = tracer.end_trace(trace_id)

        assert filepath.exists()
        assert filepath.suffix == ".json"

    def test_end_trace_cleans_spans(self, tmp_path):
        """Test that ending trace cleans up spans."""
        from src.observability.lightweight_tracer import LightweightTracer

        tracer = LightweightTracer(output_dir=tmp_path)
        trace_id = tracer.start_trace("op")
        tracer.start_span(trace_id, "child")

        tracer.end_trace(trace_id)

        assert len(tracer.spans) == 0
        assert trace_id not in tracer.active_spans

    def test_end_trace_valid_json(self, tmp_path):
        """Test that trace file is valid JSON."""
        from src.observability.lightweight_tracer import LightweightTracer

        tracer = LightweightTracer(output_dir=tmp_path)
        trace_id = tracer.start_trace("op")

        filepath = tracer.end_trace(trace_id)

        with open(filepath) as f:
            data = json.load(f)

        assert data["trace_id"] == trace_id
        assert "timestamp" in data
        assert "spans" in data
        assert "summary" in data

    def test_end_trace_with_child_spans(self, tmp_path):
        """Test ending trace with multiple spans."""
        from src.observability.lightweight_tracer import LightweightTracer

        tracer = LightweightTracer(output_dir=tmp_path)
        trace_id = tracer.start_trace("parent")
        tracer.start_span(trace_id, "child1")
        tracer.start_span(trace_id, "child2")

        filepath = tracer.end_trace(trace_id)

        with open(filepath) as f:
            data = json.load(f)

        assert len(data["spans"]) == 3


# =============================================================================
# Summary Tests
# =============================================================================


class TestBuildSummary:
    """Test _build_summary method."""

    def test_summary_empty_spans(self, tmp_path):
        """Test summary with empty spans."""
        from src.observability.lightweight_tracer import LightweightTracer

        tracer = LightweightTracer(output_dir=tmp_path)
        result = tracer._build_summary([])

        assert result == {}

    def test_summary_with_spans(self, tmp_path):
        """Test summary with spans."""
        from src.observability.lightweight_tracer import LightweightTracer, Span

        tracer = LightweightTracer(output_dir=tmp_path)
        spans = [
            Span("s1", "t1", "op_a", 0, 0.1),
            Span("s2", "t1", "op_b", 0, 0.2),
            Span("s3", "t1", "op_a", 0, 0.15),
        ]

        result = tracer._build_summary(spans)

        assert result["span_count"] == 3
        assert "op_a" in result["operations"]
        assert "op_b" in result["operations"]
        assert result["operations"]["op_a"]["count"] == 2


# =============================================================================
# Context Manager Tests
# =============================================================================


class TestContextManagers:
    """Test context managers."""

    def test_trace_context_manager(self, tmp_path, capsys):
        """Test trace context manager."""
        from src.observability.lightweight_tracer import LightweightTracer

        tracer = LightweightTracer(output_dir=tmp_path)

        with tracer.trace("test_op") as trace_id:
            assert trace_id is not None

        # Should print trace saved message
        captured = capsys.readouterr()
        assert "Trace saved" in captured.out

    def test_span_context_manager(self, tmp_path):
        """Test span context manager."""
        from src.observability.lightweight_tracer import LightweightTracer

        tracer = LightweightTracer(output_dir=tmp_path)
        trace_id = tracer.start_trace("parent")

        with tracer.span(trace_id, "child_op", key="value") as span_id:
            assert span_id is not None
            assert tracer.spans[span_id].attributes["key"] == "value"

        # Span should be ended
        assert tracer.spans[span_id].end_time is not None


# =============================================================================
# Obsidian Note Generation Tests
# =============================================================================


class TestObsidianNotes:
    """Test Obsidian note generation."""

    def test_generate_obsidian_note(self, tmp_path):
        """Test generating Obsidian note from trace."""
        from src.observability.lightweight_tracer import LightweightTracer

        tracer = LightweightTracer(output_dir=tmp_path)
        trace_id = tracer.start_trace("test_op")
        trace_file = tracer.end_trace(trace_id)

        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        note_path = tracer.generate_obsidian_note(trace_file, vault_path)

        assert note_path.exists()
        assert note_path.suffix == ".md"

    def test_obsidian_note_content(self, tmp_path):
        """Test Obsidian note contains expected content."""
        from src.observability.lightweight_tracer import LightweightTracer

        tracer = LightweightTracer(output_dir=tmp_path)
        trace_id = tracer.start_trace("test_op")
        trace_file = tracer.end_trace(trace_id)

        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        note_path = tracer.generate_obsidian_note(trace_file, vault_path)
        content = note_path.read_text()

        assert "# Trace:" in content
        assert "Total Duration:" in content
        assert "Operations" in content
        assert "Span Timeline" in content

    def test_obsidian_creates_traces_dir(self, tmp_path):
        """Test that Obsidian note creates Traces directory."""
        from src.observability.lightweight_tracer import LightweightTracer

        tracer = LightweightTracer(output_dir=tmp_path)
        trace_id = tracer.start_trace("op")
        trace_file = tracer.end_trace(trace_id)

        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        tracer.generate_obsidian_note(trace_file, vault_path)

        assert (vault_path / "Traces").exists()


# =============================================================================
# get_tracer Tests
# =============================================================================


class TestGetTracer:
    """Test get_tracer function."""

    def test_get_tracer_returns_instance(self):
        """Test get_tracer returns tracer instance."""
        from src.observability.lightweight_tracer import get_tracer

        # Clear lru_cache to prevent state leakage
        get_tracer.cache_clear()

        tracer = get_tracer()

        from src.observability.lightweight_tracer import LightweightTracer

        assert isinstance(tracer, LightweightTracer)

    def test_get_tracer_cached(self):
        """Test get_tracer returns same instance."""
        from src.observability.lightweight_tracer import get_tracer

        get_tracer.cache_clear()

        tracer1 = get_tracer()
        tracer2 = get_tracer()

        assert tracer1 is tracer2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
