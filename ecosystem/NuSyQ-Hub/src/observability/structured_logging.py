"""Structured logging utilities with rate limiting and JSON output.

Design goals:
- Rate-limit verbose operations (per-file imports, health checks, webhooks)
- Structured JSON output for external log ingestion (ELK, Splunk, etc.)
- Integration with OpenTelemetry tracing for correlation
- Log rotation configuration for long-running processes
- Minimal performance overhead with lazy formatting
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
import time
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Any

module_logger = logging.getLogger(__name__)

# Rate limiting state (key -> last_log_time)
_RATE_LIMIT_CACHE: dict[str, float] = {}
_RATE_LIMIT_COUNTERS: dict[str, int] = defaultdict(int)


class StructuredFormatter(logging.Formatter):
    """JSON formatter with OpenTelemetry correlation."""

    def __init__(self, service_name: str = "nusyq-hub", include_trace: bool = True):
        """Initialize StructuredFormatter with service_name, include_trace."""
        super().__init__()
        self.service_name = service_name
        self.include_trace = include_trace

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
        }

        # Add trace correlation if available
        if self.include_trace:
            try:
                from src.observability.tracing import current_trace_ids

                trace_id, span_id = current_trace_ids()
                if trace_id != "n/a":
                    log_data["trace_id"] = trace_id
                    log_data["span_id"] = span_id
            except Exception:
                module_logger.debug("Suppressed Exception", exc_info=True)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
            }:
                try:
                    # Ensure value is JSON serializable
                    json.dumps(value)
                    log_data[key] = value
                except (TypeError, ValueError):
                    log_data[key] = str(value)

        # Add source location
        log_data["source"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }

        return json.dumps(log_data, default=str)


class HumanReadableFormatter(logging.Formatter):
    """Human-readable formatter with optional trace correlation."""

    def __init__(self, include_trace: bool = False):
        """Initialize HumanReadableFormatter with include_trace."""
        super().__init__(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.include_trace = include_trace

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with optional trace correlation."""
        formatted = super().format(record)

        if self.include_trace:
            try:
                from src.observability.tracing import current_trace_ids

                trace_id, span_id = current_trace_ids()
                if trace_id != "n/a":
                    formatted += f" [trace_id={trace_id[:16]}... span_id={span_id[:8]}...]"
            except Exception:
                module_logger.debug("Suppressed Exception", exc_info=True)

        return formatted


