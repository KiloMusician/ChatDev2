"""Tagging subsystem — OmniTag and MegaTag metadata systems.

Provides OmniTag (structured metadata), MegaTag (high-density symbolic
annotation), and tag validation/processing framework for the NuSyQ ecosystem.
Tags drive AI model selection, task routing, and agent coordination.

OmniTag: {
    "purpose": "tagging_subsystem",
    "tags": ["OmniTag", "MegaTag", "Metadata", "Tagging"],
    "category": "infrastructure",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

__all__ = [
    "OmniTagSystem",
    "TaggingFramework",
    "TaggingFrameworkConfig",
    "Validator",
    "enhance_context_with_tags",
    "extract_tags_from_context",
    "process_mega_tags",
    "process_omni_tags",
    "validate_tags",
]


def __getattr__(name: str):
    if name == "OmniTagSystem":
        from src.tagging.omnitag_system import OmniTagSystem

        return OmniTagSystem
    if name in ("TaggingFramework", "TaggingFrameworkConfig"):
        from src.tagging.tagging_framework import (TaggingFramework,
                                                   TaggingFrameworkConfig)

        return locals()[name]
    if name in (
        "process_omni_tags",
        "process_mega_tags",
        "validate_tags",
        "extract_tags_from_context",
        "enhance_context_with_tags",
    ):
        from src.tagging.tag_processors import (enhance_context_with_tags,
                                                extract_tags_from_context,
                                                process_mega_tags,
                                                process_omni_tags,
                                                validate_tags)

        return locals()[name]
    if name == "Validator":
        from src.tagging.validator import Validator

        return Validator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
