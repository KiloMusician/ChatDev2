"""Tests for src/orchestration/emergence_protocol.py — enums, dataclass, protocol."""

import json

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_protocol(tmp_path):
    from src.orchestration.emergence_protocol import EmergenceProtocol

    ledger = tmp_path / "emergence" / "ledger.jsonl"
    return EmergenceProtocol(ledger_path=str(ledger))


def _make_event(protocol, **kwargs):
    from src.orchestration.emergence_protocol import EmergenceType

    defaults = {
        "emergence_type": EmergenceType.PHASE_JUMP,
        "title": "Test Event",
        "description": "Something happened",
        "what_was_done": ["action one", "action two"],
        "why_it_matters": "Important reason",
        "files_changed": ["src/foo.py"],
    }
    defaults.update(kwargs)
    return protocol.acknowledge(**defaults)


# ---------------------------------------------------------------------------
# EmergenceType enum
# ---------------------------------------------------------------------------


class TestEmergenceTypeEnum:
    """Tests for EmergenceType enum."""

    def test_has_five_values(self):
        from src.orchestration.emergence_protocol import EmergenceType

        assert len(list(EmergenceType)) == 5

    def test_phase_jump_value(self):
        from src.orchestration.emergence_protocol import EmergenceType

        assert EmergenceType.PHASE_JUMP.value == "phase_jump"

    def test_capability_synthesis_value(self):
        from src.orchestration.emergence_protocol import EmergenceType

        assert EmergenceType.CAPABILITY_SYNTHESIS.value == "capability_synthesis"

    def test_architectural_leap_value(self):
        from src.orchestration.emergence_protocol import EmergenceType

        assert EmergenceType.ARCHITECTURAL_LEAP.value == "architectural_leap"

    def test_insight_discovery_value(self):
        from src.orchestration.emergence_protocol import EmergenceType

        assert EmergenceType.INSIGHT_DISCOVERY.value == "insight_discovery"

    def test_self_optimization_value(self):
        from src.orchestration.emergence_protocol import EmergenceType

        assert EmergenceType.SELF_OPTIMIZATION.value == "self_optimization"


# ---------------------------------------------------------------------------
# IntegrationStatus enum
# ---------------------------------------------------------------------------


class TestIntegrationStatusEnum:
    """Tests for IntegrationStatus enum."""

    def test_has_five_values(self):
        from src.orchestration.emergence_protocol import IntegrationStatus

        assert len(list(IntegrationStatus)) == 5

    def test_quarantined_value(self):
        from src.orchestration.emergence_protocol import IntegrationStatus

        assert IntegrationStatus.QUARANTINED.value == "quarantined"

    def test_experimental_value(self):
        from src.orchestration.emergence_protocol import IntegrationStatus

        assert IntegrationStatus.EXPERIMENTAL.value == "experimental"

    def test_validated_value(self):
        from src.orchestration.emergence_protocol import IntegrationStatus

        assert IntegrationStatus.VALIDATED.value == "validated"

    def test_canonical_value(self):
        from src.orchestration.emergence_protocol import IntegrationStatus

        assert IntegrationStatus.CANONICAL.value == "canonical"

    def test_archived_value(self):
        from src.orchestration.emergence_protocol import IntegrationStatus

        assert IntegrationStatus.ARCHIVED.value == "archived"


# ---------------------------------------------------------------------------
# EmergenceEvent dataclass
# ---------------------------------------------------------------------------


class TestEmergenceEventDataclass:
    """Tests for EmergenceEvent dataclass."""

    def _make_event_direct(self):
        from src.orchestration.emergence_protocol import (
            EmergenceEvent,
            EmergenceType,
            IntegrationStatus,
        )

        return EmergenceEvent(
            timestamp="2026-01-01T00:00:00",
            emergence_type=EmergenceType.PHASE_JUMP,
            title="Direct Test",
            description="desc",
            what_was_done=["step 1"],
            why_it_matters="reason",
            files_changed=["file.py"],
            dependencies_added=["dep"],
            rollback_instructions="revert",
            integration_status=IntegrationStatus.QUARANTINED,
            phase_intended="phase2",
            phase_executed="phase1",
        )

    def test_instantiation(self):
        assert self._make_event_direct() is not None

    def test_title_stored(self):
        assert self._make_event_direct().title == "Direct Test"

    def test_to_dict_returns_dict(self):
        assert isinstance(self._make_event_direct().to_dict(), dict)

    def test_to_dict_type_is_enum_value(self):
        d = self._make_event_direct().to_dict()
        assert d["type"] == "phase_jump"

    def test_to_dict_integration_status_is_string(self):
        d = self._make_event_direct().to_dict()
        assert d["integration_status"] == "quarantined"

    def test_to_dict_has_all_required_keys(self):
        required = {
            "timestamp", "type", "title", "description",
            "what_was_done", "why_it_matters", "files_changed",
            "dependencies_added", "rollback_instructions",
            "integration_status", "phase_intended", "phase_executed",
        }
        d = self._make_event_direct().to_dict()
        assert required.issubset(d.keys())

    def test_to_dict_phase_fields(self):
        d = self._make_event_direct().to_dict()
        assert d["phase_intended"] == "phase2"
        assert d["phase_executed"] == "phase1"


