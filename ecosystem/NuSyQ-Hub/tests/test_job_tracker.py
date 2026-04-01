"""Tests for src/core/job_tracker.py - Job Tracking System.

Coverage targets:
- Job dataclass
- JobTracker class:
  - create_job() - creates jobs with processing
  - update_job_status() - updates status with dependency resolution
  - _resolve_dependencies() - resolves blocked jobs
  - get_job_queue() - filters and sorts jobs
  - get_job_stats() - returns statistics
  - load_jobs() - loads from JSON files
  - save_jobs() - saves to JSON files
"""

import asyncio
import json
import pytest
from unittest.mock import patch, AsyncMock

from src.core.job_tracker import Job, JobTracker


# Small delay to prevent timestamp-based job ID collisions
async def _delay():
    """Prevent job ID collision by adding delay (Windows needs ~16ms)."""
    await asyncio.sleep(0.02)  # 20ms for Windows timer precision


class TestJobDataclass:
    """Tests for Job dataclass."""

    def test_job_required_fields(self):
        """Create job with required fields."""
        job = Job(
            id="job_001",
            title="Test Job",
            description="Do something",
            status="pending",
            priority=5,
            tags=["test"],
            dependencies=[],
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            metadata={},
        )

        assert job.id == "job_001"
        assert job.title == "Test Job"
        assert job.status == "pending"
        assert job.priority == 5
        assert job.tags == ["test"]
        assert job.dependencies == []
        assert job.estimated_hours is None
        assert job.actual_hours is None
        assert job.assigned_to is None

    def test_job_optional_fields(self):
        """Create job with optional fields."""
        job = Job(
            id="job_002",
            title="Complex Job",
            description="Complex task",
            status="active",
            priority=8,
            tags=["complex", "important"],
            dependencies=["job_001"],
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T12:00:00",
            metadata={"source": "api"},
            estimated_hours=4.5,
            actual_hours=3.0,
            assigned_to="user@example.com",
        )

        assert job.estimated_hours == 4.5
        assert job.actual_hours == 3.0
        assert job.assigned_to == "user@example.com"
        assert job.metadata == {"source": "api"}


class TestJobTrackerInit:
    """Tests for JobTracker initialization."""

    @pytest.mark.asyncio
    async def test_init_creates_directory(self, tmp_path):
        """JobTracker creates data directory if absent."""
        data_path = tmp_path / "job_data"
        assert not data_path.exists()

        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            JobTracker(data_path=data_path)

        assert data_path.exists()

    @pytest.mark.asyncio
    async def test_init_with_existing_directory(self, tmp_path):
        """JobTracker works with existing directory."""
        data_path = tmp_path / "existing"
        data_path.mkdir()

        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            JobTracker(data_path=data_path)

        assert data_path.exists()


