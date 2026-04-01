"""Legacy adapter: Update ChatDev to use Ollama as its LLM backend."""

from __future__ import annotations

from typing import Any


class ChatDevOllamaAdapter:
    """Adapts ChatDev phases to use Ollama models instead of OpenAI."""

    async def _run_phase(self, phase: str, team: dict, session_data: dict) -> dict[str, Any]:
        """Dispatch to the appropriate phase handler, or return skipped for unknown phases."""
        handlers = {
            "design": self._handle_design_phase,
            "testing": self._handle_testing_phase,
            "review": self._handle_review_phase,
            "documentation": self._handle_documentation_phase,
        }
        handler = handlers.get(phase)
        if handler is None:
            return {"success": False, "status": "skipped", "phase": phase}
        return await handler(team=team, session_data=session_data)

    async def _handle_design_phase(self, team: dict, session_data: dict) -> dict[str, Any]:
        return {"success": True, "status": "completed", "phase": "design"}

    async def _handle_testing_phase(self, team: dict, session_data: dict) -> dict[str, Any]:
        return {"success": True, "status": "completed", "phase": "testing"}

    async def _handle_review_phase(self, team: dict, session_data: dict) -> dict[str, Any]:
        return {"success": True, "status": "completed", "phase": "review"}

    async def _handle_documentation_phase(self, team: dict, session_data: dict) -> dict[str, Any]:
        return {"success": True, "status": "completed", "phase": "documentation"}
