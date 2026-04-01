#!/usr/bin/env python3
"""ChatDev mesh bridge and backward-compatible entrypoint."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from core.agent_bus import AgentBus, MeshMessage
from scripts import chatdev_worker

LOG_DIR = BASE / "var"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] CHATDEV_MESH %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "chatdev_mesh.log"),
    ],
)
log = logging.getLogger("chatdev_mesh")


def _next_mesh_task_id(queue: dict) -> str:
    existing = {str(task.get("id", "")) for task in queue.get("tasks", [])}
    counter = len(existing) + 1
    while True:
        task_id = f"CHATDEV-MESH-{counter:04d}"
        if task_id not in existing:
            return task_id
        counter += 1


def _enqueue_mesh_task(message: MeshMessage) -> dict:
    payload = message.payload or {}
    description = (payload.get("task") or payload.get("description") or "").strip()
    if not description:
        raise ValueError("Missing mesh task description.")

    queue = chatdev_worker.load_queue()
    queue.setdefault("tasks", [])
    task_id = _next_mesh_task_id(queue)
    task = {
        "id": task_id,
        "description": description,
        "priority": payload.get("priority", "P1"),
        "category": payload.get("category", "hardening"),
        "assigned_to": "chatdev",
        "status": "open",
        "created_at": chatdev_worker.now_iso(),
        "context": payload.get("context", ""),
        "target": payload.get("target") or payload.get("path") or "",
        "source": "chatdev_mesh_bridge",
        "request_sender": message.sender,
        "correlation_id": message.id,
    }
    queue["tasks"].append(task)
    chatdev_worker.save_queue(queue)
    return task


def run_mesh_bridge() -> None:
    bus = AgentBus(
        "chatdev",
        capabilities=["code_generation", "task_enqueue"],
        tags=["mesh", "chatdev"],
        description="ChatDev mesh bridge for queue-backed code generation",
    )
    bus.register(metadata={"output_dir": str(chatdev_worker.OUTPUT_DIR)})
    bus.start_heartbeat_loop(
        interval_s=30,
        extra_factory=lambda: {"output_dir": str(chatdev_worker.OUTPUT_DIR)},
    )
    bus.heartbeat(extra={"output_dir": str(chatdev_worker.OUTPUT_DIR)})

    def _handler(message: MeshMessage, _channel: str) -> None:
        payload = message.payload or {}
        recipient = (message.recipient or payload.get("target") or "").lower()
        if recipient not in ("", "chatdev", "all"):
            return

        try:
            task = _enqueue_mesh_task(message)
            response = {
                "ok": True,
                "queued": True,
                "task_id": task["id"],
                "queue_path": str(chatdev_worker.QUEUE_PATH),
                "status": task["status"],
            }
            log.info("Queued mesh task %s from %s", task["id"], message.sender)
        except Exception as exc:
            response = {"ok": False, "error": str(exc)}
            log.exception("Failed to queue ChatDev mesh task: %s", exc)

        if message.type == "request" and message.sender:
            bus.respond(message, response, tags=["mesh", "chatdev"])

    log.info("ChatDev mesh bridge listening on mesh channels")
    bus.listen_forever(
        [AgentBus.personal_channel("chatdev"), AgentBus.TASK_CHANNEL],
        _handler,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="ChatDev compatibility entrypoint.")
    parser.add_argument(
        "--mesh", action="store_true", help="Run the ChatDev mesh bridge"
    )
    parser.add_argument(
        "--daemon", action="store_true", help="Run queue worker forever"
    )
    parser.add_argument("--once", action="store_true", help="Run one queue pass")
    parser.add_argument("--task-id", help="Process a single task id")
    parser.add_argument("--apply", action="store_true", help="Apply generated diffs")
    parser.add_argument(
        "--poll",
        type=int,
        default=chatdev_worker.DEFAULT_POLL_SECONDS,
        help="Queue poll interval",
    )
    args = parser.parse_args()

    if args.mesh:
        run_mesh_bridge()
        return 0

    forwarded = []
    if args.daemon:
        forwarded.append("--daemon")
    if args.once:
        forwarded.append("--once")
    if args.task_id:
        forwarded.extend(["--task-id", args.task_id])
    if args.apply:
        forwarded.append("--apply")
    if args.poll != chatdev_worker.DEFAULT_POLL_SECONDS:
        forwarded.extend(["--poll", str(args.poll)])

    return chatdev_worker.main(forwarded or None)


if __name__ == "__main__":
    raise SystemExit(main())
