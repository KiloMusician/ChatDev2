#!/usr/bin/env python3
"""
Theater Auditor - Port from SimulatedVerse vacuum_scanner.py
Scans for "sophisticated theater" patterns: TODOs, placeholders, hardcoded errors, etc.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Theater detection patterns (ported from SimulatedVerse)
THEATER_PATTERNS = {
    "TODO_FIXME": r"\b(TODO|FIXME|XXX|HACK|WIP|TBD)\b",
    "PLACEHOLDER": r"placeholder|not implemented",
    "PASS_STATEMENT": r"^\s*pass\s*$",
    "HARDCODED_ERROR": r"raise NotImplementedError",
    "PRINT_DEBUG": r"print\(",
    "MOCK_DATA": r"(mock|fake|dummy|test).*data",
    "DEAD_CODE": r"#.*unused|#.*dead code",
}

SEVERITY_WEIGHTS = {
    "HARDCODED_ERROR": 3.0,
    "PASS_STATEMENT": 3.0,
    "TODO_FIXME": 1.0,
    "PLACEHOLDER": 1.0,
    "MOCK_DATA": 1.0,
    "PRINT_DEBUG": 0.3,
    "DEAD_CODE": 0.3,
}


def scan_file(file_path: Path) -> List[Dict]:
    """Scan a single file for theater patterns"""
    issues = []

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            for pattern_name, pattern in THEATER_PATTERNS.items():
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(
                        {
                            "line": line_num,
                            "pattern": pattern_name,
                            "content": line.strip()[:100],
                            "severity": get_severity(pattern_name),
                            "weight": SEVERITY_WEIGHTS.get(pattern_name, 1.0),
                        }
                    )
    except (OSError, UnicodeDecodeError, ValueError, TypeError, re.error) as e:
        if os.environ.get("THEATER_AUDITOR_DEBUG", "0") == "1":
            print(f"Skipped {file_path}: {e}")

    return issues


def get_severity(pattern_name: str) -> str:
    """Get severity level for pattern"""
    if SEVERITY_WEIGHTS.get(pattern_name, 1.0) >= 3.0:
        return "high"
    elif SEVERITY_WEIGHTS.get(pattern_name, 1.0) >= 1.0:
        return "medium"
    else:
        return "low"


def scan_repository(root_dir: Optional[Path] = None) -> Tuple[Dict, Dict]:
    """Scan entire repository for theater patterns"""
    if root_dir is None:
        root_dir = Path(__file__).parent.parent

    exclude_dirs = {
        ".git",
        "node_modules",
        ".venv",
        "__pycache__",
        ".mypy_cache",
        "attic",
        ".cache",
        ".snapshots",
        "ChatDev",
        "GameDev",
    }
    exclude_files = {"theater_auditor.py", "vacuum_scanner.py"}

    file_extensions = {".py", ".ts", ".tsx", ".js", ".jsx", ".gd", ".yaml", ".yml", ".md"}

    results = {}
    files_scanned = 0
    total_hits = 0

    for file_path in root_dir.rglob("*"):
        # Skip excluded directories
        if any(excluded in file_path.parts for excluded in exclude_dirs):
            continue

        # Skip excluded files
        if file_path.name in exclude_files:
            continue

        # Only scan specific file types
        if file_path.is_file() and file_path.suffix in file_extensions:
            files_scanned += 1
            issues = scan_file(file_path)

            if issues:
                relative_path = str(file_path.relative_to(root_dir))
                results[relative_path] = issues
                total_hits += len(issues)

    # Calculate theater score
    weighted_sum = sum(sum(issue["weight"] for issue in issues) for issues in results.values())

    theater_score = weighted_sum / max(files_scanned, 1)
    normalized_score = min(theater_score / 10, 1.0)

    # Categorize by severity
    severity_counts = {"high": 0, "medium": 0, "low": 0}
    for issues in results.values():
        for issue in issues:
            severity_counts[issue["severity"]] += 1

    summary = {
        "timestamp": datetime.now().isoformat(),
        "files_scanned": files_scanned,
        "files_with_issues": len(results),
        "total_hits": total_hits,
        "severity_counts": severity_counts,
        "weighted_sum": weighted_sum,
        "theater_score": normalized_score,
        "interpretation": interpret_score(normalized_score),
    }

    return results, summary


def interpret_score(score: float) -> str:
    """Interpret theater score"""
    if score < 0.2:
        return "EXCELLENT - Minimal theater"
    elif score < 0.5:
        return "ACCEPTABLE - Moderate theater"
    elif score < 0.8:
        return "WARNING - High theater levels"
    else:
        return "CRITICAL - Maximum theater detected"


def main():
    """Run theater audit and save results"""
    print("🔍 Theater Auditor - Scanning for sophisticated theater...")
    print("=" * 60)

    results, summary = scan_repository()

    # Create Reports directory if needed
    reports_dir = Path(__file__).parent.parent / "Reports"
    reports_dir.mkdir(exist_ok=True)

    # Save detailed results
    results_path = reports_dir / "theater_audit.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "files": results}, f, indent=2)

    # Print summary
    print(f"Files scanned: {summary['files_scanned']}")
    print(f"Files with theater: {summary['files_with_issues']}")
    print(f"Total theater hits: {summary['total_hits']}")
    print()
    print("Severity breakdown:")
    print(f"  High:   {summary['severity_counts']['high']}")
    print(f"  Medium: {summary['severity_counts']['medium']}")
    print(f"  Low:    {summary['severity_counts']['low']}")
    print()
    print(f"Theater Score: {summary['theater_score']:.3f}")
    print(f"Assessment: {summary['interpretation']}")
    print()
    print(f"📋 Detailed report: {results_path}")

    # Show top offenders
    if results:
        print()
        print("Top 10 files with most theater:")
        sorted_files = sorted(results.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        for file_path, issues in sorted_files:
            print(f"  {file_path}: {len(issues)} issues")


if __name__ == "__main__":
    main()
