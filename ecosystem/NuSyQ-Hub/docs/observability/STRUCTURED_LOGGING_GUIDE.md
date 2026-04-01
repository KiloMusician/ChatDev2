# Structured Logging Guide

**Module**: `src.observability.structured_logging`
**Purpose**: Reduce log noise, enable external log ingestion, integrate with OpenTelemetry tracing

---

## Overview

The structured logging utilities address common observability challenges:

1. **Rate Limiting**: Throttle verbose operations (per-file imports, health checks, webhooks)
2. **JSON Output**: Structured logs for external ingestion (ELK, Splunk, Datadog, etc.)
3. **Trace Correlation**: Automatic OpenTelemetry trace/span ID injection
4. **Log Rotation**: Prevent disk exhaustion in long-running processes
5. **Zero Overhead**: Lazy formatting and efficient rate limiting

---

## Quick Start

### Basic Logger Setup

```python
from src.observability.structured_logging import setup_logger

# Human-readable console logger
logger = setup_logger("my_module", level="INFO", log_format="human")
logger.info("Application started")

# JSON logger for external ingestion
json_logger = setup_logger(
    "my_module",
    level="DEBUG",
    log_format="json",
    log_file="logs/app.jsonl"
)
json_logger.info("User logged in", extra={"user_id": "123", "ip": "192.168.1.1"})
```

**Output (human)**:
```
2025-12-27 23:45:12 [INFO] my_module: Application started
```

**Output (json)**:
```json
{
  "timestamp": "2025-12-27T23:45:12.123456Z",
  "level": "INFO",
  "logger": "my_module",
  "message": "User logged in",
  "service": "nusyq-hub",
  "user_id": "123",
  "ip": "192.168.1.1",
  "source": {
    "file": "/path/to/module.py",
    "line": 42,
    "function": "login_handler"
  }
}
```

---

## Rate-Limited Logging

### Problem: Verbose Per-File Import Logs

**Before** (1000 files = 1000 log lines every run):
```python
for file in files:
    logger.debug(f"Importing {file}")
    import_module(file)
```

**After** (1 log line per file per 5 minutes):
```python
from src.observability.structured_logging import rate_limited_log, get_import_logger

logger = get_import_logger()

for file in files:
    rate_limited_log(
        logger,
        logging.DEBUG,
        f"Importing {file}",
        rate_limit_key=f"import:{file}",
        rate_limit_seconds=300,  # 5 minutes
        extra={"file": file, "module": "import_scanner"}
    )
    import_module(file)
```

**Result**: Each file logs once per 5 minutes. After suppression period:
```
2025-12-27 23:45:12 [DEBUG] nusyq.imports: Importing utils.py (suppressed 47 similar messages)
```

---

### Rate-Limiting Health Checks

**Problem**: Health check endpoints flood logs every 10 seconds

**Solution**:
```python
from src.observability.structured_logging import rate_limited_log, get_health_check_logger

logger = get_health_check_logger()

def health_check():
    status = check_system_health()

    # Log only once per 60 seconds
    rate_limited_log(
        logger,
        logging.INFO,
        f"Health check: {status}",
        rate_limit_key="health:system",
        rate_limit_seconds=60,
        extra={"status": status, "uptime": get_uptime()}
    )

    return status
```

---

### Rate-Limiting Webhook Calls

**Problem**: Webhook retry logic creates log storms

**Solution**:
```python
from src.observability.structured_logging import rate_limited_log, get_webhook_logger

logger = get_webhook_logger()

def send_webhook(url, payload):
    try:
        response = requests.post(url, json=payload)

        # Log success once per 5 minutes per URL
        rate_limited_log(
            logger,
            logging.INFO,
            f"Webhook sent to {url}",
            rate_limit_key=f"webhook:success:{url}",
            rate_limit_seconds=300,
            extra={"url": url, "status_code": response.status_code}
        )

    except Exception as e:
        # Always log errors (no rate limiting for failures)
        logger.error(
            f"Webhook failed: {url}",
            exc_info=True,
            extra={"url": url, "error": str(e)}
        )
```

---

## Operation Timing with Context Managers

### Automatic Start/End Logging with Duration

