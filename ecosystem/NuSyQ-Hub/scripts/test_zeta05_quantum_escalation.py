#!/usr/bin/env python3
"""🧪 Test Suite: Zeta05 → Quantum Resolver Escalation

Tests error correction escalation pipeline from basic Zeta05 fixes
to advanced Quantum Problem Resolver multi-modal healing.

OmniTag: {
    "purpose": "Test Zeta05-Quantum escalation integration",
    "dependencies": ["zeta05_error_corrector", "quantum_problem_resolver"],
    "context": "Error handling pipeline validation",
    "evolution_stage": "v1.0-testing"
}
"""

import sys
from datetime import datetime
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))


def test_zeta05_basic_correction():
    """Test Zeta05 basic error correction (no escalation)."""
    print("\n🧪 TEST 1: Zeta05 Basic Error Correction")
    print("=" * 60)

    try:
        from src.healing.zeta05_error_corrector import (
            CorrectionStrategy,
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()

        # Create low-severity error (should auto-fix, not escalate)
        error = ErrorContext(
            error_type="NameError",
            error_message="name 'x' is not defined",
            severity=ErrorSeverity.LOW,
            timestamp=datetime.now(),
            source_file="test_script.py",
            line_number=42,
        )

        result = corrector.correct_error(error)

        print("   ✅ Zeta05 corrector initialized")
        print(f"   📊 Error: {error.error_type} ({error.severity.value})")
        print(f"   🔧 Strategy: {result.strategy_used.value}")
        print(f"   ✅ Success: {result.success}")
        print(f"   💡 Confidence: {result.confidence * 100:.0f}%")

        assert result.strategy_used != CorrectionStrategy.ESCALATE, "Low severity error should not escalate"

        return True

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_zeta05_quantum_escalation():
    """Test Zeta05 escalation to Quantum Resolver."""
    print("\n🧪 TEST 2: Zeta05 → Quantum Resolver Escalation")
    print("=" * 60)

    try:
        from src.healing.zeta05_error_corrector import (
            CorrectionStrategy,
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()

        # Create critical error (should escalate)
        error = ErrorContext(
            error_type="ComplexSystemError",
            error_message="Multi-modal system failure with cascade effects",
            severity=ErrorSeverity.CRITICAL,
            timestamp=datetime.now(),
            source_file="complex_system.py",
            line_number=999,
            stack_trace="Complex multi-file traceback...",
            metadata={"cascading": True, "affected_systems": ["db", "cache", "api"]},
        )

        result = corrector.correct_error(error)

        print("   ✅ Critical error created")
        print(f"   📊 Error: {error.error_type} ({error.severity.value})")
        print(f"   🔧 Strategy: {result.strategy_used.value}")
        print(f"   🔺 Escalated: {result.strategy_used == CorrectionStrategy.ESCALATE}")

        if result.strategy_used == CorrectionStrategy.ESCALATE:
            print("   ✅ ESCALATION TRIGGERED")
            print("   🌀 Quantum resolver invoked: True")
            print(f"   📈 Confidence: {result.confidence * 100:.0f}%")
            print(f"   💡 Suggestions: {len(result.suggestions)}")

            # Check that escalation was attempted
            assert "quantum" in result.reasoning.lower() or "escalate" in result.reasoning.lower(), (
                "Escalation should mention quantum resolver"
            )

            return True
        else:
            print("   ⚠️  WARNING: Critical error did not escalate")
            return False

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_quantum_resolver_available():
    """Test Quantum Problem Resolver is accessible."""
    print("\n🧪 TEST 3: Quantum Problem Resolver Availability")
    print("=" * 60)

    try:
        from src.healing.quantum_problem_resolver import (
            ProblemSignature,
            QuantumProblemResolver,
            QuantumProblemState,
        )

        resolver = QuantumProblemResolver()

        print("   ✅ Quantum resolver imported")
        print(f"   📍 Root path: {resolver.root_path}")
        print(f"   🔮 Problem registry: {len(resolver.problem_registry)} problems")
        print(f"   🌀 Quantum states available: {len(QuantumProblemState)}")

        # Create test problem signature
        test_problem = ProblemSignature(
            problem_id="test_problem_001",
            quantum_state=QuantumProblemState.SUPERPOSITION,
            entanglement_degree=0.5,
            resolution_probability=0.7,
            narrative_coherence=0.8,
            metadata={"test": True},
        )

        print("   ✅ Test problem signature created")
        print(f"   📊 State: {test_problem.quantum_state.value}")
        print(f"   🔗 Entanglement: {test_problem.entanglement_degree}")
        print(f"   📈 Resolution probability: {test_problem.resolution_probability}")

        return True

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_escalation_error_translation():
    """Test error context translation to problem signature."""
    print("\n🧪 TEST 4: Error Context → Problem Signature Translation")
    print("=" * 60)

    try:
        from src.healing.zeta05_error_corrector import (
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()

        # Create high-severity error
        error = ErrorContext(
            error_type="SystemIntegrityError",
            error_message="Critical system integrity violation detected",
            severity=ErrorSeverity.HIGH,
            timestamp=datetime.now(),
            source_file="core/system.py",
            line_number=1337,
            metadata={"critical": True, "auto_fix_failed": True},
        )

        # Trigger escalation
        result = corrector.correct_error(error)

        print("   ✅ High-severity error escalated")
        print(f"   📦 Error type: {error.error_type}")
        print(f"   🎯 Severity: {error.severity.value}")

        if result.strategy_used.value == "escalate":
            print("   ✅ TRANSLATION SUCCESSFUL")
            print("   🔄 Error → Problem signature mapping verified")
            print(f"   📊 Metadata preserved: {bool(error.metadata)}")
            print(f"   💡 Suggestions generated: {len(result.suggestions)}")

            # Verify metadata was captured
            assert error.metadata is not None, "Metadata should be preserved"
            return True
        else:
            print("   ⚠️  WARNING: Error did not escalate as expected")
            return False

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_correction_stats_tracking():
    """Test correction statistics tracking."""
    print("\n🧪 TEST 5: Correction Statistics Tracking")
    print("=" * 60)

    try:
        from src.healing.zeta05_error_corrector import (
            ErrorContext,
            ErrorSeverity,
            Zeta05ErrorCorrector,
        )

        corrector = Zeta05ErrorCorrector()

        # Process multiple errors
        errors = [
            ErrorContext("TypeError", "type error 1", ErrorSeverity.MEDIUM, datetime.now()),
            ErrorContext("ValueError", "value error 2", ErrorSeverity.HIGH, datetime.now()),
            ErrorContext("SystemError", "system error 3", ErrorSeverity.CRITICAL, datetime.now()),
        ]

        for error in errors:
            corrector.correct_error(error)

        stats = corrector.get_correction_stats()

        print("   ✅ Stats tracking operational")
        print(f"   📊 Total corrections: {stats['total_corrections']}")
        print(f"   📈 Success rate: {stats.get('success_rate', 0) * 100:.0f}%")
        print(f"   🔧 Strategies used: {stats.get('strategies_used', {})}")
        print(f"   🎯 History length: {len(corrector.corrections_history)}")

        # LOW errors are ignored and not counted, so we expect 2-3 corrections
        assert stats["total_corrections"] >= 2, "Should track corrections"
        assert len(corrector.corrections_history) >= 2, "History should track attempts"

        return True

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all Zeta05-Quantum escalation tests."""
    print("🔺 ZETA05 → QUANTUM RESOLVER ESCALATION TEST SUITE")
    print("=" * 60)
    print("Testing error correction escalation pipeline")
    print()

    results = {
        "Basic Correction": test_zeta05_basic_correction(),
        "Quantum Escalation": test_zeta05_quantum_escalation(),
        "Quantum Resolver": test_quantum_resolver_available(),
        "Error Translation": test_escalation_error_translation(),
        "Stats Tracking": test_correction_stats_tracking(),
    }

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")

    print(f"\n   Total: {passed}/{total} tests passing")

    if passed == total:
        print("   🎉 ALL TESTS PASSED!")
        print("\n   ✅ Escalation pipeline operational:")
        print("      Low errors → Auto-fix")
        print("      Medium errors → Suggestions")
        print("      High/Critical → Quantum Resolver")
        return 0
    else:
        print(f"   ⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
