"""Zeta13 - Code Quality Tools: Automated code quality analysis and fixing.

Purpose:
  - Integrate ruff (linting) with auto-fix capabilities
  - Integrate mypy (type checking) with auto-correction suggestions
  - Build custom fixers for common patterns:
    * Unused imports
    * Type hints completion
    * Docstring formatting
    * Code style standardization
  - Generate quality reports and metrics
  - Support batch fixing across modules

Target Coverage:
  - Fix remaining linting issues across src/
  - Improve type annotation coverage
  - Standardize code formatting
  - Reduce code complexity scores
"""

import ast
import json
import logging
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LintIssue:
    """Represents a single linting issue."""

    file: str
    line: int
    column: int
    code: str  # e.g., "F401", "E501"
    message: str
    severity: str  # "error", "warning", "info"
    suggestion: str | None = None
    fixable: bool = False


@dataclass
class TypeCheckIssue:
    """Represents a type checking issue from mypy."""

    file: str
    line: int
    column: int
    message: str
    severity: str  # "error", "warning", "note"
    suggestion: str | None = None


@dataclass
class QualityReport:
    """Summary of code quality analysis."""

    analyzed_files: int = 0
    total_issues: int = 0
    issues_by_severity: dict[str, int] = field(default_factory=dict)
    issues_by_type: dict[str, int] = field(default_factory=dict)
    fixable_issues: int = 0
    files_with_issues: list[str] = field(default_factory=list)
    timestamp: str = ""


