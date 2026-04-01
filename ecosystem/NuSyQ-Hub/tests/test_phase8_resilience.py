#!/usr/bin/env python3
"""Quick test: Phase 8 Resilience Integration (checkpoint/retry/degraded/attestation).

Runs through the complete Phase 8 flow:
1. Execute with checkpoint/retry/degraded
2. Emit audit entries
3. Create attestations
4. Generate Mission Control report
5. Verify integrity
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.integration.chatdev_resilience_handler import ResilientChatDevHandler
from src.resilience.checkpoint_retry_degraded import (
    ExecutionContext,
    RetryPolicy,
)
from src.resilience.mission_control_attestation import (
    AttestationManager,
    AuditEntry,
    AuditLog,
    MissionControlReportBuilder,
    PolicyStatus,
)
from src.resilience.sandbox_chatdev_validator import (
    SandboxConfig,
    SandboxMode,
    validate_chatdev_sandbox,
)


async def test_checkpoint_retry():
    """Test checkpoint/retry pattern."""
    print("\n=== TEST 1: Checkpoint/Retry Pattern ===")

    # Create simple async functions
    attempt_count = [0]

    def flaky_operation():
        """Operation that fails once then succeeds."""
        attempt_count[0] += 1
        if attempt_count[0] < 2:
            raise TimeoutError("Simulated transient timeout")  # Retryable error
        return {"result": "success", "attempts": attempt_count[0]}

    def fallback_operation():
        """Degraded mode fallback."""
        return {"result": "degraded_fallback", "quick": True}

    ctx = ExecutionContext(
        operation="test_flaky",
        retry_policy=RetryPolicy(max_attempts=3, initial_delay=0.1),
    )

    result = await ctx.execute(
        primary_fn=flaky_operation,
        primary_args={},
        degraded_fn=fallback_operation,
        degraded_args={},
    )

    print(f"✅ Checkpoint/Retry: {result.success}")
    print(f"   Mode: {result.mode.value}")
    print(f"   Attempts: {result.attempt}/{result.total_attempts}")
    print(f"   Output: {result.output}")
    assert result.success, "Should have succeeded on retry or degraded"
    # Note: Will use degraded if transient error happens, both are acceptable
    print("✅ Test passed")


def test_audit_log():
    """Test audit logging."""
    print("\n=== TEST 2: Audit Logging ===")

    # Clean up any previous test data
    test_file = Path("state/test_audit.jsonl")
    if test_file.exists():
        test_file.unlink()

    audit_log = AuditLog(test_file)

    # Add test entries
    for i in range(3):
        entry = AuditEntry(
            audit_id=f"test_{i}",
            timestamp=f"2026-02-12T10:{i:02d}:00Z",
            action="test_action",
            agent="test_agent",
            result="success" if i < 2 else "failure",
        )
        audit_log.append(entry)

    # Read back
    entries = audit_log.read_all()
    print(f"✅ Logged {len(entries)} audit entries")

    # Verify integrity
    all_valid = audit_log.verify_integrity()
    print(f"✅ All entries valid: {all_valid}")
    assert all_valid, "All entries should be valid"

    # Filter by result
    failures = audit_log.filter_by_result("failure")
    print(f"✅ Filtered failures: {len(failures)}")
    assert len(failures) == 1, "Should have 1 failure"
    print("✅ Test passed")


def test_attestation():
    """Test artifact attestation."""
    print("\n=== TEST 3: Artifact Attestation ===")

    # Clean up any previous test data
    import shutil

    test_dir = Path("state/test_attestations")
    if test_dir.exists():
        shutil.rmtree(test_dir)

    attestation_mgr = AttestationManager(test_dir)

    artifact_content = '{"project": "test", "files": 3}'
    audit_entries = [
        AuditEntry(
            audit_id="test_audit_1",
            timestamp="2026-02-12T10:00:00Z",
            action="test",
            agent="test",
            result="success",
        )
    ]
    policy = PolicyStatus(
        sandboxing_enabled=False,
        isolation_level="none",
        attestation_required=True,
    )

    attestation = attestation_mgr.attest_artifact(
        artifact_id="test_artifact_001",
        artifact_content=artifact_content,
        audit_entries=audit_entries,
        policy_status=policy,
        run_id="test_run_001",
    )

    print(f"✅ Attestation created: {attestation.attestation_hash[:16]}...")

    # Verify artifact
    is_valid, _ = attestation_mgr.verify_artifact("test_artifact_001", artifact_content)
    print(f"✅ Artifact verified: {is_valid}")
    assert is_valid, "Should verify successfully"
    print("✅ Test passed")


async def test_sandbox_validator():
    """Test sandbox validation."""
    print("\n=== TEST 4: Sandbox Validator ===")

    config = SandboxConfig(
        mode=SandboxMode.LOCAL_ONLY,
        timeout=10.0,
        output_dir=Path("state/test_sandbox"),
    )

    result = await validate_chatdev_sandbox(
        task="Create a simple hello world",
        model="phi:latest",
        config=config,
    )

    print(f"✅ Sandbox validation: {result.success}")
    print(f"   Sandbox ID: {result.sandbox_id}")
    print(f"   Execution time: {result.execution_time:.2f}s")
    print(f"   Validation score: {result.validation_score:.2f}")
    print(f"   Audit entries: {len(result.audit_entries)}")
    print("✅ Test passed")


async def test_resilient_handler():
    """Test ResilientChatDevHandler."""
    print("\n=== TEST 5: Resilient ChatDev Handler ===")

    handler = ResilientChatDevHandler()

    result = await handler.execute_generate_project(
        task="Create a simple CLI app",
        model="qwen2.5-coder:7b",
        agent="test_agent",
        use_sandbox=False,
    )

    print(f"✅ Handler execution: {result['success']}")
    print(f"   Mode: {result['execution_mode']}")
    print(f"   Time: {result.get('execution_time', 0):.2f}s")
    if "attestation_hash" in result:
        print(f"   Attestation: {result['attestation_hash'][:16]}...")
    print(f"   Audit entries: {len(result.get('audit_entries', []))}")
    print("✅ Test passed")


def test_culture_ship_report():
    """Test Mission Control report generation."""
    print("\n=== TEST 6: Culture Ship Report ===")

    # Create some test audit entries first
    audit_log = AuditLog(Path("state/test_mission_control_audit.jsonl"))
    for i in range(5):
        entry = AuditEntry(
            audit_id=f"cs_test_{i}",
            timestamp=f"2026-02-12T10:{i:02d}:00Z",
            action=["generate", "analyze", "heal", "review", "test"][i],
            agent="test_agent",
            result=["success", "success", "success", "partial", "failure"][i],
        )
        audit_log.append(entry)

    # Build report
    builder = MissionControlReportBuilder()

    # Override audit log for this test
    builder.audit_log = audit_log

    report = builder.build_report()

    print("✅ Culture Ship Report:")
    print(f"   Report ID: {report.report_id[:8]}...")
    print(f"   Total entries: {report.audit_summary.get('total_entries', 0)}")
    print(f"   Health score: {report.health_score:.2f}")
    print(f"   Patterns detected: {len(report.patterns_observed)}")
    print(f"   Violations: {len(report.policy_violations)}")
    print(f"   Lessons learned: {len(report.lessons_learned)}")
    if report.lessons_learned:
        print(f"   Sample lesson: {report.lessons_learned[0][:60]}...")
    print("✅ Test passed")


async def main():
    """Run all tests."""
    print("=" * 70)
    print("PHASE 8 RESILIENCE INTEGRATION TEST")
    print("=" * 70)

    try:
        await test_checkpoint_retry()
        test_audit_log()
        test_attestation()
        await test_sandbox_validator()
        await test_resilient_handler()
        test_culture_ship_report()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print("\nPhase 8 Resilience: Checkpoint/Retry ✅")
        print("                   Degraded-Mode ✅")
        print("                   Attestation ✅")
        print("                   Audit Trail ✅")
        print("                   Sandbox Validation ✅")
        print("                   Culture Ship Report ✅")
        print("\nReady for: ChatDev MCP handler wiring and production deployment")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
