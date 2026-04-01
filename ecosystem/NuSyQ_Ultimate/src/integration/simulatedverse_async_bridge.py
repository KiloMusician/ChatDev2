"""File-backed SimulatedVerse async bridge for cross-repo coordination."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4


class SimulatedVerseBridge:
    """Submit tasks to SimulatedVerse and poll for async results."""

    def __init__(self, root_path: Optional[str] = None) -> None:
        self.root = Path(root_path).resolve() if root_path else Path(".").resolve()
        self.tasks_dir = self.root / "tasks"
        self.results_dir = self.root / "results"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def submit_task(
        self,
        agent_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Write a task envelope to `tasks/<task_id>.json`."""
        now_ms = int(time.time() * 1000)
        task_id = f"{agent_id}_{now_ms}_{uuid4().hex[:8]}"
        payload: Dict[str, Any] = {
            "task_id": task_id,
            "agent_id": agent_id,
            "content": content,
            "metadata": metadata or {},
            "ask": {"payload": metadata or {}},
            "t": now_ms,
            "utc": now_ms,
            "entropy": 0.5,
            "budget": 0.95,
            "source": "nusyq-root",
            "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        task_file = self.tasks_dir / f"{task_id}.json"
        task_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return task_id

    def check_result(
        self,
        task_id: str,
        timeout: int = 30,
    ) -> Optional[Dict[str, Any]]:
        """Poll for `<task_id>_result.json` until timeout."""
        result_file = self.results_dir / f"{task_id}_result.json"
        deadline = time.time() + max(timeout, 0)
        while time.time() <= deadline:
            if result_file.exists():
                try:
                    return json.loads(result_file.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    return {"task_id": task_id, "status": "invalid_result_json"}
            time.sleep(0.5)
        return None
