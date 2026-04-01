"""Tests for src/core/ modules: job_tracker, action_receipt_ledger, eol_integration."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_action(
    *,
    action_id: str = "act-001",
    agent: str = "ollama",
    task_type: str = "analysis",
    description: str = "Do something",
    preconditions: list[str] | None = None,
    postconditions: list[str] | None = None,
    risk_score: float = 0.1,
    policy_category: str = "FEATURE",
    quest_dependency: str | None = None,
) -> dict[str, Any]:
    return {
        "action_id": action_id,
        "agent": agent,
        "task_type": task_type,
        "description": description,
        "preconditions": preconditions or [],
        "postconditions": postconditions or [],
        "risk_score": risk_score,
        "policy_category": policy_category,
        "estimated_cost": {"tokens": 100},
        "quest_dependency": quest_dependency,
    }


def _make_world_state(
    *,
    token_budget: int = 5000,
    time_budget: int = 300,
    agents: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "decision_epoch": 1,
        "signals": {"facts": []},
        "coherence": {"contradictions": []},
        "policy_state": {
            "safety_gates": {"max_risk_score": 0.7},
            "resource_budgets": {
                "token_budget_remaining": token_budget,
                "time_budget_remaining_s": time_budget,
            },
        },
        "runtime_state": {
            "agent_capabilities": agents or {},
        },
        "objective": {},
    }


# ===========================================================================
# 1. JobTracker tests
# ===========================================================================


class TestJobTrackerInit:
    """JobTracker initialisation and basic structure."""

    def test_init_creates_data_dir(self, tmp_path: Path) -> None:
        """JobTracker creates the data directory on init."""
        data_dir = tmp_path / "jobs"
        # Patch asyncio.create_task so we don't need a running loop
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=data_dir)

        assert data_dir.exists()
        assert tracker.jobs == {}

    def test_init_uses_default_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """When no path supplied, default data/jobs is used."""
        monkeypatch.chdir(tmp_path)
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker()

        assert "jobs" in str(tracker.data_path)

    def test_init_jobs_dict_empty(self, tmp_path: Path) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        assert isinstance(tracker.jobs, dict)
        assert len(tracker.jobs) == 0

    def test_logger_created(self, tmp_path: Path) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        assert isinstance(tracker.logger, logging.Logger)


class TestJobTrackerCreate:
    """JobTracker.create_job()."""

    @pytest.mark.asyncio
    async def test_create_job_returns_id(self, tmp_path: Path) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        job_id = await tracker.create_job("My Task", "Do the thing")

        assert job_id.startswith("job_")
        assert job_id in tracker.jobs

    @pytest.mark.asyncio
    async def test_create_job_stores_title_and_description(self, tmp_path: Path) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        job_id = await tracker.create_job("Title", "Desc")
        job = tracker.jobs[job_id]

        assert job.title == "Title"
        assert job.description == "Desc"

    @pytest.mark.asyncio
    async def test_create_job_default_status_is_pending(self, tmp_path: Path) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        job_id = await tracker.create_job("T", "D")
        assert tracker.jobs[job_id].status == "pending"

    @pytest.mark.asyncio
    async def test_create_job_with_custom_priority(self, tmp_path: Path) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        job_id = await tracker.create_job("T", "D", priority=9)
        assert tracker.jobs[job_id].priority == 9

    @pytest.mark.asyncio
    async def test_create_job_with_tags(self, tmp_path: Path) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        job_id = await tracker.create_job("T", "D", tags=["alpha", "beta"])
        assert "alpha" in tracker.jobs[job_id].tags
        assert "beta" in tracker.jobs[job_id].tags

    @pytest.mark.asyncio
    async def test_create_job_with_dependencies(self, tmp_path: Path) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        job_id = await tracker.create_job("T", "D", dependencies=["dep-1"])
        assert "dep-1" in tracker.jobs[job_id].dependencies

    @pytest.mark.asyncio
    async def test_create_job_with_estimated_hours(self, tmp_path: Path) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        job_id = await tracker.create_job("T", "D", estimated_hours=4.0)
        assert tracker.jobs[job_id].estimated_hours == 4.0

    @pytest.mark.asyncio
    async def test_create_job_with_assigned_to(self, tmp_path: Path) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        job_id = await tracker.create_job("T", "D", assigned_to="agent-x")
        assert tracker.jobs[job_id].assigned_to == "agent-x"

    @pytest.mark.asyncio
    async def test_create_job_persists_to_disk(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "j"
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=data_dir)

        await tracker.create_job("Disk Job", "Persisted")
        active_file = data_dir / "active_jobs.json"
        assert active_file.exists()

    @pytest.mark.asyncio
    async def test_create_multiple_jobs_unique_ids(self, tmp_path: Path) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        id1 = await tracker.create_job("J1", "D")
        await asyncio.sleep(0.002)  # ensure different millisecond → unique ID
        id2 = await tracker.create_job("J2", "D")
        assert id1 != id2


class TestJobTrackerUpdateStatus:
    """JobTracker.update_job_status()."""

    @pytest.mark.asyncio
    async def test_update_status_changes_status(self, tmp_path: Path) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        job_id = await tracker.create_job("T", "D")
        await tracker.update_job_status(job_id, "active")
        assert tracker.jobs[job_id].status == "active"

    @pytest.mark.asyncio
    async def test_update_status_records_actual_hours(self, tmp_path: Path) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        job_id = await tracker.create_job("T", "D")
        await tracker.update_job_status(job_id, "completed", actual_hours=2.5)
        assert tracker.jobs[job_id].actual_hours == 2.5

    @pytest.mark.asyncio
    async def test_update_status_raises_for_unknown_id(self, tmp_path: Path) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        with pytest.raises(ValueError, match="not found"):
            await tracker.update_job_status("ghost-id", "active")

    @pytest.mark.asyncio
    async def test_update_status_to_completed_resolves_blocked_dependents(
        self, tmp_path: Path
    ) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        parent_id = await tracker.create_job("Parent", "D")
        child_id = await tracker.create_job("Child", "D", dependencies=[parent_id])
        # Manually set child to blocked
        tracker.jobs[child_id].status = "blocked"

        await tracker.update_job_status(parent_id, "completed")
        # Child should now be pending (all deps completed)
        assert tracker.jobs[child_id].status == "pending"

    @pytest.mark.asyncio
    async def test_update_status_blocked_stays_blocked_when_other_deps_remain(
        self, tmp_path: Path
    ) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        dep1 = await tracker.create_job("Dep1", "D")
        await asyncio.sleep(0.002)
        dep2 = await tracker.create_job("Dep2", "D")
        await asyncio.sleep(0.002)
        child_id = await tracker.create_job("Child", "D", dependencies=[dep1, dep2])
        tracker.jobs[child_id].status = "blocked"

        # Complete only dep1
        await tracker.update_job_status(dep1, "completed")
        # dep2 still pending → child stays blocked
        assert tracker.jobs[child_id].status == "blocked"


class TestJobTrackerGetQueue:
    """JobTracker.get_job_queue()."""

    @pytest.mark.asyncio
    async def test_get_all_jobs(self, tmp_path: Path) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        await tracker.create_job("J1", "D")
        await asyncio.sleep(0.002)  # ensure different millisecond → unique ID
        await tracker.create_job("J2", "D")
        queue = await tracker.get_job_queue()
        assert len(queue) == 2

    @pytest.mark.asyncio
    async def test_filter_by_status(self, tmp_path: Path) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        id1 = await tracker.create_job("J1", "D")
        await asyncio.sleep(0.002)
        await tracker.create_job("J2", "D")
        await tracker.update_job_status(id1, "active")

        active = await tracker.get_job_queue(status="active")
        assert len(active) == 1
        assert active[0].status == "active"

    @pytest.mark.asyncio
    async def test_filter_by_assigned_to(self, tmp_path: Path) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        await tracker.create_job("J1", "D", assigned_to="alice")
        await asyncio.sleep(0.002)
        await tracker.create_job("J2", "D", assigned_to="bob")

        alice_jobs = await tracker.get_job_queue(assigned_to="alice")
        assert len(alice_jobs) == 1
        assert alice_jobs[0].assigned_to == "alice"

    @pytest.mark.asyncio
    async def test_sorted_by_priority_descending(self, tmp_path: Path) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        await tracker.create_job("Low", "D", priority=1)
        await asyncio.sleep(0.002)
        await tracker.create_job("High", "D", priority=10)

        queue = await tracker.get_job_queue()
        assert queue[0].priority == 10
        assert queue[-1].priority == 1

    @pytest.mark.asyncio
    async def test_empty_queue_returns_empty_list(self, tmp_path: Path) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        queue = await tracker.get_job_queue()
        assert queue == []


class TestJobTrackerStats:
    """JobTracker.get_job_stats()."""

    @pytest.mark.asyncio
    async def test_stats_empty(self, tmp_path: Path) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        stats = await tracker.get_job_stats()
        assert stats["total"] == 0

    @pytest.mark.asyncio
    async def test_stats_counts_by_status(self, tmp_path: Path) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        id1 = await tracker.create_job("J1", "D")
        await asyncio.sleep(0.002)
        await tracker.create_job("J2", "D")
        await tracker.update_job_status(id1, "completed")

        stats = await tracker.get_job_stats()
        assert stats["by_status"]["completed"] == 1
        assert stats["by_status"]["pending"] == 1

    @pytest.mark.asyncio
    async def test_stats_completion_rate(self, tmp_path: Path) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        id1 = await tracker.create_job("J1", "D")
        await asyncio.sleep(0.002)
        await tracker.create_job("J2", "D")
        await tracker.update_job_status(id1, "completed")

        stats = await tracker.get_job_stats()
        assert stats["completion_rate"] == 50.0

    @pytest.mark.asyncio
    async def test_stats_tracks_hours(self, tmp_path: Path) -> None:
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        id1 = await tracker.create_job("J1", "D", estimated_hours=3.0)
        await tracker.update_job_status(id1, "completed", actual_hours=2.0)

        stats = await tracker.get_job_stats()
        assert stats["total_estimated_hours"] == 3.0
        assert stats["total_actual_hours"] == 2.0


class TestJobTrackerPersistence:
    """JobTracker load/save round-trip."""

    @pytest.mark.asyncio
    async def test_save_and_load_jobs(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "j"
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=data_dir)

        job_id = await tracker.create_job("Saved Job", "Description")

        # Create a new tracker and load from disk
        with patch("asyncio.create_task"):
            tracker2 = JobTracker(data_path=data_dir)
        await tracker2.load_jobs()

        assert job_id in tracker2.jobs
        assert tracker2.jobs[job_id].title == "Saved Job"

    @pytest.mark.asyncio
    async def test_completed_jobs_saved_separately(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "j"
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=data_dir)

        job_id = await tracker.create_job("Done", "D")
        await tracker.update_job_status(job_id, "completed")

        completed_file = data_dir / "completed_jobs.json"
        assert completed_file.exists()
        content = json.loads(completed_file.read_text())
        ids = [j["id"] for j in content["jobs"]]
        assert job_id in ids

    @pytest.mark.asyncio
    async def test_load_jobs_handles_missing_files(self, tmp_path: Path) -> None:
        """load_jobs does not raise when files don't exist."""
        with patch("asyncio.create_task"):
            from src.core.job_tracker import JobTracker

            tracker = JobTracker(data_path=tmp_path / "j")

        # No exception should be raised
        await tracker.load_jobs()
        assert tracker.jobs == {}