# ---------------------------------------------------------------------------
# EmergenceProtocol — initialization
# ---------------------------------------------------------------------------


class TestEmergenceProtocolInit:
    """Tests for EmergenceProtocol.__init__."""

    def test_ledger_dir_created(self, tmp_path):
        _proto = _make_protocol(tmp_path)
        assert (tmp_path / "emergence").is_dir()

    def test_custom_ledger_path_stored(self, tmp_path):
        from src.orchestration.emergence_protocol import EmergenceProtocol
        from pathlib import Path

        custom = tmp_path / "custom" / "ledger.jsonl"
        p = EmergenceProtocol(ledger_path=str(custom))
        assert p.ledger_path == custom


# ---------------------------------------------------------------------------
# EmergenceProtocol — acknowledge
# ---------------------------------------------------------------------------


class TestEmergenceProtocolAcknowledge:
    """Tests for EmergenceProtocol.acknowledge."""

    def test_returns_emergence_event(self, tmp_path):
        from src.orchestration.emergence_protocol import EmergenceEvent

        proto = _make_protocol(tmp_path)
        event = _make_event(proto)
        assert isinstance(event, EmergenceEvent)

    def test_title_preserved(self, tmp_path):
        proto = _make_protocol(tmp_path)
        event = _make_event(proto, title="My Title")
        assert event.title == "My Title"

    def test_initial_status_is_quarantined(self, tmp_path):
        from src.orchestration.emergence_protocol import IntegrationStatus

        proto = _make_protocol(tmp_path)
        event = _make_event(proto)
        assert event.integration_status == IntegrationStatus.QUARANTINED

    def test_empty_dependencies_defaults_to_list(self, tmp_path):
        proto = _make_protocol(tmp_path)
        event = _make_event(proto, dependencies_added=None)
        assert event.dependencies_added == []

    def test_dependencies_stored(self, tmp_path):
        proto = _make_protocol(tmp_path)
        event = _make_event(proto, dependencies_added=["requests", "pydantic"])
        assert "requests" in event.dependencies_added

    def test_ledger_file_written(self, tmp_path):
        proto = _make_protocol(tmp_path)
        _make_event(proto)
        assert proto.ledger_path.exists()

    def test_ledger_line_is_valid_json(self, tmp_path):
        proto = _make_protocol(tmp_path)
        _make_event(proto)
        lines = proto.ledger_path.read_text().strip().splitlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["title"] == "Test Event"

    def test_multiple_events_append_to_ledger(self, tmp_path):
        proto = _make_protocol(tmp_path)
        _make_event(proto, title="First")
        _make_event(proto, title="Second")
        lines = proto.ledger_path.read_text().strip().splitlines()
        assert len(lines) == 2

    def test_phase_defaults_apply(self, tmp_path):
        proto = _make_protocol(tmp_path)
        event = _make_event(proto)
        assert event.phase_intended == "future"
        assert event.phase_executed == "current"

    def test_phase_custom_values(self, tmp_path):
        proto = _make_protocol(tmp_path)
        event = _make_event(proto, phase_intended="phase3", phase_executed="phase2")
        assert event.phase_intended == "phase3"
        assert event.phase_executed == "phase2"


# ---------------------------------------------------------------------------
# EmergenceProtocol — promote
# ---------------------------------------------------------------------------


class TestEmergenceProtocolPromote:
    """Tests for EmergenceProtocol.promote."""

    def test_promote_changes_status(self, tmp_path):
        from src.orchestration.emergence_protocol import IntegrationStatus

        proto = _make_protocol(tmp_path)
        _make_event(proto, title="Promote Me")
        proto.promote("Promote Me", IntegrationStatus.VALIDATED)
        events = proto.get_recent_emergences()
        matching = [e for e in events if e["title"] == "Promote Me"]
        assert matching[0]["integration_status"] == "validated"

    def test_promote_only_changes_matching_title(self, tmp_path):
        from src.orchestration.emergence_protocol import IntegrationStatus

        proto = _make_protocol(tmp_path)
        _make_event(proto, title="Target")
        _make_event(proto, title="Other")
        proto.promote("Target", IntegrationStatus.CANONICAL)
        events = proto.get_recent_emergences()
        other = next(e for e in events if e["title"] == "Other")
        assert other["integration_status"] == "quarantined"

    def test_promote_nonexistent_title_no_error(self, tmp_path):
        from src.orchestration.emergence_protocol import IntegrationStatus

        proto = _make_protocol(tmp_path)
        _make_event(proto, title="Real Event")
        # Should not raise
        proto.promote("Ghost Event", IntegrationStatus.ARCHIVED)

    def test_promote_to_experimental(self, tmp_path):
        from src.orchestration.emergence_protocol import IntegrationStatus

        proto = _make_protocol(tmp_path)
        _make_event(proto, title="Exp")
        proto.promote("Exp", IntegrationStatus.EXPERIMENTAL)
        events = proto.get_recent_emergences()
        assert events[0]["integration_status"] == "experimental"


