"""ChatDev subprocess service layer."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class SubprocessResult:
    command: list[str]
    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def success(self) -> bool:
        return self.returncode == 0


_RUN = "run.py"
_RUN_OLLAMA = "run_ollama.py"


class ChatDevService:
    """Manages a ChatDev subprocess session."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config: dict[str, Any] = {}
        self.config.update(os.environ)
        if config:
            self.config.update(config)
        self.active: bool = False
        raw_path = self.config.get("CHATDEV_PATH")
        self.chatdev_path: Path | None = Path(raw_path) if raw_path else None

    # ------------------------------------------------------------------
    def start(self) -> dict[str, Any]:
        if self.active:
            return {"success": True, "message": "already running"}
        if self.chatdev_path is None:
            return {"success": False, "error": "ChatDev path not found"}
        entrypoint = self._find_entrypoint()
        if entrypoint is None:
            return {"success": False, "error": "No valid entrypoint found in ChatDev path"}
        self.active = True
        return {"success": True, "entrypoint": str(entrypoint)}

    def stop(self) -> None:
        self.active = False

    def send_request(self, args: list[str]) -> SubprocessResult:
        result = self.start()
        if not result["success"]:
            return SubprocessResult(command=[], returncode=-1, stderr=result.get("error", ""))
        entrypoint = self._find_entrypoint()
        cmd = [sys.executable, entrypoint.name, *args]
        completed = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(self.chatdev_path), check=False
        )
        return SubprocessResult(
            command=cmd,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    # ------------------------------------------------------------------
    def _find_entrypoint(self) -> Path | None:
        if self.chatdev_path is None:
            return None
        use_ollama = self.config.get("CHATDEV_USE_OLLAMA", "").strip() in ("1", "true", "yes")
        order = (_RUN_OLLAMA, _RUN) if use_ollama else (_RUN, _RUN_OLLAMA)
        for name in order:
            candidate = self.chatdev_path / name
            if candidate.exists():
                return candidate
        return None
