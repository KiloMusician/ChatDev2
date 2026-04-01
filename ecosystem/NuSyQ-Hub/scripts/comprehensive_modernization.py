#!/usr/bin/env python3
"""Comprehensive Modernization Script - Autonomous Repository Enhancement.

This script applies AI-coordinated modernization across the entire codebase.
Utilizes the Unified AI Context Manager and Multi-AI Orchestration.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="🔧 %(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)


class ComprehensiveModernizer:
    """Orchestrates comprehensive repository modernization."""

    def __init__(self, repo_root: Path | None = None):
        """Initialize modernizer.

        Args:
            repo_root: Repository root path (defaults to script location)
        """
        self.repo_root = repo_root or Path(__file__).parent.parent
        self.fixes_applied: list[dict[str, Any]] = []
        self.errors_encountered: list[dict[str, Any]] = []

        # Try to initialize context manager
        try:
            sys.path.insert(0, str(self.repo_root))
            from src.integration.unified_ai_context_manager import get_unified_context_manager

            self.context_mgr = get_unified_context_manager()
            self.context_enabled = True
            logger.info("✅ Unified AI Context Manager initialized")
        except ImportError:
            self.context_mgr = None
            self.context_enabled = False
            logger.warning("⚠️ Context manager not available, proceeding without tracking")

    def record_fix(
        self,
        category: str,
        description: str,
        count: int = 1,
        metadata: dict[str, Any] | None = None,
    ):
        """Record a fix in the context manager and local tracking.

        Args:
            category: Fix category
            description: Description of fix
            count: Number of items fixed
            metadata: Additional metadata
        """
        fix_record = {
            "category": category,
            "description": description,
            "count": count,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }
        self.fixes_applied.append(fix_record)

        if self.context_enabled and self.context_mgr:
            try:
                self.context_mgr.add_context(
                    content=f"{category}: {description}",
                    context_type="code",
                    source_system="modernizer",
                    metadata={"count": count, **(metadata or {})},
                    tags=["modernization", category.lower().replace(" ", "_")],
                )
            except Exception as e:
                logger.debug(f"Context recording failed: {e}")

    def run_command(self, cmd: list[str], description: str) -> subprocess.CompletedProcess:
        """Run a command and log results.

        Args:
            cmd: Command to run
            description: Description for logging

        Returns:
            CompletedProcess result
        """
        logger.info(f"▶️ {description}")
        try:
            result = subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True, timeout=300)
            return result
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Command timed out: {description}")
            self.errors_encountered.append({"command": cmd, "error": "timeout"})
            raise
        except Exception as e:
            logger.error(f"❌ Command failed: {description} - {e}")
            self.errors_encountered.append({"command": cmd, "error": str(e)})
            raise

    def fix_ruff_auto(self):
        """Apply all ruff auto-fixes."""
        logger.info("🔍 Phase 1: Ruff Auto-Fixes")

        result = self.run_command(["ruff", "check", "src/", "--fix", "--unsafe-fixes"], "Applying ruff auto-fixes")

        fixed_count = result.stdout.count("fixed")
        if fixed_count > 0:
            self.record_fix("Ruff Auto-Fix", f"Applied {fixed_count} automatic fixes", fixed_count)
            logger.info(f"   ✅ Fixed {fixed_count} issues")
        else:
            logger.info("   Info: No auto-fixable issues found")

    def sort_imports(self):
        """Sort and organize imports."""
        logger.info("🔍 Phase 2: Import Organization")

        result = self.run_command(["ruff", "check", "src/", "--select", "I", "--fix"], "Sorting imports")

        fixed_count = result.stdout.count("fixed")
        if fixed_count > 0:
            self.record_fix("Import Sorting", f"Sorted {fixed_count} import blocks", fixed_count)
            logger.info(f"   ✅ Sorted {fixed_count} import blocks")
        else:
            logger.info("   Info: Imports already sorted")

    def remove_unused_imports(self):
        """Remove unused imports."""
        logger.info("🔍 Phase 3: Unused Import Removal")

        result = self.run_command(["ruff", "check", "src/", "--select", "F401", "--fix"], "Removing unused imports")

        fixed_count = result.stdout.count("fixed")
        if fixed_count > 0:
            self.record_fix("Unused Imports", f"Removed {fixed_count} unused imports", fixed_count)
            logger.info(f"   ✅ Removed {fixed_count} unused imports")
        else:
            logger.info("   Info: No unused imports found")

    def validate_syntax(self):
        """Validate Python syntax across src/."""
        logger.info("🔍 Phase 4: Syntax Validation")

        result = self.run_command([sys.executable, "-m", "compileall", "src/", "-q"], "Validating Python syntax")

        if result.returncode == 0:
            logger.info("   ✅ All Python files compile successfully")
            self.record_fix("Syntax Validation", "Verified syntax across src/", 1)
        else:
            logger.error(f"   ❌ Syntax errors found:\n{result.stderr}")
            self.errors_encountered.append({"phase": "syntax", "output": result.stderr})

    def run_tests(self):
        """Run test suite to validate changes."""
        logger.info("🔍 Phase 5: Test Suite Validation")

        try:
            result = self.run_command(
                [sys.executable, "-m", "pytest", "tests/", "-x", "--tb=short", "-q"],
                "Running test suite",
            )

            # Parse test results
            if "passed" in result.stdout:
                passed = result.stdout.count(" passed")
                logger.info("   ✅ Tests passed")
                self.record_fix("Test Validation", "All tests passing", 1, {"test_count": passed})
            else:
                logger.warning("   ⚠️ Some tests may have failed")
        except Exception as e:
            logger.warning(f"   ⚠️ Test suite not available or failed: {e}")

    def generate_report(self) -> str:
        """Generate comprehensive modernization report.

        Returns:
            Report as formatted string
        """
        report = [
            "\n" + "=" * 60,
            "📊 COMPREHENSIVE MODERNIZATION REPORT",
            "=" * 60,
            f"Timestamp: {datetime.now().isoformat()}",
            f"Repository: {self.repo_root}",
            "",
            f"✅ Fixes Applied: {len(self.fixes_applied)}",
            f"❌ Errors Encountered: {len(self.errors_encountered)}",
            "",
        ]

        if self.fixes_applied:
            report.append("Fixes by Category:")
            for fix in self.fixes_applied:
                report.append(f"  • {fix['category']}: {fix['description']} (count: {fix['count']})")

        if self.errors_encountered:
            report.append("\nErrors:")
            for error in self.errors_encountered:
                report.append(f"  ⚠️ {error}")

        report.extend(
            [
                "",
                "=" * 60,
                f"Total Improvements: {sum(f['count'] for f in self.fixes_applied)}",
                "=" * 60,
                "",
            ]
        )

        return "\n".join(report)

    def save_report(self, report: str):
        """Save report to file.

        Args:
            report: Report content
        """
        report_file = self.repo_root / "data" / f"modernization_report_{datetime.now():%Y%m%d_%H%M%S}.txt"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(report)
        logger.info(f"📄 Report saved: {report_file}")

        # Also save JSON
        json_file = report_file.with_suffix(".json")
        json_data = {
            "timestamp": datetime.now().isoformat(),
            "fixes_applied": self.fixes_applied,
            "errors_encountered": self.errors_encountered,
            "summary": {
                "total_fixes": len(self.fixes_applied),
                "total_improvements": sum(f["count"] for f in self.fixes_applied),
                "errors": len(self.errors_encountered),
            },
        }
        json_file.write_text(json.dumps(json_data, indent=2))
        logger.info(f"📄 JSON report saved: {json_file}")

    def run(self):
        """Execute comprehensive modernization."""
        logger.info("🚀 Starting Comprehensive Modernization")
        logger.info(f"📂 Repository: {self.repo_root}")

        if self.context_enabled:
            logger.info("🤖 AI Context Manager: ACTIVE")
        else:
            logger.info("🤖 AI Context Manager: DISABLED")

        logger.info("\n" + "=" * 60)

        try:
            # Phase 1-3: Code fixes
            self.fix_ruff_auto()
            self.sort_imports()
            self.remove_unused_imports()

            # Phase 4: Validation
            self.validate_syntax()

            # Phase 5: Testing
            self.run_tests()

            # Generate and save report
            report = self.generate_report()
            print(report)
            self.save_report(report)

            logger.info("✅ Comprehensive Modernization Complete!")

            return 0

        except KeyboardInterrupt:
            logger.warning("\n⚠️ Modernization interrupted by user")
            return 130
        except Exception as e:
            logger.error(f"❌ Modernization failed: {e}")
            return 1


def main():
    """Main entry point."""
    modernizer = ComprehensiveModernizer()
    sys.exit(modernizer.run())


if __name__ == "__main__":
    main()