class TestJobTrackerCreateJob:
    """Tests for JobTracker.create_job() method."""

    @pytest.mark.asyncio
    async def test_create_job_basic(self, tmp_path):
        """Create basic job."""
        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            tracker = JobTracker(data_path=tmp_path)
            tracker.save_jobs = AsyncMock()

        job_id = await tracker.create_job(
            title="Test Task",
            description="A test task",
        )

        assert job_id.startswith("job_")
        assert job_id in tracker.jobs
        assert tracker.jobs[job_id].title == "Test Task"
        assert tracker.jobs[job_id].status == "pending"
        assert tracker.jobs[job_id].priority == 5  # default

    @pytest.mark.asyncio
    async def test_create_job_with_tags(self, tmp_path):
        """Create job with custom tags."""
        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            tracker = JobTracker(data_path=tmp_path)
            tracker.save_jobs = AsyncMock()

        job_id = await tracker.create_job(
            title="Tagged Task",
            description="A tagged task",
            tags=["urgent", "backend"],
        )

        assert "urgent" in tracker.jobs[job_id].tags
        assert "backend" in tracker.jobs[job_id].tags

    @pytest.mark.asyncio
    async def test_create_job_with_priority(self, tmp_path):
        """Create job with custom priority."""
        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            tracker = JobTracker(data_path=tmp_path)
            tracker.save_jobs = AsyncMock()

        job_id = await tracker.create_job(
            title="High Priority",
            description="Urgent work",
            priority=10,
        )

        assert tracker.jobs[job_id].priority == 10

    @pytest.mark.asyncio
    async def test_create_job_with_dependencies(self, tmp_path):
        """Create job with dependencies."""
        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            tracker = JobTracker(data_path=tmp_path)
            tracker.save_jobs = AsyncMock()

        job_id = await tracker.create_job(
            title="Dependent Task",
            description="Depends on other jobs",
            dependencies=["job_001", "job_002"],
        )

        assert tracker.jobs[job_id].dependencies == ["job_001", "job_002"]

    @pytest.mark.asyncio
    async def test_create_job_with_assignment(self, tmp_path):
        """Create job with assignment and hours."""
        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            tracker = JobTracker(data_path=tmp_path)
            tracker.save_jobs = AsyncMock()

        job_id = await tracker.create_job(
            title="Assigned Task",
            description="Work to do",
            assigned_to="dev@company.com",
            estimated_hours=8.0,
        )

        job = tracker.jobs[job_id]
        assert job.assigned_to == "dev@company.com"
        assert job.estimated_hours == 8.0


class TestJobTrackerUpdateStatus:
    """Tests for JobTracker.update_job_status() method."""

    @pytest.mark.asyncio
    async def test_update_status_basic(self, tmp_path):
        """Update job status."""
        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            tracker = JobTracker(data_path=tmp_path)
            tracker.save_jobs = AsyncMock()

        job_id = await tracker.create_job("Task", "Description")
        assert tracker.jobs[job_id].status == "pending"

        await tracker.update_job_status(job_id, "active")

        assert tracker.jobs[job_id].status == "active"

    @pytest.mark.asyncio
    async def test_update_status_with_hours(self, tmp_path):
        """Update job status with actual hours."""
        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            tracker = JobTracker(data_path=tmp_path)
            tracker.save_jobs = AsyncMock()

        job_id = await tracker.create_job("Task", "Description")
        await tracker.update_job_status(job_id, "completed", actual_hours=3.5)

        assert tracker.jobs[job_id].status == "completed"
        assert tracker.jobs[job_id].actual_hours == 3.5

    @pytest.mark.asyncio
    async def test_update_status_not_found(self, tmp_path):
        """Update status of non-existent job raises error."""
        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            tracker = JobTracker(data_path=tmp_path)
            tracker.save_jobs = AsyncMock()

        with pytest.raises(ValueError) as exc_info:
            await tracker.update_job_status("nonexistent", "active")

        assert "not found" in str(exc_info.value)


class TestJobTrackerDependencyResolution:
    """Tests for JobTracker._resolve_dependencies() method."""

    @pytest.mark.asyncio
    async def test_resolve_unblocks_dependent_jobs(self, tmp_path):
        """Completing a job unblocks dependent jobs."""
        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            tracker = JobTracker(data_path=tmp_path)
            tracker.save_jobs = AsyncMock()

        # Create jobs with dependency - use delay to prevent ID collision
        job1_id = await tracker.create_job("First Task", "Setup")
        await _delay()
        job2_id = await tracker.create_job(
            "Second Task",
            "Depends on first",
            dependencies=[job1_id],
        )

        # Mark job2 as blocked (must be blocked for dependency resolution to work)
        tracker.jobs[job2_id].status = "blocked"

        # Complete job1 - this should trigger dependency resolution
        await tracker.update_job_status(job1_id, "completed")

        # job2 should be unblocked (pending)
        assert tracker.jobs[job2_id].status == "pending"

    @pytest.mark.asyncio
    async def test_resolve_keeps_job_blocked_with_remaining_deps(self, tmp_path):
        """Job stays blocked if other dependencies remain."""
        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            tracker = JobTracker(data_path=tmp_path)
            tracker.save_jobs = AsyncMock()

        # Create jobs with delays to prevent ID collision
        job1_id = await tracker.create_job("First", "Dep 1")
        await _delay()
        job2_id = await tracker.create_job("Second", "Dep 2")
        await _delay()
        job3_id = await tracker.create_job(
            "Third",
            "Depends on both",
            dependencies=[job1_id, job2_id],
        )

        # Mark job3 as blocked
        tracker.jobs[job3_id].status = "blocked"

        # Complete only job1
        await tracker.update_job_status(job1_id, "completed")

        # job3 should remain blocked (job2 not complete)
        assert tracker.jobs[job3_id].status == "blocked"


