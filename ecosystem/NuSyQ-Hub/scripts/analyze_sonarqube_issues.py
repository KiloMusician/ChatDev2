#!/usr/bin/env python3
"""Analyze SonarQube Issues and Create Remediation Quests.

This script looks for SonarQube diagnostic markers in Python files
and creates actionable quests to fix them.
"""

import json
import re
import tokenize
from collections import defaultdict
from io import StringIO
from pathlib import Path

TODO_FIXME_RE = re.compile(r"\b(TODO|FIXME)\b", re.IGNORECASE)


def find_sonarqube_issues_in_file(file_path: Path) -> list[dict]:
    """Find SonarQube-style issues in a Python file."""
    issues = []

    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")
        comment_lines: dict[int, str] = {}
        try:
            for token in tokenize.generate_tokens(StringIO(content).readline):
                if token.type == tokenize.COMMENT:
                    comment_lines[token.start[0]] = token.string
        except tokenize.TokenError:
            comment_lines = {}

        for line_num, line in enumerate(lines, 1):
            # Common SonarQube patterns

            # S1192: String literals should not be duplicated
            if line.count('"') > 6 or line.count("'") > 6:
                issues.append(
                    {
                        "file": str(file_path),
                        "line": line_num,
                        "code": "S1192",
                        "message": "String literals should not be duplicated",
                        "severity": "info",
                    }
                )

            # S1481: Unused local variables
            if re.search(r"^\s*(\w+)\s*=\s*.*#.*unused", line, re.IGNORECASE):
                issues.append(
                    {
                        "file": str(file_path),
                        "line": line_num,
                        "code": "S1481",
                        "message": "Unused local variable",
                        "severity": "warning",
                    }
                )

            # S1135: TODO/FIXME tags in comments (closer to Sonar semantics)
            comment = comment_lines.get(line_num, "")
            if comment and TODO_FIXME_RE.search(comment):
                issues.append(
                    {
                        "file": str(file_path),
                        "line": line_num,
                        "code": "S1135",
                        "message": "Complete TODO/FIXME",
                        "severity": "info",
                    }
                )

            # S125: Commented out code
            if re.match(r"^\s*#\s*(def |class |import |from )", line):
                issues.append(
                    {
                        "file": str(file_path),
                        "line": line_num,
                        "code": "S125",
                        "message": "Remove commented out code",
                        "severity": "info",
                    }
                )

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return issues


def scan_repository() -> dict:
    """Scan entire repository for issues."""
    all_issues = []

    src_dir = Path("src")
    if not src_dir.exists():
        print("src directory not found")
        return {}

    python_files = list(src_dir.rglob("*.py"))
    print(f"Scanning {len(python_files)} Python files...")

    for i, py_file in enumerate(python_files):
        if i % 50 == 0:
            print(f"  Progress: {i}/{len(python_files)}")

        issues = find_sonarqube_issues_in_file(py_file)
        all_issues.extend(issues)

    return {"total_files": len(python_files), "total_issues": len(all_issues), "issues": all_issues}


def categorize_and_create_quests(scan_results: dict) -> list[dict]:
    """Create quests from scan results."""
    issues = scan_results.get("issues", [])

    # Group by code
    by_code = defaultdict(list)
    for issue in issues:
        by_code[issue["code"]].append(issue)

    quests = []

    for code, code_issues in by_code.items():
        # Group by file
        by_file = defaultdict(list)
        for issue in code_issues:
            by_file[issue["file"]].append(issue)

        quest = {
            "title": f"Fix SonarQube {code}: {code_issues[0]['message']} ({len(code_issues)} occurrences)",
            "description": f"Resolve {len(code_issues)} instances of {code} across {len(by_file)} files",
            "type": "RefactorPU",
            "priority": "medium" if code_issues[0]["severity"] == "info" else "high",
            "sonarqube_code": code,
            "files_affected": list(by_file.keys())[:20],
            "total_occurrences": len(code_issues),
            "proof_criteria": [
                f"All {code} issues resolved",
                "Code quality metrics improved",
                "No new issues introduced",
            ],
        }
        quests.append(quest)

    return quests


def main():
    """Main execution."""
    print("=" * 80)
    print("🔍 SONARQUBE ISSUE ANALYZER")
    print("=" * 80)
    print()

    # Scan repository
    scan_results = scan_repository()

    print()
    print("=" * 80)
    print("📊 SCAN RESULTS")
    print("=" * 80)
    print(f"  Files Scanned: {scan_results.get('total_files', 0)}")
    print(f"  Issues Found: {scan_results.get('total_issues', 0)}")
    print()

    # Create quests
    quests = categorize_and_create_quests(scan_results)

    # Save results
    output_dir = Path("data/diagnostics")
    output_dir.mkdir(parents=True, exist_ok=True)

    results_file = output_dir / "sonarqube_scan_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(scan_results, f, indent=2)

    quests_file = output_dir / "sonarqube_quests.json"
    with open(quests_file, "w", encoding="utf-8") as f:
        json.dump({"total_quests": len(quests), "quests": quests}, f, indent=2)

    print(f"💾 Results saved to: {results_file}")
    print(f"🎯 Quests saved to: {quests_file}")
    print()

    # Show quest summary
    if quests:
        print("=" * 80)
        print("🎯 QUESTS CREATED:")
        print("=" * 80)
        for quest in quests[:10]:
            print(f"  - {quest['title']}")
        if len(quests) > 10:
            print(f"  ... and {len(quests) - 10} more")

    print()
    print("=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