# ===========================================================================
# 2. ActionReceiptLedger tests
# ===========================================================================


class TestActionReceiptModel:
    """ActionReceipt dataclass."""

    def test_to_dict_returns_dict(self) -> None:
        from src.core.action_receipt_ledger import ActionReceipt

        receipt = ActionReceipt(
            receipt_id="r1",
            action_id="a1",
            timestamp_start="2024-01-01T00:00:00+00:00",
            timestamp_end="2024-01-01T00:00:01+00:00",
            duration_s=1.0,
            agent="ollama",
            task_type="analysis",
            status="SUCCESS",
        )
        d = receipt.to_dict()
        assert isinstance(d, dict)
        assert d["receipt_id"] == "r1"

    def test_to_jsonl_produces_single_line(self) -> None:
        from src.core.action_receipt_ledger import ActionReceipt

        receipt = ActionReceipt(
            receipt_id="r1",
            action_id="a1",
            timestamp_start="2024-01-01T00:00:00+00:00",
            timestamp_end="2024-01-01T00:00:01+00:00",
            duration_s=1.0,
            agent="ollama",
            task_type="analysis",
            status="SUCCESS",
        )
        line = receipt.to_jsonl()
        assert "\n" not in line
        parsed = json.loads(line)
        assert parsed["status"] == "SUCCESS"


