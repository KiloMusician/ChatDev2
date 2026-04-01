"""ΞNuSyQ pipeline DSL package.

Small, lightweight pipeline primitives inspired by the 'ΞNuSyQ Mesh' design.
"""

from .pipeline import (Gate, Shadow, Step,  # re-export common symbols
                       merge_shadow)

__all__ = [
    # Typestates (lazy)
    "Bound",
    "Closed",
    "Frame",
    # Pipeline primitives (direct)
    "Gate",
    "Shadow",
    "Step",
    "Walked",
    "bind",
    "merge_shadow",
]


def __getattr__(name: str) -> object:
    if name in ("Frame", "Bound", "Walked", "Closed", "bind"):
        from src.xi_nusyq.typestates import Bound, Closed, Frame, Walked, bind

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
