#!/usr/bin/env python3
"""Comprehensive Observability Stack Demonstration.

This script demonstrates the full NuSyQ-Hub observability system:
- OpenTelemetry distributed tracing
- Prometheus metrics collection
- Semantic similarity caching
- Auto-healing error recovery

Run with: python test_observability_stack.py
"""

import logging
import sys
import time
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import observability components
try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    # Initialize OpenTelemetry
    resource = Resource.create({"service.name": "nusyq-hub-demo"})
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces"))
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    # Auto-instrument
    RequestsInstrumentor().instrument()
    LoggingInstrumentor().instrument()

    TRACING_ENABLED = True
    logger.info("✅ OpenTelemetry tracing initialized")
except Exception as e:
    TRACING_ENABLED = False
    logger.warning(f"⚠️  Tracing not available: {e}")

# Import Prometheus
try:
    from prometheus_client import Counter, Gauge, Histogram, start_http_server

    # Define metrics
    demo_requests = Counter("demo_requests_total", "Total demo requests", ["operation", "status"])
    demo_duration = Histogram("demo_duration_seconds", "Demo operation duration", ["operation"])
    demo_cache_size = Gauge("demo_cache_size_bytes", "Cache size in bytes")

    METRICS_ENABLED = True
    logger.info("✅ Prometheus metrics initialized")
except Exception as e:
    METRICS_ENABLED = False
    logger.warning(f"⚠️  Metrics not available: {e}")

# Import semantic cache
try:
    from src.orchestration.semantic_cache import get_cache

    CACHE_ENABLED = True
    logger.info("✅ Semantic cache initialized")
except Exception as e:
    CACHE_ENABLED = False
    logger.warning(f"⚠️  Cache not available: {e}")

# Import auto-healing
try:
    from src.orchestration.auto_healing import get_monitor

    HEALING_ENABLED = True
    logger.info("✅ Auto-healing monitor initialized")
except Exception as e:
    HEALING_ENABLED = False
    logger.warning(f"⚠️  Auto-healing not available: {e}")


def demonstrate_tracing():
    """Demonstrate distributed tracing."""
    print("\n" + "=" * 60)
    print("🔍 DISTRIBUTED TRACING DEMONSTRATION")
    print("=" * 60)

    if not TRACING_ENABLED:
        print("❌ Tracing not enabled")
        return

    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("demo_parent_operation") as parent:
        parent.set_attribute("demo.type", "observability_stack")
        parent.set_attribute("demo.version", "1.0.0")

        print("📊 Creating nested trace spans...")

        # Nested operation 1
        with tracer.start_as_current_span("demo_child_operation_1") as child1:
            child1.set_attribute("operation", "data_processing")
            time.sleep(0.1)
            print("  ├─ Child span 1: Data processing (100ms)")

        # Nested operation 2
        with tracer.start_as_current_span("demo_child_operation_2") as child2:
            child2.set_attribute("operation", "ai_inference")
            time.sleep(0.2)
            print("  ├─ Child span 2: AI inference (200ms)")

        # Nested operation 3
        with tracer.start_as_current_span("demo_child_operation_3") as child3:
            child3.set_attribute("operation", "response_formatting")
            time.sleep(0.05)
            print("  └─ Child span 3: Response formatting (50ms)")

    print("\n✅ Traces sent to http://localhost:4318/v1/traces")
    print("💡 Open AI Toolkit trace viewer to see the flame graph")


def demonstrate_metrics():
    """Demonstrate Prometheus metrics."""
    print("\n" + "=" * 60)
    print("📈 PROMETHEUS METRICS DEMONSTRATION")
    print("=" * 60)

    if not METRICS_ENABLED:
        print("❌ Metrics not enabled")
        return

    print("📊 Recording metrics...")

    # Simulate operations with metrics
    operations = [
        ("data_load", 0.5, "success"),
        ("ai_call", 1.2, "success"),
        ("ai_call", 0.8, "success"),
        ("data_save", 0.3, "success"),
        ("ai_call", 2.1, "timeout"),
    ]

    for op, duration, status in operations:
        demo_requests.labels(operation=op, status=status).inc()
        demo_duration.labels(operation=op).observe(duration)
        print(f"  ├─ {op}: {duration}s ({status})")

    # Update cache size gauge
    demo_cache_size.set(1024 * 1024 * 2.5)  # 2.5 MB

    print("\n✅ Metrics recorded:")
    print("  • demo_requests_total (Counter)")
    print("  • demo_duration_seconds (Histogram)")
    print("  • demo_cache_size_bytes (Gauge)")
    print("\n💡 Metrics available at http://localhost:8000/metrics")


def demonstrate_caching():
    """Demonstrate semantic caching."""
    print("\n" + "=" * 60)
    print("💾 SEMANTIC CACHING DEMONSTRATION")
    print("=" * 60)

    if not CACHE_ENABLED:
        print("❌ Caching not enabled")
        return

    cache = get_cache()

    print("📊 Testing semantic similarity caching...")

    # Similar queries that should hit cache
    queries = [
        "What is the meaning of life?",
        "What's the meaning of life?",  # Should match (high similarity)
        "Explain the meaning of existence",  # Should match (medium similarity)
        "How do I bake a cake?",  # Should NOT match (low similarity)
    ]

    # Store first query result
    response = "The meaning of life is to find purpose and connection."
    cache.set(
        query=queries[0], response=response, system="demo_ai", model="demo-model-v1", token_count=42
    )
    print(f"  ├─ Cached: '{queries[0]}'")

    # Test retrieval with similar queries
    for i, query in enumerate(queries[1:], 1):
        cached = cache.get(query, system="demo_ai")
        if cached:
            print(f"  ├─ Query {i}: CACHE HIT ✅")
        else:
            print(f"  └─ Query {i}: CACHE MISS ❌")

    # Show statistics
    stats = cache.get_stats()
    print("\n✅ Cache Statistics:")
    print(f"  • Hits: {stats['hits']}")
    print(f"  • Misses: {stats['misses']}")
    print(f"  • Hit Rate: {stats['hit_rate']:.1%}")
    print(f"  • Total Queries: {stats['total_queries']}")


