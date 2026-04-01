"""Automation subsystem — autonomous loops, monitors, and theater auditing.

Provides long-running autonomous operation cycles, system monitors, and
theater-style auditing of agent activity across the NuSyQ ecosystem.

OmniTag: {
    "purpose": "automation_subsystem",
    "tags": ["Automation", "Autonomous", "Monitoring", "Audit"],
    "category": "orchestration",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.automation.auto_theater_audit import AutoTheaterAuditor
    from src.automation.autonomous_loop import AutonomousLoop
    from src.automation.autonomous_monitor import AutonomousMonitor

__all__ = ["AutoTheaterAuditor", "AutonomousLoop", "AutonomousMonitor"]


def __getattr__(name: str):
    if name == "AutonomousLoop":
        from src.automation.autonomous_loop import AutonomousLoop

        return AutonomousLoop
    if name == "AutonomousMonitor":
        from src.automation.autonomous_monitor import AutonomousMonitor

        return AutonomousMonitor
    if name == "AutoTheaterAuditor":
        from src.automation.auto_theater_audit import AutoTheaterAuditor

        return AutoTheaterAuditor
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
