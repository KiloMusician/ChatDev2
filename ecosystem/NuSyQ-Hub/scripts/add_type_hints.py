#!/usr/bin/env python3
"""Add type hints to Python functions that are missing them.

This script adds basic type hints based on common patterns and default values.
"""

import ast
from pathlib import Path


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
                # Try to infer type from default value
                inferred_type = self._infer_arg_type(arg, node)
                if inferred_type:
                    arg.annotation = inferred_type
                    self.modified = True

        return node

    def _infer_return_type(self, node: ast.FunctionDef) -> ast.expr:
        """Infer return type from function body."""
        # Check for explicit return statements
        has_return_none = False
        has_return_value = False

        for child in ast.walk(node):
            if isinstance(child, ast.Return):
                if child.value is None:
                    has_return_none = True
                else:
                    has_return_value = True

        # __init__ always returns None
        if node.name == "__init__":
            return ast.Constant(value=None)

        # If function has no return or only returns None
        if has_return_none and not has_return_value:
            return ast.Constant(value=None)

        # Check for common patterns in function name
        if node.name.startswith("is_") or node.name.startswith("has_") or node.name.startswith("can_"):
            return ast.Name(id="bool", ctx=ast.Load())

        if node.name.startswith("get_") or node.name.startswith("find_"):
            # Could be Optional, but we'll be conservative
            return None

        if node.name.startswith("count_") or node.name.endswith("_count"):
            return ast.Name(id="int", ctx=ast.Load())

        # Default: don't guess
        return None

    def _infer_arg_type(self, arg: ast.arg, func: ast.FunctionDef) -> ast.expr:
        """Infer argument type from usage or default value."""
        # Find the default value for this argument
        # (This is simplified - full implementation would match args to defaults properly)

        # Common argument name patterns
        if arg.arg.endswith("_path") or arg.arg == "path" or arg.arg == "file_path":
            return ast.Name(id="str", ctx=ast.Load())

        if arg.arg.endswith("_file") or arg.arg == "filename":
            return ast.Name(id="str", ctx=ast.Load())

        if arg.arg.endswith("_name") or arg.arg == "name":
            return ast.Name(id="str", ctx=ast.Load())

        if arg.arg == "data" or arg.arg == "config":
            return ast.Name(id="dict", ctx=ast.Load())

        if arg.arg.endswith("_list") or arg.arg.endswith("_items"):
            return ast.Name(id="list", ctx=ast.Load())

        if arg.arg == "timeout" or arg.arg.endswith("_timeout"):
            return ast.Name(id="float", ctx=ast.Load())

        if arg.arg.endswith("_id") or arg.arg == "id":
            return ast.Name(id="str", ctx=ast.Load())

        # Default: don't guess
        return None


def add_type_hints_to_file(file_path: Path, dry_run: bool = False) -> tuple[bool, list[str]]:
    """Add type hints to a Python file.

    Returns: (was_modified, list of modifications).
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except (UnicodeDecodeError, PermissionError) as e:
        print(f"⚠️  Skipping {file_path}: {e}")
        return False, []

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"⚠️  Syntax error in {file_path}: {e}")
        return False, []

    # Transform the AST
    transformer = TypeHintAdder()
    new_tree = transformer.visit(tree)

    if not transformer.modified:
        return False, []

    if dry_run:
        return True, transformer.functions_modified

    # Convert AST back to source code
    # Note: ast.unparse() is Python 3.9+, for earlier versions would need astor
    try:
        new_content = ast.unparse(new_tree)
    except AttributeError:
        print("⚠️  ast.unparse not available (Python 3.9+ required)")
        return False, []

    # Write back
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return True, transformer.functions_modified


def main():
    # Target critical files identified in the session
    target_files = [
        "src/orchestration/multi_ai_orchestrator.py",
        "src/consciousness/the_oldest_house.py",
        "src/healing/quantum_problem_resolver.py",
    ]

    print("🔍 Adding type hints to critical files...")
    print("⚠️  WARNING: This uses AST transformation which may alter code formatting")
    print("⚠️  RECOMMENDATION: Review changes carefully and format with Black after")

    # Dry run first
    print("\n🔬 Dry run - scanning for functions that need type hints...")

    total_functions = 0
    for file_path_str in target_files:
        file_path = Path(file_path_str)
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            continue

        was_modified, modifications = add_type_hints_to_file(file_path, dry_run=True)
        if was_modified:
            print(f"\n📄 {file_path}:")
            for mod in modifications:
                print(f"   {mod}")
                total_functions += 1

    print(f"\n📊 Found {total_functions} functions that could have type hints added")
    print("\n⚠️  AST-based type hint addition is complex and may not preserve all formatting")
    print("💡 RECOMMENDATION: Use this as a guide and add type hints manually, or")
    print("💡 use tools like pytype, monkeytype, or Copilot for better type inference")

    # Don't auto-apply due to risk of breaking formatting
    print("\n✅ Analysis complete. Manual type hint addition recommended.")


if __name__ == "__main__":
    main()
