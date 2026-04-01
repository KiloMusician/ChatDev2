#!/usr/bin/env python3
"""Feedback Loop System - Error → Quest → Assignment → Agent.

Implements the critical missing feedback loop that connects:
1. Error detection (from diagnostic reports)
2. Quest creation (in quest system)
3. Task assignment (to agents in task queue)
4. Agent execution (real work on real commits)
5. Result integration (feedback to system)

This is the system that was missing - the bridge between visibility and action.
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from src.orchestration.agent_task_queue import (AgentTaskQueue, TaskPriority,
                                                TaskType)

logger = logging.getLogger(__name__)


def _json_default(value: Any) -> Any:
    """Best-effort JSON serializer for persisted loop state.

    Some upstream tools emit datetimes (and other non-JSON types) into the error queue;
    persistence must never crash the loop engine.
    """
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    return str(value)


@dataclass
class ErrorReport:
    """An error that needs to be addressed."""

    error_id: str
    error_type: str  # mypy, ruff, syntax, etc.
    file_path: str
    line_number: int | None = None
    message: str = ""
    severity: str = "medium"  # critical, high, medium, low
    source_system: str = "unknown"
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    processed: bool = False


@dataclass
class FeedbackLoopState:
    """Tracks state of a feedback loop execution."""

    error_id: str
    error_report: ErrorReport
    quest_id: str | None = None
    task_id: str | None = None
    agent_id: str | None = None
    status: str = "created"  # created, quest_created, assigned, in_progress, completed, failed
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    artifacts: list[str] = field(default_factory=list)


class FeedbackLoopEngine:
    """Orchestrates the Error → Quest → Assignment → Execution loop."""

    def __init__(
        self,
        loop_dir: Path | str = "state/feedback_loops",
        task_queue: AgentTaskQueue | None = None,
    ):
        """Initialize feedback loop engine.

        Args:
            loop_dir: Directory to store loop state
            task_queue: Task queue to assign work to
        """
        self.loop_dir = Path(loop_dir)
        self.loop_dir.mkdir(parents=True, exist_ok=True)

        self.task_queue = task_queue or AgentTaskQueue()
        self.loops_file = self.loop_dir / "loops.jsonl"
        self.error_queue_file = self.loop_dir / "error_queue.jsonl"

        # In-memory state
        self._loops: dict[str, FeedbackLoopState] = {}
        self._error_queue: list[ErrorReport] = []

        self._load_state()

        # Agent capabilities mapping
        self.agent_capabilities = {
            "Copilot": ["code_fix", "refactor", "test", "lint"],
            "Claude": ["analysis", "architecture", "review", "documentation"],
            "ChatDev": ["test", "integration", "optimization"],
            "Ollama": ["analysis", "documentation"],
        }

    def _load_state(self) -> None:
        """Load state from persistence."""
        try:
            if self.error_queue_file.exists():
                for line in self.error_queue_file.read_text().strip().split("\n"):
                    if line.strip():
                        data = json.loads(line)
                        self._error_queue.append(self._deserialize_error(data))

            if self.loops_file.exists():
                for line in self.loops_file.read_text().strip().split("\n"):
                    if line.strip():
                        data = json.loads(line)
                        self._loops[data["error_id"]] = self._deserialize_loop(data)
        except (json.JSONDecodeError, ValueError, OSError) as e:
            logger.error(f"Failed to load feedback loop state: {e}")

    def _deserialize_error(self, data: dict[str, Any]) -> ErrorReport:
        """Deserialize an error report from JSON."""
        return ErrorReport(
            error_id=data["error_id"],
            error_type=data["error_type"],
            file_path=data["file_path"],
            line_number=data.get("line_number"),
            message=data.get("message", ""),
            severity=data.get("severity", "medium"),
            source_system=data.get("source_system", "unknown"),
            detected_at=data.get("detected_at", datetime.now().isoformat()),
            processed=data.get("processed", False),
        )

    def _deserialize_loop(self, data: dict[str, Any]) -> FeedbackLoopState:
        """Deserialize a feedback loop state from JSON."""
        return FeedbackLoopState(
            error_id=data["error_id"],
            error_report=self._deserialize_error(data["error_report"]),
            quest_id=data.get("quest_id"),
            task_id=data.get("task_id"),
            agent_id=data.get("agent_id"),
            status=data.get("status", "created"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            artifacts=data.get("artifacts", []),
        )

    def ingest_error(self, error: ErrorReport) -> None:
        """Add an error to the processing queue.

        Args:
            error: Error report to process
        """
        self._error_queue.append(error)
        self._save_error_queue()
        logger.info(
            f"📥 Error ingested: {error.error_type} in {error.file_path}:{error.line_number}"
        )

    def ingest_errors_from_report(self, report_path: Path | str) -> int:
        """Ingest errors from a diagnostic report file.

        Args:
            report_path: Path to report file

        Returns:
            Number of errors ingested
        """
        report_path = Path(report_path)
        if not report_path.exists():
            logger.error(f"Report file not found: {report_path}")
            return 0

        count = 0
        try:
            content = report_path.read_text()

            # Parse as JSONL or JSON
            if content.strip().startswith("["):
                # JSON array
                errors_data = json.loads(content)
                for error_data in errors_data:
                    if isinstance(error_data, dict):
                        error = self._deserialize_error(error_data)
                        self.ingest_error(error)
                        count += 1
            else:
                # JSONL format
                for line in content.strip().split("\n"):
                    if line.strip():
                        error_data = json.loads(line)
                        error = self._deserialize_error(error_data)
                        self.ingest_error(error)
                        count += 1
        except (json.JSONDecodeError, ValueError, OSError) as e:
            logger.error(f"Failed to parse report: {e}")

        logger.info(f"✅ Ingested {count} errors from report")
        return count

    def process_error_queue(self, max_errors: int | None = None) -> int:
        """Process pending errors in the queue.

        This is the main loop that converts errors into tasks and assigns them to agents.

        Args:
            max_errors: Maximum number of errors to process (None = all)

        Returns:
            Number of errors processed
        """
        if not self._error_queue:
            logger.info("Info: Error queue is empty")
            return 0

        errors_to_process = self._error_queue[:max_errors] if max_errors else self._error_queue
        processed = 0

        for error in errors_to_process:
            try:
                if self._process_single_error(error):
                    processed += 1
                    self._error_queue.remove(error)
            except Exception as e:
                logger.error(f"Failed to process error {error.error_id}: {e}")

        if processed > 0:
            self._save_error_queue()
            logger.info(f"✨ Processed {processed} errors from queue")

        return processed

    def _process_single_error(self, error: ErrorReport) -> bool:
        """Process a single error through the feedback loop.

        Args:
            error: Error to process

        Returns:
            True if processed successfully, False otherwise
        """
        logger.info(f"🔄 Processing error: {error.error_type} → {error.file_path}")

        # Step 1: Create feedback loop state
        loop = FeedbackLoopState(error_id=error.error_id, error_report=error)
        self._loops[error.error_id] = loop

        # Step 2: Determine priority based on severity
        priority_map = {
            "critical": TaskPriority.CRITICAL,
            "high": TaskPriority.HIGH,
            "medium": TaskPriority.NORMAL,
            "low": TaskPriority.LOW,
        }
        priority = priority_map.get(error.severity, TaskPriority.NORMAL)

        # Step 3: Determine task type and required capabilities
        task_type, capabilities = self._get_task_type_and_capabilities(error)

        # Step 4: Create task in queue
        task_id = f"task_{error.error_id}_{int(datetime.now().timestamp())}"
        task_title = f"Fix {error.error_type}: {Path(error.file_path).name}"

        task = self.task_queue.create_task(
            task_id=task_id,
            task_type=task_type,
            title=task_title,
            description=self._build_task_description(error),
            priority=priority,
            source="feedback_loop",
            source_ref=error.error_id,
            capabilities_required=capabilities,
            estimated_duration_minutes=self._estimate_duration(error),
        )

        loop.task_id = task_id
        loop.status = "task_created"
        self._save_loop(loop)

        # Step 5: Find and assign best agent
        best_agent = self._find_best_agent(task)
        if best_agent and self.task_queue.assign_task(task_id, best_agent["id"]):
            loop.agent_id = best_agent["id"]
            loop.status = "assigned"
            self._save_loop(loop)

            logger.info(
                f"✅ Error {error.error_id} processed: Task {task_id} assigned to {best_agent['name']}"
            )
            return True

        logger.warning(f"⚠️  Could not assign task for error {error.error_id} (no agent available)")
        loop.status = "blocked"
        self._save_loop(loop)
        return False

    def _get_task_type_and_capabilities(self, error: ErrorReport) -> tuple[TaskType, list[str]]:
        """Determine task type and required capabilities from error.

        Args:
            error: Error report

        Returns:
            (TaskType, list of required capabilities)
        """
        error_type_lower = error.error_type.lower()

        if "mypy" in error_type_lower or "type" in error_type_lower:
            return TaskType.CODE_FIX, ["code_fix"]
        elif "ruff" in error_type_lower or "lint" in error_type_lower:
            return TaskType.CODE_FIX, ["code_fix", "lint"]
        elif "test" in error_type_lower:
            return TaskType.TEST, ["test"]
        elif "syntax" in error_type_lower or "import" in error_type_lower:
            return TaskType.CODE_FIX, ["code_fix"]
        else:
            return TaskType.ANALYSIS, ["analysis"]

    def _build_task_description(self, error: ErrorReport) -> str:
        """Build a detailed task description from error.

        Args:
            error: Error report

        Returns:
            Task description
        """
        desc_parts = [
            f"**Error Type:** {error.error_type}",
            f"**File:** {error.file_path}",
        ]

        if error.line_number:
            desc_parts.append(f"**Line:** {error.line_number}")

        if error.message:
            desc_parts.append(f"**Message:** {error.message}")

        desc_parts.append(f"**Severity:** {error.severity}")
        desc_parts.append(f"**Detected by:** {error.source_system}")

        return "\n".join(desc_parts)

    def _estimate_duration(self, error: ErrorReport) -> int:
        """Estimate task duration in minutes.

        Args:
            error: Error report

        Returns:
            Estimated duration in minutes
        """
        # Default estimates by error type
        estimates = {
            "mypy": 15,
            "ruff": 10,
            "syntax": 20,
            "import": 15,
            "test": 30,
        }

        error_type_lower = error.error_type.lower()
        for key, minutes in estimates.items():
            if key in error_type_lower:
                return minutes

        return 30  # Default

    def _find_best_agent(self, task: Any) -> dict[str, Any] | None:
        """Find the best agent to assign a task to.

        Args:
            task: Task to assign

        Returns:
            Best agent info or None if none available
        """
        required_caps = set(task.capabilities_required)

        best_agent = None
        best_score = 0

        for agent_id, agent_info in self.task_queue._agent_registry.items():
            # Skip if agent is at capacity
            if agent_info["current_load"] >= agent_info["max_concurrent_tasks"]:
                continue

            # Check if agent has required capabilities
            agent_caps = set(agent_info["capabilities"])
            if not required_caps.issubset(agent_caps):
                continue

            # Score agent by load (prefer less busy) and completion rate
            load_score = 1.0 / (1.0 + agent_info["current_load"])
            completion_score = agent_info.get("completed_tasks", 0) / 10.0
            score = load_score * 0.7 + completion_score * 0.3

            if score > best_score:
                best_score = score
                best_agent = {
                    "id": agent_id,
                    "name": agent_info["name"],
                    "score": score,
                }

        return best_agent

    def get_loop_status(self, error_id: str) -> FeedbackLoopState | None:
        """Get status of a feedback loop.

        Args:
            error_id: Error ID

        Returns:
            Loop state or None if not found
        """
        return self._loops.get(error_id)

    def get_engine_status(self) -> dict[str, Any]:
        """Get overall engine status.

        Returns:
            Status dictionary
        """
        return {
            "pending_errors": len(self._error_queue),
            "active_loops": len(
                [loop for loop in self._loops.values() if loop.status != "completed"]
            ),
            "completed_loops": len(
                [loop for loop in self._loops.values() if loop.status == "completed"]
            ),
            "blocked_loops": len(
                [loop for loop in self._loops.values() if loop.status == "blocked"]
            ),
            "agents_available": len(self.task_queue._agent_registry),
            "timestamp": datetime.now().isoformat(),
        }

    def _save_error_queue(self) -> None:
        """Save error queue to persistence."""
        try:
            errors_list = []
            for e in self._error_queue:
                err_dict = asdict(e)
                errors_list.append(err_dict)
            content = "\n".join(json.dumps(e, default=_json_default) for e in errors_list)
            self.error_queue_file.write_text(content + "\n", encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save error queue: {e}")

    def _save_loop(self, loop: FeedbackLoopState) -> None:
        """Save feedback loop state to persistence."""
        try:
            loops = []
            if self.loops_file.exists():
                for line in self.loops_file.read_text().strip().split("\n"):
                    if line.strip():
                        loops.append(json.loads(line))

            loops = [loop_item for loop_item in loops if loop_item["error_id"] != loop.error_id]

            loop_dict = asdict(loop)
            loop_dict["error_report"] = asdict(loop.error_report)
            loops.append(loop_dict)

            content = "\n".join(json.dumps(loop_item, default=_json_default) for loop_item in loops)
            self.loops_file.write_text(content + "\n", encoding="utf-8")
        except (json.JSONDecodeError, ValueError, OSError) as e:
            logger.error(f"Failed to save loop: {e}")
