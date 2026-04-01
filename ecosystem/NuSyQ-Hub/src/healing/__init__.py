"""Healing subsystem — autonomous error resolution and system repair.

Provides auto-repair capabilities for the NuSyQ ecosystem: error resolution
orchestration, issue detection and automated fixes, repository health
restoration, and quantum problem resolution using pattern matching.

OmniTag: {
    "purpose": "healing_subsystem",
    "tags": ["Healing", "ErrorResolution", "AutoRepair", "HealthRestorer"],
    "category": "healing",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

__all__ = [
    "DiagnosticIssue",
    "ErrorRecoveryMapper",
    "ErrorResolutionOrchestrator",
    "IssueResolver",
    "QuantumProblemResolver",
    "QuantumProblemState",
    "RecoveryAction",
    "RecoveryStrategy",
    "RepositoryHealthRestorer",
]


def __getattr__(name: str):
    if name == "ErrorResolutionOrchestrator":
        from src.healing.error_resolution_orchestrator import \
            ErrorResolutionOrchestrator

        return ErrorResolutionOrchestrator
    if name == "IssueResolver":
        from src.healing.automated_issue_resolver import IssueResolver

        return IssueResolver
    if name == "RepositoryHealthRestorer":
        from src.healing.repository_health_restorer import \
            RepositoryHealthRestorer

        return RepositoryHealthRestorer
    if name in ("QuantumProblemResolver", "QuantumProblemState"):
        from src.healing.quantum_problem_resolver import (
            QuantumProblemResolver, QuantumProblemState)

        return locals()[name]
    if name in ("ErrorRecoveryMapper", "DiagnosticIssue", "RecoveryAction", "RecoveryStrategy"):
        from src.healing.error_recovery_mapper import (DiagnosticIssue,
                                                       ErrorRecoveryMapper,
                                                       RecoveryAction,
                                                       RecoveryStrategy)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
