#!/usr/bin/env python3
"""Audit and consolidate "fix" files - identify duplicates and consolidation targets."""

import json
from collections import defaultdict
from pathlib import Path


def analyze_fix_files():
    """Analyze all fix-related files for consolidation opportunities"""
    root = Path(".")
    fix_files = list(root.glob("**/*fix*.py"))

    # Categorize by purpose
    categories = defaultdict(list)

    for file_path in fix_files:
        if ".venv" in str(file_path) or "node_modules" in str(file_path):
            continue

        # Read first 50 lines to understand purpose
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read(2000)  # First 2KB

            # Categorize
            if "import" in file_path.name.lower():
                categories["import_fixes"].append(file_path)
            elif "encoding" in file_path.name.lower():
                categories["encoding_fixes"].append(file_path)
            elif "test" in file_path.name.lower():
                categories["test_files"].append(file_path)
            elif "ollama" in content.lower() or "host" in file_path.name.lower():
                categories["ollama_fixes"].append(file_path)
            elif "simulatedverse" in file_path.name.lower():
                categories["simulatedverse_fixes"].append(file_path)
            elif "diagnostic" in file_path.name.lower():
                categories["diagnostic_fixes"].append(file_path)
            elif "logging" in file_path.name.lower():
                categories["logging_fixes"].append(file_path)
            elif "oldest_house" in file_path.name.lower():
                categories["oldest_house_fixes"].append(file_path)
            else:
                categories["misc_fixes"].append(file_path)

        except Exception as e:
            print(f"⚠️  Could not read {file_path}: {e}")

    return categories


def consolidation_recommendations(categories):
    """Generate consolidation recommendations"""
    recommendations = []

    # Import fixes consolidation
    if len(categories["import_fixes"]) > 1:
        recommendations.append(
            {
                "category": "Import Fixes",
                "count": len(categories["import_fixes"]),
                "files": [str(f) for f in categories["import_fixes"]],
                "action": "CONSOLIDATE into src/utils/import_resolver.py or scripts/fix_all_imports.py",
                "keep": "src/utils/quick_import_fix.py (most recent, part of infrastructure)",
                "remove": [f for f in categories["import_fixes"] if "quick_import_fix" not in str(f)],
            }
        )

    # Encoding fixes
    if len(categories["encoding_fixes"]) > 1:
        recommendations.append(
            {
                "category": "Encoding Fixes",
                "count": len(categories["encoding_fixes"]),
                "files": [str(f) for f in categories["encoding_fixes"]],
                "action": "CONSOLIDATE into single scripts/fix_encodings.py",
                "keep": "Keep newest, remove duplicates",
                "remove": categories["encoding_fixes"][:-1],  # Keep last one
            }
        )

    # Test files
    if categories["test_files"]:
        recommendations.append(
            {
                "category": "Test Fix Files",
                "count": len(categories["test_files"]),
                "files": [str(f) for f in categories["test_files"]],
                "action": "MOVE to tests/ directory if useful, DELETE if one-off debugging",
                "keep": "Move valuable tests to tests/",
                "remove": "Delete one-off test scripts",
            }
        )

    # Oldest House fixes
    if categories["oldest_house_fixes"]:
        recommendations.append(
            {
                "category": "Oldest House Test Files",
                "count": len(categories["oldest_house_fixes"]),
                "files": [str(f) for f in categories["oldest_house_fixes"]],
                "action": "MOVE test_oldest_house_fix.py to tests/test_oldest_house.py",
                "keep": "tests/test_oldest_house.py (proper test location)",
                "remove": "scripts/test_oldest_house_fix.py (temporary script)",
            }
        )

    # Root-level fix files
    root_fixes = [f for f in categories["misc_fixes"] if f.parent.name == "NuSyQ-Hub"]
    if root_fixes:
        recommendations.append(
            {
                "category": "Root-Level Fix Scripts",
                "count": len(root_fixes),
                "files": [str(f) for f in root_fixes],
                "action": "MOVE to scripts/ or DELETE if obsolete",
                "keep": "None - all should be in scripts/",
                "remove": root_fixes,
            }
        )

    return recommendations


def main():
    print("🔍 Auditing 'fix' files across repository...")
    print("=" * 70)

    categories = analyze_fix_files()

    total_files = sum(len(files) for files in categories.values())
    print(f"\n📊 Found {total_files} fix-related files\n")

    for category, files in sorted(categories.items()):
        if files:
            print(f"📁 {category:25s} {len(files):3d} files")
            for f in files[:3]:  # Show first 3
                print(f"   → {f}")
            if len(files) > 3:
                print(f"   ... and {len(files) - 3} more")
            print()

    print("\n" + "=" * 70)
    print("💡 CONSOLIDATION RECOMMENDATIONS")
    print("=" * 70)

    recommendations = consolidation_recommendations(categories)

    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['category']} ({rec['count']} files)")
        print(f"   Action: {rec['action']}")
        print(f"   Keep: {rec['keep']}")
        if rec["remove"]:
            print(f"   Remove: {len(rec['remove'])} files")

    # Save detailed report
    output = {
        "total_fix_files": total_files,
        "categories": {k: [str(f) for f in v] for k, v in categories.items()},
        "recommendations": recommendations,
    }

    output_path = Path("data/fix_files_audit.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n💾 Detailed report saved to: {output_path}")
    print("=" * 70)

    # Return actionable summary
    return {
        "total": total_files,
        "categories": len(categories),
        "recommendations": len(recommendations),
    }


if __name__ == "__main__":
    result = main()
    print(
        f"\n✅ Audit complete: {result['total']} files analyzed, {result['recommendations']} consolidation opportunities identified"
    )
