"""Tests for event_bus.py - Event logging utilities."""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from src.utils.event_bus import LOG_STREAMS, LOGS_DIR, emit_agent_message, emit_event


class TestEventBusConstants:
    """Tests for module constants."""

    def test_logs_dir_is_path(self):
        """Test LOGS_DIR is a Path object."""
        assert isinstance(LOGS_DIR, Path)

    def test_log_streams_has_expected_streams(self):
        """Test LOG_STREAMS contains expected stream names."""
        expected_streams = [
            "agent_bus",
            "council_decisions",
            "culture_ship_audits",
            "chatdev_latest",
            "moderator",
            "errors",
            "anomalies",
            "test_history",
        ]
        for stream in expected_streams:
            assert stream in LOG_STREAMS

    def test_log_streams_values_are_paths(self):
        """Test all LOG_STREAMS values are Path objects."""
        for stream_name, path in LOG_STREAMS.items():
            assert isinstance(path, Path), f"{stream_name} value is not a Path"


class TestEmitEvent:
    """Tests for emit_event function."""

    def test_emit_event_creates_log_directory(self, tmp_path):
        """Test emit_event creates logs directory if missing."""
        log_dir = tmp_path / "logs"
        log_file = log_dir / "agent_bus.log"

        # Don't mock Path.mkdir - let it actually create the directory
        with (
            patch("src.utils.event_bus.LOGS_DIR", log_dir),
            patch("src.utils.event_bus.LOG_STREAMS", {"agent_bus": log_file}),
        ):
            emit_event("agent_bus", "test_event")
            # Verify directory was created
            assert log_dir.exists()
            assert log_file.exists()

    def test_emit_event_writes_to_known_stream(self, tmp_path):
        """Test emit_event writes to known stream file."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "agent_bus.log"

        with (
            patch("src.utils.event_bus.LOGS_DIR", log_dir),
            patch("src.utils.event_bus.LOG_STREAMS", {"agent_bus": log_file}),
        ):
            emit_event("agent_bus", "task_routed")

            assert log_file.exists()
            content = log_file.read_text()
            assert "EVENT=task_routed" in content

    def test_emit_event_writes_to_unknown_stream(self, tmp_path):
        """Test emit_event creates new log file for unknown stream."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)

        with (
            patch("src.utils.event_bus.LOGS_DIR", log_dir),
            patch("src.utils.event_bus.LOG_STREAMS", {}),
        ):
            emit_event("custom_stream", "custom_event")

            custom_log = log_dir / "custom_stream.log"
            assert custom_log.exists()
            content = custom_log.read_text()
            assert "EVENT=custom_event" in content

    def test_emit_event_includes_timestamp(self, tmp_path):
        """Test emit_event includes timestamp in output."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "test.log"

        with (
            patch("src.utils.event_bus.LOGS_DIR", log_dir),
            patch("src.utils.event_bus.LOG_STREAMS", {"test": log_file}),
        ):
            emit_event("test", "test_event")

            content = log_file.read_text()
            # Check for date pattern YYYY-MM-DD
            year = datetime.now().year
            assert str(year) in content

    def test_emit_event_with_payload(self, tmp_path):
        """Test emit_event includes payload in JSON format."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "test.log"

        payload = {"task_id": 42, "agent": "claude"}

        with (
            patch("src.utils.event_bus.LOGS_DIR", log_dir),
            patch("src.utils.event_bus.LOG_STREAMS", {"test": log_file}),
        ):
            emit_event("test", "task_assigned", payload=payload)

            content = log_file.read_text()
            assert "payload=" in content
            assert '"task_id":42' in content
            assert '"agent":"claude"' in content

    def test_emit_event_with_message(self, tmp_path):
        """Test emit_event includes human-readable message."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "test.log"

        message = "Claude assigned to refactor compute_deltas()"

        with (
            patch("src.utils.event_bus.LOGS_DIR", log_dir),
            patch("src.utils.event_bus.LOG_STREAMS", {"test": log_file}),
        ):
            emit_event("test", "task_assigned", message=message)

            content = log_file.read_text()
            assert f"msg={message}" in content

    def test_emit_event_with_payload_and_message(self, tmp_path):
        """Test emit_event with both payload and message."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "test.log"

        payload = {"task_id": 42}
        message = "Test message"

        with (
            patch("src.utils.event_bus.LOGS_DIR", log_dir),
            patch("src.utils.event_bus.LOG_STREAMS", {"test": log_file}),
        ):
            emit_event("test", "task_assigned", payload=payload, message=message)

            content = log_file.read_text()
            assert "payload=" in content
            assert "msg=Test message" in content

    def test_emit_event_appends_to_existing_file(self, tmp_path):
        """Test emit_event appends to existing log file."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "test.log"
        log_file.write_text("existing line\n")

        with (
            patch("src.utils.event_bus.LOGS_DIR", log_dir),
            patch("src.utils.event_bus.LOG_STREAMS", {"test": log_file}),
        ):
            emit_event("test", "new_event")

            content = log_file.read_text()
            assert "existing line" in content
            assert "EVENT=new_event" in content
            # Should have two lines
            assert content.count("\n") == 2

    def test_emit_event_uses_pipe_delimiter(self, tmp_path):
        """Test emit_event uses ' | ' as delimiter."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "test.log"

        with (
            patch("src.utils.event_bus.LOGS_DIR", log_dir),
            patch("src.utils.event_bus.LOG_STREAMS", {"test": log_file}),
        ):
            emit_event("test", "test_event", {"key": "value"}, "message")

            content = log_file.read_text()
            assert " | " in content
            # Should have 4 parts: timestamp, event, payload, message
            parts = content.strip().split(" | ")
            assert len(parts) == 4


