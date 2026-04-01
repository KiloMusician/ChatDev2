"""Legacy redirect for Ollama integration.

Canonical implementation:
    src/integration/ollama_integration.py
"""

from src.integration.ollama_integration import (EnhancedOllamaHub,
                                                KILOOllamaIntegration,
                                                OllamaIntegration,
                                                get_ollama_instance, ollama)

__all__ = [
    "EnhancedOllamaHub",
    "KILOOllamaIntegration",
    "OllamaIntegration",
    "get_ollama_instance",
    "ollama",
]
