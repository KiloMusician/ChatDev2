"""Intent router stub for NuSyQ spine."""

import subprocess
from typing import Any

from . import eventlog, state


class IntentRouter:
    def __init__(self) -> None:
        """Initialize router. State managed via module-level singleton."""

    def run_tool(self, tool_cmd: str, *, timeout: int = 60) -> dict[str, Any]:
        event = {"actor": "router", "action": "run_tool", "inputs": tool_cmd}
        eventlog.append_event(event)
        try:
            completed = subprocess.run(
                tool_cmd, shell=True, capture_output=True, text=True, timeout=timeout, check=False
            )
            out = completed.stdout or completed.stderr
            result = {
                "status": "success" if completed.returncode == 0 else "failed",
                "returncode": completed.returncode,
                "output": out,
            }
        except subprocess.SubprocessError as exc:
            result = {"status": "error", "error": str(exc)}
        event.update({"outputs": str(result.get("status"))})
        eventlog.append_event(event)
        # snapshot simple state
        state.snapshot_state({"last_run": tool_cmd, "last_status": result.get("status")})
        return result


ROUTER = IntentRouter()
