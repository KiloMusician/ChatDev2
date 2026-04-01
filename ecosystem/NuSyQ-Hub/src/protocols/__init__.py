"""Protocols subsystem — Kardeshev civilization healing protocols.

Defines healing and optimization protocols modeled on advanced civilization
technology frameworks. Used by the auto-repair and error resolution systems
for systematic environment healing and system optimization.

OmniTag: {
    "purpose": "protocols_subsystem",
    "tags": ["Protocols", "Healing", "Optimization", "Kardeshev"],
    "category": "healing",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

__all__ = ["CulturalElement", "KardeshevCivilization", "Technology"]


def __getattr__(name: str):
    if name in ("Technology", "CulturalElement", "KardeshevCivilization"):
        from src.protocols.healing_protocols import (CulturalElement,
                                                     KardeshevCivilization,
                                                     Technology)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
