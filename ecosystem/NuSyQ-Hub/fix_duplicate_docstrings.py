#!/usr/bin/env python3
"""Fix duplicate docstrings that cause E402 errors."""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent


def fix_duplicate_docstrings(file_path: Path) -> bool:
    """Merge consecutive docstrings into one."""
    try:
        content = file_path.read_text(encoding="utf-8")

        # Pattern: First docstring followed by another docstring
        # Match: """..."""\n\n"""..."""
        pattern = r'("""[^"]*?""")\s*\n\s*\n\s*("""[^"]*?""")'

        matches = list(re.finditer(pattern, content, re.DOTALL))

        if not matches:
            return False

        # Merge docstrings
        for match in reversed(matches):  # Reverse to preserve positions
            first_doc = match.group(1)
            second_doc = match.group(2)

            # Remove the triple quotes from second docstring content
            second_content = second_doc.strip('"').strip()

            # Merge into first docstring
            merged = first_doc[:-3] + "\n\n" + second_content + '\n"""'

            # Replace in content
            content = content[: match.start()] + merged + content[match.end() :]

        # Write back
        file_path.write_text(content, encoding="utf-8")
        return True

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def main():
    """Fix all files with E402 errors due to duplicate docstrings."""
    # Get all Python files with E402 errors
    import subprocess

    result = subprocess.run(
        ["python", "-m", "flake8", "src/", "--select=E402", "--exclude=src/legacy,src/*BAK*"],
        capture_output=True,
        text=True,
    )

    # Extract unique file paths
    files_with_errors = set()
    for line in result.stdout.split("\n"):
        if "E402" in line:
            file_path = line.split(":")[0]
            files_with_errors.add(file_path)

    print(f"Found {len(files_with_errors)} files with E402 errors")

    fixed_count = 0
    for file_str in sorted(files_with_errors):
        file_path = PROJECT_ROOT / file_str
        if file_path.exists():
            if fix_duplicate_docstrings(file_path):
                print(f"✅ Fixed: {file_str}")
                fixed_count += 1
            else:
                print(f"⏭️  Skipped: {file_str}")
        else:
            print(f"⚠️  Not found: {file_str}")

    print(f"\n✅ Fixed {fixed_count} files")


if __name__ == "__main__":
    main()
