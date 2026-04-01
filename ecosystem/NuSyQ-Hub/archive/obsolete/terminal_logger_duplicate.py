"""Terminal logging adapter

Provides a small, resilient logging.Handler that forwards Python logging
records into the `TerminalManager` channels as structured JSON entries.

This module is best-effort: if the TerminalManager import fails at
runtime, the adapter becomes a no-op and `init_terminal_logging` returns
None so callers can continue without errors.
"""

from __future__ import annotations

import logging
from typing import Optional

try:
    from .enhanced_terminal_ecosystem import TerminalManager
except Exception:  # pragma: no cover - optional
    TerminalManager = None


class TerminalLogHandler(logging.Handler):
    """Best-effort logging handler that forwards records to TerminalManager.

    If TerminalManager isn't available, emit() is a no-op.
    """

    def __init__(self, channel: str = "Main") -> None:
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
                self.tm.send(self.channel, level, msg, meta=meta)
                if level in ("error", "critical"):
                    # also mirror to canonical Errors channel
                    try:
                        self.tm.send("Errors", "error", msg, meta=meta)
                    except Exception:
                        pass
        except Exception:
            # Ensure logging failures don't crash the host process
            try:
                logging.getLogger(__name__).exception("TerminalLogHandler emit failed")
            except Exception:
                pass


def init_terminal_logging(
    channel: str = "Main", level: int = logging.INFO
) -> Optional[TerminalLogHandler]:
    """Attach TerminalLogHandler to the root logger and return it.

    Returns None if TerminalManager is not available.
    """
    if TerminalManager is None:
        return None
    handler = TerminalLogHandler(channel=channel)
    handler.setLevel(level)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(fmt)
    logging.getLogger().addHandler(handler)
    return handler
