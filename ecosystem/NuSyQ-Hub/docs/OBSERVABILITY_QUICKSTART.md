# NuSyQ-Hub Observability Quick Start

**Purpose**: Enable distributed tracing across NuSyQ-Hub entry points with minimal setup.

**Status**: ✅ Operational (console + OTLP exporters available)

---

## Architecture

```
┌─────────────┐
│  src/main.py│──┐
└─────────────┘  │
                 │
┌─────────────┐  │    ┌───────────────────────────┐
│start_nusyq.py├──┼───▶│src/observability/otel.py│
└─────────────┘  │    └───────────────────────────┘
                 │              │
┌─────────────┐  │              │
│  AI Routers │──┘              ├──▶ ConsoleSpanExporter (fallback)
└─────────────┘                 │
                                ├──▶ OTLPSpanExporter (http://localhost:4318)
                                └──▶ BatchSpanProcessor (async export)
```

**Features**:
- Graceful degradation (no crash if OTEL unavailable)
- Environment-variable driven configuration
- Automatic shutdown/flush on process exit
- Correlation ID context (quest_id, task_id, etc.)

---

## Quick Start (Console Mode)

**No collector needed** - traces print to console for quick debugging.

### 1. Set environment variable

```bash
export OTEL_TRACES_EXPORTER=console
export NUSYQ_TRACE=1  # Enable tracing (default: enabled)
```

**Windows (PowerShell)**:
```powershell
$env:OTEL_TRACES_EXPORTER = "console"
$env:NUSYQ_TRACE = "1"
```

### 2. Run any entry point

```bash
# Example: main.py analysis mode
python src/main.py --mode=analysis --quick

# Example: spine command
python scripts/start_nusyq.py snapshot

# Example: doctrine check
python scripts/start_nusyq.py doctrine_check
```

### 3. View console output

Spans will print to stderr with attributes:

```json
{
    "name": "nusyq.startup",
    "context": {
        "trace_id": "0x1234567890abcdef1234567890abcdef",
        "span_id": "0x1234567890abcdef",
        "trace_state": "[]"
    },
    "kind": "SpanKind.INTERNAL",
    "parent_id": null,
    "start_time": "2025-12-24T07:30:00.123456Z",
    "end_time": "2025-12-24T07:30:05.654321Z",
    "status": {
        "status_code": "UNSET"
    },
    "attributes": {
        "mode": "analysis",
        "python_version": "3.12.10",
        "repo_root": "C:\\Users\\keath\\Desktop\\Legacy\\NuSyQ-Hub"
    }
}
```

---

## OTLP Mode (Local Collector)

**For production-like tracing** with Jaeger/Zipkin/Grafana visualization.

### 1. Install OTEL Collector (optional)

Download from: https://github.com/open-telemetry/opentelemetry-collector-releases/releases

**Quick setup** (macOS/Linux):
```bash
curl -L https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v0.91.0/otelcol_0.91.0_linux_amd64.tar.gz | tar xz
./otelcol --config=config/otel-collector.yaml
```

**Windows**:
Download exe from releases page, run:
```powershell
.\\otelcol.exe --config=config\\otel-collector.yaml
```

### 2. Configure environment

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_SERVICE_NAME=nusyq-hub
export OTEL_RESOURCE_ATTRIBUTES="environment=dev,version=2.0"
unset OTEL_TRACES_EXPORTER  # Use OTLP (default)
```

### 3. Run entry points

Traces will export to collector at `http://localhost:4318/v1/traces`

### 4. View in Jaeger (optional)

If collector configured with Jaeger exporter:
- Open http://localhost:16686
- Select service: `nusyq-hub` or `nusyq-hub-main`
- View trace timeline

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NUSYQ_TRACE` | `1` | Enable (1) or disable (0) tracing |
| `OTEL_TRACES_EXPORTER` | `otlp` | Exporter type: `otlp`, `console`, `none` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4318` | OTLP collector HTTP endpoint |
| `OTEL_SERVICE_NAME` | `nusyq-hub` | Service identifier in traces |
| `OTEL_RESOURCE_ATTRIBUTES` | (empty) | Key-value pairs: `key1=val1,key2=val2` |

---

## Correlation IDs

**Purpose**: Link quests → spans → logs for end-to-end request tracking.

### Bind correlation ID

```python
from src.observability.otel import bind_correlation_id

bind_correlation_id("quest_id", "a1b2c3d4")
bind_correlation_id("task_id", "analyze_file_123")
```

