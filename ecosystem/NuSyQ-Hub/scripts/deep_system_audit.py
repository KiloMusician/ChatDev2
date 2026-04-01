#!/usr/bin/env python3
"""Deep system audit - find what's actually broken, not wired, incomplete."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import ast
import json


def audit_todos_fixmes():
    """Find all TODOs/FIXMEs and categorize by severity."""
    print("\n🔍 Auditing TODOs and FIXMEs...")

    critical_keywords = ["critical", "broken", "urgent", "important", "fix", "bug"]
    todos_by_severity = {"critical": [], "high": [], "medium": []}

    for py_file in Path("src").rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            for i, line in enumerate(content.splitlines(), 1):
                if "TODO" in line or "FIXME" in line or "XXX" in line or "HACK" in line:
                    line_lower = line.lower()
                    severity = "medium"
                    if any(kw in line_lower for kw in critical_keywords):
                        severity = "critical" if "critical" in line_lower or "broken" in line_lower else "high"

                    todos_by_severity[severity].append({"file": str(py_file), "line": i, "text": line.strip()})
        except Exception:
            pass

    print(f"  Critical: {len(todos_by_severity['critical'])}")
    print(f"  High:     {len(todos_by_severity['high'])}")
    print(f"  Medium:   {len(todos_by_severity['medium'])}")

    if todos_by_severity["critical"]:
        print("\n🔴 Critical TODOs:")
        for todo in todos_by_severity["critical"][:10]:
            print(f"  {todo['file']}:{todo['line']}")
            print(f"    {todo['text']}")

    return todos_by_severity


def audit_incomplete_classes():
    """Find classes with NotImplementedError or pass-only methods."""
    print("\n🔍 Auditing incomplete implementations...")

    incomplete = []

    for py_file in Path("src").rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content, str(py_file))

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            # Check if function raises NotImplementedError
                            for stmt in ast.walk(item):
                                if isinstance(stmt, ast.Raise):
                                    if isinstance(stmt.exc, ast.Name) and stmt.exc.id == "NotImplementedError":
                                        incomplete.append(
                                            {
                                                "file": str(py_file),
                                                "class": node.name,
                                                "method": item.name,
                                                "line": item.lineno,
                                            }
                                        )
        except Exception:
            pass

    print(f"  Found {len(incomplete)} unimplemented methods")

    if incomplete:
        print("\n🔴 Sample unimplemented methods:")
        for item in incomplete[:10]:
            print(f"  {item['file']}:{item['line']}")
            print(f"    {item['class']}.{item['method']}()")

    return incomplete


def audit_unused_imports():
    """Find modules that are imported but never used."""
    print("\n🔍 Auditing unused imports...")

    # This is simplified - proper analysis would use AST visitor
    unused_count = 0

    for py_file in Path("src").rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            # Check for imports marked with
            if "# noqa: F401" in content or "# type: ignore" in content:
                unused_count += content.count("# noqa: F401") + content.count("# type: ignore")
        except Exception:
            pass

    print(f"  Found ~{unused_count} suppressed import warnings")
    return unused_count


def audit_test_coverage():
    """Check which modules have corresponding tests."""
    print("\n🔍 Auditing test coverage...")

    src_modules = set()
    test_modules = set()

    for py_file in Path("src").rglob("*.py"):
        if "__pycache__" not in str(py_file) and "__init__" not in py_file.name:
            module_name = py_file.stem
            src_modules.add(module_name)

    for py_file in Path("tests").rglob("*.py"):
        if "__pycache__" not in str(py_file):
            # Extract module name from test_module.py
            test_name = py_file.stem
            if test_name.startswith("test_"):
                module_name = test_name[5:]  # Remove 'test_' prefix
                test_modules.add(module_name)

    untested = src_modules - test_modules

    print(f"  Source modules: {len(src_modules)}")
    print(f"  Test modules:   {len(test_modules)}")
    print(f"  Untested:       {len(untested)}")

    if untested:
        print("\n🔴 Sample untested modules:")
        for mod in sorted(untested)[:20]:
            print(f"    {mod}")

    return {
        "src_count": len(src_modules),
        "test_count": len(test_modules),
        "untested": list(untested),
    }


def audit_game_dev_system():
    """Check if game development system is properly wired."""
    print("\n🔍 Auditing game development system...")

    game_files = list(Path("src/game_development").rglob("*.py")) if Path("src/game_development").exists() else []
    game_tests = list(Path("tests").rglob("test_*game*.py"))

    print(f"  Game dev modules: {len(game_files)}")
    print(f"  Game dev tests:   {len(game_tests)}")

    # Check if games directory exists and has projects
    games_dir = Path("src/games")
    game_projects = list(games_dir.rglob("*.py")) if games_dir.exists() else []

    print(f"  Game projects:    {len(game_projects)}")

    # Check for game templates
    templates_dir = Path("templates/games")
    templates = list(templates_dir.rglob("*")) if templates_dir.exists() else []

    print(f"  Game templates:   {len(templates)}")

    status = "broken" if len(game_files) > 0 and len(game_projects) == 0 else "working"

    return {
        "status": status,
        "module_count": len(game_files),
        "project_count": len(game_projects),
        "test_count": len(game_tests),
    }


def main():
    """Run comprehensive system audit."""
    print("=" * 70)
    print("  🔬 NuSyQ-Hub Deep System Audit")
    print("=" * 70)

    results = {}

    results["todos"] = audit_todos_fixmes()
    results["incomplete"] = audit_incomplete_classes()
    results["unused_imports"] = audit_unused_imports()
    results["test_coverage"] = audit_test_coverage()
    results["game_dev"] = audit_game_dev_system()

    # Save results
    output_file = Path("system_audit_report.json")
    output_file.write_text(json.dumps(results, indent=2, default=str))

    print("\n" + "=" * 70)
    print(f"  ✅ Audit complete - saved to {output_file}")
    print("=" * 70)

    # Summary
    critical_count = len(results["todos"]["critical"])
    incomplete_count = len(results["incomplete"])
    untested_count = len(results["test_coverage"]["untested"])

    print("\n📊 PRIORITY ISSUES:")
    print(f"  🔴 Critical TODOs:          {critical_count}")
    print(f"  🔴 Unimplemented methods:   {incomplete_count}")
    print(f"  🔴 Untested modules:        {untested_count}")
    print(f"  🔴 Game dev status:         {results['game_dev']['status']}")


if __name__ == "__main__":
    main()
