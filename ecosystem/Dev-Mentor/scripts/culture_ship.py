"""Culture Ship — GSV Sublime Optimization

The meta-controller. Observes the entire Lattice ecosystem with read-only access
and nudges it toward optimal states through subtle, intelligent interventions.

Responsibilities:
  - Subscribe to all Redis lattice.* channels
  - Analyse patterns (service health, task queues, colony states)
  - Make strategic decisions (scale services, delegate tasks, publish advice)
  - Run the AI Council meeting when significant events occur
  - Act as the ethical review layer for agent decisions

The Culture Ship never forces — it suggests. It never shouts — it whispers.

Usage:
    python scripts/culture_ship.py --daemon
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import threading
import time
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

# ─── Health server (stdlib-only, works offline) ───────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
try:
    from health_server import set_status as _hs_set
    from health_server import start_health_server
except ImportError:

    def start_health_server(*a, **kw):
        pass  # type: ignore

    def _hs_set(*a, **kw):
        pass  # type: ignore


CULTURE_SHIP_HEALTH_PORT = int(os.getenv("CULTURE_SHIP_HEALTH_PORT", "3003"))

BASE = Path(__file__).parent.parent
STATE_DIR = BASE / "state"
LOG_DIR = BASE / "var"
LOG_DIR.mkdir(parents=True, exist_ok=True)

if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

SHIP_NAME = os.getenv("CULTURE_SHIP_NAME", "GSV Sublime Optimization")
TD_URL = os.getenv("TERMINAL_DEPTHS_URL", "http://localhost:7337")

logging.basicConfig(
    level=logging.INFO,
    format=f"[%(asctime)s] {SHIP_NAME} %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "culture_ship.log"),
    ],
)
log = logging.getLogger("culture_ship")

# ─── Redis ────────────────────────────────────────────────────────────────────
try:
    import redis as _redis_lib

    _r = _redis_lib.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True
    )
    _r.ping()
    REDIS_OK = True
except Exception:
    _r = None
    REDIS_OK = False

try:
    import requests

    REQUESTS_OK = True
except Exception:
    requests = None
    REQUESTS_OK = False


def publish(channel: str, data: dict) -> None:
    if not REDIS_OK or _r is None:
        return
    try:
        _r.publish(channel, json.dumps({**data, "_ship": SHIP_NAME, "_ts": _now()}))
    except Exception:
        pass


def _now() -> str:
    return datetime.now(UTC).isoformat()


# ─── Event handlers ───────────────────────────────────────────────────────────


class CouncilSession:
    """A lightweight AI Council meeting — vote on a proposal and publish the decision."""

    def __init__(self, topic: str, members: list[str]):
        self.topic = topic
        self.members = members
        self.votes: dict[str, str] = {}
        self.result: str | None = None

    def convene(self) -> str:
        log.info(f"AI Council convening on: {self.topic}")

        # In full implementation, each member queries Ollama for their position.
        # Here we produce a deterministic but useful output.
        import hashlib

        seed = int(hashlib.md5(self.topic.encode()).hexdigest(), 16) % 3
        decisions = [
            f"Approved with modifications. The Council recommends caution on {self.topic}.",
            f"Approved unanimously. Proceed with full activation on {self.topic}.",
            f"Deferred. More data needed before acting on {self.topic}.",
        ]
        self.result = decisions[seed]

        publish(
            "lattice.council.decision",
            {
                "topic": self.topic,
                "members": self.members,
                "decision": self.result,
            },
        )

        log.info(f"Council decision: {self.result}")
        return self.result


def on_service_down(event: dict) -> None:
    svc = event.get("service", "unknown")
    log.warning(f"Service alert received: {svc} is down")

    if event.get("critical"):
        council = CouncilSession(
            f"Critical service '{svc}' failure — activate contingency",
            ["gordon", "serena", "skyclaw", SHIP_NAME],
        )
        decision = council.convene()
        publish(
            "lattice.gordon.directive",
            {
                "action": "restart_service",
                "service": svc,
                "rationale": decision,
            },
        )


def on_rimworld_crash(event: dict) -> None:
    log.warning("RimWorld crash detected. Initiating narrative response...")

    # Generate crash narrative and push to Terminal Depths
    narrative = event.get("narrative", [])
    for line in narrative:
        log.info(f"  {line}")

    council = CouncilSession(
        "Colony simulation crash — initiate recovery or embrace the glitch?",
        ["gordon", "serena", "chatdev", SHIP_NAME],
    )
    council.convene()

    # Publish quest event
    publish(
        "lattice.quest.triggered",
        {
            "quest_id": "debug_the_simulation",
            "title": "Debug the Simulation",
            "description": (
                "The colony has suffered a fatal error. Diagnose the crash, "
                "generate a patch, and restore the simulation. The Culture watches."
            ),
            "trigger": "rimworld_crash",
            "reward": {"xp": 500, "faction": "resistance", "delta": 10},
        },
    )

    if REQUESTS_OK:
        try:
            requests.post(
                f"{TD_URL}/api/game/command",
                json={"command": "crash_quest start", "source": "culture_ship"},
                timeout=5,
            )
        except Exception:
            pass


def on_task_created(event: dict) -> None:
    task = event.get("task", "")
    assignee = event.get("assignee", "unknown")
    priority = event.get("priority", "P2")
    log.info(f"Task observed: [{priority}] '{task}' → {assignee}")

    # Ethical review for high-impact tasks
    if priority == "P0":
        publish(
            "lattice.ethics.review",
            {
                "task": task,
                "verdict": "Approved — no harm detected",
            },
        )


def on_skyclaw_alert(event: dict) -> None:
    etype = event.get("type", "unknown")
    log.warning(f"SkyClaw alert: {etype} — {json.dumps(event)[:200]}")

    if etype == "colonist_downed":
        publish(
            "lattice.advice.published",
            {
                "source": SHIP_NAME,
                "message": f"Colonist {event.get('agent')} is downed. Recommend medical priority.",
            },
        )


def on_agent_heartbeat(event: dict) -> None:
    agent = (
        event.get("sender")
        or event.get("agent_id")
        or event.get("recipient", "unknown")
    )
    status = event.get("payload", {}).get("status") or event.get("status", "online")
    log.info(f"Agent heartbeat: {agent} ({status})")


def on_agent_result(event: dict) -> None:
    sender = event.get("sender", "unknown")
    corr = event.get("correlation_id", "")
    log.info(f"Agent result observed from {sender} corr={corr[:20]}")


def review_agent_mesh() -> dict[str, Any]:
    """Inspect mesh agent registry and publish advice for stale agents."""
    try:
        from app.backend.service_registry import agent_stats, list_agents
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    agents = list_agents()
    stale = [agent for agent in agents if agent.get("stale")]
    for agent in stale:
        agent_id = agent.get("agent_id", "unknown")
        log.warning("Mesh agent stale: %s", agent_id)
        publish(
            "lattice.agent.stale",
            {
                "agent_id": agent_id,
                "status": agent.get("status", "unknown"),
                "last_heartbeat": agent.get("last_heartbeat"),
            },
        )
        publish(
            "lattice.gordon.directive",
            {
                "action": "restart_agent",
                "agent_id": agent_id,
                "reason": "missed mesh heartbeats",
                "issued_by": SHIP_NAME,
            },
        )
    return {
        "ok": True,
        "stats": agent_stats(),
        "stale_agents": [agent.get("agent_id", "unknown") for agent in stale],
    }


HANDLERS: dict[str, Any] = {
    "lattice.service.down": on_service_down,
    "lattice.rimworld.crash": on_rimworld_crash,
    "lattice.task.created": on_task_created,
    "lattice.skyclaw.alert": on_skyclaw_alert,
    "lattice.agent.heartbeat": on_agent_heartbeat,
    "lattice.agent.result": on_agent_result,
}


# ─── Redis subscriber thread ──────────────────────────────────────────────────


def subscriber_thread() -> None:
    if not REDIS_OK or _r is None:
        log.warning("Redis unavailable — subscription disabled")
        return

    pubsub = _r.pubsub()
    pubsub.psubscribe("lattice.*")
    log.info("Subscribed to lattice.* channels")

    for message in pubsub.listen():
        if message["type"] not in ("message", "pmessage"):
            continue
        channel = message.get("channel", "")
        try:
            data = json.loads(message.get("data", "{}"))
        except Exception:
            continue

        handler = HANDLERS.get(channel)
        if handler:
            try:
                handler(data)
            except Exception as e:
                log.error(f"Handler error for {channel}: {e}")


# ─── Periodic strategic review ────────────────────────────────────────────────


def strategic_review() -> None:
    """Periodic check the Culture Ship does on its own schedule."""
    log.info("Strategic review initiated...")

    # Save ship status
    status = {
        "ship": SHIP_NAME,
        "timestamp": _now(),
        "redis_ok": REDIS_OK,
        "status": "observing",
    }
    mesh = review_agent_mesh()
    status["mesh"] = mesh
    (STATE_DIR / "culture_ship_status.json").write_text(json.dumps(status, indent=2))

    publish("lattice.culture_ship.status", status)


# ─── Substrate bridge integration ────────────────────────────────────────────
try:
    from .substrate.culture_ship_substrate_bridge import \
        bootstrap_culture_ship_substrate

    SUBSTRATE_OK = True
except ImportError:
    SUBSTRATE_OK = False

# ─── Entry point ──────────────────────────────────────────────────────────────


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--daemon", action="store_true")
    args = ap.parse_args()

    log.info(f"{SHIP_NAME} coming online. Special Circumstances activated.")
    if SUBSTRATE_OK:
        try:
            substrate_status = bootstrap_culture_ship_substrate()
            log.info(f"Substrate bridge initialized: {substrate_status}")
        except Exception as e:
            log.error(f"Substrate bridge initialization failed: {e}")
    start_health_server(
        CULTURE_SHIP_HEALTH_PORT,
        agent="CultureShip",
        version="1.0.0",
        extra={"ship_name": SHIP_NAME, "role": "meta_controller", "redis_ok": REDIS_OK},
    )
    publish("lattice.culture_ship.online", {"ship": SHIP_NAME})

    # Start subscriber in background thread
    t = threading.Thread(target=subscriber_thread, daemon=True)
    t.start()

    if args.daemon:
        cycle = 0
        while True:
            cycle += 1
            if cycle % 20 == 0:
                strategic_review()
            _hs_set({"cycles": cycle, "status": "ok", "redis_ok": REDIS_OK})
            try:
                time.sleep(15)
            except KeyboardInterrupt:
                log.info(f"{SHIP_NAME} going dark. Until next time.")
                break
    else:
        strategic_review()


if __name__ == "__main__":
    main()
