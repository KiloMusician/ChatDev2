"""Checkpoint/Retry/Degraded-Mode Framework for Phase 8 Resilience.

Goals:
    1. Capture execution state at safe checkpoints (pre-model call, pre-write)
    2. Enable retry with exponential backoff for transient failures
    3. Provide degraded-mode fallbacks when primary path fails
    4. Emit telemetry for each state transition
    5. Integrate with ArtifactManager for reproducibility

Design (Phase 8):
    - CheckpointState: Savepoint with hash/deps/metadata
    - RetryPolicy: Backoff, max attempts, jitter options
    - DegradedMode: Fallback executor (reduced scope, local-only, etc)
    - ExecutionContext: Wraps action with checkpoint/retry/degraded
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ExecutionMode(Enum):
    """Execution mode for an action."""

    PRIMARY = "primary"
    DEGRADED = "degraded"
    OFFLINE = "offline"


class FailureReason(Enum):
    """Categorized failure reasons."""

    TRANSIENT_NETWORK = "transient_network"
    TRANSIENT_TIMEOUT = "transient_timeout"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    PERMANENT_ERROR = "permanent_error"
    UNKNOWN = "unknown"


@dataclass
class CheckpointState:
    """Savepoint before a risky operation (model call, file write, etc)."""

    checkpoint_id: str
    timestamp: str  # ISO 8601
    operation: str  # e.g., "chatdev_generate", "ollama_call", "file_commit"
    context: dict = field(default_factory=dict)  # State snapshot
    dependencies: list = field(default_factory=list)  # File hashes, env vars
    metadata: dict = field(default_factory=dict)  # Custom metadata
    state_hash: str = ""  # SHA256 of context + deps (computed on init)

    def __post_init__(self) -> None:
        """Compute state hash for validation."""
        hashable = json.dumps(
            {
                "context": self.context,
                "dependencies": sorted(self.dependencies),
                "operation": self.operation,
            },
            sort_keys=True,
            default=str,
        )
        self.state_hash = hashlib.sha256(hashable.encode()).hexdigest()

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return asdict(self)


@dataclass
class RetryPolicy:
    """Policy for retrying failed operations."""

    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: bool = True
    retryable_reasons: list = field(
        default_factory=lambda: [
            FailureReason.TRANSIENT_NETWORK,
            FailureReason.TRANSIENT_TIMEOUT,
            FailureReason.RESOURCE_EXHAUSTED,
        ]
    )

    def compute_delay(self, attempt: int) -> float:
        """Compute delay for given attempt (0-indexed)."""
        delay = self.initial_delay * (self.backoff_factor**attempt)
        delay = min(delay, self.max_delay)
        if self.jitter:
            import random

            delay *= 0.5 + random.random()
        return delay

    def should_retry(self, failure: FailureReason, attempt: int) -> bool:
        """Determine if we should retry based on failure and attempt count."""
        return failure in self.retryable_reasons and attempt < self.max_attempts


@dataclass
class DegradedModeConfig:
    """Configuration for degraded-mode execution."""

    enabled: bool = True
    use_cached_models: bool = True
    reduce_scope: bool = True
    local_only: bool = True
    timeout: float = 30.0
    fallback_model: str | None = "phi:latest"  # Smaller local model
    response_size_limit: int = 2000  # chars


@dataclass
class ExecutionResult:
    """Result of an operation (primary, degraded, or failed)."""

    success: bool
    mode: ExecutionMode
    output: Any = None
    error: str | None = None
    failure_reason: FailureReason | None = None
    attempt: int = 1
    total_attempts: int = 1
    execution_time: float = 0.0
    checkpoint_id: str | None = None
    fallback_applied: bool = False


class CheckpointManager:
    """Manages creation/restoration of checkpoints."""

    def __init__(self, checkpoint_root: Path | str = "state/checkpoints"):
        """Initialize CheckpointManager with checkpoint_root."""
        self.root = Path(checkpoint_root)
        self.root.mkdir(parents=True, exist_ok=True)

    def create(
        self,
        operation: str,
        context: dict,
        dependencies: list | None = None,
        metadata: dict | None = None,
    ) -> CheckpointState:
        """Create and persist a checkpoint."""
        checkpoint = CheckpointState(
            checkpoint_id=str(uuid.uuid4()),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            operation=operation,
            context=context,
            dependencies=dependencies or [],
            metadata=metadata or {},
        )
        checkpoint_file = self.root / f"{checkpoint.checkpoint_id}.json"
        checkpoint_file.write_text(json.dumps(checkpoint.to_dict(), indent=2, default=str))
        logger.info(f"Checkpoint created: {checkpoint.checkpoint_id} for {operation}")
        return checkpoint

    def restore(self, checkpoint_id: str) -> CheckpointState | None:
        """Load checkpoint from disk."""
        checkpoint_file = self.root / f"{checkpoint_id}.json"
        if not checkpoint_file.exists():
            return None
        data = json.loads(checkpoint_file.read_text())
        return CheckpointState(**data)

    def cleanup_old(self, keep_count: int = 20) -> None:
        """Remove old checkpoints, keeping only most recent."""
        checkpoints = sorted(self.root.glob("*.json"), key=lambda x: x.stat().st_mtime)
        for old in checkpoints[:-keep_count]:
            old.unlink()


class ExecutionContext:
    """Wraps an action with checkpoint/retry/degraded-mode support."""

    def __init__(
        self,
        operation: str,
        retry_policy: RetryPolicy | None = None,
        degraded_config: DegradedModeConfig | None = None,
        checkpoint_manager: CheckpointManager | None = None,
    ):
        """Initialize ExecutionContext with operation, retry_policy, degraded_config, ...."""
        self.operation = operation
        self.retry_policy = retry_policy or RetryPolicy()
        self.degraded_config = degraded_config or DegradedModeConfig()
        self.checkpoint_manager = checkpoint_manager or CheckpointManager()
        self.execution_id = str(uuid.uuid4())

    async def execute(
        self,
        primary_fn: Callable[..., T],
        primary_args: dict | None = None,
        degraded_fn: Callable[..., T] | None = None,
        degraded_args: dict | None = None,
        context: dict | None = None,
        dependencies: list | None = None,
    ) -> ExecutionResult:
        """Execute operation with retry and degraded-mode fallback.

        Args:
            primary_fn: Main operation
            primary_args: Args for primary_fn
            degraded_fn: Fallback operation (if primary fails)
            degraded_args: Args for degraded_fn
            context: State snapshot to checkpoint
            dependencies: Files/hashes to track

        Returns:
            ExecutionResult with success, mode, output, error details
        """
        primary_args = primary_args or {}
        degraded_args = degraded_args or {}
        context = context or {}
        dependencies = dependencies or []

        # Create checkpoint before attempting
        checkpoint = self.checkpoint_manager.create(
            operation=self.operation,
            context=context,
            dependencies=dependencies,
            metadata={"execution_id": self.execution_id},
        )

        start_time = time.time()

        # Try primary mode with retries
        result = await self._try_primary_mode(primary_fn, primary_args, checkpoint, start_time)
        if result:
            return result

        # If primary failed, try degraded mode
        if self.degraded_config.enabled and degraded_fn:
            result = await self._try_degraded_mode(
                degraded_fn, degraded_args, checkpoint, start_time
            )
            if result:
                return result

        # All modes failed - return offline result
        return self._return_offline_result(checkpoint, start_time)

    async def _try_primary_mode(
        self,
        primary_fn: Callable[..., T],
        primary_args: dict,
        checkpoint: Any,
        start_time: float,
    ) -> ExecutionResult | None:
        """Try primary mode with retry logic."""
        attempt = 0
        last_failure_reason: FailureReason | None = None

        while attempt < self.retry_policy.max_attempts:
            attempt += 1
            try:
                logger.info(
                    f"[{self.execution_id}] Attempt {attempt}/{self.retry_policy.max_attempts}: "
                    f"{self.operation} (mode=primary)"
                )
                result = await self._call_async(primary_fn, primary_args)
                execution_time = time.time() - start_time
                return ExecutionResult(
                    success=True,
                    mode=ExecutionMode.PRIMARY,
                    output=result,
                    attempt=attempt,
                    total_attempts=attempt,
                    execution_time=execution_time,
                    checkpoint_id=checkpoint.checkpoint_id,
                    fallback_applied=False,
                )
            except TimeoutError:
                last_failure_reason = FailureReason.TRANSIENT_TIMEOUT
            except Exception as exc:
                # Unhandled exception - classify as transient for retry
                logger.debug(
                    "[%s] Attempt %d exception (will retry): %s", self.execution_id, attempt, exc
                )
                last_failure_reason = FailureReason.TRANSIENT_NETWORK

            # Check if we should retry
            if not self.retry_policy.should_retry(last_failure_reason, attempt):
                logger.warning(
                    f"[{self.execution_id}] Not retrying: failure={last_failure_reason.value}, attempt={attempt}"
                )
                break

            # Compute delay and wait
            delay = self.retry_policy.compute_delay(attempt - 1)
            logger.info(
                f"[{self.execution_id}] Retrying after {delay:.1f}s (reason: {last_failure_reason.value})"
            )
            await asyncio.sleep(delay)

        return None

    async def _try_degraded_mode(
        self,
        degraded_fn: Callable[..., T],
        degraded_args: dict,
        checkpoint: Any,
        start_time: float,
    ) -> ExecutionResult | None:
        """Try degraded mode fallback."""
        logger.info(f"[{self.execution_id}] Primary exhausted, attempting degraded mode")
        try:
            result = await self._call_async(
                degraded_fn, degraded_args, timeout=self.degraded_config.timeout
            )
            execution_time = time.time() - start_time
            return ExecutionResult(
                success=True,
                mode=ExecutionMode.DEGRADED,
                output=result,
                attempt=1,
                total_attempts=1,
                execution_time=execution_time,
                checkpoint_id=checkpoint.checkpoint_id,
                fallback_applied=True,
            )
        except Exception as e:
            logger.error(f"[{self.execution_id}] Degraded mode also failed: {e}")
            return None

    def _return_offline_result(self, checkpoint: Any, start_time: float) -> ExecutionResult:
        """Return offline result when all modes fail."""
        execution_time = time.time() - start_time
        return ExecutionResult(
            success=False,
            mode=ExecutionMode.OFFLINE,
            output=None,
            error="All modes exhausted",
            failure_reason=FailureReason.UNKNOWN,
            attempt=self.retry_policy.max_attempts,
            total_attempts=self.retry_policy.max_attempts,
            execution_time=execution_time,
            checkpoint_id=checkpoint.checkpoint_id,
            fallback_applied=False,
        )

    def _classify_error(self, error_str: str) -> FailureReason:
        """Classify error into FailureReason category."""
        error_lower = error_str.lower()
        if "connection" in error_lower or "network" in error_lower:
            return FailureReason.TRANSIENT_NETWORK
        elif "timeout" in error_lower:
            return FailureReason.TRANSIENT_TIMEOUT
        elif "resource" in error_lower or "exhausted" in error_lower:
            return FailureReason.RESOURCE_EXHAUSTED
        return FailureReason.PERMANENT_ERROR

    async def _call_async(self, fn: Callable, args: dict, timeout: float | None = None) -> Any:
        """Call function, handling both sync and async."""
        if asyncio.iscoroutinefunction(fn):
            if timeout:
                return await asyncio.wait_for(fn(**args), timeout=timeout)
            return await fn(**args)
        else:
            loop = asyncio.get_event_loop()
            if timeout:
                return await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: fn(**args)), timeout=timeout
                )
            return await loop.run_in_executor(None, lambda: fn(**args))


# Convenience functions for sync contexts
def execute_with_checkpoint(
    operation: str,
    primary_fn: Callable[..., T],
    primary_args: dict | None = None,
    degraded_fn: Callable[..., T] | None = None,
    degraded_args: dict | None = None,
    retry_policy: RetryPolicy | None = None,
) -> ExecutionResult:
    """Synchronous wrapper around execute_with_checkpoint."""
    ctx = ExecutionContext(
        operation=operation,
        retry_policy=retry_policy,
    )
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(
            ctx.execute(
                primary_fn=primary_fn,
                primary_args=primary_args or {},
                degraded_fn=degraded_fn,
                degraded_args=degraded_args or {},
            )
        )
    finally:
        loop.close()
