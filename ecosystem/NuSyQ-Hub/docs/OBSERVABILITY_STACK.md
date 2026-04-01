# 🌟 NuSyQ-Hub Observability Stack

**Status:** ✅ FULLY OPERATIONAL (December 24, 2025)

A complete, production-ready observability system integrating distributed tracing, metrics collection, intelligent caching, and auto-healing capabilities.

## 🎯 Overview

The NuSyQ-Hub observability stack demonstrates **system evolution** through four integrated pillars:

1. **OpenTelemetry Distributed Tracing** - Track request flows across AI systems
2. **Prometheus Metrics Collection** - Monitor performance and health metrics  
3. **Semantic Similarity Caching** - Reduce redundant AI calls with intelligent caching
4. **Auto-Healing Error Recovery** - Automatically detect and resolve errors

All components work together seamlessly, providing full visibility into the multi-AI orchestration system while automatically improving performance and reliability.

## 🚀 Quick Start

### Run the Complete Demo

```bash
python test_observability_stack.py
```

This comprehensive demonstration shows:
- ✅ Distributed tracing with nested spans
- ✅ Prometheus metrics (Counter, Histogram, Gauge)
- ✅ Semantic cache with hit/miss tracking
- ✅ Auto-healing with quantum resolver integration
- ✅ Full stack integration example

### Access Observability Endpoints

- **AI Toolkit Trace Viewer**: Open in VS Code (automatically configured)
- **Prometheus Metrics**: http://localhost:8000/metrics
- **Trace Collector**: http://localhost:4318/v1/traces (OTLP/HTTP)

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│  (Multi-AI Orchestrator, Quantum Resolver, etc.)            │
└──────────────────────┬──────────────────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       │               │               │
       ▼               ▼               ▼
┌──────────┐   ┌──────────┐   ┌──────────────┐
│  Tracing │   │ Metrics  │   │   Caching    │
│ (OTel)   │   │(Prom)    │   │(Semantic)    │
└──────────┘   └──────────┘   └──────────────┘
       │               │               │
       └───────────────┼───────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  Auto-Healing  │
              │   Monitor      │
              └────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │    Quantum     │
              │Problem Resolver│
              └────────────────┘
```

## 🔍 Distributed Tracing

### Features

- **OpenTelemetry SDK 1.39.1** with OTLP/HTTP exporter
- **AI Toolkit Integration** for visualization in VS Code
- **Auto-instrumentation** for HTTP requests and logging
- **Nested spans** showing parent-child relationships
- **Custom attributes** for rich context

### Usage

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("ai_request") as span:
    span.set_attribute("system", "ollama")
    span.set_attribute("model", "qwen2.5-coder")

    # Your AI operation here
    result = call_ai_system(prompt)

    span.set_attribute("tokens", len(result))
```

### Instrumented Operations

- ✅ Multi-AI orchestrator health checks
- ✅ AI system routing and selection
- ✅ Request/response processing
- ✅ Error handling and recovery
- ✅ HTTP requests (auto-instrumented)
- ✅ Logging events (auto-instrumented)

## 📈 Prometheus Metrics

### Metric Types

**Counters** - Monotonically increasing values
```python
from prometheus_client import Counter

requests_total = Counter(
    'ai_requests_total',
    'Total AI requests',
    ['system', 'status']
)

requests_total.labels(system='ollama', status='success').inc()
```

**Histograms** - Distribution of values
```python
from prometheus_client import Histogram

request_duration = Histogram(
    'ai_request_duration_seconds',
    'AI request latency',
    ['system']
)

with request_duration.labels(system='ollama').time():
    # Operation to measure
    result = process_request()
```

**Gauges** - Values that can go up or down
```python
from prometheus_client import Gauge

system_health = Gauge(
    'ai_system_health',
    'AI system health status',
    ['system']
)

system_health.labels(system='ollama').set(1)  # 1 = healthy
```

