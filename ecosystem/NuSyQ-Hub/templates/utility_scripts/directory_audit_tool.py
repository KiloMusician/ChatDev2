#!/usr/bin/env python3
"""Directory Audit Tool for KILO-FOOLISH Repository
Scans all directories to find missing contextual README files

OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""

import os
from pathlib import Path
from typing import Any


def scan_directories() -> list[dict[str, Any]]:
    """Scan all directories for contextual README files"""
    Path.cwd()
    results = []

    # Skip these system directories
    skip_dirs = {".git", "__pycache__", "node_modules", ".vscode", ".obsidian", ".snapshots"}

    for root, dirs, files in os.walk("."):
        # Filter out system directories
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]

        path = Path(root)
        relative_path = path.relative_to(Path("."))

        if str(relative_path) == ".":
            continue  # Skip root directory

        # Check for contextual files
        context_files = [f for f in files if "CONTEXT" in f.upper() and f.endswith(".md")]
        readme_files = [f for f in files if f.upper() == "README.MD"]

        has_contextual = len(context_files) > 0
        has_readme = len(readme_files) > 0

        results.append(
            {
                "path": str(relative_path),
                "has_contextual": has_contextual,
                "has_readme": has_readme,
                "context_files": context_files,
                "readme_files": readme_files,
                "total_files": len(files),
                "needs_attention": not has_contextual and not has_readme,
            }
        )

    return results


def main():
    print("🔍 Scanning directories for contextual documentation...")
    print("=" * 60)

    results = scan_directories()

    needs_context = []
    has_readme_only = []
    has_context = []

    for result in results:
        if result["needs_attention"]:
            needs_context.append(result)
        elif result["has_contextual"]:
            has_context.append(result)
        elif result["has_readme"]:
            has_readme_only.append(result)

    print("\n📊 SUMMARY:")
    print(f"Total directories scanned: {len(results)}")
    print(f"✅ Has contextual files: {len(has_context)}")
    print(f"⚠️  Has README only: {len(has_readme_only)}")
    print(f"❌ Needs contextual files: {len(needs_context)}")

    if needs_context:
        print(f"\n❌ DIRECTORIES NEEDING CONTEXTUAL FILES ({len(needs_context)}):")
        for result in needs_context:
            print(f"  • {result['path']} ({result['total_files']} files)")

    if has_readme_only:
        print(f"\n⚠️  DIRECTORIES WITH README ONLY ({len(has_readme_only)}):")
        for result in has_readme_only:
            print(f"  • {result['path']} - {result['readme_files']}")

    if has_context:
        print(f"\n✅ DIRECTORIES WITH CONTEXTUAL FILES ({len(has_context)}):")
        for result in has_context:
            print(f"  • {result['path']} - {result['context_files']}")


if __name__ == "__main__":
    main()
