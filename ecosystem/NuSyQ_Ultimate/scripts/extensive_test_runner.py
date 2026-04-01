#!/usr/bin/env python3
"""
🎯 EXTREME AUTONOMOUS TESTING ENGINE
=====================================
Runs ALL tests, identifies failures, and generates comprehensive analysis.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class ExtensiveTestRunner:
    """Run and analyze all tests in the workspace"""

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "test_suites": [],
            "summary": {
                "total_collected": 0,
                "total_passed": 0,
                "total_failed": 0,
                "total_errors": 0,
                "total_skipped": 0,
            },
        }

    def discover_test_files(self) -> List[Path]:
        """Find all test files"""
        test_files = []

        # Pattern 1: test_*.py in root
        test_files.extend(self.workspace.glob("test_*.py"))

        # Pattern 2: test_*.py in tests/
        if (self.workspace / "tests").exists():
            test_files.extend((self.workspace / "tests").glob("test_*.py"))
            test_files.extend((self.workspace / "tests").glob("**/test_*.py"))

        # Pattern 3: test_*.py in scripts/
        if (self.workspace / "scripts").exists():
            test_files.extend((self.workspace / "scripts").glob("test_*.py"))

        # Pattern 4: MCP server tests
        if (self.workspace / "mcp_server" / "tests").exists():
            test_files.extend((self.workspace / "mcp_server" / "tests").glob("test_*.py"))

        return sorted(set(test_files))

    def run_test_file(self, test_file: Path) -> Dict:
        """Run a single test file"""
        print(f"🧪 Testing: {test_file.relative_to(self.workspace)}")

        result = {
            "file": str(test_file.relative_to(self.workspace)),
            "collected": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "duration": 0.0,
            "output": "",
        }

        try:
            proc = subprocess.run(
                ["pytest", str(test_file), "-v", "--tb=short", "--maxfail=10"],
                capture_output=True,
                text=True,
                timeout=300,  # 5 min timeout per file
                cwd=str(self.workspace),
                check=False,
            )

            result["output"] = proc.stdout + proc.stderr

            # Parse pytest output
            for line in result["output"].split("\n"):
                if " PASSED" in line:
                    result["passed"] += 1
                elif " FAILED" in line:
                    result["failed"] += 1
                elif " ERROR" in line:
                    result["errors"] += 1
                elif " SKIPPED" in line:
                    result["skipped"] += 1
                elif "collected" in line and "item" in line:
                    # Extract collected count
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "collected" and i + 1 < len(parts):
                            try:
                                result["collected"] = int(parts[i + 1])
                            except (ValueError, IndexError) as e:
                                print(f"⚠️ Warning: Failed to parse collected count: {e}")
                elif " passed in " in line:
                    # Extract duration
                    try:
                        duration_str = line.split(" passed in ")[1].split("s")[0]
                        result["duration"] = float(duration_str)
                    except (ValueError, IndexError) as e:
                        print(f"⚠️ Warning: Failed to parse duration: {e}")

        except subprocess.TimeoutExpired:
            result["errors"] = 1
            result["output"] = "TIMEOUT: Test file exceeded 5 minute limit"
        except (subprocess.SubprocessError, OSError, ValueError, TypeError) as e:
            result["errors"] = 1
            result["output"] = f"ERROR: {e}"

        # Update summary
        self.results["summary"]["total_collected"] += result["collected"]
        self.results["summary"]["total_passed"] += result["passed"]
        self.results["summary"]["total_failed"] += result["failed"]
        self.results["summary"]["total_errors"] += result["errors"]
        self.results["summary"]["total_skipped"] += result["skipped"]

        # Print status
        status = (
            "✅"
            if result["passed"] > 0 and result["failed"] == 0 and result["errors"] == 0
            else "❌"
        )
        print(
            f"  {status} {result['passed']}P {result['failed']}F {result['errors']}E {result['skipped']}S"
        )

        return result

    def run_all_tests(self):
        """Run all discovered tests"""
        print("=" * 70)
        print("🎯 EXTENSIVE AUTONOMOUS TESTING ENGINE")
        print("=" * 70)

        test_files = self.discover_test_files()
        print(f"📁 Discovered {len(test_files)} test files\n")

        for test_file in test_files:
            result = self.run_test_file(test_file)
            self.results["test_suites"].append(result)

        # Generate summary
        self._print_summary()
        self._save_results()

    def _print_summary(self):
        """Print comprehensive summary"""
        s = self.results["summary"]

        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 70)
        print(f"Test Suites:    {len(self.results['test_suites'])}")
        print(f"Tests Collected: {s['total_collected']}")
        print(f"✅ Passed:       {s['total_passed']}")
        print(f"❌ Failed:       {s['total_failed']}")
        print(f"⚠️  Errors:       {s['total_errors']}")
        print(f"⏭️  Skipped:      {s['total_skipped']}")

        if s["total_collected"] > 0:
            pass_rate = (s["total_passed"] / s["total_collected"]) * 100
            print(f"\n🎯 Pass Rate:    {pass_rate:.1f}%")

        print("=" * 70)

        # Show failures
        failures = [r for r in self.results["test_suites"] if r["failed"] > 0 or r["errors"] > 0]
        if failures:
            print(f"\n❌ FAILING TEST SUITES ({len(failures)}):")
            for r in failures:
                print(f"   • {r['file']}: {r['failed']} failed, {r['errors']} errors")

    def _save_results(self):
        """Save results to JSON"""
        results_file = (
            self.workspace
            / "Reports"
            / f"TEST_RESULTS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        results_file.parent.mkdir(exist_ok=True)

        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n💾 Results saved: {results_file.name}")

        # Also generate markdown report
        self._generate_markdown_report()

    def _generate_markdown_report(self):
        """Generate human-readable markdown report"""
        s = self.results["summary"]
        report_file = (
            self.workspace
            / "Reports"
            / f"TEST_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )

        report = f"""# 🧪 Comprehensive Test Report

