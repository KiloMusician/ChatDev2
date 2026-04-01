"""KILO-FOOLISH Modular Logging System.

Provides structured logging with tags and subprocess awareness.
"""

from .modular_logging_system import (configure_logging, log_consciousness,
                                     log_cultivation, log_debug, log_error,
                                     log_info, log_subprocess_event,
                                     log_tagged_event, log_warning)

__all__ = [
    "configure_logging",
    "log_consciousness",
    "log_cultivation",
    "log_debug",
    "log_error",
    "log_info",
    "log_subprocess_event",
    "log_tagged_event",
    "log_warning",
]
