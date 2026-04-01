# OpenTelemetry Tracing Setup

## Overview

NuSyQ-Hub uses OpenTelemetry for distributed tracing. The system supports graceful degradation and will work without a trace backend.

## Configuration

### Console Mode (Default - No Backend Required)

Set this in your environment or `.env.tracing`:

```bash
OTEL_TRACES_EXPORTER=console
```

Traces will be printed to the console. No connection errors.

### OTLP Mode (Requires Trace Backend)

When you have a trace collector running (e.g., Jaeger):

```bash
OTEL_TRACES_EXPORTER=otlp
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```

### Disable Tracing

```bash
OTEL_TRACES_EXPORTER=none
# or
NUSYQ_TRACING=false
```

## Starting the Trace Service

### Option 1: Jaeger All-in-One (Docker)

```bash
docker run -d \
  --name jaeger \
  -p 16686:16686 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest
```

Then access the UI at: http://localhost:16686

### Option 2: Manual Service Start

```bash
python scripts/service_manager.py start trace_service
```

## Current Errors

If you see errors like:

```
ConnectionRefusedError: [WinError 10061] No connection could be made because the target machine actively refused it
```

This means:
1. OTLP exporter is enabled (default when OTEL_TRACES_EXPORTER is not set)
2. Trace service on port 4318 is not running

**Fix:** Set `OTEL_TRACES_EXPORTER=console` or start the trace service.

## Checking Current Configuration

```python
import os
print("OTEL_TRACES_EXPORTER:", os.environ.get('OTEL_TRACES_EXPORTER', 'otlp (default)'))
print("OTEL_EXPORTER_OTLP_ENDPOINT:", os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4318 (default)'))
```

## Recommended Setup

For development without Docker:

```bash
# Add to .env or shell profile
export OTEL_TRACES_EXPORTER=console
export OTEL_SERVICE_NAME=nusyq-hub
```

For production with observability stack:

```bash
export OTEL_TRACES_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_SERVICE_NAME=nusyq-hub
export ENVIRONMENT=production
```

## Graceful Degradation

The system is designed to work WITHOUT tracing infrastructure:

1. If OpenTelemetry packages aren't installed → NoOp spans (silent)
2. If OTEL_TRACES_EXPORTER=none → Tracing disabled
3. If console mode → Traces printed locally
4. If OTLP mode but service down → **ERROR** (connection refused)

**Recommended:** Use console mode for development unless actively debugging with Jaeger.