**Generated**: {self.results["timestamp"]}

## Summary

| Metric | Count |
|--------|-------|
| Test Suites | {len(self.results["test_suites"])} |
| Tests Collected | {s["total_collected"]} |
| ✅ Passed | {s["total_passed"]} |
| ❌ Failed | {s["total_failed"]} |
| ⚠️ Errors | {s["total_errors"]} |
| ⏭️ Skipped | {s["total_skipped"]} |
"""

        if s["total_collected"] > 0:
            pass_rate = (s["total_passed"] / s["total_collected"]) * 100
            report += f"\n**Pass Rate**: {pass_rate:.1f}%\n"

        # Detailed results
        report += "\n## Detailed Results\n\n"
        for r in self.results["test_suites"]:
            status = (
                "✅ PASS"
                if r["passed"] > 0 and r["failed"] == 0 and r["errors"] == 0
                else "❌ FAIL"
            )
            report += f"### {status}: `{r['file']}`\n\n"
            report += f"- Collected: {r['collected']}\n"
            report += f"- Passed: {r['passed']}\n"
            report += f"- Failed: {r['failed']}\n"
            report += f"- Errors: {r['errors']}\n"
            report += f"- Duration: {r['duration']:.2f}s\n\n"

        # Recommendations
        report += "\n## Recommendations\n\n"
        if s["total_failed"] > 0:
            report += "1. Use autonomous self-healer to fix failing tests\n"
            report += "2. Run ChatDev to regenerate broken code\n"
        if s["total_errors"] > 0:
            report += "1. Fix import errors and missing dependencies\n"
            report += "2. Check test file paths and module structure\n"
        if s["total_passed"] == s["total_collected"]:
            report += "1. ✨ All tests passing! Consider adding more tests.\n"
            report += "2. Implement test coverage measurement.\n"

        report_file.write_text(report, encoding="utf-8")
        print(f"📄 Report saved: {report_file.name}")


def main():
    workspace = Path(__file__).parent.parent
    runner = ExtensiveTestRunner(workspace)
    runner.run_all_tests()


if __name__ == "__main__":
    main()
