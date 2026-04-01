"""Diagnostics subsystem — health monitoring, error reporting, and system analysis.

Provides the primary diagnostics and health-checking infrastructure:
- EcosystemStartupSentinel: startup health gating with configurable checks
- IntegratedHealthOrchestrator: unified health orchestration across all subsystems
- HealthMonitorDaemon: continuous background health monitoring
- UnifiedErrorReporter: cross-repo error aggregation and severity classification

Most diagnostics modules are CLI-oriented scripts; the classes below represent
the reusable library API exported for programmatic use.

OmniTag: {
    "purpose": "diagnostics_subsystem",
    "tags": ["Diagnostics", "Health", "Monitoring", "ErrorReporting"],
    "category": "observability",
    "evolution_stage": "v2.0"
}
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.diagnostics.ecosystem_startup_sentinel import \
        EcosystemStartupSentinel
    from src.diagnostics.health_monitor_daemon import (HealthMetrics,
                                                       HealthMonitorDaemon)
    from src.diagnostics.integrated_health_orchestrator import \
        IntegratedHealthOrchestrator
    from src.diagnostics.unified_error_reporter import (ErrorDiagnostic,
                                                        ErrorSeverity,
                                                        ErrorType, RepoScan,
                                                        UnifiedErrorReporter)

__all__ = [
    # Startup health gating
    "EcosystemStartupSentinel",
    # Error reporting
    "ErrorDiagnostic",
    "ErrorSeverity",
    "ErrorType",
    # Continuous monitoring
    "HealthMetrics",
    "HealthMonitorDaemon",
    # Orchestrated health checks
    "IntegratedHealthOrchestrator",
    "RepoScan",
    "UnifiedErrorReporter",
]


def __getattr__(name: str) -> object:
    if name == "EcosystemStartupSentinel":
        from src.diagnostics.ecosystem_startup_sentinel import \
            EcosystemStartupSentinel

        return EcosystemStartupSentinel
    if name == "IntegratedHealthOrchestrator":
        from src.diagnostics.integrated_health_orchestrator import \
            IntegratedHealthOrchestrator

        return IntegratedHealthOrchestrator
    if name in ("HealthMetrics", "HealthMonitorDaemon"):
        from src.diagnostics.health_monitor_daemon import (HealthMetrics,
                                                           HealthMonitorDaemon)

        return locals()[name]
    if name in (
        "ErrorDiagnostic",
        "ErrorSeverity",
        "ErrorType",
        "RepoScan",
        "UnifiedErrorReporter",
        "RepoName",
    ):
        from src.diagnostics.unified_error_reporter import (
            ErrorDiagnostic, ErrorSeverity, ErrorType, RepoName, RepoScan,
            UnifiedErrorReporter)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
