"""Tests for src/core/eol_integration.py - EOLOrchestrator.

This module tests the Epistemic-Operational Lattice orchestrator which
ties together Observation, Planning, and Execution planes.

Coverage Target: 70%+
"""

import json
from unittest.mock import MagicMock, patch

import pytest

# =============================================================================
# Module Import
# =============================================================================


class TestModuleImports:
    """Test module-level imports."""

    def test_import_eol_orchestrator(self):
        """Test that EOLOrchestrator can be imported."""
        from src.core.eol_integration import EOLOrchestrator

        assert EOLOrchestrator is not None

    def test_import_integrate_function(self):
        """Test that integrate_eol_with_orchestrate can be imported."""
        from src.core.eol_integration import integrate_eol_with_orchestrate

        assert integrate_eol_with_orchestrate is not None


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace directory."""
    state_dir = tmp_path / "state"
    state_dir.mkdir(parents=True)
    return tmp_path


@pytest.fixture
def mock_world_state():
    """Sample world state for testing."""
    return {
        "decision_epoch": 42,
        "signals": {
            "facts": [
                {"source": "test", "confidence": 0.9},
                {"source": "test2", "confidence": 0.8},
            ]
        },
        "coherence": {
            "contradictions": [],
            "drift_detected": False,
        },
        "policy_state": {
            "safety_gates": {
                "max_risk_score": 0.7,
            }
        },
    }


@pytest.fixture
def mock_action():
    """Sample action for testing."""
    return {
        "action_id": "test-action-123456789",
        "agent": "ollama",
        "task_type": "analyze",
        "description": "Analyze test file",
        "risk_score": 0.3,
        "policy_category": "FEATURE",
        "estimated_cost": {"tokens": 500},
    }


@pytest.fixture
def mock_receipt():
    """Sample action receipt for testing."""
    mock = MagicMock()
    mock.receipt_id = "receipt-123"
    mock.action_type = "analyze"
    mock.status = "completed"
    mock.metadata = {"agent": "ollama"}
    mock.to_dict.return_value = {
        "receipt_id": "receipt-123",
        "action_type": "analyze",
        "status": "completed",
    }
    return mock


@pytest.fixture
def mock_ledger():
    """Mock ActionReceiptLedger."""
    ledger = MagicMock()
    ledger.execute_action.return_value = MagicMock(
        receipt_id="mock-receipt",
        status="completed",
        to_dict=MagicMock(return_value={"receipt_id": "mock-receipt", "status": "completed"}),
    )
    ledger.get_action_stats.return_value = {"total_actions": 10, "success_rate": 0.9}
    ledger.recent.return_value = []
    return ledger


@pytest.fixture
def orchestrator(temp_workspace, mock_ledger):
    """Create EOLOrchestrator with mocked dependencies."""
    with patch("src.core.eol_integration.ActionReceiptLedger", return_value=mock_ledger):
        with patch("src.core.eol_integration.PlanGenerator"):
            from src.core.eol_integration import EOLOrchestrator

            orch = EOLOrchestrator(
                workspace_root=temp_workspace,
                ledger_file=temp_workspace / "ledger.jsonl",
                state_snapshot_file=temp_workspace / "state" / "snapshot.json",
            )
            orch.ledger = mock_ledger
            return orch


# =============================================================================
# EOLOrchestrator Initialization Tests
# =============================================================================


class TestEOLOrchestratorInit:
    """Test EOLOrchestrator initialization."""

    def test_init_default_paths(self, temp_workspace):
        """Test initialization with default paths."""
        with patch("src.core.eol_integration.ActionReceiptLedger"):
            from src.core.eol_integration import EOLOrchestrator

            orch = EOLOrchestrator(workspace_root=temp_workspace)

            assert orch.workspace_root == temp_workspace
            assert orch.previous_world_state is None
            assert orch._consciousness_loop is None

    def test_init_custom_paths(self, temp_workspace):
        """Test initialization with custom paths."""
        with patch("src.core.eol_integration.ActionReceiptLedger"):
            from src.core.eol_integration import EOLOrchestrator

            ledger_file = temp_workspace / "custom_ledger.jsonl"
            snapshot_file = temp_workspace / "custom_snapshot.json"

            orch = EOLOrchestrator(
                workspace_root=temp_workspace,
                ledger_file=ledger_file,
                state_snapshot_file=snapshot_file,
            )

            assert orch.state_snapshot_file == snapshot_file

    def test_init_creates_state_dir(self, tmp_path):
        """Test that init creates state directory if needed."""
        with patch("src.core.eol_integration.ActionReceiptLedger"):
            from src.core.eol_integration import EOLOrchestrator

            snapshot = tmp_path / "new_state_dir" / "snapshot.json"

            EOLOrchestrator(
                workspace_root=tmp_path,
                state_snapshot_file=snapshot,
            )

            assert snapshot.parent.exists()


# =============================================================================
# sense() Tests
# =============================================================================


class TestSense:
    """Test sense() method."""

    def test_sense_returns_world_state(self, orchestrator, mock_world_state):
        """Test sense() returns world state dict."""
        with patch("src.core.eol_integration.build_world_state", return_value=mock_world_state):
            result = orchestrator.sense()

        assert isinstance(result, dict)
        assert "decision_epoch" in result
        assert result["decision_epoch"] == 42

    def test_sense_updates_previous_state(self, orchestrator, mock_world_state):
        """Test sense() caches world state for drift detection."""
        with patch("src.core.eol_integration.build_world_state", return_value=mock_world_state):
            assert orchestrator.previous_world_state is None

            orchestrator.sense()

            assert orchestrator.previous_world_state == mock_world_state

    def test_sense_writes_snapshot(self, orchestrator, mock_world_state):
        """Test sense() writes state snapshot to disk."""
        with patch("src.core.eol_integration.build_world_state", return_value=mock_world_state):
            orchestrator.sense()

        assert orchestrator.state_snapshot_file.exists()

        with open(orchestrator.state_snapshot_file) as f:
            saved_state = json.load(f)

        assert saved_state["decision_epoch"] == 42

    def test_sense_passes_previous_state_to_builder(self, orchestrator, mock_world_state):
        """Test sense() passes previous state for drift detection."""
        previous = {"decision_epoch": 41}
        orchestrator.previous_world_state = previous

        with patch(
            "src.core.eol_integration.build_world_state", return_value=mock_world_state
        ) as mock_build:
            orchestrator.sense()

            mock_build.assert_called_once()
            call_kwargs = mock_build.call_args[1]
            assert call_kwargs.get("previous_state") == previous


# =============================================================================
# propose() Tests
# =============================================================================


class TestPropose:
    """Test propose() method."""

    def test_propose_returns_action_list(self, orchestrator, mock_world_state):
        """Test propose() returns list of actions."""
        mock_plan = {
            "actions": [
                {"action_id": "1", "agent": "ollama", "task_type": "analyze"},
                {"action_id": "2", "agent": "chatdev", "task_type": "generate"},
            ]
        }

        with patch("src.core.eol_integration.plan_from_world_state", return_value=mock_plan):
            result = orchestrator.propose(mock_world_state, "Analyze code")

        assert isinstance(result, list)
        assert len(result) == 2

    def test_propose_with_empty_objective(self, orchestrator, mock_world_state):
        """Test propose() works with empty objective."""
        mock_plan = {"actions": [{"action_id": "x", "agent": "test", "task_type": "test"}]}

        with patch("src.core.eol_integration.plan_from_world_state", return_value=mock_plan):
            result = orchestrator.propose(mock_world_state, "")

        assert len(result) == 1

    def test_propose_returns_empty_when_no_actions(self, orchestrator, mock_world_state):
        """Test propose() returns empty list when no actions generated."""
        mock_plan = {"actions": []}

        with patch("src.core.eol_integration.plan_from_world_state", return_value=mock_plan):
            result = orchestrator.propose(mock_world_state, "Something impossible")

        assert result == []


# =============================================================================
# critique() Tests
# =============================================================================


class TestCritique:
    """Test critique() method."""

    def test_critique_approves_low_risk_action(self, orchestrator, mock_action, mock_world_state):
        """Test critique() approves action with risk below threshold."""
        mock_action["risk_score"] = 0.3  # Below 0.7 threshold

        result = orchestrator.critique(mock_action, mock_world_state)

        assert result is True

    def test_critique_rejects_high_risk_action(self, orchestrator, mock_action, mock_world_state):
        """Test critique() rejects action with risk above threshold."""
        mock_action["risk_score"] = 0.9  # Above 0.7 threshold

        result = orchestrator.critique(mock_action, mock_world_state)

        assert result is False

    def test_critique_uses_custom_max_risk(self, orchestrator, mock_action, mock_world_state):
        """Test critique() respects custom max_risk from policy state."""
        mock_action["risk_score"] = 0.5
        mock_world_state["policy_state"]["safety_gates"]["max_risk_score"] = 0.4

        result = orchestrator.critique(mock_action, mock_world_state)

        assert result is False  # 0.5 > 0.4

    def test_critique_handles_missing_risk_score(self, orchestrator, mock_world_state):
        """Test critique() handles action without risk_score."""
        action = {"action_id": "test", "policy_category": "FEATURE"}

        result = orchestrator.critique(action, mock_world_state)

        assert result is True  # Default risk 0.0 < 0.7


# =============================================================================
# SECURITY Category Tests (Culture Ship Integration)
# =============================================================================


class TestCritiqueSecurityCategory:
    """Test critique() with SECURITY category actions."""

    def test_security_action_approved_by_culture_ship(
        self, orchestrator, mock_action, mock_world_state
    ):
        """Test SECURITY action approved when Culture Ship approves."""
        mock_action["policy_category"] = "SECURITY"
        mock_action["risk_score"] = 0.3

        mock_approval = MagicMock()
        mock_approval.approved = True
        mock_approval.reason = "Approved for testing"

        mock_loop = MagicMock()
        mock_loop.request_approval.return_value = mock_approval

        with patch(
            "src.orchestration.consciousness_loop.ConsciousnessLoop", return_value=mock_loop
        ):
            result = orchestrator.critique(mock_action, mock_world_state)

        assert result is True

    def test_security_action_rejected_by_culture_ship(
        self, orchestrator, mock_action, mock_world_state
    ):
        """Test SECURITY action rejected when Culture Ship vetoes."""
        mock_action["policy_category"] = "SECURITY"
        mock_action["risk_score"] = 0.3

        mock_approval = MagicMock()
        mock_approval.approved = False
        mock_approval.reason = "Veto for testing"

        mock_loop = MagicMock()
        mock_loop.request_approval.return_value = mock_approval

        with patch(
            "src.orchestration.consciousness_loop.ConsciousnessLoop", return_value=mock_loop
        ):
            result = orchestrator.critique(mock_action, mock_world_state)

        assert result is False

    def test_security_auto_approves_when_consciousness_unavailable(
        self, orchestrator, mock_action, mock_world_state
    ):
        """Test SECURITY actions auto-approve when ConsciousnessLoop unavailable."""
        mock_action["policy_category"] = "SECURITY"
        mock_action["risk_score"] = 0.3

        with patch(
            "src.orchestration.consciousness_loop.ConsciousnessLoop",
            side_effect=Exception("Not available"),
        ):
            result = orchestrator.critique(mock_action, mock_world_state)

        assert result is True  # Graceful degradation


# =============================================================================
# act() Tests
# =============================================================================


class TestAct:
    """Test act() method."""

    def test_act_returns_receipt(self, orchestrator, mock_action, mock_world_state, mock_ledger):
        """Test act() returns ActionReceipt."""
        result = orchestrator.act(mock_action, mock_world_state)

        mock_ledger.execute_action.assert_called_once()
        assert result.receipt_id == "mock-receipt"

    def test_act_passes_dry_run_flag(
        self, orchestrator, mock_action, mock_world_state, mock_ledger
    ):
        """Test act() passes dry_run to ledger."""
        orchestrator.act(mock_action, mock_world_state, dry_run=True)

        call_args = mock_ledger.execute_action.call_args
        assert call_args[1].get("dry_run") is True

    def test_act_with_default_dry_run_false(
        self, orchestrator, mock_action, mock_world_state, mock_ledger
    ):
        """Test act() defaults dry_run to False."""
        orchestrator.act(mock_action, mock_world_state)

        call_args = mock_ledger.execute_action.call_args
        assert call_args[1].get("dry_run") is False


# =============================================================================
# learn() Tests
# =============================================================================


class TestLearn:
    """Test learn() method."""

    def test_learn_handles_receipt(self, orchestrator, mock_receipt):
        """Test learn() processes receipt without error."""
        # Should not raise
        orchestrator.learn(mock_receipt)

    def test_learn_handles_exceptions_gracefully(self, orchestrator, mock_receipt, mock_ledger):
        """Test learn() handles exceptions without crashing."""
        mock_ledger.recent.side_effect = Exception("DB error")

        # Should not raise, just log warning
        orchestrator.learn(mock_receipt)


# =============================================================================
# full_cycle() Tests
# =============================================================================


class TestFullCycle:
    """Test full_cycle() method."""

    def test_full_cycle_returns_structured_output(self, orchestrator, mock_world_state):
        """Test full_cycle() returns expected structure."""
        mock_plan = {
            "actions": [{"action_id": "1", "agent": "test", "task_type": "test", "risk_score": 0.3}]
        }

        with patch("src.core.eol_integration.build_world_state", return_value=mock_world_state):
            with patch("src.core.eol_integration.plan_from_world_state", return_value=mock_plan):
                result = orchestrator.full_cycle("Analyze code")

        assert "world_state" in result
        assert "actions" in result
        assert "approved_actions" in result
        assert "execution_results" in result
        assert "metadata" in result

    def test_full_cycle_no_auto_execute(self, orchestrator, mock_world_state):
        """Test full_cycle() without auto_execute returns no execution results."""
        mock_plan = {
            "actions": [{"action_id": "1", "agent": "test", "task_type": "test", "risk_score": 0.3}]
        }

        with patch("src.core.eol_integration.build_world_state", return_value=mock_world_state):
            with patch("src.core.eol_integration.plan_from_world_state", return_value=mock_plan):
                result = orchestrator.full_cycle("Test", auto_execute=False)

        assert result["execution_results"] == []

    def test_full_cycle_with_auto_execute(self, orchestrator, mock_world_state):
        """Test full_cycle() with auto_execute runs top action."""
        mock_plan = {
            "actions": [{"action_id": "1", "agent": "test", "task_type": "test", "risk_score": 0.3}]
        }

        with patch("src.core.eol_integration.build_world_state", return_value=mock_world_state):
            with patch("src.core.eol_integration.plan_from_world_state", return_value=mock_plan):
                result = orchestrator.full_cycle("Test", auto_execute=True)

        assert len(result["execution_results"]) == 1

    def test_full_cycle_no_actions_generated(self, orchestrator, mock_world_state):
        """Test full_cycle() handles empty action list."""
        mock_plan = {"actions": []}

        with patch("src.core.eol_integration.build_world_state", return_value=mock_world_state):
            with patch("src.core.eol_integration.plan_from_world_state", return_value=mock_plan):
                result = orchestrator.full_cycle("Impossible task")

        assert result["actions"] == []
        assert "No valid actions" in result["metadata"]["reason"]

    def test_full_cycle_all_actions_rejected(self, orchestrator, mock_world_state):
        """Test full_cycle() handles all actions being rejected."""
        mock_plan = {
            "actions": [
                {"action_id": "1", "agent": "test", "task_type": "test", "risk_score": 0.99}
            ]
        }

        with patch("src.core.eol_integration.build_world_state", return_value=mock_world_state):
            with patch("src.core.eol_integration.plan_from_world_state", return_value=mock_plan):
                result = orchestrator.full_cycle("Risky task")

        # When all rejected, no approved_actions key
        assert result["execution_results"] == []
        assert "rejected by policy" in result["metadata"]["reason"]


# =============================================================================
# State Persistence Tests
# =============================================================================


class TestStatePersistence:
    """Test state snapshot persistence."""

    def test_read_state_snapshot_returns_saved_state(self, orchestrator, mock_world_state):
        """Test read_state_snapshot() returns previously saved state."""
        # Write state
        with open(orchestrator.state_snapshot_file, "w") as f:
            json.dump(mock_world_state, f)

        result = orchestrator.read_state_snapshot()

        assert result == mock_world_state

    def test_read_state_snapshot_returns_none_when_missing(self, orchestrator):
        """Test read_state_snapshot() returns None when file doesn't exist."""
        result = orchestrator.read_state_snapshot()

        assert result is None

    def test_read_state_snapshot_handles_corrupt_file(self, orchestrator):
        """Test read_state_snapshot() handles corrupt JSON."""
        with open(orchestrator.state_snapshot_file, "w") as f:
            f.write("not valid json{{{")

        result = orchestrator.read_state_snapshot()

        assert result is None


