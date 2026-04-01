#!/usr/bin/env python3
"""Diagnose issues in systems.py after refactoring."""

import subprocess
from collections import defaultdict


def main():
    # Run ruff check
    result = subprocess.run(
        ["ruff", "check", "src/api/systems.py", "--output-format=text"],
        capture_output=True,
        text=True,
    )

    print("=" * 70)
    print("SYSTEMS.PY DIAGNOSTIC REPORT")
    print("=" * 70)

    if result.stdout:
        lines = result.stdout.strip().split("\n")
        print(f"\nTotal issues found: {len([line_text for line_text in lines if line_text.strip()])}")
        print("\nIssues by category:")

        categories = defaultdict(list)
        for line in lines:
            if ":" in line and "src/api/systems.py" in line:
                # Parse: src/api/systems.py:123:5: E123 error message
                parts = line.split(":")
                if len(parts) >= 4:
                    line_num = parts[1]
                    rest = ":".join(parts[3:])
                    code = rest.split(" ")[0] if rest.strip() else "UNKNOWN"
                    categories[code].append((line_num, rest))

        for code in sorted(categories.keys()):
            issues = categories[code]
            print(f"\n  {code}: {len(issues)} occurrence(s)")
            for line_num, msg in issues[:3]:  # Show first 3
                print(f"    Line {line_num}: {msg.strip()}")
            if len(issues) > 3:
                print(f"    ... and {len(issues) - 3} more")

    if result.returncode == 0:
        print("\n✓ All checks passed!")
    else:
        print(f"\nReturn code: {result.returncode}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
