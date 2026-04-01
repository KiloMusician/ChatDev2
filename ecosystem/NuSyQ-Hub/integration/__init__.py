"""Compatibility package for legacy ``integration.*`` imports.

This package augments its module search path to include ``src/integration`` so
older import paths continue to work even when the top-level ``integration``
package is imported first.
"""

from __future__ import annotations

from pathlib import Path
from pkgutil import extend_path

# Keep namespace-style behavior for compatibility with existing tooling.
__path__ = extend_path(__path__, __name__)  # type: ignore[name-defined]

_src_integration = Path(__file__).resolve().parents[1] / "src" / "integration"
if _src_integration.exists():
    _src_path = str(_src_integration)
    if _src_path not in __path__:
        __path__.append(_src_path)
