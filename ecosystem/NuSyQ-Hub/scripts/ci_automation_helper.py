#!/usr/bin/env python3
"""CI/CD Automation Helper
Integrates with Guild Board for automated testing and quality checks.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.terminal_output import to_errors, to_main, to_metrics, to_suggestions


class CIAutomationHelper:
    """Automated CI/CD integration with Guild Board."""

    def __init__(self):
        self.root = Path(__file__).parent.parent
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": [],
            "total_errors": 0,
            "total_warnings": 0,
            "status": "unknown",
        }

    def run_ruff_check(self) -> dict[str, Any]:
        """Run ruff linting on entire codebase."""
        to_main("Running ruff linting...")
        try:
            result = subprocess.run(
                ["ruff", "check", "src/", "--output-format=json"],
                capture_output=True,
                text=True,
                cwd=self.root,
            )
            errors = json.loads(result.stdout) if result.stdout else []
            check_result = {
                "name": "ruff_lint",
                "status": "pass" if len(errors) == 0 else "fail",
                "errors": len(errors),
                "details": errors[:10],  # First 10 errors
            }
            to_metrics(f"Ruff: {len(errors)} errors found")
            return check_result
        except Exception as e:
            to_errors(f"Ruff check failed: {e}")
            return {"name": "ruff_lint", "status": "error", "message": str(e)}

    def run_mypy_check(self) -> dict[str, Any]:
        """Run mypy type checking on guild module."""
        to_main("Running mypy type checking...")
        try:
            result = subprocess.run(
                ["python", "-m", "mypy", "src/guild/", "--no-error-summary"],
                capture_output=True,
                text=True,
                cwd=self.root,
            )
            error_count = result.stdout.count("error:")
            check_result = {
                "name": "mypy_types",
                "status": "pass" if error_count == 0 else "fail",
                "errors": error_count,
                "output": result.stdout[:500],
            }
            to_metrics(f"Mypy: {error_count} type errors found")
            return check_result
        except Exception as e:
            to_errors(f"Mypy check failed: {e}")
            return {"name": "mypy_types", "status": "error", "message": str(e)}

    def run_pytest(self) -> dict[str, Any]:
        """Run pytest suite."""
        to_main("Running pytest suite...")
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-q", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=self.root,
                timeout=300,
            )
            # Parse pytest output for pass/fail counts
            passed = result.stdout.count(" passed")
            failed = result.stdout.count(" failed")
            check_result = {
                "name": "pytest",
                "status": "pass" if result.returncode == 0 else "fail",
                "passed": passed,
                "failed": failed,
                "output": result.stdout[-500:],
            }
            to_metrics(f"Pytest: {passed} passed, {failed} failed")
            return check_result
        except subprocess.TimeoutExpired:
            to_errors("Pytest timed out after 5 minutes")
            return {"name": "pytest", "status": "timeout", "message": "Timeout after 5min"}
        except Exception as e:
            to_errors(f"Pytest failed: {e}")
            return {"name": "pytest", "status": "error", "message": str(e)}

    def run_guild_validation(self) -> dict[str, Any]:
        """Validate guild board system."""
        to_main("Validating guild board...")
        try:
            result = subprocess.run(
                ["python", "scripts/start_nusyq.py", "guild_status"],
                capture_output=True,
                text=True,
                cwd=self.root,
                timeout=30,
            )
            check_result = {
                "name": "guild_validation",
                "status": "pass" if result.returncode == 0 else "fail",
                "output": result.stdout[:300],
            }
            to_metrics("Guild board validation complete")
            return check_result
        except Exception as e:
            to_errors(f"Guild validation failed: {e}")
            return {"name": "guild_validation", "status": "error", "message": str(e)}

    def run_all_checks(self) -> dict[str, Any]:
        """Run all CI checks."""
        to_main("Starting CI automation checks...")

        # Run all checks
        self.results["checks"].append(self.run_ruff_check())
        self.results["checks"].append(self.run_mypy_check())
        self.results["checks"].append(self.run_guild_validation())
        # self.results["checks"].append(self.run_pytest())  # Optional - can be slow

        # Calculate totals
        for check in self.results["checks"]:
            if "errors" in check:
                self.results["total_errors"] += check["errors"]
            if "failed" in check:
                self.results["total_errors"] += check["failed"]

        # Determine overall status
        failed_checks = [c for c in self.results["checks"] if c["status"] != "pass"]
        if not failed_checks:
            self.results["status"] = "pass"
            to_main("✅ All CI checks passed!")
        else:
            self.results["status"] = "fail"
            to_errors(f"❌ {len(failed_checks)} checks failed")
            for check in failed_checks:
                to_suggestions(f"Fix {check['name']}: {check.get('errors', 0)} issues")

        # Save results
        results_file = self.root / "state" / "ci_results.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)

        to_metrics(f"CI results saved to: {results_file}")
        return self.results

    def generate_badge_data(self) -> dict[str, str]:
        """Generate badge data for README."""
        status = self.results["status"]
        color = "green" if status == "pass" else "red"
        return {
            "schemaVersion": 1,
            "label": "CI Status",
            "message": status.upper(),
            "color": color,
        }


def main():
    """Run CI automation."""
    helper = CIAutomationHelper()
    results = helper.run_all_checks()

    # Print summary
    print("\n" + "=" * 60)
    print("CI AUTOMATION SUMMARY")
    print("=" * 60)
    print(f"Status: {results['status'].upper()}")
    print(f"Total Errors: {results['total_errors']}")
    print(f"Checks Run: {len(results['checks'])}")
    print("\nCheck Results:")
    for check in results["checks"]:
        status_icon = "✅" if check["status"] == "pass" else "❌"
        print(f"  {status_icon} {check['name']}: {check['status']}")
    print("=" * 60)

    # Exit with appropriate code
    sys.exit(0 if results["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