class TestJobTrackerGetJobQueue:
    """Tests for JobTracker.get_job_queue() method."""

    @pytest.mark.asyncio
    async def test_get_all_jobs(self, tmp_path):
        """Get all jobs without filters."""
        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            tracker = JobTracker(data_path=tmp_path)
            tracker.save_jobs = AsyncMock()

        # Add delays to prevent job ID collisions
        await tracker.create_job("Task 1", "First")
        await _delay()
        await tracker.create_job("Task 2", "Second")
        await _delay()
        await tracker.create_job("Task 3", "Third")

        queue = await tracker.get_job_queue()

        assert len(queue) == 3

    @pytest.mark.asyncio
    async def test_filter_by_status(self, tmp_path):
        """Filter jobs by status."""
        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            tracker = JobTracker(data_path=tmp_path)
            tracker.save_jobs = AsyncMock()

        job1_id = await tracker.create_job("Task 1", "First")
        await _delay()
        await tracker.create_job("Task 2", "Second")
        await tracker.update_job_status(job1_id, "active")

        active_jobs = await tracker.get_job_queue(status="active")
        pending_jobs = await tracker.get_job_queue(status="pending")

        assert len(active_jobs) == 1
        assert active_jobs[0].id == job1_id
        assert len(pending_jobs) == 1

    @pytest.mark.asyncio
    async def test_filter_by_assigned_to(self, tmp_path):
        """Filter jobs by assignee."""
        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            tracker = JobTracker(data_path=tmp_path)
            tracker.save_jobs = AsyncMock()

        await tracker.create_job("Task 1", "First", assigned_to="alice")
        await _delay()
        await tracker.create_job("Task 2", "Second", assigned_to="bob")
        await _delay()
        await tracker.create_job("Task 3", "Third", assigned_to="alice")

        alice_jobs = await tracker.get_job_queue(assigned_to="alice")

        assert len(alice_jobs) == 2
        assert all(j.assigned_to == "alice" for j in alice_jobs)

    @pytest.mark.asyncio
    async def test_sort_by_priority(self, tmp_path):
        """Jobs are sorted by priority (highest first)."""
        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            tracker = JobTracker(data_path=tmp_path)
            tracker.save_jobs = AsyncMock()

        await tracker.create_job("Low", "Low", priority=1)
        await _delay()
        await tracker.create_job("High", "High", priority=10)
        await _delay()
        await tracker.create_job("Medium", "Medium", priority=5)

        queue = await tracker.get_job_queue()

        assert queue[0].title == "High"
        assert queue[1].title == "Medium"
        assert queue[2].title == "Low"


