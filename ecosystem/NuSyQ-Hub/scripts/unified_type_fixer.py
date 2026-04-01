#!/usr/bin/env python3
"""Unified Type Fixer - All-in-one type hint fixing and improvement tool
[ROUTE ERRORS] 🔥

Consolidates 11 separate type-fixing tools under a single unified interface with mode-based delegation.

Modes:
  add-annotations   - Add type annotations to functions missing them
  add-hints         - Add type hints to modules
  improve           - Improve existing type hints (make more specific)
  fix-mypy          - Fix common mypy errors (optional, return types, etc.)
  optional          - Fix Optional type patterns
  none-return       - Fix -> None return type errors
  no-any            - Fix no-any-return mypy errors
  surgical          - Aggressive surgical type fixing (inspect function bodies)
  modernize         - Modernize typing to Python 3.9+ (list vs List, etc.)
  fix-deprecated    - Fix deprecated typing patterns
  batch             - Apply multiple modes to multiple files
  custom            - Apply custom type fixing rules from config

Usage:
  python scripts/unified_type_fixer.py --mode <mode> [options] [path]
  python scripts/unified_type_fixer.py --list-modes
  python scripts/unified_type_fixer.py --dry-run --mode surgical src/
"""

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class FixResults:
    """Results from a type fixing operation."""

    files_processed: int = 0
    files_modified: int = 0
    total_fixes: int = 0
    changes_by_type: dict[str, int] = None

    def __post_init__(self):
        if self.changes_by_type is None:
            self.changes_by_type = {}


