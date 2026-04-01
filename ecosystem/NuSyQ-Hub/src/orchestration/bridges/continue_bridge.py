"""Continue bridge — wraps the orchestration hub for Continue.dev integration."""

from __future__ import annotations

from typing import Any


class ContinueBridge:
    """Bridge that exposes Continue.dev integration via the hub."""

    def __init__(self, hub: Any) -> None:
        self.hub = hub
