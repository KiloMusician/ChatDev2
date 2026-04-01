"""Culture Ship plugin — pytest test runner with structured pass/fail output."""

from __future__ import annotations

import subprocess
from typing import Any


class PytestRunnerPlugin:
    """Run pytest and return structured results for Culture Ship analysis."""

    def __init__(self) -> None:
        """Initialize PytestRunnerPlugin."""
        self.name = "pytest_runner"
        self.description = "Run tests via pytest and surface failures for triage"

    def analyze(self, targets: list[str], dry_run: bool = False) -> dict[str, Any]:
        """Run pytest in collect-only mode to enumerate tests without executing them."""
        collect_cmd = [
            "python",
            "-m",
            "pytest",
            *targets,
            "--collect-only",
            "-q",
            "--no-header",
        ]
        try:
            result = subprocess.run(
                collect_cmd, capture_output=True, text=True, timeout=60, check=False
            )
            lines = result.stdout.splitlines()
            tests = [ln.strip() for ln in lines if "::" in ln]
            return {
                "plugin": self.name,
                "tests_discovered": len(tests),
                "test_ids": tests[:50],  # cap to avoid huge payloads
                "dry_run": dry_run,
                "targets": targets,
            }
        except subprocess.TimeoutExpired as e:
            return {"plugin": self.name, "error": str(e), "tests_discovered": 0, "targets": targets}

    def fix(self, analysis: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
        """Execute the tests and return a pass/fail summary."""
        targets = analysis.get("targets", ["."])
        if dry_run:
            return {"plugin": self.name, "fixes_applied": 0, "files_modified": []}

        cmd = [
            "python",
            "-m",
            "pytest",
            *targets,
            "-q",
            "--no-header",
            "--tb=no",
            "--json-report",
            "--json-report-file=/dev/null",
        ]
        # Fallback without json-report if plugin not installed
        fallback_cmd = [
            "python",
            "-m",
            "pytest",
            *targets,
            "-q",
            "--no-header",
            "--tb=line",
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, check=False)
            if "unrecognized arguments" in result.stderr or result.returncode == 4:
                result = subprocess.run(
                    fallback_cmd, capture_output=True, text=True, timeout=300, check=False
                )
        except subprocess.TimeoutExpired:
            return {
                "plugin": self.name,
                "error": "pytest timed out (300s)",
                "fixes_applied": 0,
                "files_modified": [],
            }

        lines = (result.stdout + result.stderr).splitlines()
        passed = failed = errors = skipped = 0
        for line in lines:
            low = line.lower()
            if "passed" in low:
                import re

                m = re.search(r"(\d+) passed", low)
                if m:
                    passed = int(m.group(1))
            if "failed" in low:
                import re

                m = re.search(r"(\d+) failed", low)
                if m:
                    failed = int(m.group(1))
            if "error" in low:
                import re

                m = re.search(r"(\d+) error", low)
                if m:
                    errors = int(m.group(1))
            if "skipped" in low:
                import re

                m = re.search(r"(\d+) skipped", low)
                if m:
                    skipped = int(m.group(1))

        return {
            "plugin": self.name,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "exit_code": result.returncode,
            "summary": lines[-3:],
            "fixes_applied": 0,
            "files_modified": [],
        }
