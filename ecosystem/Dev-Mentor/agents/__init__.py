"""
agents/ — DevMentor 71-Agent Orchestration Framework.

Each agent is a specialized autonomous process with:
  • A personality YAML  (agents/personalities/<name>.yaml)
  • A base class        (agents/agent_base.py)
  • Optional plugins    (agents/plugins/)

Agent registry auto-discovers all .yaml files in personalities/.
"""
from __future__ import annotations

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional

from .agent_base import AgentBase, AgentPersonality, AgentStatus

_PERSONALITIES_DIR = Path(__file__).parent / "personalities"


def load_personality(name: str) -> Optional[AgentPersonality]:
    path = _PERSONALITIES_DIR / f"{name}.yaml"
    if not path.exists():
        return None
    with path.open() as fh:
        data = yaml.safe_load(fh)
    return AgentPersonality(**data)


def list_agents() -> List[str]:
    return sorted(p.stem for p in _PERSONALITIES_DIR.glob("*.yaml"))


def load_all_personalities() -> Dict[str, AgentPersonality]:
    result: Dict[str, AgentPersonality] = {}
    for path in _PERSONALITIES_DIR.glob("*.yaml"):
        try:
            with path.open() as fh:
                data = yaml.safe_load(fh)
            result[path.stem] = AgentPersonality(**data)
        except Exception:
            pass
    return result


__all__ = [
    "AgentBase",
    "AgentPersonality",
    "AgentStatus",
    "load_personality",
    "load_all_personalities",
    "list_agents",
]
