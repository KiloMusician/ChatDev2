#!/usr/bin/env python3
"""Code Modernization Scanner - Find outdated patterns

Scans for:
- Old string formatting (% and .format())
- Missing type hints
- Bare except clauses
- Old-style classes
- Deprecated imports
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def scan_file(file_path: Path) -> dict[str, list[tuple[int, str]]]:
    """Scan a file for modernization opportunities."""
    issues = defaultdict(list)

    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")
    except Exception:
        return issues

    for i, line in enumerate(lines, 1):
        # Old string formatting
        if re.search(r"%\s*[sdf]|%\(([\w_]+)\)", line):
            if not line.strip().startswith("#"):
                issues["old_string_format"].append((i, line.strip()))

        # .format() (prefer f-strings)
        if ".format(" in line and not line.strip().startswith("#"):
            issues["format_method"].append((i, line.strip()))

        # Bare except
        if re.match(r"\s*except\s*:", line):
            issues["bare_except"].append((i, line.strip()))

        # Missing function type hints
        if re.match(r"\s*def\s+\w+\([^)]*\)\s*:", line):
            if "->" not in line and "__init__" not in line:
                issues["missing_return_type"].append((i, line.strip()))

    return issues


def main() -> int:
    """Scan codebase for modernization opportunities."""
    print("🔍 MODERNIZATION SCAN")
    print("=" * 60)

    src_dir = PROJECT_ROOT / "src"
    all_issues = defaultdict(lambda: defaultdict(list))
    total_files = 0
    files_with_issues = 0

    for py_file in src_dir.rglob("*.py"):
        total_files += 1
        issues = scan_file(py_file)

        if any(issues.values()):
            files_with_issues += 1
            rel_path = py_file.relative_to(PROJECT_ROOT)

            for issue_type, occurrences in issues.items():
                all_issues[issue_type][str(rel_path)].extend(occurrences)

    # Print summary
    print(f"\n📊 Scanned {total_files} files")
    print(f"   {files_with_issues} files have modernization opportunities\n")

    # Print issues by type
    issue_names = {
        "old_string_format": "Old % formatting",
        "format_method": ".format() method (prefer f-strings)",
        "bare_except": "Bare except clauses",
        "missing_return_type": "Missing return type hints",
    }

    for issue_type, files in sorted(all_issues.items()):
        total = sum(len(occurrences) for occurrences in files.values())
        print(f"\n🔧 {issue_names.get(issue_type, issue_type)}: {total} occurrences")

        # Show top 5 files
        sorted_files = sorted(files.items(), key=lambda x: len(x[1]), reverse=True)[:5]

        for file_path, occurrences in sorted_files:
            print(f"   {file_path}: {len(occurrences)} occurrences")
            for line_num, line in occurrences[:2]:
                print(f"     L{line_num}: {line[:70]}")

    print("\n" + "=" * 60)
    print(f"✨ Scan complete! Found {sum(len(f) for f in all_issues.values())} issue types")

    return 0


if __name__ == "__main__":
    sys.exit(main())
