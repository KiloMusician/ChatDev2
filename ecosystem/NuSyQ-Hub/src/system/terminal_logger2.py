"""Logging adapter that forwards Python logging records to TerminalManager.

Usage:
  from src.system.terminal_logger2 import init_terminal_logging
  init_terminal_logging(channel='Main')

This attaches a logging.Handler to the root logger that forwards structured
log records into the TerminalManager channels as JSON entries.
"""

from __future__ import annotations

import contextlib
import logging

try:
    from .enhanced_terminal_ecosystem import TerminalManager
except Exception:
    TerminalManager = None


class TerminalLogHandler(logging.Handler):
    """Best-effort logging handler that forwards records to TerminalManager.

    If TerminalManager isn't available, this handler is a no-op for forwarded
    channels and won't raise during emit.
    """

    def __init__(self, channel: str = "Main") -> None:
        """Initialize TerminalLogHandler with channel."""
        super().__init__()
        self.channel = channel
        self.tm = TerminalManager.get_instance() if TerminalManager else None

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            level = record.levelname.lower()
            meta = {
                "logger": record.name,
                "filename": getattr(record, "pathname", None),
                "lineno": getattr(record, "lineno", None),
            }
            if self.tm:
                # forward to configured channel
                self.tm.send(self.channel, level, msg, meta=meta)
                # mirror errors to canonical Errors channel
                if level in ("error", "critical"):
                    self.tm.send("Errors", "error", msg, meta=meta)
        except Exception:
            # avoid logging causing process failure
            with contextlib.suppress(Exception):
                logging.getLogger(__name__).exception("TerminalLogHandler emit failed")


def init_terminal_logging(
    channel: str = "Main", level: int = logging.INFO
) -> TerminalLogHandler | None:
    """Attach TerminalLogHandler to the root logger. Returns handler or None.

    Non-fatal: if TerminalManager unavailable, returns None.
    """
    if TerminalManager is None:
        return None
    handler = TerminalLogHandler(channel=channel)
    handler.setLevel(level)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(fmt)
    logging.getLogger().addHandler(handler)
    return handler
