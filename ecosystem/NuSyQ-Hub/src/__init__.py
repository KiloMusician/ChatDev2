"""Compatibility shim for repo imports.

Some modules in this repository import top-level packages like `core` or
`ai` instead of `src.core` or `src.ai`. This shim helps those imports by
exposing alias modules pointing to the `src` subpackages where possible.

This file is intentionally small and defensive.
"""

import importlib
import sys


def _alias_module(alias_name: str, target: str) -> None:
    try:
        # Try to import the target module (e.g. src.core)
        mod = importlib.import_module(target)  # nosemgrep
        # Insert into sys.modules as alias_name if not already present
        if alias_name not in sys.modules:
            sys.modules[alias_name] = mod
    except Exception:
        # Best-effort aliasing only; swallow syntax/import errors from
        # partially merged modules so the rest of the package can load.
        return


# Create lightweight aliases for common top-level names
_alias_module("core", "src.core")
_alias_module("ai", "src.ai")
_alias_module("copilot", "src.copilot")

__version__ = "2.0.0"
__author__ = "KILO-FOOLISH Development Team"
