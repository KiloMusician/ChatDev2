#!/usr/bin/env python3
"""Automated Quick Wins Error Fixes - Phase 1.

Safely fixes 9 errors with zero risk:
- Remove unused imports (1)
- Create string constants (2)
- Remove unnecessary async keywords (6)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def fix_unused_import_sys():
    """Remove unused 'import sys' from artifact_manager.py."""
    file_path = Path("src/tools/artifact_manager.py")

    if not file_path.exists():
        print(f"⏭️  Skipped: {file_path} not found")
        return

    content = file_path.read_text(encoding="utf-8")

    # Remove standalone 'import sys' line
    updated = re.sub(r"^import sys\n", "", content, flags=re.MULTILINE)

    if updated != content:
        file_path.write_text(updated, encoding="utf-8")
        print(f"✅ Fixed: Removed unused 'import sys' from {file_path}")
        return True
    else:
        print(f"⏭️  Skipped: No changes needed in {file_path}")
        return False


def fix_duplicate_string_literals():
    """Create constants for duplicate string literals."""
    fixes_applied = 0

    # Fix 1: ChatDev MCP server
    file_path = Path("src/integration/chatdev_mcp_server.py")
    if file_path.exists():
        content = file_path.read_text(encoding="utf-8")
        string_literal = '"ChatDev MCP feature is disabled"'
        constant_line = 'FEATURE_DISABLED_MSG = "ChatDev MCP feature is disabled"'

        if string_literal in content:
            updated = content

            if constant_line in updated:
                placeholder = "__FEATURE_DISABLED_MSG_LITERAL__"
                updated = updated.replace(constant_line, f"FEATURE_DISABLED_MSG = {placeholder}")

            # Replace all remaining occurrences
            updated = updated.replace(string_literal, "FEATURE_DISABLED_MSG")

            if "__FEATURE_DISABLED_MSG_LITERAL__" in updated:
                updated = updated.replace(
                    "FEATURE_DISABLED_MSG = __FEATURE_DISABLED_MSG_LITERAL__",
                    constant_line,
                )

            if constant_line not in updated:
                if "# Module-level constants" in updated:
                    updated = updated.replace(
                        "# Module-level constants\n",
                        '# Module-level constants\nFEATURE_DISABLED_MSG = "ChatDev MCP feature is disabled"\n',
                        1,
                    )
                elif "logger = logging.getLogger(__name__)" in updated:
                    updated = updated.replace(
                        "logger = logging.getLogger(__name__)\n",
                        "logger = logging.getLogger(__name__)\n\n"
                        'FEATURE_DISABLED_MSG = "ChatDev MCP feature is disabled"\n',
                        1,
                    )
                else:
                    updated = 'FEATURE_DISABLED_MSG = "ChatDev MCP feature is disabled"\n\n' + updated

            file_path.write_text(updated, encoding="utf-8")
            print(f"✅ Fixed: Applied FEATURE_DISABLED_MSG constant in {file_path}")
            fixes_applied += 1
        elif constant_line in content:
            print(f"⏭️  Constant already exists in {file_path}")

    # Fix 2: ChatDev launcher - run.py
    file_path = Path("src/integration/chatdev_launcher.py")
    if file_path.exists():
        content = file_path.read_text(encoding="utf-8")

        # Add constants at module level
        if 'RUN_PY_FILENAME = "run.py"' not in content:
            # Find import section end
            import_end = content.find("\n\n", content.find("import "))
            if import_end != -1:
                insertion_point = import_end + 2
                constants = """
# File name constants
RUN_PY_FILENAME = "run.py"
RUN_OLLAMA_FILENAME = "run_ollama.py"

