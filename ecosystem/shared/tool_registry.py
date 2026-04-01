"""Tool registry — all ecosystem tools in one place."""
from __future__ import annotations

import json
from typing import Any, List, Optional

from .db import get_conn


def register(
    tool_id: str,
    name: str,
    repo: str,
    path: str = "",
    description: str = "",
    input_schema: Any = None,
) -> None:
    get_conn().execute(
        """INSERT INTO tool_registry (tool_id, name, repo, path, description, input_schema)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(tool_id) DO UPDATE SET
               name=excluded.name,
               repo=excluded.repo,
               path=excluded.path,
               description=excluded.description,
               input_schema=excluded.input_schema""",
        (tool_id, name, repo, path, description, json.dumps(input_schema or {})),
    )
    get_conn().commit()


def list_tools(repo: Optional[str] = None, enabled_only: bool = True) -> List[dict]:
    q = "SELECT * FROM tool_registry WHERE 1=1"
    args: list = []
    if repo:
        q += " AND repo=?"
        args.append(repo)
    if enabled_only:
        q += " AND enabled=1"
    return [dict(r) for r in get_conn().execute(q, args).fetchall()]


def disable(tool_id: str) -> None:
    get_conn().execute("UPDATE tool_registry SET enabled=0 WHERE tool_id=?", (tool_id,))
    get_conn().commit()


def seed_defaults() -> None:
    """Seed well-known ecosystem tools from all repos."""
    defaults = [
        ("devmentor.chug", "CHUG Cycle", "Dev-Mentor", "chug_engine.py", "Cultivation cycle runner: ASSESS→CULTIVATE→HARVEST→UPGRADE→GROW"),
        ("devmentor.game_engine", "Game Engine", "Dev-Mentor", "app/backend/main.py", "Terminal Depths FastAPI game engine, 533 commands"),
        ("devmentor.swarm", "Swarm Controller", "Dev-Mentor", "app/backend/swarm_controller.py", "Multi-agent swarm coordinator"),
        ("devmentor.lattice", "Lattice (132 infra nodes)", "Dev-Mentor", "app/backend/lattice.py", "Infrastructure node lattice"),
        ("devmentor.ml", "ML Service Registry (6 models)", "Dev-Mentor", "app/backend/ml/", "Model registry, feature store, embedder"),
        ("devmentor.serena", "Serena Analytics", "Dev-Mentor", "scripts/serena_analytics.py", "Codebase indexing and contextual Q&A"),
        ("devmentor.gordon", "Gordon Orchestrator", "Dev-Mentor", "scripts/gordon_orchestrator.py", "Self-improvement cycle runner"),
        ("devmentor.model_router", "Model Router", "Dev-Mentor", "scripts/model_router.py", "LLM model routing and dispatch"),
        ("nusyq_hub.orchestration", "Agent Orchestration Hub", "NuSyQ-Hub", "src/orchestration/agent_orchestration_hub.py", "Central agent routing hub"),
        ("nusyq_hub.task_queue", "Agent Task Queue", "NuSyQ-Hub", "src/orchestration/agent_task_queue.py", "Task prioritization and dispatch"),
        ("nusyq_hub.memory_palace", "Memory Palace", "NuSyQ-Hub", "src/memory/memory_palace.py", "Contextual memory storage and retrieval"),
        ("nusyq_hub.contextual_memory", "Contextual Memory", "NuSyQ-Hub", "src/memory/contextual_memory.py", "Session context management"),
        ("nusyq_hub.cross_sync", "Cross-Ecosystem Sync", "NuSyQ-Hub", "src/tools/cross_ecosystem_sync.py", "Repo-to-repo data synchronization"),
        ("nusyq_hub.chatdev_router", "ChatDev Autonomous Router", "NuSyQ-Hub", "src/orchestration/chatdev_autonomous_router.py", "Routes tasks to ChatDev agents"),
        ("nusyq_hub.healing", "Auto Healing", "NuSyQ-Hub", "src/orchestration/auto_healing.py", "Automatic error detection and repair"),
        ("concept_samurai.katana", "Katana Keeper", "CONCEPT_SAMURAI", "katana-keeper/", "System orchestrator and meta-logic engine"),
        ("simulatedverse.world", "World Engine", "SimulatedVerse", "app/", "RimWorld-style agent simulation"),
        ("chatdev.workflows", "Workflow Engine", "ChatDev", "server/routes/workflows.py", "Visual multi-agent workflow orchestration"),
        ("chatdev.vuegraph", "VueGraph", "ChatDev", "server/routes/vuegraphs.py", "Graph-based agent pipeline builder"),
        ("chatdev.orchestrator", "ChatDev Orchestrator", "ChatDev", "ecosystem/orchestrator.py", "Central ecosystem control layer"),
    ]
    for t in defaults:
        try:
            register(*t)
        except Exception:
            pass
