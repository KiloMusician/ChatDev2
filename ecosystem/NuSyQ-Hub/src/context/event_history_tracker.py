"""Event History Tracker - ZETA09 Phase 1.

Tracks all system events (errors, recoveries, agent decisions, status changes)
for context-aware decision making and pattern analysis.

OmniTag: {
    "purpose": "context_awareness_event_tracking",
    "tags": ["event_logging", "context", "analytics", "awareness"],
    "category": "consciousness_system",
    "evolution_stage": "v1.0_zeta09_phase1"
}
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Types of events that can be tracked."""

    ERROR = "error"
    RECOVERY = "recovery"
    AGENT_DECISION = "agent_decision"
    SYSTEM_STATUS = "system_status"
    AUTOMATIC_ACTION = "automatic_action"
    TEST_EXECUTION = "test_execution"
    GIT_OPERATION = "git_operation"


class EventSeverity(str, Enum):
    """Severity levels for events."""

    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class EventOutcome(str, Enum):
    """Outcome of an event or recovery attempt."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    PENDING = "pending"


@dataclass
class EventContext:
    """Context information for an event."""

    file: str | None = None
    module: str | None = None
    error_code: str | None = None
    ai_agent: str | None = None  # copilot, ollama, chatdev, etc.
    rule_code: str | None = None
    git_branch: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class EventMetrics:
    """Metrics associated with an event."""

    duration_ms: int = 0
    tokens_used: int = 0
    recovery_attempts: int = 0
    success_rate: float = 0.0
    memory_mb: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemEvent:
    """A tracked system event for context awareness and analysis."""

    event_id: str
    timestamp: str  # ISO 8601 format
    event_type: EventType
    severity: EventSeverity
    source: str  # "system", "agent", "automation", etc.
    title: str
    description: str
    context: EventContext = field(default_factory=EventContext)
    outcome: EventOutcome = EventOutcome.PENDING
    metrics: EventMetrics = field(default_factory=EventMetrics)
    tags: list[str] = field(default_factory=list)
    related_events: list[str] = field(default_factory=list)  # Event IDs


class EventHistoryTracker:
    """Tracks system events for context awareness and analysis.

    ZETA09 Phase 1 core component that maintains a comprehensive
    event log enabling:
    - Pattern analysis (which errors recur most often)
    - Recovery effectiveness (success rates by strategy)
    - AI agent performance (decisions, outcomes)
    - System health trending (error patterns over time)
    """

    def __init__(self, storage_path: Path | None = None) -> None:
        """Initialize the event history tracker.

        Args:
            storage_path: Path to event_history.jsonl file. If None,
                uses default path (state/event_history.jsonl).
        """
        self.storage_path = storage_path or self._default_storage_path()
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.event_counter = self._load_event_counter()
        logger.info(f"Initialized EventHistoryTracker at {self.storage_path}")

    @staticmethod
    def _default_storage_path() -> Path:
        """Get default event storage path."""
        return Path(__file__).parent.parent.parent / "state" / "event_history.jsonl"

    def _load_event_counter(self) -> int:
        """Load the current event counter to ensure unique IDs."""
        if not self.storage_path.exists():
            return 0

        count = 0
        try:
            with open(self.storage_path, encoding="utf-8") as f:
                for _ in f:
                    count += 1
        except Exception as e:
            logger.error(f"Error loading event counter: {e}")

        return count

    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        self.event_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"evt_{timestamp}_{self.event_counter:06d}"

    def log_event(
        self,
        event_type: EventType,
        severity: EventSeverity,
        title: str,
        description: str = "",
        source: str = "system",
        context: EventContext | None = None,
        outcome: EventOutcome = EventOutcome.PENDING,
        metrics: EventMetrics | None = None,
        tags: list[str] | None = None,
    ) -> SystemEvent:
        """Log a system event.

        Args:
            event_type: Type of event
            severity: Severity level
            title: Short event title
            description: Detailed description
            source: Where the event originated
            context: Contextual information
            outcome: Event outcome (default: PENDING)
            metrics: Associated metrics
            tags: Event tags for categorization

        Returns:
            The created SystemEvent object
        """
        event = SystemEvent(
            event_id=self._generate_event_id(),
            timestamp=datetime.now().isoformat() + "Z",
            event_type=event_type,
            severity=severity,
            source=source,
            title=title,
            description=description,
            context=context or EventContext(),
            outcome=outcome,
            metrics=metrics or EventMetrics(),
            tags=tags or [],
        )

        self._persist_event(event)
        logger.debug(f"Logged event: {event.event_id} - {title}")
        return event

    def _persist_event(self, event: SystemEvent) -> None:
        """Persist an event to JSONL storage.

        Args:
            event: Event to persist
        """
        try:
            event_dict = asdict(event)
            # Convert enums to strings
            event_dict["event_type"] = event.event_type.value
            event_dict["severity"] = event.severity.value
            event_dict["outcome"] = event.outcome.value
            event_dict["context"]["extra"] = event_dict["context"].get("extra", {})
            event_dict["metrics"]["extra"] = event_dict["metrics"].get("extra", {})

            with open(self.storage_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_dict) + "\n")
        except Exception as e:
            logger.error(f"Failed to persist event {event.event_id}: {e}")

    def get_recent_events(self, hours: int = 24) -> list[SystemEvent]:
        """Get events from the last N hours.

        Args:
            hours: Number of hours to look back

        Returns:
            List of events within the time window
        """
        cutoff_time = datetime.now(UTC) - timedelta(hours=hours)
        events = []

        try:
            with open(self.storage_path, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        event_dict = json.loads(line)
                        event_time = datetime.fromisoformat(
                            event_dict["timestamp"].replace("Z", "+00:00")
                        )

                        if event_time >= cutoff_time:
                            events.append(self._dict_to_event(event_dict))
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Error parsing event line: {e}")

        except FileNotFoundError:
            logger.debug("Event history file not found")

        return events

    def get_events_by_type(self, event_type: EventType) -> list[SystemEvent]:
        """Get all events of a specific type.

        Args:
            event_type: Type of event to filter by

        Returns:
            List of events matching the type
        """
        events = []

        try:
            with open(self.storage_path, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        event_dict = json.loads(line)
                        if event_dict.get("event_type") == event_type.value:
                            events.append(self._dict_to_event(event_dict))
                    except (json.JSONDecodeError, ValueError):
                        logger.debug("Suppressed ValueError/json", exc_info=True)

        except FileNotFoundError:
            logger.debug("Event history file not found")

        return events

    def get_error_patterns(self, window_days: int = 7) -> dict[str, int]:
        """Analyze error patterns from the last N days.

        Args:
            window_days: Number of days to analyze

        Returns:
            Dictionary mapping error codes to occurrence counts
        """
        cutoff_time = datetime.now(UTC) - timedelta(days=window_days)
        error_counts: dict[str, int] = {}

        try:
            with open(self.storage_path, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        event_dict = json.loads(line)

                        if event_dict.get("event_type") != "error":
                            continue

                        event_time = datetime.fromisoformat(
                            event_dict["timestamp"].replace("Z", "+00:00")
                        )
                        if event_time < cutoff_time:
                            continue

                        error_code = event_dict.get("context", {}).get("error_code", "unknown")
                        error_counts[error_code] = error_counts.get(error_code, 0) + 1

                    except (json.JSONDecodeError, ValueError):
                        logger.debug("Suppressed ValueError/json", exc_info=True)

        except FileNotFoundError:
            logger.debug("Event history file not found")

        # Sort by frequency
        return dict(sorted(error_counts.items(), key=lambda x: x[1], reverse=True))

    def get_recovery_effectiveness(self) -> dict[str, Any]:
        """Analyze recovery effectiveness from event history.

        Returns:
            Dictionary with recovery statistics
        """
        recovery_events = self.get_events_by_type(EventType.RECOVERY)

        if not recovery_events:
            return {
                "total_recoveries": 0,
                "success_rate": 0.0,
                "avg_attempts": 0.0,
            }

        successes = sum(1 for e in recovery_events if e.outcome == EventOutcome.SUCCESS)
        total = len(recovery_events)
        avg_attempts = (
            sum(e.metrics.recovery_attempts for e in recovery_events) / total if total > 0 else 0
        )

        return {
            "total_recoveries": total,
            "successful": successes,
            "failed": total - successes,
            "success_rate": 100 * successes / total if total > 0 else 0,
            "avg_recovery_attempts": avg_attempts,
        }

    def get_ai_agent_activity(self) -> dict[str, int]:
        """Get activity statistics by AI agent.

        Returns:
            Dictionary mapping agent names to event counts
        """
        agent_counts: dict[str, int] = {}

        for hours in [24, 7 * 24, 30 * 24]:  # Last day, week, month
            events = self.get_recent_events(hours=hours)

            for event in events:
                if event.context.ai_agent:
                    agent = event.context.ai_agent
                    agent_counts[agent] = agent_counts.get(agent, 0) + 1

        return agent_counts

    @staticmethod
    def _dict_to_event(event_dict: dict[str, Any]) -> SystemEvent:
        """Convert a dictionary back to a SystemEvent object.

        Args:
            event_dict: Dictionary representation of event

        Returns:
            SystemEvent object
        """
        context_dict = event_dict.get("context", {})
        context = EventContext(
            file=context_dict.get("file"),
            module=context_dict.get("module"),
            error_code=context_dict.get("error_code"),
            ai_agent=context_dict.get("ai_agent"),
            rule_code=context_dict.get("rule_code"),
            git_branch=context_dict.get("git_branch"),
            extra=context_dict.get("extra", {}),
        )

        metrics_dict = event_dict.get("metrics", {})
        metrics = EventMetrics(
            duration_ms=metrics_dict.get("duration_ms", 0),
            tokens_used=metrics_dict.get("tokens_used", 0),
            recovery_attempts=metrics_dict.get("recovery_attempts", 0),
            success_rate=metrics_dict.get("success_rate", 0.0),
            memory_mb=metrics_dict.get("memory_mb", 0),
            extra=metrics_dict.get("extra", {}),
        )

        return SystemEvent(
            event_id=event_dict["event_id"],
            timestamp=event_dict["timestamp"],
            event_type=EventType(event_dict["event_type"]),
            severity=EventSeverity(event_dict["severity"]),
            source=event_dict.get("source", "system"),
            title=event_dict.get("title", ""),
            description=event_dict.get("description", ""),
            context=context,
            outcome=EventOutcome(event_dict.get("outcome", "pending")),
            metrics=metrics,
            tags=event_dict.get("tags", []),
            related_events=event_dict.get("related_events", []),
        )

    def get_event_summary(self) -> dict[str, Any]:
        """Get summary statistics of all tracked events.

        Returns:
            Dictionary with event statistics
        """
        all_events = {
            "errors": self.get_events_by_type(EventType.ERROR),
            "recoveries": self.get_events_by_type(EventType.RECOVERY),
            "decisions": self.get_events_by_type(EventType.AGENT_DECISION),
            "status": self.get_events_by_type(EventType.SYSTEM_STATUS),
        }

        return {
            "total_events": sum(len(events) for events in all_events.values()),
            "by_type": {k: len(v) for k, v in all_events.items()},
            "error_patterns": self.get_error_patterns(),
            "recovery_effectiveness": self.get_recovery_effectiveness(),
            "ai_agent_activity": self.get_ai_agent_activity(),
        }
