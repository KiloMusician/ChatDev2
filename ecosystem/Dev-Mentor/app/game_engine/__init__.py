"""
Terminal Depths — Python Game Engine
Server-side port of the browser JS game logic.
Shared by: web thin-client (/game-cli/) and CLI client (python -m cli.devmentor play)
"""
from .session import SessionStore, GameSession

__all__ = ["SessionStore", "GameSession"]
