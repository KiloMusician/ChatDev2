"""NuSyQ-Hub Service Managers.

This package contains service lifecycle managers for external dependencies
that NuSyQ-Hub orchestrates (Ollama, ChatDev, etc).

Key components:
- OllamaServiceManager: WSL-aware Ollama lifecycle management
- ensure_ollama(): Quick function to ensure Ollama is running

Usage:
    from src.services import ensure_ollama, get_ollama_status

    if ensure_ollama():
        # Ollama ready for LLM calls
        ...

    status = get_ollama_status()
    print(f"Models: {status.models_available}")
"""

from src.services.ollama_service_manager import (OllamaEnvironment,
                                                 OllamaServiceManager,
                                                 OllamaStatus, ensure_ollama,
                                                 get_ollama_status)

__all__ = [
    "OllamaEnvironment",
    "OllamaServiceManager",
    "OllamaStatus",
    "ensure_ollama",
    "get_ollama_status",
]
