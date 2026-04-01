"""Game Analytics and Telemetry — Track and analyze gameplay metrics.

Provides telemetry collection, metrics aggregation, and analytics dashboards
for the NuSyQ game systems. Supports event logging, session tracking, and
performance analysis.

Zeta39: Implement game analytics and telemetry.

OmniTag: {
    "purpose": "game_analytics",
    "tags": ["Games", "Analytics", "Telemetry", "Metrics"],
    "category": "observability",
    "evolution_stage": "v1.0"
}
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

ANALYTICS_DIR = Path("state/game_analytics")
EVENTS_FILE = ANALYTICS_DIR / "events.jsonl"
METRICS_FILE = ANALYTICS_DIR / "metrics.json"


@dataclass
class GameEvent:
    """A single game event for telemetry."""

    event_type: str
    timestamp: str
    player_id: str = "default"
    session_id: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Convert to JSON line."""
        return json.dumps(asdict(self))


@dataclass
class SessionMetrics:
    """Metrics for a game session."""

    session_id: str
    player_id: str
    started_at: str
    ended_at: str | None = None
    duration_seconds: float = 0.0
    quests_started: int = 0
    quests_completed: int = 0
    xp_earned: int = 0
    achievements_unlocked: int = 0
    games_played: int = 0
    games_won: int = 0


@dataclass
class PlayerAnalytics:
    """Aggregated analytics for a player."""

    player_id: str
    total_sessions: int = 0
    total_play_time_hours: float = 0.0
    total_xp: int = 0
    total_quests_completed: int = 0
    total_achievements: int = 0
    favorite_game: str = ""
    win_rate: float = 0.0
    avg_session_minutes: float = 0.0
    last_active: str = ""