class TestJobTrackerGetStats:
    """Tests for JobTracker.get_job_stats() method."""

    @pytest.mark.asyncio
    async def test_stats_empty(self, tmp_path):
        """Stats for empty tracker."""
        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            tracker = JobTracker(data_path=tmp_path)

        stats = await tracker.get_job_stats()

        assert stats["total"] == 0
        assert stats["by_status"] == {}
        assert stats["by_priority"] == {}

    @pytest.mark.asyncio
    async def test_stats_with_jobs(self, tmp_path):
        """Stats with multiple jobs."""
        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            tracker = JobTracker(data_path=tmp_path)
            tracker.save_jobs = AsyncMock()

        await tracker.create_job("Task 1", "First", priority=5)
        await _delay()
        await tracker.create_job("Task 2", "Second", priority=10)
        await _delay()
        job3_id = await tracker.create_job("Task 3", "Third", priority=5)
        await tracker.update_job_status(job3_id, "completed")

        stats = await tracker.get_job_stats()

        assert stats["total"] == 3
        assert stats["by_status"]["pending"] == 2
        assert stats["by_status"]["completed"] == 1
        assert stats["by_priority"][5] == 2
        assert stats["by_priority"][10] == 1

    @pytest.mark.asyncio
    async def test_stats_completion_rate(self, tmp_path):
        """Stats includes completion rate."""
        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            tracker = JobTracker(data_path=tmp_path)
            tracker.save_jobs = AsyncMock()

        job1_id = await tracker.create_job("Task 1", "First")
        await _delay()
        await tracker.create_job("Task 2", "Second")
        await tracker.update_job_status(job1_id, "completed")

        stats = await tracker.get_job_stats()

        assert stats["completion_rate"] == 50.0  # 1 of 2 completed

    @pytest.mark.asyncio
    async def test_stats_hours_tracking(self, tmp_path):
        """Stats tracks hours."""
        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            tracker = JobTracker(data_path=tmp_path)
            tracker.save_jobs = AsyncMock()

        job1_id = await tracker.create_job("Task 1", "First", estimated_hours=4.0)
        await _delay()
        await tracker.create_job("Task 2", "Second", estimated_hours=6.0)
        await tracker.update_job_status(job1_id, "completed", actual_hours=3.5)

        stats = await tracker.get_job_stats()

        assert stats["total_estimated_hours"] == 10.0
        assert stats["total_actual_hours"] == 3.5


class TestJobTrackerPersistence:
    """Tests for JobTracker.load_jobs() and save_jobs() methods."""

    @pytest.mark.asyncio
    async def test_save_creates_files(self, tmp_path):
        """save_jobs creates JSON files."""
        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            tracker = JobTracker(data_path=tmp_path)

        await tracker.create_job("Task", "Description")
        await tracker.save_jobs()

        active_file = tmp_path / "active_jobs.json"
        assert active_file.exists()

        with open(active_file) as f:
            data = json.load(f)
            assert "jobs" in data
            assert len(data["jobs"]) == 1

    @pytest.mark.asyncio
    async def test_save_separates_completed(self, tmp_path):
        """save_jobs separates active and completed jobs."""
        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            tracker = JobTracker(data_path=tmp_path)

        job1_id = await tracker.create_job("Active", "Active task")
        await _delay()
        job2_id = await tracker.create_job("Done", "Completed task")
        tracker.jobs[job2_id].status = "completed"

        await tracker.save_jobs()

        active_file = tmp_path / "active_jobs.json"
        completed_file = tmp_path / "completed_jobs.json"

        with open(active_file) as f:
            active_data = json.load(f)
            assert len(active_data["jobs"]) == 1
            assert active_data["jobs"][0]["id"] == job1_id

        with open(completed_file) as f:
            completed_data = json.load(f)
            assert len(completed_data["jobs"]) == 1
            assert completed_data["jobs"][0]["id"] == job2_id

    @pytest.mark.asyncio
    async def test_load_restores_jobs(self, tmp_path):
        """load_jobs restores jobs from files."""
        # First create and save
        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            tracker1 = JobTracker(data_path=tmp_path)

        job_id = await tracker1.create_job("Persistent", "Should persist")
        await tracker1.save_jobs()

        # Create new tracker and load
        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            tracker2 = JobTracker(data_path=tmp_path)

        # Manually call load_jobs
        await tracker2.load_jobs()

        assert job_id in tracker2.jobs
        assert tracker2.jobs[job_id].title == "Persistent"

    @pytest.mark.asyncio
    async def test_load_handles_missing_files(self, tmp_path):
        """load_jobs handles missing files gracefully."""
        with patch.object(JobTracker, "load_jobs", new_callable=AsyncMock):
            tracker = JobTracker(data_path=tmp_path)

        # Manually call load - should not raise
        await tracker.load_jobs()

        assert len(tracker.jobs) == 0
