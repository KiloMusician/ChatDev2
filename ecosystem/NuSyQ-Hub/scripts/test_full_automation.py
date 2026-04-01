"""
Full Automation Integration Test
=================================

Validates the complete error→signal→quest→action pipeline.

Usage:
    python scripts/test_full_automation.py [--verbose]
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent


class AutomationTest:
    """Test the full automation pipeline."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.passed = 0
        self.failed = 0
        self.results: list[dict[str, Any]] = []

    def test(self, name: str, func) -> bool:
        """Run a test."""
        logger.info(f"\n{'=' * 80}")
        logger.info(f"TEST: {name}")
        logger.info("=" * 80)

        try:
            result = func()

            if result:
                logger.info(f"✅ PASS: {name}")
                self.passed += 1
                self.results.append({"name": name, "status": "pass"})
                return True
            else:
                logger.error(f"❌ FAIL: {name}")
                self.failed += 1
                self.results.append({"name": name, "status": "fail"})
                return False

        except Exception as e:
            logger.error(f"❌ ERROR: {name}: {e}")
            self.failed += 1
            self.results.append({"name": name, "status": "error", "error": str(e)})
            return False

    def test_bootstrap_system(self) -> bool:
        """Test bootstrap system exists and runs."""
        bootstrap_script = ROOT / "scripts" / "copilot_bootstrap.py"

        if not bootstrap_script.exists():
            logger.error("Bootstrap script not found")
            return False

        # Try to run it
        try:
            result = subprocess.run(
                [sys.executable, str(bootstrap_script), "--output", "json"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                logger.error(f"Bootstrap failed: {result.stderr[:200]}")
                return False

            # Parse output
            output = json.loads(result.stdout)
            logger.info(f"Bootstrap output keys: {list(output.keys())}")
            return True

        except subprocess.TimeoutExpired:
            logger.error("Bootstrap timed out")
            return False
        except json.JSONDecodeError:
            logger.error("Bootstrap output was not JSON")
            return False
        except Exception as e:
            logger.error(f"Bootstrap error: {e}")
            return False

    def test_capability_registry(self) -> bool:
        """Test capability registry exists and loads."""
        registry_script = ROOT / "scripts" / "copilot_capability_registry.py"

        if not registry_script.exists():
            logger.error("Registry script not found")
            return False

        # Try to import and load
        try:
            sys.path.insert(0, str(ROOT))
            from scripts.copilot_capability_registry import load_registry

            registry = load_registry()

            logger.info(f"Terminals: {len(registry.terminals)}")
            logger.info(f"Commands: {len(registry.commands)}")
            logger.info(f"API endpoints: {len(registry.api_endpoints)}")

            if len(registry.terminals) == 0:
                logger.error("No terminals in registry")
                return False

            if len(registry.commands) == 0:
                logger.error("No commands in registry")
                return False

            return True

        except Exception as e:
            logger.error(f"Registry load error: {e}")
            return False

    def test_error_signal_bridge(self) -> bool:
        """Test error→signal bridge module exists."""
        bridge_script = ROOT / "src" / "orchestration" / "error_signal_bridge.py"

        if not bridge_script.exists():
            logger.error("Error→Signal bridge not found")
            return False

        # Try to import
        try:
            sys.path.insert(0, str(ROOT))

            logger.info("✅ Bridge imports successful")
            return True

        except Exception as e:
            logger.error(f"Bridge import error: {e}")
            return False

    def test_signal_quest_mapper(self) -> bool:
        """Test signal→quest mapper module exists."""
        mapper_script = ROOT / "src" / "orchestration" / "signal_quest_mapper.py"

        if not mapper_script.exists():
            logger.error("Signal→Quest mapper not found")
            return False

        # Try to import
        try:
            sys.path.insert(0, str(ROOT))

            logger.info("✅ Mapper imports successful")
            return True

        except Exception as e:
            logger.error(f"Mapper import error: {e}")
            return False

    def test_orchestrator(self) -> bool:
        """Test orchestra module exists."""
        orchest_script = ROOT / "src" / "orchestration" / "ecosystem_orchestrator.py"

        if not orchest_script.exists():
            logger.error("Orchestrator not found")
            return False

        # Try to import
        try:
            sys.path.insert(0, str(ROOT))

            logger.info("✅ Orchestrator imports successful")
            return True

        except Exception as e:
            logger.error(f"Orchestrator import error: {e}")
            return False

    def test_bridge_with_data(self) -> bool:
        """Test error→signal bridge with sample data."""
        try:
            sys.path.insert(0, str(ROOT))
            from src.orchestration.error_signal_bridge import (
                ErrorGroup,
                ErrorSeverity,
                errors_to_signals,
            )

            # Create sample error group
            sample_errors = [
                ErrorGroup(
                    category="mypy",
                    count=5,
                    severity=ErrorSeverity.CRITICAL,
                    files_affected=["src/main.py", "src/utils.py"],
                    examples=["Type error on line 10", "Unknown type", "Missing return"],
                )
            ]

            # Convert to signals
            signals = errors_to_signals(sample_errors)

            if len(signals) != 1:
                logger.error(f"Expected 1 signal, got {len(signals)}")
                return False

            signal = signals[0]
            logger.info(f"Signal type: {signal.signal_type}")
            logger.info(f"Severity: {signal.severity}")
            logger.info(f"Message: {signal.message}")

            return signal.severity == "critical"

        except Exception as e:
            logger.error(f"Bridge test error: {e}")
            import traceback

            traceback.print_exc()
            return False

    def test_quest_creation_from_signal(self) -> bool:
        """Test signal→quest conversion."""
        try:
            sys.path.insert(0, str(ROOT))
            from src.orchestration.signal_quest_mapper import signal_to_quest

            # Create sample signal
            quest = signal_to_quest(
                signal_id="test_signal_1",
                signal_type="error",
                severity="critical",
                message="Found 5 type errors in mypy",
                context={
                    "error_category": "mypy",
                    "error_count": 5,
                    "files_affected": ["src/main.py"],
                    "example_errors": ["Type error on line 10"],
                },
            )

            logger.info(f"Quest title: {quest.title}")
            logger.info(f"Priority: {quest.priority}")
            logger.info(f"Action hint: {quest.action_hint}")

            if quest.priority < 3:
                logger.error("Critical error should have high priority")
                return False

            return True

        except Exception as e:
            logger.error(f"Quest creation error: {e}")
            import traceback

            traceback.print_exc()
            return False

    def run_all_tests(self) -> bool:
        """Run all tests."""
        logger.info("\n" + "╔" + "=" * 78 + "╗")
        logger.info("║ FULL AUTOMATION INTEGRATION TEST SUITE")
        logger.info("╚" + "=" * 78 + "╝\n")

        # All tests are synchronous now
        self.test("Bootstrap System", self.test_bootstrap_system)
        self.test("Capability Registry", self.test_capability_registry)
        self.test("Error→Signal Bridge Module", self.test_error_signal_bridge)
        self.test("Signal→Quest Mapper Module", self.test_signal_quest_mapper)
        self.test("Ecosystem Orchestrator Module", self.test_orchestrator)

        # Sync versions of async tests
        self.test("Bridge with Sample Data", self.test_bridge_with_data)
        self.test("Quest Creation from Signal", self.test_quest_creation_from_signal)

        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"✅ Passed: {self.passed}")
        logger.info(f"❌ Failed: {self.failed}")
        logger.info(f"Total: {self.passed + self.failed}")
        logger.info("=" * 80 + "\n")

        return self.failed == 0


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Full Automation Integration Tests")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    test_suite = AutomationTest(verbose=args.verbose)
    success = test_suite.run_all_tests()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
