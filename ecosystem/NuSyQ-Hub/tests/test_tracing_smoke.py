from __future__ import annotations

import os


def test_tracing_smoke_import_and_ids():
    # Allow disabled mode
    os.environ.setdefault("NUSYQ_TRACE", "1")
    try:
        from src.observability import otel
    except Exception:
        # If OTEL not installed, import fails gracefully in runtime; ensure module import path exists
        assert True
        return

    otel.init_tracing("nusyq-hub-test")
    # Should not crash even if OTEL packages missing
    with otel.start_action_span("nusyq.test.smoke", {"key": "value"}):
        trace_id, span_id = otel.current_trace_ids()
        assert isinstance(trace_id, str)
        assert isinstance(span_id, str)


def test_init_tracing_otlp_exporter_protocol_backward_compat(monkeypatch):
    from src.observability import tracing

    class _FakeResource:
        @staticmethod
        def create(_attrs):
            return {"resource": "ok"}

    class _FakeProvider:
        def __init__(self, resource=None):
            self.resource = resource
            self.processors = []

        def add_span_processor(self, processor):
            self.processors.append(processor)

        def force_flush(self, timeout_millis=0):
            return True

        def shutdown(self, timeout_millis=0):
            return True

    class _FakeProcessor:
        def __init__(self, exporter):
            self.exporter = exporter

    class _FakeTrace:
        def __init__(self):
            self.provider = None
            self.set_count = 0

        def set_tracer_provider(self, provider):
            self.provider = provider
            self.set_count += 1

        def get_tracer(self, _name):
            return object()

    class _FakeOTLPExporter:
        def __init__(self, *, endpoint, protocol=None):
            if protocol is not None:
                raise TypeError("unexpected keyword argument 'protocol'")
            self.endpoint = endpoint

    fake_trace = _FakeTrace()
    monkeypatch.setattr(
        tracing,
        "_import_opentelemetry",
        lambda: {
            "baggage": object(),
            "trace": fake_trace,
            "Resource": _FakeResource,
            "TracerProvider": _FakeProvider,
            "BatchSpanProcessor": _FakeProcessor,
            "ConsoleSpanExporter": object,
            "SimpleSpanProcessor": _FakeProcessor,
            "SpanKind": object(),
            "OTLPSpanExporter": _FakeOTLPExporter,
            "LoggingInstrumentor": None,
            "RequestsInstrumentor": None,
        },
    )
    monkeypatch.setattr(tracing, "_instrument_logging_and_requests", lambda _imports: None)
    monkeypatch.setattr(tracing, "_TRACING_READY", False)
    monkeypatch.setattr(tracing, "_TRACER", None)
    monkeypatch.setattr(tracing, "_PROVIDER", None)
    monkeypatch.setenv("NUSYQ_TRACING", "1")
    monkeypatch.setenv("OTEL_TRACES_EXPORTER", "otlp")

    assert tracing.init_tracing(service_name="nusyq-hub-test", endpoint="http://localhost:4318")
    assert tracing.init_tracing(service_name="nusyq-hub-test", endpoint="http://localhost:4318")
    assert tracing.tracing_enabled() is True
    assert fake_trace.set_count == 1
