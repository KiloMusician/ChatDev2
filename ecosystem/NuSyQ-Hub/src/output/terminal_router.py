#!/usr/bin/env python3
"""Terminal Routing Hints.

Provides lightweight channel hints so task outputs can be directed to themed terminals.
Usage: emit_route("METRICS") or emit_route(Channel.METRICS).
"""

import logging
from enum import Enum

logger = logging.getLogger(__name__)


class Channel(str, Enum):
    METRICS = "METRICS"
    AGENTS = "AGENTS"
    TASKS = "TASKS"
    ERRORS = "ERRORS"
    SUGGESTIONS = "SUGGESTIONS"
    ZETA = "ZETA"
    ANOMALIES = "ANOMALIES"
    FUTURE = "FUTURE"
    MAIN = "MAIN"


_PREFIX = {
    Channel.METRICS: "📊",
    Channel.AGENTS: "🤖",
    Channel.TASKS: "✓",
    Channel.ERRORS: "🔥",
    Channel.SUGGESTIONS: "💡",
    Channel.ZETA: "🎯",
    Channel.ANOMALIES: "⚡",
    Channel.FUTURE: "🔮",
    Channel.MAIN: "🏠",
}


def emit_route(channel: Channel | str, message: str | None = None) -> None:
    """Print a standardized routing hint header for terminal grouping."""
    try:
        chan = Channel(channel) if isinstance(channel, str) else channel
    except Exception:
        chan = Channel.MAIN

    prefix = _PREFIX.get(chan, "🏠")
    header = f"[ROUTE {chan.value}] {prefix}"
    logger.info(header)
    if message:
        logger.info(message)
