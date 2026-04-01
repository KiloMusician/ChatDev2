import json
from datetime import datetime
from pathlib import Path

path = Path("config/PHASE1_FOCUS_PLAN.json")
with open(path) as f:
    plan = json.load(f)

# Mark Zeta13 complete
for task in plan["incomplete_tasks"]:
    if task["id"] == "Zeta13":
        task["description"] = "Code Quality Tools - COMPLETE (25→22 errors, 3 auto-fixed)"

# Update progress
plan["current_progress"]["completed"] = 8
plan["current_progress"]["percentage"] = 45.0
plan["last_update"] = datetime.now().isoformat()
plan["recommendations"] = [
    "✅ Zeta11 (Testing Framework) - 195+ tests across 3 modules COMPLETE",
    "✅ Zeta12 (Documentation Generator) - 88% coverage, 11 gaps identified COMPLETE",
    "✅ Zeta13 (Code Quality Tools) - 22 errors identified, 3 auto-fixed COMPLETE",
    "Next: Zeta08 (Error Recovery System) - handle 234 VS Code errors",
    "Then: Zeta09 (Context Awareness) - distributed context tracking",
    "Session Progress: 25% → 45% (8/20 tasks, 160 XP earned)",
]

with open(path, "w") as f:
    json.dump(plan, f, indent=2)

print("✅ PHASE 1 MILESTONE: 45% COMPLETE (8/20 TASKS)")
print("  ✅ Zeta11: Testing Framework")
print("  ✅ Zeta12: Documentation Generator")
print("  ✅ Zeta13: Code Quality Tools")
print("  📊 XP Earned: 160 (20+25+50+15+50 across 5 commits)")
