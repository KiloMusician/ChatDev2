"""Structured JSON response envelope for MJOLNIR Protocol.

Every MJOLNIR output follows this contract so Claude Code (and other callers)
can reliably parse results without fragile text scraping.

Fields:
    mjolnir (str): Protocol version identifier
    status (str): "ok" | "error" | "partial" | "timeout"
    success (bool): Whether the primary operation succeeded
    agent (str): Agent that handled the request (or "multi" for patterns)
    context_mode (str): Detected context mode (ecosystem/project/game)
    pattern (str): Dispatch pattern used (ask/council/parallel/chain/delegate/status)
    sns_applied (bool): Whether SNS-Core compression was applied
    output (Any): Primary result payload
    error (str | None): Error message if status != "ok"
    guild_quest_id (str | None): Guild board quest ID if tracking was enabled
    agents_used (list[str]): All agents consulted (for multi-agent patterns)
    timing_ms (float | None): Wall-clock time in milliseconds
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ResponseEnvelope:
    """Structured response container for all MJOLNIR outputs."""

    mjolnir: str = "0.1.0"
    status: str = "ok"
    success: bool = True
    agent: str = "unknown"
    context_mode: str = "auto"
    pattern: str = "ask"
    sns_applied: bool = False
    output: Any = None
    error: str | None = None
    guild_quest_id: str | None = None
    agents_used: list[str] = field(default_factory=list)
    timing_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict, dropping None values for cleaner JSON."""
        raw = asdict(self)
        return {k: v for k, v in raw.items() if v is not None}

    @classmethod
    def wrap(
        cls,
        result: Any,
        *,
        agent: str = "unknown",
        context_mode: str = "auto",
        pattern: str = "ask",
        sns_applied: bool = False,
        guild_quest_id: str | None = None,
        agents_used: list[str] | None = None,
        start_time: float | None = None,
    ) -> ResponseEnvelope:
        """Wrap a successful result into a response envelope.

        Args:
            result: Raw result from AgentTaskRouter or aggregated results
            agent: Primary agent name (or "multi" for patterns)
            context_mode: Detected context mode
            pattern: Dispatch pattern used
            sns_applied: Whether SNS-Core was applied to the prompt
            guild_quest_id: Guild board quest tracking ID
            agents_used: List of all agents consulted
            start_time: time.monotonic() value from before the call (for timing)
        """
        timing = None
        if start_time is not None:
            timing = round((time.monotonic() - start_time) * 1000, 1)

        # Extract status from router result if available
        status = "ok"
        success = True
        output = result

        if isinstance(result, dict):
            router_status = result.get("status", "")
            if router_status in ("failed", "error"):
                status = "error"
                success = False
            elif router_status == "timeout":
                status = "timeout"
                success = False
            output = result.get("output", result.get("result", result))

        return cls(
            status=status,
            success=success,
            agent=agent,
            context_mode=context_mode,
            pattern=pattern,
            sns_applied=sns_applied,
            output=output,
            guild_quest_id=guild_quest_id,
            agents_used=agents_used or ([agent] if agent != "unknown" else []),
            timing_ms=timing,
        )

    @classmethod
    def from_error(
        cls,
        message: str,
        *,
        agent: str = "unknown",
        context_mode: str = "auto",
        pattern: str = "ask",
        start_time: float | None = None,
    ) -> ResponseEnvelope:
        """Create an error response envelope."""
        timing = None
        if start_time is not None:
            timing = round((time.monotonic() - start_time) * 1000, 1)

        return cls(
            status="error",
            success=False,
            agent=agent,
            context_mode=context_mode,
            pattern=pattern,
            error=message,
            timing_ms=timing,
        )