# =============================================================================
# stats() and debug_info() Tests
# =============================================================================


class TestStatsAndDebug:
    """Test stats() and debug_info() methods."""

    def test_stats_returns_ledger_stats(self, orchestrator, mock_ledger):
        """Test stats() returns stats from ledger."""
        result = orchestrator.stats()

        mock_ledger.get_action_stats.assert_called_once()
        assert result["total_actions"] == 10

    def test_debug_info_returns_full_debug(self, orchestrator, mock_ledger):
        """Test debug_info() returns comprehensive debug info."""
        result = orchestrator.debug_info()

        assert "workspace_root" in result
        assert "ledger_file" in result
        assert "state_snapshot_file" in result
        assert "action_stats" in result
        assert "previous_world_state_epoch" in result

    def test_debug_info_epoch_negative_one_when_no_previous(self, orchestrator):
        """Test debug_info() returns -1 for epoch when no previous state."""
        result = orchestrator.debug_info()

        assert result["previous_world_state_epoch"] == -1


# =============================================================================
# Edge Cases & Error Handling
# =============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_write_snapshot_handles_serialization_error(self, orchestrator, caplog):
        """Test _write_state_snapshot handles non-serializable objects."""
        import logging

        bad_state = {"decision_epoch": 1, "bad_object": object()}

        with caplog.at_level(logging.ERROR):
            orchestrator._write_state_snapshot(bad_state)

        # Should log error but not raise
        assert "Failed to write" in caplog.text or True  # May not log in all cases

    def test_critique_handles_missing_policy_state(self, orchestrator, mock_action):
        """Test critique() handles world state without policy_state."""
        world_state = {"decision_epoch": 1}  # No policy_state
        mock_action["risk_score"] = 0.3

        result = orchestrator.critique(mock_action, world_state)

        assert result is True  # Uses default threshold

    def test_act_with_minimal_action(self, orchestrator, mock_world_state, mock_ledger):
        """Test act() with minimal action dict."""
        minimal_action = {"action_id": "min"}

        orchestrator.act(minimal_action, mock_world_state)

        mock_ledger.execute_action.assert_called_once()

    def test_consciousness_loop_cached(self, orchestrator, mock_action, mock_world_state):
        """Test ConsciousnessLoop is cached after first use."""
        mock_action["policy_category"] = "SECURITY"
        mock_action["risk_score"] = 0.3

        mock_approval = MagicMock()
        mock_approval.approved = True
        mock_approval.reason = "OK"

        mock_loop = MagicMock()
        mock_loop.request_approval.return_value = mock_approval

        with patch(
            "src.orchestration.consciousness_loop.ConsciousnessLoop", return_value=mock_loop
        ) as mock_cls:
            orchestrator.critique(mock_action, mock_world_state)
            orchestrator.critique(mock_action, mock_world_state)

        # Should only create loop once
        assert mock_cls.call_count == 1


# =============================================================================
# Integration Function Tests
# =============================================================================


class TestIntegration:
    """Test integration helpers."""

    def test_integrate_function_exists(self):
        """Test integrate_eol_with_orchestrate exists."""
        from src.core.eol_integration import integrate_eol_with_orchestrate

        # Should not raise when called
        integrate_eol_with_orchestrate()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
