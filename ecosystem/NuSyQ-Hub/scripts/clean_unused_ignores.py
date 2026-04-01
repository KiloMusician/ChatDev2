#!/usr/bin/env python
"""Remove unused type: ignore comments from codebase."""

import re
import subprocess
from pathlib import Path


def get_unused_ignores():
    """Get list of files with unused-ignore errors from mypy."""
    result = subprocess.run(
        ["python", "-m", "mypy", "src/", "tests/", "--show-error-codes"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    unused = []
    for line in result.stdout.split("\n") + result.stderr.split("\n"):
        if "unused-ignore" in line:
            # Parse: src\file.py:10: error: Unused "type: ignore" comment
            match = re.match(r"(.+):(\d+):", line)
            if match:
                filepath, lineno = match.groups()
                unused.append((filepath, int(lineno)))

    return unused


def remove_type_ignores(filepath: Path, line_numbers: list[int]):
    """Remove # type: ignore comments from specific lines."""
    lines = filepath.read_text(encoding="utf-8").split("\n")

    modified = False
    for lineno in sorted(set(line_numbers), reverse=True):
        idx = lineno - 1  # Convert to 0-based
        if idx < len(lines):
            # Remove # type: ignore[...] or # type: ignore
            original = lines[idx]
            cleaned = re.sub(r"\s*#\s*type:\s*ignore(\[[\w-]+\])?", "", lines[idx])
            if cleaned != original:
                lines[idx] = cleaned.rstrip()
                modified = True
                print(f"  Line {lineno}: Removed type: ignore")

    if modified:
        filepath.write_text("\n".join(lines), encoding="utf-8")
        return True
    return False


def main():
    """Remove all unused type: ignore comments."""
    print("=" * 80)
    print("REMOVING UNUSED TYPE: IGNORE COMMENTS")
    print("=" * 80)

    unused = get_unused_ignores()
    print(f"\nFound {len(unused)} unused type: ignore comments")

    # Group by file
    by_file: dict[str, list[int]] = {}
    for filepath, lineno in unused:
        if filepath not in by_file:
            by_file[filepath] = []
        by_file[filepath].append(lineno)

    fixed_count = 0
    for filepath, line_numbers in by_file.items():
        path_obj = Path(filepath)
        if path_obj.exists():
            print(f"\n📝 {filepath} ({len(line_numbers)} ignores)")
            if remove_type_ignores(path_obj, line_numbers):
                fixed_count += len(line_numbers)

    print("\n" + "=" * 80)
    print(f"✅ Removed {fixed_count} unused type: ignore comments")
    print("=" * 80)


if __name__ == "__main__":
    main()
