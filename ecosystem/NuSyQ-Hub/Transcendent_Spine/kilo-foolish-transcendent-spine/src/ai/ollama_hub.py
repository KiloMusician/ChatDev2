"""KILO-FOOLISH Ollama Hub
Central hub for Ollama model management.
"""

import logging

from .ollama_integration import ollama


class OllamaHub:
    def __init__(self):
        self.ollama = ollama
        self.available_models = []

    def list_models(self):
        """List available Ollama models."""
        try:
            self.ollama.generate("", "", stream=False)
            # This would typically call the /api/tags endpoint
            return self.available_models
        except (ConnectionError, TimeoutError, ValueError) as e:
            logging.debug(f"Failed to list Ollama models: {e}")
            return []

    def load_model(self, model_name):
        """Load a specific model."""
        # Placeholder for model loading logic
        return True


# Global instance
ollama_hub = OllamaHub()
