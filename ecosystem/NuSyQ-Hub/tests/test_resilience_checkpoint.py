"""Tests for src/resilience/checkpoint_retry_degraded.py — dataclasses and managers."""

import pytest


class TestExecutionModeFailureReason:
    """Tests for ExecutionMode and FailureReason enums."""

    def test_execution_mode_values(self):
        from src.resilience.checkpoint_retry_degraded import ExecutionMode
        assert ExecutionMode.PRIMARY.value == "primary"
        assert ExecutionMode.DEGRADED.value == "degraded"
        assert ExecutionMode.OFFLINE.value == "offline"

    def test_failure_reason_values(self):
        from src.resilience.checkpoint_retry_degraded import FailureReason
        assert FailureReason.UNKNOWN is not None
        assert FailureReason.PERMANENT_ERROR is not None
        assert len(list(FailureReason)) >= 3


class TestCheckpointState:
    """Tests for CheckpointState dataclass."""

    def test_basic_construction(self):
        from src.resilience.checkpoint_retry_degraded import CheckpointState
        cs = CheckpointState(
            checkpoint_id="cp1",
            timestamp="2026-01-01T00:00:00",
            operation="ollama_call",
        )
        assert cs.checkpoint_id == "cp1"
        assert cs.operation == "ollama_call"

    def test_state_hash_computed(self):
        from src.resilience.checkpoint_retry_degraded import CheckpointState
        cs = CheckpointState(
            checkpoint_id="cp2",
            timestamp="2026-01-01T00:00:00",
            operation="chatdev_generate",
            context={"model": "llama3"},
        )
        assert isinstance(cs.state_hash, str)
        assert len(cs.state_hash) == 64  # SHA256 hex

    def test_hash_changes_with_context(self):
        from src.resilience.checkpoint_retry_degraded import CheckpointState
        cs1 = CheckpointState("c1", "ts", "op", context={"a": 1})
        cs2 = CheckpointState("c1", "ts", "op", context={"a": 2})
        assert cs1.state_hash != cs2.state_hash

    def test_to_dict(self):
        from src.resilience.checkpoint_retry_degraded import CheckpointState
        cs = CheckpointState("cp3", "2026-01-01", "op")
        d = cs.to_dict()
        assert isinstance(d, dict)
        assert d["checkpoint_id"] == "cp3"
        assert "state_hash" in d


class TestRetryPolicy:
    """Tests for RetryPolicy dataclass."""

    def test_defaults(self):
        from src.resilience.checkpoint_retry_degraded import RetryPolicy
        rp = RetryPolicy()
        assert rp.max_attempts == 3
        assert rp.initial_delay == 1.0
        assert rp.backoff_factor == 2.0
        assert rp.jitter is True

    def test_compute_delay_increases(self):
        from src.resilience.checkpoint_retry_degraded import RetryPolicy
        rp = RetryPolicy(jitter=False)  # No jitter for determinism
        d0 = rp.compute_delay(0)
        d1 = rp.compute_delay(1)
        d2 = rp.compute_delay(2)
        assert d0 < d1 < d2

    def test_compute_delay_caps_at_max(self):
        from src.resilience.checkpoint_retry_degraded import RetryPolicy
        rp = RetryPolicy(max_delay=5.0, jitter=False)
        # Large attempt number should hit max
        delay = rp.compute_delay(20)
        assert delay <= 5.0

    def test_should_retry_transient(self):
        from src.resilience.checkpoint_retry_degraded import FailureReason, RetryPolicy
        rp = RetryPolicy(max_attempts=3)
        assert rp.should_retry(FailureReason.TRANSIENT_NETWORK, attempt=0) is True
        assert rp.should_retry(FailureReason.TRANSIENT_NETWORK, attempt=1) is True

    def test_should_not_retry_permanent(self):
        from src.resilience.checkpoint_retry_degraded import FailureReason, RetryPolicy
        rp = RetryPolicy()
        assert rp.should_retry(FailureReason.PERMANENT_ERROR, attempt=0) is False

    def test_should_not_retry_at_max_attempts(self):
        from src.resilience.checkpoint_retry_degraded import FailureReason, RetryPolicy
        rp = RetryPolicy(max_attempts=3)
        assert rp.should_retry(FailureReason.TRANSIENT_NETWORK, attempt=3) is False


class TestDegradedModeConfig:
    """Tests for DegradedModeConfig dataclass."""

    def test_defaults(self):
        from src.resilience.checkpoint_retry_degraded import DegradedModeConfig
        cfg = DegradedModeConfig()
        assert cfg.enabled is True
        assert cfg.local_only is True
        assert cfg.timeout == 30.0

    def test_custom(self):
        from src.resilience.checkpoint_retry_degraded import DegradedModeConfig
        cfg = DegradedModeConfig(enabled=False, timeout=10.0, local_only=False)
        assert cfg.enabled is False
        assert cfg.timeout == 10.0


class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""

    def test_success_result(self):
        from src.resilience.checkpoint_retry_degraded import ExecutionMode, ExecutionResult
        r = ExecutionResult(success=True, mode=ExecutionMode.PRIMARY, output="done")
        assert r.success is True
        assert r.output == "done"

    def test_failure_result(self):
        from src.resilience.checkpoint_retry_degraded import (
            ExecutionMode,
            ExecutionResult,
            FailureReason,
        )
        r = ExecutionResult(
            success=False,
            mode=ExecutionMode.DEGRADED,
            error="timeout",
            failure_reason=FailureReason.TRANSIENT_TIMEOUT,
        )
        assert r.success is False
        assert r.failure_reason == FailureReason.TRANSIENT_TIMEOUT


class TestCheckpointManager:
    """Tests for CheckpointManager with tmp_path."""

    @pytest.fixture
    def mgr(self, tmp_path):
        from src.resilience.checkpoint_retry_degraded import CheckpointManager
        return CheckpointManager(checkpoint_root=tmp_path / "checkpoints")

    def test_instantiation(self, mgr):
        assert mgr is not None

    def test_root_created(self, mgr):
        assert mgr.root.exists()

    def test_create_returns_checkpoint(self, mgr):
        from src.resilience.checkpoint_retry_degraded import CheckpointState
        cp = mgr.create("test_op", context={"key": "value"})
        assert isinstance(cp, CheckpointState)
        assert cp.operation == "test_op"

    def test_checkpoint_file_written(self, mgr):
        cp = mgr.create("file_commit", context={"rev": "abc"})
        cp_file = mgr.root / f"{cp.checkpoint_id}.json"
        assert cp_file.exists()

    def test_restore_checkpoint(self, mgr):
        from src.resilience.checkpoint_retry_degraded import CheckpointState
        cp = mgr.create("restore_test", context={"data": 42})
        restored = mgr.restore(cp.checkpoint_id)
        assert isinstance(restored, CheckpointState)
        assert restored.checkpoint_id == cp.checkpoint_id
        assert restored.context["data"] == 42

    def test_restore_missing_returns_none(self, mgr):
        result = mgr.restore("nonexistent-id")
        assert result is None
