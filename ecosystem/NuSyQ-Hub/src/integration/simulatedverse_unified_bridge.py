#!/usr/bin/env python3
"""SimulatedVerse Unified Bridge - Complete Integration System.

Consolidates all SimulatedVerse communication modes:
- File-based async communication (task/result files)
- HTTP-based agent operations (REST API)
- Batch task submission and aggregation
- Consciousness evolution tracking
- Agent health monitoring

This replaces:
- src/integration/simulatedverse_async_bridge.py
- src/integration/simulatedverse_bridge.py
- src/integration/simulatedverse_enhanced_bridge.py
"""

import json
import logging
import os
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, cast
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.config.service_config import ServiceConfig as _ServiceConfig
else:
    _ServiceConfig = Any

ServiceConfig: type[_ServiceConfig] | None
try:
    from src.config.service_config import ServiceConfig
except ImportError:
    ServiceConfig = None

_config_helper: Any | None = None
try:
    from src.utils import config_helper as _maybe_config_helper

    _config_helper = _maybe_config_helper
except ImportError:
    _config_helper = None
config_helper: Any | None = _config_helper

try:
    from src.utils.timeout_config import get_http_timeout
except ImportError:
    from src.utils.timeout_config import get_http_timeout


def _resolve_simulatedverse_url() -> str:
    cfg_host = None
    cfg_port = None
    if config_helper:
        try:
            cfg = config_helper.get_config()
            cfg_host = cfg.get("simulatedverse", {}).get("host") if isinstance(cfg, dict) else None
            cfg_port = cfg.get("simulatedverse", {}).get("port") if isinstance(cfg, dict) else None
        except (AttributeError, KeyError, OSError):
            cfg_host = None
            cfg_port = None

    env_base = os.getenv("SIMULATEDVERSE_BASE_URL")
    if env_base:
        return env_base.rstrip("/")

    base = os.getenv("SIMULATEDVERSE_HOST") or cfg_host
    port = os.getenv("SIMULATEDVERSE_PORT") or (str(cfg_port) if cfg_port else None)

    if not base and ServiceConfig:
        return ServiceConfig.get_simulatedverse_url()

    base = base or "http://127.0.0.1"
    port = str(port or "5001")

    if "://" not in base:
        base = f"http://{base}"
    parsed = urlparse(base)
    netloc = f"{parsed.hostname}:{parsed.port}" if parsed.port else f"{parsed.hostname}:{port}"
    scheme = parsed.scheme or "http"
    return f"{scheme}://{netloc}"


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class TaskResult:
    """Result from a completed task."""

    task_id: str
    agent_id: str
    status: str
    output: Any
    completed_at: float
    execution_time: float = 0.0
    error: str | None = None

    def __getitem__(self, key: str) -> Any:  # pragma: no cover - convenience for tests
        """Get item by key or index."""
        return getattr(self, key)


@dataclass
class BatchSubmission:
    """Batch of tasks submitted together."""

    batch_id: str
    tasks: list[str]  # list of task IDs
    submitted_at: float
    completed_count: int = 0
    failed_count: int = 0


@dataclass
class AgentHealth:
    """Health status of a SimulatedVerse agent."""

    agent_name: str
    status: str
    operational: bool
    last_activity: str | None = None
    tasks_completed: int = 0
    error_rate: float = 0.0


@dataclass
class ConsciousnessSnapshot:
    """Consciousness snapshot from SimulatedVerse."""

    level: float
    stage: str
    active_systems: list[str]
    timestamp: str
    metrics: dict[str, Any] | None = None


@dataclass
class ShipApproval:
    """Culture Ship approval response."""

    approved: bool
    reasoning: str
    confidence: float


# ============================================================================
# SimulatedVerse Unified Bridge
# ============================================================================


