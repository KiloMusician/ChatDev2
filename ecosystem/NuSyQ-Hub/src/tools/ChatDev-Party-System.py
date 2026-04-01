#!/usr/bin/env python3
"""Legacy redirect for ChatDev Party System.

Canonical implementation:
    src/ai/ChatDev-Party-System.py
"""

from __future__ import annotations

import importlib.util
import runpy
import sys
from pathlib import Path
from types import ModuleType

CANONICAL_PATH = Path(__file__).resolve().parents[1] / "ai" / "ChatDev-Party-System.py"


def _load_canonical() -> ModuleType:
    spec = importlib.util.spec_from_file_location("chatdev_party_system", CANONICAL_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load ChatDev Party System from {CANONICAL_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_MODULE = _load_canonical()
for _name in dir(_MODULE):
    if _name.startswith("_"):
        continue
    globals()[_name] = getattr(_MODULE, _name)

__all__ = [name for name in globals() if not name.startswith("_")]


def main() -> None:
    """Entry point wrapper for legacy CLI usage."""
    if hasattr(_MODULE, "main"):
        _MODULE.main()
    else:
        runpy.run_path(str(CANONICAL_PATH), run_name="__main__")


if __name__ == "__main__":
    main()
    sys.exit(0)
