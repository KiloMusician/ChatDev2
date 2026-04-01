#!/usr/bin/env python3
"""Semantic Auto-Fixer: Smart pattern-based code fixes"""

import re
from pathlib import Path


class SemanticAutoFixer:
    """Apply semantic fixes to common code issues"""

    def __init__(self, root: Path):
        self.root = root
        self.fixes_applied = 0
        self.files_modified = set()

    def fix_missing_return_annotations(self, filepath: Path) -> int:
        """Add -> None to functions without return annotations"""
        content = filepath.read_text(encoding="utf-8")
        original = content

        # Pattern: def function(...): (no ->)
        # Match indented functions only (avoid top-level)
        pattern = r"(\n    def \w+\([^)]*\)):\n"
        replacement = r"\1 -> None:\n"
        content = re.sub(pattern, replacement, content)

        if content != original:
            filepath.write_text(content, encoding="utf-8")
            count = content.count("-> None") - original.count("-> None")
            self.fixes_applied += count
            self.files_modified.add(filepath)
            return count
        return 0

    def add_typing_imports(self, filepath: Path) -> int:
        """Add typing.Any import when needed"""
        content = filepath.read_text(encoding="utf-8")
        # Check if Any is used but not imported
        if "Any" in content and "from typing import" in content:
            import_line = [line for line in content.split("\n") if "from typing import" in line][0]
            if "Any" not in import_line:
                # Add Any to existing import
                content = content.replace(import_line, import_line.replace(" import ", " import Any, "))
                filepath.write_text(content, encoding="utf-8")
                self.fixes_applied += 1
                self.files_modified.add(filepath)
                return 1

        return 0

    def fix_unused_imports(self, filepath: Path) -> int:
        """Remove or mark unused imports"""
        content = filepath.read_text(encoding="utf-8")
        # Pattern: imports that look unused (start of line, single name)
        # Add
        lines = content.split("\n")
        fixed_lines = []
        fixes = 0

        for line in lines:
            if line.startswith("import ") or line.startswith("from "):
                if "# noqa" not in line and "# type:" not in line:
                    # Add noqa comment
                    fixed_lines.append(f"{line}  # noqa: F401")
                    fixes += 1
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)

        if fixes > 0:
            content = "\n".join(fixed_lines)
            filepath.write_text(content, encoding="utf-8")
            self.fixes_applied += fixes
            self.files_modified.add(filepath)
            return fixes

        return 0

    def standardize_tool_interfaces(self, filepath: Path) -> int:
        """Ensure all tools follow standard interface pattern"""
        content = filepath.read_text(encoding="utf-8")
        # Tools should have run() method
        if "class " in content and "Tool" in filepath.stem:
            # Check if run method exists
            if "def run(" not in content:
                # Find class definition
                class_match = re.search(r"class \w+.*?:\n", content)
                if class_match:
                    insert_pos = class_match.end()
                    run_method = '''    def run(self) -> Dict[str, Any]:
        """Execute tool and return results"""
        raise NotImplementedError("Subclass must implement run()")

'''
                    content = content[:insert_pos] + run_method + content[insert_pos:]
                    filepath.write_text(content, encoding="utf-8")
                    self.fixes_applied += 1
                    self.files_modified.add(filepath)
                    return 1

        return 0

    def fix_all_python_files(self) -> dict[str, int]:
        """Apply all fixes to Python files"""
        stats = {
            "return_annotations": 0,
            "typing_imports": 0,
            "unused_imports": 0,
            "tool_interfaces": 0,
        }

        src_path = self.root / "src"
        for pyfile in src_path.rglob("*.py"):
            if "__pycache__" in str(pyfile):
                continue

            stats["return_annotations"] += self.fix_missing_return_annotations(pyfile)
            stats["typing_imports"] += self.add_typing_imports(pyfile)
            # stats['unused_imports'] += self.fix_unused_imports(pyfile)  # Disabled - too aggressive

            if "tools" in str(pyfile):
                stats["tool_interfaces"] += self.standardize_tool_interfaces(pyfile)

        return stats


def main():
    """Run semantic auto-fixes"""
    print("🔧 Semantic Auto-Fixer")
    print("=" * 60)

    root = Path.cwd()
    fixer = SemanticAutoFixer(root)

    stats = fixer.fix_all_python_files()

    print(f"\n✅ Fixes applied: {fixer.fixes_applied}")
    print(f"📁 Files modified: {len(fixer.files_modified)}\n")
    print("Breakdown:")
    for fix_type, count in stats.items():
        if count > 0:
            print(f"   • {fix_type}: {count}")

    print("\nModified files:")
    for f in sorted(fixer.files_modified):
        print(f"   {f.relative_to(root)}")


if __name__ == "__main__":
    main()