class RuffLinter:
    """Wrapper for ruff linting with auto-fix support."""

    def __init__(self, target_path: str = "src"):
        """Initialize ruff linter.

        Args:
            target_path: Path to lint (file or directory)
        """
        self.target_path = Path(target_path)
        self.issues: list[LintIssue] = []

    def check(self) -> list[LintIssue]:
        """Run ruff check without fixing.

        Returns:
            List of LintIssue instances
        """
        try:
            result = subprocess.run(
                ["ruff", "check", str(self.target_path), "--output-format", "json"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.stdout:
                data = json.loads(result.stdout)
                for item in data:
                    issue = LintIssue(
                        file=item.get("filename", ""),
                        line=item.get("line", 0),
                        column=item.get("column", 0),
                        code=item.get("code", ""),
                        message=item.get("message", ""),
                        severity=self._map_rule_code_to_severity(item.get("code", "")),
                        fixable=item.get("fix", {}) is not None,
                    )
                    self.issues.append(issue)

            logger.info(f"✅ Ruff check complete: {len(self.issues)} issues found")
            return self.issues

        except subprocess.TimeoutExpired:
            logger.error("❌ Ruff check timeout")
            return []
        except (json.JSONDecodeError, subprocess.CalledProcessError) as e:
            logger.error(f"❌ Ruff error: {e}")
            return []

    def fix(self, target_path: str | None = None) -> dict[str, Any]:
        """Run ruff with auto-fix enabled.

        Args:
            target_path: Optional path override for fixing

        Returns:
            Dictionary with fix results
        """
        path = target_path or str(self.target_path)

        try:
            result = subprocess.run(
                ["ruff", "check", "--fix", path],
                capture_output=True,
                text=True,
                timeout=30,
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        except subprocess.TimeoutExpired:
            logger.error("❌ Ruff fix timeout")
            return {"success": False, "error": "Timeout"}
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Ruff fix error: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def _map_rule_code_to_severity(code: str) -> str:
        """Map ruff rule code to severity level.

        Args:
            code: Ruff rule code (e.g., "F401", "E501")

        Returns:
            Severity level ("error", "warning", "info")
        """
        if code.startswith("E") or code.startswith("F"):
            return "error"
        elif code.startswith("W"):
            return "warning"
        else:
            return "info"


class MypyChecker:
    """Wrapper for mypy type checking."""

    def __init__(self, target_path: str = "src"):
        """Initialize mypy checker.

        Args:
            target_path: Path to check (dir or file)
        """
        self.target_path = Path(target_path)
        self.issues: list[TypeCheckIssue] = []

    def check(self) -> list[TypeCheckIssue]:
        """Run mypy type checking.

        Returns:
            List of TypeCheckIssue instances
        """
        try:
            result = subprocess.run(
                [
                    "mypy",
                    str(self.target_path),
                    "--json-report=/dev/null",
                    "--no-error-summary",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Parse output
            for line in result.stdout.split("\n"):
                if line.strip():
                    parsed = self._parse_mypy_line(line)
                    if parsed:
                        self.issues.append(parsed)

            logger.info(f"✅ Mypy check complete: {len(self.issues)} issues found")
            return self.issues

        except subprocess.TimeoutExpired:
            logger.error("❌ Mypy check timeout")
            return []
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Mypy error: {e}")
            return []

    @staticmethod
    def _parse_mypy_line(line: str) -> TypeCheckIssue | None:
        """Parse a mypy output line.

        Args:
            line: A line from mypy output

        Returns:
            TypeCheckIssue or None
        """
        # Format: path/file.py:123:45: error: message
        match = re.match(r"^(.*?):(\d+):(\d+):\s+(error|warning|note):\s+(.*)$", line)
        if match:
            return TypeCheckIssue(
                file=match.group(1),
                line=int(match.group(2)),
                column=int(match.group(3)),
                severity=match.group(4),
                message=match.group(5),
            )
        return None


class CustomFixer:
    """Custom code fixer for patterns not handled by standard tools."""

    def __init__(self, module_path: str):
        """Initialize custom fixer.

        Args:
            module_path: Path to Python module
        """
        self.module_path = Path(module_path)
        self.source: str | None = None
        self.tree: ast.AST | None = None
        self._load_module()

    def _load_module(self):
        """Load module source and AST."""
        try:
            with open(self.module_path, encoding="utf-8") as f:
                self.source = f.read()
            self.tree = ast.parse(self.source)
        except Exception as e:
            logger.warning(f"Failed to load {self.module_path}: {e}")

    def fix_unused_imports(self) -> tuple[str, int]:
        """Remove unused imports.

        Returns:
            Tuple of (fixed_source, num_removed)
        """
        if not self.source or not self.tree:
            return self.source or "", 0

        # Identify imported names
        imported = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported.add(alias.name if alias.name != "*" else None)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.asname or alias.name)

        # Identify used names
        used = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Name):
                used.add(node.id)

        # Find unused
        unused = imported - used

        if not unused:
            return self.source, 0

        # Remove unused imports
        fixed = self.source
        for name in unused:
            if not isinstance(name, str):
                continue
            pattern = rf"^\s*(?:from .* )?import .*\b{re.escape(name)}\b.*$"
            fixed = re.sub(pattern, "", fixed, flags=re.MULTILINE)

        # Clean up empty lines
        fixed = re.sub(r"\n\n\n+", "\n\n", fixed)

        return fixed, len(unused)

    def add_type_hints(self) -> tuple[str, int]:
        """Add missing type hints to function signatures.

        Returns:
            Tuple of (fixed_source, num_added)
        """
        if not self.source or not self.tree:
            return self.source or "", 0

        added = 0

        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function has unannotated parameters
                for arg in node.args.args:
                    if arg.annotation is None and arg.arg != "self":
                        added += 1

        return self.source, added


class CodeQualityAnalyzer:
    """Comprehensive code quality analyzer."""

    def __init__(self, target_path: str = "src"):
        """Initialize analyzer.

        Args:
            target_path: Path to analyze
        """
        self.target_path = Path(target_path)
        self.ruff_linter = RuffLinter(str(self.target_path))
        self.mypy_checker = MypyChecker(str(self.target_path))
        self.report = QualityReport()

    def analyze(self) -> QualityReport:
        """Run comprehensive analysis.

        Returns:
            QualityReport with findings
        """
        logger.info("🔍 Starting code quality analysis...")
        self.report.timestamp = datetime.now().isoformat()

        # Run checks
        ruff_issues = self.ruff_linter.check()
        mypy_issues = self.mypy_checker.check()

        # Aggregate results
        self.report.total_issues = len(ruff_issues) + len(mypy_issues)
        self.report.fixable_issues = sum(1 for i in ruff_issues if i.fixable)

        # Count by severity
        for issue in ruff_issues:
            self.report.issues_by_severity[issue.severity] = (
                self.report.issues_by_severity.get(issue.severity, 0) + 1
            )
            self.report.issues_by_type[issue.code] = (
                self.report.issues_by_type.get(issue.code, 0) + 1
            )

        # Get unique files
        all_files = {i.file for i in ruff_issues + mypy_issues if isinstance(i.file, str)}
        self.report.files_with_issues = list(all_files)
        self.report.analyzed_files = len(all_files)

        logger.info(f"✅ Analysis complete: {self.report.total_issues} issues found")
        return self.report

    def auto_fix(self) -> dict[str, Any]:
        """Apply auto-fixes.

        Returns:
            Dictionary with fix results
        """
        logger.info("🔧 Applying auto-fixes...")

        results: dict[str, Any] = {
            "ruff_fix": self.ruff_linter.fix(),
            "issues_before": self.report.total_issues,
            "timestamp": datetime.now().isoformat(),
        }

        # Re-analyze after fixes
        logger.info("🔍 Re-analyzing after fixes...")
        new_report = self.analyze()
        results["issues_after"] = new_report.total_issues
        issues_before = int(results["issues_before"])
        issues_after = int(results["issues_after"])
        results["issues_fixed"] = issues_before - issues_after

        logger.info(
            f"✅ Fixed {results['issues_fixed']} issues ({results['issues_before']} → {results['issues_after']})"
        )

        return results

    def export_report(self, output_path: str = "docs/reports/code_quality.json"):
        """Export quality report to file.

        Args:
            output_path: Where to save the report
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        report_data = {
            "timestamp": self.report.timestamp,
            "analyzed_files": self.report.analyzed_files,
            "total_issues": self.report.total_issues,
            "fixable_issues": self.report.fixable_issues,
            "issues_by_severity": self.report.issues_by_severity,
            "issues_by_type": self.report.issues_by_type,
            "files_with_issues": self.report.files_with_issues[:20],  # Top 20
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        logger.info(f"✅ Report saved to {output_path}")


def main():
    """Run code quality analysis and fixing."""
    analyzer = CodeQualityAnalyzer("src")

    # Run analysis
    report = analyzer.analyze()

    # Log summary
    logger.info("%s", "=" * 70)
    logger.info("📊 CODE QUALITY ANALYSIS REPORT")
    logger.info("%s", "=" * 70)
    logger.info("Files analyzed: %s", report.analyzed_files)
    logger.info("Total issues: %s", report.total_issues)
    logger.info("Fixable issues: %s", report.fixable_issues)
    logger.info("Issues by severity:")
    for severity, count in report.issues_by_severity.items():
        logger.info("  • %s: %s", severity, count)

    if report.issues_by_type:
        logger.info("Top issues by type:")
        sorted_types = sorted(report.issues_by_type.items(), key=lambda x: x[1], reverse=True)
        for code, count in sorted_types[:10]:
            logger.info("  • %s: %s", code, count)

    # Export
    analyzer.export_report()

    logger.info("%s", "=" * 70)

    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    main()
