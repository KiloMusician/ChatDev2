"""CyberTerminal — virtual filesystem game loop engine.

Standalone CyberTerminal engine with virtual filesystem node tree,
interactive CLI, and immersive hacker-themed game world. Distinct from
the game-integrated cyber_terminal in src/games/ — this is the core engine.

OmniTag: {
    "purpose": "cyber_terminal_engine",
    "tags": ["CyberTerminal", "GameEngine", "VirtualFilesystem", "CLI"],
    "category": "game_systems",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

# Lazy re-exports are resolved via __getattr__; pylint cannot infer them statically.
# pylint: disable=import-outside-toplevel,possibly-unused-variable,undefined-all-variable

__all__ = ["CyberTerminal", "Node", "build_world", "run_cli"]


def __getattr__(name: str):
    if name in ("Node", "CyberTerminal", "build_world", "run_cli"):
        from src.cyber_terminal.engine import (CyberTerminal, Node,
                                               build_world, run_cli)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
