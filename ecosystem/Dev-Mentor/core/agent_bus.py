"""
Agent bus — thin compatibility layer over the existing lattice Redis channels.

This does not replace the current pub/sub surface. It standardizes it so agents
can share one envelope, registry path, and heartbeat loop.
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Iterable, Optional

from app.backend import service_registry

LOG = logging.getLogger("agent_bus")


@dataclass
class MeshMessage:
    id: str
    type: str
    sender: str
    recipient: str
    payload: dict[str, Any]
    timestamp: float
    channel: str = ""
    session: str = ""
    context: str = ""
    tags: list[str] = field(default_factory=list)
    correlation_id: str = ""

    @classmethod
    def create(cls, **kwargs: Any) -> "MeshMessage":
        kwargs.setdefault("id", f"msg⛛{{{uuid.uuid4()}}}")
        kwargs.setdefault("timestamp", time.time())
        kwargs.setdefault("tags", [])
        kwargs.setdefault("payload", {})
        return cls(**kwargs)

    @classmethod
    def from_raw(cls, raw: str) -> "MeshMessage":
        data = json.loads(raw)
        return cls(
            id=data.get("id", f"msg⛛{{{uuid.uuid4()}}}"),
            type=data.get("type", "event"),
            sender=data.get("sender", "unknown"),
            recipient=data.get("recipient", ""),
            payload=data.get("payload") or {},
            timestamp=float(data.get("timestamp", time.time())),
            channel=data.get("channel", ""),
            session=data.get("session", ""),
            context=data.get("context", ""),
            tags=list(data.get("tags") or []),
            correlation_id=data.get("correlation_id", ""),
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self))


class AgentBus:
    HEARTBEAT_CHANNEL = "lattice.agent.heartbeat"
    TASK_CHANNEL = "lattice.agent.task"
    RESULT_CHANNEL = "lattice.agent.result"

    def __init__(
        self,
        agent_id: str,
        capabilities: Optional[list[str]] = None,
        *,
        tags: Optional[list[str]] = None,
        description: str = "",
        kind: str = "agent",
        redis_url: Optional[str] = None,
    ) -> None:
        self.agent_id = agent_id
        self.capabilities = capabilities or []
        self.tags = tags or []
        self.description = description
        self.kind = kind
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._redis = None
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._connect()

    @staticmethod
    def personal_channel(agent_id: str) -> str:
        return f"lattice.agent.personal.{agent_id}"

    def _connect(self) -> None:
        try:
            import redis

            self._redis = redis.from_url(self.redis_url, decode_responses=True)
            self._redis.ping()
        except Exception as exc:
            self._redis = None
            LOG.warning("AgentBus Redis unavailable for %s: %s", self.agent_id, exc)

    @property
    def connected(self) -> bool:
        return self._redis is not None

    def register(self, metadata: Optional[dict[str, Any]] = None) -> None:
        service_registry.register_agent(
            agent_id=self.agent_id,
            name=self.agent_id,
            kind=self.kind,
            capabilities=self.capabilities,
            channels=[
                self.personal_channel(self.agent_id),
                self.TASK_CHANNEL,
                self.RESULT_CHANNEL,
                self.HEARTBEAT_CHANNEL,
            ],
            tags=self.tags,
            description=self.description,
            metadata=metadata or {},
        )

    def heartbeat(self, status: str = "online", extra: Optional[dict[str, Any]] = None) -> None:
        payload = {
            "status": status,
            "capabilities": self.capabilities,
            "tags": self.tags,
            "extra": extra or {},
        }
        if not service_registry.heartbeat_agent(self.agent_id, status=status, metadata=payload):
            self.register(metadata=payload)
        self.publish(
            self.HEARTBEAT_CHANNEL,
            MeshMessage.create(
                type="event",
                sender=self.agent_id,
                recipient=self.HEARTBEAT_CHANNEL,
                payload=payload,
                tags=["heartbeat", *self.tags],
            ),
        )

    def start_heartbeat_loop(self, interval_s: int = 30, extra_factory: Optional[Callable[[], dict[str, Any]]] = None) -> None:
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            return

        def _loop() -> None:
            while not self._stop_event.is_set():
                try:
                    self.heartbeat(extra=extra_factory() if extra_factory else None)
                except Exception as exc:
                    LOG.debug("Heartbeat loop failed for %s: %s", self.agent_id, exc)
                self._stop_event.wait(interval_s)

        self._heartbeat_thread = threading.Thread(
            target=_loop,
            daemon=True,
            name=f"{self.agent_id}-heartbeat",
        )
        self._heartbeat_thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def publish(self, channel: str, message: MeshMessage | dict[str, Any]) -> Optional[MeshMessage]:
        if not self.connected or self._redis is None:
            return None
        if isinstance(message, MeshMessage):
            msg = message
        else:
            msg = MeshMessage.create(
                type=message.get("type", "event"),
                sender=message.get("sender", self.agent_id),
                recipient=message.get("recipient", channel),
                payload=message.get("payload", {}),
                channel=channel,
                session=message.get("session", ""),
                context=message.get("context", ""),
                tags=list(message.get("tags") or []),
                correlation_id=message.get("correlation_id", ""),
            )
        if not msg.channel:
            msg.channel = channel
        self._redis.publish(channel, msg.to_json())
        return msg

    def request(
        self,
        recipient: str,
        payload: dict[str, Any],
        *,
        channel: Optional[str] = None,
        session: str = "",
        context: str = "",
        tags: Optional[list[str]] = None,
        correlation_id: str = "",
    ) -> MeshMessage:
        target_channel = channel or self.personal_channel(recipient)
        msg = MeshMessage.create(
            type="request",
            sender=self.agent_id,
            recipient=recipient,
            payload=payload,
            channel=target_channel,
            session=session,
            context=context,
            tags=tags or [],
            correlation_id=correlation_id,
        )
        self.publish(target_channel, msg)
        return msg

    def respond(
        self,
        request: MeshMessage,
        payload: dict[str, Any],
        *,
        channel: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> MeshMessage:
        target_channel = channel or self.personal_channel(request.sender)
        response = MeshMessage.create(
            type="response",
            sender=self.agent_id,
            recipient=request.sender,
            payload=payload,
            channel=target_channel,
            session=request.session,
            context=request.context,
            tags=tags or [],
            correlation_id=request.id,
        )
        self.publish(target_channel, response)
        self.publish(self.RESULT_CHANNEL, response)
        return response

    def listen_forever(
        self,
        channels: Iterable[str],
        handler: Callable[[MeshMessage, str], None],
        *,
        patterns: bool = False,
    ) -> None:
        if not self.connected or self._redis is None:
            raise RuntimeError("Redis is unavailable for AgentBus listener")

        pubsub = self._redis.pubsub()
        channel_list = list(channels)
        if patterns:
            pubsub.psubscribe(*channel_list)
        else:
            pubsub.subscribe(*channel_list)

        for message in pubsub.listen():
            if message.get("type") not in {"message", "pmessage"}:
                continue
            raw = message.get("data")
            if not isinstance(raw, str):
                continue
            try:
                envelope = MeshMessage.from_raw(raw)
                live_channel = str(message.get("channel") or message.get("pattern") or "")
                if not envelope.channel:
                    envelope.channel = live_channel
                handler(envelope, live_channel)
            except Exception as exc:
                LOG.exception("AgentBus handler failed for %s: %s", self.agent_id, exc)
