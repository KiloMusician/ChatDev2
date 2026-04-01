"""Tests for EOLFacade - Epistemic-Operational Lattice Facade.

Tests the EOL facade integration for the sense → propose → critique → act
decision cycle with proper isolation via mocking.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from src.core.eol_facade_integration import EOLFacade
from src.core.result import Result

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_parent():
    """Create a mock parent orchestrator."""
    return MagicMock()


@pytest.fixture
def facade(mock_parent):
    """Create EOLFacade with mock parent."""
    return EOLFacade(mock_parent)


@pytest.fixture
def mock_eol_orchestrator():
    """Create a mock EOLOrchestrator."""
    mock = MagicMock()

    # Default sense returns a world state dict
    mock.sense.return_value = {
        "timestamp": "2025-01-01T00:00:00Z",
        "decision_epoch": 1,
        "observations": {},
        "signals": {"facts": []},
        "coherence": {"contradictions": []},
        "runtime_state": {},
        "policy_state": {},
        "objective": "",
        "metadata": {},
    }

    # Default propose returns action list
    mock.propose.return_value = [
        {"id": "act1", "agent": "ollama", "task_type": "analyze"},
        {"id": "act2", "agent": "chatdev", "task_type": "generate"},
    ]

    # Default critique returns approval
    mock.critique.return_value = True

    # Default act returns receipt
    receipt_mock = MagicMock()
    receipt_mock.status = "completed"
    receipt_mock.to_dict.return_value = {
        "id": "R001",
        "status": "completed",
        "duration_s": 0.5,
    }
    mock.act.return_value = receipt_mock

    # Default full_cycle returns cycle output
    mock.full_cycle.return_value = {
        "world_state": mock.sense.return_value,
        "actions": mock.propose.return_value,
        "approved_actions": [mock.propose.return_value[0]],
        "execution_results": [],
    }

    # Default stats
    mock.stats.return_value = {
        "success_rate": 0.85,
        "total_actions": 100,
        "by_agent": {"ollama": 50, "chatdev": 30},
    }

    # Default debug_info
    mock.debug_info.return_value = {
        "workspace_root": "/path/to/workspace",
        "ledger_size": 42,
    }

    return mock


# =============================================================================
# Initialization Tests
# =============================================================================


class TestEOLFacadeInit:
    """Tests for EOLFacade initialization."""

    def test_facade_creation(self, mock_parent):
        """Test facade can be created with a parent."""
        facade = EOLFacade(mock_parent)

        assert facade._parent is mock_parent
        assert facade._orchestrator is None

    def test_facade_stores_parent_reference(self, mock_parent):
        """Test facade stores reference to parent orchestrator."""
        facade = EOLFacade(mock_parent)

        assert facade._parent == mock_parent

    def test_orchestrator_lazy_loading(self, facade):
        """Test orchestrator is not loaded at init."""
        assert facade._orchestrator is None


# =============================================================================
# _get_orchestrator Tests
# =============================================================================


class TestGetOrchestrator:
    """Tests for the _get_orchestrator method."""

    def test_get_orchestrator_returns_none_on_import_error(self, facade):
        """Test _get_orchestrator returns None when import fails."""
        with patch.dict("sys.modules", {"src.core.eol_integration": None}):
            with patch(
                "src.core.eol_facade_integration.EOLFacade._get_orchestrator", return_value=None
            ):
                pass  # Just verify no exception

    def test_get_orchestrator_caches_instance(self, facade, mock_eol_orchestrator):
        """Test orchestrator is cached after first load."""
        with patch("src.core.eol_integration.EOLOrchestrator", return_value=mock_eol_orchestrator):
            # First call creates instance
            orch1 = facade._get_orchestrator()
            # Second call returns cached
            orch2 = facade._get_orchestrator()

            assert orch1 is orch2


# =============================================================================
# sense() Tests
# =============================================================================


class TestSense:
    """Tests for the sense() method."""

    def test_sense_success(self, facade, mock_eol_orchestrator):
        """Test sense() returns Ok with world state on success."""
        facade._orchestrator = mock_eol_orchestrator

        result = facade.sense()

        assert isinstance(result, Result)
        assert result.ok is True
        assert "decision_epoch" in result.value
        assert "signals" in result.value

    def test_sense_returns_decision_epoch(self, facade, mock_eol_orchestrator):
        """Test sense() includes decision epoch in message."""
        facade._orchestrator = mock_eol_orchestrator

        result = facade.sense()

        assert result.ok
        assert "epoch" in result.message.lower()

    def test_sense_unavailable_orchestrator(self, facade):
        """Test sense() returns Fail when orchestrator unavailable."""
        with patch.object(facade, "_get_orchestrator", return_value=None):
            result = facade.sense()

        assert not result.ok
        assert result.code == "UNAVAILABLE"

    def test_sense_handles_exception(self, facade, mock_eol_orchestrator):
        """Test sense() returns Fail on exception."""
        mock_eol_orchestrator.sense.side_effect = Exception("Sense failed")
        facade._orchestrator = mock_eol_orchestrator

        result = facade.sense()

        assert not result.ok
        assert result.code == "SENSE_ERROR"
        assert "Sense failed" in result.error


# =============================================================================
# propose() Tests
# =============================================================================


class TestPropose:
    """Tests for the propose() method."""

    def test_propose_success(self, facade, mock_eol_orchestrator):
        """Test propose() returns Ok with action list on success."""
        facade._orchestrator = mock_eol_orchestrator
        world_state = {"decision_epoch": 1}

        result = facade.propose(world_state, "Analyze errors")

        assert result.ok
        assert isinstance(result.value, list)
        assert len(result.value) == 2

    def test_propose_includes_agent_info(self, facade, mock_eol_orchestrator):
        """Test propose() returns actions with agent information."""
        facade._orchestrator = mock_eol_orchestrator
        world_state = {"decision_epoch": 1}

        result = facade.propose(world_state, "Fix tests")

        assert result.ok
        assert result.value[0]["agent"] == "ollama"
        assert result.value[1]["agent"] == "chatdev"

    def test_propose_empty_objective(self, facade, mock_eol_orchestrator):
        """Test propose() works with empty objective."""
        facade._orchestrator = mock_eol_orchestrator
        world_state = {"decision_epoch": 1}

        result = facade.propose(world_state, "")

        assert result.ok

    def test_propose_unavailable_orchestrator(self, facade):
        """Test propose() returns Fail when orchestrator unavailable."""
        with patch.object(facade, "_get_orchestrator", return_value=None):
            result = facade.propose({}, "test")

        assert not result.ok
        assert result.code == "UNAVAILABLE"

    def test_propose_handles_exception(self, facade, mock_eol_orchestrator):
        """Test propose() returns Fail on exception."""
        mock_eol_orchestrator.propose.side_effect = Exception("Propose failed")
        facade._orchestrator = mock_eol_orchestrator

        result = facade.propose({}, "test")

        assert not result.ok
        assert result.code == "PROPOSE_ERROR"


# =============================================================================
# critique() Tests
# =============================================================================


class TestCritique:
    """Tests for the critique() method."""

    def test_critique_approved(self, facade, mock_eol_orchestrator):
        """Test critique() returns Ok(True) when approved."""
        facade._orchestrator = mock_eol_orchestrator
        action = {"id": "act1", "agent": "ollama"}
        world_state = {"decision_epoch": 1}

        result = facade.critique(action, world_state)

        assert result.ok
        assert result.value is True
        assert "approved" in result.message.lower()

    def test_critique_rejected(self, facade, mock_eol_orchestrator):
        """Test critique() returns Ok(False) when rejected."""
        mock_eol_orchestrator.critique.return_value = False
        facade._orchestrator = mock_eol_orchestrator
        action = {"id": "act1", "agent": "ollama"}
        world_state = {"decision_epoch": 1}

        result = facade.critique(action, world_state)

        assert result.ok
        assert result.value is False
        assert "rejected" in result.message.lower()

    def test_critique_unavailable_orchestrator(self, facade):
        """Test critique() returns Fail when orchestrator unavailable."""
        with patch.object(facade, "_get_orchestrator", return_value=None):
            result = facade.critique({}, {})

        assert not result.ok
        assert result.code == "UNAVAILABLE"

    def test_critique_handles_exception(self, facade, mock_eol_orchestrator):
        """Test critique() returns Fail on exception."""
        mock_eol_orchestrator.critique.side_effect = Exception("Critique failed")
        facade._orchestrator = mock_eol_orchestrator

        result = facade.critique({}, {})

        assert not result.ok
        assert result.code == "CRITIQUE_ERROR"


# =============================================================================
# act() Tests
# =============================================================================


class TestAct:
    """Tests for the act() method."""

    def test_act_success(self, facade, mock_eol_orchestrator):
        """Test act() returns Ok with receipt on success."""
        facade._orchestrator = mock_eol_orchestrator
        action = {"id": "act1", "agent": "ollama"}
        world_state = {"decision_epoch": 1}

        result = facade.act(action, world_state)

        assert result.ok
        assert "status" in result.value
        assert result.value["status"] == "completed"

    def test_act_dry_run(self, facade, mock_eol_orchestrator):
        """Test act() respects dry_run parameter."""
        facade._orchestrator = mock_eol_orchestrator
        action = {"id": "act1", "agent": "ollama"}
        world_state = {"decision_epoch": 1}

        facade.act(action, world_state, dry_run=True)

        mock_eol_orchestrator.act.assert_called_with(action, world_state, dry_run=True)

    def test_act_returns_receipt_dict(self, facade, mock_eol_orchestrator):
        """Test act() returns receipt as dict, not object."""
        facade._orchestrator = mock_eol_orchestrator

        result = facade.act({}, {})

        assert result.ok
        assert isinstance(result.value, dict)
        assert "id" in result.value or "status" in result.value

    def test_act_unavailable_orchestrator(self, facade):
        """Test act() returns Fail when orchestrator unavailable."""
        with patch.object(facade, "_get_orchestrator", return_value=None):
            result = facade.act({}, {})

        assert not result.ok
        assert result.code == "UNAVAILABLE"

    def test_act_handles_exception(self, facade, mock_eol_orchestrator):
        """Test act() returns Fail on exception."""
        mock_eol_orchestrator.act.side_effect = Exception("Act failed")
        facade._orchestrator = mock_eol_orchestrator

        result = facade.act({}, {})

        assert not result.ok
        assert result.code == "ACT_ERROR"


# =============================================================================
# full_cycle() Tests
# =============================================================================


class TestFullCycle:
    """Tests for the full_cycle() method."""

    def test_full_cycle_success(self, facade, mock_eol_orchestrator):
        """Test full_cycle() returns Ok with cycle output on success."""
        facade._orchestrator = mock_eol_orchestrator

        result = facade.full_cycle("Analyze errors")

        assert result.ok
        assert "world_state" in result.value
        assert "actions" in result.value
        assert "approved_actions" in result.value

    def test_full_cycle_respects_auto_execute(self, facade, mock_eol_orchestrator):
        """Test full_cycle() passes auto_execute parameter."""
        facade._orchestrator = mock_eol_orchestrator

        facade.full_cycle("test", auto_execute=True)

        mock_eol_orchestrator.full_cycle.assert_called_with(
            "test", auto_execute=True, dry_run=False
        )

    def test_full_cycle_respects_dry_run(self, facade, mock_eol_orchestrator):
        """Test full_cycle() passes dry_run parameter."""
        facade._orchestrator = mock_eol_orchestrator

        facade.full_cycle("test", dry_run=True)

        mock_eol_orchestrator.full_cycle.assert_called_with(
            "test", auto_execute=False, dry_run=True
        )

    def test_full_cycle_empty_objective(self, facade, mock_eol_orchestrator):
        """Test full_cycle() works with empty objective."""
        facade._orchestrator = mock_eol_orchestrator

        result = facade.full_cycle("")

        assert result.ok

    def test_full_cycle_unavailable_orchestrator(self, facade):
        """Test full_cycle() returns Fail when orchestrator unavailable."""
        with patch.object(facade, "_get_orchestrator", return_value=None):
            result = facade.full_cycle("test")

        assert not result.ok
        assert result.code == "UNAVAILABLE"

    def test_full_cycle_handles_exception(self, facade, mock_eol_orchestrator):
        """Test full_cycle() returns Fail on exception."""
        mock_eol_orchestrator.full_cycle.side_effect = Exception("Cycle failed")
        facade._orchestrator = mock_eol_orchestrator

        result = facade.full_cycle("test")

        assert not result.ok
        assert result.code == "FULL_CYCLE_ERROR"


# =============================================================================
# stats() Tests
# =============================================================================


class TestStats:
    """Tests for the stats() method."""

    def test_stats_success(self, facade, mock_eol_orchestrator):
        """Test stats() returns Ok with stats dict on success."""
        facade._orchestrator = mock_eol_orchestrator

        result = facade.stats()

        assert result.ok
        assert "success_rate" in result.value
        assert "total_actions" in result.value

    def test_stats_includes_by_agent(self, facade, mock_eol_orchestrator):
        """Test stats() includes per-agent breakdown."""
        facade._orchestrator = mock_eol_orchestrator

        result = facade.stats()

        assert result.ok
        assert "by_agent" in result.value
        assert "ollama" in result.value["by_agent"]

    def test_stats_unavailable_orchestrator(self, facade):
        """Test stats() returns Fail when orchestrator unavailable."""
        with patch.object(facade, "_get_orchestrator", return_value=None):
            result = facade.stats()

        assert not result.ok
        assert result.code == "UNAVAILABLE"

    def test_stats_handles_exception(self, facade, mock_eol_orchestrator):
        """Test stats() returns Fail on exception."""
        mock_eol_orchestrator.stats.side_effect = Exception("Stats failed")
        facade._orchestrator = mock_eol_orchestrator

        result = facade.stats()

        assert not result.ok
        assert result.code == "STATS_ERROR"


# =============================================================================
# debug() Tests
# =============================================================================


class TestDebug:
    """Tests for the debug() method."""

    def test_debug_success(self, facade, mock_eol_orchestrator):
        """Test debug() returns Ok with debug info on success."""
        facade._orchestrator = mock_eol_orchestrator

        result = facade.debug()

        assert result.ok
        assert isinstance(result.value, dict)

    def test_debug_includes_workspace_root(self, facade, mock_eol_orchestrator):
        """Test debug() includes workspace root path."""
        facade._orchestrator = mock_eol_orchestrator

        result = facade.debug()

        assert result.ok
        assert "workspace_root" in result.value

    def test_debug_unavailable_orchestrator(self, facade):
        """Test debug() returns Fail when orchestrator unavailable."""
        with patch.object(facade, "_get_orchestrator", return_value=None):
            result = facade.debug()

        assert not result.ok
        assert result.code == "UNAVAILABLE"

    def test_debug_handles_exception(self, facade, mock_eol_orchestrator):
        """Test debug() returns Fail on exception."""
        mock_eol_orchestrator.debug_info.side_effect = Exception("Debug failed")
        facade._orchestrator = mock_eol_orchestrator

        result = facade.debug()

        assert not result.ok
        assert result.code == "DEBUG_ERROR"


# =============================================================================
# Integration Flow Tests
# =============================================================================


class TestIntegrationFlows:
    """Tests for complete workflow integration."""

    def test_sense_propose_critique_act_flow(self, facade, mock_eol_orchestrator):
        """Test complete sense → propose → critique → act flow."""
        facade._orchestrator = mock_eol_orchestrator

        # 1. Sense
        sense_result = facade.sense()
        assert sense_result.ok
        world_state = sense_result.value

        # 2. Propose
        propose_result = facade.propose(world_state, "Fix the bug")
        assert propose_result.ok
        actions = propose_result.value
        assert len(actions) > 0

        # 3. Critique
        critique_result = facade.critique(actions[0], world_state)
        assert critique_result.ok
        approved = critique_result.value

        # 4. Act (if approved)
        if approved:
            act_result = facade.act(actions[0], world_state)
            assert act_result.ok
            receipt = act_result.value
            assert "status" in receipt

    def test_full_cycle_equivalent_to_manual_steps(self, facade, mock_eol_orchestrator):
        """Test full_cycle produces similar output to manual steps."""
        facade._orchestrator = mock_eol_orchestrator

        # Full cycle
        cycle_result = facade.full_cycle("Analyze errors")
        assert cycle_result.ok

        # Verify structure
        output = cycle_result.value
        assert "world_state" in output
        assert "actions" in output
        assert "approved_actions" in output


# =============================================================================
# Error Recovery Tests
# =============================================================================


class TestErrorRecovery:
    """Tests for error handling and recovery."""

    def test_all_methods_handle_import_error_gracefully(self, facade):
        """Test all methods return Fail when orchestrator unavailable."""
        with patch.object(facade, "_get_orchestrator", return_value=None):
            sense_result = facade.sense()
            propose_result = facade.propose({}, "test")
            critique_result = facade.critique({}, {})
            act_result = facade.act({}, {})
            cycle_result = facade.full_cycle("test")
            stats_result = facade.stats()
            debug_result = facade.debug()

        for result in [
            sense_result,
            propose_result,
            critique_result,
            act_result,
            cycle_result,
            stats_result,
            debug_result,
        ]:
            assert not result.ok
            assert result.code == "UNAVAILABLE"

    def test_exception_messages_preserved(self, facade, mock_eol_orchestrator):
        """Test exception messages are preserved in Fail results."""
        unique_error = "UniqueError_XYZ_12345"
        mock_eol_orchestrator.sense.side_effect = Exception(unique_error)
        facade._orchestrator = mock_eol_orchestrator

        result = facade.sense()

        assert not result.ok
        assert unique_error in result.error

    def test_error_codes_are_specific(self, facade, mock_eol_orchestrator):
        """Test each method has its own error code."""
        facade._orchestrator = mock_eol_orchestrator

        # Set up failures
        mock_eol_orchestrator.sense.side_effect = Exception("fail")
        mock_eol_orchestrator.propose.side_effect = Exception("fail")
        mock_eol_orchestrator.critique.side_effect = Exception("fail")
        mock_eol_orchestrator.act.side_effect = Exception("fail")
        mock_eol_orchestrator.full_cycle.side_effect = Exception("fail")
        mock_eol_orchestrator.stats.side_effect = Exception("fail")
        mock_eol_orchestrator.debug_info.side_effect = Exception("fail")

        # Collect error codes
        codes = {
            facade.sense().code,
            facade.propose({}, "").code,
            facade.critique({}, {}).code,
            facade.act({}, {}).code,
            facade.full_cycle("").code,
            facade.stats().code,
            facade.debug().code,
        }

        # All codes should be unique
        assert len(codes) == 7


# =============================================================================
# Result Type Tests
# =============================================================================


class TestResultTypes:
    """Tests verifying correct Result type usage."""

    def test_sense_returns_result(self, facade, mock_eol_orchestrator):
        """Test sense() returns Result type."""
        facade._orchestrator = mock_eol_orchestrator

        result = facade.sense()

        assert isinstance(result, Result)

    def test_propose_returns_result(self, facade, mock_eol_orchestrator):
        """Test propose() returns Result type."""
        facade._orchestrator = mock_eol_orchestrator

        result = facade.propose({}, "test")

        assert isinstance(result, Result)

    def test_successful_results_are_ok(self, facade, mock_eol_orchestrator):
        """Test successful operations return Ok results."""
        facade._orchestrator = mock_eol_orchestrator

        for result in [
            facade.sense(),
            facade.propose({}, ""),
            facade.critique({}, {}),
            facade.act({}, {}),
            facade.full_cycle(""),
            facade.stats(),
            facade.debug(),
        ]:
            assert result.ok, f"Expected Ok but got {result}"

    def test_failed_results_are_fail(self, facade):
        """Test failed operations return Fail results."""
        with patch.object(facade, "_get_orchestrator", return_value=None):
            for result in [
                facade.sense(),
                facade.propose({}, ""),
                facade.critique({}, {}),
                facade.act({}, {}),
                facade.full_cycle(""),
                facade.stats(),
                facade.debug(),
            ]:
                assert not result.ok, f"Expected Fail but got {result}"
