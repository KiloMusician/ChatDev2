#!/usr/bin/env python3
"""Batch 4: Fast Unused Imports Analyzer - AST-based approach

Uses AST analysis to detect and remove unused imports quickly.
"""

import ast
from pathlib import Path


class UnusedImportAnalyzer(ast.NodeVisitor):
    """AST visitor to find unused imports."""

    def __init__(self):
        self.imported_names: set[str] = set()
        self.used_names: set[str] = set()
        self.import_nodes: list[tuple[str, ast.stmt]] = []

    def visit_Import(self, node: ast.Import):
        """Track import statements."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imported_names.add(name)
            self.import_nodes.append((name, node))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track from...import statements."""
        for alias in node.names:
            if alias.name == "*":
                # Can't track star imports
                return
            name = alias.asname if alias.asname else alias.name
            self.imported_names.add(name)
            self.import_nodes.append((name, node))
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        """Track name usage."""
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        """Track attribute access (e.g., os.path)."""
        if isinstance(node.value, ast.Name) and isinstance(node.value.ctx, ast.Load):
            self.used_names.add(node.value.id)
        self.generic_visit(node)


def find_unused_imports(filepath: str) -> set[str]:
    """Find unused imports in a Python file."""
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        analyzer = UnusedImportAnalyzer()
        analyzer.visit(tree)

        # Find unused: imported but not used
        unused = analyzer.imported_names - analyzer.used_names

        # Filter out special cases (like __all__)
        unused = {u for u in unused if not u.startswith("_")}

        return unused
    except Exception:
        return set()


def process_batch(max_files: int = 50):
    """Process unused imports in batch."""
    print("🧹 Batch 4: Fast Unused Imports Analyzer (AST-based)")
    print("=" * 60)

    src_dir = Path("src").resolve()
    cwd = Path.cwd()
    py_files = list(src_dir.glob("**/*.py"))[:max_files]

    total_unused = 0
    files_with_unused = 0

    for py_file in sorted(py_files):
        unused = find_unused_imports(str(py_file))
        if unused:
            files_with_unused += 1
            total_unused += len(unused)
            try:
                rel_path = py_file.relative_to(cwd)
            except ValueError:
                rel_path = py_file
            print(f"📄 {rel_path}: {len(unused)} unused")
            for name in sorted(unused):
                print(f"   - {name}")

    print()
    print("=" * 60)
    print(f"Found {total_unused} unused imports in {files_with_unused} files")
    print(f"(Analyzed {len(py_files)} files)")


if __name__ == "__main__":
    process_batch()