### Available Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `ai_requests_total` | Counter | Total AI requests by system/status |
| `ai_request_duration_seconds` | Histogram | Request latency distribution |
| `ai_system_health` | Gauge | System health (1=healthy, 0=unhealthy) |
| `cache_hits_total` | Counter | Semantic cache hits |
| `cache_misses_total` | Counter | Semantic cache misses |
| `cache_latency_seconds` | Histogram | Cache lookup latency |
| `auto_healing_attempts_total` | Counter | Healing attempts by error type |
| `auto_healing_duration_seconds` | Histogram | Healing operation duration |

### Metrics Server

```python
from prometheus_client import start_http_server

# Start metrics HTTP server
start_http_server(8000)
# Metrics available at http://localhost:8000/metrics
```

## 💾 Semantic Caching

### Features

- **Intelligent similarity matching** using token overlap
- **TTL expiration** (default 1 hour)
- **Disk-based persistence** with memory fallback
- **Prometheus integration** for cache metrics
- **Hit rate tracking** and statistics

### Usage

```python
from src.orchestration.semantic_cache import get_cache

cache = get_cache()

# Store response
cache.set(
    query="What is quantum computing?",
    response="Quantum computing uses quantum mechanics...",
    system="ollama",
    model="qwen2.5-coder",
    token_count=128
)

# Retrieve similar queries
cached = cache.get(
    query="Explain quantum computing",  # Similar query
    system="ollama"
)

if cached:
    print(f"Cache hit! Response: {cached.response}")
else:
    print("Cache miss, generating new response...")

# Get statistics
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.1%}")
```

### Similarity Algorithm

Currently uses **Jaccard similarity** on token sets:

```
similarity = |tokens1 ∩ tokens2| / |tokens1 ∪ tokens2|
```

**Future enhancement:** Replace with embedding-based similarity using sentence-transformers for better semantic matching.

### Configuration

```python
cache = SemanticCache(
    cache_dir=".cache/ai_responses",
    ttl_seconds=3600,          # 1 hour
    similarity_threshold=0.7,   # 70% similarity required
    max_size_mb=100            # Max disk cache size
)
```

## 🔧 Auto-Healing

### Features

- **Real-time error detection** from traced operations
- **Quantum resolver integration** for intelligent healing
- **Cooldown periods** to prevent healing storms
- **Retry limits** per error type
- **Success/failure tracking** with Prometheus metrics
- **Custom healing callbacks** for specific error types

### Usage

#### Decorator Pattern

```python
from src.orchestration.auto_healing import traced_operation

@traced_operation("critical_ai_call", auto_heal=True)
def call_ai_system(prompt):
    """Automatically traced and healed if errors occur."""
    return ai.generate(prompt)
```

#### Manual Error Handling

```python
from src.orchestration.auto_healing import get_monitor, ErrorContext

monitor = get_monitor()

try:
    result = risky_operation()
except Exception as e:
    context = ErrorContext(
        error_type=type(e).__name__,
        error_message=str(e),
        span_name="risky_operation",
        timestamp=time.time(),
        attributes={"critical": True}
    )

    healed = monitor.on_error(e, context)

    if healed:
        result = risky_operation()  # Retry after healing
    else:
        raise  # Propagate if healing failed
```

### Healing Statistics

```python
monitor = get_monitor()
stats = monitor.get_stats()

print(f"Errors detected: {stats['errors_detected']}")
print(f"Healing success rate: {stats['success_rate']:.1%}")
```

### Auto-Fixable Errors

The following error types are automatically healed:

- ✅ **ConnectionError** - Retries with exponential backoff
- ✅ **TimeoutError** - Adjusts timeout parameters
- ✅ **ImportError** - Auto-fixes import paths
- 🔄 **Custom errors** - Via quantum resolver analysis

### Configuration

```python
monitor = AutoHealingMonitor(
    enable_auto_heal=True,
    max_retry_attempts=3,
    cooldown_seconds=60
)
```

## 🌟 Full Stack Integration

### Example: Cached AI Request with Tracing and Metrics

