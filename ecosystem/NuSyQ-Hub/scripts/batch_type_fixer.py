#!/usr/bin/env python3
"""Batch Type Annotation Fixer - Add encoding and type hints systematically"""

import re
from pathlib import Path


def fix_open_calls(content: str) -> tuple[str, int]:
    """Add encoding='utf-8' to open() calls that lack it."""
    fixes = 0
    lines = content.split("\n")
    result_lines = []

    for line in lines:
        # Pattern: open(...) without encoding
        if "open(" in line and "encoding" not in line and not line.strip().startswith("#"):
            # Simple pattern matching for common cases
            if re.search(r"\bopen\s*\([^)]+\)\s*(?:as\b|:)", line):
                # Check if it's a simple open(path) or open(path, mode)
                if line.count("(") == line.count(")"):  # Balanced parens on same line
                    # Find the closing paren before 'as' or ':'
                    match = re.search(r"(\bopen\s*\([^)]+)(\)\s*(?:as\b|:))", line)
                    if match:
                        new_line = line[: match.start(2)] + ', encoding="utf-8"' + match.group(2) + line[match.end(2) :]
                        result_lines.append(new_line)
                        fixes += 1
                        continue

        result_lines.append(line)

    return "\n".join(result_lines), fixes


def add_list_type_annotations(content: str) -> tuple[str, int]:
    """Add type hints to list initializations."""
    fixes = 0
    lines = content.split("\n")
    result_lines = []

    # Pattern: variable = []
    pattern = r"^(\s+)([a-z_][a-z0-9_]*)\s*=\s*\[\]\s*$"

    for i, line in enumerate(lines):
        match = re.match(pattern, line, re.IGNORECASE)
        if match:
            indent, var_name = match.groups()
            # Check if there's already a type comment
            if i > 0 and "type:" in lines[i - 1]:
                result_lines.append(line)
                continue

            # Add type annotation
            new_line = f"{indent}{var_name}: List[Any] = []"
            result_lines.append(new_line)
            fixes += 1
        else:
            result_lines.append(line)

    return "\n".join(result_lines), fixes


def add_dict_type_annotations(content: str) -> tuple[str, int]:
    """Add type hints to dict initializations."""
    fixes = 0
    lines = content.split("\n")
    result_lines = []

    # Pattern: variable = {}
    pattern = r"^(\s+)([a-z_][a-z0-9_]*)\s*=\s*\{\}\s*$"

    for i, line in enumerate(lines):
        match = re.match(pattern, line, re.IGNORECASE)
        if match:
            indent, var_name = match.groups()
            # Check if there's already a type comment
            if i > 0 and "type:" in lines[i - 1]:
                result_lines.append(line)
                continue

            # Add type annotation
            new_line = f"{indent}{var_name}: Dict[str, Any] = {{}}"
            result_lines.append(new_line)
            fixes += 1
        else:
            result_lines.append(line)

    return "\n".join(result_lines), fixes


def ensure_typing_imports(content: str, needed: set) -> str:
    """Ensure required typing imports are present."""
    lines = content.split("\n")

    # Find existing typing import
    typing_import_idx = None
    current_imports = set()

    for i, line in enumerate(lines):
        if re.match(r"from typing import", line):
            typing_import_idx = i
            # Extract current imports
            imports_str = line.split("import")[1]
            current_imports = {imp.strip() for imp in imports_str.split(",")}
            break

    # Add missing imports
    missing = needed - current_imports
    if not missing:
        return content

    if typing_import_idx is not None:
        # Update existing import
        all_imports = sorted(current_imports | missing)
        lines[typing_import_idx] = f"from typing import {', '.join(all_imports)}"
    else:
        # Add new import after other imports
        import_end_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                import_end_idx = i

        if missing:
            lines.insert(import_end_idx + 1, f"from typing import {', '.join(sorted(missing))}")

    return "\n".join(lines)


def fix_file(file_path: Path) -> dict:
    """Fix a single Python file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        original = content
        stats = {"encoding": 0, "list_types": 0, "dict_types": 0}

        # Apply fixes
        content, encoding_fixes = fix_open_calls(content)
        stats["encoding"] = encoding_fixes

        content, list_fixes = add_list_type_annotations(content)
        stats["list_types"] = list_fixes

        content, dict_fixes = add_dict_type_annotations(content)
        stats["dict_types"] = dict_fixes

        # Add typing imports if needed
        needed_imports = set()
        if list_fixes > 0:
            needed_imports.update(["List", "Any"])
        if dict_fixes > 0:
            needed_imports.update(["Dict", "Any"])

        if needed_imports:
            content = ensure_typing_imports(content, needed_imports)

        # Write if changed
        if content != original:
            file_path.write_text(content, encoding="utf-8")
            return stats

        return None

    except Exception as e:
        print(f"⚠️  Error processing {file_path}: {e}")
        return None


def main():
    """Process all Python files in src/."""
    root = Path("src")
    total_stats = {"files": 0, "encoding": 0, "list_types": 0, "dict_types": 0}

    print("🔧 Batch Type Annotation Fixer")
    print("=" * 70)

    for py_file in root.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue

        stats = fix_file(py_file)
        if stats:
            total_stats["files"] += 1
            total_stats["encoding"] += stats["encoding"]
            total_stats["list_types"] += stats["list_types"]
            total_stats["dict_types"] += stats["dict_types"]

            if sum(stats.values()) > 0:
                print(f"✅ {py_file.relative_to(root.parent)}: {stats}")

    print("\n" + "=" * 70)
    print("📊 Summary:")
    print(f"   Files modified: {total_stats['files']}")
    print(f"   Encoding fixes: {total_stats['encoding']}")
    print(f"   List type hints: {total_stats['list_types']}")
    print(f"   Dict type hints: {total_stats['dict_types']}")
    print("\n✅ Complete!")


if __name__ == "__main__":
    main()
