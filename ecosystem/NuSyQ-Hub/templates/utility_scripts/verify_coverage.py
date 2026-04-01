"""OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""

import json
from pathlib import Path

# Load the latest snapshot
snapshot_file = Path(".snapshots/directory_coverage_snapshot_20250803_210457.json")
with open(snapshot_file) as f:
    data = json.load(f)

coverage = data["coverage_summary"]
print("🎯 FINAL DIRECTORY COVERAGE VERIFICATION")
print("=" * 50)
print(f"✅ Total Directories: {coverage['total_directories']}")
print(f"✅ Documented Directories: {coverage['covered_directories']}")
print(f"📊 Coverage Percentage: {coverage['coverage_percentage']}%")
print(f"❌ Missing Documentation: {coverage['missing_directories']}")
print("")
print("🔍 Directories without contextual files:")
for missing in coverage["missing_list"]:
    print(f"  📁 {missing}")

print("")
if coverage["coverage_percentage"] >= 95:
    print("🎉 EXCELLENT COVERAGE ACHIEVED!")
    print("✅ Repository is comprehensively documented")
else:
    print("⚠️  Additional documentation needed")
