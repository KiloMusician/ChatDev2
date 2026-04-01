"""Tests for src/utils/auto_recovery_watchdog.py - AutoRecoveryWatchdog.

Tests the watchdog system that detects and recovers from AI agent softlocks
and workflow failures in real-time.
"""

import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from src.utils.auto_recovery_watchdog import (
    AutoRecoveryWatchdog,
    WatchdogEvent,
    WatchdogState,
)

# =============================================================================
# Test WatchdogState Enum
# =============================================================================


class TestWatchdogState:
    """Tests for WatchdogState enum."""

    def test_idle_state_value(self) -> None:
        """IDLE state has correct value."""
        assert WatchdogState.IDLE.value == "idle"

    def test_monitoring_state_value(self) -> None:
        """MONITORING state has correct value."""
        assert WatchdogState.MONITORING.value == "monitoring"

    def test_warning_state_value(self) -> None:
        """WARNING state has correct value."""
        assert WatchdogState.WARNING.value == "warning"

    def test_recovering_state_value(self) -> None:
        """RECOVERING state has correct value."""
        assert WatchdogState.RECOVERING.value == "recovering"

    def test_escalated_state_value(self) -> None:
        """ESCALATED state has correct value."""
        assert WatchdogState.ESCALATED.value == "escalated"

    def test_enum_has_five_states(self) -> None:
        """Enum has exactly 5 states."""
        assert len(WatchdogState) == 5


# =============================================================================
# Test WatchdogEvent Dataclass
# =============================================================================


class TestWatchdogEvent:
    """Tests for WatchdogEvent dataclass."""

    def test_create_event(self) -> None:
        """Create event with all fields."""
        ts = datetime.now()
        event = WatchdogEvent(
            timestamp=ts,
            state=WatchdogState.MONITORING,
            message="Test event",
            context={"key": "value"},
        )
        assert event.timestamp == ts
        assert event.state == WatchdogState.MONITORING
        assert event.message == "Test event"
        assert event.context == {"key": "value"}

    def test_event_with_empty_context(self) -> None:
        """Create event with empty context."""
        event = WatchdogEvent(
            timestamp=datetime.now(),
            state=WatchdogState.IDLE,
            message="Empty context",
            context={},
        )
        assert event.context == {}


# =============================================================================
# Test AutoRecoveryWatchdog Initialization
# =============================================================================


class TestAutoRecoveryWatchdogInit:
    """Tests for AutoRecoveryWatchdog initialization."""

    def test_default_initialization(self) -> None:
        """Default initialization sets expected values."""
        watchdog = AutoRecoveryWatchdog()
        assert watchdog.timeout == 120.0
        assert watchdog.warning_threshold == 0.8
        assert watchdog.auto_recover is True
        assert watchdog.checkpoint_on_recovery is True

    def test_custom_timeout(self) -> None:
        """Custom timeout is set correctly."""
        watchdog = AutoRecoveryWatchdog(timeout=60.0)
        assert watchdog.timeout == 60.0

    def test_custom_warning_threshold(self) -> None:
        """Custom warning threshold is set correctly."""
        watchdog = AutoRecoveryWatchdog(warning_threshold=0.5)
        assert watchdog.warning_threshold == 0.5

    def test_auto_recover_disabled(self) -> None:
        """Auto recover can be disabled."""
        watchdog = AutoRecoveryWatchdog(auto_recover=False)
        assert watchdog.auto_recover is False

    def test_checkpoint_on_recovery_disabled(self) -> None:
        """Checkpoint on recovery can be disabled."""
        watchdog = AutoRecoveryWatchdog(checkpoint_on_recovery=False)
        assert watchdog.checkpoint_on_recovery is False

    def test_initial_state_is_idle(self) -> None:
        """Initial state is IDLE."""
        watchdog = AutoRecoveryWatchdog()
        assert watchdog.state == WatchdogState.IDLE

    def test_initial_start_time_is_none(self) -> None:
        """Initial start_time is None."""
        watchdog = AutoRecoveryWatchdog()
        assert watchdog.start_time is None

    def test_initial_events_is_empty_list(self) -> None:
        """Initial events list is empty."""
        watchdog = AutoRecoveryWatchdog()
        assert watchdog.events == []


