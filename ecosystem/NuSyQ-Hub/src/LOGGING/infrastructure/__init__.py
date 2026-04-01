"""Legacy redirect — canonical LOGGING lives at src.LOGGING.modular_logging_system.

This sub-package exists for backward compatibility with code that imported
from src.LOGGING.infrastructure. All new code should use src.LOGGING directly.

Consolidated: 2025-12-28. Canonical: src/LOGGING/modular_logging_system.py
"""

from src.LOGGING import modular_logging_system as _canonical
from src.LOGGING.modular_logging_system import *

__all__ = list(getattr(_canonical, "__all__", []))
