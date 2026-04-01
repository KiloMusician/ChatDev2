import importlib

import telemetry.tracing_setup as tracing


def test_initialize_tracing_no_throw():
    # Should not throw even if OpenTelemetry is not installed
    _ = tracing.initialize_tracing(service_name="unit_test_tracing")
    # tracer may be noop or an opentelemetry tracer; ensure API surface exists
    assert hasattr(tracing, "start_span")
    assert isinstance(tracing.is_tracing_enabled(), bool)
    # tracer should be usable via context manager; ensure start_span works
    with tracing.start_span("test_span", {"a": 1}) as span:
        # if tracing disabled, span may be None; ensure no error
        if span is not None:
            assert hasattr(span, "set_attribute")


def test_nusyq_chatdev_imports_without_crash():
    # Import nusyq_chatdev and ensure module attribute exists
    import integrations.nusyq_chatdev as nc  # noqa: F401
    importlib.reload(nc)
    assert hasattr(nc, "run_chatdev_with_ollama")


def test_visualizer_imports_without_crash():
    from ChatDev.visualizer import app as visualizer_app  # noqa: F401
    importlib.reload(visualizer_app)
    assert hasattr(visualizer_app, "app")


def test_get_tracer_and_env_init_no_errors(monkeypatch):
    # get_tracer works whether or not OTEL is installed
    t = tracing.get_tracer("test_tracer")
    assert hasattr(t, "start_as_current_span")

    # initialize_tracing_from_env respects OTEL_ENABLED
    monkeypatch.setenv("OTEL_ENABLED", "0")
    t2 = tracing.initialize_tracing_from_env("env_test")
    assert hasattr(t2, "start_as_current_span")
    monkeypatch.delenv("OTEL_ENABLED", raising=False)


def test_instrument_fastapi_no_throw():
    # Should not throw if FastAPI not installed; simply call safely
    tracing.instrument_fastapi(None)


def test_instrument_flask_no_throw():
    # Should not throw if Flask not installed; create a dummy app
    class DummyApp:
        pass

    tracing.instrument_flask(DummyApp())


def test_instrument_requests_no_throw():
    # Should not throw if requests instrumentation is not available
    tracing.instrument_requests()


def test_get_exporter_info():
    info = tracing.get_exporter_info()
    # If tracing not installed we get None; otherwise expect type key
    if info is not None:
        assert isinstance(info, dict) and "type" in info


def test_tracing_status_monotonic():
    st = tracing.tracing_status()
    assert isinstance(st, dict)
    assert "installed" in st and "tracer" in st and "exporter" in st
