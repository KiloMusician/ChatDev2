"""RimAPI Bridge — listens for RimWorld API events and relays them
to the Terminal Depths ecosystem via Redis and REST.

The Terminal Keeper mod calls /api/game/command on Terminal Depths directly,
but this bridge provides an additional compatibility layer for the RIMAPI mod
(http://localhost:8765) and exposes a simplified status API.

Usage:
    python scripts/rimapi_bridge.py --port 8765
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import UTC, datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent.parent
LOG_DIR = BASE / "var"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] RIMAPI %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "rimapi.log"),
    ],
)
log = logging.getLogger("rimapi")

try:
    import uvicorn
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel

    FASTAPI_OK = True
except ImportError:
    FASTAPI_OK = False

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

TD_URL = os.getenv("TERMINAL_DEPTHS_URL", "http://localhost:7337")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def publish(channel: str, data: dict) -> None:
    if not REDIS_OK or _r is None:
        return
    try:
        _r.publish(channel, json.dumps({**data, "_ts": _now()}))
    except Exception:
        pass


if FASTAPI_OK:
    app = FastAPI(title="RimAPI Bridge", version="0.1.0")
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )

    class PawnState(BaseModel):
        name: str
        mood: float = 0.5
        health: float = 1.0
        job: str | None = None
        downed: bool = False

    class ColonyEvent(BaseModel):
        event_type: str
        data: dict = {}

    class BridgeEvent(BaseModel):
        eventType: str
        ticks: str | int = 0
        payload: dict = {}

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "rimapi_bridge", "ts": _now()}

    @app.get("/api/status")
    async def status():
        return {
            "status": "ok",
            "redis": REDIS_OK,
            "td_url": TD_URL,
            "ts": _now(),
        }

    @app.post("/api/colony/pawn")
    async def push_pawn(pawn: PawnState):
        """Receive pawn state from Terminal Keeper mod."""
        event = {"type": "pawn_state", **pawn.dict()}
        publish("lattice.rimworld.pawn", event)
        log.info(f"Pawn state: {pawn.name} mood={pawn.mood:.2f}")
        return {"status": "ok"}

    @app.post("/api/game/incident")
    async def push_incident(evt: ColonyEvent):
        """Receive game events from Terminal Keeper mod."""
        event = {"type": "colony_incident", "event_type": evt.event_type, **evt.data}
        publish("lattice.rimworld.incident", event)
        log.info(f"Incident: {evt.event_type}")
        return {"status": "ok"}

    @app.post("/api/events")
    async def push_bridge_event(evt: BridgeEvent):
        """Receive generic event-bridge payloads from the RimWorld event bridge mod."""
        event = {
            "type": evt.eventType,
            "ticks": evt.ticks,
            **evt.payload,
        }

        if evt.eventType == "chat_interaction":
            channel = "lattice.rimworld.chat"
            if "omniTag" not in event:
                event["omniTag"] = "[Msg⛛{Chat}]"
            log.info(
                "Chat event: %s %s -> %s (%s)",
                event.get("source", "unknown"),
                event.get("initiator", "unknown"),
                event.get("recipient", "unknown"),
                event.get("outcome", "unknown"),
            )
        else:
            channel = "lattice.rimworld.event"
            log.info(f"Bridge event: {evt.eventType}")

        publish(channel, event)
        return {"status": "ok", "channel": channel, "event_type": evt.eventType}

    @app.post("/api/game/crash")
    async def push_crash(body: dict):
        """Explicit crash notification from Terminal Keeper mod."""
        publish("lattice.rimworld.crash", {**body, "source": "rimapi_bridge"})
        log.warning("Crash event received via RimAPI bridge")
        return {"status": "ok", "message": "Crash registered. Gordon is watching."}

    @app.get("/api/council/status")
    async def council_status():
        return {
            "council": ["gordon", "serena", "skyclaw", "culture_ship"],
            "status": "active",
            "ts": _now(),
        }


def main() -> None:
    if not FASTAPI_OK:
        log.error("FastAPI not available. Install with: pip install fastapi uvicorn")
        return

    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="0.0.0.0")
    args = ap.parse_args()

    log.info(f"RimAPI Bridge starting on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
