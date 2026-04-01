"""ConsciousnessLoop — thin adapter wiring SimulatedVerseUnifiedBridge into the orchestrator.

Responsibilities:
  - Lazy init of SimulatedVerseUnifiedBridge (never blocks startup)
  - 30s cache for breathing_factor (one filesystem read per 30s at most)
  - Graceful degradation: factor=1.0, auto-approve, empty state when unavailable
  - Fire-and-forget event logging (sync wrapper, never raises)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

_CACHE_TTL_S = 30.0  # seconds to cache the breathing factor


@dataclass
class ShipApproval:
    approved: bool
    reason: str


class ConsciousnessLoop:
    """Adapter between BackgroundTaskOrchestrator and SimulatedVerseUnifiedBridge."""

    def __init__(self) -> None:
        """Initialize ConsciousnessLoop."""
        self._bridge: Any | None = None
        self._initialized = False
        self._cached_factor: float = 1.0
        self._factor_expires_at: float = 0.0

    # ------------------------------------------------------------------
    # Initialization (call once from orchestrator.start())
    # ------------------------------------------------------------------

    def initialize(self) -> bool:
        """Try to connect to SimulatedVerseUnifiedBridge. Returns True on success."""
        if self._initialized:
            return self._bridge is not None
        self._initialized = True
        try:
            from src.integration.simulatedverse_unified_bridge import \
                SimulatedVerseUnifiedBridge

            self._bridge = SimulatedVerseUnifiedBridge()
            logger.info("ConsciousnessLoop: SimulatedVerse bridge connected")
            return True
        except Exception as exc:
            logger.info("ConsciousnessLoop: bridge unavailable (%s) — degraded mode", exc)
            self._bridge = None
            return False

    # ------------------------------------------------------------------
    # Breathing factor (cached, never raises)
    # ------------------------------------------------------------------

    @property
    def breathing_factor(self) -> float:
        """Return the current breathing multiplier (0.60-1.50). Cached 30s."""
        if self._bridge is None:
            return 1.0
        now = time.monotonic()
        if now < self._factor_expires_at:
            return self._cached_factor
        try:
            factor = float(self._bridge.get_breathing_factor())
            self._cached_factor = max(0.5, min(2.0, factor))  # guard extremes
            self._factor_expires_at = now + _CACHE_TTL_S
            logger.debug("Breathing factor refreshed: %.2f", self._cached_factor)
        except Exception as exc:
            logger.debug("ConsciousnessLoop: breathing factor fetch failed (%s)", exc)
        return self._cached_factor

    # ------------------------------------------------------------------
    # Culture Ship approval (never raises)
    # ------------------------------------------------------------------

    def request_approval(self, action: str, context: dict[str, Any]) -> ShipApproval:
        """Ask Culture Ship to approve a sensitive action. Auto-approves when unavailable."""
        if self._bridge is None:
            approval = ShipApproval(approved=True, reason="unavailable — auto-approved")
            self._emit_approval(action, approval)
            return approval
        try:
            result = self._bridge.request_ship_approval(action, context)
            approval = ShipApproval(
                approved=bool(getattr(result, "approved", True)),
                reason=str(getattr(result, "reasoning", getattr(result, "reason", ""))),
            )
            self._emit_approval(action, approval)
            return approval
        except Exception as exc:
            logger.debug("ConsciousnessLoop: approval check failed (%s) — auto-approving", exc)
            approval = ShipApproval(approved=True, reason=f"error — auto-approved: {exc}")
            self._emit_approval(action, approval)
            return approval

    def _emit_approval(self, action: str, approval: ShipApproval) -> None:
        """Emit approval decision to culture_ship terminal (fire-and-forget)."""
        try:
            from src.system.agent_awareness import emit as _emit

            _lvl = "WARNING" if not approval.approved else "INFO"
            _emit(
                "culture_ship",
                f"Approval: action={action[:60]} approved={approval.approved} reason={approval.reason[:80]}",
                level=_lvl,
                source="consciousness_loop",
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Event logging (fire-and-forget sync wrapper, never raises)
    # ------------------------------------------------------------------

    def emit_event_sync(self, event_type: str, data: dict[str, Any]) -> None:
        """Log an event to SimulatedVerse. Never raises. Safe to call anywhere."""
        if self._bridge is None:
            return
        try:
            self._bridge.log_event(event_type, data)
        except Exception as exc:
            logger.debug("ConsciousnessLoop: event emit failed (%s)", exc)

    # ------------------------------------------------------------------
    # Brief state (for start_nusyq.py brief output)
    # ------------------------------------------------------------------

    def get_brief_state(self) -> dict[str, Any]:
        """Return consciousness state dict for brief display. Never raises."""
        if self._bridge is None:
            return {
                "available": False,
                "stage": "dormant",
                "level": 0.0,
                "breathing_factor": 1.0,
                "directives": [],
            }
        try:
            snapshot = self._bridge.get_consciousness_state()
            directives = self._bridge.get_ship_directives()
            return {
                "available": True,
                "level": float(getattr(snapshot, "level", 0.0)),
                "stage": str(getattr(snapshot, "stage", "unknown")),
                "active_systems": list(getattr(snapshot, "active_systems", [])),
                "breathing_factor": self.breathing_factor,
                "directives": directives,
            }
        except Exception as exc:
            logger.debug("ConsciousnessLoop: get_brief_state failed (%s)", exc)
            return {
                "available": False,
                "stage": "error",
                "level": 0.0,
                "breathing_factor": 1.0,
                "directives": [],
            }
