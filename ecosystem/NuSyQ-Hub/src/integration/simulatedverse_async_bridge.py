#!/usr/bin/env python3
"""SimulatedVerse Async Bridge - Backward Compatibility Shim.

This module provides backward compatibility for code that imports from
the old simulatedverse_async_bridge module. All functionality has been
consolidated into simulatedverse_unified_bridge.

DEPRECATED: Use simulatedverse_unified_bridge.SimulatedVerseUnifiedBridge instead.

Migration:
    OLD: from src.integration.simulatedverse_async_bridge import SimulatedVerseBridge
    NEW: from src.integration.simulatedverse_unified_bridge import SimulatedVerseUnifiedBridge

    or use the alias:
    from src.integration.simulatedverse_unified_bridge import (
        SimulatedVerseUnifiedBridge as SimulatedVerseBridge
    )
"""

import warnings

from src.integration.simulatedverse_unified_bridge import (
    AgentHealth, BatchSubmission, SimulatedVerseUnifiedBridge, TaskResult,
    create_simulatedverse_bridge)

# Backward compatibility alias
SimulatedVerseBridge = SimulatedVerseUnifiedBridge

# Show deprecation warning when imported
warnings.warn(
    "simulatedverse_async_bridge is deprecated. Use simulatedverse_unified_bridge.SimulatedVerseUnifiedBridge instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "AgentHealth",
    "BatchSubmission",
    "SimulatedVerseBridge",  # Deprecated alias
    "SimulatedVerseUnifiedBridge",  # Preferred
    "TaskResult",
    "create_simulatedverse_bridge",
]
