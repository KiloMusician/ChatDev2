#!/usr/bin/env python3
"""Run Culture Ship Strategic Cycle in Production Mode.

Identifies strategic issues, makes decisions, and implements real fixes.
"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration.ecosystem_activator import EcosystemActivator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main():
    print("\n" + "=" * 70)
    print("🌟 CULTURE SHIP STRATEGIC CYCLE - PRODUCTION RUN")
    print("=" * 70 + "\n")

    # Initialize and activate Culture Ship
    activator = EcosystemActivator()
    systems = activator.discover_systems()
    culture_ship_def = next((s for s in systems if s.system_id == "culture_ship_advisor"), None)

    if not culture_ship_def:
        print("❌ Culture Ship not found!")
        return 1

    activator.activate_system(culture_ship_def)
    culture_ship_system = activator.get_system("culture_ship_advisor")

    if not culture_ship_system or culture_ship_system.status != "active":
        print("❌ Culture Ship not active!")
        return 1

    advisor = culture_ship_system.instance
    if not advisor:
        print("❌ No Culture Ship instance!")
        return 1

    # Run full strategic cycle
    print("🚀 Starting strategic cycle...\n")
    result = advisor.run_full_strategic_cycle()

    print("\n" + "=" * 70)
    print("📊 CYCLE RESULTS")
    print("=" * 70)
    print(f"Issues identified: {result.get('issues_count', 0)}")
    print(f"Decisions made: {result.get('decisions_count', 0)}")
    print(f"Fixes applied: {result.get('total_fixes', 0)}")
    print("=" * 70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