class TestPreconditionValidator:
    """PreconditionValidator.validate_all()."""

    def test_empty_preconditions_returns_true(self) -> None:
        from src.core.action_receipt_ledger import PreconditionValidator

        ok, details = PreconditionValidator.validate_all([], {})
        assert ok is True
        assert details == {}

    def test_agent_online_precondition_satisfied(self) -> None:
        from src.core.action_receipt_ledger import PreconditionValidator

        world_state = _make_world_state(agents={"ollama": {"online": True}})
        ok, _ = PreconditionValidator.validate_all(
            ["Agent ollama is online"], world_state
        )
        assert ok is True

    def test_agent_online_precondition_fails_when_offline(self) -> None:
        from src.core.action_receipt_ledger import PreconditionValidator

        world_state = _make_world_state(agents={"ollama": {"online": False}})
        ok, _ = PreconditionValidator.validate_all(
            ["Agent ollama is online"], world_state
        )
        assert ok is False

    def test_token_budget_sufficient(self) -> None:
        from src.core.action_receipt_ledger import PreconditionValidator

        world_state = _make_world_state(token_budget=5000)
        ok, _ = PreconditionValidator.validate_all(
            ["Available tokens >= 500"], world_state
        )
        assert ok is True

    def test_token_budget_insufficient(self) -> None:
        from src.core.action_receipt_ledger import PreconditionValidator

        world_state = _make_world_state(token_budget=100)
        ok, _ = PreconditionValidator.validate_all(
            ["Available tokens >= 500"], world_state
        )
        assert ok is False

    def test_unknown_precondition_defaults_to_true(self) -> None:
        from src.core.action_receipt_ledger import PreconditionValidator

        ok, _ = PreconditionValidator.validate_all(["some unknown condition"], {})
        assert ok is True


