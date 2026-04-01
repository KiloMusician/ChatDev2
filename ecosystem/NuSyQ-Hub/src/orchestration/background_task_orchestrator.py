"""Background Task Orchestrator - High Token Action Delegation.

Enables Claude Code CLI (and other agents) to dispatch high-token/expensive
operations to local LLMs (Ollama, LM Studio) or ChatDev multi-agent teams.

This solves the problem of expensive token operations by:
1. Receiving task requests from any orchestrating agent (Claude, Copilot, Codex)
2. Routing to the appropriate local LLM or ChatDev based on task type
3. Running tasks in background with progress tracking
4. Reporting results back through the intermediary

Architecture:
    Claude Code CLI  <---->  Background Task Orchestrator  <---->  Ollama
                                       |                    <---->  LM Studio
    Copilot          <------->         |                    <---->  ChatDev
    Codex            <------->         |
                                       v
                              Guild Board / Quest Log

Usage via CLI:
    python scripts/start_nusyq.py dispatch_task "Analyze this large codebase" --model=deepseek-coder-v2:16b
    python scripts/start_nusyq.py dispatch_task "Generate comprehensive tests" --target=chatdev
    python scripts/start_nusyq.py dispatch_task "Review this module" --target=copilot --type=review
    python scripts/start_nusyq.py task_status <task_id>
    python scripts/start_nusyq.py list_background_tasks
"""

import asyncio
import contextlib
import json
import logging
import os
import threading
import time
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar, cast

try:  # Python 3.11+
    from datetime import UTC  # type: ignore[attr-defined]
except ImportError:
    from datetime import timezone  # Python 3.10

    UTC = timezone.utc  # noqa: UP017

try:
    import fcntl
except ImportError:  # pragma: no cover - only for non-posix platforms
    fcntl = None  # type: ignore[assignment]

try:
    import msvcrt
except ImportError:  # pragma: no cover - only for non-Windows platforms
    msvcrt = None  # type: ignore[assignment]

# Phase 3 Integration imports
Phase3Integration: Any = None
try:
    from src.integration.phase3_integration import \
        Phase3Integration as _Phase3Integration

    Phase3Integration = _Phase3Integration
    PHASE3_AVAILABLE = True
except ImportError:
    PHASE3_AVAILABLE = False

try:
    from src.guild.guild_board import AgentStatus, GuildBoard
except ImportError:
    AgentStatus = None  # type: ignore
    GuildBoard = None  # type: ignore

logger = logging.getLogger(__name__)


# Custom exceptions for orchestration
class OrchestrationError(Exception):
    """Base exception for orchestration errors."""

    pass


class OllamaError(OrchestrationError):
    """Exception for Ollama-related errors."""

    pass


class LMStudioError(OrchestrationError):
    """Exception for LM Studio-related errors."""

    pass


class ChatDevError(OrchestrationError):
    """Exception for ChatDev-related errors."""

    pass


class TaskTarget(Enum):
    """Available task execution targets."""

    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"
    CHATDEV = "chatdev"
    COPILOT = "copilot"
    AUTO = "auto"  # Intelligent routing based on task type