```python
from src.observability.structured_logging import log_operation, get_application_logger

logger = get_application_logger("nusyq.data_processor")

def process_file(file_path):
    with log_operation(logger, "file_processing", file=file_path, size=get_size(file_path)):
        data = read_file(file_path)
        validate_data(data)
        transform_data(data)
        save_data(data)
```

**Output**:
```
2025-12-27 23:45:12 [INFO] nusyq.data_processor: Starting file_processing
2025-12-27 23:45:15 [INFO] nusyq.data_processor: Completed file_processing in 3.142s
```

**JSON Output with trace correlation**:
```json
{
  "timestamp": "2025-12-27T23:45:15.123456Z",
  "level": "INFO",
  "logger": "nusyq.data_processor",
  "message": "Completed file_processing in 3.142s",
  "service": "nusyq-hub",
  "operation": "file_processing",
  "status": "completed",
  "duration_seconds": 3.142,
  "file": "/data/input.csv",
  "size": 1024000,
  "trace_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "span_id": "q1r2s3t4u5v6w7x8"
}
```

### Error Handling with Automatic Exception Logging

```python
def risky_operation():
    with log_operation(logger, "api_call", endpoint="/users/123"):
        response = call_external_api()
        if response.status != 200:
            raise APIError("Request failed")
        return response.data
```

**Error Output**:
```
2025-12-27 23:45:12 [ERROR] nusyq.api: Failed api_call after 0.523s: Request failed
Traceback (most recent call last):
  ...
APIError: Request failed
```

**JSON Error Output**:
```json
{
  "timestamp": "2025-12-27T23:45:12.523456Z",
  "level": "ERROR",
  "logger": "nusyq.api",
  "message": "Failed api_call after 0.523s: Request failed",
  "service": "nusyq-hub",
  "operation": "api_call",
  "status": "failed",
  "duration_seconds": 0.523,
  "endpoint": "/users/123",
  "error_type": "APIError",
  "error_message": "Request failed",
  "exception": {
    "type": "APIError",
    "message": "Request failed",
    "traceback": "Traceback (most recent call last):\n  ..."
  }
}
```

---

## OpenTelemetry Integration

### Automatic Trace Correlation

When OpenTelemetry tracing is active, all logs automatically include trace/span IDs:

```python
from src.observability.tracing import init_tracing, start_span
from src.observability.structured_logging import get_application_logger

# Initialize tracing
init_tracing(service_name="nusyq-hub", console_fallback=True)

# Setup JSON logger
logger = get_application_logger("nusyq.quest_engine", log_format="json")

def complete_quest(quest_id):
    with start_span("quest.complete", attrs={"quest_id": quest_id}):
        logger.info("Quest completion started", extra={"quest_id": quest_id})
        # ... quest completion logic ...
        logger.info("Quest completion finished", extra={"quest_id": quest_id})
```

**JSON Output with correlation**:
```json
{
  "timestamp": "2025-12-27T23:45:12.123456Z",
  "level": "INFO",
  "logger": "nusyq.quest_engine",
  "message": "Quest completion started",
  "service": "nusyq-hub",
  "quest_id": "915cf0d2",
  "trace_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "span_id": "q1r2s3t4u5v6w7x8",
  "source": {
    "file": "/src/quest_engine.py",
    "line": 42,
    "function": "complete_quest"
  }
}
```

This allows correlation in observability platforms:
- **Datadog**: Click trace ID to see all logs in that trace
- **Jaeger**: See logs inline with trace spans
- **ELK**: Filter logs by trace_id to see full request flow

---

## Log Rotation Configuration

### Prevent Disk Exhaustion

```python
from src.observability.structured_logging import setup_logger

logger = setup_logger(
    "nusyq.long_running_service",
    log_format="json",
    log_file="logs/service.jsonl",
    max_bytes=10 * 1024 * 1024,  # 10MB per file
    backup_count=5,  # Keep 5 backup files (50MB total)
)
```

**Rotation Behavior**:
- When `service.jsonl` reaches 10MB, it's renamed to `service.jsonl.1`
- Previous backups shift: `.1` → `.2`, `.2` → `.3`, etc.
- Oldest backup (`.5`) is deleted
- New `service.jsonl` starts fresh
- Total disk usage: ~50MB max

---

## Environment Configuration

### Log Level Control

