"""Legacy import redirect - Use src.LOGGING.modular_logging_system instead.

This file exists for backward compatibility with legacy code that imported
from src.LOGGING.infrastructure.modular_logging_system. All new code should import
from src.LOGGING.modular_logging_system directly.

Consolidated: 2025-12-28
Canonical location: src/LOGGING/modular_logging_system.py
"""

from src.LOGGING import modular_logging_system as _canonical
from src.LOGGING.modular_logging_system import *

__all__ = list(getattr(_canonical, "__all__", []))