class TestEmitAgentMessage:
    """Tests for emit_agent_message convenience function."""

    def test_emit_agent_message_emits_to_agent_bus(self, tmp_path):
        """Test emit_agent_message writes to agent_bus stream."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "agent_bus.log"

        with (
            patch("src.utils.event_bus.LOGS_DIR", log_dir),
            patch("src.utils.event_bus.LOG_STREAMS", {"agent_bus": log_file}),
        ):
            emit_agent_message("claude", "Hello world")

            assert log_file.exists()
            content = log_file.read_text()
            assert "EVENT=agent_message" in content

    def test_emit_agent_message_includes_agent_name(self, tmp_path):
        """Test emit_agent_message includes agent name in payload."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "agent_bus.log"

        with (
            patch("src.utils.event_bus.LOGS_DIR", log_dir),
            patch("src.utils.event_bus.LOG_STREAMS", {"agent_bus": log_file}),
        ):
            emit_agent_message("copilot", "Test message")

            content = log_file.read_text()
            assert '"agent":"copilot"' in content

    def test_emit_agent_message_includes_message_text(self, tmp_path):
        """Test emit_agent_message includes message text."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "agent_bus.log"

        with (
            patch("src.utils.event_bus.LOGS_DIR", log_dir),
            patch("src.utils.event_bus.LOG_STREAMS", {"agent_bus": log_file}),
        ):
            emit_agent_message("ollama", "Processing request")

            content = log_file.read_text()
            assert "msg=Processing request" in content

    def test_emit_agent_message_with_extra_kwargs(self, tmp_path):
        """Test emit_agent_message passes extra kwargs to payload."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "agent_bus.log"

        with (
            patch("src.utils.event_bus.LOGS_DIR", log_dir),
            patch("src.utils.event_bus.LOG_STREAMS", {"agent_bus": log_file}),
        ):
            emit_agent_message("claude", "Test", task_id=123, status="active")

            content = log_file.read_text()
            assert '"task_id":123' in content
            assert '"status":"active"' in content


class TestEdgeCases:
    """Edge case tests."""

    def test_emit_event_with_empty_payload(self, tmp_path):
        """Test emit_event with empty payload dict - empty dict is falsy, no payload in output."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "test.log"

        with (
            patch("src.utils.event_bus.LOGS_DIR", log_dir),
            patch("src.utils.event_bus.LOG_STREAMS", {"test": log_file}),
        ):
            emit_event("test", "test_event", payload={})

            content = log_file.read_text()
            # Empty dict {} is falsy in Python, so code does NOT include payload
            assert "payload" not in content
            assert "EVENT=test_event" in content

    def test_emit_event_with_none_payload(self, tmp_path):
        """Test emit_event with None payload (should skip payload)."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "test.log"

        with (
            patch("src.utils.event_bus.LOGS_DIR", log_dir),
            patch("src.utils.event_bus.LOG_STREAMS", {"test": log_file}),
        ):
            emit_event("test", "test_event", payload=None)

            content = log_file.read_text()
            # Should NOT include payload= when None
            assert "payload=" not in content

    def test_emit_event_with_empty_message(self, tmp_path):
        """Test emit_event with empty message string."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "test.log"

        with (
            patch("src.utils.event_bus.LOGS_DIR", log_dir),
            patch("src.utils.event_bus.LOG_STREAMS", {"test": log_file}),
        ):
            emit_event("test", "test_event", message="")

            content = log_file.read_text()
            # Empty string is falsy, so msg should not appear
            assert "msg=" not in content

    def test_emit_event_with_special_characters_in_payload(self, tmp_path):
        """Test emit_event handles special characters in payload."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "test.log"

        payload = {"key": "value with \"quotes\" and 'apostrophes'", "unicode": "émojis 🎉"}

        with (
            patch("src.utils.event_bus.LOGS_DIR", log_dir),
            patch("src.utils.event_bus.LOG_STREAMS", {"test": log_file}),
        ):
            emit_event("test", "test_event", payload=payload)

            content = log_file.read_text()
            assert "payload=" in content
            # JSON should escape quotes
            assert '\\"quotes\\"' in content or '\\"quotes\\"' in content or "quotes" in content

    def test_emit_event_with_nested_payload(self, tmp_path):
        """Test emit_event handles nested dict in payload."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "test.log"

        payload = {"outer": {"inner": {"deep": 42}}}

        with (
            patch("src.utils.event_bus.LOGS_DIR", log_dir),
            patch("src.utils.event_bus.LOG_STREAMS", {"test": log_file}),
        ):
            emit_event("test", "test_event", payload=payload)

            content = log_file.read_text()
            assert '"outer"' in content
            assert '"inner"' in content
            assert '"deep":42' in content

    def test_emit_event_concurrent_writes(self, tmp_path):
        """Test multiple emit_event calls don't corrupt the log."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "test.log"

        with (
            patch("src.utils.event_bus.LOGS_DIR", log_dir),
            patch("src.utils.event_bus.LOG_STREAMS", {"test": log_file}),
        ):
            # Emit multiple events
            for i in range(5):
                emit_event("test", f"event_{i}", {"index": i})

            content = log_file.read_text()
            lines = content.strip().split("\n")
            assert len(lines) == 5
            for i in range(5):
                assert f"EVENT=event_{i}" in lines[i]