"""
                updated = content[:insertion_point] + constants + content[insertion_point:]

                # Replace occurrences
                updated = updated.replace('"run.py"', "RUN_PY_FILENAME")
                updated = updated.replace('"run_ollama.py"', "RUN_OLLAMA_FILENAME")

                file_path.write_text(updated, encoding="utf-8")
                print(f"✅ Fixed: Created RUN_PY_FILENAME and RUN_OLLAMA_FILENAME constants in {file_path}")
                fixes_applied += 1
        else:
            print(f"⏭️  Constants already exist in {file_path}")

    return fixes_applied


def fix_unnecessary_async_keywords():
    """Remove async keyword from functions that don't use await."""
    fixes = [
        (
            Path("src/system/output_source_intelligence.py"),
            "async def init(self):",
            "def init(self):",
            68,
            ["await self.init()", "await _output_intelligence.init()"],
        ),
        (
            Path("src/system/terminal_intelligence_orchestrator.py"),
            "async def main():",
            "def main():",
            639,
            ["asyncio.run(main())"],
        ),
        (
            Path("src/integration/chatdev_mcp_integration.py"),
            "async def _handle_search_projects(self, query: str, top_k: int = 5) -> Dict[str, Any]:",
            "def _handle_search_projects(self, query: str, top_k: int = 5) -> Dict[str, Any]:",
            186,
            ["await self._handle_search_projects"],
        ),
        (
            Path("src/integration/chatdev_mcp_integration.py"),
            "async def _handle_index_workspace(self, start_fresh: bool = False) -> Dict[str, Any]:",
            "def _handle_index_workspace(self, start_fresh: bool = False) -> Dict[str, Any]:",
            208,
            ["await self._handle_index_workspace"],
        ),
        (
            Path("src/integration/chatdev_mcp_integration.py"),
            "async def _handle_project_summary(self, project_name: str) -> Dict[str, Any]:",
            "def _handle_project_summary(self, project_name: str) -> Dict[str, Any]:",
            229,
            ["await self._handle_project_summary"],
        ),
        (
            Path("src/integration/chatdev_mcp_integration.py"),
            "async def test_complete_integration():",
            "def test_complete_integration():",
            295,
            ["asyncio.run(test_complete_integration())"],
        ),
    ]

    fixes_applied = 0

    for file_path, old_pattern, new_pattern, line_num, guard_patterns in fixes:
        if not file_path.exists():
            print(f"⏭️  Skipped: {file_path} not found")
            continue

        content = file_path.read_text(encoding="utf-8")

        if any(pattern in content for pattern in guard_patterns):
            print(f"⏭️  Skipped: async usage detected in {file_path} (line {line_num})")
            continue

        if old_pattern in content:
            updated = content.replace(old_pattern, new_pattern)
            file_path.write_text(updated, encoding="utf-8")
            print(f"✅ Fixed: Removed async from line {line_num} in {file_path}")
            fixes_applied += 1
        else:
            print(f"⏭️  Already fixed or pattern not found in {file_path} (line {line_num})")

    return fixes_applied


def main():
    """Run all quick win fixes."""
    print("\n" + "=" * 80)
    print("Phase 1: Quick Wins - Automated Error Fixes")
    print("=" * 80 + "\n")

    total_fixes = 0

    # Fix 1: Unused imports
    print("1️⃣  Removing unused imports...")
    if fix_unused_import_sys():
        total_fixes += 1

    # Fix 2: Duplicate string literals
    print("\n2️⃣  Creating string constants...")
    total_fixes += fix_duplicate_string_literals()

    # Fix 3: Unnecessary async keywords
    print("\n3️⃣  Removing unnecessary async keywords...")
    total_fixes += fix_unnecessary_async_keywords()

    # Summary
    print("\n" + "=" * 80)
    print(f"✅ Total Fixes Applied: {total_fixes}/9")
    print("=" * 80 + "\n")

    if total_fixes > 0:
        print("📝 Next Steps:")
        print("   1. Review changes: git diff")
        print("   2. Run tests: pytest tests/test_phase8_resilience.py")
        print("   3. Commit: git add -A && git commit -m 'fix: Phase 1 quick wins (9 errors)'")
    else:
        print("ℹ️  All fixes already applied or files not found.")


if __name__ == "__main__":
    main()
