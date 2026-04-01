"""Lightweight compatibility stub for Ollama/ChatDev integrator used by tests.

Exports a minimal `OllamaChatDevIntegrator` class with the methods tests might
call. This is intentionally tiny and safe for import at test-collection time.
"""

from typing import Any


class OllamaChatDevIntegrator:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.available = False

    def is_available(self) -> bool:
        return self.available

    def ping(self) -> dict:
        return {"status": "stub", "available": self.available}


def get_integrator() -> OllamaChatDevIntegrator:
    return OllamaChatDevIntegrator()
