#!/usr/bin/env python3
"""Automated __future__ Import Fixer for NuSyQ-Hub
-------------------------------------------------
Fixes SyntaxError: from __future__ imports must occur at the beginning of file

Pattern:
- Moves 'from __future__ import annotations' to line immediately after docstring
- Preserves shebang, docstring, and all other imports
- Dry-run mode by default

OmniTag: [fix_future_imports, automated_code_repair, import_ordering, python313_compliance]
"""

from __future__ import annotations

from pathlib import Path

# Files discovered with __future__ import issues
AFFECTED_FILES = [
    "src/tools/agent_context_manager.py",
    "src/tools/embeddings_exporter.py",
    "src/tools/maze_solver.py",
    "src/ai/conversation_manager.py",
    "src/context/extensions/file_summaries.py",
    "src/context/extensions/repo_stats.py",
    "src/copilot/bridge_cli.py",
    "src/copilot/task_manager.py",
    "src/integration/chatdev_service.py",
    "src/integration/n8n_integration.py",
    "src/orchestration/colonist_scheduler.py",
    "src/orchestration/ingest_maze_summary.py",
    "src/system/feature_flags.py",
    "src/system/task_queue.py",
    "src/tools/ai_backend_status.py",
    "src/tools/meshctl.py",
    "src/tools/performance_optimizer.py",
    "src/tools/register_lattice.py",
    "src/tools/run_and_capture.py",
    "src/tools/vibe_indexer.py",
    "src/utils/timeout_config.py",
    "src/diagnostics/integrated_health_orchestrator.py",
]


def find_docstring_end(lines: list[str]) -> int:
    """Find where the module docstring ends."""
    in_docstring = False
    docstring_char = None
    start_line = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Skip shebang and encoding
        if stripped.startswith("#"):
            continue

        # Start of docstring
        if not in_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
            docstring_char = stripped[:3]
            in_docstring = True
            start_line = i

            # Single-line docstring
            if stripped.endswith(docstring_char) and len(stripped) > 6:
                return i + 1

        # End of docstring
        elif in_docstring and stripped.endswith(docstring_char):
            return i + 1

        # No docstring, first real code line
        elif not in_docstring and stripped and not stripped.startswith("#"):
            return i

    return start_line + 1


def fix_future_import(file_path: Path, dry_run: bool = True) -> tuple[bool, str]:
    """Fix __future__ import ordering in a single file.

    Returns:
        (changed, message) tuple
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Find __future__ import line
        future_line_idx = None
        for i, line in enumerate(lines):
            if "from __future__ import" in line:
                future_line_idx = i
                break

        if future_line_idx is None:
            return False, f"⚠️  No __future__ import found in {file_path.name}"

        # Check if already at correct position (line 0-2 for shebang/encoding/docstring start)
        docstring_end = find_docstring_end(lines)

        if future_line_idx < docstring_end:
            return (
                False,
                f"✅ {file_path.name}: __future__ import already correct (line {future_line_idx + 1})",
            )

        # Extract the __future__ import line
        future_import = lines[future_line_idx]

        # Remove from current position
        lines_without_future = lines[:future_line_idx] + lines[future_line_idx + 1 :]

        # Insert at correct position (after docstring)
        lines_fixed = [
            *lines_without_future[:docstring_end],
            future_import,
            *lines_without_future[docstring_end:],
        ]

        # Write back
        if not dry_run:
            file_path.write_text("\n".join(lines_fixed), encoding="utf-8")
            return (
                True,
                f"✅ FIXED {file_path.name}: Moved __future__ from line {future_line_idx + 1} → {docstring_end + 1}",
            )
        else:
            return (
                True,
                f"🔍 DRY-RUN {file_path.name}: Would move __future__ from line {future_line_idx + 1} → {docstring_end + 1}",
            )

    except Exception as e:
        return False, f"❌ ERROR {file_path.name}: {e}"


def main():
    """Run batch __future__ import fixes."""
    repo_root = Path(__file__).parent.parent

    print("=" * 70)
    print("🔧 NuSyQ-Hub __future__ Import Batch Fixer")
    print("=" * 70)
    print(f"\n📁 Repository: {repo_root}")
    print(f"📋 Files to check: {len(AFFECTED_FILES)}\n")

    # Dry-run first
    print("🔍 DRY-RUN MODE (no changes will be made)\n")

    results = []
    for rel_path in AFFECTED_FILES:
        file_path = repo_root / rel_path
        if not file_path.exists():
            results.append((False, f"⚠️  File not found: {rel_path}"))
            continue

        changed, message = fix_future_import(file_path, dry_run=True)
        results.append((changed, message))
        print(message)

    # Summary
    needs_fixing = sum(1 for changed, _ in results if changed)
    print(f"\n📊 Summary: {needs_fixing}/{len(AFFECTED_FILES)} files need fixing")

    # Confirm before applying
    if needs_fixing > 0:
        print("\n" + "=" * 70)
        response = input(f"Apply fixes to {needs_fixing} files? [y/N]: ").strip().lower()

        if response == "y":
            print("\n🚀 APPLYING FIXES...\n")

            fixed_count = 0
            for rel_path in AFFECTED_FILES:
                file_path = repo_root / rel_path
                if not file_path.exists():
                    continue

                changed, message = fix_future_import(file_path, dry_run=False)
                if changed:
                    fixed_count += 1
                print(message)

            print(f"\n✅ COMPLETE: Fixed {fixed_count}/{needs_fixing} files")
            print("\n📝 Next steps:")
            print("   1. Run: python health.py --awaken")
            print("   2. Verify: Multi-AI Orchestrator importable")
            print("   3. Test: python -c 'from src.orchestration.unified_ai_orchestrator import MultiAIOrchestrator'")
        else:
            print("\n❌ Cancelled. No changes made.")
    else:
        print("\n✅ No fixes needed!")


if __name__ == "__main__":
    main()
