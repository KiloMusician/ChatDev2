"""Validation subsystem — symbolic protocol linting and enforcement.

Validates and enforces OmniTag/MegaTag/RSHTS symbolic protocols with
syntax validation, semantic consistency checks, and auto-fix suggestions.
Provides CI/CD integration hooks for tag compliance.

OmniTag: {
    "purpose": "validation_subsystem",
    "tags": ["Validation", "SymbolicProtocols", "OmniTag", "CodeQuality"],
    "category": "quality_assurance",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

__all__ = [
    "MegaTagValidator",
    "OmniTagValidator",
    "RSHTSValidator",
    "SymbolicProtocolValidator",
    "TagType",
    "ValidationIssue",
    "ValidationLevel",
]


def __getattr__(name: str):
    if name in (
        "TagType",
        "ValidationLevel",
        "ValidationIssue",
        "OmniTagValidator",
        "MegaTagValidator",
        "RSHTSValidator",
        "SymbolicProtocolValidator",
    ):
        from src.validation.symbolic_protocol_validator import (
            MegaTagValidator, OmniTagValidator, RSHTSValidator,
            SymbolicProtocolValidator, TagType, ValidationIssue,
            ValidationLevel)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