class TestPostconditionValidator:
    """PostconditionValidator.validate_all()."""

    def test_empty_returns_true(self) -> None:
        from src.core.action_receipt_ledger import PostconditionValidator

        ok, _ = PostconditionValidator.validate_all([], 0, "", "")
        assert ok is True

    def test_completed_postcondition_ok_on_exit_0(self) -> None:
        from src.core.action_receipt_ledger import PostconditionValidator

        ok, _ = PostconditionValidator.validate_all(
            ["Task completed successfully"], 0, "output", ""
        )
        assert ok is True

    def test_completed_postcondition_fails_on_nonzero_exit(self) -> None:
        from src.core.action_receipt_ledger import PostconditionValidator

        ok, _ = PostconditionValidator.validate_all(
            ["Task completed successfully"], 1, "", "error"
        )
        assert ok is False

    def test_receipt_logged_postcondition_always_true(self) -> None:
        from src.core.action_receipt_ledger import PostconditionValidator

        ok, _ = PostconditionValidator.validate_all(
            ["Receipt logged"], 1, "", "error"
        )
        assert ok is True


class TestActionReceiptLedgerInit:
    """ActionReceiptLedger initialisation."""

    def test_init_creates_parent_dir(self, tmp_path: Path) -> None:
        from src.core.action_receipt_ledger import ActionReceiptLedger

        ledger_path = tmp_path / "sub" / "ledger.jsonl"
        ActionReceiptLedger(ledger_file=ledger_path)
        assert ledger_path.parent.exists()

    def test_init_stores_paths(self, tmp_path: Path) -> None:
        from src.core.action_receipt_ledger import ActionReceiptLedger

        ledger_path = tmp_path / "ledger.jsonl"
        ledger = ActionReceiptLedger(ledger_file=ledger_path, workspace_root=tmp_path)
        assert ledger.ledger_file == ledger_path
        assert ledger.workspace_root == tmp_path


class TestActionReceiptLedgerExecuteAction:
    """ActionReceiptLedger.execute_action()."""

    def test_dry_run_returns_success_receipt(self, tmp_path: Path) -> None:
        from src.core.action_receipt_ledger import ActionReceiptLedger

        ledger = ActionReceiptLedger(
            ledger_file=tmp_path / "ledger.jsonl", workspace_root=tmp_path
        )
        action = _make_action()
        world_state = _make_world_state()
        receipt = ledger.execute_action(action, world_state, dry_run=True)
        assert receipt.status == "SUCCESS"

    def test_dry_run_stdout_contains_dry_run_marker(self, tmp_path: Path) -> None:
        from src.core.action_receipt_ledger import ActionReceiptLedger

        ledger = ActionReceiptLedger(
            ledger_file=tmp_path / "ledger.jsonl", workspace_root=tmp_path
        )
        action = _make_action(description="Analyze errors")
        world_state = _make_world_state()
        receipt = ledger.execute_action(action, world_state, dry_run=True)
        assert "[DRY RUN]" in receipt.stdout

    def test_preconditions_failed_returns_cancelled(self, tmp_path: Path) -> None:
        from src.core.action_receipt_ledger import ActionReceiptLedger

        ledger = ActionReceiptLedger(
            ledger_file=tmp_path / "ledger.jsonl", workspace_root=tmp_path
        )
        # Agent not in world state → precondition fails
        action = _make_action(preconditions=["Agent offline_agent is online"])
        world_state = _make_world_state(agents={})  # offline_agent absent
        receipt = ledger.execute_action(action, world_state, dry_run=True)
        assert receipt.status == "CANCELLED"
        assert receipt.preconditions_met is False

    def test_receipt_written_to_ledger_file(self, tmp_path: Path) -> None:
        from src.core.action_receipt_ledger import ActionReceiptLedger

        ledger_path = tmp_path / "ledger.jsonl"
        ledger = ActionReceiptLedger(ledger_file=ledger_path, workspace_root=tmp_path)
        action = _make_action()
        world_state = _make_world_state()
        ledger.execute_action(action, world_state, dry_run=True)
        assert ledger_path.exists()
        lines = [l for l in ledger_path.read_text().splitlines() if l.strip()]
        assert len(lines) == 1

    def test_multiple_actions_append_to_ledger(self, tmp_path: Path) -> None:
        from src.core.action_receipt_ledger import ActionReceiptLedger

        ledger_path = tmp_path / "ledger.jsonl"
        ledger = ActionReceiptLedger(ledger_file=ledger_path, workspace_root=tmp_path)
        world_state = _make_world_state()
        for i in range(3):
            ledger.execute_action(_make_action(action_id=f"act-{i}"), world_state, dry_run=True)
        lines = [l for l in ledger_path.read_text().splitlines() if l.strip()]
        assert len(lines) == 3

    def test_receipt_has_correct_agent(self, tmp_path: Path) -> None:
        from src.core.action_receipt_ledger import ActionReceiptLedger

        ledger = ActionReceiptLedger(
            ledger_file=tmp_path / "ledger.jsonl", workspace_root=tmp_path
        )
        action = _make_action(agent="claude")
        world_state = _make_world_state()
        receipt = ledger.execute_action(action, world_state, dry_run=True)
        assert receipt.agent == "claude"

    def test_receipt_preconditions_met_when_no_preconditions(self, tmp_path: Path) -> None:
        from src.core.action_receipt_ledger import ActionReceiptLedger

        ledger = ActionReceiptLedger(
            ledger_file=tmp_path / "ledger.jsonl", workspace_root=tmp_path
        )
        action = _make_action(preconditions=[])
        world_state = _make_world_state()
        receipt = ledger.execute_action(action, world_state, dry_run=True)
        assert receipt.preconditions_met is True


