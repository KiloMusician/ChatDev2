

import telemetry.tracing_setup as ts


def test_tracing_status_reports_installed_flag(monkeypatch):
    # Save original
    original_state = ts._OTEL_AVAILABLE
    try:
        monkeypatch.setattr(ts, "_OTEL_AVAILABLE", False)
        s = ts.tracing_status()
        assert s["installed"] is False

        monkeypatch.setattr(ts, "_OTEL_AVAILABLE", True)
        s = ts.tracing_status()
        assert s["installed"] is True
    finally:
        monkeypatch.setattr(ts, "_OTEL_AVAILABLE", original_state)


def test_initialize_and_start_span_noop(monkeypatch):
    # Force no OTEL environment
    original_state = ts._OTEL_AVAILABLE
    try:
        monkeypatch.setattr(ts, "_OTEL_AVAILABLE", False)
        tracer = ts.initialize_tracing(service_name="testsvc")
        assert hasattr(tracer, "start_as_current_span")

        # Test context manager yields an object with set_attribute
        with ts.start_span("op", {"k": "v"}) as span:
            assert span is not None
            assert hasattr(span, "set_attribute")
            span.set_attribute("x", 1)
    finally:
        monkeypatch.setattr(ts, "_OTEL_AVAILABLE", original_state)


def test_get_exporter_info_otlp_and_console(monkeypatch):
    # Clear env
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", raising=False)
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)

    # If no endpoint set, and available mocked True => console
    original_state = ts._OTEL_AVAILABLE
    try:
        monkeypatch.setattr(ts, "_OTEL_AVAILABLE", True)
        info = ts.get_exporter_info()
        assert info is not None
        assert info["type"] in ("console", "otlp")

        # If we set an OTLP endpoint, expect otlp
        monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://example.com")
        info = ts.get_exporter_info()
        assert info is not None
        assert info["type"] == "otlp"
        assert "endpoint" in info
    finally:
        monkeypatch.setattr(ts, "_OTEL_AVAILABLE", original_state)
        monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)


def test_get_tracer_and_is_tracing_enabled(monkeypatch):
    original_state = ts._OTEL_AVAILABLE
    try:
        monkeypatch.setattr(ts, "_OTEL_AVAILABLE", False)
        assert ts.is_tracing_enabled() is False
        t = ts.get_tracer("foo")
        assert hasattr(t, "start_as_current_span")

        monkeypatch.setattr(ts, "_OTEL_AVAILABLE", True)
        # if otel is installed in the environment, get_tracer should return
        # a tracer object; otherwise, it still should work (we're not asserting
        # type here to stay flexible in environment)
        tr = ts.get_tracer("bar")
        assert hasattr(tr, "start_as_current_span")
    finally:
        monkeypatch.setattr(ts, "_OTEL_AVAILABLE", original_state)