# ---------------------------------------------------------------------------
# EmergenceProtocol — get_recent_emergences
# ---------------------------------------------------------------------------


class TestEmergenceProtocolGetRecent:
    """Tests for EmergenceProtocol.get_recent_emergences."""

    def test_empty_ledger_returns_empty_list(self, tmp_path):
        proto = _make_protocol(tmp_path)
        assert proto.get_recent_emergences() == []

    def test_returns_list(self, tmp_path):
        proto = _make_protocol(tmp_path)
        _make_event(proto)
        assert isinstance(proto.get_recent_emergences(), list)

    def test_limit_respected(self, tmp_path):
        proto = _make_protocol(tmp_path)
        for i in range(15):
            _make_event(proto, title=f"Event {i}")
        result = proto.get_recent_emergences(limit=5)
        assert len(result) == 5

    def test_returns_most_recent_last(self, tmp_path):
        proto = _make_protocol(tmp_path)
        for i in range(12):
            _make_event(proto, title=f"Event {i}")
        result = proto.get_recent_emergences(limit=3)
        assert result[-1]["title"] == "Event 11"

    def test_default_limit_is_ten(self, tmp_path):
        proto = _make_protocol(tmp_path)
        for i in range(15):
            _make_event(proto, title=f"E{i}")
        result = proto.get_recent_emergences()
        assert len(result) == 10


# ---------------------------------------------------------------------------
# EmergenceProtocol — format_emergence
# ---------------------------------------------------------------------------


class TestEmergenceProtocolFormatEmergence:
    """Tests for EmergenceProtocol.format_emergence."""

    def test_format_returns_string(self, tmp_path):
        proto = _make_protocol(tmp_path)
        event = _make_event(proto)
        result = proto.format_emergence(event)
        assert isinstance(result, str)

    def test_format_contains_title(self, tmp_path):
        proto = _make_protocol(tmp_path)
        event = _make_event(proto, title="My Unique Title")
        result = proto.format_emergence(event)
        assert "My Unique Title" in result

    def test_format_contains_type_value(self, tmp_path):
        proto = _make_protocol(tmp_path)
        event = _make_event(proto)
        result = proto.format_emergence(event)
        assert "phase_jump" in result

    def test_format_contains_phase_info(self, tmp_path):
        proto = _make_protocol(tmp_path)
        event = _make_event(proto, phase_intended="phase3", phase_executed="phase2")
        result = proto.format_emergence(event)
        assert "phase3" in result
        assert "phase2" in result

    def test_format_no_deps_section_empty_list(self, tmp_path):
        proto = _make_protocol(tmp_path)
        event = _make_event(proto, dependencies_added=[])
        result = proto.format_emergence(event)
        # Section should be empty/not shown when no deps
        assert "Dependencies Added:" not in result

    def test_format_deps_shown_when_present(self, tmp_path):
        proto = _make_protocol(tmp_path)
        event = _make_event(proto, dependencies_added=["my-dep"])
        result = proto.format_emergence(event)
        assert "my-dep" in result


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


class TestModuleLevelHelpers:
    """Tests for get_protocol and acknowledge_emergence helpers."""

    def test_get_protocol_returns_instance(self):
        from src.orchestration.emergence_protocol import EmergenceProtocol, get_protocol

        import src.orchestration.emergence_protocol as _mod

        _mod._global_protocol = None
        p = get_protocol()
        assert isinstance(p, EmergenceProtocol)
        _mod._global_protocol = None  # clean up

    def test_get_protocol_singleton(self):
        from src.orchestration.emergence_protocol import get_protocol

        import src.orchestration.emergence_protocol as _mod

        _mod._global_protocol = None
        p1 = get_protocol()
        p2 = get_protocol()
        assert p1 is p2
        _mod._global_protocol = None

    def test_acknowledge_emergence_convenience(self, tmp_path):
        from src.orchestration.emergence_protocol import (
            EmergenceEvent,
            EmergenceProtocol,
            acknowledge_emergence,
        )
        import src.orchestration.emergence_protocol as _mod

        # Redirect global protocol to tmp_path
        proto = EmergenceProtocol(ledger_path=str(tmp_path / "e" / "led.jsonl"))
        _mod._global_protocol = proto

        event = acknowledge_emergence(
            title="Convenience Test",
            description="via helper",
            what_was_done=["did stuff"],
            why_it_matters="matters",
            files_changed=["x.py"],
        )
        assert isinstance(event, EmergenceEvent)
        assert event.title == "Convenience Test"
        _mod._global_protocol = None
