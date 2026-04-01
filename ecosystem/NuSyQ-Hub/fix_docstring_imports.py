#!/usr/bin/env python3
"""Fix imports that are mistakenly inside docstrings."""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent


def fix_docstring_import(file_path: Path) -> bool:
    """Fix 'from typing import X' that appears in docstring."""
    try:
        content = file_path.read_text(encoding="utf-8")

        # Pattern: docstring with "from typing import X" inside
        pattern = r'("""[^"]*?)(from typing import [A-Za-z, ]+)(\n[^"]*?""")'

        matches = list(re.finditer(pattern, content, re.DOTALL))

        if not matches:
            return False

        # Extract the import statement
        imports_to_add = []
        for match in matches:
            import_stmt = match.group(2).strip()
            imports_to_add.append(import_stmt)

        # Remove import from docstring
        content = re.sub(pattern, r"\1\3", content, flags=re.DOTALL)

        # Find where to add the import (after other imports or after docstring)
        lines = content.split("\n")

        # Find last import line
        last_import_idx = -1
        for idx, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                last_import_idx = idx

        # Find first docstring end
        first_docstring_end = -1
        in_docstring = False
        docstring_char = None
        for idx, line in enumerate(lines):
            if '"""' in line or "'''" in line:
                if not in_docstring:
                    in_docstring = True
                    docstring_char = '"""' if '"""' in line else "'''"
                    # Check if it's a single-line docstring
                    if line.count(docstring_char) >= 2:
                        first_docstring_end = idx
                        break
                else:
                    first_docstring_end = idx
                    break

        # Add imports after last import, or after first docstring
        insert_idx = max(last_import_idx, first_docstring_end) + 1

        for import_stmt in imports_to_add:
            lines.insert(insert_idx, import_stmt)
            insert_idx += 1

        # Write back
        file_path.write_text("\n".join(lines), encoding="utf-8")
        return True

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def main():
    """Fix all files with docstring import issues."""
    files_to_fix = [
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

    print("🔧 Fixing docstring import issues...\n")

    for file_rel in files_to_fix:
        file_path = PROJECT_ROOT / file_rel
        if file_path.exists():
            if fix_docstring_import(file_path):
                print(f"✅ Fixed: {file_rel}")
                fixed_count += 1
            else:
                print(f"⏭️  Skipped: {file_rel}")
        else:
            print(f"⚠️  Not found: {file_rel}")

    print(f"\n✅ Fixed {fixed_count} files")


if __name__ == "__main__":
    main()
