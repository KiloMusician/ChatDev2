"""Centralized tracing utilities for NuSyQ-Hub.

Design goals:
- Graceful degradation when OpenTelemetry is missing.
- Environment-driven configuration with safe defaults.
- Lightweight, dependency-free interface for spans and correlation IDs.
"""

# mypy: disable-error-code=import

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger(__name__)

_TRACING_READY: bool = False
_OTEL_AVAILABLE: bool = False
_TRACER: Any = None
_PROVIDER: Any = None
_LOGGING_INSTRUMENTED: bool = False
_REQUESTS_INSTRUMENTED: bool = False
_CORRELATION_CONTEXT: dict[str, str] = {}


class _NoopSpan:
    def set_attribute(self, *_: Any, **__: Any) -> None:
        return None

    def add_event(self, *_: Any, **__: Any) -> None:
        return None

    def record_exception(self, *_: Any, **__: Any) -> None:
        return None

    def set_status(self, *_: Any, **__: Any) -> None:
        return None


def _env_truthy(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _resolve_enabled(enable: bool | None) -> bool:
    if enable is not None:
        return bool(enable)
    if "NUSYQ_TRACING" in os.environ:
        return _env_truthy(os.environ.get("NUSYQ_TRACING"), True)
    return _env_truthy(os.environ.get("NUSYQ_TRACE"), True)


def _parse_resource_attributes(raw: str | None) -> dict[str, str]:
    attrs: dict[str, str] = {}
    if not raw:
        return attrs
    for item in raw.split(","):
        if not item.strip() or "=" not in item:
            continue
        key, value = item.split("=", 1)
        attrs[key.strip()] = value.strip()
    return attrs


def _import_opentelemetry() -> dict | None:
    try:
        from opentelemetry import baggage, trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (BatchSpanProcessor,
                                                    ConsoleSpanExporter,
                                                    SimpleSpanProcessor)
        from opentelemetry.trace import SpanKind

        otlp_exporter_cls: type[Any] | None
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import \
                OTLPSpanExporter as _OTLPSpanExporter

            otlp_exporter_cls = _OTLPSpanExporter
        except Exception:
            otlp_exporter_cls = None

        logging_instrumentor_cls: type[Any] | None
        try:
            from opentelemetry.instrumentation.logging import \
                LoggingInstrumentor as _LoggingInstrumentor

            logging_instrumentor_cls = _LoggingInstrumentor
        except Exception:
            logging_instrumentor_cls = None

        requests_instrumentor_cls: type[Any] | None
        try:
            from opentelemetry.instrumentation.requests import \
                RequestsInstrumentor as _RequestsInstrumentor

            requests_instrumentor_cls = _RequestsInstrumentor
        except Exception:
            requests_instrumentor_cls = None

        return {
            "baggage": baggage,
            "trace": trace,
            "Resource": Resource,
            "TracerProvider": TracerProvider,
            "BatchSpanProcessor": BatchSpanProcessor,
            "ConsoleSpanExporter": ConsoleSpanExporter,
            "SimpleSpanProcessor": SimpleSpanProcessor,
            "SpanKind": SpanKind,
            "OTLPSpanExporter": otlp_exporter_cls,
            "LoggingInstrumentor": logging_instrumentor_cls,
            "RequestsInstrumentor": requests_instrumentor_cls,
        }
    except Exception:
        return None


def _instrument_logging_and_requests(imports: dict) -> None:
    global _LOGGING_INSTRUMENTED, _REQUESTS_INSTRUMENTED

    if imports.get("LoggingInstrumentor") and not _LOGGING_INSTRUMENTED:
        try:
            imports["LoggingInstrumentor"]().instrument()
            _LOGGING_INSTRUMENTED = True
        except Exception as e:
            logger.debug(f"Non-critical: Failed to instrument logging: {e}")

    if imports.get("RequestsInstrumentor") and not _REQUESTS_INSTRUMENTED:
        try:
            imports["RequestsInstrumentor"]().instrument()
            _REQUESTS_INSTRUMENTED = True
        except Exception as e:
            logger.debug(f"Non-critical: Failed to instrument requests: {e}")


def _build_otlp_exporter(imports: dict, endpoint: str, protocol: str) -> Any | None:
    """Create OTLP exporter across old/new constructor signatures."""
    exporter_cls = imports.get("OTLPSpanExporter")
    if not exporter_cls:
        return None

    try:
        return exporter_cls(endpoint=endpoint, protocol=protocol)
    except TypeError:
        # Older opentelemetry-exporter versions do not accept "protocol".
        try:
            return exporter_cls(endpoint=endpoint)
        except Exception as exc:
            logger.debug(f"Non-critical: OTLP exporter init failed without protocol: {exc}")
            return None
    except Exception as exc:
        logger.debug(f"Non-critical: OTLP exporter init failed: {exc}")
        return None


def init_tracing(
    service_name: str | None = None,
    environment: str | None = None,
    endpoint: str | None = None,
    enable: bool | None = None,
    console_fallback: bool = False,  # Changed to False to avoid noisy CLI output
) -> bool:
    """Initialize OpenTelemetry if available, else return False.

    Note: console_fallback is False by default to avoid polluting CLI output
    with JSON trace spans. Set OTEL_TRACES_EXPORTER=console to enable explicitly.
    """
    global _TRACING_READY, _OTEL_AVAILABLE, _TRACER, _PROVIDER

    enabled = _resolve_enabled(enable)
    if not enabled:
        _TRACING_READY = False
        return False
    if _env_truthy(os.environ.get("OTEL_SDK_DISABLED"), False):
        _TRACING_READY = False
        return False

    # Avoid re-registering global tracer provider in long-running processes.
    if _TRACING_READY and _TRACER is not None and _PROVIDER is not None:
        return True

    imports = _import_opentelemetry()
    if not imports:
        _TRACING_READY = False
        return False

    exporter_name = os.environ.get("OTEL_TRACES_EXPORTER", "otlp").strip().lower()
    if exporter_name in {"none", "off", "disabled"}:
        _TRACING_READY = False
        return False

    service_name = service_name or os.environ.get("OTEL_SERVICE_NAME") or "nusyq-hub"
    environment = (
        environment or os.environ.get("NUSYQ_ENVIRONMENT") or os.environ.get("ENVIRONMENT")
    )
    # Prefer traces-specific endpoint if provided, else fall back
    endpoint = (
        endpoint
        or os.environ.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
        or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
        or "http://localhost:4318/v1/traces"
    )
    protocol = os.environ.get("OTEL_EXPORTER_OTLP_TRACES_PROTOCOL") or os.environ.get(
        "OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf"
    )

    resource_attrs = _parse_resource_attributes(os.environ.get("OTEL_RESOURCE_ATTRIBUTES"))
    resource_attrs["service.name"] = service_name
    if environment:
        resource_attrs.setdefault("deployment.environment", environment)

    resource = imports["Resource"].create(resource_attrs)
    provider = imports["TracerProvider"](resource=resource)

    exporter = None
    if exporter_name in {"console", "stdout"}:
        exporter = imports["ConsoleSpanExporter"]()
    elif exporter_name in {"otlp", "otlp_http", "http"} and imports.get("OTLPSpanExporter"):
        exporter = _build_otlp_exporter(imports, endpoint=endpoint, protocol=protocol)

    if exporter is None and console_fallback:
        exporter = imports["ConsoleSpanExporter"]()

    if exporter is None:
        _TRACING_READY = False
        return False

    try:
        processor = imports["BatchSpanProcessor"](exporter)
    except Exception:
        processor = imports["SimpleSpanProcessor"](exporter)

    provider.add_span_processor(processor)
    imports["trace"].set_tracer_provider(provider)
    _TRACER = imports["trace"].get_tracer("nusyq.tracing")
    _PROVIDER = provider
    _OTEL_AVAILABLE = True
    _TRACING_READY = True

    _instrument_logging_and_requests(imports)
    return True


def tracing_enabled() -> bool:
    return _TRACING_READY


def get_tracer(name: str):
    if not _TRACING_READY:
        return None
    try:
        imports = _import_opentelemetry()
        if not imports:
            return None
        return imports["trace"].get_tracer(name)
    except Exception:
        return None


def bind_context(**kwargs: str | None) -> None:
    for key, value in kwargs.items():
        if value is None:
            continue
        _CORRELATION_CONTEXT[key] = str(value)
        try:
            imports = _import_opentelemetry()
            if imports and imports.get("baggage"):
                imports["baggage"].set_baggage(key, str(value))
        except Exception as e:
            logger.debug(f"Non-critical: Failed to set baggage {key}: {e}")


def get_context_value(key: str) -> str | None:
    return _CORRELATION_CONTEXT.get(key)


def get_all_context() -> dict[str, str]:
    return _CORRELATION_CONTEXT.copy()


def clear_context() -> None:
    _CORRELATION_CONTEXT.clear()


@contextmanager
def start_span(name: str, attrs: dict[str, Any] | None = None, kind: str = "INTERNAL"):
    if not _TRACING_READY:
        yield _NoopSpan()
        return

    imports = _import_opentelemetry()
    if not imports:
        yield _NoopSpan()
        return

    tracer = imports["trace"].get_tracer("nusyq.tracing")
    span_kind = getattr(imports["SpanKind"], kind, imports["SpanKind"].INTERNAL)
    span_ctx = tracer.start_as_current_span(name, kind=span_kind)

    with span_ctx as span:
        merged_attrs = dict(_CORRELATION_CONTEXT)
        if attrs:
            merged_attrs.update(attrs)
        for key, value in merged_attrs.items():
            try:
                span.set_attribute(key, value)
            except Exception as e:
                logger.debug(f"Non-critical: Failed to set span attribute {key}: {e}")
        yield span


def start_action_span(name: str, attributes: dict[str, Any] | None = None):
    return start_span(name, attrs=attributes)


def current_trace_ids() -> tuple[str, str]:
    if not _TRACING_READY:
        return ("n/a", "n/a")
    try:
        imports = _import_opentelemetry()
        if not imports:
            return ("n/a", "n/a")
        span = imports["trace"].get_current_span()
        ctx = span.get_span_context() if span else None
        if not ctx:
            return ("n/a", "n/a")
        trace_id = format(ctx.trace_id, "032x") if getattr(ctx, "trace_id", 0) else "n/a"
        span_id = format(ctx.span_id, "016x") if getattr(ctx, "span_id", 0) else "n/a"
        return (trace_id, span_id)
    except Exception:
        return ("n/a", "n/a")


def flush_tracing(timeout: int = 5) -> bool:
    if not _TRACING_READY or not _PROVIDER:
        return True
    try:
        if hasattr(_PROVIDER, "force_flush"):
            _PROVIDER.force_flush(timeout_millis=timeout * 1000)
        return True
    except Exception:
        return False


def shutdown_tracing(timeout: int = 5) -> bool:
    global _TRACING_READY
    if not _TRACING_READY or not _PROVIDER:
        return True
    try:
        if hasattr(_PROVIDER, "shutdown"):
            _PROVIDER.shutdown(timeout_millis=timeout * 1000)
        _TRACING_READY = False
        return True
    except Exception:
        _TRACING_READY = False
        return False


def bind_correlation_id(key: str, value: str) -> None:
    bind_context(**{key: value})


def get_correlation_id(key: str) -> str | None:
    return get_context_value(key)


def get_all_correlation_ids() -> dict[str, str]:
    return get_all_context()


def clear_correlation_ids() -> None:
    clear_context()