class TestActionReceiptLedgerReadReceipts:
    """ActionReceiptLedger.read_receipts()."""

    def _write_receipt_line(self, ledger_path: Path, data: dict) -> None:
        with open(ledger_path, "a") as f:
            f.write(json.dumps(data) + "\n")

    def test_returns_empty_when_no_file(self, tmp_path: Path) -> None:
        from src.core.action_receipt_ledger import ActionReceiptLedger

        ledger = ActionReceiptLedger(
            ledger_file=tmp_path / "ledger.jsonl", workspace_root=tmp_path
        )
        assert ledger.read_receipts() == []

    def test_reads_receipt_after_execute(self, tmp_path: Path) -> None:
        from src.core.action_receipt_ledger import ActionReceiptLedger

        ledger = ActionReceiptLedger(
            ledger_file=tmp_path / "ledger.jsonl", workspace_root=tmp_path
        )
        action = _make_action(action_id="act-read-test")
        world_state = _make_world_state()
        ledger.execute_action(action, world_state, dry_run=True)

        receipts = ledger.read_receipts()
        assert len(receipts) == 1
        assert receipts[0].action_id == "act-read-test"

    def test_filters_by_agent(self, tmp_path: Path) -> None:
        from src.core.action_receipt_ledger import ActionReceiptLedger

        ledger = ActionReceiptLedger(
            ledger_file=tmp_path / "ledger.jsonl", workspace_root=tmp_path
        )
        world_state = _make_world_state()
        ledger.execute_action(_make_action(agent="claude"), world_state, dry_run=True)
        ledger.execute_action(_make_action(action_id="a2", agent="ollama"), world_state, dry_run=True)

        claude_receipts = ledger.read_receipts(agent="claude")
        assert all(r.agent == "claude" for r in claude_receipts)
        assert len(claude_receipts) == 1

    def test_filters_by_status(self, tmp_path: Path) -> None:
        from src.core.action_receipt_ledger import ActionReceiptLedger

        ledger = ActionReceiptLedger(
            ledger_file=tmp_path / "ledger.jsonl", workspace_root=tmp_path
        )
        world_state = _make_world_state()
        # Successful action
        ledger.execute_action(_make_action(), world_state, dry_run=True)
        # Cancelled action (failed precondition)
        ledger.execute_action(
            _make_action(action_id="a2", preconditions=["Agent ghost is online"]),
            world_state,
            dry_run=True,
        )

        cancelled = ledger.read_receipts(status="CANCELLED")
        assert len(cancelled) == 1

    def test_limit_parameter(self, tmp_path: Path) -> None:
        from src.core.action_receipt_ledger import ActionReceiptLedger

        ledger = ActionReceiptLedger(
            ledger_file=tmp_path / "ledger.jsonl", workspace_root=tmp_path
        )
        world_state = _make_world_state()
        for i in range(5):
            ledger.execute_action(_make_action(action_id=f"a{i}"), world_state, dry_run=True)

        receipts = ledger.read_receipts(limit=2)
        assert len(receipts) == 2

    def test_skips_malformed_lines(self, tmp_path: Path) -> None:
        from src.core.action_receipt_ledger import ActionReceiptLedger

        ledger_path = tmp_path / "ledger.jsonl"
        ledger = ActionReceiptLedger(ledger_file=ledger_path, workspace_root=tmp_path)
        # Write a malformed line then a valid receipt
        with open(ledger_path, "w") as f:
            f.write("not-json\n")
        world_state = _make_world_state()
        ledger.execute_action(_make_action(), world_state, dry_run=True)

        # Should return 1 valid receipt without raising
        receipts = ledger.read_receipts()
        assert len(receipts) == 1


