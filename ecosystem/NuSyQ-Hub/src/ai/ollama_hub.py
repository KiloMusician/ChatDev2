"""KILO-FOOLISH Ollama Hub.

Central hub for Ollama model management.

OmniTag: {"purpose": "file_systematically_tagged", "tags": ["Python", "Ollama"], "category": "auto_tagged", "evolution_stage": "v1.0"}
MegaTag: OLLAMA⨳HUB→MODEL_REGISTRY
"""

from typing import Any

from src.ai.ollama_integration import ollama


class OllamaHub:
    def __init__(self) -> None:
        """Initialize OllamaHub."""
        self.ollama = ollama
        self.available_models: list[Any] = []

    def list_models(self) -> list[Any]:
        """List available Ollama models via the integration API."""
        try:
            models = self.ollama.list_models()
            # Cache for reuse
            self.available_models = models or []
            return self.available_models
        except (AttributeError, RuntimeError, TypeError):
            return []

    def load_model(self, model_name: str) -> bool:
        """Load a specific model by pulling it if not available.

        Args:
            model_name: Name of the Ollama model to load (e.g., 'llama2', 'mistral')

        Returns:
            True if model is loaded successfully, False otherwise
        """
        try:
            if not self.ollama.is_available():
                return False

            # Check if model is already available
            current_models = self.list_models()
            if any(model_name in str(m) for m in current_models):
                return True

            # Attempt to pull the model
            # Some integrations expose `pull`, others provide `ensure_model`
            if hasattr(self.ollama, "pull"):
                result = self.ollama.pull(model_name)
            elif hasattr(self.ollama, "ensure_model"):
                result = self.ollama.ensure_model(model_name)
            else:
                return False
            return bool(result)
        except (AttributeError, RuntimeError, TypeError):
            return False


# Global instance
ollama_hub = OllamaHub()