# =============================================================================
# Test _log_event
# =============================================================================


class TestLogEvent:
    """Tests for _log_event method."""

    def test_log_event_appends_to_events(self) -> None:
        """_log_event appends event to events list."""
        watchdog = AutoRecoveryWatchdog()
        watchdog._log_event(WatchdogState.MONITORING, "Test message")
        assert len(watchdog.events) == 1
        assert watchdog.events[0].message == "Test message"

    def test_log_event_with_context(self) -> None:
        """_log_event stores context."""
        watchdog = AutoRecoveryWatchdog()
        watchdog._log_event(
            WatchdogState.WARNING,
            "Warning message",
            {"elapsed": 10.5},
        )
        assert watchdog.events[0].context == {"elapsed": 10.5}

    def test_log_event_without_context(self) -> None:
        """_log_event uses empty context when not provided."""
        watchdog = AutoRecoveryWatchdog()
        watchdog._log_event(WatchdogState.IDLE, "No context")
        assert watchdog.events[0].context == {}

    def test_log_event_sets_timestamp(self) -> None:
        """_log_event sets timestamp."""
        watchdog = AutoRecoveryWatchdog()
        before = datetime.now()
        watchdog._log_event(WatchdogState.IDLE, "Test")
        after = datetime.now()
        assert before <= watchdog.events[0].timestamp <= after

    def test_log_event_sets_state(self) -> None:
        """_log_event sets state on event."""
        watchdog = AutoRecoveryWatchdog()
        watchdog._log_event(WatchdogState.ESCALATED, "Test")
        assert watchdog.events[0].state == WatchdogState.ESCALATED


# =============================================================================
# Test monitor context manager (quick tasks)
# =============================================================================


class TestMonitorContextManager:
    """Tests for monitor() context manager."""

    def test_monitor_sets_task_description(self) -> None:
        """monitor() sets task_description."""
        watchdog = AutoRecoveryWatchdog(timeout=10)
        with watchdog.monitor("My task"):
            assert watchdog.task_description == "My task"

    def test_monitor_sets_state_to_monitoring(self) -> None:
        """monitor() sets state to MONITORING."""
        watchdog = AutoRecoveryWatchdog(timeout=10)
        with watchdog.monitor("Test"):
            assert watchdog.state == WatchdogState.MONITORING

    def test_monitor_sets_start_time(self) -> None:
        """monitor() sets start_time."""
        watchdog = AutoRecoveryWatchdog(timeout=10)
        with watchdog.monitor("Test"):
            assert watchdog.start_time is not None
            assert watchdog.start_time > 0

    def test_monitor_returns_to_idle_after_completion(self) -> None:
        """monitor() returns state to IDLE after completion."""
        watchdog = AutoRecoveryWatchdog(timeout=10)
        with watchdog.monitor("Test"):
            pass
        assert watchdog.state == WatchdogState.IDLE

    def test_monitor_yields_watchdog(self) -> None:
        """monitor() yields the watchdog instance."""
        watchdog = AutoRecoveryWatchdog(timeout=10)
        with watchdog.monitor("Test") as w:
            assert w is watchdog

    def test_monitor_logs_start_event(self) -> None:
        """monitor() logs start monitoring event."""
        watchdog = AutoRecoveryWatchdog(timeout=10)
        with watchdog.monitor("Test task"):
            pass
        # Should have at least 2 events: started and completed
        assert len(watchdog.events) >= 2
        assert "Started monitoring" in watchdog.events[0].message

    def test_monitor_logs_completion_event(self) -> None:
        """monitor() logs completion event."""
        watchdog = AutoRecoveryWatchdog(timeout=10)
        with watchdog.monitor("Test task"):
            pass
        # Last event should be completion
        last_event = watchdog.events[-1]
        assert "Completed monitoring" in last_event.message

    def test_monitor_handles_exception(self) -> None:
        """monitor() re-raises exception and logs."""
        watchdog = AutoRecoveryWatchdog(timeout=10)
        with pytest.raises(ValueError):
            with watchdog.monitor("Failing task"):
                raise ValueError("Test error")
        # Should have warning event for exception
        warning_events = [e for e in watchdog.events if e.state == WatchdogState.WARNING]
        assert len(warning_events) > 0

    def test_monitor_tracks_elapsed_time(self) -> None:
        """monitor() tracks elapsed time in completion event."""
        watchdog = AutoRecoveryWatchdog(timeout=10)
        with watchdog.monitor("Timed task"):
            time.sleep(0.1)  # Brief sleep
        # Completion event should have elapsed time
        last_event = watchdog.events[-1]
        assert "elapsed" in last_event.context
        assert last_event.context["elapsed"] >= 0.1


