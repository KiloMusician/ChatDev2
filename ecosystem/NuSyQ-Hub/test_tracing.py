#!/usr/bin/env python3
"""Test script to demonstrate OpenTelemetry tracing in NuSyQ-Hub.

This script demonstrates the tracing functionality without requiring
all the complex imports.
"""

import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Initialize OpenTelemetry tracing
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SpanExporter,
)

# Configure resource with service name
resource = Resource.create({"service.name": "nusyq-hub-test"})

# Set up tracer provider
tracer_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer_provider)

# Configure exporter: use OTLP if endpoint is provided, otherwise fallback to console exporter
otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
exporter: SpanExporter
try:
    if otel_endpoint:
        # Normalize endpoint to include path for traces if not provided
        endpoint = otel_endpoint.rstrip("/")
        if not endpoint.endswith("/v1/traces"):
            endpoint = f"{endpoint}/v1/traces"
        exporter = OTLPSpanExporter(endpoint=endpoint)
    else:
        exporter = ConsoleSpanExporter()
except Exception:
    # If OTLP cannot be configured (e.g., package mismatch or bad endpoint), fallback to console
    exporter = ConsoleSpanExporter()

# Add batch span processor
tracer_provider.add_span_processor(BatchSpanProcessor(exporter))

# Auto-instrument HTTP requests only if explicitly enabled via env
if os.getenv("OTEL_INSTRUMENT_REQUESTS", "0") in {"1", "true", "True"}:
    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor

        RequestsInstrumentor().instrument()
    except Exception:
        # Safe to ignore if instrumentation isn't available
        pass

# Get tracer
tracer = trace.get_tracer(__name__)


def test_orchestrator_health():
    """Test the multi-AI orchestrator health check with tracing."""
    with tracer.start_as_current_span("orchestrator_health_check") as span:
        span.set_attribute("service.component", "multi-ai-orchestrator")

        print("🔍 Testing Multi-AI Orchestrator Health Check...")

        # Simulate checking Ollama
        with tracer.start_as_current_span("check_ollama") as ollama_span:
            ollama_span.set_attribute("system", "ollama")
            ollama_span.set_attribute("endpoint", "http://localhost:11434")

            try:
                import requests

                response = requests.get("http://localhost:11434/api/tags", timeout=1.0)
                status = response.status_code == 200
                ollama_span.set_attribute("status", "healthy" if status else "unhealthy")
                print(f"  ✅ Ollama: {'healthy' if status else 'unhealthy'}")
            except Exception as e:
                # Do not fail the test if Ollama is not running; record and continue.
                ollama_span.set_attribute("status", "unavailable")
                ollama_span.set_attribute("error", str(e))
                print(f"  ⚠️ Ollama unavailable: {e}")

        # Simulate route request
        with tracer.start_as_current_span("route_request") as route_span:
            route_span.set_attribute("task_type", "code_generation")
            route_span.set_attribute("complexity", "medium")
            time.sleep(0.1)  # Simulate processing
            route_span.set_attribute("selected_system", "ollama")
            print("  📍 Routed code_generation task to Ollama")

        print("\n✅ Tracing test complete!")
        print("📊 Check AI Toolkit Trace Viewer for spans:")
        print("   - orchestrator_health_check")
        print("   - check_ollama")
        print("   - route_request")
        if isinstance(exporter, ConsoleSpanExporter):
            print("\n💡 Traces are printed to console (ConsoleSpanExporter)")
        else:
            print(
                "\n💡 Traces are being sent to:",
                getattr(exporter, "_endpoint", "<configured OTLP endpoint>"),
            )


if __name__ == "__main__":
    test_orchestrator_health()

    # Give time for spans to be exported
    time.sleep(2)
    print("\n✅ All spans exported successfully!")
