"""Culture Ship plugin registry.

Plugins follow the interface::

    class FooPlugin:
        name: str
        description: str
        def analyze(self, targets: list[str], dry_run: bool = False) -> dict: ...
        def fix(self, analysis: dict, dry_run: bool = False) -> dict: ...

Use :func:`get_all_plugins` to obtain a ready-to-use list of plugin instances,
or import individual classes for targeted use.
"""

from __future__ import annotations

from typing import Any

from .black_formatter import BlackFormatterPlugin
from .mypy_checker import MypyCheckerPlugin
from .pytest_runner import PytestRunnerPlugin
from .ruff_fixer import RuffFixerPlugin
from .semgrep_scanner import SemgrepScannerPlugin

__all__ = [
    "BlackFormatterPlugin",
    "MypyCheckerPlugin",
    "PytestRunnerPlugin",
    "RuffFixerPlugin",
    "SemgrepScannerPlugin",
    "get_all_plugins",
    "get_plugin",
]

# Ordered by typical Culture Ship audit sequence:
#   format → lint → type-check → test → security
_PLUGIN_REGISTRY: list[Any] = [
    BlackFormatterPlugin,
    RuffFixerPlugin,
    MypyCheckerPlugin,
    PytestRunnerPlugin,
    SemgrepScannerPlugin,
]


def get_all_plugins() -> list[Any]:
    """Return instantiated plugin objects in audit-sequence order."""
    return [cls() for cls in _PLUGIN_REGISTRY]


def get_plugin(name: str) -> Any | None:
    """Return a single instantiated plugin by name, or None if not found."""
    for cls in _PLUGIN_REGISTRY:
        instance = cls()
        if instance.name == name:
            return instance
    return None