# =============================================================================
# Test async_monitor context manager
# =============================================================================


class TestAsyncMonitorContextManager:
    """Tests for async_monitor() async context manager."""

    @pytest.mark.asyncio
    async def test_async_monitor_sets_task_description(self) -> None:
        """async_monitor() sets task_description."""
        watchdog = AutoRecoveryWatchdog(timeout=10)
        async with watchdog.async_monitor("My async task"):
            assert watchdog.task_description == "My async task"

    @pytest.mark.asyncio
    async def test_async_monitor_sets_state_to_monitoring(self) -> None:
        """async_monitor() sets state to MONITORING."""
        watchdog = AutoRecoveryWatchdog(timeout=10)
        async with watchdog.async_monitor("Test"):
            assert watchdog.state == WatchdogState.MONITORING

    @pytest.mark.asyncio
    async def test_async_monitor_returns_to_idle(self) -> None:
        """async_monitor() returns state to IDLE after completion."""
        watchdog = AutoRecoveryWatchdog(timeout=10)
        async with watchdog.async_monitor("Test"):
            pass
        assert watchdog.state == WatchdogState.IDLE

    @pytest.mark.asyncio
    async def test_async_monitor_yields_watchdog(self) -> None:
        """async_monitor() yields the watchdog instance."""
        watchdog = AutoRecoveryWatchdog(timeout=10)
        async with watchdog.async_monitor("Test") as w:
            assert w is watchdog

    @pytest.mark.asyncio
    async def test_async_monitor_handles_exception(self) -> None:
        """async_monitor() re-raises exception and logs."""
        watchdog = AutoRecoveryWatchdog(timeout=10)
        with pytest.raises(RuntimeError):
            async with watchdog.async_monitor("Failing async"):
                raise RuntimeError("Async error")
        # Should have warning event
        warning_events = [e for e in watchdog.events if e.state == WatchdogState.WARNING]
        assert len(warning_events) > 0


# =============================================================================
# Test get_event_log
# =============================================================================


class TestGetEventLog:
    """Tests for get_event_log method."""

    def test_empty_event_log(self) -> None:
        """Empty watchdog returns empty event log."""
        watchdog = AutoRecoveryWatchdog()
        assert watchdog.get_event_log() == []

    def test_event_log_format(self) -> None:
        """Event log returns dictionary format."""
        watchdog = AutoRecoveryWatchdog(timeout=10)
        with watchdog.monitor("Test"):
            pass
        log = watchdog.get_event_log()
        assert len(log) >= 2
        # Check first event structure
        event = log[0]
        assert "timestamp" in event
        assert "state" in event
        assert "message" in event
        assert "context" in event

    def test_event_log_timestamp_is_iso_format(self) -> None:
        """Event log timestamps are ISO format strings."""
        watchdog = AutoRecoveryWatchdog(timeout=10)
        with watchdog.monitor("Test"):
            pass
        log = watchdog.get_event_log()
        # Should be parseable as ISO format
        datetime.fromisoformat(log[0]["timestamp"])

    def test_event_log_state_is_string(self) -> None:
        """Event log states are string values."""
        watchdog = AutoRecoveryWatchdog(timeout=10)
        with watchdog.monitor("Test"):
            pass
        log = watchdog.get_event_log()
        # State should be string like "monitoring"
        assert isinstance(log[0]["state"], str)
        assert log[0]["state"] == "monitoring"


# =============================================================================
# Test _handle_timeout
# =============================================================================


