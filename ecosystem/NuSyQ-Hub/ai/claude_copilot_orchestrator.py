"""Lightweight compatibility stub for Claude/Copilot orchestrator used by tests.

Provides a minimal `ClaudeCopilotOrchestrator` to satisfy imports and basic
health checks during test runs.
"""

from typing import Any


class ClaudeCopilotOrchestrator:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.ready = False

    def start(self) -> bool:
        self.ready = True
        return self.ready

    def status(self) -> dict:
        return {"ready": self.ready}


def get_orchestrator() -> ClaudeCopilotOrchestrator:
    return ClaudeCopilotOrchestrator()
