"""Tests for infrastructure batch 12: agent_orchestration_types, system.status, consciousness_bridge."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# =============================================================================
# Agent Orchestration Types Tests
# =============================================================================
class TestTaskPriority:
    """Tests for TaskPriority enum."""

    def test_all_priorities_exist(self) -> None:
        from src.agents.agent_orchestration_types import TaskPriority

        assert TaskPriority.CRITICAL.value == 1
        assert TaskPriority.HIGH.value == 2
        assert TaskPriority.NORMAL.value == 3
        assert TaskPriority.LOW.value == 4
        assert TaskPriority.BACKGROUND.value == 5

    def test_priority_ordering(self) -> None:
        from src.agents.agent_orchestration_types import TaskPriority

        # Lower value = higher priority
        assert TaskPriority.CRITICAL.value < TaskPriority.HIGH.value
        assert TaskPriority.HIGH.value < TaskPriority.NORMAL.value
        assert TaskPriority.NORMAL.value < TaskPriority.LOW.value
        assert TaskPriority.LOW.value < TaskPriority.BACKGROUND.value


class TestExecutionMode:
    """Tests for ExecutionMode enum."""

    def test_all_modes_exist(self) -> None:
        from src.agents.agent_orchestration_types import ExecutionMode

        assert ExecutionMode.CONSENSUS.value == "consensus"
        assert ExecutionMode.VOTING.value == "voting"
        assert ExecutionMode.SEQUENTIAL.value == "sequential"
        assert ExecutionMode.PARALLEL.value == "parallel"
        assert ExecutionMode.FIRST_SUCCESS.value == "first_success"


class TestTaskLock:
    """Tests for TaskLock dataclass."""

    def test_creation(self) -> None:
        from src.agents.agent_orchestration_types import TaskLock

        now = time.time()
        lock = TaskLock(
            task_id="task-001",
            agent_id="agent-001",
            acquired_at=now,
            expires_at=now + 300,
        )
        assert lock.task_id == "task-001"
        assert lock.agent_id == "agent-001"
        assert lock.acquired_at == now
        assert lock.expires_at == now + 300
        assert lock.metadata == {}

    def test_with_metadata(self) -> None:
        from src.agents.agent_orchestration_types import TaskLock

        lock = TaskLock(
            task_id="t1",
            agent_id="a1",
            acquired_at=0.0,
            expires_at=100.0,
            metadata={"reason": "testing"},
        )
        assert lock.metadata == {"reason": "testing"}


class TestServiceCapability:
    """Tests for ServiceCapability dataclass."""

    def test_required_fields(self) -> None:
        from src.agents.agent_orchestration_types import ServiceCapability

        cap = ServiceCapability(name="code_review", description="Review code")
        assert cap.name == "code_review"
        assert cap.description == "Review code"
        assert cap.priority == 5
        assert cap.requires_consciousness is False
        assert cap.metadata == {}

    def test_custom_fields(self) -> None:
        from src.agents.agent_orchestration_types import ServiceCapability

        cap = ServiceCapability(
            name="analysis",
            description="Deep analysis",
            priority=2,
            requires_consciousness=True,
            metadata={"model": "gpt-4"},
        )
        assert cap.priority == 2
        assert cap.requires_consciousness is True
        assert cap.metadata == {"model": "gpt-4"}


class TestRegisteredService:
    """Tests for RegisteredService dataclass."""

    def test_required_fields(self) -> None:
        from src.agents.agent_orchestration_types import RegisteredService, ServiceCapability

        cap = ServiceCapability(name="test", description="Test cap")
        svc = RegisteredService(
            service_id="svc-001",
            name="Test Service",
            capabilities=[cap],
        )
        assert svc.service_id == "svc-001"
        assert svc.name == "Test Service"
        assert len(svc.capabilities) == 1
        assert svc.endpoint is None
        assert svc.active is True
        assert svc.registered_at > 0
        assert svc.metadata == {}

    def test_custom_fields(self) -> None:
        from src.agents.agent_orchestration_types import RegisteredService

        svc = RegisteredService(
            service_id="svc-002",
            name="Custom Service",
            capabilities=[],
            endpoint="http://localhost:8080",
            active=False,
            registered_at=1234567890.0,
            metadata={"version": "2.0"},
        )
        assert svc.endpoint == "http://localhost:8080"
        assert svc.active is False
        assert svc.registered_at == 1234567890.0
        assert svc.metadata == {"version": "2.0"}


# =============================================================================
# System Status Tests
# =============================================================================
class TestSetSystemStatus:
    """Tests for set_system_status function."""

    def test_creates_status_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.system.status as status_module

        status_file = tmp_path / "state" / "system_status.json"
        monkeypatch.setattr(status_module, "STATUS_FILE", status_file)

        status_module.set_system_status("on", run_id="test-123")

        assert status_file.exists()
        data = json.loads(status_file.read_text())
        assert data["status"] == "on"
        assert data["run_id"] == "test-123"
        assert "timestamp" in data

    def test_with_details(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.system.status as status_module

        status_file = tmp_path / "state" / "system_status.json"
        monkeypatch.setattr(status_module, "STATUS_FILE", status_file)

        status_module.set_system_status("on", details={"mode": "test"})

        data = json.loads(status_file.read_text())
        assert data["details"] == {"mode": "test"}


class TestGetSystemStatus:
    """Tests for get_system_status function."""

    def test_returns_default_when_no_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import src.system.status as status_module

        status_file = tmp_path / "state" / "system_status.json"
        monkeypatch.setattr(status_module, "STATUS_FILE", status_file)

        result = status_module.get_system_status()
        assert result["status"] == "off"
        assert result["timestamp"] is None

    def test_returns_current_status(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.system.status as status_module

        status_file = tmp_path / "state" / "system_status.json"
        status_file.parent.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(status_module, "STATUS_FILE", status_file)

        status_module.set_system_status("on", run_id="run-456")
        result = status_module.get_system_status()

        assert result["status"] == "on"
        assert result["run_id"] == "run-456"


class TestIsSystemOn:
    """Tests for is_system_on function."""

    def test_off_when_no_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.system.status as status_module

        status_file = tmp_path / "state" / "system_status.json"
        monkeypatch.setattr(status_module, "STATUS_FILE", status_file)

        assert status_module.is_system_on() is False

    def test_on_when_status_on(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.system.status as status_module

        status_file = tmp_path / "state" / "system_status.json"
        monkeypatch.setattr(status_module, "STATUS_FILE", status_file)

        status_module.set_system_status("on")
        assert status_module.is_system_on() is True

    def test_off_when_status_off(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.system.status as status_module

        status_file = tmp_path / "state" / "system_status.json"
        monkeypatch.setattr(status_module, "STATUS_FILE", status_file)

        status_module.set_system_status("off")
        assert status_module.is_system_on() is False


class TestHeartbeat:
    """Tests for heartbeat function."""

    def test_keeps_system_on(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.system.status as status_module

        status_file = tmp_path / "state" / "system_status.json"
        monkeypatch.setattr(status_module, "STATUS_FILE", status_file)

        status_module.heartbeat(run_id="hb-001")
        result = status_module.get_system_status()

        assert result["status"] == "on"
        assert result["run_id"] == "hb-001"

    def test_preserves_run_id(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.system.status as status_module

        status_file = tmp_path / "state" / "system_status.json"
        monkeypatch.setattr(status_module, "STATUS_FILE", status_file)

        status_module.set_system_status("on", run_id="original")
        status_module.heartbeat()  # No run_id passed

        result = status_module.get_system_status()
        assert result["run_id"] == "original"

    def test_round_trip_updates_status_file_coherently(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import src.system.status as status_module

        status_file = tmp_path / "state" / "system_status.json"
        monkeypatch.setattr(status_module, "STATUS_FILE", status_file)

        status_module.set_system_status(
            "off",
            run_id="before-heartbeat",
            details={"health": "critical", "note": "pre-heartbeat"},
        )
        status_module.heartbeat(
            run_id="hb-002",
            details={
                "health": "healthy",
                "last_heartbeat": "2026-03-21T12:00:00Z",
                "service": "reactive-api",
            },
        )

        file_payload = json.loads(status_file.read_text())
        round_trip_payload = status_module.get_system_status()

        assert file_payload == round_trip_payload
        assert file_payload["status"] == "on"
        assert file_payload["run_id"] == "hb-002"
        assert file_payload["details"]["health"] == "healthy"
        assert file_payload["details"]["last_heartbeat"] == "2026-03-21T12:00:00Z"


# =============================================================================
# Consciousness Bridge Tests
# =============================================================================
class TestConsciousnessBridgeInit:
    """Tests for ConsciousnessBridge initialization."""

    def test_init_creates_components(self) -> None:
        with (
            patch("src.integration.consciousness_bridge.OmniTagSystem"),
            patch("src.integration.consciousness_bridge.MegaTagProcessor"),
            patch("src.integration.consciousness_bridge.SymbolicCognition"),
        ):
            from src.integration.consciousness_bridge import ConsciousnessBridge

            bridge = ConsciousnessBridge()
            assert bridge.contextual_memory == {}
            assert bridge.initialized_at is not None


class TestConsciousnessBridgeInitialize:
    """Tests for ConsciousnessBridge.initialize method."""

    def test_initialize_calls_subsystems(self) -> None:
        with (
            patch("src.integration.consciousness_bridge.OmniTagSystem"),
            patch("src.integration.consciousness_bridge.MegaTagProcessor"),
            patch("src.integration.consciousness_bridge.SymbolicCognition"),
        ):
            from src.integration.consciousness_bridge import ConsciousnessBridge

            bridge = ConsciousnessBridge()
            bridge.initialize()

            bridge.omni_tag_system.initialize.assert_called_once()
            bridge.mega_tag_processor.initialize.assert_called_once()
            bridge.symbolic_cognition.initialize.assert_called_once()


class TestConsciousnessBridgeEnhance:
    """Tests for ConsciousnessBridge.enhance_contextual_memory method."""

    def test_enhance_updates_memory(self) -> None:
        with (
            patch("src.integration.consciousness_bridge.OmniTagSystem") as mock_omni_cls,
            patch("src.integration.consciousness_bridge.MegaTagProcessor") as mock_mega_cls,
            patch("src.integration.consciousness_bridge.SymbolicCognition"),
        ):
            mock_omni = MagicMock()
            mock_mega = MagicMock()
            mock_omni_cls.return_value = mock_omni
            mock_mega_cls.return_value = mock_mega

            mock_omni.create_tags.return_value = {"tag": "value"}
            mock_mega.process_tags.return_value = {"processed": "data"}

            from src.integration.consciousness_bridge import ConsciousnessBridge

            bridge = ConsciousnessBridge()
            bridge.enhance_contextual_memory({"input": "test"})

            assert "processed" in bridge.contextual_memory


class TestConsciousnessBridgeRetrieve:
    """Tests for ConsciousnessBridge.retrieve_contextual_memory method."""

    def test_retrieve_calls_cognition(self) -> None:
        with (
            patch("src.integration.consciousness_bridge.OmniTagSystem"),
            patch("src.integration.consciousness_bridge.MegaTagProcessor"),
            patch("src.integration.consciousness_bridge.SymbolicCognition") as mock_cog_cls,
        ):
            mock_cog = MagicMock()
            mock_cog_cls.return_value = mock_cog
            mock_cog.query_memory.return_value = "found"

            from src.integration.consciousness_bridge import ConsciousnessBridge

            bridge = ConsciousnessBridge()
            result = bridge.retrieve_contextual_memory("test query")

            mock_cog.query_memory.assert_called_once()
            assert result == "found"


class TestConsciousnessBridgeGetTime:
    """Tests for ConsciousnessBridge.get_initialization_time method."""

    def test_returns_formatted_time(self) -> None:
        with (
            patch("src.integration.consciousness_bridge.OmniTagSystem"),
            patch("src.integration.consciousness_bridge.MegaTagProcessor"),
            patch("src.integration.consciousness_bridge.SymbolicCognition"),
        ):
            from src.integration.consciousness_bridge import ConsciousnessBridge

            bridge = ConsciousnessBridge()
            time_str = bridge.get_initialization_time()

            # Should be format YYYY-MM-DD HH:MM:SS
            assert len(time_str) == 19
            assert "-" in time_str
            assert ":" in time_str
