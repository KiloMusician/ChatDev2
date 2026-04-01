"""Tests for ZETA09 Event History Tracker

Tests the context awareness event tracking infrastructure.
"""

import tempfile
from pathlib import Path

import pytest
from src.context.event_history_tracker import (
    EventContext,
    EventHistoryTracker,
    EventMetrics,
    EventOutcome,
    EventSeverity,
    EventType,
)


@pytest.fixture
def temp_event_file() -> Path:
    """Create a temporary event history file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        temp_path = Path(f.name)
    yield temp_path
    # Cleanup
    temp_path.unlink(missing_ok=True)


@pytest.fixture
def tracker(temp_event_file: Path) -> EventHistoryTracker:
    """Create a tracker instance with temp storage."""
    return EventHistoryTracker(storage_path=temp_event_file)


def test_tracker_initialization(tracker: EventHistoryTracker) -> None:
    """Test that tracker initializes properly."""
    assert tracker is not None
    assert tracker.storage_path is not None
    assert tracker.storage_path.parent.exists()


def test_log_simple_event(tracker: EventHistoryTracker) -> None:
    """Test logging a simple event."""
    event = tracker.log_event(
        event_type=EventType.ERROR,
        severity=EventSeverity.WARNING,
        title="Test Error",
        description="This is a test error event",
    )

    assert event is not None
    assert event.event_id.startswith("evt_")
    assert event.event_type == EventType.ERROR
    assert event.severity == EventSeverity.WARNING
    assert event.title == "Test Error"


def test_log_event_with_context(tracker: EventHistoryTracker) -> None:
    """Test logging event with contextual information."""
    context = EventContext(
        file="src/test.py", module="test_module", error_code="E402", ai_agent="copilot"
    )

    event = tracker.log_event(
        event_type=EventType.ERROR,
        severity=EventSeverity.ERROR,
        title="Import Order Error",
        context=context,
    )

    assert event.context.file == "src/test.py"
    assert event.context.error_code == "E402"
    assert event.context.ai_agent == "copilot"


def test_log_event_with_metrics(tracker: EventHistoryTracker) -> None:
    """Test logging event with performance metrics."""
    metrics = EventMetrics(
        duration_ms=500, tokens_used=1234, recovery_attempts=2, success_rate=0.85
    )

    event = tracker.log_event(
        event_type=EventType.RECOVERY,
        severity=EventSeverity.INFO,
        title="Recovery Completed",
        metrics=metrics,
        outcome=EventOutcome.SUCCESS,
    )

    assert event.metrics.duration_ms == 500
    assert event.metrics.tokens_used == 1234
    assert event.metrics.recovery_attempts == 2


def test_get_recent_events(tracker: EventHistoryTracker) -> None:
    """Test retrieving recent events."""
    # Log some events
    tracker.log_event(event_type=EventType.ERROR, severity=EventSeverity.INFO, title="Event 1")
    tracker.log_event(event_type=EventType.RECOVERY, severity=EventSeverity.INFO, title="Event 2")

    # Should get both events (within last 24 hours)
    recent = tracker.get_recent_events(hours=24)
    assert len(recent) >= 2


def test_get_events_by_type(tracker: EventHistoryTracker) -> None:
    """Test filtering events by type."""
    # Log different event types
    tracker.log_event(event_type=EventType.ERROR, severity=EventSeverity.ERROR, title="Error 1")
    tracker.log_event(
        event_type=EventType.RECOVERY, severity=EventSeverity.INFO, title="Recovery 1"
    )
    tracker.log_event(event_type=EventType.ERROR, severity=EventSeverity.WARNING, title="Error 2")

    # Get only errors
    errors = tracker.get_events_by_type(EventType.ERROR)
    assert len(errors) == 2
    assert all(e.event_type == EventType.ERROR for e in errors)

    # Get only recoveries
    recoveries = tracker.get_events_by_type(EventType.RECOVERY)
    assert len(recoveries) == 1


def test_error_pattern_analysis(tracker: EventHistoryTracker) -> None:
    """Test error pattern analysis."""
    # Log errors with different codes
    context_e402 = EventContext(error_code="E402")
    context_f401 = EventContext(error_code="F401")

    tracker.log_event(
        event_type=EventType.ERROR,
        severity=EventSeverity.ERROR,
        title="E402 Error 1",
        context=context_e402,
    )
    tracker.log_event(
        event_type=EventType.ERROR,
        severity=EventSeverity.ERROR,
        title="E402 Error 2",
        context=context_e402,
    )
    tracker.log_event(
        event_type=EventType.ERROR,
        severity=EventSeverity.ERROR,
        title="F401 Error",
        context=context_f401,
    )

    patterns = tracker.get_error_patterns()
    assert patterns["E402"] == 2
    assert patterns["F401"] == 1


def test_recovery_effectiveness(tracker: EventHistoryTracker) -> None:
    """Test recovery effectiveness statistics."""
    # Log successful recovery
    tracker.log_event(
        event_type=EventType.RECOVERY,
        severity=EventSeverity.INFO,
        title="Recovery Success",
        outcome=EventOutcome.SUCCESS,
        metrics=EventMetrics(recovery_attempts=1),
    )

    # Log failed recovery
    tracker.log_event(
        event_type=EventType.RECOVERY,
        severity=EventSeverity.WARNING,
        title="Recovery Failed",
        outcome=EventOutcome.FAILURE,
        metrics=EventMetrics(recovery_attempts=3),
    )

    effectiveness = tracker.get_recovery_effectiveness()
    assert effectiveness["total_recoveries"] == 2
    assert effectiveness["successful"] == 1
    assert effectiveness["failed"] == 1
    assert abs(effectiveness["success_rate"] - 50.0) < 0.1  # 50%


def test_ai_agent_activity(tracker: EventHistoryTracker) -> None:
    """Test AI agent activity tracking."""
    # Log events from different agents
    context_copilot = EventContext(ai_agent="copilot")
    context_ollama = EventContext(ai_agent="ollama")

    tracker.log_event(
        event_type=EventType.AGENT_DECISION,
        severity=EventSeverity.INFO,
        title="Copilot Decision",
        context=context_copilot,
    )
    tracker.log_event(
        event_type=EventType.AGENT_DECISION,
        severity=EventSeverity.INFO,
        title="Ollama Decision 1",
        context=context_ollama,
    )
    tracker.log_event(
        event_type=EventType.AGENT_DECISION,
        severity=EventSeverity.INFO,
        title="Ollama Decision 2",
        context=context_ollama,
    )

    activity = tracker.get_ai_agent_activity()
    assert activity.get("copilot", 0) > 0
    assert activity.get("ollama", 0) >= 1


def test_event_persistence(temp_event_file: Path) -> None:
    """Test that events are properly persisted to file."""
    tracker1 = EventHistoryTracker(storage_path=temp_event_file)

    # Log an event with first tracker
    event1 = tracker1.log_event(
        event_type=EventType.ERROR, severity=EventSeverity.ERROR, title="Persisted Event"
    )

    # Create another tracker instance reading same file
    tracker2 = EventHistoryTracker(storage_path=temp_event_file)

    # Should be able to retrieve the event
    errors = tracker2.get_events_by_type(EventType.ERROR)
    assert len(errors) > 0
    assert any(e.event_id == event1.event_id for e in errors)


def test_event_counter_increments(tracker: EventHistoryTracker) -> None:
    """Test that event counter increments properly."""
    event1 = tracker.log_event(
        event_type=EventType.ERROR, severity=EventSeverity.ERROR, title="Event 1"
    )
    event2 = tracker.log_event(
        event_type=EventType.ERROR, severity=EventSeverity.ERROR, title="Event 2"
    )

    # Event IDs should be different
    assert event1.event_id != event2.event_id
    # Second event counter should be higher
    assert int(event2.event_id.split("_")[-1]) > int(event1.event_id.split("_")[-1])


def test_event_summary(tracker: EventHistoryTracker) -> None:
    """Test event summary generation."""
    # Log various event types
    tracker.log_event(event_type=EventType.ERROR, severity=EventSeverity.ERROR, title="Error")
    tracker.log_event(event_type=EventType.RECOVERY, severity=EventSeverity.INFO, title="Recovery")
    tracker.log_event(
        event_type=EventType.AGENT_DECISION, severity=EventSeverity.INFO, title="Decision"
    )

    summary = tracker.get_event_summary()
    assert "total_events" in summary
    assert "by_type" in summary
    assert summary["by_type"]["errors"] >= 1
    assert summary["by_type"]["recoveries"] >= 1
    assert summary["by_type"]["decisions"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
