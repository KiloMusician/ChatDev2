"""Evolution subsystem — system evolution auditing and progress tracking.

Provides consolidated system evolution tracking, progress monitoring, and
automated audit capabilities. Enables AI agents to track system growth,
identify regressions, and propose improvement strategies.

OmniTag: {
    "purpose": "evolution_subsystem",
    "tags": ["Evolution", "Auditing", "Progress", "SystemTracking"],
    "category": "observability",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

__all__ = [
    # Consolidated system
    "ConsolidatedEvolutionSystem",
    "FileSnapshot",
    "Issue",
    # Auditing
    "IssueType",
    # Progress tracking
    "ProgressTracker",
    "Proposal",
    "SystemEvolutionAuditor",
]


def __getattr__(name: str):
    if name == "ConsolidatedEvolutionSystem":
        from src.evolution.consolidated_system import \
            ConsolidatedEvolutionSystem

        return ConsolidatedEvolutionSystem
    if name == "ProgressTracker":
        from src.evolution.progress_tracker import ProgressTracker

        return ProgressTracker
    if name in ("IssueType", "FileSnapshot", "Issue", "Proposal", "SystemEvolutionAuditor"):
        from src.evolution.system_evolution_auditor import (
            FileSnapshot, Issue, IssueType, Proposal, SystemEvolutionAuditor)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
