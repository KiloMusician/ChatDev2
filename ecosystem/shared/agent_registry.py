"""Agent registry — tracks all agents across the ecosystem."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, List, Optional

from .db import get_conn


def register(
    agent_id: str,
    name: str,
    repo: str,
    endpoint: Optional[str] = None,
    capabilities: Optional[List[str]] = None,
    status: str = "idle",
) -> None:
    get_conn().execute(
        """INSERT INTO agent_registry (agent_id, name, repo, endpoint, capabilities, status, last_seen)
           VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(agent_id) DO UPDATE SET
               name=excluded.name,
               repo=excluded.repo,
               endpoint=excluded.endpoint,
               capabilities=excluded.capabilities,
               status=excluded.status,
               last_seen=excluded.last_seen""",
        (
            agent_id, name, repo, endpoint,
            json.dumps(capabilities or []),
            status,
            datetime.utcnow().isoformat(),
        ),
    )
    get_conn().commit()


def heartbeat(agent_id: str, status: str = "active") -> None:
    get_conn().execute(
        "UPDATE agent_registry SET last_seen=?, status=? WHERE agent_id=?",
        (datetime.utcnow().isoformat(), status, agent_id),
    )
    get_conn().commit()


def list_agents() -> List[dict]:
    return [dict(r) for r in get_conn().execute("SELECT * FROM agent_registry ORDER BY repo, name").fetchall()]


def seed_defaults() -> None:
    defaults = [
        ("chatdev.backend", "ChatDev Backend", "ChatDev", "http://localhost:6400", ["workflow", "orchestration", "api"]),
        ("devmentor.game", "Dev-Mentor Game Engine", "Dev-Mentor", "http://localhost:8008/api", ["game", "cli", "ml", "swarm", "llm"]),
        ("devmentor.serena", "Serena Analytics", "Dev-Mentor", None, ["indexing", "search", "qa"]),
        ("devmentor.gordon", "Gordon Self-Improver", "Dev-Mentor", None, ["self-improvement", "code-gen", "testing"]),
        ("devmentor.swarm", "Swarm Controller", "Dev-Mentor", "http://localhost:8008/api", ["multi-agent", "delegation"]),
        ("nusyq_hub.spine", "NuSyQ Hub Spine", "NuSyQ-Hub", None, ["orchestration", "routing", "memory"]),
        ("concept_samurai.katana", "Katana Keeper", "CONCEPT_SAMURAI", None, ["meta", "logic", "abstraction"]),
    ]
    for d in defaults:
        try:
            register(*d)
        except Exception:
            pass
