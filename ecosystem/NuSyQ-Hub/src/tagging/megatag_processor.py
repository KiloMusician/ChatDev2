"""Legacy redirect for MegaTagProcessor.

Canonical implementation:
    src/copilot/megatag_processor.py

Compatibility wrapper:
    src/core/megatag_processor.py
"""

from src.core.megatag_processor import MegaTagProcessor

__all__ = ["MegaTagProcessor"]
