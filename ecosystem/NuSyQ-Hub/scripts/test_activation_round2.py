#!/usr/bin/env python3
"""🧪 Quick Activation Test - Round 2

Tests second batch of activated systems:
- Wizard Navigator (consolidated)
- Breathing Pacing Integration
- Zen Engine Wrapper
- Zeta05 Error Corrector
"""

import logging
import sys
from pathlib import Path

# Add repo to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)


def test_wizard_navigator():
    """Test Wizard Navigator consolidation."""
    print("\n🧙 Testing Wizard Navigator (Consolidated)...")
    try:
        from src.tools.wizard_navigator_consolidated import WizardNavigator

        # Create navigator
        wizard = WizardNavigator(".")
        print("✅ Wizard Navigator initialized")

        # Test room display
        room = wizard.get_current_room()
        print(f"   Current room: {room['name']}")
        print(f"   Exits: {len(room['exits'])}")
        print(f"   Items: {len(room['items'])}")

        # Test command handling
        wizard.handle_command("help")
        print("✅ Command handling works")

        # Test stats
        wizard.stats()
        print("✅ Statistics tracking works")

        return True

    except Exception as e:
        logger.exception(f"❌ Wizard Navigator test failed: {e}")
        return False


def test_breathing_integration():
    """Test Breathing Pacing Integration."""
    print("\n⏱️  Testing Breathing Pacing Integration...")
    try:
        from src.integration.breathing_integration import BreathingIntegration

        # Create integration
        breathing = BreathingIntegration(tau_base=90.0, enable_breathing=True)
        print("✅ Breathing Integration initialized")
        print(f"   Enabled: {breathing.enable_breathing}")
        print(f"   Tau base: {breathing.tau_base}s")

        # Test breathing calculation
        factor = breathing.calculate_breathing_factor(success_rate=0.85, backlog_level=0.40, failure_burst=0.10)
        print(f"   Breathing factor: {factor:.2f}x")

        # Test timeout adjustment
        base_timeout = 120.0
        adjusted = breathing.apply_to_timeout(base_timeout)
        print(f"   Timeout: {base_timeout}s → {adjusted:.1f}s")

        # Test state retrieval
        state = breathing.get_breathing_state()
        print(f"✅ Breathing state: {state['enabled']}")

        return True

    except Exception as e:
        logger.exception(f"❌ Breathing Integration test failed: {e}")
        return False


def test_zen_wrapper():
    """Test Zen Engine Wrapper."""
    print("\n🧘 Testing Zen Engine Wrapper...")
    try:
        from src.integration.zen_engine_wrapper import ZenEngineWrapper

        # Create wrapper
        zen = ZenEngineWrapper()
        print("✅ Zen Engine Wrapper initialized")
        print(f"   Available: {zen.available}")

        if zen.available:
            # Test command validation
            result = zen.validate_command("ls -la")
            print(f"   Validation result: safe={result.is_safe}, blocked={result.blocked}")

            # Test safe command extraction
            safe_cmd = zen.get_safe_command("python test.py")
            print(f"   Safe command: {safe_cmd}")
        else:
            print("   ⚠️  Zen CLI not available (expected if zen_engine not installed)")

        return True

    except Exception as e:
        logger.exception(f"❌ Zen Engine Wrapper test failed: {e}")
        return False


def test_zeta05():
    """Test Zeta05 Error Corrector."""
    print("\n🔧 Testing Zeta05 Error Corrector...")
    try:
        from src.healing.zeta05_error_corrector import Zeta05ErrorCorrector

        # Create corrector
        corrector = Zeta05ErrorCorrector()
        print("✅ Zeta05 Error Corrector initialized")

        # Test error detection
        test_error = ValueError("Invalid input value")
        error_context = corrector.detect_error(test_error, source_file="test.py")
        print(f"   Detected: {error_context.error_type} ({error_context.severity.value})")

        # Test correction
        result = corrector.correct_error(error_context)
        print(f"   Strategy: {result.strategy_used.value}")
        print(f"   Confidence: {result.confidence:.0%}")
        print(f"   Suggestions: {len(result.suggestions or [])}")

        # Test stats
        stats = corrector.get_correction_stats()
        print(f"✅ Stats: {stats['total_corrections']} corrections tracked")

        return True

    except Exception as e:
        logger.exception(f"❌ Zeta05 test failed: {e}")
        return False


def main():
    """Run all activation tests."""
    print("=" * 70)
    print("🚀 NuSyQ-Hub Dormant Systems Activation - Round 2")
    print("=" * 70)

    results = {
        "Wizard Navigator": test_wizard_navigator(),
        "Breathing Integration": test_breathing_integration(),
        "Zen Engine Wrapper": test_zen_wrapper(),
        "Zeta05 Error Corrector": test_zeta05(),
    }

    print("\n" + "=" * 70)
    print("📊 Round 2 Activation Test Results")
    print("=" * 70)

    all_passed = True
    for system, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {system}")
        if not passed:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("\n🎉 All Round 2 systems activated successfully!")
        print("\n📋 Next Steps:")
        print("   1. Use Wizard Navigator: python -m src.tools.wizard_navigator_consolidated")
        print("   2. Integrate Breathing with timeout_config")
        print("   3. Use Zen wrapper for automated command validation")
        print("   4. Wire Zeta05 into error handling pipelines")
    else:
        print("\n⚠️  Some systems failed activation. Check logs above.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
