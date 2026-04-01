#!/usr/bin/env python3
"""Problem → Quest → Fix Pipeline

This is the MISSING LINK that converts diagnostic problems into
executable quests that actually FIX the issues.

Workflow:
1. Load diagnostics from data/diagnostics/
2. Convert to Processing Units (PUs)
3. Submit PUs to Unified PU Queue
4. Autonomous Quest Generator converts PUs → Quests
5. Agents execute quests and fix issues
6. Verify fixes and close quests
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def load_diagnostics() -> dict:
    """Load all diagnostic data."""
    diag_dir = Path("data/diagnostics")
    if not diag_dir.exists():
        print("❌ No diagnostics found. Run export_vscode_diagnostics.py first.")
        return {}

    all_diagnostics = {"sonarqube": {}, "vscode": {}, "total_issues": 0}

    # Load SonarQube results
    sonar_file = diag_dir / "sonarqube_scan_results.json"
    if sonar_file.exists():
        with open(sonar_file, encoding="utf-8") as f:
            all_diagnostics["sonarqube"] = json.load(f)
            all_diagnostics["total_issues"] += all_diagnostics["sonarqube"].get("total_issues", 0)

    # Load VSCode diagnostics
    vscode_file = diag_dir / "vscode_diagnostics_export.json"
    if vscode_file.exists():
        with open(vscode_file, encoding="utf-8") as f:
            all_diagnostics["vscode"] = json.load(f)
            all_diagnostics["total_issues"] += all_diagnostics["vscode"].get("total_issues", 0)

    return all_diagnostics


def create_pu_from_quest(quest: dict) -> dict:
    """Convert a quest dict to a Processing Unit (PU)."""
    return {
        "id": f"diag_{quest.get('sonarqube_code', 'unknown')}_{int(datetime.now().timestamp())}",
        "title": quest["title"],
        "description": quest["description"],
        "type": quest.get("type", "RefactorPU"),
        "priority": quest.get("priority", "medium"),
        "source_repo": "NuSyQ-Hub",
        "created_at": datetime.now().isoformat(),
        "status": "queued",
        "metadata": {
            "diagnostic_source": "sonarqube",
            "code": quest.get("sonarqube_code", "unknown"),
            "files_affected": quest.get("files_affected", []),
            "total_occurrences": quest.get("total_occurrences", 0),
        },
        "proof_criteria": quest.get("proof_criteria", []),
        "assigned_agents": [],
    }


def submit_pus_to_queue(pus: list[dict]) -> dict:
    """Submit PUs to the unified PU queue."""
    queue_file = Path("data") / "unified_pu_queue.json"

    # Load existing queue
    if queue_file.exists():
        with open(queue_file, encoding="utf-8") as f:
            existing_queue = json.load(f)
            # Handle both list and dict formats
            if isinstance(existing_queue, list):
                queue_list = existing_queue
            else:
                queue_list = existing_queue.get("queue", [])
    else:
        queue_list = []

    # Add new PUs
    existing_ids = {pu["id"] for pu in queue_list}
    new_pus = [pu for pu in pus if pu["id"] not in existing_ids]

    queue_list.extend(new_pus)

    # Save queue as list (matches current format)
    queue_file.parent.mkdir(parents=True, exist_ok=True)
    with open(queue_file, "w", encoding="utf-8") as f:
        json.dump(queue_list, f, indent=2)

    return {
        "total_submitted": len(new_pus),
        "duplicates_skipped": len(pus) - len(new_pus),
        "queue_size": len(queue_list),
    }


def main():
    """Main pipeline execution."""
    print("=" * 80)
    print("🔄 PROBLEM → QUEST PIPELINE")
    print("=" * 80)
    print()

    # Step 1: Load diagnostics
    print("📊 Step 1: Loading diagnostics...")
    diagnostics = load_diagnostics()

    if not diagnostics or diagnostics["total_issues"] == 0:
        print("❌ No diagnostics found. Run analysis scripts first:")
        print("   - python scripts/export_vscode_diagnostics.py")
        print("   - python scripts/analyze_sonarqube_issues.py")
        return 1

    print(f"  ✅ Loaded {diagnostics['total_issues']} total issues")
    print(f"     - SonarQube: {diagnostics['sonarqube'].get('total_issues', 0)}")
    print(f"     - VSCode: {diagnostics['vscode'].get('total_issues', 0)}")
    print()

    # Step 2: Load quests
    print("🎯 Step 2: Loading quests...")
    quests = []

    # Load SonarQube quests
    sonar_quests_file = Path("data/diagnostics/sonarqube_quests.json")
    if sonar_quests_file.exists():
        with open(sonar_quests_file, encoding="utf-8") as f:
            quests.extend(json.load(f).get("quests", []))

    # Load VSCode quests
    vscode_quests_file = Path("data/diagnostics/diagnostic_quests.json")
    if vscode_quests_file.exists():
        with open(vscode_quests_file, encoding="utf-8") as f:
            quests.extend(json.load(f).get("quests", []))

    print(f"  ✅ Loaded {len(quests)} quests")
    print()

    # Step 3: Convert quests to PUs
    print("🔄 Step 3: Converting quests to Processing Units...")
    pus = [create_pu_from_quest(quest) for quest in quests]
    print(f"  ✅ Created {len(pus)} PUs")
    print()

    # Step 4: Submit to queue
    print("📤 Step 4: Submitting PUs to queue...")
    result = submit_pus_to_queue(pus)
    print(f"  ✅ Submitted {result['total_submitted']} new PUs")
    print(f"  Info: Skipped {result['duplicates_skipped']} duplicates")
    print(f"  📊 Queue size: {result['queue_size']}")
    print()

    # Step 5: Show next steps
    print("=" * 80)
    print("✅ PIPELINE COMPLETE")
    print("=" * 80)
    print()
    print("🎯 Next Steps:")
    print("  1. Run autonomous quest generator to convert PUs → Quests:")
    print("     python src/automation/autonomous_quest_generator.py")
    print()
    print("  2. View quest board:")
    print(
        '     python -c "from src.agents.unified_agent_ecosystem import get_ecosystem; e=get_ecosystem(); print(e.get_party_quest_summary())"'
    )
    print()
    print("  3. Execute quests manually or wait for autonomous execution")
    print()
    print("=" * 80)
    print()

    # Show summary of PUs created
    print("📋 PUs Created by Type:")
    pu_types = {}
    for pu in pus:
        pu_type = pu["type"]
        pu_types[pu_type] = pu_types.get(pu_type, 0) + 1

    for pu_type, count in sorted(pu_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {pu_type}: {count}")
    print()

    print("📋 PUs by Priority:")
    pu_priorities = {}
    for pu in pus:
        priority = pu["priority"]
        pu_priorities[priority] = pu_priorities.get(priority, 0) + 1

    for priority in ["critical", "high", "medium", "low"]:
        count = pu_priorities.get(priority, 0)
        if count > 0:
            print(f"  - {priority}: {count}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
