"""Lightweight ChatDev integration stub for testing and CI.

Provides a minimal API compatible with ChatDev client usage patterns in the
repository. Returns deterministic stubbed outputs and does not perform any
network requests.
"""

from __future__ import annotations

from typing import Any


class ChatDevClient:
    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Initialize ChatDevClient."""
        self._meta = {"stub": True}

    def generate(
        self, prompt: str, *, temperature: float = 0.0, timeout: int = 60
    ) -> dict[str, Any]:
        """Synchronous stubbed generation API.

        The additional parameters are echoed back in the response so callers
        that inspect them continue to work during tests.
        """
        return {
            "text": "[chatdev-stub] " + (prompt or ""),
            "success": True,
            "temperature": temperature,
            "timeout": timeout,
        }

    async def generate_async(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        # Use an asynchronous scheduling point to satisfy async callers and linters
        import asyncio

        await asyncio.sleep(0)
        # forward known options to the sync implementation when present
        temperature = kwargs.get("temperature", 0.0)
        timeout = kwargs.get("timeout", 60)
        return self.generate(prompt=prompt, temperature=temperature, timeout=timeout)


def get_client(*args: Any, **kwargs: Any) -> ChatDevClient:
    return ChatDevClient(*args, **kwargs)
