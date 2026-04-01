#!/usr/bin/env python3
"""Extract String Constants

Identifies the most commonly duplicated strings and suggests extracting them
as constants to reduce S1192 violations.
"""

import ast
import json
import sys
from collections import defaultdict
from pathlib import Path


def extract_strings_from_file(file_path: Path) -> list[tuple[str, int]]:
    """Extract all string literals from a Python file with line numbers."""
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return []

    strings = []

    class StringVisitor(ast.NodeVisitor):
        def visit_Str(self, node):
            if hasattr(node, "lineno"):
                strings.append((node.s, node.lineno))
            self.generic_visit(node)

        def visit_Constant(self, node):
            if isinstance(node.value, str) and hasattr(node, "lineno"):
                strings.append((node.value, node.lineno))
            self.generic_visit(node)

    visitor = StringVisitor()
    visitor.visit(tree)

    return strings


def analyze_string_duplications(src_dir: Path) -> dict:
    """Analyze string duplications across all Python files."""
    all_strings = defaultdict(list)

    py_files = list(src_dir.rglob("*.py"))

    for py_file in py_files:
        strings = extract_strings_from_file(py_file)
        for string, line_no in strings:
            # Ignore very short strings, docstrings, and common patterns
            if len(string) < 15:
                continue
            if "\n" in string:  # Skip docstrings
                continue
            if string.strip() in ["", " "]:
                continue

            all_strings[string].append({"file": str(py_file), "line": line_no})

    # Find duplicated strings
    duplicated = {
        string: locations
        for string, locations in all_strings.items()
        if len(locations) >= 3  # Appears 3+ times
    }

    return duplicated


def suggest_constant_name(string: str) -> str:
    """Suggest a constant name for a string."""
    # Remove special characters
    name = "".join(c if c.isalnum() or c == " " else "_" for c in string)

    # Convert to uppercase snake case
    words = name.split()
    if len(words) > 5:
        words = words[:5]

    name = "_".join(words).upper()

    # Limit length
    if len(name) > 50:
        name = name[:50]

    return name


def main():
    """Main execution."""
    print("=" * 80)
    print("🔍 STRING DUPLICATION ANALYZER")
    print("=" * 80)
    print()

    src_dir = Path("src")
    if not src_dir.exists():
        print("❌ src directory not found")
        return 1

    print("📊 Analyzing string duplications...")
    duplicated = analyze_string_duplications(src_dir)

    if not duplicated:
        print("✅ No significant string duplications found!")
        return 0

    print(f"  Found {len(duplicated)} duplicated strings")
    print()

    # Sort by duplication count
    sorted_duplications = sorted(duplicated.items(), key=lambda x: len(x[1]), reverse=True)

    # Show top duplications
    print("=" * 80)
    print("🔝 TOP 20 DUPLICATED STRINGS")
    print("=" * 80)
    print()

    for i, (string, locations) in enumerate(sorted_duplications[:20], 1):
        count = len(locations)
        suggested_name = suggest_constant_name(string)

        print(f"{i}. Occurrences: {count}")
        print(f'   String: "{string[:60]}{"..." if len(string) > 60 else ""}"')
        print(f"   Suggested constant: {suggested_name}")

        # Show first 3 locations
        for loc in locations[:3]:
            file_name = Path(loc["file"]).name
            print(f"     - {file_name}:{loc['line']}")

        if len(locations) > 3:
            print(f"     ... and {len(locations) - 3} more")

        print()

    # Create a constants file suggestion
    print("=" * 80)
    print("💡 SUGGESTED CONSTANTS FILE")
    print("=" * 80)
    print()
    print("# Create src/utils/common_strings.py:")
    print()
    print('"""Common string constants used across the codebase."""')
    print()

    for string, locations in sorted_duplications[:10]:
        if len(locations) >= 5:  # Only suggest constants for 5+ occurrences
            const_name = suggest_constant_name(string)
            print(f'{const_name} = "{string}"')

    print()
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"  Total duplicated strings: {len(duplicated)}")
    print(f"  High-frequency (5+ uses): {sum(1 for _, locs in duplicated.items() if len(locs) >= 5)}")
    print(f"  Potential savings: ~{sum(len(locs) - 1 for locs in duplicated.values())} lines")
    print()

    # Save report
    report_file = Path("data/diagnostics/string_duplication_report.json")
    report_file.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "total_duplicated": len(duplicated),
        "high_frequency": sum(1 for _, locs in duplicated.items() if len(locs) >= 5),
        "top_20": [
            {
                "string": string[:100],
                "count": len(locations),
                "suggested_constant": suggest_constant_name(string),
                "sample_locations": [{"file": loc["file"], "line": loc["line"]} for loc in locations[:3]],
            }
            for string, locations in sorted_duplications[:20]
        ],
    }

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"💾 Detailed report saved to: {report_file}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
