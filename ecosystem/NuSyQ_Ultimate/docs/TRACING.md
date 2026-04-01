# Tracing (OpenTelemetry) Setup for NuSyQ

This document describes the lightweight tracing setup provided in `tracing_setup.py` for NuSyQ.

Key features
- Safe no-op behavior when OpenTelemetry is not installed.
- Environment aware initialization: `initialize_tracing_from_env()` reads OTEL_ENABLED and OTEL_SERVICE_NAME.
- Convenience helpers: `get_tracer`, `start_span` context manager.
- FastAPI, Flask, and requests optional instrumentation helpers.

Usage
1. Initialization (automatic):

```python
import tracing_setup as tracing
tracer = tracing.initialize_tracing(service_name="my_service")
```

2. Environment driven init:

```python
tracer = tracing.initialize_tracing_from_env()
# Set OTEL_ENABLED=0 to disable tracing
```

3. Getting a tracer (safe fallback):

```python
tracer = tracing.get_tracer("my_service")
with tracing.start_span("my_op") as span:
    # safe even when OTEL not installed
    if span:
        span.set_attribute("example", True)
```

4. Instrumenting frameworks:

```python
tracing.instrument_requests()  # instrument requests library
tracing.instrument_flask(app)  # instrument Flask apps
tracing.instrument_fastapi(app) # instrument FastAPI apps
```

Notes & Best Practices
- Calls to `instrument_*` are best effort: they won't crash if the optional instrumentation packages are not available.
- Environment variables:
  - `OTEL_ENABLED`: set to `0`, `false`, or `no` to disable tracing entirely.
  - `OTEL_SERVICE_NAME`: to set (override) service name.
  - `OTEL_EXPORTER_OTLP_ENDPOINT`: the endpoint for the OTLP trace exporter.

Why this approach
- Keeping tracing optional (no-op fallback) prevents tests and consumer scripts from needing the OTEL packages installed while still allowing local/CI instrumentation.

If you'd like a sample configuration for running with an OTLP collector, ask me and I can add an example `docker-compose` snippet.

Quick example Docker Compose (OTel Collector):

```yaml
version: '3.8'
services:
    otel-collector:
        image: otel/opentelemetry-collector:latest
        ports:
            - '4318:4318'
        command: ["--config=/etc/otel-collector-config.yaml"]
        volumes:
            - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml

# Set env var before running your application to send traces to collector
# OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```
# Tracing (OpenTelemetry) for NuSyQ

This repository includes an optional, developer-friendly tracing setup using OpenTelemetry.

Key features
- Lightweight `tracing_setup.py` helper with graceful no-op fallback when OpenTelemetry is not installed.
- Request and Flask instrumentation helpers.
- Minimal, backward-compatible default: Console exporter will be used if no OTLP endpoint is configured.

How to enable tracing
1. Install OpenTelemetry packages and the OTLP exporter for your preferred backend.
   Example (pip):

   pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-instrumentation-requests opentelemetry-instrumentation-flask

2. Set environment variable for OTLP endpoint (optional):

   export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318/v1/traces"

3. Run the instrumented apps as normal; the code will start tracing if OpenTelemetry packages are installed.

Developer usage
- Initialize tracing in your Python script:

    import tracing_setup as tracing
    tracing.initialize_tracing(service_name="nusyq_chatdev")
    tracing.instrument_requests()

- Wrap key sections in spans:

    with tracing.start_span("my_operation", {"task": "build"}):
        ...

Notes
- Tracing is optional. If OpenTelemetry SDK is not installed, `tracing_setup` is a no-op and will not affect behavior.
- This setup uses a console exporter as default for local development. Configure an OTLP endpoint to export to a tracing backend.