### Retrieve in spans

```python
from src.observability.otel import get_all_correlation_ids, start_action_span

with start_action_span("my.action", get_all_correlation_ids()) as span:
    # Span will include quest_id + task_id as attributes
    do_work()
```

---

## VS Code Integration

### Task: Console Tracing Mode

```json
{
  "label": "NuSyQ: Tracing Console Mode",
  "type": "shell",
  "command": "python",
  "args": ["src/main.py", "--mode=analysis", "--quick"],
  "options": {
    "cwd": "${workspaceFolder}",
    "env": {
      "OTEL_TRACES_EXPORTER": "console",
      "NUSYQ_TRACE": "1"
    }
  }
}
```

### Task: OTLP Tracing Mode

```json
{
  "label": "NuSyQ: Tracing OTLP Mode",
  "type": "shell",
  "command": "python",
  "args": ["scripts/start_nusyq.py", "snapshot"],
  "options": {
    "cwd": "${workspaceFolder}",
    "env": {
      "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4318",
      "NUSYQ_TRACE": "1"
    }
  }
}
```

---

## Testing Tracing

### Verify module loads

```bash
python -m pytest tests/test_imports_smoke.py::test_observability_module_import -v
```

**Expected**: ✅ PASSED (1/1)

### Smoke test with console exporter

```bash
OTEL_TRACES_EXPORTER=console python scripts/start_nusyq.py selfcheck 2>&1 | grep "trace_id"
```

**Expected output**:
```
trace_id: 0x<32-hex-chars>
```

---

## Troubleshooting

### Issue: "OpenTelemetry not installed"

**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

Or install OTEL manually:
```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-http
```

### Issue: "No data was collected" in coverage

**Solution**: Subprocess contract tests are excluded from coverage (by design).

Run unit tests separately:
```bash
pytest tests/test_imports_smoke.py --cov
```

### Issue: Spans not appearing in Jaeger

**Checklist**:
1. Collector running? `curl http://localhost:4318/v1/traces -v`
2. Environment variable set? `echo $OTEL_EXPORTER_OTLP_ENDPOINT`
3. Tracing enabled? `echo $NUSYQ_TRACE`
4. Check collector logs for errors

### Issue: "NUSYQ_TRACE=0" disables everything

**Correct**: This is intentional. To enable:
```bash
export NUSYQ_TRACE=1  # or unset NUSYQ_TRACE
```

---

## API Reference

### `init_tracing(service_name: str) -> bool`

Initialize tracer provider. Returns `True` if tracing active.

**Example**:
```python
from src.observability.otel import init_tracing

enabled = init_tracing(service_name="my-service")
if enabled:
    print("Tracing active")
```

### `start_action_span(name: str, attributes: dict | None) -> ContextManager`

Create a span with attributes. Safe no-op if tracing disabled.

**Example**:
```python
from src.observability.otel import start_action_span

with start_action_span("action.snapshot", {"repo": "NuSyQ-Hub"}) as span:
    span.set_attribute("file_count", 42)
    # Do work
```

### `flush_tracing(timeout: int = 5) -> bool`

Flush pending spans before shutdown. Returns `True` if successful.

**Example**:
```python
from src.observability.otel import flush_tracing

flush_tracing(timeout=10)  # Wait up to 10s for export
```

### `shutdown_tracing(timeout: int = 5) -> bool`

Shutdown tracer provider. Returns `True` if successful.

**Example**:
```python
from src.observability.otel import shutdown_tracing

shutdown_tracing(timeout=5)
```

### `bind_correlation_id(key: str, value: str) -> None`

Bind correlation ID to current context.

### `get_correlation_id(key: str) -> str | None`

Retrieve correlation ID.

### `get_all_correlation_ids() -> dict[str, str]`

Get all bound correlation IDs.

### `clear_correlation_ids() -> None`

Clear all correlation IDs.

---

## Next Steps

1. **Add spans to long-running loops**: `develop_system`, `auto_cycle`, `queue`
2. **Wire agent_task_router**: Add spans to `route_task()`, `submit_task()`
3. **Create trace_doctor action**: Validate OTEL env + collector reachability
4. **Metrics integration**: Add OpenTelemetry metrics alongside traces

---

**Last Updated**: 2025-12-24
**Status**: Production-ready (console + OTLP exporters operational)
**Maintainer**: NuSyQ-Hub Observability Team