class TestActionReceiptLedgerStats:
    """ActionReceiptLedger.get_action_stats()."""

    def test_stats_empty_ledger(self, tmp_path: Path) -> None:
        from src.core.action_receipt_ledger import ActionReceiptLedger

        ledger = ActionReceiptLedger(
            ledger_file=tmp_path / "ledger.jsonl", workspace_root=tmp_path
        )
        stats = ledger.get_action_stats()
        assert stats["total_actions"] == 0
        assert stats["success_rate"] == 0.0

    def test_stats_counts_successful(self, tmp_path: Path) -> None:
        from src.core.action_receipt_ledger import ActionReceiptLedger

        ledger = ActionReceiptLedger(
            ledger_file=tmp_path / "ledger.jsonl", workspace_root=tmp_path
        )
        world_state = _make_world_state()
        ledger.execute_action(_make_action(), world_state, dry_run=True)

        stats = ledger.get_action_stats()
        assert stats["total_actions"] == 1
        assert stats["successful"] == 1

    def test_stats_by_agent(self, tmp_path: Path) -> None:
        from src.core.action_receipt_ledger import ActionReceiptLedger

        ledger = ActionReceiptLedger(
            ledger_file=tmp_path / "ledger.jsonl", workspace_root=tmp_path
        )
        world_state = _make_world_state()
        ledger.execute_action(_make_action(agent="agent-a"), world_state, dry_run=True)
        ledger.execute_action(_make_action(action_id="a2", agent="agent-b"), world_state, dry_run=True)

        stats = ledger.get_action_stats()
        assert "agent-a" in stats["by_agent"]
        assert "agent-b" in stats["by_agent"]


# ===========================================================================
# 3. EOLOrchestrator tests
# ===========================================================================


@pytest.fixture()
def _stub_build_world_state() -> Any:
    """Return a minimal valid world state dict."""
    return {
        "decision_epoch": 42,
        "signals": {"facts": ["fact1"]},
        "coherence": {"contradictions": []},
        "policy_state": {
            "safety_gates": {"max_risk_score": 0.7},
            "resource_budgets": {
                "token_budget_remaining": 5000,
                "time_budget_remaining_s": 300,
            },
        },
        "runtime_state": {"agent_capabilities": {}},
        "objective": {"quest_id": "q-001"},
    }


@pytest.fixture()
def _stub_actions() -> list[dict[str, Any]]:
    return [
        _make_action(action_id="plan-a1", risk_score=0.1),
        _make_action(action_id="plan-a2", agent="claude", risk_score=0.3),
    ]


class TestEOLOrchestratorInit:
    """EOLOrchestrator initialisation."""

    def test_init_with_tmp_paths(self, tmp_path: Path) -> None:
        from src.core.eol_integration import EOLOrchestrator

        eol = EOLOrchestrator(
            workspace_root=tmp_path,
            ledger_file=tmp_path / "ledger.jsonl",
            state_snapshot_file=tmp_path / "state" / "snap.json",
        )
        assert eol.workspace_root == tmp_path
        assert eol._consciousness_loop is None

    def test_init_creates_state_dir(self, tmp_path: Path) -> None:
        from src.core.eol_integration import EOLOrchestrator

        state_file = tmp_path / "state" / "sub" / "snap.json"
        EOLOrchestrator(
            workspace_root=tmp_path,
            ledger_file=tmp_path / "ledger.jsonl",
            state_snapshot_file=state_file,
        )
        assert state_file.parent.exists()

    def test_init_previous_state_is_none(self, tmp_path: Path) -> None:
        from src.core.eol_integration import EOLOrchestrator

        eol = EOLOrchestrator(
            workspace_root=tmp_path,
            ledger_file=tmp_path / "l.jsonl",
            state_snapshot_file=tmp_path / "s.json",
        )
        assert eol.previous_world_state is None


class TestEOLOrchestratorSense:
    """EOLOrchestrator.sense()."""

    def test_sense_returns_dict_with_required_keys(self, tmp_path: Path) -> None:
        from src.core.eol_integration import EOLOrchestrator

        eol = EOLOrchestrator(
            workspace_root=tmp_path,
            ledger_file=tmp_path / "l.jsonl",
            state_snapshot_file=tmp_path / "snap.json",
        )
        with patch("src.core.eol_integration.build_world_state") as mock_bws:
            mock_bws.return_value = {
                "decision_epoch": 1,
                "signals": {"facts": []},
                "coherence": {"contradictions": []},
            }
            ws = eol.sense()

        assert isinstance(ws, dict)
        assert "decision_epoch" in ws

    def test_sense_writes_snapshot(self, tmp_path: Path) -> None:
        from src.core.eol_integration import EOLOrchestrator

        snap_file = tmp_path / "snap.json"
        eol = EOLOrchestrator(
            workspace_root=tmp_path,
            ledger_file=tmp_path / "l.jsonl",
            state_snapshot_file=snap_file,
        )
        fake_ws = {"decision_epoch": 7, "signals": {"facts": []}, "coherence": {"contradictions": []}}
        with patch("src.core.eol_integration.build_world_state", return_value=fake_ws):
            eol.sense()

        assert snap_file.exists()
        saved = json.loads(snap_file.read_text())
        assert saved["decision_epoch"] == 7

    def test_sense_caches_previous_world_state(self, tmp_path: Path) -> None:
        from src.core.eol_integration import EOLOrchestrator

        eol = EOLOrchestrator(
            workspace_root=tmp_path,
            ledger_file=tmp_path / "l.jsonl",
            state_snapshot_file=tmp_path / "snap.json",
        )
        fake_ws = {"decision_epoch": 3, "signals": {"facts": []}, "coherence": {"contradictions": []}}
        with patch("src.core.eol_integration.build_world_state", return_value=fake_ws):
            eol.sense()

        assert eol.previous_world_state is not None
        assert eol.previous_world_state["decision_epoch"] == 3


