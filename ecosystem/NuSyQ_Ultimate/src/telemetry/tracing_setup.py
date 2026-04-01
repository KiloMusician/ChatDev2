"""
Lightweight tracing setup for NuSyQ (OpenTelemetry-based
with graceful fallback).


Usage (safe even if OpenTelemetry isn't installed):

    import tracing_setup as tracing
    tracer = tracing.initialize_tracing(service_name="nusyq_chatdev")
    tracing.instrument_requests()
    with tracing.start_span("my_operation", {"key": "value"}):
        ...

If OpenTelemetry packages are not available, all functions become no-ops.
"""

from __future__ import annotations

import contextlib
import json
import os
from typing import Any, ContextManager, Dict, Optional

_OTEL_AVAILABLE = True

try:
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )

    try:
        # Prefer HTTP/OTLP exporter
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
    except ImportError:  # pragma: no cover - exporter may be missing
        OTLPSpanExporter = None  # type: ignore[assignment]

    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
    except ImportError:  # pragma: no cover - optional
        RequestsInstrumentor = None  # type: ignore[assignment]

    try:
        from opentelemetry.instrumentation.flask import (
            FlaskInstrumentor,  # type: ignore[reportMissingImports]
        )
    except ImportError:  # pragma: no cover - optional
        FlaskInstrumentor = None  # type: ignore[assignment]
except ImportError:  # OpenTelemetry not installed
    _OTEL_AVAILABLE = False


class _NoopSpan:
    """Very small no-op span compatible with opentelemetry.span interface."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def set_attribute(self, _key, _value) -> None:  # pragma: no cover
        return None


class _NoopTracer:
    """No-op tracer that matches minimal interface used by
    the rest of the app.
    """

    def __init__(self, name: str = "noop") -> None:
        self.name = name

    def start_as_current_span(
        self, _name: str, *_args, **_kwargs
    ) -> ContextManager[_NoopSpan]:
        return _NoopSpan()


def _get_default_exporter():
    """Choose an exporter based on environment or fall back to console."""
    if not _OTEL_AVAILABLE:
        return None

    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") or os.getenv(
        "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"
    )
    if otlp_endpoint and "v1/traces" not in otlp_endpoint:
        # Normalize typical endpoint to the HTTP traces path
        otlp_endpoint = otlp_endpoint.rstrip("/") + "/v1/traces"

    if otlp_endpoint and OTLPSpanExporter is not None:
        return OTLPSpanExporter(endpoint=otlp_endpoint)

    # Default to console exporter for local development
    return ConsoleSpanExporter()


def get_exporter_info():
    """Return lightweight information about the current default exporter.

    Returns a dict like {"type": "console"} or
    {"type": "otlp", "endpoint": "..."}
    or None if tracing/OTEL is not available.
    """
    if not _OTEL_AVAILABLE:
        return None
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") or os.getenv(
        "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"
    )
    if otlp_endpoint:
        if "v1/traces" not in otlp_endpoint:
            otlp_endpoint = otlp_endpoint.rstrip("/") + "/v1/traces"
        return {"type": "otlp", "endpoint": otlp_endpoint}
    return {"type": "console"}


def tracing_status():
    """Return a small status dictionary describing the tracing environment.

    Useful for health checks or debugging.
    """
    status = {
        "installed": _OTEL_AVAILABLE,
        "exporter": get_exporter_info(),
        "tracer": "otel" if _OTEL_AVAILABLE else "noop",
    }
    return status


def initialize_tracing(service_name: str = "nusyq"):
    """Initialize tracing provider and exporter.

    Safe to call multiple times.
    """
    if not _OTEL_AVAILABLE:  # no-op fallback
        return _NoopTracer(service_name)

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    exporter = _get_default_exporter()
    if exporter is not None:
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)

    try:
        trace.set_tracer_provider(provider)
        return trace.get_tracer(service_name)
    except (NameError, AttributeError, RuntimeError):
        return _NoopTracer(service_name)


def instrument_requests() -> None:
    if _OTEL_AVAILABLE and RequestsInstrumentor:
        try:
            RequestsInstrumentor().instrument()
        except RuntimeError:
            # Some instrumentors may raise runtime errors if used in a
            # non-supported environment; best-effort, ignore.
            pass


def instrument_flask(app) -> None:
    if _OTEL_AVAILABLE and FlaskInstrumentor:
        try:
            FlaskInstrumentor().instrument_app(app)
        except RuntimeError:
            # best-effort
            pass


def instrument_fastapi(app) -> None:
    """Instrument a FastAPI application if OpenTelemetry is available.

    This function attempts to import the FastAPI instrumentor lazily so
    instrumentation is optional.
    """
    if not _OTEL_AVAILABLE:
        return
    try:
        from opentelemetry.instrumentation.fastapi import (
            FastAPIInstrumentor,  # type: ignore[reportMissingImports]
        )

        FastAPIInstrumentor().instrument_app(app)
    except ImportError:
        # optional; package not installed
        return
    except RuntimeError:
        # best-effort: ignore instrumentation errors
        return


def is_tracing_enabled() -> bool:
    """Return True if OTEL packages are available and we can export traces."""
    return _OTEL_AVAILABLE


def get_tracer(service_name: str = "nusyq"):
    """Return an OpenTelemetry tracer or a no-op tracer fallback."""
    if _OTEL_AVAILABLE:
        try:
            return trace.get_tracer(service_name)
        except (NameError, AttributeError, RuntimeError):
            return _NoopTracer(service_name)
    return _NoopTracer(service_name)


def initialize_tracing_from_env(service_name: Optional[str] = None):
    """Initialize tracing if env permits.

    Respects the following env vars:
    - OTEL_ENABLED: if '0' or 'false' (case-insensitive), disable tracing
    - OTEL_SERVICE_NAME: service name override (fallback is provided)
    - OTEL_EXPORTER_OTLP_ENDPOINT: traces endpoint used by exporter
    """
    enabled_env = os.getenv("OTEL_ENABLED", "1").lower()
    if enabled_env in ("0", "false", "no"):
        return _NoopTracer(service_name or "nusyq")
    svc = service_name or os.getenv("OTEL_SERVICE_NAME") or "nusyq"
    return initialize_tracing(svc)


@contextlib.contextmanager
def start_span(name: str, attributes: Optional[Dict[str, Any]] = None):
    """Start a span as context manager; no-op if OTEL unavailable."""
    if not _OTEL_AVAILABLE:
        span = _NoopSpan()
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, v)
        yield span
        return

    tracer = get_tracer("nusyq")
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for k, v in attributes.items():
                try:
                    span.set_attribute(k, v)  # type: ignore[attr-defined]
                except (TypeError, ValueError, AttributeError):
                    # Best-effort; ignore invalid attribute types
                    pass
        yield span


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Tracing setup and status utility")
    parser.add_argument("--status", action="store_true", help="Print tracing status")
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize tracing based on env vars (nonblocking)",
    )
    parser.add_argument(
        "--service", default="nusyq", help="Service name when initializing tracing"
    )
    args = parser.parse_args()

    if args.status:
        print(json.dumps(tracing_status(), indent=2))
    if args.init:
        tracer = initialize_tracing_from_env(args.service)
        print(f"initialized tracer: {type(tracer).__name__}")
