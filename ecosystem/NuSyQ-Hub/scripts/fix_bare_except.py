#!/usr/bin/env python3
"""Fix bare except: statements to catch Exception explicitly.

Converts:
    except:
    →
    except Exception:
"""

import re
import sys
from pathlib import Path


def fix_bare_except(content: str) -> tuple[str, int]:
    """Fix bare except statements.

    Returns:
        (modified_content, count_fixed)
    """
    fixed_count = 0
    lines = content.split("\n")
    new_lines = []

    for line in lines:
        if re.match(r"^\s+except:\s*$", line):
            # Replace bare except with Exception
            new_line = re.sub(r"except:", "except Exception:", line)
            new_lines.append(new_line)
            fixed_count += 1
        else:
            new_lines.append(line)

    return "\n".join(new_lines), fixed_count


def fix_file(filepath: Path) -> tuple[int, int]:
    """Fix bare except in a file.

    Returns:
        (count_fixed, errors)
    """
    try:
        content = filepath.read_text(encoding="utf-8")
        new_content, count_fixed = fix_bare_except(content)

        if count_fixed > 0:
            filepath.write_text(new_content, encoding="utf-8")
            return count_fixed, 0

        return 0, 0

    except Exception as e:
        print(f"Error processing {filepath}: {e}", file=sys.stderr)
        return 0, 1


def main():
    if len(sys.argv) < 2:
        print("Usage: python fix_bare_except.py <directory_or_file>")
        sys.exit(1)

    path = Path(sys.argv[1])

    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = list(path.rglob("*.py"))
    else:
        print(f"Invalid path: {path}")
        sys.exit(1)

    total_fixed = 0
    total_errors = 0
    files_modified = 0

    for filepath in files:
        fixed, errors = fix_file(filepath)

        if fixed > 0:
            files_modified += 1
            total_fixed += fixed
            print(f"✅ {filepath.name}: {fixed} bare except statements fixed")

        total_errors += errors

    print("\n📊 Summary:")
    print(f"  Files modified: {files_modified}")
    print(f"  Bare except statements fixed: {total_fixed}")
    if total_errors > 0:
        print(f"  Errors: {total_errors}")


if __name__ == "__main__":
    main()