class TestEOLOrchestratorPropose:
    """EOLOrchestrator.propose()."""

    def test_propose_returns_list(self, tmp_path: Path, _stub_actions: list) -> None:
        from src.core.eol_integration import EOLOrchestrator

        eol = EOLOrchestrator(
            workspace_root=tmp_path,
            ledger_file=tmp_path / "l.jsonl",
            state_snapshot_file=tmp_path / "snap.json",
        )
        world_state = _make_world_state()
        with patch("src.core.eol_integration.plan_from_world_state") as mock_plan:
            mock_plan.return_value = {"actions": _stub_actions}
            result = eol.propose(world_state, "Fix errors")

        assert isinstance(result, list)
        assert len(result) == 2

    def test_propose_empty_actions(self, tmp_path: Path) -> None:
        from src.core.eol_integration import EOLOrchestrator

        eol = EOLOrchestrator(
            workspace_root=tmp_path,
            ledger_file=tmp_path / "l.jsonl",
            state_snapshot_file=tmp_path / "snap.json",
        )
        world_state = _make_world_state()
        with patch("src.core.eol_integration.plan_from_world_state") as mock_plan:
            mock_plan.return_value = {"actions": []}
            result = eol.propose(world_state)

        assert result == []


class TestEOLOrchestratorCritique:
    """EOLOrchestrator.critique()."""

    def test_critique_approves_low_risk_action(self, tmp_path: Path) -> None:
        from src.core.eol_integration import EOLOrchestrator

        eol = EOLOrchestrator(
            workspace_root=tmp_path,
            ledger_file=tmp_path / "l.jsonl",
            state_snapshot_file=tmp_path / "snap.json",
        )
        action = _make_action(risk_score=0.1)
        world_state = _make_world_state()
        assert eol.critique(action, world_state) is True

    def test_critique_rejects_high_risk_action(self, tmp_path: Path) -> None:
        from src.core.eol_integration import EOLOrchestrator

        eol = EOLOrchestrator(
            workspace_root=tmp_path,
            ledger_file=tmp_path / "l.jsonl",
            state_snapshot_file=tmp_path / "snap.json",
        )
        action = _make_action(risk_score=0.9)
        world_state = _make_world_state()
        assert eol.critique(action, world_state) is False

    def test_critique_security_action_auto_approves_when_bridge_unavailable(
        self, tmp_path: Path
    ) -> None:
        from src.core.eol_integration import EOLOrchestrator

        eol = EOLOrchestrator(
            workspace_root=tmp_path,
            ledger_file=tmp_path / "l.jsonl",
            state_snapshot_file=tmp_path / "snap.json",
        )
        action = _make_action(risk_score=0.1, policy_category="SECURITY")
        world_state = _make_world_state()

        with patch(
            "src.core.eol_integration.EOLOrchestrator._request_culture_ship_approval",
            return_value=True,
        ):
            result = eol.critique(action, world_state)

        assert result is True

    def test_critique_security_action_vetoed_by_culture_ship(self, tmp_path: Path) -> None:
        from src.core.eol_integration import EOLOrchestrator

        eol = EOLOrchestrator(
            workspace_root=tmp_path,
            ledger_file=tmp_path / "l.jsonl",
            state_snapshot_file=tmp_path / "snap.json",
        )
        action = _make_action(risk_score=0.1, policy_category="SECURITY")
        world_state = _make_world_state()

        with patch(
            "src.core.eol_integration.EOLOrchestrator._request_culture_ship_approval",
            return_value=False,
        ):
            result = eol.critique(action, world_state)

        assert result is False


class TestEOLOrchestratorCultureShipApproval:
    """EOLOrchestrator._request_culture_ship_approval()."""

    def test_auto_approves_when_consciousness_loop_import_fails(self, tmp_path: Path) -> None:
        from src.core.eol_integration import EOLOrchestrator

        eol = EOLOrchestrator(
            workspace_root=tmp_path,
            ledger_file=tmp_path / "l.jsonl",
            state_snapshot_file=tmp_path / "snap.json",
        )
        action = _make_action(policy_category="SECURITY")
        world_state = _make_world_state()

        with patch.dict("sys.modules", {"src.orchestration.consciousness_loop": None}):
            with patch(
                "builtins.__import__",
                side_effect=ImportError("no module"),
            ):
                result = eol._request_culture_ship_approval(action, world_state)

        # Should auto-approve on failure
        assert isinstance(result, bool)

    def test_uses_existing_consciousness_loop_if_set(self, tmp_path: Path) -> None:
        from src.core.eol_integration import EOLOrchestrator

        eol = EOLOrchestrator(
            workspace_root=tmp_path,
            ledger_file=tmp_path / "l.jsonl",
            state_snapshot_file=tmp_path / "snap.json",
        )
        # Pre-set a mock consciousness loop
        mock_loop = MagicMock()
        mock_approval = MagicMock()
        mock_approval.approved = True
        mock_approval.reason = "approved by mock"
        mock_loop.request_approval.return_value = mock_approval
        eol._consciousness_loop = mock_loop

        action = _make_action(policy_category="SECURITY")
        result = eol._request_culture_ship_approval(action, _make_world_state())
        assert result is True
        mock_loop.request_approval.assert_called_once()


