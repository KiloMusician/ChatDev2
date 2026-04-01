"""MJOLNIR Protocol — Unified Agent Dispatch for NuSyQ-Hub.

Thin coordination layer wrapping AgentTaskRouter, GuildBoard, and SNS-Core
behind a single CLI entry point with context-aware routing and multi-agent patterns.

OmniTag: {
    "purpose": "dispatch_subsystem",
    "tags": ["MJOLNIR", "Dispatch", "AgentRouting", "MultiAgent"],
    "category": "orchestration",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.dispatch.agent_registry import (AgentAvailabilityRegistry,
                                             AgentProbeResult, AgentStatus)
    from src.dispatch.context_detector import ContextDetector, ContextMode
    from src.dispatch.mjolnir import MjolnirProtocol
    from src.dispatch.response_envelope import ResponseEnvelope

__version__ = "0.1.0"

__all__ = [
    "AgentAvailabilityRegistry",
    "AgentProbeResult",
    "AgentStatus",
    "ContextDetector",
    "ContextMode",
    "MjolnirProtocol",
    "ResponseEnvelope",
]


def __getattr__(name: str):
    if name == "MjolnirProtocol":
        from src.dispatch.mjolnir import MjolnirProtocol

        return MjolnirProtocol
    if name in ("AgentStatus", "AgentProbeResult", "AgentAvailabilityRegistry"):
        from src.dispatch.agent_registry import (AgentAvailabilityRegistry,
                                                 AgentProbeResult, AgentStatus)

        return locals()[name]
    if name in ("ContextMode", "ContextDetector"):
        from src.dispatch.context_detector import ContextDetector, ContextMode

        return locals()[name]
    if name == "ResponseEnvelope":
        from src.dispatch.response_envelope import ResponseEnvelope

        return ResponseEnvelope
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
