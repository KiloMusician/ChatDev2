#!/usr/bin/env python3
"""Validation script for exception handler fixes.

Guard the execution under __main__ so pytest can import this file while
collecting tests without executing the script-level sys.exit().
"""
import ast
import sys

files_to_test = [
    "scripts/generate_prune_plan.py",
    "scripts/theater_audit.py",
    "scripts/extract_string_constants.py",
    "scripts/integration_health_check.py",
    "src/utils/generate_structure_tree2BAK.py",
    "src/interface/archived/Enhanced-Interactive-Context-Browser-v2.py",
    "examples/sns_core_ollama_test.py",
]


def run_checks():
    print("✅ Testing Fixed NuSyQ-Hub Files:\n")
    passed = 0
    failed = 0

    for filepath in files_to_test:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                code = f.read()
            ast.parse(code)
            compile(code, filepath, "exec")
            print(f"  ✓ {filepath}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {filepath}: {e}")
            failed += 1

    print(f"\n📊 Results: {passed} passed, {failed} failed")

    # Also test one file specifically for exception handler format
    print("\n🔍 Exception Handler Verification (generate_prune_plan.py):")
    try:
        with open("scripts/generate_prune_plan.py", "r", encoding="utf-8") as f:
            content = f.read()
        if "except (ValueError, TypeError):" in content:
            print("  ✓ Line 25: except (ValueError, TypeError)")
        if "except (OSError, RuntimeError)" in content:
            print("  ✓ Line 86: except (OSError, RuntimeError)")
        if "except (FileNotFoundError, IOError, OSError)" in content:
            print("  ✓ Line 88: except (FileNotFoundError, IOError, OSError)")
    except Exception as e:
        print(f"  ✗ Could not verify: {e}")

    return failed


if __name__ == "__main__":
    failed = run_checks()
    sys.exit(0 if failed == 0 else 1)
