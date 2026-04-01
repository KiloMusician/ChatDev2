"""Culture Ship — Strategic health probes and plugin-based fixers.

OmniTag: {
    "purpose": "culture_ship_subsystem",
    "tags": ["CultureShip", "HealthProbe", "Plugins", "StrategicAdvisor"],
    "category": "orchestration",
    "evolution_stage": "v2.0"
}

Note: This module uses __getattr__ for lazy imports. Pylint E0603 warnings
about undefined names in __all__ are false positives.
"""

# pylint: disable=E0603

from __future__ import annotations

__all__ = [
    # Terminal (lazy)
    "CultureShipContext",
    "CultureShipTerminal",
    # Health probe (lazy)
    "check_dependencies",
    "generate_recommendations",
    "run_health_probe",
]


def __getattr__(name: str) -> object:
    if name in ("check_dependencies", "generate_recommendations", "run_health_probe"):
        from src.culture_ship import health_probe as _hp

        mapping = {
            "check_dependencies": _hp.check_dependencies,
            "generate_recommendations": _hp.generate_recommendations,
            "run_health_probe": _hp.run,
        }
        return mapping[name]
    if name in ("CultureShipContext", "CultureShipTerminal"):
        from src.culture_ship.integrated_terminal import (CultureShipContext,
                                                          CultureShipTerminal)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
