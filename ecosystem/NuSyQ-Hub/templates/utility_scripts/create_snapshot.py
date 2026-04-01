#!/usr/bin/env python3
"""Repository Coverage Snapshot Creator
Purpose: Final verification of directory contextual documentation

OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""

import json
from datetime import datetime
from pathlib import Path


def create_snapshot():
    print("🎯 Creating Repository Snapshot...")

    # Create comprehensive repository snapshot
    snapshot_data = {
        "snapshot_info": {
            "timestamp": datetime.now().isoformat(),
            "purpose": "Complete directory contextual coverage verification",
            "session": "Directory audit completion",
            "version": "v4.0_complete",
        },
        "directory_analysis": {},
        "coverage_summary": {},
    }

    # Scan all directories
    total_dirs = 0
    covered_dirs = 0
    missing_dirs = []

    for dirpath in Path(".").rglob("*"):
        if dirpath.is_dir() and ".venv" not in str(dirpath) and "__pycache__" not in str(dirpath):
            total_dirs += 1
            relative_path = str(dirpath.relative_to("."))

            # Check for contextual files
            context_files = list(dirpath.glob("*CONTEXT*.md"))
            readme_files = list(dirpath.glob("README*.md"))

            has_documentation = bool(context_files or readme_files)

            snapshot_data["directory_analysis"][relative_path] = {
                "has_context": len(context_files) > 0,
                "has_readme": len(readme_files) > 0,
                "context_files": [f.name for f in context_files],
                "readme_files": [f.name for f in readme_files],
                "documented": has_documentation,
                "file_count": len(list(dirpath.iterdir())) if dirpath.exists() else 0,
            }

            if has_documentation:
                covered_dirs += 1
            else:
                missing_dirs.append(relative_path)

    # Summary statistics
    coverage_pct = round((covered_dirs / total_dirs * 100), 2) if total_dirs > 0 else 0
    snapshot_data["coverage_summary"] = {
        "total_directories": total_dirs,
        "covered_directories": covered_dirs,
        "missing_directories": len(missing_dirs),
        "coverage_percentage": coverage_pct,
        "missing_list": missing_dirs,
    }

    # Save snapshot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_file = Path(".snapshots") / f"directory_coverage_snapshot_{timestamp}.json"
    snapshot_file.parent.mkdir(exist_ok=True)

    with open(snapshot_file, "w") as f:
        json.dump(snapshot_data, f, indent=2)

    print(f"✅ Snapshot saved: {snapshot_file.name}")
    print(f"📊 Coverage: {covered_dirs}/{total_dirs} directories ({coverage_pct}%)")

    if missing_dirs:
        print(f"❌ Missing documentation: {len(missing_dirs)} directories")
        for missing in sorted(missing_dirs)[:10]:
            print(f"  📁 {missing}")
        if len(missing_dirs) > 10:
            print(f"  ... and {len(missing_dirs) - 10} more")
    else:
        print("🎉 Perfect coverage achieved!")

    return snapshot_file


if __name__ == "__main__":
    create_snapshot()
