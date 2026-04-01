"""
NuSyQ-Hub Orchestrator Client
================================
Thin HTTP client wrapping the ChatDev orchestrator API.
Every repo can use this to post tasks, read agent state, and query memory.

Usage:
    from nusyq_surface.hub_client import HubClient
    hub = HubClient()
    print(hub.status())
    hub.enqueue("scan_repo", repo="nusyq_hub")
    hub.memory_write("my_key", {"data": 42})
"""
from __future__ import annotations
import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

from .env import CHATDEV_API


class HubClient:
    def __init__(self, base_url: str = CHATDEV_API, timeout: int = 8):
        self.base = base_url.rstrip("/")
        self.timeout = timeout

    def _get(self, path: str) -> Any:
        try:
            with urllib.request.urlopen(f"{self.base}{path}", timeout=self.timeout) as r:
                return json.loads(r.read())
        except urllib.error.URLError as e:
            return {"error": str(e)}

    def _post(self, path: str, data: Any = None) -> Any:
        try:
            body = json.dumps(data or {}).encode()
            req = urllib.request.Request(
                f"{self.base}{path}", data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read())
        except urllib.error.URLError as e:
            return {"error": str(e)}

    # ── Orchestrator surfaces ──────────────────────────────────────────────

    def status(self) -> dict:
        return self._get("/api/orchestrator/status")

    def scan(self) -> dict:
        return self._get("/api/orchestrator/scan")

    def run_cycle(self) -> dict:
        return self._post("/api/orchestrator/cycle", {})

    def agents(self) -> List[dict]:
        return self._get("/api/orchestrator/agents").get("agents", [])

    def tools(self, repo: str = None) -> List[dict]:
        path = f"/api/orchestrator/tools?repo={repo}" if repo else "/api/orchestrator/tools"
        return self._get(path).get("tools", [])

    def enqueue(self, action: str, repo: str = "ecosystem", agent: str = None,
                payload: Any = None, priority: int = 5) -> str:
        r = self._post("/api/orchestrator/tasks/enqueue", {
            "action": action, "repo": repo, "agent": agent,
            "payload": payload or {}, "priority": priority,
        })
        return r.get("task_id", "")

    def tasks(self) -> dict:
        return self._get("/api/orchestrator/tasks")

    def memory_write(self, key: str, value: Any, namespace: str = "global") -> dict:
        return self._post("/api/orchestrator/memory/write", {
            "key": key, "value": value, "namespace": namespace
        })

    def memory_read(self, namespace: str = None) -> dict:
        path = f"/api/orchestrator/memory?namespace={namespace}" if namespace else "/api/orchestrator/memory"
        return self._get(path)

    def logs(self, limit: int = 20, repo: str = None) -> List[dict]:
        path = f"/api/orchestrator/logs?limit={limit}"
        if repo:
            path += f"&repo={repo}"
        return self._get(path).get("logs", [])

    @classmethod
    def from_env(cls) -> "HubClient":
        from .env import CHATDEV_API
        return cls(base_url=CHATDEV_API)