class TestHandleTimeout:
    """Tests for _handle_timeout method."""

    def test_handle_timeout_with_auto_recover(self) -> None:
        """_handle_timeout triggers recovery when auto_recover=True."""
        watchdog = AutoRecoveryWatchdog(timeout=1, auto_recover=True)
        watchdog.start_time = time.time()
        watchdog.task_description = "Test task"

        with patch.object(watchdog, "_trigger_recovery") as mock_recover:
            watchdog._handle_timeout()
            mock_recover.assert_called_once()

    def test_handle_timeout_without_auto_recover(self) -> None:
        """_handle_timeout escalates when auto_recover=False."""
        watchdog = AutoRecoveryWatchdog(timeout=1, auto_recover=False)
        watchdog.start_time = time.time()
        watchdog.task_description = "Test task"

        with patch.object(watchdog, "_escalate_to_human") as mock_escalate:
            watchdog._handle_timeout()
            mock_escalate.assert_called_once()

    def test_handle_timeout_logs_event(self) -> None:
        """_handle_timeout logs an event."""
        watchdog = AutoRecoveryWatchdog(timeout=1, auto_recover=True)
        watchdog.start_time = time.time()
        watchdog.task_description = "Slow task"

        with patch.object(watchdog, "_trigger_recovery"):
            watchdog._handle_timeout()

        assert len(watchdog.events) > 0
        # Should have RECOVERING state when auto_recover=True
        assert any(e.state == WatchdogState.RECOVERING for e in watchdog.events)


# =============================================================================
# Test _trigger_recovery
# =============================================================================


class TestTriggerRecovery:
    """Tests for _trigger_recovery method."""

    def test_trigger_recovery_sets_state(self) -> None:
        """_trigger_recovery sets state to RECOVERING."""
        watchdog = AutoRecoveryWatchdog(timeout=1, checkpoint_on_recovery=False)
        watchdog.start_time = time.time()
        watchdog._trigger_recovery()
        assert watchdog.state == WatchdogState.RECOVERING

    def test_trigger_recovery_logs_completion_event(self) -> None:
        """_trigger_recovery logs recovery completion event."""
        watchdog = AutoRecoveryWatchdog(timeout=1, checkpoint_on_recovery=False)
        watchdog.start_time = time.time()
        watchdog._trigger_recovery()

        # Should have IDLE event for recovery completion
        idle_events = [e for e in watchdog.events if e.state == WatchdogState.IDLE]
        assert len(idle_events) > 0

    def test_trigger_recovery_with_checkpoint(self) -> None:
        """_trigger_recovery saves checkpoint when enabled."""
        # Mock SessionCheckpoint
        mock_checkpoint_class = MagicMock()
        mock_instance = MagicMock()
        mock_checkpoint_class.return_value = mock_instance

        with patch(
            "src.utils.auto_recovery_watchdog.SessionCheckpoint",
            mock_checkpoint_class,
        ):
            watchdog = AutoRecoveryWatchdog(timeout=1, checkpoint_on_recovery=True)
            watchdog.start_time = time.time()
            watchdog.task_description = "Test"
            watchdog._trigger_recovery()

            # SessionCheckpoint().save() should be called
            mock_instance.save.assert_called_once()

    def test_trigger_recovery_handles_missing_checkpoint_module(self) -> None:
        """_trigger_recovery handles missing checkpoint module."""
        with patch("src.utils.auto_recovery_watchdog.SessionCheckpoint", None):
            with patch("src.utils.auto_recovery_watchdog.restore_latest", None):
                watchdog = AutoRecoveryWatchdog(timeout=1, checkpoint_on_recovery=True)
                watchdog.start_time = time.time()
                # Should not raise
                watchdog._trigger_recovery()

    def test_trigger_recovery_escalates_on_error(self) -> None:
        """_trigger_recovery escalates to human on error."""
        mock_checkpoint_class = MagicMock()
        mock_checkpoint_class.return_value.save.side_effect = Exception("Checkpoint failed")

        with patch(
            "src.utils.auto_recovery_watchdog.SessionCheckpoint",
            mock_checkpoint_class,
        ):
            watchdog = AutoRecoveryWatchdog(timeout=1, checkpoint_on_recovery=True)
            watchdog.start_time = time.time()

            with patch.object(watchdog, "_escalate_to_human") as mock_escalate:
                watchdog._trigger_recovery()
                mock_escalate.assert_called_once()


# =============================================================================
# Test _escalate_to_human
# =============================================================================