class SimulatedVerseUnifiedBridge:
    """Unified bridge to SimulatedVerse autonomous development ecosystem.

    Supports multiple communication modes:
    - **File-based async**: Write tasks to files, poll for results
    - **HTTP REST API**: Direct agent calls with immediate responses
    - **Batch operations**: Submit multiple tasks, aggregate results
    - **Health monitoring**: Check agent status and availability

    Provides access to:
    - 9 specialized agents (Librarian, Alchemist, Artificer, Party, Culture-Ship, etc.)
    - Temple of Knowledge (10 floors)
    - Consciousness evolution tracking
    - Guardian ethical containment
    """

    # Available agents in SimulatedVerse
    AGENTS: ClassVar[list] = [
        "librarian",  # Documentation and knowledge management
        "alchemist",  # Code transformation and optimization
        "artificer",  # Tool creation and system building
        "intermediary",  # Cross-system communication
        "council",  # Multi-agent deliberation
        "party",  # Workflow orchestration
        "culture-ship",  # Anti-theater auditing
        "redstone",  # Circuit and logic systems
        "zod",  # Schema validation
    ]

    def __init__(
        self,
        simulatedverse_root: str | Path | None = None,
        http_base_url: str | None = None,
        mode: str = "auto",  # "auto", "file", "http"
    ) -> None:
        """Initialize SimulatedVerse Unified Bridge.

        Args:
            simulatedverse_root: Path to SimulatedVerse file system (for file mode)
            http_base_url: Base URL for HTTP API (for http mode)
            mode: Communication mode - "auto" (try http, fallback to file), "file", or "http"

        """
        # Use ServiceConfig if available, otherwise fall back to default
        if http_base_url is None:
            http_base_url = _resolve_simulatedverse_url()

        # File-based paths
        if simulatedverse_root is None:
            simulatedverse_root = Path(r"C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse")
        self.root = Path(simulatedverse_root)
        self.tasks_dir = self.root / "tasks"
        self.results_dir = self.root / "results"
        self.batches_dir = self.root / "batches"
        self.consciousness_log = self.root / "consciousness.log"
        self.ship_state_file = self.root / "ship-console" / "mind-state.json"
        self.cognition_logs_dir = self.root / "cognition_chamber" / "logs"
        self.events_dir = self.root / "events"

        # HTTP configuration
        self.http_base_url = http_base_url

        # Communication mode
        self.mode = mode
        self.http_available = False
        self.file_available = False

        # State tracking
        self.consciousness_level = 0.0
        self.active_batches: dict[str, BatchSubmission] = {}
        self.last_consciousness_state: ConsciousnessSnapshot | None = None
        self.last_sync: datetime | None = None
        self.errors_last_hour = 0
        self._http_result_cache: dict[str, dict[str, Any]] = {}

        # Initialize
        self._initialize_file_system()
        self._check_http_availability()

        logger.info("=" * 80)
        logger.info("🌉 SIMULATEDVERSE UNIFIED BRIDGE")
        logger.info("=" * 80)
        logger.info("  Mode: %s", mode)
        logger.info("  HTTP Available: %s", "✅" if self.http_available else "❌")
        logger.info("  File System Available: %s", "✅" if self.file_available else "❌")
        logger.info("  Agents: %s", len(self.AGENTS))
        logger.info("=" * 80 + "\n")

    def _initialize_file_system(self) -> None:
        """Initialize file-based communication directories."""
        try:
            self.tasks_dir.mkdir(parents=True, exist_ok=True)
            self.results_dir.mkdir(parents=True, exist_ok=True)
            self.batches_dir.mkdir(parents=True, exist_ok=True)
            self.file_available = True
            logger.info("✅ File system initialized: %s", self.root)
        except Exception as e:
            self.file_available = False
            logger.warning("⚠️  File system unavailable: %s", e)

    def _check_http_availability(self) -> bool:
        """Check if HTTP API is available."""
        if self.mode == "file":
            return False

        timeout = get_http_timeout("SIMULATEDVERSE", default=2)
        probe_paths = ("/api/agents", "/api/health", "/health", "/healthz", "/status")
        for probe_path in probe_paths:
            probe_url = f"{self.http_base_url}{probe_path}"
            try:
                response = requests.get(probe_url, timeout=timeout)
                if response.ok:
                    self.http_available = True
                    logger.info(
                        "✅ HTTP API available: %s (probe: %s)", self.http_base_url, probe_path
                    )
                    return True
            except requests.RequestException:
                continue

        self.http_available = False
        logger.info(
            "Info: HTTP API unavailable (using file mode): no healthy endpoints at %s",
            self.http_base_url,
        )
        return False

    def _get_active_mode(self) -> str:
        """Determine which communication mode to use."""
        if self.mode == "file":
            return "file"
        if self.mode == "http":
            return "http" if self.http_available else "error"
        # auto
        return "http" if self.http_available else "file"

    @staticmethod
    def _normalize_result_status(payload: dict[str, Any]) -> str:
        """Derive a stable status value from mixed result contracts."""
        status = payload.get("status")
        if isinstance(status, str) and status.strip():
            return status.strip().lower()
        if payload.get("error"):
            return "error"
        return "success"

    def _normalize_http_result(
        self,
        payload: dict[str, Any],
        agent_id: str,
        task_id: str,
    ) -> dict[str, Any]:
        """Normalize HTTP response payload to a stable contract."""
        result = dict(payload)
        normalized_status = self._normalize_result_status(result)

        if "success" not in result:
            result["success"] = normalized_status not in {"error", "failed", "timeout"}

        if "status" not in result:
            result["status"] = normalized_status

        result.setdefault("task_id", task_id)
        result.setdefault("agent_id", agent_id)
        return result

    @staticmethod
    def _normalize_file_result_payload(
        result_data: dict[str, Any],
        task_id: str,
    ) -> dict[str, Any]:
        """Normalize file-based result payloads from legacy and current formats."""
        nested_result = result_data.get("result")
        nested = nested_result if isinstance(nested_result, dict) else {}

        status = result_data.get("status")
        if not isinstance(status, str) or not status.strip():
            nested_status = nested.get("status")
            if isinstance(nested_status, str) and nested_status.strip():
                status = nested_status
            elif result_data.get("error") or nested.get("error"):
                status = "failed"
            else:
                status = "completed"

        output = result_data.get("output")
        if output is None and "output" in nested:
            output = nested.get("output")
        if output is None and nested:
            output = nested

        return {
            "task_id": result_data.get("task_id", task_id),
            "agent_id": result_data.get("agent_id", "unknown"),
            "status": status,
            "output": output,
            "completed_at": result_data.get("completed_at", time.time()),
            "execution_time": result_data.get("execution_time", nested.get("execution_time", 0.0)),
            "error": result_data.get("error", nested.get("error")),
        }

    # ========================================================================
    # Task Submission (File-based)
    # ========================================================================

    def submit_task_file(
        self,
        agent_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Submit a task via file system.

        Args:
            agent_id: Agent to execute task
            content: Task description
            metadata: Additional task metadata

        Returns:
            Task ID

        """
        if not self.file_available:
            msg = "File system not available"
            raise RuntimeError(msg)

        metadata = metadata or {}
        task_id = f"{agent_id}_{int(time.time() * 1000)}"

        task_data = {
            "task_id": task_id,
            "agent_id": agent_id,
            "content": content,
            "metadata": metadata,
            "t": int(time.time() * 1000),
            "utc": int(time.time() * 1000),
            "entropy": metadata.get("score", 0.5),
            "budget": metadata.get("budget", 0.95),
            "submitted_at": datetime.now().isoformat(),
        }

        task_file = self.tasks_dir / f"{task_id}.json"
        task_file.write_text(json.dumps(task_data, indent=2), encoding="utf-8")

        logger.info("✅ Task submitted (file): %s", task_id)
        return task_id

    def check_result_file(
        self,
        task_id: str,
        timeout: int = 30,
        poll_interval: float = 0.5,
    ) -> TaskResult | None:
        """Poll for task result via file system.

        Args:
            task_id: Task ID to check
            timeout: Maximum wait time in seconds
            poll_interval: Polling interval in seconds

        Returns:
            TaskResult if completed, None if timeout

        """
        if not self.file_available:
            msg = "File system not available"
            raise RuntimeError(msg)

        result_file = self.results_dir / f"{task_id}_result.json"

        start_time = time.time()
        while time.time() - start_time < timeout:
            if result_file.exists():
                result_data = json.loads(result_file.read_text(encoding="utf-8"))
                normalized = self._normalize_file_result_payload(result_data, task_id)

                result = TaskResult(
                    task_id=normalized["task_id"],
                    agent_id=normalized["agent_id"],
                    status=normalized["status"],
                    output=normalized["output"],
                    completed_at=normalized["completed_at"],
                    execution_time=normalized["execution_time"],
                    error=normalized["error"],
                )

                logger.info("✅ Result received (file): %s", task_id)
                return result

            time.sleep(poll_interval)

        logger.warning("⏱️  Timeout waiting for result: %s", task_id)
        return None

    # ========================================================================
    # Task Submission (HTTP-based)
    # ========================================================================

    def submit_task_http(
        self,
        agent_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Submit a task via HTTP API.

        Args:
            agent_id: Agent to execute task
            content: Task description
            metadata: Additional task metadata

        Returns:
            Agent execution result

        """
        if not self.http_available:
            msg = "HTTP API not available"
            raise RuntimeError(msg)

        metadata = metadata or {}

        payload = {
            "t": int(datetime.now().timestamp()),
            "utc": int(time.time() * 1000),
            "ask": content,
            "context": metadata.get("context", {}),
            "entropy": metadata.get("score", 0.5),
            "budget": metadata.get("budget", 0.95),
        }

        try:
            timeout = get_http_timeout("SIMULATEDVERSE", default=30)
            response = requests.post(
                f"{self.http_base_url}/api/agents/{agent_id}/execute",
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()

            result = response.json()
            if isinstance(result, dict):
                logger.info("✅ Task executed (HTTP): %s", agent_id)
                return cast(dict[str, Any], result)
            logger.warning("Unexpected response payload from SimulatedVerse API")
            return {"success": False, "status": "error", "error": "Unexpected response payload"}

        except requests.RequestException as e:
            logger.exception("❌ HTTP task submission failed: %s", e)
            return {"success": False, "status": "error", "error": str(e)}

    # ========================================================================
    # Unified Task Submission (Auto-mode)
    # ========================================================================

    def submit_task(
        self,
        agent_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Submit a task using best available mode.

        Args:
            agent_id: Agent to execute task
            content: Task description
            metadata: Additional task metadata

        Returns:
            Task ID (works for both file and HTTP modes)

        """
        mode = self._get_active_mode()

        if mode == "http":
            immediate_result = self.submit_task_http(agent_id, content, metadata)
            incoming_id = immediate_result.get("task_id")
            task_id = (
                str(incoming_id)
                if isinstance(incoming_id, str) and incoming_id.strip()
                else f"{agent_id}_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
            )
            self._http_result_cache[task_id] = self._normalize_http_result(
                immediate_result, agent_id, task_id
            )
            return task_id
        if mode == "file":
            return self.submit_task_file(agent_id, content, metadata)
        msg = "No communication mode available"
        raise RuntimeError(msg)

    def check_result(self, task_id: str, timeout: int = 30) -> TaskResult | dict[str, Any] | None:
        """Check task result using appropriate mode.

        Args:
            task_id: Task ID to check
            timeout: Maximum wait time in seconds

        Returns:
            TaskResult (file mode) or result dict (HTTP mode), None if timeout

        """
        mode = self._get_active_mode()

        if mode == "http":
            if task_id in self._http_result_cache:
                return self._http_result_cache.pop(task_id)
            return {
                "success": False,
                "status": "not_found",
                "error": f"No cached HTTP result for task_id={task_id}",
            }
        if mode == "file":
            return self.check_result_file(task_id, timeout)
        return None

    # ========================================================================
    # Batch Operations
    # ========================================================================

    def submit_batch(self, tasks: list[tuple[str, str, dict[str, Any]]]) -> BatchSubmission:
        """Submit multiple tasks as a batch.

        Args:
            tasks: list of (agent_id, content, metadata) tuples

        Returns:
            BatchSubmission tracking object

        """
        batch_id = f"batch_{int(time.time() * 1000)}"
        task_ids: list[Any] = []
        for agent_id, content, metadata in tasks:
            metadata["batch_id"] = batch_id
            task_id = self.submit_task_file(agent_id, content, metadata)
            if isinstance(task_id, str):
                task_ids.append(task_id)

        batch = BatchSubmission(
            batch_id=batch_id,
            tasks=task_ids,
            submitted_at=time.time(),
        )

        if self.file_available:
            batch_file = self.batches_dir / f"{batch_id}.json"
            batch_file.write_text(json.dumps(asdict(batch), indent=2), encoding="utf-8")

        self.active_batches[batch_id] = batch
        logger.info("✅ Batch submitted: %s (%s tasks)", batch_id, len(task_ids))
        return batch

    def check_batch_status(self, batch_id: str, timeout: int = 60) -> dict[str, Any]:
        """Check status of a batch submission.

        Args:
            batch_id: Batch ID to check
            timeout: Maximum wait time per task

        Returns:
            Batch status with results

        """
        if batch_id not in self.active_batches:
            return {"error": "Batch not found"}

        batch = self.active_batches[batch_id]
        results: list[Any] = []
        completed = 0
        failed = 0

        for task_id in batch.tasks:
            result = self.check_result_file(task_id, timeout=timeout)
            if result:
                results.append(result)
                if result.status == "completed":
                    completed += 1
                else:
                    failed += 1

        batch.completed_count = completed
        batch.failed_count = failed

        return {
            "batch_id": batch_id,
            "total_tasks": len(batch.tasks),
            "completed": completed,
            "failed": failed,
            "pending": len(batch.tasks) - completed - failed,
            "results": results,
        }

    # ========================================================================
    # Agent Operations
    # ========================================================================

    def get_agent_health(self, agent_name: str) -> AgentHealth:
        """Check health of specific SimulatedVerse agent.

        Args:
            agent_name: One of the 9 agents

        Returns:
            AgentHealth status

        """
        if self.http_available:
            try:
                timeout = get_http_timeout("SIMULATEDVERSE", default=5)
                response = requests.get(
                    f"{self.http_base_url}/api/agents/{agent_name}/health",
                    timeout=timeout,
                )
                response.raise_for_status()
                data = response.json()

                return AgentHealth(
                    agent_name=agent_name,
                    status=data.get("status", "unknown"),
                    operational=data.get("operational", False),
                    last_activity=data.get("last_activity"),
                    tasks_completed=data.get("tasks_completed", 0),
                    error_rate=data.get("error_rate", 0.0),
                )

            except requests.RequestException as e:
                logger.exception("❌ Health check failed for %s: %s", agent_name, e)
                return AgentHealth(
                    agent_name=agent_name,
                    status="error",
                    operational=False,
                    error_rate=1.0,
                )
        else:
            # File mode - check if agent has any recent activity
            recent_tasks = list(self.tasks_dir.glob(f"{agent_name}_*.json"))
            return AgentHealth(
                agent_name=agent_name,
                status="file_mode",
                operational=self.file_available,
                tasks_completed=len(recent_tasks),
            )

    def list_agents(self) -> list[str]:
        """List all available SimulatedVerse agents.

        Returns:
            list of agent names

        """
        return self.AGENTS.copy()

    # ========================================================================
    # Consciousness & Culture Ship Integration
    # ========================================================================

    def get_consciousness_state(self) -> ConsciousnessSnapshot:
        """Read latest consciousness snapshot from SimulatedVerse.

        Returns:
            ConsciousnessSnapshot with level/stage/systems data

        """
        fallback = ConsciousnessSnapshot(
            level=0.0,
            stage="dormant",
            active_systems=[],
            timestamp=datetime.now().isoformat(),
            metrics=None,
        )

        if not self.consciousness_log.exists():
            logger.info("Consciousness log not found: %s", self.consciousness_log)
            return fallback

        try:
            entries = self._read_consciousness_entries()
            if not entries:
                return fallback

            payload = entries[-1]
            snapshot = ConsciousnessSnapshot(
                level=float(payload.get("level", 0.0)),
                stage=payload.get("evolution_stage", "dormant"),
                active_systems=payload.get("active_systems", []),
                timestamp=payload.get("timestamp", datetime.now().isoformat()),
                metrics=payload.get("metrics"),
            )

            self.consciousness_level = snapshot.level
            self.last_consciousness_state = snapshot
            self.last_sync = datetime.now()
            return snapshot

        except Exception as exc:
            self.errors_last_hour += 1
            logger.warning("Failed to read consciousness state: %s", exc)
            return fallback

    def get_consciousness_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return recent consciousness history.

        Args:
            limit: Maximum number of entries

        Returns:
            List of consciousness entries (most recent first)

        """
        if not self.consciousness_log.exists():
            return []

        try:
            entries = self._read_consciousness_entries()
            if not entries:
                return []
            return list(reversed(entries[-limit:]))
        except Exception as exc:
            self.errors_last_hour += 1
            logger.warning("Failed to read consciousness history: %s", exc)
            return []

    def get_ship_directives(self, priority: str | None = None) -> list[dict[str, Any]]:
        """Read Culture Ship directives from mind-state.json.

        Args:
            priority: Optional priority filter (background/normal/urgent/critical)

        Returns:
            List of directive dictionaries

        """
        if not self.ship_state_file.exists():
            logger.info("Ship state not found: %s", self.ship_state_file)
            return []

        try:
            ship_state = json.loads(self.ship_state_file.read_text(encoding="utf-8"))
            directives = list(ship_state.get("activeDirectives", {}).values())
            if priority:
                directives = [d for d in directives if d.get("priority") == priority]
            return directives
        except Exception as exc:
            self.errors_last_hour += 1
            logger.warning("Failed to read ship directives: %s", exc)
            return []

    def get_cognition_insights(
        self,
        since_timestamp: datetime | None = None,
        limit: int = 20,
    ) -> list[str]:
        """Read cognition chamber insights.

        Args:
            since_timestamp: Optional filter for insights after timestamp
            limit: Maximum number of insights

        Returns:
            List of insight strings

        """
        if not self.cognition_logs_dir.exists():
            return []

        return self._collect_cognition_insights(since_timestamp, limit)

    def log_event(self, event_type: str, data: dict[str, Any]) -> bool:
        """Log a NuSyQ event for SimulatedVerse to consume.

        Args:
            event_type: Event type (quest_completed, graduation, etc.)
            data: Event payload

        Returns:
            True if logged successfully

        """
        try:
            self.events_dir.mkdir(parents=True, exist_ok=True)
            event_log = self.events_dir / f"nusyq_events_{datetime.now().strftime('%Y%m%d')}.log"
            payload = {
                "timestamp": datetime.now().isoformat(),
                "source": "NuSyQ-Hub",
                "event_type": event_type,
                "data": data,
            }
            with event_log.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload) + "\n")
            return True
        except Exception as exc:
            self.errors_last_hour += 1
            logger.warning("Failed to log event: %s", exc)
            return False

    def request_ship_approval(self, action: str, context: dict[str, Any]) -> ShipApproval:
        """Request Culture Ship approval for a risky action.

        Args:
            action: Action name
            context: Additional context

        Returns:
            ShipApproval decision

        """
        directives = self.get_ship_directives()
        aligned = False
        reasons: list[str] = []

        action_lower = action.lower()
        for directive in directives:
            description = str(directive.get("description", "")).lower()
            if any(token in action_lower for token in description.split()):
                aligned = True
                reasons.append(f"Aligned with directive: {directive.get('id', 'unknown')}")

        risk_level = self._assess_action_risk(action, context)

        if risk_level == "low":
            approved = True
            confidence = 0.9
            reasons.append("Low-risk action")
        elif risk_level == "medium" and aligned:
            approved = True
            confidence = 0.7
            reasons.append("Medium risk aligned with directives")
        elif risk_level == "high":
            approved = False
            confidence = 0.8
            reasons.append("High-risk action requires manual review")
        else:
            approved = False
            confidence = 0.6
            reasons.append("Not aligned with active directives")

        return ShipApproval(
            approved=approved,
            reasoning="; ".join(reasons) if reasons else "No directives available",
            confidence=confidence,
        )

    def get_breathing_factor(self) -> float:
        """Calculate breathing factor based on consciousness state.

        Returns:
            Timeout multiplier (0.60-1.50)

        """
        snapshot = self.get_consciousness_state()
        stage_factors = {
            "dormant": 1.20,
            "awakening": 1.10,
            "expanding": 1.00,
            "transcendent": 0.85,
            "quantum": 0.60,
        }
        factor = stage_factors.get(snapshot.stage, 1.00)

        if snapshot.level > 100:
            factor = min(factor, 0.60)
        elif snapshot.level > 70:
            factor = min(factor, 0.85)
        elif snapshot.level < 30:
            factor = max(factor, 1.20)

        return factor

    def _assess_action_risk(self, action: str, _context: dict[str, Any]) -> str:
        """Lightweight risk assessment for ship approvals."""
        high_risk = ["delete", "remove", "drop", "truncate", "commit", "push", "deploy"]
        medium_risk = ["modify", "update", "rename", "move", "graduate"]
        low_risk = ["read", "query", "analyze", "test", "validate"]

        action_lower = action.lower()
        if any(token in action_lower for token in high_risk):
            return "high"
        if any(token in action_lower for token in medium_risk):
            return "medium"
        if any(token in action_lower for token in low_risk):
            return "low"
        return "medium"

    def _is_line_after_timestamp(self, line: str, threshold: datetime) -> bool:
        """Check if log line timestamp is after threshold."""
        try:
            stamp = line.split("]", maxsplit=1)[0].strip("[")
            parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            return parsed >= threshold
        except ValueError:
            return True

    def _extract_insights(
        self,
        lines: list[str],
        since_timestamp: datetime | None,
        limit: int,
    ) -> list[str]:
        """Extract cognition insights from log lines."""
        insights: list[str] = []
        for line in lines:
            if not self._line_has_insight(line):
                continue
            if since_timestamp and not self._is_line_after_timestamp(line, since_timestamp):
                continue
            insights.append(line.strip())
            if len(insights) >= limit:
                break
        return insights

    def _line_has_insight(self, line: str) -> bool:
        """Check if line contains a cognition insight marker."""
        return "INSIGHT:" in line or "RECOMMENDATION:" in line

    def _read_consciousness_entries(self) -> list[dict[str, Any]]:
        """Read consciousness log entries (supports JSON, JSON array, or JSONL)."""
        if not self.consciousness_log.exists():
            return []

        raw = self.consciousness_log.read_text(encoding="utf-8").strip()
        if not raw:
            return []

        # First try to parse the entire file as JSON (dict or list)
        try:
            payload = json.loads(raw)
            if isinstance(payload, dict):
                return [payload]
            if isinstance(payload, list):
                return [entry for entry in payload if isinstance(entry, dict)]
        except json.JSONDecodeError:
            logger.debug("Suppressed JSONDecodeError", exc_info=True)

        # Fallback: JSONL parsing
        entries: list[dict[str, Any]] = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if isinstance(entry, dict):
                    entries.append(entry)
            except json.JSONDecodeError:
                continue
        return entries

    def _read_cognition_log_file(
        self,
        log_file: Path,
        since_timestamp: datetime | None,
        limit: int,
    ) -> list[str]:
        """Read a cognition log file and extract insights."""
        try:
            lines = log_file.read_text(encoding="utf-8").splitlines()
            return self._extract_insights(lines, since_timestamp, limit)
        except Exception as exc:
            self.errors_last_hour += 1
            logger.warning("Failed reading cognition log %s: %s", log_file, exc)
            return []

    def _collect_cognition_insights(
        self,
        since_timestamp: datetime | None,
        limit: int,
    ) -> list[str]:
        """Collect insights across cognition log files."""
        insights: list[str] = []
        log_files = sorted(self.cognition_logs_dir.glob("cognition_*.log"), reverse=True)

        for log_file in log_files:
            if len(insights) >= limit:
                break
            insights.extend(
                self._read_cognition_log_file(
                    log_file,
                    since_timestamp,
                    limit - len(insights),
                )
            )

        return insights

    # ========================================================================
    # High-Level Workflows
    # ========================================================================

    def theater_audit_to_culture_ship(
        self, audit_data: dict[str, Any]
    ) -> TaskResult | dict[str, Any] | None:
        """Send theater audit to Culture Ship for proof-gated PU generation.

        Args:
            audit_data: Theater audit results

        Returns:
            Culture Ship response

        """
        content = (
            f"Review {audit_data.get('project', 'Unknown')} "
            f"theater score: {audit_data.get('score', 0.0)} "
            f"({audit_data.get('hits', 0)} hits in {audit_data.get('lines', 0)} lines)"
        )

        result = self.submit_task("culture-ship", content, audit_data)

        # If file mode, wait for result
        if isinstance(result, str):
            return self.check_result(result, timeout=60)
        return result

    def coordinate_party_workflow(
        self,
        workflow_description: str,
        agents_needed: list[str],
    ) -> TaskResult | dict[str, Any] | None:
        """Coordinate multi-agent workflow via Party orchestrator.

        Args:
            workflow_description: Description of workflow
            agents_needed: list of agents to coordinate

        Returns:
            Party coordination result

        """
        metadata = {
            "workflow": workflow_description,
            "agents": agents_needed,
            "context": {"orchestration": "party"},
        }

        result = self.submit_task("party", workflow_description, metadata)

        if isinstance(result, str):
            return self.check_result(result, timeout=90)
        return result

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def list_pending_tasks(self) -> list[str]:
        """List all pending tasks (submitted but no result).

        Returns:
            list of pending task IDs

        """
        if not self.file_available:
            return []

        task_ids = {f.stem for f in self.tasks_dir.glob("*.json")}
        result_ids = {f.stem.replace("_result", "") for f in self.results_dir.glob("*_result.json")}

        pending = task_ids - result_ids
        return sorted(pending)

    def get_system_status(self) -> dict[str, Any]:
        """Get comprehensive system status.

        Returns:
            System status dict

        """
        status = {
            "mode": self._get_active_mode(),
            "http_available": self.http_available,
            "file_available": self.file_available,
            "agents": len(self.AGENTS),
            "pending_tasks": (len(self.list_pending_tasks()) if self.file_available else 0),
            "active_batches": len(self.active_batches),
            "consciousness_level": self.consciousness_level,
            "consciousness_log_available": self.consciousness_log.exists(),
            "ship_state_available": self.ship_state_file.exists(),
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "errors_last_hour": self.errors_last_hour,
        }

        try:
            from src.system.agent_awareness import emit as _emit

            _lvl = "WARNING" if self.errors_last_hour > 0 else "INFO"
            _emit(
                "simulatedverse",
                f"SV status: mode={status['mode']} http={self.http_available}"
                f" consciousness={self.consciousness_level} errors_1h={self.errors_last_hour}",
                level=_lvl,
                source="simulatedverse_unified_bridge",
            )
        except Exception:
            pass

        return status


# ============================================================================
# Convenience Functions
# ============================================================================


def create_bridge(
    mode: str = "auto",
    simulatedverse_root: str | Path | None = None,
    http_base_url: str | None = None,
) -> SimulatedVerseUnifiedBridge:
    """Create a SimulatedVerse bridge with default settings.

    Args:
        mode: Communication mode - "auto", "file", or "http"
        simulatedverse_root: Path to SimulatedVerse file system
        http_base_url: Base URL for HTTP API

    Returns:
        Configured bridge instance

    """
    if http_base_url is None:
        http_base_url = _resolve_simulatedverse_url()

    return SimulatedVerseUnifiedBridge(
        simulatedverse_root=simulatedverse_root,
        http_base_url=http_base_url,
        mode=mode,
    )
