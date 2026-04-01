"""KILO-FOOLISH Modular Logging System.

Provides structured logging with tags and subprocess awareness.

OmniTag: {
    "purpose": "Modular logging with semantic tags and subprocess tracking",
    "tags": ["Logging", "Python"],
    "category": "core_infrastructure",
    "evolution_stage": "v1.1",
    "notes": (
        "Added duplicate message suppression filter to reduce noisy repeats in"
        " active terminals"
    )
}
"""

import json
import logging
import logging.handlers
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

try:
    from datetime import UTC  # type: ignore[attr-defined]
except ImportError:
    UTC = timezone.utc  # noqa: UP017

logger = logging.getLogger(__name__)

StructuredFormatterType = type[Any] | None
HumanReadableFormatterType = type[Any] | None
StructuredFormatter: StructuredFormatterType
HumanReadableFormatter: HumanReadableFormatterType

if TYPE_CHECKING:
    from src.observability.structured_logging import \
        HumanReadableFormatter as _HRF
    from src.observability.structured_logging import StructuredFormatter as _SF

    StructuredFormatter = _SF
    HumanReadableFormatter = _HRF
else:  # pragma: no cover - lazy import with graceful fallback
    try:
        from src.observability.structured_logging import \
            HumanReadableFormatter as _HRF
        from src.observability.structured_logging import \
            StructuredFormatter as _SF

        StructuredFormatter = _SF
        HumanReadableFormatter = _HRF
    except ImportError:  # pragma: no cover
        StructuredFormatter = None
        HumanReadableFormatter = None


def _dedup_window_key(logger_name: str) -> str:
    """Return the environment key for a logger-specific dedup window."""
    sanitized = re.sub(r"[^\w]", "_", logger_name.upper())
    sanitized = sanitized.strip("_")
    if not sanitized:
        sanitized = "ROOT"
    return f"NU_SYG_LOG_DEDUP_WINDOW_{sanitized}"


def _dedup_window_for_logger(logger_name: str) -> float:
    """Compute the deduplication window for a given logger."""
    specific = os.getenv(_dedup_window_key(logger_name))
    if specific:
        try:
            return float(specific)
        except ValueError:
            logger.debug("Suppressed ValueError", exc_info=True)
    try:
        return float(os.getenv("NU_SYG_LOG_DEDUP_WINDOW", "2"))
    except ValueError:
        return 2.0


class DuplicateMessageFilter(logging.Filter):
    """Suppress duplicate log messages within a configurable window.

    Tracks the last emitted message (post-format) per logger+level and blocks
    repeats that occur within ``window_seconds``. This mitigates spammy output
    from frequently-updating systems (e.g., guild board status reads).
    """

    def __init__(self, window_seconds: float = 2.0, logger_name: str = "root") -> None:
        super().__init__()
        self.window_seconds = window_seconds
        self.logger_name = logger_name
        self._cache: dict[tuple[str, int, str], float] = {}

    def filter(self, record: logging.LogRecord) -> bool:
        # Use fully formatted message for accurate duplicate detection
        msg = record.getMessage()
        key = (record.name, record.levelno, msg)
        now = time.time()
        last = self._cache.get(key)
        if last is not None and (now - last) <= self.window_seconds:
            # Suppress duplicate within the window
            return False
        # Update cache and allow the record
        self._cache[key] = now
        return True


