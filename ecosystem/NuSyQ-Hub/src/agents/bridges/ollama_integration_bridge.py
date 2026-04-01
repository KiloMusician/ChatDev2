"""Ollama Integration Bridge - Hub-aware wrapper for Ollama calls."""

from typing import Any

from src.agents.agent_orchestration_hub import get_agent_orchestration_hub
from src.integration.ollama_integration import KILOOllamaIntegration
from src.LOGGING.modular_logging_system import get_logger

# Auto-recovery for Ollama
try:
    from src.services.ollama_service_manager import ensure_ollama
except ImportError:
    ensure_ollama = None  # Graceful degradation

logger = get_logger(__name__)


class OllamaIntegrationBridge:
    """Compatibility wrapper for Ollama interactions."""

    def __init__(self, host: str | None = None, hub: Any | None = None) -> None:
        """Initialize OllamaIntegrationBridge with host, hub."""
        self._integration = KILOOllamaIntegration(host=host)
        self._hub = hub or get_agent_orchestration_hub()

    async def generate(
        self,
        prompt: str,
        model: str = "qwen2.5-coder:7b",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate text via Ollama with hub fallback."""
        context = context or {}
        if context.get("simulate"):
            return {
                "success": True,
                "status": "success",
                "simulated": True,
                "model": model,
                "response": "",
            }

        hub_result = await self._hub.route_task(
            task_type="ollama_generate",
            description=prompt,
            context={**context, "model": model},
            target_service=context.get("target_service"),
        )
        normalized_hub_result = self._normalize_result(hub_result)
        if normalized_hub_result.get("status") != "error" or not context.get(
            "fallback_direct", True
        ):
            return normalized_hub_result

        direct_result = self._integration.generate(model=model, prompt=prompt)
        if not direct_result:
            # ── Auto-recovery before giving up ──────────────────────────────
            if ensure_ollama and ensure_ollama():
                direct_result = self._integration.generate(model=model, prompt=prompt)
            if not direct_result:
                return {
                    "success": False,
                    "status": "error",
                    "error": "Ollama unavailable (recovery failed)",
                }

        return {
            "success": True,
            "status": "success",
            "model": model,
            "response": direct_result.get("response", ""),
            "raw": direct_result,
        }

    @staticmethod
    def _normalize_result(result: Any) -> dict[str, Any]:
        """Normalize bridge responses to include explicit success status."""
        if not isinstance(result, dict):
            return {"success": False, "status": "error", "error": "Invalid hub response payload"}

        normalized = dict(result)
        if "success" not in normalized:
            normalized["success"] = normalized.get("status") in {"success", "ok"}
        return normalized


__all__ = ["OllamaIntegrationBridge"]
