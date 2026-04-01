"""Aggregates API routers."""

from . import artifacts, batch, bridge, ecosystem, execute, health, nusyq_bridge, orchestrator, sessions, uploads, vuegraphs, workflows, websocket

ALL_ROUTERS = [
    health.router,
    bridge.router,
    ecosystem.router,
    nusyq_bridge.router,
    orchestrator.router,
    vuegraphs.router,
    workflows.router,
    uploads.router,
    artifacts.router,
    sessions.router,
    batch.router,
    execute.router,
    websocket.router,
]

__all__ = ["ALL_ROUTERS"]