def setup_logger(
    name: str,
    level: int | str = logging.INFO,
    log_format: str = "human",  # "human" or "json"
    log_file: str | Path | None = None,
    console: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB default
    backup_count: int = 5,
    service_name: str = "nusyq-hub",
) -> logging.Logger:
    """Setup a logger with structured formatting and optional rotation.

    Args:
        name: Logger name
        level: Logging level (INFO, DEBUG, etc.)
        log_format: "human" for console, "json" for ingestion
        log_file: Optional file path for file handler with rotation
        console: Whether to add console handler
        max_bytes: Max log file size before rotation (default 10MB)
        backup_count: Number of backup files to keep (default 5)
        service_name: Service name for structured logs

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logger("my_module", level="DEBUG", log_format="json")
        >>> logger.info("Processing started", extra={"user_id": "123"})
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()  # Remove existing handlers

    # Choose formatter
    formatter: StructuredFormatter | HumanReadableFormatter
    if log_format == "json":
        formatter = StructuredFormatter(service_name=service_name)
    else:
        formatter = HumanReadableFormatter(include_trace=True)

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler with rotation
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_path),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def rate_limited_log(
    logger: logging.Logger,
    level: int,
    message: str,
    rate_limit_key: str,
    rate_limit_seconds: float = 60.0,
    **kwargs: Any,
) -> bool:
    """Log a message with rate limiting.

    Args:
        logger: Logger instance
        level: Log level (logging.INFO, logging.DEBUG, etc.)
        message: Log message
        rate_limit_key: Unique key for this log message type
        rate_limit_seconds: Minimum seconds between logs with this key
        **kwargs: Extra fields to pass to logger

    Returns:
        True if logged, False if rate-limited

    Example:
        >>> logger = setup_logger("imports")
        >>> for file in files:
        ...     rate_limited_log(
        ...         logger, logging.DEBUG,
        ...         f"Importing {file}",
        ...         rate_limit_key=f"import:{file}",
        ...         rate_limit_seconds=300,  # Once per 5 minutes per file
        ...         extra={"file": file}
        ...     )
    """
    current_time = time.time()
    last_log_time = _RATE_LIMIT_CACHE.get(rate_limit_key, 0.0)

    if current_time - last_log_time < rate_limit_seconds:
        # Increment suppressed counter
        _RATE_LIMIT_COUNTERS[rate_limit_key] += 1
        return False

    # Check if we suppressed any logs
    suppressed_count = _RATE_LIMIT_COUNTERS.get(rate_limit_key, 0)
    if suppressed_count > 0:
        message += f" (suppressed {suppressed_count} similar messages)"
        _RATE_LIMIT_COUNTERS[rate_limit_key] = 0

    # Log the message
    logger.log(level, message, **kwargs)
    _RATE_LIMIT_CACHE[rate_limit_key] = current_time
    return True


@contextmanager
def log_operation(
    logger: logging.Logger,
    operation_name: str,
    level: int = logging.INFO,
    log_args: bool = False,
    **context: Any,
):
    """Context manager for logging operation start/end with timing.

    Args:
        logger: Logger instance
        operation_name: Name of the operation
        level: Log level for start/end messages
        log_args: Whether to log context arguments
        **context: Additional context fields

    Example:
        >>> logger = setup_logger("operations")
        >>> with log_operation(logger, "file_processing", file="data.csv"):
        ...     process_file("data.csv")
    """
    start_time = time.time()

    # Build start message
    start_extra = {"operation": operation_name, "status": "started"}
    start_extra.update(context)

    if log_args:
        logger.log(level, f"Starting {operation_name}", extra=start_extra)
    else:
        logger.log(level, f"Starting {operation_name}")

    try:
        yield
        # Success path
        duration = time.time() - start_time
        end_extra = {
            "operation": operation_name,
            "status": "completed",
            "duration_seconds": round(duration, 3),
        }
        end_extra.update(context)
        logger.log(level, f"Completed {operation_name} in {duration:.3f}s", extra=end_extra)

    except Exception as e:
        # Error path
        duration = time.time() - start_time
        error_extra = {
            "operation": operation_name,
            "status": "failed",
            "duration_seconds": round(duration, 3),
            "error_type": type(e).__name__,
            "error_message": str(e),
        }
        error_extra.update(context)
        logger.error(
            f"Failed {operation_name} after {duration:.3f}s: {e}",
            exc_info=True,
            extra=error_extra,
        )
        raise


def get_log_level_from_env(default: int = logging.INFO) -> int:
    """Get log level from environment variable.

    Checks NUSYQ_LOG_LEVEL or LOG_LEVEL environment variables.

    Args:
        default: Default log level if not set

    Returns:
        Log level constant (logging.INFO, logging.DEBUG, etc.)

    Example:
        >>> # With LOG_LEVEL=DEBUG in environment
        >>> level = get_log_level_from_env()
        >>> logger = setup_logger("my_module", level=level)
    """
    level_str = os.environ.get("NUSYQ_LOG_LEVEL") or os.environ.get("LOG_LEVEL")
    if not level_str:
        return default

    level_str = level_str.strip().upper()
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "WARN": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return level_map.get(level_str, default)


def clear_rate_limit_cache() -> None:
    """Clear the rate limit cache.

    Useful for testing or manual reset.
    """
    _RATE_LIMIT_CACHE.clear()
    _RATE_LIMIT_COUNTERS.clear()


# Pre-configured logger instances for common use cases
def get_import_logger(log_format: str = "human") -> logging.Logger:
    """Get a logger for import operations with rate limiting."""
    return setup_logger(
        "nusyq.imports",
        level=get_log_level_from_env(logging.WARNING),  # Quieter by default
        log_format=log_format,
    )


def get_health_check_logger(log_format: str = "human") -> logging.Logger:
    """Get a logger for health check operations with rate limiting."""
    return setup_logger(
        "nusyq.health",
        level=get_log_level_from_env(logging.WARNING),  # Quieter by default
        log_format=log_format,
    )


def get_webhook_logger(log_format: str = "human") -> logging.Logger:
    """Get a logger for webhook operations with rate limiting."""
    return setup_logger(
        "nusyq.webhooks",
        level=get_log_level_from_env(logging.INFO),
        log_format=log_format,
    )


def get_application_logger(
    name: str,
    log_format: str = "human",
    log_file: str | Path | None = None,
) -> logging.Logger:
    """Get a general application logger.

    Args:
        name: Logger name (e.g., "nusyq.quest_engine")
        log_format: "human" or "json"
        log_file: Optional log file path with rotation

    Example:
        >>> logger = get_application_logger(
        ...     "nusyq.quest_engine",
        ...     log_format="json",
        ...     log_file="logs/quest_engine.jsonl"
        ... )
    """
    return setup_logger(
        name,
        level=get_log_level_from_env(),
        log_format=log_format,
        log_file=log_file,
    )
