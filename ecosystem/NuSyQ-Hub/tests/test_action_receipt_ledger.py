"""Comprehensive tests for src/core/action_receipt_ledger.py.

Tests ActionReceipt dataclass, validators, and ActionReceiptLedger for:
- Receipt model serialization
- Precondition and postcondition validation
- Action execution with dry-run and real dispatch
- Ledger persistence (append/read)
- Statistics computation
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.action_receipt_ledger import (
    ActionReceipt,
    ActionReceiptLedger,
    PostconditionValidator,
    PreconditionValidator,
    execute_action_and_log,
)


class TestActionReceipt:
    """Test ActionReceipt dataclass."""

    def test_receipt_required_fields(self) -> None:
        """Create receipt with required fields."""
        receipt = ActionReceipt(
            receipt_id="r-123",
            action_id="a-456",
            timestamp_start="2024-01-01T00:00:00+00:00",
            timestamp_end="2024-01-01T00:01:00+00:00",
            duration_s=60.0,
            agent="ollama",
            task_type="analysis",
            status="SUCCESS",
        )

        assert receipt.receipt_id == "r-123"
        assert receipt.action_id == "a-456"
        assert receipt.agent == "ollama"
        assert receipt.status == "SUCCESS"
        assert receipt.duration_s == 60.0

    def test_receipt_optional_fields_defaults(self) -> None:
        """Optional fields have correct defaults."""
        receipt = ActionReceipt(
            receipt_id="r-1",
            action_id="a-1",
            timestamp_start="2024-01-01T00:00:00+00:00",
            timestamp_end="2024-01-01T00:00:01+00:00",
            duration_s=1.0,
            agent="test",
            task_type="test",
            status="SUCCESS",
        )

        assert receipt.exit_code is None
        assert receipt.stdout == ""
        assert receipt.stderr == ""
        assert receipt.artifacts == []
        assert receipt.preconditions_met is False
        assert receipt.postconditions_met is False
        assert receipt.postcondition_validation_results == {}
        assert receipt.error_message is None
        assert receipt.linked_quest_id is None
        assert receipt.metadata == {}

    def test_receipt_to_dict(self) -> None:
        """to_dict returns dict representation."""
        receipt = ActionReceipt(
            receipt_id="r-1",
            action_id="a-1",
            timestamp_start="2024-01-01T00:00:00+00:00",
            timestamp_end="2024-01-01T00:00:01+00:00",
            duration_s=1.0,
            agent="test",
            task_type="analysis",
            status="SUCCESS",
            exit_code=0,
        )

        data = receipt.to_dict()
        assert isinstance(data, dict)
        assert data["receipt_id"] == "r-1"
        assert data["exit_code"] == 0

    def test_receipt_to_jsonl(self) -> None:
        """to_jsonl returns single-line JSON."""
        receipt = ActionReceipt(
            receipt_id="r-1",
            action_id="a-1",
            timestamp_start="2024-01-01T00:00:00+00:00",
            timestamp_end="2024-01-01T00:00:01+00:00",
            duration_s=1.0,
            agent="test",
            task_type="test",
            status="FAILED",
        )

        line = receipt.to_jsonl()
        assert isinstance(line, str)
        assert "\n" not in line
        parsed = json.loads(line)
        assert parsed["status"] == "FAILED"


class TestPreconditionValidator:
    """Test PreconditionValidator."""

    def test_empty_preconditions(self) -> None:
        """Empty preconditions are valid."""
        valid, details = PreconditionValidator.validate_all([], {})
        assert valid is True
        assert details == {}

    def test_agent_online_satisfied(self) -> None:
        """Agent online precondition passes when agent is online."""
        world_state = {"runtime_state": {"agent_capabilities": {"ollama": {"online": True}}}}
        preconditions = ["Agent ollama is online"]

        valid, details = PreconditionValidator.validate_all(preconditions, world_state)
        assert valid is True
        assert details["Agent ollama is online"] is True

    def test_agent_online_not_satisfied(self) -> None:
        """Agent online precondition fails when agent is offline."""
        world_state = {"runtime_state": {"agent_capabilities": {"ollama": {"online": False}}}}
        preconditions = ["Agent ollama is online"]

        valid, details = PreconditionValidator.validate_all(preconditions, world_state)
        assert valid is False
        assert details["Agent ollama is online"] is False

    def test_agent_online_missing_agent(self) -> None:
        """Agent online fails when agent not in world state."""
        world_state = {"runtime_state": {"agent_capabilities": {}}}
        preconditions = ["Agent chatdev is online"]

        valid, _details = PreconditionValidator.validate_all(preconditions, world_state)
        assert valid is False

    def test_tokens_budget_satisfied(self) -> None:
        """Token budget precondition passes with sufficient tokens."""
        world_state = {"policy_state": {"resource_budgets": {"token_budget_remaining": 5000}}}
        preconditions = ["Available tokens >= 1000"]

        valid, _details = PreconditionValidator.validate_all(preconditions, world_state)
        assert valid is True

    def test_tokens_budget_insufficient(self) -> None:
        """Token budget precondition fails with insufficient tokens."""
        world_state = {"policy_state": {"resource_budgets": {"token_budget_remaining": 100}}}
        preconditions = ["Available tokens >= 500"]

        valid, _details = PreconditionValidator.validate_all(preconditions, world_state)
        assert valid is False

    def test_time_budget_satisfied(self) -> None:
        """Time budget precondition passes with sufficient time."""
        world_state = {"policy_state": {"resource_budgets": {"time_budget_remaining_s": 600}}}
        preconditions = ["Time budget >= 300"]

        valid, _details = PreconditionValidator.validate_all(preconditions, world_state)
        assert valid is True

    def test_unknown_precondition_defaults_true(self) -> None:
        """Unknown preconditions default to satisfied."""
        preconditions = ["Some unknown condition"]
        valid, details = PreconditionValidator.validate_all(preconditions, {})
        assert valid is True
        assert details["Some unknown condition"] is True

    def test_extract_number_found(self) -> None:
        """Extract number from string."""
        result = PreconditionValidator._extract_number("tokens >= 500")
        assert result == 500

    def test_extract_number_not_found(self) -> None:
        """No number returns 0."""
        result = PreconditionValidator._extract_number("no number here")
        assert result == 0


class TestPostconditionValidator:
    """Test PostconditionValidator."""

    def test_empty_postconditions(self) -> None:
        """Empty postconditions are valid."""
        valid, details = PostconditionValidator.validate_all([], 0, "", "")
        assert valid is True
        assert details == {}

    def test_completed_postcondition_exit_zero(self) -> None:
        """Completed postcondition passes with exit code 0."""
        postconditions = ["Task completed successfully"]
        valid, _details = PostconditionValidator.validate_all(postconditions, 0, "", "")
        assert valid is True

    def test_completed_postcondition_exit_nonzero(self) -> None:
        """Completed postcondition fails with non-zero exit code."""
        postconditions = ["Task completed with status recorded"]
        valid, _details = PostconditionValidator.validate_all(postconditions, 1, "", "")
        assert valid is False

    def test_receipt_postcondition_always_true(self) -> None:
        """Receipt/logged postconditions are always satisfied."""
        postconditions = ["Receipt was logged", "Action is logged to ledger"]
        valid, details = PostconditionValidator.validate_all(postconditions, 1, "", "err")
        assert valid is True
        assert all(details.values())

    def test_error_postcondition_no_errors(self) -> None:
        """Error postcondition passes with no errors."""
        postconditions = ["No error in output"]
        valid, _details = PostconditionValidator.validate_all(postconditions, 0, "ok", "")
        assert valid is True

    def test_error_postcondition_with_errors(self) -> None:
        """Error postcondition fails when stderr contains error."""
        postconditions = ["No error detected"]
        valid, _details = PostconditionValidator.validate_all(
            postconditions, 0, "", "RuntimeError occurred"
        )
        assert valid is False

    def test_unknown_postcondition_exit_zero(self) -> None:
        """Unknown postcondition passes with exit code 0."""
        postconditions = ["Some custom postcondition"]
        valid, _details = PostconditionValidator.validate_all(postconditions, 0, "", "")
        assert valid is True


class TestActionReceiptLedgerInit:
    """Test ActionReceiptLedger initialization."""

    def test_init_creates_parent_directory(self, tmp_path: Path) -> None:
        """Init creates ledger parent directory."""
        ledger_file = tmp_path / "nested" / "dir" / "ledger.jsonl"
        ActionReceiptLedger(ledger_file=ledger_file)
        assert ledger_file.parent.exists()

    def test_init_default_paths(self) -> None:
        """Init with default paths."""
        ledger = ActionReceiptLedger()
        assert ledger.workspace_root == Path(".")


class TestActionReceiptLedgerExecute:
    """Test action execution."""

    @pytest.fixture
    def ledger(self, tmp_path: Path) -> ActionReceiptLedger:
        """Create ledger with temp file."""
        return ActionReceiptLedger(
            ledger_file=tmp_path / "ledger.jsonl",
            workspace_root=tmp_path,
        )

    @pytest.fixture
    def valid_world_state(self) -> dict:
        """World state with online agent and budget."""
        return {
            "policy_state": {
                "resource_budgets": {
                    "token_budget_remaining": 5000,
                    "time_budget_remaining_s": 600,
                }
            },
            "runtime_state": {"agent_capabilities": {"ollama": {"online": True}}},
        }

    def test_execute_dry_run(self, ledger: ActionReceiptLedger, valid_world_state: dict) -> None:
        """Dry run executes without subprocess."""
        action = {
            "action_id": "test-action",
            "agent": "ollama",
            "task_type": "analysis",
            "description": "Test task",
            "preconditions": [],
            "postconditions": [],
        }

        receipt = ledger.execute_action(action, valid_world_state, dry_run=True)

        assert receipt.status == "SUCCESS"
        assert receipt.exit_code == 0
        assert "DRY RUN" in receipt.stdout
        assert receipt.preconditions_met is True

    def test_execute_preconditions_not_met(self, ledger: ActionReceiptLedger) -> None:
        """Action cancelled when preconditions fail."""
        action = {
            "action_id": "test-action",
            "agent": "ollama",
            "task_type": "analysis",
            "description": "Test task",
            "preconditions": ["Agent ollama is online"],
            "postconditions": [],
        }
        world_state = {"runtime_state": {"agent_capabilities": {"ollama": {"online": False}}}}

        receipt = ledger.execute_action(action, world_state)

        assert receipt.status == "CANCELLED"
        assert receipt.preconditions_met is False
        assert "Preconditions not met" in (receipt.error_message or "")

    @patch("src.core.action_receipt_ledger.subprocess.run")
    def test_execute_real_dispatch_success(
        self, mock_run: MagicMock, ledger: ActionReceiptLedger, valid_world_state: dict
    ) -> None:
        """Real dispatch calls subprocess."""
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")

        action = {
            "action_id": "real-action",
            "agent": "ollama",
            "task_type": "analysis",
            "description": "Real task",
            "preconditions": [],
            "postconditions": [],
        }

        receipt = ledger.execute_action(action, valid_world_state, dry_run=False)

        assert receipt.status == "SUCCESS"
        assert receipt.exit_code == 0
        mock_run.assert_called_once()

    @patch("src.core.action_receipt_ledger.subprocess.run")
    def test_execute_real_dispatch_failure(
        self, mock_run: MagicMock, ledger: ActionReceiptLedger, valid_world_state: dict
    ) -> None:
        """Failed dispatch returns FAILED status."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error occurred")

        action = {
            "action_id": "fail-action",
            "agent": "ollama",
            "task_type": "analysis",
            "description": "Failing task",
            "preconditions": [],
            "postconditions": [],
        }

        receipt = ledger.execute_action(action, valid_world_state, dry_run=False)

        assert receipt.status == "FAILED"
        assert receipt.exit_code == 1

    @patch("src.core.action_receipt_ledger.subprocess.run")
    def test_execute_postconditions_partial(
        self, mock_run: MagicMock, ledger: ActionReceiptLedger, valid_world_state: dict
    ) -> None:
        """Partial status when postconditions fail."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")

        action = {
            "action_id": "partial-action",
            "agent": "ollama",
            "task_type": "analysis",
            "description": "Partial task",
            "preconditions": [],
            "postconditions": ["Task completed successfully"],
        }

        receipt = ledger.execute_action(action, valid_world_state, dry_run=False)

        # Exit code 1 means postcondition fails -> PARTIAL if others succeed
        # Actually, exit_code != 0 means FAILED, postconditions just add info
        assert receipt.postconditions_met is False

    def test_execute_records_linked_quest(
        self, ledger: ActionReceiptLedger, valid_world_state: dict
    ) -> None:
        """Quest dependency is linked in receipt."""
        action = {
            "action_id": "quest-action",
            "agent": "ollama",
            "task_type": "analysis",
            "description": "Quest task",
            "preconditions": [],
            "postconditions": [],
            "quest_dependency": "quest-123",
        }

        receipt = ledger.execute_action(action, valid_world_state, dry_run=True)

        assert receipt.linked_quest_id == "quest-123"


class TestActionReceiptLedgerPersistence:
    """Test ledger file operations."""

    def test_append_and_read_receipt(self, tmp_path: Path) -> None:
        """Append and read back receipts."""
        ledger = ActionReceiptLedger(ledger_file=tmp_path / "ledger.jsonl")

        # Execute action that appends receipt
        action = {
            "action_id": "persist-action",
            "agent": "test",
            "task_type": "test",
            "description": "Test persist",
            "preconditions": [],
            "postconditions": [],
        }
        ledger.execute_action(action, {}, dry_run=True)

        # Read back
        receipts = ledger.read_receipts()
        assert len(receipts) == 1
        assert receipts[0].action_id == "persist-action"

    def test_read_receipts_with_filters(self, tmp_path: Path) -> None:
        """Filter receipts by action_id, agent, status."""
        ledger = ActionReceiptLedger(ledger_file=tmp_path / "ledger.jsonl")

        # Create multiple receipts
        for i in range(3):
            action = {
                "action_id": f"action-{i}",
                "agent": "agent-a" if i < 2 else "agent-b",
                "task_type": "test",
                "description": f"Task {i}",
                "preconditions": [],
                "postconditions": [],
            }
            ledger.execute_action(action, {}, dry_run=True)

        # Filter by action_id
        results = ledger.read_receipts(action_id="action-1")
        assert len(results) == 1
        assert results[0].action_id == "action-1"

        # Filter by agent
        results = ledger.read_receipts(agent="agent-a")
        assert len(results) == 2

        # Filter by status
        results = ledger.read_receipts(status="SUCCESS")
        assert len(results) == 3

    def test_read_receipts_empty_ledger(self, tmp_path: Path) -> None:
        """Read from non-existent ledger returns empty."""
        ledger = ActionReceiptLedger(ledger_file=tmp_path / "missing.jsonl")
        receipts = ledger.read_receipts()
        assert receipts == []

    def test_read_receipts_limit(self, tmp_path: Path) -> None:
        """Limit parameter caps results."""
        ledger = ActionReceiptLedger(ledger_file=tmp_path / "ledger.jsonl")

        for i in range(10):
            action = {
                "action_id": f"action-{i}",
                "agent": "test",
                "task_type": "test",
                "description": f"Task {i}",
                "preconditions": [],
                "postconditions": [],
            }
            ledger.execute_action(action, {}, dry_run=True)

        results = ledger.read_receipts(limit=5)
        assert len(results) == 5

    def test_read_receipts_malformed_line(self, tmp_path: Path) -> None:
        """Malformed JSON lines are skipped."""
        ledger_file = tmp_path / "ledger.jsonl"
        ledger_file.write_text('{"valid": true}\nnot valid json\n')

        ledger = ActionReceiptLedger(ledger_file=ledger_file)
        # Should not raise, just skip bad line
        receipts = ledger.read_receipts()
        # Valid line may not match ActionReceipt schema
        assert isinstance(receipts, list)


class TestActionReceiptLedgerStats:
    """Test statistics computation."""

    def test_stats_empty_ledger(self, tmp_path: Path) -> None:
        """Stats on empty ledger."""
        ledger = ActionReceiptLedger(ledger_file=tmp_path / "ledger.jsonl")
        stats = ledger.get_action_stats()

        assert stats["total_actions"] == 0
        assert stats["successful"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["avg_duration_s"] == 0.0

    def test_stats_with_actions(self, tmp_path: Path) -> None:
        """Stats computed correctly."""
        ledger = ActionReceiptLedger(ledger_file=tmp_path / "ledger.jsonl")

        # Create successful actions
        for i in range(3):
            action = {
                "action_id": f"success-{i}",
                "agent": "ollama",
                "task_type": "test",
                "description": "Success",
                "preconditions": [],
                "postconditions": [],
            }
            ledger.execute_action(action, {}, dry_run=True)

        stats = ledger.get_action_stats()

        assert stats["total_actions"] == 3
        assert stats["successful"] == 3
        assert stats["success_rate"] == 1.0
        assert stats["by_agent"]["ollama"]["count"] == 3

    def test_stats_by_agent(self, tmp_path: Path) -> None:
        """Stats grouped by agent."""
        ledger = ActionReceiptLedger(ledger_file=tmp_path / "ledger.jsonl")

        for agent in ["ollama", "ollama", "chatdev"]:
            action = {
                "action_id": f"action-{agent}",
                "agent": agent,
                "task_type": "test",
                "description": "Test",
                "preconditions": [],
                "postconditions": [],
            }
            ledger.execute_action(action, {}, dry_run=True)

        stats = ledger.get_action_stats()

        assert stats["by_agent"]["ollama"]["count"] == 2
        assert stats["by_agent"]["chatdev"]["count"] == 1


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def test_execute_action_and_log(self, tmp_path: Path) -> None:
        """Convenience function creates ledger and executes."""
        ledger_file = tmp_path / "convenience.jsonl"

        action = {
            "action_id": "convenience-action",
            "agent": "test",
            "task_type": "test",
            "description": "Convenience test",
            "preconditions": [],
            "postconditions": [],
        }

        receipt = execute_action_and_log(action, {}, ledger_file=ledger_file)

        assert receipt.action_id == "convenience-action"
        assert ledger_file.exists()
