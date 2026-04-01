from __future__ import annotations

import json
import os
from collections import deque
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
STATE_DIR = ROOT / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)
EVENT_LOG = STATE_DIR / "events.jsonl"
COMMAND_LOG = STATE_DIR / "commands.jsonl"

EVENTS: deque[dict[str, Any]] = deque(maxlen=500)
COMMANDS: deque[dict[str, Any]] = deque()
PORT = int(os.environ.get("TK_EVENT_BRIDGE_PORT", "9000"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(length) if length else b"{}"
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=True) + "\n")


class Handler(BaseHTTPRequestHandler):
    server_version = "TerminalKeeperEventBridge/0.1"

    def do_GET(self) -> None:
        if self.path == "/health":
            return self._json(HTTPStatus.OK, {
                "status": "ok",
                "events_buffered": len(EVENTS),
                "commands_buffered": len(COMMANDS),
                "ts": _now(),
            })

        if self.path == "/api/events":
            return self._json(HTTPStatus.OK, {
                "count": len(EVENTS),
                "events": list(EVENTS),
            })

        if self.path.startswith("/api/commands/next"):
            if not COMMANDS:
                return self._empty(HTTPStatus.NO_CONTENT)
            command = COMMANDS.popleft()
            return self._text(HTTPStatus.OK, command["command"])

        return self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path == "/api/events":
            payload = _read_json(self)
            envelope = {
                "received_at": _now(),
                **payload,
            }
            EVENTS.append(envelope)
            _append_jsonl(EVENT_LOG, envelope)
            return self._json(HTTPStatus.ACCEPTED, {"queued": True, "eventType": payload.get("eventType")})

        if self.path == "/api/commands":
            payload = _read_json(self)
            command = {
                "received_at": _now(),
                "command": payload.get("command", "").strip(),
            }
            if not command["command"]:
                return self._json(HTTPStatus.BAD_REQUEST, {"error": "command is required"})
            COMMANDS.append(command)
            _append_jsonl(COMMAND_LOG, command)
            return self._json(HTTPStatus.ACCEPTED, {"queued": True, "command": command["command"]})

        return self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def _json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _text(self, status: HTTPStatus, body: str) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _empty(self, status: HTTPStatus) -> None:
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.end_headers()


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"TerminalKeeper event server listening on http://127.0.0.1:{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
