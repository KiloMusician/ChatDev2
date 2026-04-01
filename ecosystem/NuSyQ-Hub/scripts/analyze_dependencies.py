#!/usr/bin/env python3
"""Dependency Analyzer - Understand module relationships.

Analyzes:
- Import dependencies between modules
- Circular dependencies
- Highly coupled modules
- Orphaned modules
"""

import ast
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def extract_imports(file_path: Path) -> list[str]:
    """Extract import statements from a Python file."""
    imports = []

    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split(".")[0])

    except Exception:
        pass

    return imports


def main() -> int:
    """Analyze module dependencies."""
    print("🔍 DEPENDENCY ANALYSIS")
    print("=" * 60)

    src_dir = PROJECT_ROOT / "src"
    dependencies = defaultdict(set)
    reverse_deps = defaultdict(set)
    all_modules = set()

    # Collect dependencies
    for py_file in src_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue

        rel_path = py_file.relative_to(src_dir)
        module = str(rel_path.with_suffix("")).replace("\\", ".").replace("/", ".")
        all_modules.add(module)

        imports = extract_imports(py_file)

        for imp in imports:
            if imp != module.split(".")[0]:
                dependencies[module].add(imp)
                reverse_deps[imp].add(module)

    # Analyze
    print(f"\n📊 Total modules: {len(all_modules)}")

    # Most imported modules
    print("\n🔥 Most Imported Modules:")
    sorted_imports = sorted(reverse_deps.items(), key=lambda x: len(x[1]), reverse=True)[:10]

    for module, importers in sorted_imports:
        print(f"   {module}: imported by {len(importers)} modules")

    # Modules with most dependencies
    print("\n🔗 Modules with Most Dependencies:")
    sorted_deps = sorted(dependencies.items(), key=lambda x: len(x[1]), reverse=True)[:10]

    for module, deps in sorted_deps:
        print(f"   {module}: depends on {len(deps)} modules")

    # Orphaned modules (no imports, no importers)
    orphaned = []
    for module in all_modules:
        if module not in dependencies and module not in reverse_deps:
            orphaned.append(module)

    if orphaned:
        print(f"\n🏝️ Orphaned Modules ({len(orphaned)}):")
        for module in orphaned[:10]:
            print(f"   {module}")

    # Check for potential circular dependencies (simplified)
    print("\n🔄 Potential Circular Dependencies:")
    circular_count = 0

    for module, deps in dependencies.items():
        for dep in deps:
            if dep in dependencies and module in dependencies[dep]:
                circular_count += 1
                if circular_count <= 5:
                    print(f"   {module} <-> {dep}")

    if circular_count > 5:
        print(f"   ... and {circular_count - 5} more")
    elif circular_count == 0:
        print("   ✅ No circular dependencies detected")

    print("\n" + "=" * 60)
    print("✨ Analysis complete!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
