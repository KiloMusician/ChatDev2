#!/usr/bin/env python3
"""Test if start_nusyq.py parses correctly."""

import ast
import sys

try:
    with open("scripts/start_nusyq.py", "r", encoding="utf-8") as f:
        content = f.read()

    tree = ast.parse(content)
    print("✅ File parses successfully as valid Python")

    # Find KNOWN_ACTIONS assignment
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "KNOWN_ACTIONS":
                    if isinstance(node.value, ast.Set):
                        elements = [
                            elt.value for elt in node.value.elts if isinstance(elt, ast.Constant)
                        ]
                        print(f"\nFound KNOWN_ACTIONS set with {len(elements)} elements")
                        print("Has 'ai_work_gate':", "ai_work_gate" in elements)
                        print("Has 'ai_status':", "ai_status" in elements)
                        print("Has 'brief':", "brief" in elements)
                        if "ai_work_gate" not in elements:
                            print("\n⚠️ 'ai_work_gate' is NOT in the parsed set!")
                            print("First 10 elements:", sorted(elements)[:10])

except SyntaxError as e:
    print(f"❌ SYNTAX ERROR: {e}")
    print(f"Line {e.lineno}: {e.text}")
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)
