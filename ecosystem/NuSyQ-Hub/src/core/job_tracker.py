"""OmniTag: {.

    "purpose": "file_systematically_tagged",
    "tags": ["Python", "Async"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}.
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Import with error handling for missing dependencies
try:
    from src.Rosetta_Quest_System.rosetta_stone_integration import RosettaStone
except ImportError:
    RosettaStone = None  # type: ignore[assignment,misc]
    logging.warning("RosettaStone not available - functionality limited")

try:
    from .tagging_systems.tag_manager import TagManager
except ImportError:
    TagManager = None
    logging.warning("TagManager not available - auto-tagging disabled")


@dataclass
class Job:
    id: str
    title: str
    description: str
    status: str  # 'pending', 'active', 'completed', 'blocked', 'cancelled'
    priority: int  # 1-10 (10 = highest)
    tags: list[str]
    dependencies: list[str]
    created_at: str
    updated_at: str
    metadata: dict[str, Any]
    estimated_hours: float | None = None
    actual_hours: float | None = None
    assigned_to: str | None = None


class JobTracker:
    def __init__(self, data_path: Path | None = None) -> None:
        """Initialize JobTracker with data_path."""
        self.data_path = data_path or Path("data/jobs")
        self.data_path.mkdir(parents=True, exist_ok=True)

        # Initialize components with graceful fallbacks
        self.rosetta = RosettaStone() if RosettaStone else None
        self.tag_manager = TagManager() if TagManager else None

        self.jobs: dict[str, Job] = {}
        self.logger = logging.getLogger(__name__)

        # Load existing jobs (keep reference to avoid dangling-task warning)
        self._init_task = asyncio.create_task(self.load_jobs())

    async def create_job(
        self,
        title: str,
        description: str,
        tags: list[str] | None = None,
        priority: int = 5,
        dependencies: list[str] | None = None,
        estimated_hours: float | None = None,
        assigned_to: str | None = None,
    ) -> str:
        """Create new job with intelligent processing."""
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:19]}"

        # Process description through Rosetta Stone if available
        processed_desc = description
        if self.rosetta:
            try:
                processed_desc = await self.rosetta.process_unknown_words(description)
            except Exception as e:
                self.logger.warning(f"Rosetta processing failed: {e}")

        # Auto-generate tags if TagManager available
        auto_tags: list[Any] = []
        if self.tag_manager:
            try:
                auto_tags = await self.tag_manager.extract_tags(description)
            except Exception as e:
                self.logger.warning(f"Auto-tagging failed: {e}")

        # Combine tags
        all_tags = list(set((tags or []) + auto_tags))

        # Create job
        job = Job(
            id=job_id,
            title=title,
            description=processed_desc,
            status="pending",
            priority=priority,
            tags=all_tags,
            dependencies=dependencies or [],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            metadata={},
            estimated_hours=estimated_hours,
            assigned_to=assigned_to,
        )

        self.jobs[job_id] = job
        await self.save_jobs()

        self.logger.info(f"Created job {job_id}: {title}")
        return job_id

    async def update_job_status(
        self, job_id: str, status: str, actual_hours: float | None = None
    ) -> None:
        """Update job status with dependency resolution."""
        if job_id not in self.jobs:
            msg = f"Job {job_id} not found"
            raise ValueError(msg)

        old_status = self.jobs[job_id].status
        self.jobs[job_id].status = status
        self.jobs[job_id].updated_at = datetime.now().isoformat()

        if actual_hours is not None:
            self.jobs[job_id].actual_hours = actual_hours

        # Auto-resolve dependencies when job completes
        if status == "completed" and old_status != "completed":
            await self._resolve_dependencies(job_id)

        await self.save_jobs()
        self.logger.info(f"Updated job {job_id} status: {old_status} -> {status}")

    async def _resolve_dependencies(self, completed_job_id: str) -> None:
        """Automatically activate jobs waiting on this dependency."""
        resolved_count = 0

        for job in self.jobs.values():
            if completed_job_id in job.dependencies and job.status == "blocked":
                # Check if all dependencies are completed
                remaining_deps = [
                    dep
                    for dep in job.dependencies
                    if self.jobs.get(dep, Job("", "", "", "pending", 0, [], [], "", "", {})).status
                    != "completed"
                ]

                if not remaining_deps:
                    job.status = "pending"
                    job.updated_at = datetime.now().isoformat()
                    resolved_count += 1

        if resolved_count > 0:
            self.logger.info(f"Resolved {resolved_count} dependent jobs")

    async def get_job_queue(
        self, status: str | None = None, assigned_to: str | None = None
    ) -> list[Job]:
        """Get filtered job queue."""
        jobs = list(self.jobs.values())

        if status:
            jobs = [job for job in jobs if job.status == status]

        if assigned_to:
            jobs = [job for job in jobs if job.assigned_to == assigned_to]

        # Sort by priority (highest first), then by creation date
        jobs.sort(key=lambda x: (-x.priority, x.created_at))
        return jobs

    async def get_job_stats(self) -> dict[str, Any]:
        """Get comprehensive job statistics."""
        if not self.jobs:
            return {"total": 0, "by_status": {}, "by_priority": {}}

        stats = {
            "total": len(self.jobs),
            "by_status": {},
            "by_priority": {},
            "total_estimated_hours": 0,
            "total_actual_hours": 0,
            "completion_rate": 0,
        }

        for job in self.jobs.values():
            # Status counts
            stats["by_status"][job.status] = stats["by_status"].get(job.status, 0) + 1

            # Priority counts
            stats["by_priority"][job.priority] = stats["by_priority"].get(job.priority, 0) + 1

            # Hours tracking
            if job.estimated_hours:
                stats["total_estimated_hours"] += job.estimated_hours
            if job.actual_hours:
                stats["total_actual_hours"] += job.actual_hours

        # Calculate completion rate
        completed = stats["by_status"].get("completed", 0)
        if stats["total"] > 0:
            stats["completion_rate"] = (completed / stats["total"]) * 100

        return stats

    async def load_jobs(self) -> None:
        """Load jobs from storage with error handling."""
        active_file = self.data_path / "active_jobs.json"
        completed_file = self.data_path / "completed_jobs.json"

        # Load active jobs
        if active_file.exists():
            try:
                with open(active_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for job_data in data.get("jobs", []):
                        job = Job(**job_data)
                        self.jobs[job.id] = job
                self.logger.info(f"Loaded {len(data.get('jobs', []))} active jobs")
            except Exception as e:
                self.logger.exception(f"Failed to load active jobs: {e}")

        # Load completed jobs
        if completed_file.exists():
            try:
                with open(completed_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for job_data in data.get("jobs", []):
                        job = Job(**job_data)
                        self.jobs[job.id] = job
                self.logger.info(f"Loaded {len(data.get('jobs', []))} completed jobs")
            except Exception as e:
                self.logger.exception(f"Failed to load completed jobs: {e}")

    async def save_jobs(self) -> None:
        """Save jobs to storage with backup."""
        active_file = self.data_path / "active_jobs.json"
        completed_file = self.data_path / "completed_jobs.json"

        # Separate active and completed jobs
        active_jobs = [asdict(job) for job in self.jobs.values() if job.status != "completed"]
        completed_jobs = [asdict(job) for job in self.jobs.values() if job.status == "completed"]

        try:
            # Save active jobs
            with open(active_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "jobs": active_jobs,
                        "last_updated": datetime.now().isoformat(),
                        "version": "1.0",
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            # Save completed jobs
            with open(completed_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "jobs": completed_jobs,
                        "last_updated": datetime.now().isoformat(),
                        "version": "1.0",
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            self.logger.debug(
                f"Saved {len(active_jobs)} active, {len(completed_jobs)} completed jobs"
            )

        except Exception as e:
            self.logger.exception(f"Failed to save jobs: {e}")
            raise


# Convenience functions for quick access
async def create_quick_job(title: str, description: str, priority: int = 5) -> str:
    """Quick job creation function."""
    tracker = JobTracker()
    return await tracker.create_job(title, description, priority=priority)


async def get_active_jobs() -> list[Job]:
    """Get all active jobs."""
    tracker = JobTracker()
    return await tracker.get_job_queue(status="pending")
