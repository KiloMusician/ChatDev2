"""Compatibility shim for the `mcp_server` package.

This attempts to import the real implementation from the sibling `NuSyQ`
workspace when available (so IDE/type-checkers can resolve symbols). If the
real package isn't importable in this environment, provide minimal
placeholders that raise clear runtime errors when used.
"""

from __future__ import annotations

__all__ = ["main", "run", "start"]

try:  # prefer explicit NuSyQ package if present in workspace
    from NuSyQ import mcp_server as _real  # type: ignore
except Exception:  # pragma: no cover - best-effort shim
    _real = None

if _real is not None:
    main = getattr(_real, "main", None)
    start = getattr(_real, "start", None)
    run = getattr(_real, "run", None)
else:

    def main(*args, **kwargs):
        raise RuntimeError(
            "NuSyQ.mcp_server is not importable in this environment;"
            " install or add the NuSyQ workspace to PYTHONPATH to use the real implementation"
        )

    start = main
    run = main