class GameAnalytics:
    """Collects and analyzes game telemetry."""

    def __init__(self, analytics_dir: Path | None = None):
        """Initialize the analytics system.

        Args:
            analytics_dir: Directory for analytics data.
        """
        self.dir = analytics_dir or ANALYTICS_DIR
        self.dir.mkdir(parents=True, exist_ok=True)
        self.events_file = self.dir / "events.jsonl"
        self.metrics_file = self.dir / "metrics.json"

        self._current_session: SessionMetrics | None = None
        self._event_buffer: list[GameEvent] = []
        self._metrics: dict[str, Any] = self._load_metrics()

    def _load_metrics(self) -> dict[str, Any]:
        """Load metrics from disk."""
        if self.metrics_file.exists():
            try:
                return json.loads(self.metrics_file.read_text())
            except Exception as e:
                logger.warning(f"Failed to load metrics: {e}")
        return {
            "total_events": 0,
            "total_sessions": 0,
            "event_counts": {},
            "player_stats": {},
        }

    def _save_metrics(self) -> None:
        """Save metrics to disk."""
        try:
            self.metrics_file.write_text(json.dumps(self._metrics, indent=2))
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def start_session(self, player_id: str = "default") -> str:
        """Start a new game session.

        Returns:
            Session ID.
        """
        session_id = f"session_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{player_id}"
        self._current_session = SessionMetrics(
            session_id=session_id,
            player_id=player_id,
            started_at=datetime.now(UTC).isoformat(),
        )
        self._metrics["total_sessions"] += 1
        self.track_event("session_start", {"player_id": player_id})
        logger.info(f"Started session: {session_id}")
        return session_id

    def end_session(self) -> SessionMetrics | None:
        """End the current session.

        Returns:
            Session metrics or None if no session.
        """
        if not self._current_session:
            return None

        self._current_session.ended_at = datetime.now(UTC).isoformat()

        # Calculate duration
        start = datetime.fromisoformat(self._current_session.started_at)
        end = datetime.fromisoformat(self._current_session.ended_at)
        self._current_session.duration_seconds = (end - start).total_seconds()

        # Flush events
        self._flush_events()
        self._save_metrics()

        self.track_event("session_end", asdict(self._current_session))
        logger.info(f"Ended session: {self._current_session.session_id}")

        session = self._current_session
        self._current_session = None
        return session

    def track_event(
        self,
        event_type: str,
        data: dict[str, Any] | None = None,
        player_id: str | None = None,
    ) -> None:
        """Track a game event.

        Args:
            event_type: Type of event.
            data: Event data.
            player_id: Override player ID.
        """
        event = GameEvent(
            event_type=event_type,
            timestamp=datetime.now(UTC).isoformat(),
            player_id=player_id
            or (self._current_session.player_id if self._current_session else "default"),
            session_id=self._current_session.session_id if self._current_session else "",
            data=data or {},
        )

        self._event_buffer.append(event)
        self._metrics["total_events"] += 1

        # Update event counts
        counts = self._metrics.get("event_counts", {})
        counts[event_type] = counts.get(event_type, 0) + 1
        self._metrics["event_counts"] = counts

        # Update session metrics
        if self._current_session:
            if event_type == "quest_start":
                self._current_session.quests_started += 1
            elif event_type == "quest_complete":
                self._current_session.quests_completed += 1
                self._current_session.xp_earned += data.get("xp", 0) if data else 0
            elif event_type == "achievement_unlock":
                self._current_session.achievements_unlocked += 1
            elif event_type == "game_play":
                self._current_session.games_played += 1
            elif event_type == "game_win":
                self._current_session.games_won += 1

        # Flush if buffer is large
        if len(self._event_buffer) >= 100:
            self._flush_events()

    def _flush_events(self) -> None:
        """Flush event buffer to disk."""
        if not self._event_buffer:
            return

        try:
            with open(self.events_file, "a") as f:
                for event in self._event_buffer:
                    f.write(event.to_json() + "\n")
            self._event_buffer.clear()
        except Exception as e:
            logger.error(f"Failed to flush events: {e}")

    def track_quest_complete(self, quest_id: str, quest_name: str, xp: int) -> None:
        """Track quest completion."""
        self.track_event(
            "quest_complete", {"quest_id": quest_id, "quest_name": quest_name, "xp": xp}
        )

    def track_achievement(self, achievement_id: str, name: str, points: int) -> None:
        """Track achievement unlock."""
        self.track_event(
            "achievement_unlock", {"achievement_id": achievement_id, "name": name, "points": points}
        )

    def track_game_result(self, game_name: str, won: bool, score: int, xp: int) -> None:
        """Track mini-game result."""
        event_type = "game_win" if won else "game_loss"
        self.track_event(event_type, {"game": game_name, "score": score, "xp": xp})
        self.track_event("game_play", {"game": game_name})

    def track_level_up(self, old_level: int, new_level: int) -> None:
        """Track level up."""
        self.track_event("level_up", {"old_level": old_level, "new_level": new_level})

    def get_event_counts(self) -> dict[str, int]:
        """Get event type counts."""
        return self._metrics.get("event_counts", {})

    def get_recent_events(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent events from log."""
        events = []
        if self.events_file.exists():
            try:
                lines = self.events_file.read_text().strip().split("\n")
                for line in lines[-limit:]:
                    if line:
                        events.append(json.loads(line))
            except Exception as e:
                logger.warning(f"Failed to read events: {e}")
        return events

    def get_player_analytics(self, player_id: str = "default") -> PlayerAnalytics:
        """Get aggregated analytics for a player."""
        stats = self._metrics.get("player_stats", {}).get(player_id, {})
        return PlayerAnalytics(
            player_id=player_id,
            total_sessions=stats.get("sessions", 0),
            total_play_time_hours=stats.get("play_time_hours", 0.0),
            total_xp=stats.get("total_xp", 0),
            total_quests_completed=stats.get("quests_completed", 0),
            total_achievements=stats.get("achievements", 0),
            favorite_game=stats.get("favorite_game", ""),
            win_rate=stats.get("win_rate", 0.0),
            avg_session_minutes=stats.get("avg_session_minutes", 0.0),
            last_active=stats.get("last_active", ""),
        )

    def get_dashboard_summary(self) -> dict[str, Any]:
        """Get a summary for dashboard display."""
        return {
            "total_events": self._metrics.get("total_events", 0),
            "total_sessions": self._metrics.get("total_sessions", 0),
            "event_counts": self._metrics.get("event_counts", {}),
            "active_session": self._current_session.session_id if self._current_session else None,
            "buffer_size": len(self._event_buffer),
        }


# Module-level instance
_analytics: GameAnalytics | None = None


def get_analytics() -> GameAnalytics:
    """Get or create the global analytics instance."""
    global _analytics
    if _analytics is None:
        _analytics = GameAnalytics()
    return _analytics


# Convenience functions
def track(event_type: str, data: dict[str, Any] | None = None) -> None:
    """Track an event."""
    get_analytics().track_event(event_type, data)


def start_session(player_id: str = "default") -> str:
    """Start a session."""
    return get_analytics().start_session(player_id)


def end_session() -> SessionMetrics | None:
    """End the current session."""
    return get_analytics().end_session()


def quest_completed(quest_id: str, quest_name: str, xp: int) -> None:
    """Track quest completion."""
    get_analytics().track_quest_complete(quest_id, quest_name, xp)


def game_played(game_name: str, won: bool, score: int, xp: int) -> None:
    """Track game result."""
    get_analytics().track_game_result(game_name, won, score, xp)


def get_summary() -> dict[str, Any]:
    """Get dashboard summary."""
    return get_analytics().get_dashboard_summary()


logger.info("Game analytics system loaded")
