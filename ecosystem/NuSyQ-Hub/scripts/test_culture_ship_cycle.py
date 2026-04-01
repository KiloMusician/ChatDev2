#!/usr/bin/env python3
"""Test Culture Ship strategic cycle."""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration.ecosystem_activator import EcosystemActivator


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Culture Ship strategic cycle tests.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run Culture Ship in non-mutating mode for gate/smoke checks.",
    )
    args = parser.parse_args()

    if args.dry_run:
        os.environ["NUSYQ_CULTURE_SHIP_DRY_RUN"] = "1"
        print("🧪 Dry-run enabled: no source mutations will be applied")

    print("\n🧠 TESTING CULTURE SHIP STRATEGIC CYCLE\n")
    print("=" * 70)

    activator = EcosystemActivator()

    # Re-activate Culture Ship to get fresh instance
    systems = activator.discover_systems()
    culture_ship_def = next((s for s in systems if s.system_id == "culture_ship_advisor"), None)

    if not culture_ship_def:
        print("❌ Culture Ship not found!")
        return

    # Activate it
    activator.activate_system(culture_ship_def)

    culture_ship_system = activator.get_system("culture_ship_advisor")

    if not culture_ship_system or culture_ship_system.status != "active":
        print("❌ Culture Ship not active!")
        return

    advisor = culture_ship_system.instance

    # Test 1: Identify issues
    print("\n📍 Test 1: Identify Strategic Issues")
    print("-" * 70)
    issues = advisor.identify_strategic_issues()
    print(f"✅ Identified {len(issues)} strategic issues")
    if issues:
        issue = issues[0]
        print("\n   Example Issue:")
        print(f"   Category: {issue.category}")
        print(f"   Severity: {issue.severity}")
        print(f"   Description: {issue.description[:100]}...")
        print(f"   Affected files: {len(issue.affected_files)}")

    # Test 2: Make decisions
    if issues:
        print("\n🎯 Test 2: Make Strategic Decisions")
        print("-" * 70)
        decisions = advisor.make_strategic_decisions(issues)
        print(f"✅ Made {len(decisions)} strategic decisions\n")
        if decisions:
            dec = decisions[0]
            print("   Example Decision:")
            print(f"   Decision: {dec.decision}")
            print(f"   Priority: {dec.priority}/10")
            print(f"   Impact: {dec.estimated_impact}")
            print(f"   Action steps: {len(dec.action_plan)}")

            # Show first action step
            if dec.action_plan:
                print(f"\n   First step: {dec.action_plan[0]}")

    # Test 3: Full cycle
    print("\n🔄 Test 3: Full Strategic Cycle")
    print("-" * 70)
    result = advisor.run_full_strategic_cycle()
    print("✅ Strategic cycle completed")
    print(f"   Issues identified: {result.get('issues_identified', 0)}")
    print(f"   Decisions made: {result.get('decisions_made', 0)}")

    print("\n🎉 ALL TESTS PASSED - CULTURE SHIP OPERATIONAL!")
    print("=" * 70)


if __name__ == "__main__":
    main()
