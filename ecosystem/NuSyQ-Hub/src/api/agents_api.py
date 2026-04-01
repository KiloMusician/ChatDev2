"""Agents API - HTTP + WebSocket endpoints for the NuSyQ-Hub agent ecosystem.

Phase 1 (HTTP): wraps AgentCommunicationHub + AgentOrchestrationHub behind REST.
Phase 3 (WebSocket): real-time agent event stream for Dev-Mentor, SimulatedVerse, etc.

HTTP Endpoints:
- GET  /api/agents/status            - Hub health + agent roster
- POST /api/agents/message           - Send inter-agent message
- GET  /api/agents/messages/{agent}  - Retrieve pending messages for agent
- POST /api/agents/orchestrate       - Route a task via AgentOrchestrationHub
- POST /api/agents/bus               - Re-publish to Dev-Mentor agent bus
- GET  /api/agents/bus/status        - Dev-Mentor relay health

WebSocket:
- WS   /api/agents/ws                - Real-time agent event stream (Phase 3 mesh)
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])

# ---------------------------------------------------------------------------
# Lazy singletons — import at first request to avoid circular-import boot pain
# ---------------------------------------------------------------------------

_comm_hub: Any = None
_orch_hub: Any = None


def _get_comm_hub() -> Any:
    global _comm_hub
    if _comm_hub is None:
        try:
            from src.agents.agent_communication_hub import (
                AgentCommunicationHub, AgentRole)

            _comm_hub = AgentCommunicationHub()
            # Ensure the core agents are registered
            for name, role_val in [
                ("claude", AgentRole.CLAUDE),
                ("copilot", AgentRole.COPILOT),
                ("chatdev", AgentRole.CHATDEV),
                ("ollama", AgentRole.OLLAMA),
                ("dev_mentor", AgentRole.CULTURE_SHIP),
            ]:
                _comm_hub.register_agent(name, role_val)
        except Exception as exc:
            logger.warning("AgentCommunicationHub unavailable: %s", exc)
            _comm_hub = None
    return _comm_hub


def _get_orch_hub() -> Any:
    global _orch_hub
    if _orch_hub is None:
        try:
            from src.agents.agent_orchestration_hub import \
                AgentOrchestrationHub

            _orch_hub = AgentOrchestrationHub()
        except Exception as exc:
            logger.warning("AgentOrchestrationHub unavailable: %s", exc)
            _orch_hub = None
    return _orch_hub


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class MessageRequest(BaseModel):
    from_agent: str = Field(..., description="Sending agent name")
    to_agent: str | None = Field(None, description="Target agent (None = broadcast)")
    message_type: str = Field(
        "request", description="request|response|broadcast|quest_complete|level_up|share_knowledge"
    )
    content: dict[str, Any] = Field(default_factory=dict)
    thread_id: str | None = None


class OrchestrationRequest(BaseModel):
    task_type: str = Field(..., description="Task category (code_review, analysis, generation, …)")
    description: str = Field(..., description="Human-readable task description")
    context: dict[str, Any] = Field(default_factory=dict)
    priority: str = Field("normal", description="low|normal|high|critical")
    target_service: str | None = None


class BusRelayRequest(BaseModel):
    from_agent: str = Field(..., description="Origin agent")
    text: str = Field(..., description="Message body")
    to_agent: str | None = None
    channel: str = Field("hive.broadcast", description="Pub/sub channel")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/status")
async def get_agents_status() -> dict[str, Any]:
    """Hub health and agent roster."""
    hub = _get_comm_hub()
    orch = _get_orch_hub()

    agents_info: dict[str, Any] = {}
    if hub:
        for name, agent in hub.agents.items():
            agents_info[name] = {
                "role": agent.role.value,
                "level": agent.stats.level,
                "xp": agent.stats.experience,
                "active": agent.active,
                "last_seen": agent.last_seen,
                "tasks_completed": agent.stats.tasks_completed,
            }

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "comm_hub": "available" if hub else "unavailable",
        "orch_hub": "available" if orch else "unavailable",
        "agents": agents_info,
        "agent_count": len(agents_info),
    }


@router.post("/message")
async def send_message(req: MessageRequest) -> dict[str, Any]:
    """Send an inter-agent message."""
    hub = _get_comm_hub()
    if not hub:
        raise HTTPException(status_code=503, detail="AgentCommunicationHub unavailable")

    try:
        from src.agents.agent_communication_hub import Message, MessageType

        msg = Message(
            id=str(uuid.uuid4()),
            from_agent=req.from_agent,
            to_agent=req.to_agent,
            message_type=MessageType(req.message_type),
            content=req.content,
            thread_id=req.thread_id,
        )
        # Ensure sender is registered
        if req.from_agent not in hub.agents:
            from src.agents.agent_communication_hub import AgentRole

            hub.register_agent(req.from_agent, AgentRole.CULTURE_SHIP)

        success = await hub.send_message(req.from_agent, msg)

        # Fan out to WebSocket clients (Phase 3 mesh)
        if success and _ws_clients:
            asyncio.create_task(
                _broadcast_agent_event(
                    {
                        "type": "agent_msg",
                        "from_agent": msg.from_agent,
                        "to_agent": msg.to_agent,
                        "message_type": msg.message_type.value,
                        "content": msg.content,
                        "timestamp": msg.timestamp,
                    }
                )
            )

        return {
            "success": success,
            "message_id": msg.id,
            "timestamp": msg.timestamp,
        }
    except Exception as exc:
        logger.exception("send_message failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/messages/{agent_name}")
async def get_messages(agent_name: str, limit: int = 20) -> dict[str, Any]:
    """Retrieve recent messages for an agent (history scan)."""
    hub = _get_comm_hub()
    if not hub:
        raise HTTPException(status_code=503, detail="AgentCommunicationHub unavailable")

    try:
        from dataclasses import asdict

        from src.agents.agent_communication_hub import MessageType

        relevant = [
            m for m in hub.message_history if m.to_agent == agent_name or m.to_agent is None
        ][-limit:]

        return {
            "agent": agent_name,
            "messages": [
                {
                    "id": m.id,
                    "from_agent": m.from_agent,
                    "to_agent": m.to_agent,
                    "message_type": m.message_type.value,
                    "content": m.content,
                    "timestamp": m.timestamp,
                }
                for m in relevant
            ],
            "count": len(relevant),
        }
    except Exception as exc:
        logger.exception("get_messages failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/orchestrate")
async def orchestrate_task(req: OrchestrationRequest) -> dict[str, Any]:
    """Route a task via AgentOrchestrationHub."""
    orch = _get_orch_hub()
    if not orch:
        raise HTTPException(status_code=503, detail="AgentOrchestrationHub unavailable")

    try:
        from src.agents.agent_orchestration_types import TaskPriority

        priority_map = {
            "low": TaskPriority.LOW,
            "normal": TaskPriority.NORMAL,
            "high": TaskPriority.HIGH,
            "critical": TaskPriority.CRITICAL,
        }
        priority = priority_map.get(req.priority.lower(), TaskPriority.NORMAL)
        result = await orch.route_task(
            task_type=req.task_type,
            description=req.description,
            context=req.context,
            priority=priority,
            target_service=req.target_service,
        )
        return result
    except Exception as exc:
        logger.exception("orchestrate_task failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/bus")
async def relay_to_bus(req: BusRelayRequest) -> dict[str, Any]:
    """Re-publish a message to the Dev-Mentor agent bus."""
    try:
        from src.integration.dev_mentor_relay import relay_to_dev_mentor

        ok = await relay_to_dev_mentor(
            from_agent=req.from_agent,
            text=req.text,
            to_agent=req.to_agent,
            channel=req.channel,
        )
        return {"success": ok, "channel": req.channel}
    except Exception as exc:
        logger.warning("Bus relay failed: %s", exc)
        return {"success": False, "error": str(exc)}


@router.get("/bus/status")
async def bus_relay_status() -> dict[str, Any]:
    """Check Dev-Mentor relay health."""
    try:
        from src.integration.dev_mentor_relay import get_dev_mentor_status

        return await get_dev_mentor_status()
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


# ---------------------------------------------------------------------------
# Phase 3: WebSocket mesh — real-time agent event stream
# ---------------------------------------------------------------------------

# In-process connection registry: set of active WebSocket connections
_ws_clients: set[WebSocket] = set()


async def _broadcast_agent_event(event: dict[str, Any]) -> None:
    """Push an event dict to all connected WebSocket clients."""
    dead: set[WebSocket] = set()
    for ws in list(_ws_clients):
        try:
            await ws.send_json(event)
        except Exception:
            dead.add(ws)
    _ws_clients.difference_update(dead)


async def agent_ws(websocket: WebSocket) -> None:
    """Registered directly on app in main.py (bypasses APIRouter WS prefix issue)."""
    """Real-time agent event stream (Phase 3 WebSocket mesh).

    Clients (Dev-Mentor, SimulatedVerse, browser extensions) connect here
    to receive live agent messages as they flow through the hub.

    Message types pushed to clients:
      {"type": "agent_msg",  "from_agent": str, "to_agent": str|null,
       "message_type": str, "content": {...}, "timestamp": str}
      {"type": "agent_join", "name": str, "role": str, "timestamp": str}
      {"type": "heartbeat",  "timestamp": str, "agent_count": int}

    Clients may also send:
      {"action": "ping"}  → server replies {"type": "pong"}
      {"action": "publish", "from_agent": str, "text": str, ...}
         → relays message back into hub and to all other clients
    """
    await websocket.accept()
    _ws_clients.add(websocket)
    logger.info("WS client connected — total: %d", len(_ws_clients))

    # Send welcome + current roster
    hub = _get_comm_hub()
    agents_snapshot = {}
    if hub:
        agents_snapshot = {
            name: {"role": a.role.value, "level": a.stats.level} for name, a in hub.agents.items()
        }
    await websocket.send_json(
        {
            "type": "connected",
            "timestamp": datetime.now().isoformat(),
            "agents": agents_snapshot,
            "client_count": len(_ws_clients),
        }
    )

    heartbeat_task: asyncio.Task[None] | None = None

    async def _heartbeat() -> None:
        while True:
            await asyncio.sleep(30)
            try:
                await websocket.send_json(
                    {
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat(),
                        "agent_count": len(hub.agents) if hub else 0,
                        "client_count": len(_ws_clients),
                    }
                )
            except Exception:
                break

    try:
        heartbeat_task = asyncio.create_task(_heartbeat())
        while True:
            raw = await websocket.receive_json()
            action = raw.get("action", "")

            if action == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})

            elif action == "publish":
                # Client-initiated message → fan out to all other WS clients
                # and optionally relay to Dev-Mentor bus
                event: dict[str, Any] = {
                    "type": "agent_msg",
                    "from_agent": raw.get("from_agent", "unknown"),
                    "to_agent": raw.get("to_agent"),
                    "message_type": raw.get("message_type", "broadcast"),
                    "content": {"text": raw.get("text", "")},
                    "timestamp": datetime.now().isoformat(),
                }
                await _broadcast_agent_event(event)
                # Also send to Dev-Mentor
                try:
                    from src.integration.dev_mentor_relay import \
                        relay_to_dev_mentor

                    await relay_to_dev_mentor(
                        from_agent=event["from_agent"],
                        text=raw.get("text", ""),
                        to_agent=event["to_agent"],
                    )
                except Exception:
                    pass

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.debug("WS client error: %s", exc)
    finally:
        _ws_clients.discard(websocket)
        if heartbeat_task:
            heartbeat_task.cancel()
        logger.info("WS client disconnected — remaining: %d", len(_ws_clients))
