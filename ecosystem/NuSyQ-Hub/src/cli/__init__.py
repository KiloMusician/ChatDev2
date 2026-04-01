"""CLI subsystem — NuSyQ interactive command-line interface.

OmniTag: {
    "purpose": "cli_subsystem",
    "tags": ["CLI", "NuSyQ", "Interface"],
    "category": "tooling",
    "evolution_stage": "v2.0"
}
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.cli.nusyq_cli import NuSyQCLI

__all__ = ["NuSyQCLI"]


def __getattr__(name: str) -> object:
    if name == "NuSyQCLI":
        from src.cli.nusyq_cli import NuSyQCLI

        return NuSyQCLI
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
