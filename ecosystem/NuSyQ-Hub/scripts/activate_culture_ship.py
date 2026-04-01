#!/usr/bin/env python3
"""Activate Culture Ship Strategic Advisor.

[ROUTE AGENTS] 🤖
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration.ecosystem_activator import EcosystemActivator


def main():
    print("\n🚀 ACTIVATING CULTURE SHIP STRATEGIC ADVISOR\n")
    print("=" * 70)

    activator = EcosystemActivator()

    # Get current status
    culture_ship = activator.get_system("culture_ship_advisor")
    if culture_ship and culture_ship.status == "active":
        print("✅ Culture Ship is already active!")
        print(f"   Capabilities: {', '.join(culture_ship.capabilities)}")
        return

    # Discover systems
    systems = activator.discover_systems()
    culture_ship_system = next((s for s in systems if s.system_id == "culture_ship_advisor"), None)

    if not culture_ship_system:
        print("❌ Culture Ship not found in discovered systems")
        return

    print(f"📍 Found: {culture_ship_system.name}")
    print(f"   Type: {culture_ship_system.system_type}")
    print(f"   Capabilities: {len(culture_ship_system.capabilities)}")
    print()

    # Activate
    print("🔌 Activating...")
    success = activator.activate_system(culture_ship_system)

    if success:
        print("✅ Culture Ship ACTIVATED!")
        print(f"   Status: {culture_ship_system.status}")
        print(f"   Instance: {type(culture_ship_system.instance).__name__}")
        print("   Capabilities:")
        for cap in culture_ship_system.capabilities:
            print(f"      - {cap}")

        # Write updated state
        registry_path = Path("state/ecosystem_registry.json")
        registry_path.parent.mkdir(parents=True, exist_ok=True)

        import json

        registry_data = {
            "systems": {
                sid: {
                    "name": s.name,
                    "module_path": s.module_path,
                    "system_type": s.system_type,
                    "capabilities": s.capabilities,
                    "metadata": s.metadata,
                    "activated_at": s.activated_at,
                }
                for sid, s in activator.systems.items()
            }
        }
        registry_path.write_text(json.dumps(registry_data, indent=2), encoding="utf-8")
        print(f"\n💾 Updated registry: {registry_path}")

    else:
        print("❌ Activation failed!")
        if culture_ship_system.error:
            print(f"   Error: {culture_ship_system.error}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
