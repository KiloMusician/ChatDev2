#!/usr/bin/env python3
"""Quick validation that systems.py is syntactically sound."""

import ast
import sys

try:
    with open("src/api/systems.py") as f:
        code = f.read()

    # Parse the code
    ast.parse(code)
    print("✓ systems.py: Syntax valid (AST parse successful)")
    print(f"✓ {len(code)} bytes read successfully")

    # Count functions
    tree = ast.parse(code)
    functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    routers = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and "@" in ast.get_source_segment(code, node)
        if ast.get_source_segment(code, node)
    ]

    print(f"✓ Found {len(functions)} functions")
    print("✓ Help: Run 'python -m pylint src/api/systems.py' for specific issues")

except SyntaxError as e:
    print(f"✗ SYNTAX ERROR in systems.py: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ ERROR: {e}")
    sys.exit(1)
