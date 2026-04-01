"""
TerminalDepths / ChatDev Bridge Client
=======================================
Any repo can import this and call the bridge without knowing the full API surface.

Usage:
    from nusyq_surface.bridge_client import BridgeClient
    td = BridgeClient()
    print(td.ping())
    print(td.manifest())
    result = td.command("repo list")
    task_id = td.task_add("scan", payload={"target": "all"})
    td.repo_open("nusyq_hub")
"""
from __future__ import annotations
import json
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

from .env import CHATDEV_API


class BridgeClient:
    """Minimal zero-dependency HTTP client for the ChatDev bridge surface."""

    def __init__(self, base_url: str = CHATDEV_API, timeout: int = 8):
        self.base = base_url.rstrip("/")
        self.timeout = timeout

    def _get(self, path: str) -> Any:
        try:
            url = f"{self.base}/api/bridge{path}"
            with urllib.request.urlopen(url, timeout=self.timeout) as r:
                return json.loads(r.read())
        except urllib.error.URLError as e:
            return {"error": str(e), "path": path}

    def _post(self, path: str, data: Any = None) -> Any:
        try:
            url = f"{self.base}/api/bridge{path}"
            body = json.dumps(data or {}).encode()
            req = urllib.request.Request(
                url, data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read())
        except urllib.error.URLError as e:
            return {"error": str(e), "path": path}

    # ── Bridge surfaces ────────────────────────────────────────────────────

    def ping(self) -> dict:
        """Health check — returns latency and bridge status."""
        return self._get("/ping")

    def manifest(self) -> dict:
        """Full bridge manifest: capabilities, repos, agents, surfaces."""
        return self._get("/manifest")

    def command(self, cmd: str, context: Optional[dict] = None) -> dict:
        """Execute a bridge command (e.g. 'repo list', 'chug run')."""
        return self._post("/command", {"command": cmd, "context": context or {}})

    def task_add(self, action: str, repo: str = "ecosystem", payload: Any = None, priority: int = 5) -> dict:
        """Add a task to the shared ecosystem task queue."""
        return self._post("/task/add", {"action": action, "repo": repo, "payload": payload, "priority": priority})

    def repo_list(self) -> dict:
        """List all repos in the ecosystem registry."""
        return self._get("/repo/list")

    def repo_status(self, name: Optional[str] = None) -> dict:
        """Get status for one or all repos."""
        path = f"/repo/status/{name}" if name else "/repo/status"
        return self._get(path)

    def repo_open(self, name: str) -> dict:
        """Signal intent to open/activate a repo."""
        return self._post("/repo/open", {"name": name})

    def repo_exec(self, name: str, cmd: str) -> dict:
        """Execute a shell command in a repo's root directory."""
        return self._post("/repo/exec", {"repo": name, "command": cmd})

    def agent_dispatch(self, agent: str, task: str, payload: Any = None) -> dict:
        """Dispatch a task to a named agent."""
        return self._post("/agent/dispatch", {"agent": agent, "task": task, "payload": payload or {}})

    def session_open(self, session_id: str, context: Optional[dict] = None) -> dict:
        """Open a session context on the bridge."""
        return self._post("/session/open", {"session_id": session_id, "context": context or {}})

    def session_state(self, session_id: str) -> dict:
        """Read the state of an open session."""
        return self._get(f"/session/state/{session_id}")

    @classmethod
    def from_env(cls) -> "BridgeClient":
        from .env import CHATDEV_API
        return cls(base_url=CHATDEV_API)
