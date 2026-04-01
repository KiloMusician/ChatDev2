#!/usr/bin/env python3
"""Deterministic mock LLM bridge for the agent mesh."""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from core.agent_bus import AgentBus, MeshMessage

LOG_DIR = BASE / "var"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] MOCK-LLM %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "mock_llm_bridge.log"),
    ],
)
log = logging.getLogger("mock_llm_bridge")


def _deterministic_response(prompt: str) -> dict:
    prompt = (prompt or "").strip()
    seed = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]
    summary = prompt[:120] + ("..." if len(prompt) > 120 else "")
    return {
        "text": f"[mock-llm:{seed}] {summary or 'No prompt provided.'}",
        "model": "mock-llm",
        "deterministic": True,
    }


def _handle_message(bus: AgentBus, message: MeshMessage) -> None:
    payload = message.payload or {}
    recipient = (message.recipient or payload.get("target") or "").lower()
    if recipient not in ("", "mock-llm", "all"):
        return

    prompt = payload.get("prompt") or payload.get("task") or payload.get("query") or ""
    result = {
        "ok": True,
        "result": _deterministic_response(prompt),
        "request": {
            "sender": message.sender,
            "channel": message.channel,
            "type": message.type,
        },
    }
    if message.type == "request" and message.sender:
        bus.respond(message, result, tags=["mesh", "mock-llm"])
    else:
        bus.publish(
            AgentBus.RESULT_CHANNEL,
            MeshMessage.create(
                type="event",
                sender="mock-llm",
                recipient=AgentBus.RESULT_CHANNEL,
                payload=result,
                channel=AgentBus.RESULT_CHANNEL,
                tags=["mesh", "mock-llm"],
            ),
        )


def run_daemon() -> None:
    bus = AgentBus(
        "mock-llm",
        capabilities=["prompt_response"],
        tags=["mesh", "bridge", "mock-llm"],
        description="Deterministic request/response bridge for the agent mesh",
    )
    bus.register(metadata={"bridge": "mock-llm"})
    bus.start_heartbeat_loop(interval_s=30, extra_factory=lambda: {"bridge": "mock-llm"})
    bus.heartbeat(extra={"bridge": "mock-llm"})

    def _handler(message: MeshMessage, _channel: str) -> None:
        _handle_message(bus, message)

    log.info("mock-llm bridge listening on mesh channels")
    bus.listen_forever(
        [AgentBus.personal_channel("mock-llm"), AgentBus.TASK_CHANNEL],
        _handler,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--daemon", action="store_true")
    ap.add_argument("--prompt", type=str, help="Run a one-shot deterministic prompt.")
    args = ap.parse_args()

    if args.prompt:
        print(json.dumps(_deterministic_response(args.prompt), indent=2))
        return

    if args.daemon:
        run_daemon()
        return

    log.info("No mode specified. Use --daemon or --prompt.")
    time.sleep(1)


if __name__ == "__main__":
    main()