```bash
# Set via environment variables
export NUSYQ_LOG_LEVEL=DEBUG
export LOG_LEVEL=INFO  # Fallback

# Or in .env file
NUSYQ_LOG_LEVEL=DEBUG
```

```python
from src.observability.structured_logging import get_log_level_from_env, setup_logger

# Automatically uses environment variable
logger = setup_logger("my_module", level=get_log_level_from_env())
```

---

## Pre-Configured Logger Instances

### Import Logger (Quieter by Default)

```python
from src.observability.structured_logging import get_import_logger, rate_limited_log

logger = get_import_logger()  # WARNING level by default

for module in modules:
    rate_limited_log(
        logger,
        logging.DEBUG,
        f"Importing {module}",
        rate_limit_key=f"import:{module}",
        rate_limit_seconds=300
    )
```

### Health Check Logger

```python
from src.observability.structured_logging import get_health_check_logger, rate_limited_log

logger = get_health_check_logger()  # WARNING level by default

def health_check_endpoint():
    rate_limited_log(
        logger,
        logging.INFO,
        "Health check passed",
        rate_limit_key="health:check",
        rate_limit_seconds=60
    )
```

### Webhook Logger

```python
from src.observability.structured_logging import get_webhook_logger

logger = get_webhook_logger()  # INFO level by default
```

---

## Real-World Usage Patterns

### Pattern 1: Quest Commit Bridge Logging

```python
from src.observability.structured_logging import get_application_logger, log_operation
from src.observability.tracing import init_tracing, start_span

# Initialize
init_tracing(service_name="nusyq-quest-bridge")
logger = get_application_logger(
    "nusyq.quest_commit_bridge",
    log_format="json",
    log_file="logs/quest_bridge.jsonl"
)

def process_commit(commit_sha):
    with start_span("commit.process", attrs={"commit_sha": commit_sha}):
        with log_operation(logger, "commit_processing", commit=commit_sha):
            message = get_commit_message(commit_sha)
            quests = extract_quest_references(message)

            logger.info(
                f"Found {len(quests)} quest references",
                extra={"commit": commit_sha, "quest_count": len(quests)}
            )

            for quest_id in quests:
                with log_operation(logger, "quest_completion", quest=quest_id):
                    complete_quest(quest_id, commit_sha)
```

### Pattern 2: Error Reporter with Rate Limiting

```python
from src.observability.structured_logging import (
    get_application_logger,
    rate_limited_log,
    log_operation
)

logger = get_application_logger("nusyq.error_reporter", log_format="json")

def scan_repository(repo_path):
    with log_operation(logger, "repository_scan", repo=repo_path):
        for file_path in get_python_files(repo_path):
            # Rate-limit per-file scan logs
            rate_limited_log(
                logger,
                logging.DEBUG,
                f"Scanning {file_path}",
                rate_limit_key=f"scan:{file_path}",
                rate_limit_seconds=600,  # Once per 10 minutes
                extra={"file": file_path}
            )

            errors = lint_file(file_path)

            if errors:
                # Always log errors (no rate limiting)
                logger.warning(
                    f"Found {len(errors)} errors in {file_path}",
                    extra={"file": file_path, "error_count": len(errors)}
                )
```

### Pattern 3: Unified AI Orchestrator

```python
from src.observability.structured_logging import (
    get_application_logger,
    rate_limited_log,
    log_operation
)

logger = get_application_logger("nusyq.orchestrator", log_format="json")

def execute_agent(agent_name, task):
    with log_operation(
        logger,
        "agent_execution",
        agent=agent_name,
        task_type=task.type
    ):
        # Rate-limit health check logs
        rate_limited_log(
            logger,
            logging.DEBUG,
            f"Agent {agent_name} health check",
            rate_limit_key=f"health:{agent_name}",
            rate_limit_seconds=120
        )

        result = agent.run(task)

        logger.info(
            f"Agent {agent_name} completed task",
            extra={
                "agent": agent_name,
                "task_id": task.id,
                "result_status": result.status
            }
        )

        return result
```

---

## Integration with Existing Tracing

### Combined Tracing + Structured Logging

