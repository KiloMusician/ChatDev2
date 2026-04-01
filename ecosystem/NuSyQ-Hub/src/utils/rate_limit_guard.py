"""Persistent agent rate-limit state guard.

Tracks which agents are currently rate-limited and for how long, persisting
state to ``state/agent_rate_limits.json`` so the information survives process
restarts (e.g. Codex rate-limited for 72 hours).

Usage::

    guard = RateLimitGuard()

    # Check before calling an agent
    if guard.is_rate_limited("codex"):
        # skip codex, go to fallback
        ...

    # Record a rate-limit detection
    guard.mark_rate_limited("codex", duration_hours=72)

    # Manually clear (e.g. after successful call confirms limit lifted)
    guard.clear_rate_limit("codex")

    # List all currently-limited agents
    guard.get_limited_agents()  # -> [{"agent": "codex", "until": "...", ...}]
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

UTC = UTC

# Default state file path (overridable via env var)
_DEFAULT_STATE_FILE = Path(__file__).resolve().parents[2] / "state" / "agent_rate_limits.json"


class RateLimitGuard:
    """Persistent rate-limit state for agent routing.

    Thread-safe for single-process use; uses atomic read/write for multi-process
    safety (last writer wins, which is acceptable for rate-limit TTL tracking).
    """

    def __init__(self, state_file: Path | None = None) -> None:
        env_override = os.getenv("NUSYQ_RATE_LIMIT_STATE_FILE", "").strip()
        self._state_file: Path = (
            Path(env_override) if env_override else (state_file or _DEFAULT_STATE_FILE)
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def is_rate_limited(self, agent: str) -> bool:
        """Return True if agent is currently within its rate-limit window."""
        state = self._load()
        entry = state.get(agent.lower().strip())
        if not entry:
            return False
        try:
            until = datetime.fromisoformat(entry["until"])
            # Make timezone-aware if needed
            if until.tzinfo is None:
                until = until.replace(tzinfo=UTC)
            return datetime.now(UTC) < until
        except (KeyError, ValueError, TypeError):
            return False

    def mark_rate_limited(
        self,
        agent: str,
        *,
        duration_hours: float = 72.0,
        reason: str = "",
    ) -> None:
        """Record that an agent is rate-limited for ``duration_hours`` hours.

        Args:
            agent: Agent name (e.g. "codex", "claude_cli", "copilot").
            duration_hours: How long to treat the agent as rate-limited.
            reason: Optional human-readable reason (logged and stored).
        """
        from datetime import timedelta

        agent_key = agent.lower().strip()
        until = datetime.now(UTC) + timedelta(hours=duration_hours)
        state = self._load()
        state[agent_key] = {
            "agent": agent_key,
            "until": until.isoformat(),
            "duration_hours": duration_hours,
            "marked_at": datetime.now(UTC).isoformat(),
            "reason": reason or "rate_limit_detected",
        }
        self._save(state)
        logger.warning(
            "Agent %s marked rate-limited for %.1fh (until %s). Reason: %s",
            agent_key,
            duration_hours,
            until.strftime("%Y-%m-%d %H:%M UTC"),
            reason or "rate_limit_detected",
        )

    def clear_rate_limit(self, agent: str) -> bool:
        """Remove a rate-limit entry for an agent.

        Returns True if an entry was found and removed, False otherwise.
        """
        agent_key = agent.lower().strip()
        state = self._load()
        if agent_key in state:
            del state[agent_key]
            self._save(state)
            logger.info("Rate-limit cleared for agent: %s", agent_key)
            return True
        return False

    def get_limited_agents(self) -> list[dict[str, Any]]:
        """Return list of agents currently within their rate-limit window."""
        state = self._load()
        now = datetime.now(UTC)
        active: list[dict[str, Any]] = []
        stale: list[str] = []
        for agent_key, entry in state.items():
            try:
                until = datetime.fromisoformat(entry["until"])
                if until.tzinfo is None:
                    until = until.replace(tzinfo=UTC)
                if now < until:
                    remaining_h = (until - now).total_seconds() / 3600
                    active.append({**entry, "remaining_hours": round(remaining_h, 2)})
                else:
                    stale.append(agent_key)
            except (KeyError, ValueError, TypeError):
                stale.append(agent_key)
        # Prune expired entries lazily
        if stale:
            for key in stale:
                del state[key]
            self._save(state)
        return active

    def status_summary(self) -> dict[str, Any]:
        """Return a dict summarizing all rate-limit state (for health checks)."""
        limited = self.get_limited_agents()
        return {
            "rate_limited_agents": [e["agent"] for e in limited],
            "details": limited,
            "state_file": str(self._state_file),
        }

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _load(self) -> dict[str, Any]:
        try:
            if self._state_file.exists():
                data = json.loads(self._state_file.read_text(encoding="utf-8"))
                return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError, ValueError):
            pass
        return {}

    def _save(self, state: dict[str, Any]) -> None:
        try:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            self._state_file.write_text(
                json.dumps(state, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.warning("Could not persist rate-limit state: %s", exc)


# Module-level singleton (lazy-init, safe to import)
_guard: RateLimitGuard | None = None


def get_rate_limit_guard() -> RateLimitGuard:
    """Return the shared RateLimitGuard singleton."""
    global _guard
    if _guard is None:
        _guard = RateLimitGuard()
    return _guard
