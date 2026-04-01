#!/usr/bin/env python3
"""Coding Fundamentals Auto-Fix Script
Scans and fixes common Python coding issues across the codebase

OmniTag: {
    "purpose": "Automated code quality improvement",
    "tags": ["CodeQuality", "Automation", "BestPractices"],
    "category": "development_tools",
    "evolution_stage": "v1.0"
}
"""

import ast
import re
import sys
from collections import defaultdict
from pathlib import Path


class CodingFundamentalsScanner:
    """Scans Python files for coding fundamental issues"""

    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path)
        self.issues = defaultdict(list)
        self.stats = defaultdict(int)

    def scan_all(self) -> dict[str, list]:
        """Scan all Python files for issues"""
        print("🔍 Scanning repository for coding fundamental issues...")

        py_files = list(self.repo_path.rglob("*.py"))
        print(f"📄 Found {len(py_files)} Python files to scan")

        for file_path in py_files:
            # Skip cache and virtual environment directories
            if any(skip in str(file_path) for skip in ["__pycache__", ".venv", "venv", ".git"]):
                continue

            self._scan_file(file_path)

        return dict(self.issues)

    def _scan_file(self, file_path: Path):
        """Scan a single file for issues"""
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = file_path.read_text(encoding="latin-1")
            except (OSError, UnicodeDecodeError):
                return  # Skip binary or unreadable files

        relative_path = file_path.relative_to(self.repo_path)

        # Check for bare except clauses
        self._check_bare_except(content, relative_path)

        # Check for missing timeouts in requests
        self._check_missing_timeouts(content, relative_path)

        # Check for print statements in library code
        self._check_print_statements(content, relative_path, file_path)

        # Check for missing type hints in functions
        self._check_type_hints(content, relative_path)

    def _check_bare_except(self, content: str, file_path: Path):
        """Find bare except: clauses"""
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            # Match bare except: (not except Exception:, except Error:, etc.)
            if re.match(r"^\s*except\s*:\s*$", line):
                self.issues["bare_except"].append(
                    {
                        "file": str(file_path),
                        "line": i,
                        "code": line.strip(),
                        "severity": "CRITICAL",
                        "suggestion": "Replace with specific exception types",
                    }
                )
                self.stats["bare_except"] += 1

    def _check_missing_timeouts(self, content: str, file_path: Path):
        """Find requests.get/post without timeout parameter"""
        if "import requests" not in content:
            return

        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            # Match requests.get() or requests.post() without timeout
            if re.search(r"requests\.(get|post)\([^)]*\)", line):
                if "timeout=" not in line and "timeout =" not in line:
                    self.issues["missing_timeout"].append(
                        {
                            "file": str(file_path),
                            "line": i,
                            "code": line.strip(),
                            "severity": "MEDIUM",
                            "suggestion": "Add timeout parameter (e.g., timeout=30)",
                        }
                    )
                    self.stats["missing_timeout"] += 1

    def _check_print_statements(self, content: str, file_path: Path, full_path: Path):
        """Find print() statements in library code (not CLI tools)"""
        # Skip files in specific directories that are allowed to use print
        allowed_dirs = ["diagnostics", "tools", "scripts", "consciousness"]
        if any(d in str(file_path) for d in allowed_dirs):
            return

        # Skip if file has if __name__ == '__main__': (CLI entry point)
        if "if __name__ == '__main__':" in content or 'if __name__ == "__main__":' in content:
            return

        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            if re.search(r"\bprint\s*\(", line) and not line.strip().startswith("#"):
                self.issues["print_statement"].append(
                    {
                        "file": str(file_path),
                        "line": i,
                        "code": line.strip(),
                        "severity": "MEDIUM",
                        "suggestion": "Use logger.info/debug instead of print",
                    }
                )
                self.stats["print_statement"] += 1

    def _check_type_hints(self, content: str, file_path: Path):
        """Check for missing type hints in function definitions"""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return  # Skip files with syntax errors

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function has type hints
                has_return_hint = node.returns is not None
                has_arg_hints = any(arg.annotation is not None for arg in node.args.args)

                # Skip private functions and __init__, __str__, etc.
                if node.name.startswith("_") and not node.name.startswith("__"):
                    continue

                if not has_return_hint and not has_arg_hints:
                    self.issues["missing_type_hints"].append(
                        {
                            "file": str(file_path),
                            "line": node.lineno,
                            "function": node.name,
                            "severity": "LOW",
                            "suggestion": "Add type hints to function parameters and return value",
                        }
                    )
                    self.stats["missing_type_hints"] += 1

    def generate_report(self) -> str:
        """Generate a formatted report of issues"""
        report = []
        report.append("=" * 80)
        report.append("🔍 CODING FUNDAMENTALS SCAN RESULTS")
        report.append("=" * 80)
        report.append("")

        # Summary
        report.append("📊 SUMMARY:")
        total_issues = sum(len(issues) for issues in self.issues.values())
        report.append(f"   Total Issues Found: {total_issues}")
        report.append("")

        for issue_type, count in sorted(self.stats.items(), key=lambda x: x[1], reverse=True):
            report.append(f"   {issue_type}: {count}")

        report.append("")
        report.append("-" * 80)

        # Detailed issues by type
        severity_order = {"CRITICAL": 0, "MEDIUM": 1, "LOW": 2}

        for issue_type, issues_list in sorted(self.issues.items()):
            if not issues_list:
                continue

            report.append("")
            report.append(f"🔴 {issue_type.upper().replace('_', ' ')} ({len(issues_list)} found)")
            report.append("-" * 80)

            # Sort by severity
            sorted_issues = sorted(
                issues_list,
                key=lambda x: severity_order.get(x.get("severity", "LOW"), 3),
            )

            for issue in sorted_issues[:10]:  # Show first 10 per type
                severity_icon = {"CRITICAL": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(issue.get("severity", "LOW"), "⚪")

                report.append(f"{severity_icon} {issue['file']}:{issue['line']}")
                report.append(f"   Code: {issue.get('code', issue.get('function', 'N/A'))}")
                report.append(f"   💡 {issue['suggestion']}")
                report.append("")

            if len(issues_list) > 10:
                report.append(f"   ... and {len(issues_list) - 10} more")
                report.append("")

        report.append("=" * 80)
        report.append("✅ Scan complete!")
        report.append("")
        report.append("📋 Next steps:")
        report.append("   1. Review CRITICAL issues first")
        report.append("   2. Fix bare except clauses with specific exceptions")
        report.append("   3. Add timeout parameters to network requests")
        report.append("   4. See docs/CODING_FUNDAMENTALS_AUDIT.md for guidance")
        report.append("=" * 80)

        return "\n".join(report)

    def save_report(self, output_path: Path):
        """Save report to file"""
        report = self.generate_report()
        output_path.write_text(report, encoding="utf-8")
        print(f"📄 Report saved to: {output_path}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Scan Python codebase for coding fundamental issues")
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Repository path to scan (default: current directory)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("Reports/coding_fundamentals_scan.txt"),
        help="Output report path",
    )
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")

    args = parser.parse_args()

    # Run scan
    scanner = CodingFundamentalsScanner(args.repo)
    scanner.scan_all()

    # Generate and display report
    report = scanner.generate_report()
    print(report)

    # Save report
    args.output.parent.mkdir(parents=True, exist_ok=True)
    scanner.save_report(args.output)

    # Exit with code based on critical issues
    critical_count = scanner.stats.get("bare_except", 0)
    if critical_count > 0:
        print(f"\n⚠️  Found {critical_count} CRITICAL issues that should be fixed")
        sys.exit(1)
    else:
        print("\n✅ No critical issues found!")
        sys.exit(0)


if __name__ == "__main__":
    main()