class TaskStatus(Enum):
    """Task execution status."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""

    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


@dataclass
class BackgroundTask:
    """Represents a background task for local LLM execution."""

    task_id: str
    prompt: str
    target: TaskTarget
    model: str | None = None
    status: TaskStatus = TaskStatus.QUEUED
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: str | None = None
    error: str | None = None
    progress: float = 0.0
    metadata: dict = field(default_factory=dict)
    requesting_agent: str = "unknown"
    token_estimate: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        prompt_preview = self.prompt[:200] + "..." if len(self.prompt) > 200 else self.prompt
        return {
            "task_id": self.task_id,
            # Keep legacy prompt behavior (truncated) for stable CLI/test output.
            "prompt": prompt_preview,
            # Preserve full prompt for deterministic reload and dedupe behavior.
            "prompt_full": self.prompt,
            "prompt_preview": prompt_preview,
            "target": self.target.value,
            "model": self.model,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "result_preview": (
                self.result[:500] + "..." if self.result and len(self.result) > 500 else self.result
            ),
            "error": self.error,
            "progress": self.progress,
            "metadata": self.metadata,
            "requesting_agent": self.requesting_agent,
            "token_estimate": self.token_estimate,
        }


class BackgroundTaskOrchestrator:
    """Orchestrates background task execution across local LLMs and ChatDev.

    This enables Claude Code CLI and other agents to offload expensive
    token operations to local resources.
    """

    # Default model mappings for different task types
    MODEL_ROUTING: ClassVar[dict] = {
        "code_analysis": "deepseek-coder-v2:16b",
        "code_generation": "qwen2.5-coder:14b",
        "code_completion": "codellama:7b",
        "general": "llama3.1:8b",
        "embedding": "nomic-embed-text:latest",
        "fast": "phi3.5:latest",
        "precise": "deepseek-coder-v2:16b",
    }

    # Ollama endpoint
    OLLAMA_URL = "http://localhost:11434"

    # LM Studio endpoint
    LM_STUDIO_URL = "http://10.0.0.172:1234"

    # Timezone suffix for ISO 8601 datetime parsing
    UTC_OFFSET_SUFFIX = "+00:00"

    _STATUS_RANK: ClassVar[dict] = {
        TaskStatus.QUEUED.value: 0,
        TaskStatus.RUNNING.value: 1,
        TaskStatus.COMPLETED.value: 2,
        TaskStatus.FAILED.value: 2,
        TaskStatus.CANCELLED.value: 2,
    }

    def __init__(self, state_dir: Path | None = None):
        """Initialize persisted task orchestrator state and runtime helpers."""
        self.state_dir = state_dir or Path("state/background_tasks")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_file = self.state_dir / "tasks.json"
        self.lock_file = self.state_dir / "tasks.lock"

        self.tasks: dict[str, BackgroundTask] = {}
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="bg_task_")
        self._running = False
        self._worker_task: asyncio.Task | None = None
        self._lock = threading.RLock()

        # Phase 3 Integration (lazy initialization)
        self.phase3: Phase3Integration | None = None
        self._phase3_initialized = False

        # Culture Ship Strategic Advisor (lazy initialization)
        self.culture_ship_advisor: Any | None = None
        self._culture_ship_initialized = False

        # Consciousness Loop (lazy init)
        self._consciousness_loop = None
        self._consciousness_initialized: bool = False

        # Guild Board Integration (lazy init)
        self.guild_board: Any | None = None
        self._guild_board_initialized = False
        self._heartbeat_task: asyncio.Task | None = None

        # Load persisted tasks
        self._load_tasks()
        deduped = self._deduplicate_queued_tasks_in_memory()
        if deduped:
            self._save_tasks()
            logger.info(f"Deduplicated {deduped} queued tasks at startup")

        logger.info("BackgroundTaskOrchestrator initialized")

    def _load_tasks(self):
        """Load persisted tasks from disk."""
        if self.tasks_file.exists():
            try:
                with self._file_lock():
                    data = json.loads(self.tasks_file.read_text(encoding="utf-8"))
                loaded = 0
                skipped = 0
                for task_data in data.get("tasks", []):
                    try:
                        # Parse datetime fields
                        created_at = datetime.now(UTC)
                        if task_data.get("created_at"):
                            with contextlib.suppress(ValueError, AttributeError):
                                created_at = datetime.fromisoformat(
                                    task_data["created_at"].replace("Z", self.UTC_OFFSET_SUFFIX)
                                )

                        started_at = None
                        if task_data.get("started_at"):
                            with contextlib.suppress(ValueError, AttributeError):
                                started_at = datetime.fromisoformat(
                                    task_data["started_at"].replace("Z", self.UTC_OFFSET_SUFFIX)
                                )

                        completed_at = None
                        if task_data.get("completed_at"):
                            with contextlib.suppress(ValueError, AttributeError):
                                completed_at = datetime.fromisoformat(
                                    task_data["completed_at"].replace("Z", self.UTC_OFFSET_SUFFIX)
                                )

                        target_raw = task_data.get("target", "auto")
                        try:
                            target = TaskTarget(target_raw)
                        except ValueError:
                            target = TaskTarget.AUTO

                        status_raw = task_data.get("status", "queued")
                        try:
                            status = TaskStatus(status_raw)
                        except ValueError:
                            status = TaskStatus.QUEUED

                        priority_raw = task_data.get("priority", TaskPriority.NORMAL.value)
                        if isinstance(priority_raw, str):
                            try:
                                priority = TaskPriority[priority_raw.upper()]
                            except KeyError:
                                try:
                                    priority = TaskPriority(int(priority_raw))
                                except (ValueError, KeyError):
                                    priority = TaskPriority.NORMAL
                        else:
                            try:
                                priority = TaskPriority(priority_raw)
                            except (TypeError, ValueError):
                                priority = TaskPriority.NORMAL

                        metadata = task_data.get("metadata")
                        if not isinstance(metadata, dict):
                            metadata = {}

                        task = BackgroundTask(
                            task_id=task_data["task_id"],
                            prompt=task_data.get("prompt_full")
                            or task_data.get("prompt")
                            or task_data.get("prompt_preview", "")
                            or "",
                            target=target,
                            model=task_data.get("model"),
                            status=status,
                            priority=priority,
                            requesting_agent=task_data.get("requesting_agent", "unknown"),
                            created_at=created_at,
                            started_at=started_at,
                            completed_at=completed_at,
                            result=task_data.get("result", task_data.get("result_preview")),
                            error=task_data.get("error"),
                            progress=task_data.get("progress", 0.0),
                            token_estimate=task_data.get("token_estimate", 0),
                            metadata=metadata,
                        )
                        self.tasks[task.task_id] = task
                        loaded += 1
                    except (KeyError, TypeError, ValueError):
                        skipped += 1
                        continue
                logger.info(f"Loaded {loaded} persisted tasks")
                if skipped:
                    logger.warning(f"Skipped {skipped} malformed persisted tasks")
            except (OSError, json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to load tasks: {e}")

    @contextlib.contextmanager
    def _file_lock(self, timeout_seconds: float = 10.0):
        """Cross-process lock for tasks persistence."""
        lock_fh = open(self.lock_file, "a+", encoding="utf-8")
        # Windows path: use msvcrt byte-range lock on first byte.
        if os.name == "nt" and msvcrt is not None:
            locking_fn = getattr(msvcrt, "locking", None)
            lock_nonblocking = getattr(msvcrt, "LK_NBLCK", None)
            lock_unlock = getattr(msvcrt, "LK_UNLCK", None)
            if not callable(locking_fn) or lock_nonblocking is None or lock_unlock is None:
                lock_fh.close()
                raise RuntimeError("msvcrt locking API unavailable")
            deadline = time.monotonic() + timeout_seconds
            while True:
                try:
                    lock_fh.seek(0)
                    locking_fn(lock_fh.fileno(), lock_nonblocking, 1)
                    break
                except OSError as exc:
                    if time.monotonic() >= deadline:
                        lock_fh.close()
                        raise TimeoutError("Timed out waiting for tasks file lock") from exc
                    time.sleep(0.05)
            try:
                yield
            finally:
                try:
                    lock_fh.seek(0)
                    locking_fn(lock_fh.fileno(), lock_unlock, 1)
                finally:
                    lock_fh.close()
            return

        fcntl_module = globals().get("fcntl")
        if fcntl_module is None:
            # Best effort fallback when advisory locks are unavailable.
            try:
                yield
            finally:
                lock_fh.close()
            return

        deadline = time.monotonic() + timeout_seconds
        while True:
            try:
                fcntl_module.flock(lock_fh.fileno(), fcntl_module.LOCK_EX | fcntl_module.LOCK_NB)
                break
            except BlockingIOError as exc:
                if time.monotonic() >= deadline:
                    lock_fh.close()
                    raise TimeoutError("Timed out waiting for tasks file lock") from exc
                time.sleep(0.05)
        try:
            yield
        finally:
            fcntl_module.flock(lock_fh.fileno(), fcntl_module.LOCK_UN)
            lock_fh.close()

    def _task_rank(self, task_dict: dict) -> int:
        status = str(task_dict.get("status", TaskStatus.QUEUED.value)).lower()
        return self._STATUS_RANK.get(status, 0)

    def _task_timestamp(self, task_dict: dict) -> datetime:
        for field_name in ("completed_at", "started_at", "created_at"):
            raw = task_dict.get(field_name)
            if not raw:
                continue
            try:
                return datetime.fromisoformat(str(raw).replace("Z", self.UTC_OFFSET_SUFFIX))
            except ValueError:
                continue
        return datetime.fromtimestamp(0, tz=UTC)

    def _parse_ts(self, raw_value: str | None) -> datetime | None:
        if not raw_value:
            return None
        try:
            return datetime.fromisoformat(str(raw_value).replace("Z", self.UTC_OFFSET_SUFFIX))
        except ValueError:
            return None

    def _requeue_requested_at(self, task_dict: dict) -> datetime | None:
        metadata = task_dict.get("metadata")
        if not isinstance(metadata, dict):
            return None

        requeue_meta = metadata.get("requeue")
        if isinstance(requeue_meta, dict):
            for key in ("requested_at", "requestedAt", "timestamp", "ts"):
                parsed = self._parse_ts(requeue_meta.get(key))
                if parsed:
                    return parsed

        parsed = self._parse_ts(metadata.get("requeue_requested_at"))
        if parsed:
            return parsed

        if metadata.get("force_requeue") is True:
            return self._task_timestamp(task_dict)

        return None

    def _has_explicit_requeue(self, task_dict: dict) -> bool:
        return self._requeue_requested_at(task_dict) is not None

    def _merge_task_dicts(self, existing: dict, incoming: dict) -> dict:
        """Resolve two versions of the same task without regressing progress."""
        existing_rank = self._task_rank(existing)
        incoming_rank = self._task_rank(incoming)
        existing_status = str(existing.get("status", TaskStatus.QUEUED.value)).lower()
        incoming_status = str(incoming.get("status", TaskStatus.QUEUED.value)).lower()

        # Explicit requeue semantics:
        # allow intentional status downgrade to queued when requested.
        if (
            incoming_status == TaskStatus.QUEUED.value
            and existing_status != TaskStatus.QUEUED.value
            and self._has_explicit_requeue(incoming)
        ):
            winner, loser = incoming, existing
        elif (
            existing_status == TaskStatus.QUEUED.value
            and incoming_status != TaskStatus.QUEUED.value
            and self._has_explicit_requeue(existing)
        ):
            winner, loser = existing, incoming
        else:
            if incoming_rank > existing_rank:
                winner, loser = incoming, existing
            elif incoming_rank < existing_rank:
                winner, loser = existing, incoming
            else:
                if self._task_timestamp(incoming) >= self._task_timestamp(existing):
                    winner, loser = incoming, existing
                else:
                    winner, loser = existing, incoming

        merged = dict(winner)
        for field_name in ("result", "result_preview", "error"):
            if not merged.get(field_name) and loser.get(field_name):
                merged[field_name] = loser[field_name]

        if not isinstance(merged.get("metadata"), dict):
            merged["metadata"] = {}
        loser_metadata = loser.get("metadata")
        if isinstance(loser_metadata, dict):
            merged["metadata"] = {**loser_metadata, **merged["metadata"]}

        with contextlib.suppress(Exception):
            merged["progress"] = max(
                float(existing.get("progress", 0.0)), float(incoming.get("progress", 0.0))
            )

        return merged

    def _deduplicate_queued_tasks_in_memory(self) -> int:
        """Cancel duplicate queued tasks by prompt, preserving the oldest task."""
        queued_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.QUEUED]
        queued_tasks.sort(key=lambda t: t.created_at)

        seen_prompts: set[str] = set()
        removed = 0

        for task in queued_tasks:
            key = task.prompt.strip()
            if key in seen_prompts:
                task.status = TaskStatus.CANCELLED
                task.error = "Deduplicated queued task at load"
                task.completed_at = datetime.now(UTC)
                removed += 1
            else:
                seen_prompts.add(key)

        return removed

    def _save_tasks(self, preserve_on_disk: bool = True):
        """Persist tasks to disk."""
        try:
            with self._lock, self._file_lock():
                on_disk_tasks: dict[str, dict] = {}
                if preserve_on_disk and self.tasks_file.exists():
                    try:
                        existing_data = json.loads(self.tasks_file.read_text(encoding="utf-8"))
                        for task_data in existing_data.get("tasks", []):
                            task_id = task_data.get("task_id")
                            if task_id:
                                on_disk_tasks[str(task_id)] = task_data
                    except (OSError, json.JSONDecodeError, ValueError, KeyError):
                        # Corrupt file should not block progress; rewrite from memory.
                        on_disk_tasks = {}

                in_memory_tasks = {task_id: task.to_dict() for task_id, task in self.tasks.items()}
                if preserve_on_disk:
                    merged_tasks: dict[str, dict] = dict(on_disk_tasks)
                    for task_id, incoming in in_memory_tasks.items():
                        existing = merged_tasks.get(task_id)
                        if existing is None:
                            merged_tasks[task_id] = incoming
                        else:
                            merged_tasks[task_id] = self._merge_task_dicts(existing, incoming)
                else:
                    merged_tasks = dict(in_memory_tasks)

                data = {
                    "tasks": list(merged_tasks.values()),
                    "updated_at": datetime.now(UTC).isoformat(),
                }
                tmp_file = self.tasks_file.with_suffix(".json.tmp")
                tmp_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
                os.replace(tmp_file, self.tasks_file)
        except Exception as e:
            logger.warning(f"Failed to save tasks: {e}")

    def submit_task(
        self,
        prompt: str,
        target: TaskTarget = TaskTarget.AUTO,
        model: str | None = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        requesting_agent: str = "claude",
        task_type: str = "general",
        metadata: dict | None = None,
        allow_duplicate: bool = False,
    ) -> BackgroundTask:
        """Submit a new background task for execution.

        Args:
            prompt: The task prompt/instruction
            target: Execution target (ollama, lm_studio, chatdev, copilot, auto)
            model: Specific model to use (auto-selected if None)
            priority: Task priority
            requesting_agent: Which agent submitted this task
            task_type: Type of task for routing (code_analysis, code_generation, etc.)
            metadata: Additional task metadata
            allow_duplicate: If False, returns existing task if prompt already queued

        Returns:
            BackgroundTask instance with task_id for tracking
        """
        task_id = f"bg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        # Auto-select model if not specified
        if model is None and target in (TaskTarget.AUTO, TaskTarget.OLLAMA):
            model = self.MODEL_ROUTING.get(task_type, self.MODEL_ROUTING["general"])

        # Auto-select target based on task type
        if target == TaskTarget.AUTO:
            if task_type in ("code_analysis", "code_generation", "code_completion"):
                # Prefer local LLMs for code tasks
                target = TaskTarget.OLLAMA
            elif "team" in task_type.lower() or "multi" in task_type.lower():
                target = TaskTarget.CHATDEV
            else:
                target = TaskTarget.OLLAMA

        # Estimate tokens (rough: 4 chars per token)
        token_estimate = len(prompt) // 4

        task_metadata = dict(metadata or {})
        task_metadata.setdefault("task_type", task_type)
        if target == TaskTarget.COPILOT:
            # Copilot bridge tasks are often advisory; opt-in for PR automation.
            task_metadata.setdefault("autonomy_enabled", False)

        task = BackgroundTask(
            task_id=task_id,
            prompt=prompt,
            target=target,
            model=model,
            priority=priority,
            requesting_agent=requesting_agent,
            token_estimate=token_estimate,
            metadata=task_metadata,
        )

        with self._lock:
            # Check for duplicate prompts (deduplication) under lock to avoid races.
            if not allow_duplicate:
                for existing in self.tasks.values():
                    if existing.prompt == prompt and existing.status == TaskStatus.QUEUED:
                        logger.debug(
                            f"Duplicate prompt detected, returning existing task: {existing.task_id}"
                        )
                        return existing
            self.tasks[task_id] = task
            self._save_tasks()

        logger.info(f"Task submitted: {task_id} -> {target.value}/{model} by {requesting_agent}")

        try:
            from src.system.agent_awareness import emit as _emit

            _emit(
                "tasks",
                f"Submit: {task_id} target={target.value} priority={priority.name}"
                f" by={requesting_agent} tokens~{token_estimate}",
                level="INFO",
                source="background_task_orchestrator",
            )
        except Exception:
            pass

        return task

    async def execute_task(self, task: BackgroundTask) -> BackgroundTask:
        """Execute a single background task."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(UTC)
        task.progress = 0.1

        # --- agent_awareness: task started ---
        try:
            from src.system.agent_awareness import emit as _emit

            _agent = task.requesting_agent or "orchestrator"
            _emit.task_started(_agent, task.task_id, task.prompt[:120])
        except Exception:
            pass

        # --- Culture Ship veto (pre-execution) ---
        if self._consciousness_loop is not None and self._task_needs_approval(task):
            approval = self._consciousness_loop.request_approval(
                action=f"execute_{task.target.value}",
                context={
                    "task_id": task.task_id,
                    "prompt_preview": task.prompt[:120],
                    "metadata": task.metadata,
                },
            )
            if not approval.approved:
                task.status = TaskStatus.FAILED
                task.error = f"Culture Ship veto: {approval.reason}"
                task.completed_at = datetime.now(UTC)
                self._save_tasks()
                logger.warning("Task %s vetoed by Culture Ship: %s", task.task_id, approval.reason)
                return task

        # --- Event: task started ---
        if self._consciousness_loop is not None:
            self._consciousness_loop.emit_event_sync(
                "task_started",
                {
                    "task_id": task.task_id,
                    "target": task.target.value,
                    "prompt_preview": task.prompt[:80],
                },
            )

        try:
            if task.target == TaskTarget.OLLAMA:
                result = await self._execute_ollama(task)
            elif task.target == TaskTarget.LM_STUDIO:
                result = await self._execute_lm_studio(task)
            elif task.target == TaskTarget.CHATDEV:
                result = await self._execute_chatdev(task)
            elif task.target == TaskTarget.COPILOT:
                result = await self._execute_copilot(task)
            else:
                raise ValueError(f"Unknown target: {task.target}")

            task.result = result
            task.status = TaskStatus.COMPLETED
            task.progress = 1.0

            # --- agent_awareness: task completed ---
            try:
                from src.system.agent_awareness import emit as _emit

                _agent = task.requesting_agent or "orchestrator"
                _emit.task_completed(_agent, task.task_id, f"{task.prompt[:80]}: completed")
            except Exception:
                pass

        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            logger.error(f"Task {task.task_id} failed: {e}")

            # --- agent_awareness: task failed ---
            try:
                from src.system.agent_awareness import emit as _emit

                _agent = task.requesting_agent or "orchestrator"
                _emit.task_failed(_agent, task.task_id, str(e))
            except Exception:
                pass

        task.completed_at = datetime.now(UTC)
        self._save_tasks()

        # --- Event: task completed or failed ---
        if self._consciousness_loop is not None:
            duration = (
                (task.completed_at - task.started_at).total_seconds() if task.started_at else 0
            )
            event = "task_completed" if task.status == TaskStatus.COMPLETED else "task_failed"
            self._consciousness_loop.emit_event_sync(
                event,
                {
                    "task_id": task.task_id,
                    "status": task.status.value,
                    "duration_seconds": round(duration, 2),
                    "error": task.error,
                },
            )

        # Log to quest log for tracking
        self._log_to_quest(task)

        # Trigger autonomy pipeline if applicable (for code generation tasks)
        if (
            task.status == TaskStatus.COMPLETED
            and task.metadata.get("autonomy_enabled", True)
            and not task.metadata.get("autonomy_processed")
        ):
            try:
                await self._trigger_autonomy(task)
            except Exception as e:
                logger.warning(f"Autonomy processing failed for {task.task_id}: {e}")

        return task

    async def _execute_ollama(self, task: BackgroundTask) -> str:
        """Execute task via Ollama."""
        import aiohttp

        url = f"{self.OLLAMA_URL}/api/generate"
        payload = {
            "model": task.model or "llama3.1:8b",
            "prompt": task.prompt,
            "stream": False,
        }

        task.progress = 0.3

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self._get_adaptive_timeout(600)),
            ) as resp,
        ):
            if resp.status != 200:
                raise OllamaError(f"Ollama error: {resp.status}")

            task.progress = 0.8
            data = await resp.json()
            return str(data.get("response", ""))

    async def _execute_lm_studio(self, task: BackgroundTask) -> str:
        """Execute task via LM Studio (OpenAI-compatible API)."""
        import aiohttp

        url = f"{self.LM_STUDIO_URL}/v1/chat/completions"
        payload = {
            "model": task.model or "openai/gpt-oss-20b",
            "messages": [{"role": "user", "content": task.prompt}],
            "temperature": 0.7,
            "max_tokens": 4096,
        }

        task.progress = 0.3

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self._get_adaptive_timeout(600)),
            ) as resp,
        ):
            if resp.status != 200:
                raise LMStudioError(f"LM Studio error: {resp.status}")

            task.progress = 0.8
            data = await resp.json()
            choices = data.get("choices")
            if isinstance(choices, list) and choices and isinstance(choices[0], dict):
                message = choices[0].get("message")
                if isinstance(message, dict):
                    return str(message.get("content", ""))
            raise LMStudioError("LM Studio response missing message content")

    async def _execute_chatdev(self, task: BackgroundTask) -> str:
        """Execute task via ChatDev multi-agent team."""
        try:
            from src.integration.chatdev_launcher import ChatDevLauncher

            launcher = ChatDevLauncher()
            task.progress = 0.3
            project_name = f"task_{task.task_id}"

            # Preferred path for launchers that expose an async task API.
            run_task_fn = cast(Callable[..., Any] | None, getattr(launcher, "run_task", None))
            if callable(run_task_fn):
                maybe_result = run_task_fn(  # pylint: disable=not-callable
                    task_description=task.prompt,
                    project_name=project_name,
                )
                if asyncio.iscoroutine(maybe_result):
                    result = await maybe_result
                    task.progress = 0.9
                    return json.dumps(result) if isinstance(result, dict) else str(result)

            # Backward-compatible path using the current ChatDevLauncher API.
            process = launcher.launch_chatdev(
                task=task.prompt,
                name=project_name,
                model=task.model or "qwen2.5-coder:14b",
                organization="NuSyQ",
                config="Default",
            )

            # launch_chatdev may return either Popen or CompletedProcess.
            if hasattr(process, "wait"):
                return_code = await asyncio.to_thread(process.wait, 1200)  # 20 minute max
            else:
                return_code = getattr(process, "returncode", 0)

            task.progress = 0.9
            if return_code != 0:
                raise RuntimeError(f"ChatDev exited with return code {return_code}")

            return (
                f"ChatDev completed for {project_name} "
                f"(target={task.target.value}, model={task.model or 'qwen2.5-coder:14b'})"
            )

        except ImportError:
            # Fallback if ChatDev not available
            return f"ChatDev not available. Task queued: {task.prompt[:100]}..."

    def _resolve_copilot_task_type(self, task: BackgroundTask) -> str:
        """Map background task metadata into AgentTaskRouter task types."""
        metadata = task.metadata or {}

        explicit = str(metadata.get("router_task_type", "")).strip().lower()
        if explicit in {"analyze", "generate", "review", "debug", "plan", "test", "document"}:
            return explicit

        task_type = str(metadata.get("task_type", "")).strip().lower()
        if "review" in task_type:
            return "review"
        if "debug" in task_type or "fix" in task_type:
            return "debug"
        if "plan" in task_type:
            return "plan"
        if "test" in task_type:
            return "test"
        if "doc" in task_type:
            return "document"
        if "gen" in task_type or "build" in task_type:
            return "generate"
        return "analyze"

    async def _execute_copilot(self, task: BackgroundTask) -> str:
        """Execute task via AgentTaskRouter Copilot bridge."""
        try:
            from src.tools.agent_task_router import AgentTaskRouter
        except ImportError as exc:
            raise RuntimeError(f"Copilot routing unavailable: {exc}") from exc

        task.progress = 0.25
        router = AgentTaskRouter()
        router_task_type = self._resolve_copilot_task_type(task)
        priority_name = (
            task.priority.name if hasattr(task.priority, "name") else str(task.priority).upper()
        )

        context = dict(task.metadata or {})
        context.setdefault("background_task_id", task.task_id)
        context.setdefault("requesting_agent", task.requesting_agent)

        result = await router.route_task(
            task_type=router_task_type,
            description=task.prompt,
            context=context,
            target_system="copilot",
            priority=priority_name,
        )
        task.progress = 0.9

        status = str(result.get("status", "")).lower()
        if status not in {"success", "submitted"}:
            message = result.get("error") or result.get("reason") or "Unknown Copilot failure"
            raise RuntimeError(str(message))

        return json.dumps(result, default=str)

    def _log_to_quest(self, task: BackgroundTask):
        """Log completed task to quest log."""
        try:
            quest_log = Path("src/Rosetta_Quest_System/quest_log.jsonl")
            entry = {
                "timestamp": datetime.now(UTC).isoformat(),
                "task_type": "background_task",
                "description": f"Background task: {task.prompt[:100]}...",
                "status": task.status.value,
                "result": {
                    "task_id": task.task_id,
                    "target": task.target.value,
                    "model": task.model,
                    "requesting_agent": task.requesting_agent,
                    "duration_seconds": (
                        (task.completed_at - task.started_at).total_seconds()
                        if task.completed_at and task.started_at
                        else 0
                    ),
                },
            }
            with open(quest_log, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.warning(f"Failed to log to quest: {e}")

    async def _trigger_autonomy(self, task: BackgroundTask):
        """Trigger autonomy processing for completed task.

        This closes the feedback loop:
        Task completes → Result analyzed → Patches applied → PR created → Loop continues

        Only processes tasks that:
        1. Completed successfully with a result
        2. Not already processed
        3. Contain code output (optionally configurable via metadata)

        Phase 3 Enhancement: Validates OmniTag protocols before creating PRs
        """
        if not task.result or len(task.result.strip()) < 10:
            logger.debug(f"Task {task.task_id} has insufficient result for autonomy")
            return

        try:
            from src.autonomy import GitHubPRBot

            logger.info(f"[AUTONOMY] Processing task {task.task_id} through PR bot")

            # Phase 3: Validate code before autonomy processing
            validation_issues = []
            if self.phase3 and hasattr(self.phase3, "validate_code_before_pr"):
                try:
                    # Extract file paths from task metadata (if available)
                    files_to_validate = task.metadata.get("modified_files", [])
                    if files_to_validate:
                        validation_issues = await self.phase3.validate_code_before_pr(
                            files_to_validate
                        )
                        if validation_issues:
                            logger.warning(
                                f"[VALIDATION] Found {len(validation_issues)} OmniTag issues in task {task.task_id}"
                            )
                            task.metadata["omnitag_issues"] = validation_issues[
                                :10
                            ]  # Store first 10
                except Exception as e:
                    logger.warning(f"[VALIDATION] Failed for task {task.task_id}: {e}")

            bot = GitHubPRBot()
            result = await bot.process_llm_response(
                task_id=task.task_id, llm_response=task.result, task_description=task.prompt[:100]
            )

            # Mark task as autonomy-processed
            task.metadata["autonomy_processed"] = True
            task.metadata["autonomy_result"] = result
            self._save_tasks()

            logger.info(
                f"[AUTONOMY] Completed for {task.task_id}: "
                f"{result.get('action_taken', 'unknown')} "
                f"(risk={result.get('risk_level', 'unknown')})"
            )

        except ImportError:
            logger.debug("Autonomy system not available, skipping")
        except Exception as e:
            logger.error(f"[AUTONOMY] Failed to process task {task.task_id}: {e}", exc_info=True)

    def get_task(self, task_id: str) -> BackgroundTask | None:
        """Get task by ID."""
        return self.tasks.get(task_id)

    def list_tasks(
        self,
        status: TaskStatus | None = None,
        requesting_agent: str | None = None,
        limit: int = 50,
    ) -> list[BackgroundTask]:
        """List tasks with optional filtering."""
        tasks = list(self.tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]
        if requesting_agent:
            tasks = [t for t in tasks if t.requesting_agent == requesting_agent]

        # Sort by created_at descending
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        return tasks[:limit]

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a queued task."""
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.QUEUED:
            task.status = TaskStatus.CANCELLED
            self._save_tasks()
            return True
        return False

    def requeue_task(
        self,
        task_id: str,
        reason: str = "manual_requeue",
        requested_by: str = "system",
    ) -> bool:
        """Explicitly requeue a task and tag metadata for merge-aware status downgrade."""
        task = self.tasks.get(task_id)
        if not task:
            return False

        task.status = TaskStatus.QUEUED
        task.started_at = None
        task.completed_at = None
        task.progress = 0.0
        task.error = None
        task.result = None

        existing_requeue = task.metadata.get("requeue")
        current_count = 0
        if isinstance(existing_requeue, dict):
            try:
                current_count = int(existing_requeue.get("count", 0))
            except Exception:
                current_count = 0

        task.metadata["requeue"] = {
            "requested_at": datetime.now(UTC).isoformat(),
            "reason": reason,
            "requested_by": requested_by,
            "count": current_count + 1,
        }

        self._save_tasks()
        return True

    def get_orchestrator_status(self) -> dict:
        """Get orchestrator status summary."""
        status_counts = {s.value: 0 for s in TaskStatus}
        for task in self.tasks.values():
            status_counts[task.status.value] += 1

        return {
            "total_tasks": len(self.tasks),
            "status_counts": status_counts,
            "targets": {
                "ollama": {
                    "url": self.OLLAMA_URL,
                    "available_models": list(self.MODEL_ROUTING.values()),
                },
                "lm_studio": {
                    "url": self.LM_STUDIO_URL,
                },
                "chatdev": {
                    "available": True,
                },
                "copilot": {
                    "available": True,
                    "bridge_mode": os.getenv("NUSYQ_COPILOT_BRIDGE_MODE", "disabled"),
                    "endpoint": os.getenv("NUSYQ_COPILOT_BRIDGE_ENDPOINT", ""),
                },
            },
            "worker_running": self._running,
        }

    def get_queue_stats(self) -> dict:
        """Get queue statistics for monitoring.

        Returns:
            Dictionary with queued, running, completed, failed counts
        """
        stats = {"queued": 0, "running": 0, "completed": 0, "failed": 0}
        for task in self.tasks.values():
            if task.status == TaskStatus.QUEUED:
                stats["queued"] += 1
            elif task.status == TaskStatus.RUNNING:
                stats["running"] += 1
            elif task.status == TaskStatus.COMPLETED:
                stats["completed"] += 1
            elif task.status == TaskStatus.FAILED:
                stats["failed"] += 1
        return stats

    def _task_order_key(self, task: BackgroundTask) -> datetime:
        """Sort key for pruning: most recent lifecycle timestamp first."""
        return task.completed_at or task.started_at or task.created_at

    def prune_tasks(
        self,
        *,
        keep_completed: int = 250,
        keep_failed: int = 200,
        keep_cancelled: int = 200,
        stale_running_after_s: int = 3600,
        dry_run: bool = False,
    ) -> dict:
        """Prune stale/history tasks to keep orchestrator state actionable."""
        keep_completed = max(int(keep_completed), 0)
        keep_failed = max(int(keep_failed), 0)
        keep_cancelled = max(int(keep_cancelled), 0)
        stale_running_after_s = max(int(stale_running_after_s), 0)

        now = datetime.now(UTC)
        stale_cutoff = now - timedelta(seconds=stale_running_after_s)

        with self._lock:
            before_total = len(self.tasks)
            removed_task_ids: list[str] = []
            running_reconciled = 0

            for task in self.tasks.values():
                if task.status != TaskStatus.RUNNING:
                    continue
                if not task.started_at:
                    continue
                if task.started_at > stale_cutoff:
                    continue
                running_reconciled += 1
                if dry_run:
                    continue
                task.status = TaskStatus.FAILED
                task.completed_at = now
                if not task.error:
                    task.error = f"Reconciled stale running task during hygiene (threshold={stale_running_after_s}s)"

            plan = [
                (TaskStatus.COMPLETED, keep_completed),
                (TaskStatus.FAILED, keep_failed),
                (TaskStatus.CANCELLED, keep_cancelled),
            ]
            removed_by_status = {
                TaskStatus.COMPLETED.value: 0,
                TaskStatus.FAILED.value: 0,
                TaskStatus.CANCELLED.value: 0,
            }

            for status, keep_limit in plan:
                bucket = [task for task in self.tasks.values() if task.status == status]
                bucket.sort(key=self._task_order_key, reverse=True)
                to_remove = bucket[keep_limit:]
                removed_by_status[status.value] = len(to_remove)
                if dry_run:
                    continue
                for task in to_remove:
                    removed_task_ids.append(task.task_id)
                    self.tasks.pop(task.task_id, None)

            if (removed_task_ids or running_reconciled) and not dry_run:
                self._save_tasks(preserve_on_disk=False)

            after_total = (
                len(self.tasks) if not dry_run else before_total - sum(removed_by_status.values())
            )

        return {
            "status": "ok",
            "dry_run": dry_run,
            "before_total": before_total,
            "after_total": after_total,
            "removed_total": sum(removed_by_status.values()),
            "removed_by_status": removed_by_status,
            "running_reconciled": running_reconciled,
            "stale_running_after_s": stale_running_after_s,
            "retention": {
                "completed": keep_completed,
                "failed": keep_failed,
                "cancelled": keep_cancelled,
            },
            "removed_task_ids": removed_task_ids,
        }

    async def _ensure_phase3_initialized(self):
        """Initialize Phase 3 systems on first use (lazy loading)."""
        if self._phase3_initialized:
            return

        if PHASE3_AVAILABLE and Phase3Integration:
            try:
                self.phase3 = Phase3Integration(orchestrator=self)
                await self.phase3.integrate_all()
                self._phase3_initialized = True
                logger.info("✅ Phase 3 systems initialized")
            except Exception as e:
                logger.warning(f"Phase 3 initialization failed (using fallback): {e}")
                self.phase3 = None
                self._phase3_initialized = True  # Mark attempted to avoid retry loops
        else:
            logger.info("Phase 3 systems not available (using legacy mode)")
            self._phase3_initialized = True

    async def _ensure_culture_ship_initialized(self) -> None:
        """Initialize Culture Ship Strategic Advisor on first use (lazy loading)."""
        if self._culture_ship_initialized:
            return
        try:
            from src.orchestration.ecosystem_activator import \
                EcosystemActivator

            activator = EcosystemActivator()
            systems = activator.discover_systems()
            cs_def = next((s for s in systems if s.system_id == "culture_ship_advisor"), None)
            if cs_def and activator.activate_system(cs_def):
                self.culture_ship_advisor = cs_def.instance
                logger.info("✅ Culture Ship Strategic Advisor initialized")
            else:
                logger.info("Culture Ship advisor not available (continuing without it)")
        except Exception as e:
            logger.debug(f"Culture Ship initialization skipped: {e}")
        finally:
            self._culture_ship_initialized = True

    async def _ensure_consciousness_loop_initialized(self) -> None:
        """Initialize ConsciousnessLoop on first use (lazy loading)."""
        if self._consciousness_initialized:
            return
        self._consciousness_initialized = True
        try:
            from src.orchestration.consciousness_loop import ConsciousnessLoop

            loop = ConsciousnessLoop()
            loop.initialize()
            self._consciousness_loop = loop
        except Exception as exc:
            logger.debug("ConsciousnessLoop init skipped: %s", exc)

    def _get_adaptive_timeout(self, base: float) -> float:
        """Apply breathing factor to a timeout. Returns base when loop is down."""
        loop = self._consciousness_loop
        if loop is None:
            return base
        import time as _time

        # Use cached factor directly when still valid (avoids bridge I/O and
        # works even if bridge is temporarily unavailable).
        if _time.monotonic() < loop._factor_expires_at:
            return base * loop._cached_factor
        return base * loop.breathing_factor

    def _task_needs_approval(self, task) -> bool:
        """Return True if this task requires Culture Ship approval before execution."""
        # Future logic: check Security category, etc.
        return bool(task.metadata.get("requires_approval", False))

    async def _ensure_guild_board_initialized(self) -> None:
        """Initialize Guild Board logic on first use (lazy loading)."""
        if self._guild_board_initialized:
            return
        try:
            from src.guild.guild_board import GuildBoard

            self.guild_board = GuildBoard()
            logger.info("✅ Guild Board integration initialized")
            self._guild_board_initialized = True
        except Exception as e:
            logger.debug("Guild Board integration failed to initialize: %s", e)
            self._guild_board_initialized = True

    async def _heartbeat_loop(self) -> None:
        """Periodically pulses heartbeats for automated agents."""
        logger.info("💓 Background heartbeat loop started")
        while self._running:
            try:
                await self._ensure_guild_board_initialized()
                if self.guild_board and hasattr(self.guild_board, "auto_heartbeat_agents"):
                    agents = self.guild_board.auto_heartbeat_agents
                    if agents:
                        logger.debug("Sending %d heartbeats for automated agents", len(agents))
                        for agent_id in agents:
                            try:
                                await self.guild_board.agent_heartbeat(
                                    agent_id=agent_id,
                                    status=AgentStatus.IDLE,
                                    current_quest=None,
                                )
                            except Exception as agent_err:
                                logger.debug("Heartbeat failed for %s: %s", agent_id, agent_err)

                # Use a safe sleep that checks _running state
                # Heartbeat interval is typically 300s, let's pulse every 60s for responsiveness
                for _ in range(60):
                    if not self._running:
                        break
                    await asyncio.sleep(1)
            except Exception as e:
                logger.error("Error in heartbeat loop: %s", e)
                await asyncio.sleep(5)

    async def _is_security_task(self, task) -> bool:
        """Check if task is SECURITY category via the scheduler."""
        try:
            if self.phase3 and hasattr(self.phase3, "scheduler"):
                from src.orchestration.enhanced_task_scheduler import \
                    TaskCategory

                cat = self.phase3.scheduler.categorize_task(task)
                return cat == TaskCategory.SECURITY
        except Exception:
            logger.debug("Suppressed Exception", exc_info=True)
        return False

    async def start(self):
        """Start the background worker to process queued tasks."""
        if self._running:
            logger.info("Worker already running")
            return

        self._running = True
        logger.info("Starting background task worker...")

        # Initialize Phase 3 if available
        await self._ensure_phase3_initialized()

        # Initialize Culture Ship Strategic Advisor if available
        await self._ensure_culture_ship_initialized()

        # Initialize Consciousness Loop if available
        await self._ensure_consciousness_loop_initialized()

        # Start background heartbeat loop if initialized through this start call
        if not self._heartbeat_task:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        # Process queued tasks
        queued_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.QUEUED]

        # Use Phase 3 enhanced scheduler if available, otherwise fall back to priority sort
        if self.phase3 and hasattr(self.phase3, "enhanced_task_selection"):
            try:
                selected_tasks = await self.phase3.enhanced_task_selection(
                    queued_tasks, batch_size=len(queued_tasks)
                )
                queued_tasks = [t for t in selected_tasks if isinstance(t, BackgroundTask)]
                logger.info(f"🧠 Using Phase 3 enhanced task selection ({len(queued_tasks)} tasks)")
            except Exception as e:
                logger.warning(f"Enhanced scheduler failed (using fallback): {e}")
                # Fallback to priority sort
                queued_tasks.sort(
                    key=lambda t: t.priority.value,
                    reverse=True,
                )
        else:
            # Legacy: Sort by priority (higher values first)
            queued_tasks.sort(
                key=lambda t: t.priority.value,
                reverse=True,
            )

        completed_count = 0
        failed_count = 0

        for task in queued_tasks:
            if not self._running:
                break  # Stop requested

            try:
                logger.info(f"Executing task {task.task_id}")

                # Record task start to dashboard
                if self.phase3:
                    await self.phase3.record_task_execution(
                        task,
                        success=False,
                        duration_seconds=0,  # Will update on completion
                    )

                # Execute the task
                start_time = time.time()
                await self.execute_task(task)
                duration = time.time() - start_time

                # Record task completion to dashboard
                if self.phase3:
                    await self.phase3.record_task_execution(
                        task,
                        success=(task.status == TaskStatus.COMPLETED),
                        duration_seconds=duration,
                    )

                if task.status == TaskStatus.COMPLETED:
                    completed_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Task {task.task_id} failed: {e}")
                failed_count += 1

        self._running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        logger.info(f"Worker stopped. Completed: {completed_count}, Failed: {failed_count}")

    def stop(self):
        """Stop the background worker."""
        self._running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        logger.info("Stop requested for background worker")

    async def process_next_task(self) -> BackgroundTask | None:
        """Process the next queued task (one-shot execution)."""
        await self._ensure_phase3_initialized()

        queued_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.QUEUED]
        if not queued_tasks:
            return None

        # Use Phase 3 enhanced scheduler if available
        if self.phase3 and hasattr(self.phase3, "enhanced_task_selection"):
            try:
                selected = await self.phase3.enhanced_task_selection(queued_tasks, batch_size=1)
                task = (
                    selected[0]
                    if selected and isinstance(selected[0], BackgroundTask)
                    else queued_tasks[0]
                )
            except Exception as e:
                logger.warning(f"Enhanced scheduler failed (using fallback): {e}")
                # Fallback: Get highest priority task
                queued_tasks.sort(
                    key=lambda t: t.priority.value,
                    reverse=True,
                )
                task = queued_tasks[0]
        else:
            # Legacy: Get highest priority task
            queued_tasks.sort(
                key=lambda t: t.priority.value,
                reverse=True,
            )
            task = queued_tasks[0]

        start_time = time.time()
        await self.execute_task(task)
        duration = time.time() - start_time

        # Record to dashboard
        if self.phase3:
            await self.phase3.record_task_execution(
                task, success=(task.status == TaskStatus.COMPLETED), duration_seconds=duration
            )

        return task


# Singleton instance
_orchestrator: BackgroundTaskOrchestrator | None = None


def get_orchestrator() -> BackgroundTaskOrchestrator:
    """Get or create the singleton orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = BackgroundTaskOrchestrator()
    return _orchestrator


# CLI interface functions for start_nusyq.py integration
async def dispatch_task_cli(
    prompt: str,
    target: str = "auto",
    model: str | None = None,
    priority: str = "normal",
    agent: str = "claude",
    task_type: str = "general",
) -> dict:
    """CLI interface for dispatching tasks."""
    orchestrator = get_orchestrator()

    task = orchestrator.submit_task(
        prompt=prompt,
        target=TaskTarget(target),
        model=model,
        priority=TaskPriority[priority.upper()],
        requesting_agent=agent,
        task_type=task_type,
    )

    # Execute immediately (could be queued for background processing)
    result = await orchestrator.execute_task(task)

    return result.to_dict()


def task_status_cli(task_id: str) -> dict:
    """CLI interface for checking task status."""
    orchestrator = get_orchestrator()
    task = orchestrator.get_task(task_id)

    if task:
        return task.to_dict()
    return {"error": f"Task not found: {task_id}"}


def list_tasks_cli(status: str | None = None, limit: int = 20) -> list[dict]:
    """CLI interface for listing tasks."""
    orchestrator = get_orchestrator()

    task_status = TaskStatus(status) if status else None
    tasks = orchestrator.list_tasks(status=task_status, limit=limit)

    return [t.to_dict() for t in tasks]


def orchestrator_status_cli() -> dict:
    """CLI interface for orchestrator status."""
    return get_orchestrator().get_orchestrator_status()


def orchestrator_hygiene_cli(
    *,
    keep_completed: int = 250,
    keep_failed: int = 200,
    keep_cancelled: int = 200,
    stale_running_after_s: int = 3600,
    dry_run: bool = False,
) -> dict:
    """CLI interface for orchestrator queue hygiene pruning."""
    orchestrator = get_orchestrator()
    return orchestrator.prune_tasks(
        keep_completed=keep_completed,
        keep_failed=keep_failed,
        keep_cancelled=keep_cancelled,
        stale_running_after_s=stale_running_after_s,
        dry_run=dry_run,
    )


if __name__ == "__main__":
    # Quick test
    async def test():
        orchestrator = get_orchestrator()
        logger.info(
            "Orchestrator status:", json.dumps(orchestrator.get_orchestrator_status(), indent=2)
        )

        # Test task submission
        task = orchestrator.submit_task(
            prompt="Explain the concept of recursion in programming",
            target=TaskTarget.OLLAMA,
            model="phi3.5:latest",  # Use fast model for testing
            requesting_agent="test",
            task_type="general",
        )
        logger.info(f"Submitted task: {task.task_id}")

        # Execute
        result = await orchestrator.execute_task(task)
        logger.info(f"Result: {result.result[:200] if result.result else 'No result'}...")

    asyncio.run(test())
