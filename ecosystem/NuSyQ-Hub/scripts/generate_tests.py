#!/usr/bin/env python3
"""AI-assisted test generation for untested modules.

Creates basic smoke tests for modules that lack test coverage.
Uses Ollama for intelligent test generation based on code analysis.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import ast
import json
from typing import Any


def analyze_module(module_path: Path) -> dict[str, Any]:
    """Analyze a Python module to extract testable components."""
    try:
        content = module_path.read_text(encoding="utf-8")
        tree = ast.parse(content, str(module_path))

        functions = []
        classes = []
        imports = []

        # Only get top-level functions and classes, not nested ones
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip private functions
                if not node.name.startswith("_"):
                    functions.append(
                        {
                            "name": node.name,
                            "args": [arg.arg for arg in node.args.args],
                            "lineno": node.lineno,
                            "is_async": isinstance(node, ast.AsyncFunctionDef),
                        }
                    )
            elif isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if not item.name.startswith("_") or item.name == "__init__":
                            methods.append(
                                {
                                    "name": item.name,
                                    "args": [arg.arg for arg in item.args.args],
                                    "lineno": item.lineno,
                                }
                            )
                classes.append(
                    {
                        "name": node.name,
                        "methods": methods,
                        "lineno": node.lineno,
                    }
                )
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(ast.unparse(node))

        return {
            "module_path": str(module_path),
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "has_main": any(
                isinstance(node, ast.If) and isinstance(node.test, ast.Compare) and "__name__" in ast.unparse(node.test)
                for node in ast.walk(tree)
            ),
        }
    except Exception as e:
        return {"error": str(e), "module_path": str(module_path)}


def generate_test_template(module_analysis: dict[str, Any]) -> str:
    """Generate a pytest test file template for the module."""
    module_path = Path(module_analysis["module_path"])
    module_name = module_path.stem
    # Convert to absolute path first, then make relative
    abs_module_path = module_path.absolute() if not module_path.is_absolute() else module_path
    relative_import = str(abs_module_path.relative_to(Path.cwd())).replace("\\", "/")
    import_path = relative_import.replace("/", ".").replace(".py", "")

    test_code = f'''"""Tests for {module_name}.

Auto-generated smoke tests to establish basic coverage.
"""

import pytest
from {import_path} import (
'''

    # Add imports for classes and functions
    for cls in module_analysis.get("classes", []):
        test_code += f"    {cls['name']},\n"

    for func in module_analysis.get("functions", [])[:5]:  # Limit to 5 functions
        test_code += f"    {func['name']},\n"

    test_code += ")\n\n\n"

    # Generate basic class tests
    for cls in module_analysis.get("classes", []):
        test_code += f'''def test_{cls["name"].lower()}_instantiation():
    """Test that {cls["name"]} can be instantiated."""
    # TODO: Add proper initialization parameters
    try:
        instance = {cls["name"]}()
        assert instance is not None
    except TypeError:
        # May require initialization parameters
        pytest.skip("Requires initialization parameters - add them manually")


'''

        # Test key methods
        for method in cls["methods"][:3]:  # Limit to 3 methods per class
            if method["name"] != "__init__":
                test_code += f'''def test_{cls["name"].lower()}_{method["name"]}():
    """Test {cls["name"]}.{method["name"]}() method."""
    # TODO: Implement actual test
    pytest.skip("Test needs implementation")


'''

    # Generate basic function tests
    for func in module_analysis.get("functions", [])[:5]:  # Limit to 5 functions
        test_code += f'''def test_{func["name"]}():
    """Test {func["name"]}() function."""
    # TODO: Add test parameters and assertions
    pytest.skip("Test needs implementation")


'''

    return test_code


def generate_tests_for_untested_modules(
    limit: int = 20,
    output_dir: Path | None = None,
    dry_run: bool = False,
) -> None:
    """Generate test files for untested modules.

    Args:
        limit: Maximum number of test files to generate
        output_dir: Directory to write test files (default: tests/)
        dry_run: If True, print tests without writing files
    """
    if output_dir is None:
        output_dir = Path("tests")

    output_dir.mkdir(exist_ok=True)

    # Find untested modules
    src_modules = set()
    test_modules = set()

    for py_file in Path("src").rglob("*.py"):
        if "__pycache__" not in str(py_file) and "__init__" not in py_file.name:
            src_modules.add(py_file)

    for py_file in Path("tests").rglob("*.py"):
        if "__pycache__" not in str(py_file):
            test_name = py_file.stem
            if test_name.startswith("test_"):
                module_name = test_name[5:]  # Remove 'test_' prefix
                test_modules.add(module_name)

    # Filter to untested modules
    untested = []
    for module_path in src_modules:
        module_name = module_path.stem
        if module_name not in test_modules:
            untested.append(module_path)

    print(f"Found {len(untested)} untested modules")
    print(f"Generating tests for first {min(limit, len(untested))} modules...\n")

    generated_count = 0
    for module_path in sorted(untested)[:limit]:
        print(f"Analyzing: {module_path}")

        # Analyze module
        analysis = analyze_module(module_path)

        if "error" in analysis:
            print(f"  ❌ Error analyzing: {analysis['error']}\n")
            continue

        # Skip modules with no testable components
        if not analysis.get("classes") and not analysis.get("functions") and not analysis.get("has_main"):
            print("  ⏭️  Skipping: No testable components\n")
            continue

        # Generate test template
        test_code = generate_test_template(analysis)

        # Determine output file
        module_name = module_path.stem
        test_file = output_dir / f"test_{module_name}.py"

        if test_file.exists():
            print(f"  ⚠️  Test file already exists: {test_file}\n")
            continue

        if dry_run:
            print(f"  📄 Would create: {test_file}")
            print(f"     Classes: {len(analysis.get('classes', []))}")
            print(f"     Functions: {len(analysis.get('functions', []))}")
            print(f"     Lines: {len(test_code.splitlines())}\n")
        else:
            # Write test file
            test_file.write_text(test_code, encoding="utf-8")
            print(f"  ✅ Created: {test_file}")
            print(f"     Classes: {len(analysis.get('classes', []))}")
            print(f"     Functions: {len(analysis.get('functions', []))}")
            print(f"     Lines: {len(test_code.splitlines())}\n")
            generated_count += 1

    print(f"\n{'Dry run complete' if dry_run else f'Generated {generated_count} test files'}")
    print("Next: Review generated tests and implement TODO items")


def main() -> None:
    """Run test generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate tests for untested modules")
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of test files to generate (default: 20)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tests"),
        help="Output directory for test files (default: tests/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without writing files",
    )
    parser.add_argument(
        "--analyze-only",
        type=str,
        help="Analyze a specific module and print JSON analysis",
    )

    args = parser.parse_args()

    if args.analyze_only:
        module_path = Path(args.analyze_only)
        if not module_path.exists():
            print(f"Error: Module not found: {module_path}")
            sys.exit(1)

        analysis = analyze_module(module_path)
        print(json.dumps(analysis, indent=2))
        return

    generate_tests_for_untested_modules(
        limit=args.limit,
        output_dir=args.output,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