```python
from opentelemetry import trace
from prometheus_client import Counter, Histogram
from src.orchestration.semantic_cache import get_cache

tracer = trace.get_tracer(__name__)
cache = get_cache()

requests = Counter('ai_requests', 'AI requests', ['status'])
latency = Histogram('ai_latency', 'AI latency')

def process_ai_request(query: str):
    """Process AI request with full observability."""

    with tracer.start_as_current_span("ai_request") as span:
        span.set_attribute("query", query)

        # Check cache first
        cached = cache.get(query, system="ollama")

        if cached:
            span.set_attribute("cache_hit", True)
            requests.labels(status="cache_hit").inc()
            return cached.response

        # Cache miss - call AI
        span.set_attribute("cache_hit", False)

        with latency.time():
            try:
                response = call_ai_system(query)
                requests.labels(status="success").inc()

                # Cache for next time
                cache.set(query, response, "ollama", "qwen2.5", 100)

                return response

            except Exception as e:
                requests.labels(status="error").inc()
                span.record_exception(e)
                raise
```

## 📦 Dependencies

```
# Tracing
opentelemetry-api==1.39.1
opentelemetry-sdk==1.39.1
opentelemetry-exporter-otlp==1.39.1
opentelemetry-instrumentation-requests==0.51b0
opentelemetry-instrumentation-logging==0.51b0

# Metrics
prometheus-client>=0.19.0

# Caching
cachetools>=5.3.0
diskcache>=5.6.0
```

## 🎯 Use Cases

### 1. Performance Monitoring
Track latency, throughput, and error rates across all AI systems

### 2. Cost Optimization
Use semantic caching to reduce redundant AI API calls ($$$ savings)

### 3. Debugging
Trace request flows to identify bottlenecks and errors

### 4. Reliability
Auto-heal errors automatically without human intervention

### 5. Capacity Planning
Use metrics to understand usage patterns and scale appropriately

## 🔬 Testing

### Run Full Test Suite

```bash
# Comprehensive observability demo
python test_observability_stack.py

# Individual tracing test
python test_tracing.py
```

### Verify Components

```bash
# Check Prometheus metrics
curl http://localhost:8000/metrics

# Check traces (requires AI Toolkit)
# Open VS Code > View > Command Palette > "Open Trace Viewer"
```

## 🚀 Production Deployment

### 1. Environment Configuration

```bash
# Enable all systems
export TRACING_ENABLED=true
export METRICS_ENABLED=true
export CACHE_ENABLED=true
export AUTO_HEALING_ENABLED=true

# Configure endpoints
export OTLP_ENDPOINT=http://collector:4318/v1/traces
export PROMETHEUS_PORT=8000
```

### 2. Resource Limits

```python
# semantic_cache.py
cache = SemanticCache(
    max_size_mb=500,  # 500MB cache limit
    ttl_seconds=7200  # 2 hour TTL
)

# auto_healing.py
monitor = AutoHealingMonitor(
    max_retry_attempts=5,
    cooldown_seconds=300  # 5 minute cooldown
)
```

### 3. Monitoring

Set up Grafana dashboards for:
- Request rate and latency (from Prometheus)
- Cache hit rates and savings
- Auto-healing success rates
- Distributed trace visualization

## 📚 Additional Resources

- [OpenTelemetry Python Docs](https://opentelemetry.io/docs/languages/python/)
- [Prometheus Client Python](https://prometheus.github.io/client_python/)
- [AI Toolkit for VS Code](https://marketplace.visualstudio.com/items?itemName=ms-windows-ai-studio.windows-ai-studio)

## 🎉 System Evolution Demonstrated

This observability stack shows the NuSyQ-Hub system's ability to **evolve and grow** capabilities:

- Started with basic tracing ✅
- Added comprehensive metrics ✅
- Integrated intelligent caching ✅
- Enabled auto-healing ✅
- Created cohesive unified stack ✅

**Result:** A production-ready observability system that enhances reliability, performance, and developer experience while demonstrating autonomous system evolution.

---

*Last updated: December 24, 2025*
*Status: Fully operational and tested*
