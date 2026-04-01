"""Lightweight Ollama integration stub used for CI and local testing.

Provides a minimal, safe API compatible with the real Ollama client used
elsewhere in the codebase. This file is intentionally simple: it returns
deterministic stub responses and never performs network I/O.
"""

from __future__ import annotations

from typing import Any


class OllamaClient:
    """Minimal synchronous and async Ollama client stub."""

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Initialize OllamaClient."""
        # Accept arbitrary args to be a drop-in replacement
        self._meta = {"stub": True}

    def generate(self, prompt: str, _timeout: int = 30) -> dict[str, Any]:
        """Return a deterministic stubbed response for synchronous callers."""
        return {"text": "[ollama-stub] " + (prompt or ""), "ok": True}

    async def generate_async(self, prompt: str, timeout: int = 30) -> dict[str, Any]:
        """Async variant for callers using await.

        This implementation is synchronous internally but declared async to
        be usable with 'await' in tests and other async code paths.
        """
        return self.generate(prompt=prompt, timeout=timeout)


def get_client(*args: Any, **kwargs: Any) -> OllamaClient:
    """Factory used by integration code to obtain a client instance."""
    return OllamaClient(*args, **kwargs)
