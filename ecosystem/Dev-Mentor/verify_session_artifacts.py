#!/usr/bin/env python3
"""
Post-Session Verification

Verify that all critical artifacts are in place for next session.
"""

import json
from pathlib import Path
import sys

BASE = Path(__file__).parent
CHECKS = []

def check_file(path, description):
    """Verify file exists"""
    if path.exists():
        CHECKS.append({"check": description, "status": "✅", "path": str(path)})
        return True
    else:
        CHECKS.append({"check": description, "status": "❌", "path": str(path)})
        return False

def check_registry():
    """Verify registry has 5 entries"""
    registry = BASE / ".substrate" / "registry.jsonl"
    if registry.exists():
        entries = [json.loads(line) for line in registry.read_text().strip().split("\n") if line]
        count = len(entries)
        if count == 5:
            CHECKS.append({"check": "Registry entries (should be 5)", "status": "✅", "count": count})
            return True
        else:
            CHECKS.append({"check": "Registry entries (should be 5)", "status": "⚠️", "count": count})
            return False
    else:
        CHECKS.append({"check": "Registry entries", "status": "❌", "path": str(registry)})
        return False

def check_bootstrap_hook():
    """Verify culture_ship.py has bootstrap hook"""
    culture_ship = BASE / "scripts" / "culture_ship.py"
    if culture_ship.exists():
        content = culture_ship.read_text()
        if "from .substrate.culture_ship_substrate_bridge import bootstrap_culture_ship_substrate" in content:
            CHECKS.append({"check": "Culture Ship bootstrap hook installed", "status": "✅"})
            return True
        else:
            CHECKS.append({"check": "Culture Ship bootstrap hook installed", "status": "❌"})
            return False
    else:
        CHECKS.append({"check": "Culture Ship bootstrap hook", "status": "❌"})
        return False

def main():
    print("\n" + "="*80)
    print("POST-SESSION VERIFICATION — CRITICAL ARTIFACTS")
    print("="*80 + "\n")

    # Core infrastructure
    check_file(BASE / ".substrate" / "culture_ship_substrate_bridge.py", "Substrate bridge (bootstrap)")
    check_file(BASE / ".substrate" / "msgx.schema.json", "MsgX protocol schema")
    check_file(BASE / ".substrate" / "omniatag.schema.json", "OmniTag tagging schema")
    check_registry()
    check_bootstrap_hook()

    # Orchestrator
    check_file(BASE / "scripts" / "orchestrate_phases_3_5.py", "Multi-phase orchestrator")
    check_file(BASE / "scripts" / "phase_2b_remediate.py", "Phase 2B remediation script")

    # Documentation
    check_file(BASE / "state" / "reports" / "closed_loop_proof.md", "Closed loop proof (2A-2C)")
    check_file(BASE / "state" / "reports" / "phases_3_5_orchestration_complete.md", "Orchestration report (3-6)")
    check_file(BASE / "state" / "reports" / "SESSION_MANIFEST_PHASES_1_6_COMPLETE.md", "Session manifest")

    # Quick reference
    check_file(BASE / "PHASES_1_6_COMPLETE.txt", "Executive summary")
    check_file(BASE / "HANDOFF_NEXT_SESSION.md", "Next session handoff")
    check_file(BASE / "DECISION_REGISTRY_QUERIES.sh", "Registry query guide")

    # Print results
    print(f"{'Check':<45} {'Status':<5} {'Detail':<30}")
    print("-" * 80)
    for check in CHECKS:
        status = check["status"]
        detail = check.get("count") or check.get("path", "")
        print(f"{check['check']:<45} {status:<5} {str(detail):<30}")

    print("\n" + "="*80)
    passed = sum(1 for c in CHECKS if "✅" in c["status"])
    total = len(CHECKS)
    print(f"RESULT: {passed}/{total} checks passed")

    if passed == total:
        print("✅ ALL CRITICAL ARTIFACTS VERIFIED — Ready for next session")
        print("="*80 + "\n")
        return 0
    else:
        print("⚠️  SOME ARTIFACTS MISSING — See above for details")
        print("="*80 + "\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
