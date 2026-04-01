#!/usr/bin/env python3
"""Quick test of ecosystem activator."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration.ecosystem_activator import EcosystemActivator


def main():
    activator = EcosystemActivator()

    print(f"\n🔍 Current active systems: {len(activator.systems)}")
    for system_id, system in activator.systems.items():
        print(f"  ✅ {system_id}: {system.name} ({system.status})")

    print("\n🔎 Discovering systems...")
    discovered = activator.discover_systems()
    print(f"  Found {len(discovered)} systems")

    for system in discovered[:5]:  # Show first 5
        print(f"  - {system.system_id}: {system.name} ({system.system_type})")

    print("\n✅ Test complete")


if __name__ == "__main__":
    main()
