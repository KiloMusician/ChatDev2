"""Compatibility shim for `mcp_registry_loader`.

Provides a `load_registry` function that forwards to known locations under the
`NuSyQ` workspace when available; falls back to a safe no-op that returns an
empty registry dict for static checks and tests that don't require the real
registry implementation.
"""

from __future__ import annotations

__all__ = ["load_registry"]

_real = None
try:
    import NuSyQ.mcp_registry_loader as _real  # type: ignore
except Exception:
    try:
        # some layouts put the loader under NuSyQ.mcp_server
        from NuSyQ.mcp_server import \
            mcp_registry_loader as _real  # type: ignore
    except Exception:
        _real = None

if _real is not None:
    load_registry = getattr(_real, "load_registry", lambda *a, **k: {})
else:

    def load_registry(*args, **kwargs):
        """Fallback minimal loader returning an empty registry."""
        return {}