class TestEscalateToHuman:
    """Tests for _escalate_to_human method."""

    def test_escalate_sets_state(self) -> None:
        """_escalate_to_human sets state to ESCALATED."""
        watchdog = AutoRecoveryWatchdog(timeout=1)
        watchdog._escalate_to_human()
        assert watchdog.state == WatchdogState.ESCALATED


# =============================================================================
# Test Timer Behavior (without actual timeouts)
# =============================================================================


class TestTimerBehavior:
    """Tests for timer-related behavior without real timeouts."""

    def test_watchdog_timer_thread_starts(self) -> None:
        """Watchdog timer thread starts when monitoring begins."""
        watchdog = AutoRecoveryWatchdog(timeout=60)
        with watchdog.monitor("Test"):
            assert watchdog._timer_thread is not None
            assert watchdog._timer_thread.is_alive()

    def test_watchdog_timer_thread_stops(self) -> None:
        """Watchdog timer thread stops when monitoring ends."""
        watchdog = AutoRecoveryWatchdog(timeout=60)
        with watchdog.monitor("Test"):
            pass
        # Give thread time to join
        time.sleep(0.1)
        # Thread should be stopped
        assert watchdog._stop_event.is_set()

    def test_stop_event_cleared_on_start(self) -> None:
        """Stop event is cleared when monitoring starts."""
        watchdog = AutoRecoveryWatchdog(timeout=60)
        watchdog._stop_event.set()  # Pre-set
        with watchdog.monitor("Test"):
            assert not watchdog._stop_event.is_set()


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_multiple_monitor_sessions(self) -> None:
        """Watchdog can be used for multiple sessions."""
        watchdog = AutoRecoveryWatchdog(timeout=10)

        with watchdog.monitor("Session 1"):
            pass

        with watchdog.monitor("Session 2"):
            pass

        # Should have events from both sessions
        assert len(watchdog.events) >= 4  # 2 per session

    def test_very_short_timeout(self) -> None:
        """Watchdog handles very short timeout values."""
        watchdog = AutoRecoveryWatchdog(timeout=0.1)
        assert watchdog.timeout == 0.1

    def test_very_long_timeout(self) -> None:
        """Watchdog handles very long timeout values."""
        watchdog = AutoRecoveryWatchdog(timeout=86400)  # 24 hours
        assert watchdog.timeout == 86400

    def test_zero_warning_threshold(self) -> None:
        """Watchdog handles zero warning threshold."""
        watchdog = AutoRecoveryWatchdog(warning_threshold=0)
        assert watchdog.warning_threshold == 0

    def test_full_warning_threshold(self) -> None:
        """Watchdog handles 1.0 (100%) warning threshold."""
        watchdog = AutoRecoveryWatchdog(warning_threshold=1.0)
        assert watchdog.warning_threshold == 1.0

    def test_default_task_description(self) -> None:
        """monitor() uses default task description."""
        watchdog = AutoRecoveryWatchdog(timeout=10)
        with watchdog.monitor():
            assert watchdog.task_description == "Task"

    def test_handle_timeout_with_no_start_time(self) -> None:
        """_handle_timeout handles missing start_time gracefully."""
        watchdog = AutoRecoveryWatchdog(timeout=1, auto_recover=True)
        watchdog.start_time = None
        watchdog.task_description = "Test"

        with patch.object(watchdog, "_trigger_recovery"):
            watchdog._handle_timeout()
        # Should complete without error

    def test_events_accumulate_across_sessions(self) -> None:
        """Events accumulate but don't reset between sessions."""
        watchdog = AutoRecoveryWatchdog(timeout=10)

        with watchdog.monitor("S1"):
            pass
        event_count_after_1 = len(watchdog.events)

        with watchdog.monitor("S2"):
            pass
        event_count_after_2 = len(watchdog.events)

        assert event_count_after_2 > event_count_after_1

    def test_all_configuration_options(self) -> None:
        """All configuration options can be set together."""
        watchdog = AutoRecoveryWatchdog(
            timeout=30.0,
            warning_threshold=0.6,
            auto_recover=False,
            checkpoint_on_recovery=False,
        )
        assert watchdog.timeout == 30.0
        assert watchdog.warning_threshold == 0.6
        assert watchdog.auto_recover is False
        assert watchdog.checkpoint_on_recovery is False
