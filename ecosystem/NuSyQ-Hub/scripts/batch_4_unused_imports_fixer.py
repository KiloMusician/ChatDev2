#!/usr/bin/env python3
"""Batch 4: Automated Unused Imports Remover

Systematically removes unused imports from Python files in src/
"""

import re
import subprocess
import sys


def get_unused_imports() -> dict[str, set[str]]:
    """Get unused imports from pylint output."""
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pylint",
                "--disable=all",
                "--enable=unused-import",
                "src",
                "--exit-zero",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception as e:
        print(f"Error running pylint: {e}")
        return {}

    unused = {}
    for line in result.stdout.split("\n"):
        if "unused-import" not in line:
            continue
        # Parse: "src\file.py:10:0: W0611: Unused X imported from Y (unused-import)"
        parts = line.split(":")
        if len(parts) < 2:
            continue
        filepath = parts[0].strip()

        # Extract import name from message
        if "Unused" in line:
            # "Unused X imported from" or "Unused import X"
            match = re.search(r"Unused (?:import )?([^ ]+)", line)
            if match:
                import_name = match.group(1)
                if filepath not in unused:
                    unused[filepath] = set()
                unused[filepath].add(import_name)

    return unused


def remove_import_from_file(filepath: str, import_name: str) -> bool:
    """Remove specific import from a file."""
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Pattern 1: "from X import Y" where Y is the unused import
        pattern1 = rf"from\s+\S+\s+import\s+[^#\n]*\b{re.escape(import_name)}\b[^#\n]*\n"
        content = re.sub(pattern1, "", content)

        # Pattern 2: "import X" where X is unused
        pattern2 = rf"^import\s+{re.escape(import_name)}\s*(?:#.*)?$"
        content = re.sub(pattern2, "", content, flags=re.MULTILINE)

        # Pattern 3: Handle "from X import A, B, C" case
        # Remove just B if B is unused
        pattern3 = rf",\s*{re.escape(import_name)}\b"
        temp = re.sub(pattern3, "", content)
        pattern4 = rf"\b{re.escape(import_name)}\s*,"
        temp = re.sub(pattern4, "", temp)
        content = temp

        # Clean up empty lines
        content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)

        if content != original_content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True

        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False


def main():
    """Main batch processor."""
    print("🧹 Batch 4: Automated Unused Imports Remover")
    print("=" * 60)

    unused = get_unused_imports()

    if not unused:
        print("✅ No unused imports found!")
        return 0

    print(f"Found {len(unused)} files with unused imports")
    print(f"Total unused imports: {sum(len(v) for v in unused.values())}")
    print()

    fixed_count = 0
    files_fixed = set()

    for filepath in sorted(unused.keys()):
        imports = unused[filepath]
        print(f"📄 {filepath}")

        for import_name in sorted(imports):
            if remove_import_from_file(filepath, import_name):
                print(f"  ✓ Removed: {import_name}")
                fixed_count += 1
                files_fixed.add(filepath)
            else:
                print(f"  ✗ Failed to remove: {import_name}")

    print()
    print("=" * 60)
    print(f"✅ Fixed {fixed_count} unused imports in {len(files_fixed)} files")

    return 0


if __name__ == "__main__":
    sys.exit(main())
