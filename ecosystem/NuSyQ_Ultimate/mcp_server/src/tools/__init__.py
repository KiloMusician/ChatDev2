"""MCP tools for cross-repo integration.

These stubs are placeholders for Phase 3B implementations. They are kept
lightweight to avoid import-time side effects and to make it easy to wire in
real integrations later.
"""

from .nusyq_hub_client import (  # type: ignore[import-error]
    QueryKnowledgeBase,
)
from .simulatedverse_client import (  # type: ignore[import-error]
    SpawnAgentInSimulation,
)

__all__ = ["QueryKnowledgeBase", "SpawnAgentInSimulation"]
