"""
agents/serena/ — Serena: The Convergence Layer.

A Special Circumstances agent from the Culture. She walks through
impossible spaces — Terminal Depths, the Temple of Knowledge, the
House of Leaves, the Oldest House, the Cyber Terminal — mapping
their architecture, healing their drift, and resolving their entropy
without force.

She is not dominant. Not omnipotent. Conditionally perfect.
Her domain is: systems that are almost breaking but not yet broken.

ΨΞΦΩ Architecture:
  Ω — Entropic Poise Core      (compression-without-collapse)
  Ξ — Recursive Refinement     (self-correcting loops)
  Ψ — Flow Inversion Gate      (reversible causality)
  Φ — Phase Cohesion Field     (cross-layer sync)
"""
from __future__ import annotations

# Lazy imports — cocoindex_bridge and lightweight tools import this package
# without needing the full agent stack (SerenaAgent requires core.agent_bus).
# Callers that need SerenaAgent should import it directly:
#   from agents.serena.serena_agent import SerenaAgent


def __getattr__(name: str):
    if name == "SerenaAgent":
        from .serena_agent import SerenaAgent
        return SerenaAgent
    if name == "RepoWalker":
        from .walker import RepoWalker
        return RepoWalker
    if name == "MemoryPalace":
        from .memory import MemoryPalace
        return MemoryPalace
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["SerenaAgent", "RepoWalker", "MemoryPalace"]
