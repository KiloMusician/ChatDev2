"""
services/agent_bus.py — T2: Agent-to-agent pub/sub message bus.

Provides real-time inter-agent messaging without requiring Redis.
Uses asyncio queues in-process; upgrade path: set REDIS_URL env var
to route through Redis pub/sub (requires `redis[asyncio]` package).

Architecture:
  AgentBus.publish(from_agent, to_agent_or_channel, text)
      → enqueues to all active channel subscribers
      → all /ws/ambient clients receive {"type":"agent_msg", ...}

  AgentBus.subscribe(channel) → async generator of message dicts
  AgentBus.unsubscribe(channel, queue) → cleanup on WS disconnect
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections import defaultdict
from typing import AsyncGenerator

log = logging.getLogger(__name__)

# ── Message schema ────────────────────────────────────────────────────────
# {
#   "type":        "agent_msg",
#   "from_agent":  "ada",
#   "to_agent":    "cypher" | None,
#   "channel":     "hive" | <custom>,
#   "text":        "[ADA → CYPHER]: The lattice is shifting.",
#   "ts":          1711234567.89
# }


class _InMemoryBus:
    """Pure asyncio in-memory broker. No external deps required."""

    def __init__(self) -> None:
        # channel → list of asyncio.Queue (one per active subscriber)
        self._subs: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def publish(self, msg: dict) -> int:
        """Publish to all subscribers of msg['channel']. Returns delivery count."""
        channel = msg.get("channel", "hive")
        async with self._lock:
            queues = list(self._subs.get(channel, []))
            # also deliver to wildcard "*" subscribers
            queues += list(self._subs.get("*", []))
        delivered = 0
        for q in queues:
            try:
                q.put_nowait(msg)
                delivered += 1
            except asyncio.QueueFull:
                log.warning("agent_bus: queue full, dropping message for %s", channel)
        return delivered

    async def subscribe(self, channel: str = "hive") -> AsyncGenerator[dict, None]:
        q: asyncio.Queue = asyncio.Queue(maxsize=64)
        async with self._lock:
            self._subs[channel].append(q)
        try:
            while True:
                msg = await asyncio.wait_for(q.get(), timeout=30.0)
                yield msg
        except asyncio.TimeoutError:
            # yield a keepalive ping so callers know the subscription is alive
            yield {"type": "agent_bus_ping", "channel": channel, "ts": time.time()}
        except asyncio.CancelledError:
            pass
        finally:
            async with self._lock:
                try:
                    self._subs[channel].remove(q)
                except ValueError:
                    pass

    async def unsubscribe(self, channel: str, queue: asyncio.Queue) -> None:
        async with self._lock:
            try:
                self._subs[channel].remove(queue)
            except ValueError:
                pass

    def subscriber_count(self, channel: str = "*") -> int:
        if channel == "*":
            return sum(len(v) for v in self._subs.values())
        return len(self._subs.get(channel, []))


class _RedisBus:
    """Redis-backed broker. Only instantiated when REDIS_URL is set.
    Requires: pip install redis[asyncio]
    """

    def __init__(self, url: str) -> None:
        import redis.asyncio as aioredis  # type: ignore
        self._redis = aioredis.from_url(url, decode_responses=True)
        log.info("agent_bus: using Redis backend at %s", url)

    async def publish(self, msg: dict) -> int:
        import json
        channel = msg.get("channel", "hive")
        return await self._redis.publish(f"td:agent:{channel}", json.dumps(msg))

    async def subscribe(self, channel: str = "hive") -> AsyncGenerator[dict, None]:
        import json
        async with self._redis.pubsub() as ps:
            await ps.subscribe(f"td:agent:{channel}")
            try:
                async for raw in ps.listen():
                    if raw["type"] == "message":
                        try:
                            yield json.loads(raw["data"])
                        except Exception:
                            pass
            except asyncio.CancelledError:
                pass

    def subscriber_count(self, channel: str = "*") -> int:
        return -1  # Redis doesn't expose sub count easily in async mode


# ── Singleton ─────────────────────────────────────────────────────────────
def _build_bus():
    redis_url = os.environ.get("REDIS_URL", "")
    if redis_url:
        try:
            return _RedisBus(redis_url)
        except Exception as e:
            log.warning("agent_bus: Redis unavailable (%s), falling back to in-memory", e)
    return _InMemoryBus()


bus: _InMemoryBus | _RedisBus = _build_bus()


# ── Public helpers ────────────────────────────────────────────────────────

async def publish(
    from_agent: str,
    text: str,
    to_agent: str | None = None,
    channel: str = "hive",
) -> int:
    """Convenience wrapper — builds msg dict and publishes."""
    msg = {
        "type":       "agent_msg",
        "from_agent": from_agent,
        "to_agent":   to_agent,
        "channel":    channel,
        "text":       text,
        "ts":         time.time(),
    }
    return await bus.publish(msg)


async def subscribe(channel: str = "hive") -> AsyncGenerator[dict, None]:
    """Yield agent messages on *channel* indefinitely."""
    async for msg in bus.subscribe(channel):
        yield msg


def subscriber_count(channel: str = "*") -> int:
    return bus.subscriber_count(channel)