def demonstrate_auto_healing():
    """Demonstrate auto-healing."""
    print("\n" + "=" * 60)
    print("🔧 AUTO-HEALING DEMONSTRATION")
    print("=" * 60)

    if not HEALING_ENABLED:
        print("❌ Auto-healing not enabled")
        return

    monitor = get_monitor()

    print("📊 Testing error detection and healing...")

    # Simulate different error scenarios
    from src.orchestration.auto_healing import ErrorContext

    errors = [
        ("ConnectionError", "Failed to connect to AI service"),
        ("TimeoutError", "Request timed out after 30s"),
        ("ImportError", "Module 'quantum_magic' not found"),
    ]

    for error_type, message in errors:
        context = ErrorContext(
            error_type=error_type,
            error_message=message,
            span_name="demo_operation",
            timestamp=time.time(),
            attributes={"demo": True},
        )

        # Simulate error
        error = Exception(message)
        healed = monitor.on_error(error, context)

        status = "✅ HEALED" if healed else "❌ NOT HEALED"
        print(f"  ├─ {error_type}: {status}")

    # Show healing stats
    stats = monitor.get_stats()
    print("\n✅ Auto-Healing Statistics:")
    print(f"  • Errors Detected: {stats['errors_detected']}")
    print(f"  • Healing Attempts: {stats['healing_attempts']}")
    print(f"  • Successes: {stats['healing_successes']}")
    print(f"  • Success Rate: {stats['success_rate']:.1%}")


def demonstrate_integration():
    """Demonstrate all systems working together."""
    print("\n" + "=" * 60)
    print("🌟 FULL STACK INTEGRATION")
    print("=" * 60)

    if not (TRACING_ENABLED and METRICS_ENABLED and CACHE_ENABLED):
        print("⚠️  Not all systems available for integration demo")
        return

    tracer = trace.get_tracer(__name__)
    cache = get_cache()

    query = "Explain quantum computing"

    print(f"📊 Processing query: '{query}'")

    with tracer.start_as_current_span("integrated_ai_request") as span:
        span.set_attribute("query", query)
        start = time.time()

        # Check cache first
        cached = cache.get(query, system="demo_ai")

        if cached:
            print("  ├─ 💾 CACHE HIT - Using cached response")
            span.set_attribute("cache_hit", True)
            response = cached["response"]
            demo_requests.labels(operation="ai_request", status="cache_hit").inc()
        else:
            print("  ├─ 🔍 CACHE MISS - Generating new response")
            span.set_attribute("cache_hit", False)

            # Simulate AI call
            time.sleep(0.5)
            response = "Quantum computing uses quantum mechanics..."

            # Cache the response
            cache.set(
                query=query,
                response=response,
                system="demo_ai",
                model="quantum-explainer-v1",
                token_count=128,
            )

            demo_requests.labels(operation="ai_request", status="success").inc()

        duration = time.time() - start
        demo_duration.labels(operation="ai_request").observe(duration)
        span.set_attribute("duration_ms", int(duration * 1000))

        print(f"  └─ ✅ Response generated in {duration * 1000:.0f}ms")

    print("\n✅ Full observability stack operational:")
    print("  • Trace: Captured distributed timing")
    print("  • Metrics: Recorded latency and status")
    print("  • Cache: Stored for future similarity matches")
    print("  • Healing: Monitoring for errors")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("🚀 NUSYQ-HUB OBSERVABILITY STACK DEMO")
    print("=" * 60)
    print("\nThis demonstrates the complete observability system:")
    print("• OpenTelemetry Distributed Tracing")
    print("• Prometheus Metrics Collection")
    print("• Semantic Similarity Caching")
    print("• Auto-Healing Error Recovery")

    # Start Prometheus metrics server
    if METRICS_ENABLED:
        try:
            start_http_server(8000)
            print("\n✅ Prometheus metrics server started on http://localhost:8000")
        except Exception as e:
            print(f"\n⚠️  Could not start metrics server: {e}")

    # Run demonstrations
    demonstrate_tracing()
    demonstrate_metrics()
    demonstrate_caching()
    demonstrate_auto_healing()
    demonstrate_integration()

    # Summary
    print("\n" + "=" * 60)
    print("📊 OBSERVABILITY STACK STATUS")
    print("=" * 60)

    components = [
        ("OpenTelemetry Tracing", TRACING_ENABLED),
        ("Prometheus Metrics", METRICS_ENABLED),
        ("Semantic Caching", CACHE_ENABLED),
        ("Auto-Healing", HEALING_ENABLED),
    ]

    for name, enabled in components:
        status = "✅ ACTIVE" if enabled else "❌ INACTIVE"
        print(f"{status} - {name}")

    print("\n💡 Next steps:")
    print("  1. Open AI Toolkit trace viewer for distributed traces")
    print("  2. Visit http://localhost:8000/metrics for Prometheus data")
    print("  3. Check semantic_cache stats for hit rates")
    print("  4. Monitor auto-healing for error recovery")

    print("\n🎉 Demo complete! System evolution demonstrated.")


if __name__ == "__main__":
    main()
