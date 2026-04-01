"""Tests for src/resilience/checkpoint_retry_degraded.py — enums, dataclasses,
CheckpointManager, RetryPolicy, and ExecutionContext async execution.
"""

import json
import time


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TestExecutionMode:
    """Tests for ExecutionMode enum."""

    def test_has_three_values(self):
        from src.resilience.checkpoint_retry_degraded import ExecutionMode
        assert len(list(ExecutionMode)) == 3

    def test_values(self):
        from src.resilience.checkpoint_retry_degraded import ExecutionMode
        assert ExecutionMode.PRIMARY.value == "primary"
        assert ExecutionMode.DEGRADED.value == "degraded"
        assert ExecutionMode.OFFLINE.value == "offline"


class TestFailureReason:
    """Tests for FailureReason enum."""

    def test_has_five_values(self):
        from src.resilience.checkpoint_retry_degraded import FailureReason
        assert len(list(FailureReason)) == 5

    def test_known_values(self):
        from src.resilience.checkpoint_retry_degraded import FailureReason
        assert FailureReason.TRANSIENT_NETWORK.value == "transient_network"
        assert FailureReason.PERMANENT_ERROR.value == "permanent_error"
        assert FailureReason.UNKNOWN.value == "unknown"


# ---------------------------------------------------------------------------
# CheckpointState dataclass
# ---------------------------------------------------------------------------


class TestCheckpointState:
    """Tests for CheckpointState dataclass."""

    def _make(self, **kwargs):
        from src.resilience.checkpoint_retry_degraded import CheckpointState
        defaults = {
            "checkpoint_id": "ckpt-001",
            "timestamp": "2026-01-01T00:00:00Z",
            "operation": "test_op",
        }
        defaults.update(kwargs)
        return CheckpointState(**defaults)

    def test_instantiation(self):
        assert self._make() is not None

    def test_fields_stored(self):
        cp = self._make(operation="chatdev_generate")
        assert cp.checkpoint_id == "ckpt-001"
        assert cp.operation == "chatdev_generate"

    def test_state_hash_computed_on_init(self):
        cp = self._make()
        assert isinstance(cp.state_hash, str)
        assert len(cp.state_hash) == 64  # SHA256 hex

    def test_state_hash_deterministic(self):
        cp1 = self._make(context={"key": "val"})
        cp2 = self._make(context={"key": "val"})
        assert cp1.state_hash == cp2.state_hash

    def test_state_hash_changes_with_context(self):
        cp1 = self._make(context={"key": "a"})
        cp2 = self._make(context={"key": "b"})
        assert cp1.state_hash != cp2.state_hash

    def test_default_context_empty(self):
        assert self._make().context == {}

    def test_default_dependencies_empty(self):
        assert self._make().dependencies == []

    def test_default_metadata_empty(self):
        assert self._make().metadata == {}

    def test_to_dict_returns_dict(self):
        d = self._make().to_dict()
        assert isinstance(d, dict)

    def test_to_dict_has_required_keys(self):
        d = self._make().to_dict()
        for key in ("checkpoint_id", "timestamp", "operation", "state_hash"):
            assert key in d

    def test_dependencies_sorted_for_hash(self):
        # Same deps in different order should hash identically
        cp1 = self._make(dependencies=["file_a", "file_b"])
        cp2 = self._make(dependencies=["file_b", "file_a"])
        assert cp1.state_hash == cp2.state_hash


# ---------------------------------------------------------------------------
# RetryPolicy dataclass
# ---------------------------------------------------------------------------


