"""Minimal MCP (Model Context Protocol) stub for local testing.

Provides a tiny client with basic connectivity checks and message sending so
that code expecting an MCP client can run in CI without real services.
"""

from __future__ import annotations

from typing import Any


class MCPClient:
    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Initialize MCPClient."""
        self._meta = {"stub": True}

    def ping(self) -> bool:
        return True

    def send(self, channel: str, payload: dict[str, Any]) -> dict[str, Any]:
        # Echo back the payload with a stubbed status
        return {"channel": channel, "payload": payload, "status": "stubbed"}

    async def send_async(self, channel: str, payload: dict[str, Any]) -> dict[str, Any]:
        # Minimal async implementation
        return self.send(channel, payload)


def get_client(*args: Any, **kwargs: Any) -> MCPClient:
    return MCPClient(*args, **kwargs)
