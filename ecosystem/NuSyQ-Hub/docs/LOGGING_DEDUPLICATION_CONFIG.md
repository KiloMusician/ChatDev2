# Logging Deduplication & Noise Suppression Configuration

## Overview

NuSyQ-Hub includes two complementary logging filters:

1. **DuplicateMessageFilter** — Prevents repeated identical messages within a
   time window
2. **OTELNoiseSuppressor** — Suppresses benign OpenTelemetry exporter errors in
   dev mode

Together, they keep terminal output clean while preserving legitimate
diagnostics.

## DuplicateMessageFilter

### How It Works

Tracks recently-emitted messages (post-format) per logger+level and blocks
repeats within a configurable window. This mitigates spammy output from
frequently-updating systems (e.g., "Guild board loaded..." every few seconds).

**Key Features:**

- Windowed deduplication (default: 2 seconds)
- Per-logger/handler tracking
- Minimal performance overhead
- Configurable via environment variable

### Configuration

```bash
NU_SYQ_LOG_DEDUP_WINDOW=<seconds>
```

- **Default:** 2 seconds
- **Type:** Float (supports fractional seconds)
- **Scope:** Applies to all loggers in both logging modules
- **Per-logger overrides:** Set `NU_SYG_LOG_DEDUP_WINDOW_<LOGGER_NAME>` to override the
  default window for a specific logger. Replace dots with underscores and uppercase
  the name (e.g., `NU_SYG_LOG_DEDUP_WINDOW_SRC_GUILD_BOARD`).

### Example Usage

```bash
# Use the default 2-second window
python scripts/start_nusyq.py guild_status

# Use a 5-second window (less aggressive suppression)
set NU_SYQ_LOG_DEDUP_WINDOW=5
python scripts/start_nusyq.py guild_status

# Disable deduplication by using a very large window
set NU_SYQ_LOG_DEDUP_WINDOW=999999
python scripts/start_nusyq.py guild_status

# In .env file (permanent)
NU_SYQ_LOG_DEDUP_WINDOW=3
```

## OTELNoiseSuppressor

### How It Works

Recognizes benign OpenTelemetry exporter errors (connection refused,
localhost:4318 unavailable, etc.) and suppresses them. In offline/development
mode without a running telemetry collector, these errors are expected and
harmless.

**Key Features:**

- Suppresses only recognized benign patterns
- Preserves legitimate OTEL and other errors
- Minimal performance overhead
- Can be disabled if you need full OTEL diagnostics

### Configuration

```bash
NUSYG_SUPPRESS_OTEL_ERRORS=<0|1|true|false>
```

- **Default:** 1 (enabled)
- **Type:** Boolean-like (0/1 or true/false)
- **Scope:** Applies to both logging modules

### Example Usage

```bash
# Use default (suppression enabled)
python scripts/start_nusyq.py guild_status

# Disable suppression to see all OTEL errors
set NUSYG_SUPPRESS_OTEL_ERRORS=0
python scripts/start_nusyq.py guild_status

# In .env file (permanent)
NUSYG_SUPPRESS_OTEL_ERRORS=1
```

## Benign OTEL Patterns Suppressed

The OTELNoiseSuppressor recognizes these patterns as safe to ignore:

- `opentelemetry.sdk._shared_internal` (logger name)
- `ConnectionRefusedError` (exception type)
- `Max retries exceeded` (HTTP client error)
- `Failed to establish a new connection` (network error)
- `HTTPConnectionPool(host='localhost', port=4318)` (collector endpoint)
- `target machine actively refused it` (Windows-specific connection error)

If you see OTEL errors matching these patterns, they are benign when the
collector isn't running.

## Implementation Details

### Affected Modules

- `src/LOGGING/modular_logging_system.py` — Core modular logging
- `src/LOGGING/infrastructure/modular_logging_system.py` —
  Infrastructure/structured logging

### Filter Installation Points

1. **Root Logger:** Installed during `configure_logging()`
2. **Module Loggers:** Installed during `get_logger(module_name)` calls
3. **Per-Handler:** Attached to all handlers for comprehensive coverage

### Message Key for Deduplication

The DuplicateMessageFilter deduplicates based on:

- Logger name
- Log level (INFO, WARNING, ERROR, etc.)
- Formatted message string

This ensures that the same message from different loggers or at different levels
is treated separately.

## Verification

To verify both filters are working:

```bash
# Run guild status (should show single "Guild board loaded" line, no OTEL errors)
python scripts/start_nusyq.py guild_status

# Wait longer than dedup window
sleep 3

# Run again (message should appear again after window expires)
python scripts/start_nusyq.py guild_status
```

## Troubleshooting

### Still Seeing Repeated Messages?

- **Check window setting:** Is `NU_SYQ_LOG_DEDUP_WINDOW` set to a very large
  value?
- **Different loggers:** If the message comes from different logger instances,
  each may have its own dedup window.
- **Message formatting:** Slight variations in message text (e.g., different
  counts) will bypass deduplication.
- **Status command:** Run `python scripts/start_nusyq.py log_dedup_status` to
  inspect handler coverage, per-logger overrides, and the overall dedup status
  that is now reported in detail.

### Still Seeing OTEL Errors?

- **Check suppression setting:** Is `NUSYG_SUPPRESS_OTEL_ERRORS=0`?
- **Run OTEL collector:** Start the observability stack to accept OTEL exports
  and prevent errors:
  ```bash
  python scripts/start_nusyq.py  # Or run "Observability: Up (Collector+UI)" VS Code task
  ```

### Want to See All Messages?

```bash
# Disable duplicate suppression
set NU_SYQ_LOG_DEDUP_WINDOW=999999

# Disable OTEL suppression
set NUSYG_SUPPRESS_OTEL_ERRORS=0
```

## Related Files & Commits

- Commit `d50e2a8` — "logging: add duplicate message suppression filter"
- Commit `a852815` — "logging: add OTEL exporter error suppression"
- Source: `src/guild/guild_board.py` — Guild board status logger
- Configuration: `.env` in NuSyQ-Hub root (if present)