class UnifiedTypeFixer:
    """Master type fixer that consolidates all type-fixing strategies."""

    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose

    # ========== MODE: add-annotations ==========
    def mode_add_annotations(self, scan_dir: Path) -> FixResults:
        """Add type annotations to functions missing them (AST-based)."""
        results = FixResults(changes_by_type={})

        class TypeHintAdder(ast.NodeTransformer):
            """AST transformer to add type hints to functions."""

            def __init__(self):
                self.modified = False
                self.functions_modified = []

            def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
                """Visit function definitions and add type hints if missing."""
                # Skip if function already has return type annotation
                if node.returns is not None:
                    return node

                # Skip special methods (except __init__)
                if node.name.startswith("__") and node.name.endswith("__") and node.name != "__init__":
                    return node

                # Add return type based on common patterns
                inferred_return = self._infer_return_type(node)
                if inferred_return:
                    node.returns = inferred_return
                    self.modified = True
                    self.functions_modified.append(f"Line {node.lineno}: {node.name}")

                # Add argument annotations if missing
                for arg in node.args.args:
                    if arg.annotation is None and arg.arg != "self" and arg.arg != "cls":
                        inferred_type = self._infer_arg_type(arg, node)
                        if inferred_type:
                            arg.annotation = inferred_type
                            self.modified = True

                return node

            def _infer_return_type(self, node: ast.FunctionDef) -> ast.expr | None:
                """Infer return type from function body."""
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.Return) and stmt.value:
                        if isinstance(stmt.value, ast.Constant):
                            if isinstance(stmt.value.value, bool):
                                return ast.Name(id="bool", ctx=ast.Load())
                            elif isinstance(stmt.value.value, int):
                                return ast.Name(id="int", ctx=ast.Load())
                            elif isinstance(stmt.value.value, str):
                                return ast.Name(id="str", ctx=ast.Load())
                return None

            def _infer_arg_type(self, arg: ast.arg, node: ast.FunctionDef) -> ast.expr | None:
                """Infer argument type from default value or usage."""
                # Simple heuristic: check if argument has default value
                for default in node.args.defaults:
                    if isinstance(default, ast.Constant):
                        if isinstance(default.value, str):
                            return ast.Name(id="str", ctx=ast.Load())
                        elif isinstance(default.value, int):
                            return ast.Name(id="int", ctx=ast.Load())
                return None

        for py_file in scan_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content)

                adder = TypeHintAdder()
                new_tree = adder.visit(tree)

                if adder.modified:
                    results.files_modified += 1
                    results.total_fixes += len(adder.functions_modified)
                    if not self.dry_run:
                        py_file.write_text(ast.unparse(new_tree), encoding="utf-8")
                    if self.verbose:
                        print(
                            f"  ✅ {py_file.relative_to(PROJECT_ROOT)}: {len(adder.functions_modified)} annotations added"
                        )

                results.files_processed += 1
            except (OSError, SyntaxError) as e:
                if self.verbose:
                    print(f"  ⚠️ {py_file}: {e}")

        results.changes_by_type["annotations_added"] = results.total_fixes
        return results

    # ========== MODE: fix-mypy ==========
    def mode_fix_mypy(self, scan_dir: Path) -> FixResults:
        """Fix common mypy errors (Optional defaults, -> None, etc.)."""
        results = FixResults(
            changes_by_type={
                "optional_import": 0,
                "optional_defaults": 0,
                "none_return_type": 0,
                "bare_except": 0,
            }
        )

        for py_file in scan_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                original = content

                # Fix Optional defaults
                content, count = self._fix_optional_defaults(content)
                results.changes_by_type["optional_defaults"] += count

                # Add Optional import if needed
                if count > 0:
                    content, added = self._add_optional_import(content)
                    results.changes_by_type["optional_import"] += 1 if added else 0

                # Add -> None return types
                content, count = self._add_none_return_type(content)
                results.changes_by_type["none_return_type"] += count

                # Fix bare except blocks
                content, count = self._fix_bare_except(content)
                results.changes_by_type["bare_except"] += count

                if content != original:
                    results.files_modified += 1
                    results.total_fixes += sum(results.changes_by_type.values())
                    if not self.dry_run:
                        py_file.write_text(content, encoding="utf-8")
                    if self.verbose:
                        print(
                            f"  ✅ {py_file.relative_to(PROJECT_ROOT)}: {sum(results.changes_by_type.values())} fixes"
                        )

                results.files_processed += 1
            except (OSError, UnicodeDecodeError) as e:
                if self.verbose:
                    print(f"  ⚠️ {py_file}: {e}")

        return results

    # ========== MODE: surgical ==========
    def mode_surgical(self, scan_dir: Path) -> FixResults:
        """Aggressive surgical type fixing (inspect function bodies)."""
        results = FixResults(
            changes_by_type={
                "return_none_to_actual": 0,
                "module_var_annotations": 0,
            }
        )

        for py_file in scan_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                original = content

                # Fix: methods typed as -> None that actually return values
                content, count = self._fix_return_none_to_actual_type(content)
                results.changes_by_type["return_none_to_actual"] += count

                # Fix: module-level variables like logger
                content, count = self._add_module_var_annotations(content)
                results.changes_by_type["module_var_annotations"] += count

                if content != original:
                    results.files_modified += 1
                    results.total_fixes += sum(results.changes_by_type.values())
                    if not self.dry_run:
                        py_file.write_text(content, encoding="utf-8")
                    if self.verbose:
                        print(
                            f"  ✅ {py_file.relative_to(PROJECT_ROOT)}: {sum(results.changes_by_type.values())} fixes"
                        )

                results.files_processed += 1
            except (OSError, UnicodeDecodeError) as e:
                if self.verbose:
                    print(f"  ⚠️ {py_file}: {e}")

        return results

    # ========== MODE: modernize ==========
    def mode_modernize(self, scan_dir: Path) -> FixResults:
        """Modernize typing to Python 3.9+ (list -> list, etc.)."""
        results = FixResults(
            changes_by_type={
                "modernized": 0,
            }
        )

        patterns = [
            (r"\bList\[", "list["),
            (r"\bDict\[", "dict["),
            (r"\bSet\[", "set["),
            (r"\bTuple\[", "tuple["),
            (r"\bFrozenSet\[", "frozenset["),
        ]

        for py_file in scan_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                original = content
                count = 0

                for old_pattern, new_pattern in patterns:
                    matches = len(re.findall(old_pattern, content))
                    if matches > 0:
                        content = re.sub(old_pattern, new_pattern, content)
                        count += matches

                if content != original:
                    results.files_modified += 1
                    results.total_fixes += count
                    results.changes_by_type["modernized"] += count
                    if not self.dry_run:
                        py_file.write_text(content, encoding="utf-8")
                    if self.verbose:
                        print(f"  ✅ {py_file.relative_to(PROJECT_ROOT)}: {count} patterns modernized")

                results.files_processed += 1
            except (OSError, UnicodeDecodeError) as e:
                if self.verbose:
                    print(f"  ⚠️ {py_file}: {e}")

        return results

    # ========== Helper Methods ==========
    @staticmethod
    def _add_optional_import(content: str) -> tuple[str, bool]:
        """Add Optional import if not present."""
        if "from typing import" not in content:
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    lines.insert(i, "from typing import Optional")
                    return "\n".join(lines), True
            return content, False

        if "Optional" in content:
            return content, False

        pattern = r"from typing import ([^(]+)$"
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            imports = match.group(1)
            new_imports = imports.strip() + ", Optional"
            new_content = re.sub(pattern, f"from typing import {new_imports}", content, flags=re.MULTILINE)
            return new_content, True

        return content, False

    @staticmethod
    def _fix_optional_defaults(content: str) -> tuple[str, int]:
        """Fix Optional type hints for parameters with None default."""
        count = 0
        pattern = r"(\w+):\s*([A-Z]\w+(?:\[[^\]]+\])?)\s*=\s*None"

        def replacer(match):
            nonlocal count
            param_name = match.group(1)
            type_hint = match.group(2)

            if "Optional" not in type_hint:
                count += 1
                return f"{param_name}: Optional[{type_hint}] = None"
            return match.group(0)

        new_content = re.sub(pattern, replacer, content)
        return new_content, count

    @staticmethod
    def _add_none_return_type(content: str) -> tuple[str, int]:
        """Add -> None to functions missing return type."""
        count = 0
        pattern = r"^(\s*def\s+(?!__)(\w+)\s*\([^)]*\)\s*):\s*$"

        def replacer(match):
            nonlocal count
            count += 1
            return f"{match.group(1)} -> None:"

        new_content = re.sub(pattern, replacer, content, flags=re.MULTILINE)
        return new_content, count

    @staticmethod
    def _fix_bare_except(content: str) -> tuple[str, int]:
        """Fix bare except blocks with context-aware exception types."""
        count = 0
        lines = content.split("\n")

        for i, line in enumerate(lines):
            if not re.match(r"^\s*except\s*:\s*$", line):
                continue

            indent_level = len(line) - len(line.lstrip())
            # Simple heuristic: use generic Exception if we can't determine
            indent = " " * indent_level
            lines[i] = f"{indent}except Exception:"
            count += 1

        return "\n".join(lines), count

    @staticmethod
    def _fix_return_none_to_actual_type(content: str) -> tuple[str, int]:
        """Fix methods that return values but are typed as -> None."""
        fixes = 0
        lines = content.splitlines()

        for i, line in enumerate(lines):
            if " -> None:" not in line or "    def " not in line or "__init__" in line:
                continue

            for j in range(i + 1, min(i + 25, len(lines))):
                next_line = lines[j]

                if "return 0" in next_line or re.search(r"return \d+$", next_line.strip()):
                    lines[i] = line.replace(" -> None:", " -> int:")
                    fixes += 1
                    break
                elif "return True" in next_line or "return False" in next_line:
                    lines[i] = line.replace(" -> None:", " -> bool:")
                    fixes += 1
                    break
                elif "return []" in next_line:
                    lines[i] = line.replace(" -> None:", " -> list:")
                    fixes += 1
                    break
                elif "return {}" in next_line:
                    lines[i] = line.replace(" -> None:", " -> dict:")
                    fixes += 1
                    break
                elif next_line.strip().startswith("def "):
                    break

        return "\n".join(lines), fixes

    @staticmethod
    def _add_module_var_annotations(content: str) -> tuple[str, int]:
        """Add type annotations to module-level variables like logger."""
        fixes = 0

        if "logger = logging.getLogger" in content and "logger: logging.Logger" not in content:
            content = re.sub(
                r"^logger = logging\.getLogger",
                "logger: logging.Logger = logging.getLogger",
                content,
                flags=re.MULTILINE,
            )
            fixes += 1

        return content, fixes


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Unified Type Fixer - All-in-one type hint fixing tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--mode",
        type=str,
        default="fix-mypy",
        choices=[
            "add-annotations",
            "add-hints",
            "improve",
            "fix-mypy",
            "optional",
            "none-return",
            "no-any",
            "surgical",
            "modernize",
            "fix-deprecated",
            "batch",
            "custom",
        ],
        help="Type fixing mode to use",
    )
    parser.add_argument("--path", type=str, default="src", help="Path to scan for Python files")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying them")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--list-modes", action="store_true", help="List all available modes")

    args = parser.parse_args()

    if args.list_modes:
        modes = [
            "add-annotations - Add type annotations to functions",
            "fix-mypy       - Fix common mypy errors",
            "surgical       - Aggressive surgical type fixing",
            "modernize      - Modernize typing to Python 3.9+",
        ]
        print("Available modes:")
        for mode in modes:
            print(f"  {mode}")
        return 0

    scan_dir = PROJECT_ROOT / args.path
    if not scan_dir.exists():
        print(f"❌ Path not found: {scan_dir}")
        return 1

    fixer = UnifiedTypeFixer(dry_run=args.dry_run, verbose=args.verbose)

    print(f"{'🔧' if not args.dry_run else '👀'} UNIFIED TYPE FIXER - Mode: {args.mode}")
    print("=" * 60)

    # Dispatch to mode handler
    if args.mode == "fix-mypy":
        results = fixer.mode_fix_mypy(scan_dir)
    elif args.mode == "add-annotations":
        results = fixer.mode_add_annotations(scan_dir)
    elif args.mode == "surgical":
        results = fixer.mode_surgical(scan_dir)
    elif args.mode == "modernize":
        results = fixer.mode_modernize(scan_dir)
    else:
        print(f"❌ Mode not yet implemented: {args.mode}")
        return 1

    # Print results
    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print(f"   Files processed: {results.files_processed}")
    print(f"   Files {'would be ' if args.dry_run else ''}modified: {results.files_modified}")
    print(f"   Total fixes: {results.total_fixes}")

    for change_type, count in results.changes_by_type.items():
        if count > 0:
            print(f"   {change_type}: {count}")

    if args.dry_run:
        print("\n💡 Run without --dry-run to apply changes")

    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