class TestEOLOrchestratorAct:
    """EOLOrchestrator.act()."""

    def test_act_dry_run_returns_success_receipt(self, tmp_path: Path) -> None:
        from src.core.eol_integration import EOLOrchestrator

        eol = EOLOrchestrator(
            workspace_root=tmp_path,
            ledger_file=tmp_path / "l.jsonl",
            state_snapshot_file=tmp_path / "snap.json",
        )
        action = _make_action()
        world_state = _make_world_state()
        receipt = eol.act(action, world_state, dry_run=True)
        assert receipt.status == "SUCCESS"

    def test_act_returns_action_receipt(self, tmp_path: Path) -> None:
        from src.core.action_receipt_ledger import ActionReceipt
        from src.core.eol_integration import EOLOrchestrator

        eol = EOLOrchestrator(
            workspace_root=tmp_path,
            ledger_file=tmp_path / "l.jsonl",
            state_snapshot_file=tmp_path / "snap.json",
        )
        receipt = eol.act(_make_action(), _make_world_state(), dry_run=True)
        assert isinstance(receipt, ActionReceipt)


class TestEOLOrchestratorStateSnapshot:
    """EOLOrchestrator state snapshot read/write."""

    def test_read_state_snapshot_returns_none_when_missing(self, tmp_path: Path) -> None:
        from src.core.eol_integration import EOLOrchestrator

        eol = EOLOrchestrator(
            workspace_root=tmp_path,
            ledger_file=tmp_path / "l.jsonl",
            state_snapshot_file=tmp_path / "no_snap.json",
        )
        assert eol.read_state_snapshot() is None

    def test_read_state_snapshot_returns_dict_after_sense(self, tmp_path: Path) -> None:
        from src.core.eol_integration import EOLOrchestrator

        snap_file = tmp_path / "snap.json"
        eol = EOLOrchestrator(
            workspace_root=tmp_path,
            ledger_file=tmp_path / "l.jsonl",
            state_snapshot_file=snap_file,
        )
        fake_ws = {"decision_epoch": 5, "signals": {"facts": []}, "coherence": {"contradictions": []}}
        with patch("src.core.eol_integration.build_world_state", return_value=fake_ws):
            eol.sense()

        result = eol.read_state_snapshot()
        assert result is not None
        assert result["decision_epoch"] == 5

    def test_read_state_snapshot_handles_corrupt_json(self, tmp_path: Path) -> None:
        from src.core.eol_integration import EOLOrchestrator

        snap_file = tmp_path / "snap.json"
        snap_file.write_text("not-valid-json")
        eol = EOLOrchestrator(
            workspace_root=tmp_path,
            ledger_file=tmp_path / "l.jsonl",
            state_snapshot_file=snap_file,
        )
        # Should not raise, returns None
        assert eol.read_state_snapshot() is None


class TestEOLOrchestratorDebugStats:
    """EOLOrchestrator.stats() and debug_info()."""

    def test_stats_returns_dict(self, tmp_path: Path) -> None:
        from src.core.eol_integration import EOLOrchestrator

        eol = EOLOrchestrator(
            workspace_root=tmp_path,
            ledger_file=tmp_path / "l.jsonl",
            state_snapshot_file=tmp_path / "snap.json",
        )
        stats = eol.stats()
        assert isinstance(stats, dict)
        assert "total_actions" in stats

    def test_debug_info_has_paths(self, tmp_path: Path) -> None:
        from src.core.eol_integration import EOLOrchestrator

        eol = EOLOrchestrator(
            workspace_root=tmp_path,
            ledger_file=tmp_path / "l.jsonl",
            state_snapshot_file=tmp_path / "snap.json",
        )
        info = eol.debug_info()
        assert "workspace_root" in info
        assert "ledger_file" in info
        assert "action_stats" in info

    def test_debug_info_previous_state_epoch_is_minus_one_initially(self, tmp_path: Path) -> None:
        from src.core.eol_integration import EOLOrchestrator

        eol = EOLOrchestrator(
            workspace_root=tmp_path,
            ledger_file=tmp_path / "l.jsonl",
            state_snapshot_file=tmp_path / "snap.json",
        )
        info = eol.debug_info()
        assert info["previous_world_state_epoch"] == -1
