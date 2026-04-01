#!/usr/bin/env python3
import os
import sys

# Ensure src/ is on sys.path for both direct and module execution
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
"""Multi-AI Orchestrator - Redirect Bridge to Unified AI Orchestrator.

LEGACY IMPORT COMPATIBILITY LAYER
=================================
This module provides backward compatibility for code importing from:
    from src.orchestration.multi_ai_orchestrator import MultiAIOrchestrator

All imports are redirected to the canonical unified orchestrator:
    src/orchestration/unified_ai_orchestrator.py (UnifiedAIOrchestrator)

This allows gradual migration of old code without breaking changes.

CONSOLIDATION STATUS: ✅ Phase 2 Complete
- Canonical: UnifiedAIOrchestrator (src/orchestration/unified_ai_orchestrator.py)
- Redirect: MultiAIOrchestrator (this file)
- Imports Updated: 10+ files
- Legacy Support: Full backward compatibility
"""


import logging

# Redirect to canonical unified orchestrator
try:
    from src.orchestration.unified_ai_orchestrator import (
        AISystemType, MultiAIOrchestrator, OrchestrationTask, TaskPriority,
        TaskStatus, UnifiedAIOrchestrator)
except ImportError as e:
    logging.warning(f"Failed to import from unified_ai_orchestrator: {e}")
    raise

# For compatibility with old get_multi_ai_orchestrator function
_orchestrator_instance = None


def get_multi_ai_orchestrator() -> MultiAIOrchestrator:
    """Get or create singleton multi-AI orchestrator instance.

    Legacy compatibility function. New code should use UnifiedAIOrchestrator directly.

    Returns:
        MultiAIOrchestrator instance (actually UnifiedAIOrchestrator)
    """
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = UnifiedAIOrchestrator()
    return _orchestrator_instance


__all__ = [
    "AISystemType",
    "MultiAIOrchestrator",
    "OrchestrationTask",
    "TaskPriority",
    "TaskStatus",
    "UnifiedAIOrchestrator",
    "get_multi_ai_orchestrator",
]
