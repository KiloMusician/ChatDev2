#!/usr/bin/env python3
"""Automatically fix missing type imports in Python files."""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent


def fix_missing_any_import(file_path: Path) -> bool:
    """Fix missing 'Any' import in a file."""
    try:
        content = file_path.read_text(encoding="utf-8")

        # Check if Any is used but not imported
        if "Any" not in content:
            return False  # No usage of Any

        # Check if already imported
        if "from typing import" in content and re.search(
            r"\bAny\b", content.split("from typing import")[1].split("\n")[0]
        ):
            return False  # Already imported

        if "import typing" in content:
            return False  # Using typing.Any

        # Find the first import statement
        lines = content.split("\n")
        last_import_idx = -1
        has_typing_import = False
        typing_import_idx = -1

        for idx, line in enumerate(lines):
            if line.startswith("from typing import"):
                has_typing_import = True
                typing_import_idx = idx
                last_import_idx = idx
            elif line.startswith("import ") or line.startswith("from "):
                last_import_idx = idx

        # Fix the import
        if has_typing_import and typing_import_idx >= 0:
            # Add Any to existing typing import
            typing_line = lines[typing_import_idx]
            if "Any" not in typing_line:
                # Check if it's a multiline import
                if "(" in typing_line:
                    # Multiline import
                    close_idx = typing_import_idx
                    for i in range(typing_import_idx, len(lines)):
                        if ")" in lines[i]:
                            close_idx = i
                            break

                    # Add Any before closing paren
                    lines[close_idx] = lines[close_idx].replace(")", ",\n    Any,\n)")
                else:
                    # Single line import
                    lines[typing_import_idx] = typing_line.replace("import ", "import Any, ")
        else:
            # Add new typing import after last import
            if last_import_idx >= 0:
                lines.insert(last_import_idx + 1, "from typing import Any")
            else:
                # No imports found, add at top after docstring/comments
                insert_idx = 0
                for idx, line in enumerate(lines):
                    if (
                        line.strip()
                        and not line.strip().startswith("#")
                        and not line.strip().startswith('"""')
                        and not line.strip().startswith("'''")
                    ):
                        insert_idx = idx
                        break
                lines.insert(insert_idx, "from typing import Any\n")

        # Write back
        file_path.write_text("\n".join(lines), encoding="utf-8")
        return True

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def main():
    """Fix missing imports across the codebase."""
    # Files with missing Any imports (from linting output)
    files_with_missing_any = [
        "src/analysis/broken_paths_analyzer.py",
        "src/analysis/health_verifier.py",
        "src/analysis/quantum_analyzer.py",
        "src/analysis/repository_analyzer.py",
        "src/automation/ollama_validation_pipeline.py",
        "src/consciousness/floor_6_wisdom.py",
        "src/consciousness/temple_of_knowledge/floor_2_patterns.py",
        "src/consciousness/temple_of_knowledge/floor_3_systems.py",
        "src/consciousness/temple_of_knowledge/floor_4_metacognition.py",
        "src/copilot/vscode_integration.py",
        "src/diagnostics/broken_paths_analyzer.py",
        "src/diagnostics/comprehensive_integration_validator.py",
        "src/diagnostics/comprehensive_quantum_analysis.py",
        "src/diagnostics/comprehensive_test_runner.py",
        "src/diagnostics/direct_repository_audit.py",
        "src/diagnostics/health_verification.py",
        "src/diagnostics/quick_quest_audit.py",
        "src/diagnostics/quick_system_analyzer.py",
        "src/diagnostics/systematic_src_audit.py",
        "src/evolution/system_evolution_auditor.py",
        "src/games/house_of_leaves.py",
    ]

    fixed_count = 0

    print("🔧 Fixing missing 'Any' imports...\n")

    for file_rel in files_with_missing_any:
        file_path = PROJECT_ROOT / file_rel
        if file_path.exists():
            if fix_missing_any_import(file_path):
                print(f"✅ Fixed: {file_rel}")
                fixed_count += 1
            else:
                print(f"⏭️  Skipped: {file_rel} (already has import)")
        else:
            print(f"⚠️  Not found: {file_rel}")

    print(f"\n✅ Fixed {fixed_count} files")


if __name__ == "__main__":
    main()
