"""Compatibility shim to initialize terminal logging across repos.

Expose `init_terminal_logging(channel, level)` that tries available implementations.
"""

try:
    from .terminal_logger2 import init_terminal_logging as _init
except Exception:
    _init = None


def init_terminal_logging(channel: str = "Main", level: int = 20) -> object | None:
    """Initialize terminal logging using available adapter.

    Returns the handler object or None if not available.
    """
    if _init is None:
        return None
    return _init(channel=channel, level=level)
