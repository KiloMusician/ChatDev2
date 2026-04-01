"""
core — Meta-awareness layer for the Terminal Depths / DevMentor ecosystem.

Offline-first. Zero AI required. Pure stdlib.

  from core.environment import get_environment
  from core.suggest     import get_suggester
"""

from .environment import Environment, get_environment, RuntimeInfo, SiblingRepo, ServiceProbe
from .suggest import Suggester, get_suggester

__all__ = [
    "Environment", "get_environment", "RuntimeInfo", "SiblingRepo", "ServiceProbe",
    "Suggester", "get_suggester",
]
