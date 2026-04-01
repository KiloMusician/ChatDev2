import json
import subprocess
from typing import Any


class RuffFixerPlugin:
    """Ruff-based fixer plugin with structured output."""

    def __init__(self) -> None:
        """Initialize RuffFixerPlugin."""
        self.name = "ruff_fixer"
        self.description = "Fix linting issues using ruff"

    def analyze(self, targets: list[str], dry_run: bool = False) -> dict[str, Any]:
        """Analyze targets and return fixable issues."""
        cmd = ["python", "-m", "ruff", "check", *targets, "--select=E,F", "--format=json"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
            issues = json.loads(result.stdout) if result.stdout else []

            # Group by file and error type
            grouped: dict[str, list[dict[str, Any]]] = {}
            for issue in issues:
                file_path = issue.get("filename")
                if not file_path:
                    # Fallback for older ruff JSON formats
                    file_path = issue.get("file")
                if file_path not in grouped:
                    grouped[file_path] = []
                grouped[file_path].append(issue)

            return {
                "plugin": self.name,
                "issues_found": len(issues),
                "issues_by_file": grouped,
                "fixable_issues": self._count_fixable(issues),
                "dry_run": dry_run,
                "targets": targets,
            }
        except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            return {
                "plugin": self.name,
                "error": str(e),
                "issues_found": 0,
                "fixable_issues": 0,
                "targets": targets,
            }

    def fix(self, analysis: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
        """Apply fixes based on analysis."""
        if dry_run or analysis.get("fixable_issues", 0) == 0:
            return {"plugin": self.name, "fixes_applied": 0, "files_modified": []}

        fixes_applied = 0
        files_modified: list[str] = []

        # Run ruff fix on each problematic file
        for file_path in analysis.get("issues_by_file", {}):
            if not file_path:
                continue
            cmd = ["python", "-m", "ruff", "check", file_path, "--select=E,F", "--fix"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if result.returncode == 0:
                fixes_applied += 1
                files_modified.append(file_path)

        return {
            "plugin": self.name,
            "fixes_applied": fixes_applied,
            "files_modified": files_modified,
        }

    def _count_fixable(self, issues: list[dict[str, Any]]) -> int:
        """Count issues that ruff can auto-fix."""
        # Ruff can fix many E/F codes except some syntax errors
        fixable_prefixes = {"E", "F"}
        count = 0
        for issue in issues:
            code = issue.get("code") or issue.get("message_id") or ""
            if isinstance(code, str) and code[:1] in fixable_prefixes:
                count += 1
        return count
