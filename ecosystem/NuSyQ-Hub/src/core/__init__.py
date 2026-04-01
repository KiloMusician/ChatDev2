"""Core system components and base classes.

This module provides the foundational utilities for NuSyQ-Hub:
- Result: Unified result type for consistent API responses
- safe_import: Safe import with fallback support
- SystemBootstrap: Unified system initialization
"""

from .bootstrap import SystemBootstrap, get_bootstrap, quick_boot
from .imports import (get_ai_council, get_ai_intermediary,
                      get_background_orchestrator, get_chatdev_router,
                      get_connector_registry, get_quest_engine,
                      get_smart_search, get_sns_converter, get_test_loop,
                      get_workflow_engine, get_zero_token_bridge,
                      import_status, lazy_import, safe_import)
from .orchestrate import NuSyQOrchestrator, nusyq
from .result import Fail, Ok, Result

__all__ = [
    "Fail",
    "NuSyQOrchestrator",
    "Ok",
    # Result types
    "Result",
    # Bootstrap
    "SystemBootstrap",
    "get_ai_council",
    "get_ai_intermediary",
    "get_background_orchestrator",
    "get_bootstrap",
    "get_chatdev_router",
    "get_connector_registry",
    "get_quest_engine",
    # Component getters
    "get_smart_search",
    "get_sns_converter",
    "get_test_loop",
    "get_workflow_engine",
    "get_zero_token_bridge",
    "import_status",
    "lazy_import",
    # Orchestrator
    "nusyq",
    "quick_boot",
    # Import utilities
    "safe_import",
]

"""
OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""