class TestRetryPolicy:
    """Tests for RetryPolicy dataclass."""

    def test_default_max_attempts(self):
        from src.resilience.checkpoint_retry_degraded import RetryPolicy
        assert RetryPolicy().max_attempts == 3

    def test_default_initial_delay(self):
        from src.resilience.checkpoint_retry_degraded import RetryPolicy
        assert RetryPolicy().initial_delay == 1.0

    def test_default_backoff_factor(self):
        from src.resilience.checkpoint_retry_degraded import RetryPolicy
        assert RetryPolicy().backoff_factor == 2.0

    def test_default_max_delay(self):
        from src.resilience.checkpoint_retry_degraded import RetryPolicy
        assert RetryPolicy().max_delay == 60.0

    def test_default_jitter_true(self):
        from src.resilience.checkpoint_retry_degraded import RetryPolicy
        assert RetryPolicy().jitter is True

    def test_default_retryable_reasons_has_three(self):
        from src.resilience.checkpoint_retry_degraded import RetryPolicy
        assert len(RetryPolicy().retryable_reasons) == 3

    def test_compute_delay_first_attempt(self):
        from src.resilience.checkpoint_retry_degraded import RetryPolicy
        policy = RetryPolicy(initial_delay=1.0, backoff_factor=2.0, jitter=False)
        delay = policy.compute_delay(0)
        assert delay == 1.0

    def test_compute_delay_second_attempt(self):
        from src.resilience.checkpoint_retry_degraded import RetryPolicy
        policy = RetryPolicy(initial_delay=1.0, backoff_factor=2.0, jitter=False)
        delay = policy.compute_delay(1)
        assert delay == 2.0

    def test_compute_delay_capped_at_max(self):
        from src.resilience.checkpoint_retry_degraded import RetryPolicy
        policy = RetryPolicy(initial_delay=10.0, backoff_factor=10.0, max_delay=30.0, jitter=False)
        delay = policy.compute_delay(5)  # 10 * 10^5 = 1,000,000 → capped at 30
        assert delay == 30.0

    def test_compute_delay_with_jitter_in_range(self):
        from src.resilience.checkpoint_retry_degraded import RetryPolicy
        policy = RetryPolicy(initial_delay=1.0, backoff_factor=2.0, jitter=True)
        delay = policy.compute_delay(0)
        # With jitter: base=1.0, jitter factor 0.5..1.5 → range [0.5, 1.5]
        assert 0.4 <= delay <= 1.6  # small buffer for floating point

    def test_should_retry_retryable_reason_within_attempts(self):
        from src.resilience.checkpoint_retry_degraded import FailureReason, RetryPolicy
        policy = RetryPolicy(max_attempts=3)
        assert policy.should_retry(FailureReason.TRANSIENT_NETWORK, attempt=1) is True

    def test_should_retry_exceeded_attempts(self):
        from src.resilience.checkpoint_retry_degraded import FailureReason, RetryPolicy
        policy = RetryPolicy(max_attempts=3)
        assert policy.should_retry(FailureReason.TRANSIENT_NETWORK, attempt=3) is False

    def test_should_retry_permanent_error_returns_false(self):
        from src.resilience.checkpoint_retry_degraded import FailureReason, RetryPolicy
        policy = RetryPolicy(max_attempts=3)
        assert policy.should_retry(FailureReason.PERMANENT_ERROR, attempt=1) is False


# ---------------------------------------------------------------------------
# DegradedModeConfig dataclass
# ---------------------------------------------------------------------------


class TestDegradedModeConfig:
    """Tests for DegradedModeConfig dataclass."""

    def test_default_enabled_true(self):
        from src.resilience.checkpoint_retry_degraded import DegradedModeConfig
        assert DegradedModeConfig().enabled is True

    def test_default_local_only_true(self):
        from src.resilience.checkpoint_retry_degraded import DegradedModeConfig
        assert DegradedModeConfig().local_only is True

    def test_default_fallback_model(self):
        from src.resilience.checkpoint_retry_degraded import DegradedModeConfig
        assert DegradedModeConfig().fallback_model == "phi:latest"

    def test_custom_timeout(self):
        from src.resilience.checkpoint_retry_degraded import DegradedModeConfig
        assert DegradedModeConfig(timeout=60.0).timeout == 60.0


# ---------------------------------------------------------------------------
# ExecutionResult dataclass
# ---------------------------------------------------------------------------


class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""

    def test_instantiation(self):
        from src.resilience.checkpoint_retry_degraded import ExecutionMode, ExecutionResult
        r = ExecutionResult(success=True, mode=ExecutionMode.PRIMARY)
        assert r is not None

    def test_success_stored(self):
        from src.resilience.checkpoint_retry_degraded import ExecutionMode, ExecutionResult
        r = ExecutionResult(success=False, mode=ExecutionMode.DEGRADED)
        assert r.success is False
        assert r.mode.value == "degraded"

    def test_default_output_none(self):
        from src.resilience.checkpoint_retry_degraded import ExecutionMode, ExecutionResult
        r = ExecutionResult(success=True, mode=ExecutionMode.PRIMARY)
        assert r.output is None

    def test_default_attempt_one(self):
        from src.resilience.checkpoint_retry_degraded import ExecutionMode, ExecutionResult
        r = ExecutionResult(success=True, mode=ExecutionMode.PRIMARY)
        assert r.attempt == 1
        assert r.total_attempts == 1

    def test_default_fallback_applied_false(self):
        from src.resilience.checkpoint_retry_degraded import ExecutionMode, ExecutionResult
        r = ExecutionResult(success=True, mode=ExecutionMode.PRIMARY)
        assert r.fallback_applied is False


# ---------------------------------------------------------------------------
# CheckpointManager
# ---------------------------------------------------------------------------


