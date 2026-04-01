# OpenTelemetry Tracing - NuSyQ-Hub

## Status: ✅ ACTIVE (December 24, 2025)

Distributed tracing is now **fully configured** using OpenTelemetry with AI Toolkit integration.

## Quick Start

### View Live Traces

The AI Toolkit Trace Viewer is integrated and ready. All traces are sent to:
- **Endpoint**: `http://localhost:4318/v1/traces`
- **Protocol**: OTLP/HTTP

### Test Tracing

```bash
python test_tracing.py
```

This creates sample spans for:
- Multi-AI orchestrator health checks
- Ollama system monitoring
- Request routing decisions

## Setup Complete

### Dependencies Installed ✅

- `opentelemetry-api>=1.20.0`
- `opentelemetry-sdk>=1.20.0`
- `opentelemetry-exporter-otlp>=1.20.0`
- `opentelemetry-instrumentation-requests>=0.41b0`
- `opentelemetry-instrumentation-logging>=0.41b0`

### Files Modified

1. **`requirements.txt`** - Added OpenTelemetry packages
2. **`src/main.py`** - Tracing initialization at startup
3. **`src/orchestration/multi_ai_orchestrator.py`** - Spans for key operations
4. **`test_tracing.py`** - Demo script

## Architecture

```
NuSyQ-Hub Application
         ↓
OpenTelemetry SDK
         ↓
OTLP Exporter (HTTP)
         ↓
AI Toolkit Trace Collector (localhost:4318)
         ↓
Trace Viewer (VS Code)
```

## Instrumented Operations

### Automatic (via Auto-Instrumentation)
- ✅ HTTP requests (via `RequestsInstrumentor`)
- ✅ Logging events (via `LoggingInstrumentor`)

### Manual Spans Added
- ✅ `health_check` - Multi-AI orchestrator health monitoring
- ✅ `route_request` - AI system routing with attributes:
  - `task_type`
  - `complexity`
  - `selected_system`

## Adding Tracing to Your Code

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def my_ai_operation():
    with tracer.start_as_current_span("my_operation") as span:
        span.set_attribute("ai.system", "ollama")
        span.set_attribute("task.type", "code_generation")
        # Your code here
```

## Environment Variables (Optional)

While tracing is enabled by default, you can configure:

```bash
# Disable tracing
OTEL_ENABLED=0

# Custom endpoint
OTEL_EXPORTER_OTLP_ENDPOINT=http://custom-collector:4318/v1/traces

# Service name
OTEL_SERVICE_NAME=nusyq-hub-custom
```

## Legacy Support

This file previously documented a simpler tracing helper. The new implementation:
- ✅ Uses industry-standard OpenTelemetry
- ✅ Integrates with AI Toolkit's built-in trace viewer
- ✅ Provides auto-instrumentation for common operations
- ✅ Supports both development and production use

## Troubleshooting

**Traces not appearing?**
1. Verify AI Toolkit trace collector is running
2. Check endpoint: `curl http://localhost:4318/v1/traces`
3. Review logs for export errors
4. Confirm packages installed: `pip list | grep opentelemetry`

**Performance concerns?**
- Spans are batched for efficiency
- Sampling can be configured via `TraceProvider`
- Disable with `OTEL_ENABLED=0` if needed

## Next Steps

Consider adding spans to:
- Ollama API interactions
- ChatDev multi-agent operations
- Quantum resolver workflows
- Consciousness bridge semantic analysis

---

**Updated**: December 24, 2025  
**OpenTelemetry SDK**: 1.39.1  
**AI Toolkit**: Integrated


Then run the app and it will export traces to the collector.
