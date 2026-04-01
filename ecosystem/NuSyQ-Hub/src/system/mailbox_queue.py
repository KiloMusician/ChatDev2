"""File-based mailbox queue for offline CLI integration.

This provides a minimal NDJSON-based command mailbox: `commands.ndjson` and
`results.ndjson` under `data/mailbox/`. It's intentionally simple so it works
without network dependencies and can be used by CLI tools or other constrained
environments.

Usage:
  from src.system.mailbox_queue import Mailbox
  mb = Mailbox()
  mb.append_command({"id": "cmd-1", "command": "run", "args": {}})

The run loop (NuSyQ-Hub) can poll `Mailbox.consume_commands()` to process
commands and write responses via `Mailbox.append_result()`.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterable
from pathlib import Path
from typing import Any

BASE = Path("data") / "mailbox"
BASE.mkdir(parents=True, exist_ok=True)
COMMANDS = BASE / "commands.ndjson"
RESULTS = BASE / "results.ndjson"

# ensure files exist
COMMANDS.touch(exist_ok=True)
RESULTS.touch(exist_ok=True)

_lock = threading.Lock()


class Mailbox:
    def __init__(self, commands_path: Path = COMMANDS, results_path: Path = RESULTS):
        """Initialize Mailbox with commands_path, results_path."""
        self.commands_path = commands_path
        self.results_path = results_path

    def append_command(self, obj: dict[str, Any]) -> None:
        with _lock, open(self.commands_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    def append_result(self, obj: dict[str, Any]) -> None:
        with _lock, open(self.results_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    def read_commands(self) -> list[dict[str, Any]]:
        with _lock:
            try:
                with open(self.commands_path, encoding="utf-8") as f:
                    return [json.loads(line) for line in f if line.strip()]
            except Exception:
                return []

    def consume_commands(self) -> Iterable[dict[str, Any]]:
        """Read and clear commands atomically. Returns all commands.

        Note: This truncates the commands file after reading. Callers should
        ensure they process/commit results before returning.
        """
        with _lock:
            cmds = self.read_commands()
            # truncate file
            with open(self.commands_path, "w", encoding="utf-8"):
                pass
        return cmds

    def read_results(self) -> list[dict[str, Any]]:
        with _lock:
            try:
                with open(self.results_path, encoding="utf-8") as f:
                    return [json.loads(line) for line in f if line.strip()]
            except Exception:
                return []