class TestCheckpointManager:
    """Tests for CheckpointManager."""

    def test_instantiation(self, tmp_path):
        from src.resilience.checkpoint_retry_degraded import CheckpointManager
        mgr = CheckpointManager(checkpoint_root=tmp_path / "checkpoints")
        assert mgr is not None

    def test_root_dir_created(self, tmp_path):
        from src.resilience.checkpoint_retry_degraded import CheckpointManager
        root = tmp_path / "checkpoints"
        CheckpointManager(checkpoint_root=root)
        assert root.exists()

    def test_create_returns_checkpoint_state(self, tmp_path):
        from src.resilience.checkpoint_retry_degraded import CheckpointManager, CheckpointState
        mgr = CheckpointManager(checkpoint_root=tmp_path)
        cp = mgr.create("test_op", {"key": "value"})
        assert isinstance(cp, CheckpointState)

    def test_create_persists_file(self, tmp_path):
        from src.resilience.checkpoint_retry_degraded import CheckpointManager
        mgr = CheckpointManager(checkpoint_root=tmp_path)
        cp = mgr.create("test_op", {})
        checkpoint_file = tmp_path / f"{cp.checkpoint_id}.json"
        assert checkpoint_file.exists()

    def test_create_file_is_valid_json(self, tmp_path):
        from src.resilience.checkpoint_retry_degraded import CheckpointManager
        mgr = CheckpointManager(checkpoint_root=tmp_path)
        cp = mgr.create("test_op", {"data": 1})
        checkpoint_file = tmp_path / f"{cp.checkpoint_id}.json"
        data = json.loads(checkpoint_file.read_text())
        assert data["operation"] == "test_op"

    def test_restore_known_checkpoint(self, tmp_path):
        from src.resilience.checkpoint_retry_degraded import CheckpointManager, CheckpointState
        mgr = CheckpointManager(checkpoint_root=tmp_path)
        cp = mgr.create("restore_test", {"x": 1})
        restored = mgr.restore(cp.checkpoint_id)
        assert restored is not None
        assert isinstance(restored, CheckpointState)
        assert restored.operation == "restore_test"

    def test_restore_unknown_returns_none(self, tmp_path):
        from src.resilience.checkpoint_retry_degraded import CheckpointManager
        mgr = CheckpointManager(checkpoint_root=tmp_path)
        assert mgr.restore("nonexistent-uuid") is None

    def test_cleanup_removes_old_checkpoints(self, tmp_path):
        from src.resilience.checkpoint_retry_degraded import CheckpointManager
        mgr = CheckpointManager(checkpoint_root=tmp_path)
        # Create 5 checkpoints
        for _ in range(5):
            mgr.create("op", {})
            time.sleep(0.01)  # ensure distinct mtime
        # Keep only 2
        mgr.cleanup_old(keep_count=2)
        remaining = list(tmp_path.glob("*.json"))
        assert len(remaining) == 2


# ---------------------------------------------------------------------------
# ExecutionContext (async)
# ---------------------------------------------------------------------------


class TestExecutionContextAsync:
    """Tests for ExecutionContext.execute() async method."""

    import pytest

    @pytest.mark.asyncio
    async def test_primary_success(self, tmp_path):
        from src.resilience.checkpoint_retry_degraded import (
            CheckpointManager,
            ExecutionContext,
            ExecutionMode,
        )
        mgr = CheckpointManager(checkpoint_root=tmp_path)
        ctx = ExecutionContext("test_op", checkpoint_manager=mgr)

        async def primary_fn():
            return "primary_result"

        result = await ctx.execute(primary_fn)
        assert result.success is True
        assert result.mode == ExecutionMode.PRIMARY
        assert result.output == "primary_result"

    @pytest.mark.asyncio
    async def test_primary_failure_degraded_fallback(self, tmp_path):
        from src.resilience.checkpoint_retry_degraded import (
            CheckpointManager,
            DegradedModeConfig,
            ExecutionContext,
            ExecutionMode,
            RetryPolicy,
        )
        mgr = CheckpointManager(checkpoint_root=tmp_path)
        policy = RetryPolicy(max_attempts=1, jitter=False, initial_delay=0.0)
        degraded_cfg = DegradedModeConfig(enabled=True)
        ctx = ExecutionContext("fail_op", retry_policy=policy, degraded_config=degraded_cfg, checkpoint_manager=mgr)

        async def primary_fn():
            raise RuntimeError("primary failed")

        async def degraded_fn():
            return "degraded_result"

        result = await ctx.execute(primary_fn, degraded_fn=degraded_fn)
        assert result.success is True
        assert result.mode == ExecutionMode.DEGRADED

    @pytest.mark.asyncio
    async def test_all_paths_fail_returns_offline(self, tmp_path):
        from src.resilience.checkpoint_retry_degraded import (
            CheckpointManager,
            ExecutionContext,
            ExecutionMode,
            RetryPolicy,
        )
        mgr = CheckpointManager(checkpoint_root=tmp_path)
        policy = RetryPolicy(max_attempts=1, jitter=False, initial_delay=0.0)
        ctx = ExecutionContext("all_fail", retry_policy=policy, checkpoint_manager=mgr)

        async def primary_fn():
            raise RuntimeError("all fail")

        result = await ctx.execute(primary_fn)
        assert result.success is False
        assert result.mode == ExecutionMode.OFFLINE