```python
from src.observability.tracing import init_tracing, start_span, bind_context
from src.observability.structured_logging import get_application_logger, log_operation

# Initialize both
init_tracing(service_name="nusyq-hub", environment="production")
logger = get_application_logger(
    "nusyq.service",
    log_format="json",
    log_file="logs/service.jsonl"
)

def handle_request(user_id, request_id):
    # Bind correlation context (propagates to all logs and spans)
    bind_context(user_id=user_id, request_id=request_id)

    with start_span("request.handle", attrs={"user_id": user_id}):
        with log_operation(logger, "request_handling", user=user_id):
            # All logs will include trace_id, span_id, user_id, request_id
            logger.info("Processing request")

            result = process_request(user_id)

            logger.info("Request completed", extra={"result": result})

            return result
```

**Log Output** (automatically includes all context):
```json
{
  "timestamp": "2025-12-27T23:45:12.123456Z",
  "level": "INFO",
  "logger": "nusyq.service",
  "message": "Processing request",
  "service": "nusyq-hub",
  "user_id": "user_123",
  "request_id": "req_abc",
  "trace_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "span_id": "q1r2s3t4u5v6w7x8",
  "operation": "request_handling",
  "status": "started"
}
```

---

## Performance Considerations

### Rate Limit Cache Efficiency

- **Memory**: O(n) where n = unique rate limit keys
- **Time**: O(1) lookup per log call
- **Typical overhead**: <1μs per rate_limited_log() call

### JSON Formatting Overhead

- **Human format**: ~50-100μs per log
- **JSON format**: ~100-200μs per log
- **Recommendation**: Use JSON only for file logging, human for console

### Best Practices

1. **Rate-limit verbose operations**: imports, health checks, webhooks
2. **Never rate-limit errors**: Always log failures immediately
3. **Use log_operation for timing**: Automatic duration tracking
4. **Leverage extra fields**: Structured data for filtering/aggregation
5. **Set appropriate rotation limits**: Prevent disk exhaustion

---

## Migration from Standard Logging

### Before (stdlib logging)

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("User logged in")
logger.debug(f"Processing file {file}")  # Floods logs
```

### After (structured logging)

```python
from src.observability.structured_logging import (
    get_application_logger,
    rate_limited_log,
    log_operation
)

logger = get_application_logger(__name__, log_format="json", log_file="logs/app.jsonl")

logger.info("User logged in", extra={"user_id": user.id})

rate_limited_log(
    logger,
    logging.DEBUG,
    f"Processing file {file}",
    rate_limit_key=f"process:{file}",
    rate_limit_seconds=300
)
```

---

## Advanced: Custom Formatters

### Extend StructuredFormatter

```python
from src.observability.structured_logging import StructuredFormatter
import json

class CustomFormatter(StructuredFormatter):
    def format(self, record):
        log_data = json.loads(super().format(record))

        # Add custom fields
        log_data["environment"] = os.environ.get("ENVIRONMENT", "dev")
        log_data["hostname"] = socket.gethostname()

        return json.dumps(log_data)
```

---

## Troubleshooting

### Logs not appearing

Check log level:
```python
logger.setLevel(logging.DEBUG)  # Ensure level is appropriate
```

### Rate limiting too aggressive

Increase rate_limit_seconds or clear cache:
```python
from src.observability.structured_logging import clear_rate_limit_cache
clear_rate_limit_cache()
```

### JSON logs not parseable

Ensure extra fields are JSON-serializable:
```python
# Bad: datetime objects
logger.info("Event", extra={"timestamp": datetime.now()})

# Good: ISO format strings
logger.info("Event", extra={"timestamp": datetime.now().isoformat()})
```

---

## Summary

**Structured logging provides**:
- ✅ Rate limiting for verbose operations (-90% log volume)
- ✅ JSON output for external ingestion (ELK, Splunk, Datadog)
- ✅ Automatic OpenTelemetry correlation (trace_id, span_id)
- ✅ Log rotation to prevent disk exhaustion
- ✅ Operation timing with context managers
- ✅ Zero-overhead design with lazy formatting

**When to use**:
- Import scanning (rate-limit per file)
- Health checks (rate-limit per endpoint)
- Webhooks (rate-limit per URL)
- Long-running services (rotation required)
- Production deployments (JSON + external ingestion)

**Pattern**: Rate-limit verbosity, structure everything, correlate with traces, rotate to survive.