class OTELNoiseSuppressor(logging.Filter):
    """Suppress benign OpenTelemetry exporter errors when collector is unavailable.

    In development/offline mode, OTEL exporter attempts to connect to localhost:4318
    and fails. These errors are benign and expected when the collector isn't running.
    This filter suppresses them to reduce terminal noise.

    Enable via: NUSYG_SUPPRESS_OTEL_ERRORS=1 (default: enabled in dev)
    """

    # Patterns to recognize as benign OTEL errors
    BENIGN_PATTERNS: ClassVar[list] = [
        "opentelemetry.sdk._shared_internal",
        "ConnectionRefusedError",
        "Max retries exceeded",
        "Failed to establish a new connection",
        "HTTPConnectionPool(host='localhost', port=4318)",
        "target machine actively refused it",
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        # Get full message including exception info if present
        msg = record.getMessage()
        if record.exc_info:
            import traceback

            exc_text = "".join(traceback.format_exception(*record.exc_info))
            msg = f"{msg}\n{exc_text}"

        # Check if any benign pattern matches
        return all(
            not (pattern in msg or pattern in record.name) for pattern in self.BENIGN_PATTERNS
        )


def _install_duplicate_filter(logger: logging.Logger) -> None:
    """Install the duplicate message filter on all handlers for the given logger."""
    try:
        window = _dedup_window_for_logger(logger.name)
    except ValueError:
        window = 2.0
    if not any(isinstance(f, DuplicateMessageFilter) for f in logger.filters):
        logger.addFilter(
            DuplicateMessageFilter(window_seconds=window, logger_name=logger.name or "root")
        )
    for handler in logger.handlers:
        # Avoid stacking multiple filters of the same type
        if not any(isinstance(f, DuplicateMessageFilter) for f in handler.filters):
            handler.addFilter(
                DuplicateMessageFilter(
                    window_seconds=_dedup_window_for_logger(
                        f"{logger.name}.{handler.__class__.__name__}"
                    ),
                    logger_name=f"{logger.name}.{handler.__class__.__name__}",
                )
            )


def _install_otel_suppressor(logger: logging.Logger) -> None:
    """Install OTEL noise suppressor filter on all handlers for the given logger."""
    # Only install if not explicitly disabled
    if os.getenv("NUSYG_SUPPRESS_OTEL_ERRORS", "1").lower() in ("1", "true", "yes"):
        if not any(isinstance(f, OTELNoiseSuppressor) for f in logger.filters):
            logger.addFilter(OTELNoiseSuppressor())
        for handler in logger.handlers:
            # Avoid stacking multiple filters of the same type
            if not any(isinstance(f, OTELNoiseSuppressor) for f in handler.filters):
                handler.addFilter(OTELNoiseSuppressor())


# Configure base logging with duplicate suppression and OTEL noise suppression
_root_logger = logging.getLogger()
if not _root_logger.handlers:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
_install_duplicate_filter(_root_logger)
_install_otel_suppressor(_root_logger)


def get_logger(module_name: str) -> logging.Logger:
    """Get a logger for the specified module and ensure filters are installed."""
    logger = logging.getLogger(module_name)
    _install_duplicate_filter(logger)
    _install_otel_suppressor(logger)
    return logger


def get_dedup_status() -> dict[str, Any]:
    """Return deduplication details for diagnostics."""
    root_logger = logging.getLogger()
    handler_count = len(root_logger.handlers)

    handler_details = []
    for handler in root_logger.handlers:
        handler_details.append(
            {
                "handler": handler.__class__.__name__,
                "filters": [
                    f.__class__.__name__
                    for f in handler.filters
                    if isinstance(f, DuplicateMessageFilter)
                ],
            }
        )

    logger_names = [
        root_logger.name,
        *(
            name
            for name, obj in logging.Logger.manager.loggerDict.items()
            if isinstance(obj, logging.Logger)
        ),
    ]
    unique_logger_names = []
    for name in logger_names:
        if name not in unique_logger_names:
            unique_logger_names.append(name)

    logger_windows = {
        name: _dedup_window_for_logger(name or "root") for name in unique_logger_names
    }

    logger_filter_count = sum(
        1 for f in root_logger.filters if isinstance(f, DuplicateMessageFilter)
    )
    total_filter_count = logger_filter_count + sum(
        sum(1 for f in handler.filters if isinstance(f, DuplicateMessageFilter))
        for handler in root_logger.handlers
    )

    return {
        "root": root_logger.name or "root",
        "handler_count": handler_count,
        "handlers_with_filters": sum(
            1
            for handler in root_logger.handlers
            if any(isinstance(f, DuplicateMessageFilter) for f in handler.filters)
        ),
        "handler_details": handler_details,
        "logger_filter_count": logger_filter_count,
        "total_filter_count": total_filter_count,
        "window_default": _dedup_window_for_logger(root_logger.name or "root"),
        "logger_windows": logger_windows,
        "status": "active" if total_filter_count > 0 else "inactive",
    }


def log_info(module_name: str, message: str) -> None:
    """Log an info message with module context."""
    logger = logging.getLogger(module_name)
    logger.info(message)


def log_debug(module_name: str, message: str) -> None:
    """Log a debug message with module context."""
    logger = logging.getLogger(module_name)
    logger.debug(message)


def log_error(module_name: str, message: str, exc_info: bool | None = None) -> None:
    """Log an error message with module context."""
    logger = logging.getLogger(module_name)
    logger.error(message, exc_info=exc_info)


def log_warning(module_name: str, message: str) -> None:
    """Log a warning message with module context."""
    logger = logging.getLogger(module_name)
    logger.warning(message)


def log_subprocess_event(
    module_name: str,
    message: str,
    command: str | None = None,
    pid: int | None = None,
    tags: dict[str, Any] | None = None,
) -> None:
    """Log a subprocess event with metadata.

    Args:
        module_name: Name of the module logging the event
        message: Event message
        command: Command being executed (optional)
        pid: Process ID (optional)
        tags: Dictionary of metadata tags (optional)

    """
    logger = logging.getLogger(module_name)
    metadata = {
        "command": command,
        "pid": pid,
        "tags": tags or {},
        "timestamp": datetime.now(UTC).isoformat(),
    }
    logger.info("%s | Metadata: %s", message, json.dumps(metadata))


def log_tagged_event(
    module_name: str,
    message: str,
    omnitag: dict[str, Any] | None = None,
    megatag: str | dict[str, Any] | None = None,
    rshts: str | None = None,
) -> None:
    """Log an event with semantic tags (OmniTag, MegaTag, RSHTS).

    Args:
        module_name: Name of the module logging the event
        message: Event message
        omnitag: OmniTag metadata dictionary (optional)
        megatag: MegaTag string or metadata dict (optional)
        rshts: RSHTS symbolic tag (optional)

    """
    logger = logging.getLogger(module_name)
    tags: dict[str, Any] = {}
    if omnitag:
        tags["omnitag"] = omnitag
    if megatag:
        tags["megatag"] = megatag
    if rshts:
        tags["rshts"] = rshts

    logger.info("%s | Tags: %s", message, json.dumps(tags))


def log_consciousness(module_name: str, message: str, awareness_level: float = 0.0) -> None:
    """Log consciousness-related events with awareness level tracking.

    Args:
        module_name: Name of the module logging the event
        message: Consciousness event description
        awareness_level: Float 0.0-1.0 representing awareness depth

    """
    logger = logging.getLogger(module_name)
    logger.info("[CONSCIOUSNESS:%.2f] %s", awareness_level, message)


def log_cultivation(module_name: str, message: str, growth_level: float = 0.0) -> None:
    """Log cultivation and growth-related events with development tracking.

    Args:
        module_name: Name of the module logging the event
        message: Cultivation event description
        growth_level: Float 0.0-1.0 representing cultivation depth

    """
    logger = logging.getLogger(module_name)
    logger.info("[CULTIVATION:%.2f] %s", growth_level, message)


def configure_logging(level: int = logging.INFO, log_file: str | None = None) -> None:
    """Configure logging with custom level and optional file output.

    Args:
        level: Logging level (default: INFO)
        log_file: Path to log file (optional)

    """
    env_log_file = os.getenv("NUSYG_LOG_FILE")
    log_file = log_file or env_log_file
    log_format = (os.getenv("NUSYG_LOG_FORMAT") or "human").strip().lower()
    rotate_flag = os.getenv("NUSYG_LOG_ROTATE", "1" if log_file else "0").lower()
    rotate = rotate_flag in ("1", "true", "yes")

    max_bytes_env = os.getenv("NUSYG_LOG_ROTATE_MAX_BYTES")
    max_mb_env = os.getenv("NUSYG_LOG_ROTATE_MAX_MB")
    if max_bytes_env and max_bytes_env.isdigit():
        max_bytes = int(max_bytes_env)
    elif max_mb_env and max_mb_env.isdigit():
        max_bytes = int(max_mb_env) * 1024 * 1024
    else:
        max_bytes = 10 * 1024 * 1024

    backup_count_env = os.getenv("NUSYG_LOG_ROTATE_BACKUPS")
    backup_count = int(backup_count_env) if backup_count_env and backup_count_env.isdigit() else 5

    if log_format == "json" and StructuredFormatter is not None:
        formatter: logging.Formatter = StructuredFormatter(service_name="nusyq-hub")
    elif HumanReadableFormatter is not None:
        formatter = HumanReadableFormatter(include_trace=True)
    else:
        formatter = logging.Formatter(fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    handlers: list[logging.Handler] = []
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        if rotate:
            file_handler: logging.Handler = logging.handlers.RotatingFileHandler(
                filename=str(log_path),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
        else:
            file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    logging.basicConfig(level=level, handlers=handlers, force=True)
    # After reconfiguration, install filters across all handlers
    root = logging.getLogger()
    _install_duplicate_filter(root)
    _install_otel_suppressor(root)


__all__ = [
    "configure_logging",
    "get_logger",
    "log_consciousness",
    "log_debug",
    "log_error",
    "log_info",
    "log_subprocess_event",
    "log_tagged_event",
    "log_warning",
]
