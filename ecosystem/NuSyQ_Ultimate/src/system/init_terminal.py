"""Best-effort terminal logging initializer for standalone NuSyQ usage."""

from __future__ import annotations

import logging
import sys
from typing import Any, Optional

_HANDLER_PREFIX = "nusyq_terminal_"


def _resolve_level(level: Any) -> int:
    if isinstance(level, int):
        return level
    if isinstance(level, str):
        return getattr(logging, level.upper(), logging.INFO)
    return logging.INFO


def init_terminal_logging(
    channel: Optional[str] = None,
    level: Any = "INFO",
    **_kwargs: Any,
) -> Optional[logging.Handler]:
    """Attach a channel-tagged stdout handler once and return it."""
    logger = logging.getLogger()
    channel_name = (channel or "Main").strip() or "Main"
    handler_name = f"{_HANDLER_PREFIX}{channel_name}"

    for existing in logger.handlers:
        if getattr(existing, "name", None) == handler_name:
            existing.setLevel(_resolve_level(level))
            return existing

    handler = logging.StreamHandler(sys.stdout)
    handler.name = handler_name
    handler.setLevel(_resolve_level(level))
    handler.setFormatter(
        logging.Formatter(
            f"%(asctime)s [%(levelname)s] [{channel_name}] %(name)s: %(message)s"
        )
    )
    logger.addHandler(handler)
    logger.setLevel(min(logger.level or logging.INFO, handler.level))
    return handler
