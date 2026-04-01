"""Test full ecosystem activation including new Breathing Integration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.orchestration.ecosystem_activator import EcosystemActivator

if __name__ == "__main__":
    print("🔌 FULL ECOSYSTEM ACTIVATION TEST")
    print("=" * 70)

    activator = EcosystemActivator()
    result = activator.activate_all()

    print("\n📊 ACTIVATION RESULTS:")
    print(f"  Total Systems: {result['total']}")
    print(f"  ✅ Activated:   {result['activated']}")
    print(f"  ❌ Failed:      {result['failed']}")

    print("\n✅ ACTIVE SYSTEMS:")
    for sys in result["systems"]:
        if sys.get("status") == "active":
            caps = sys.get("capabilities", 0)
            print(f"  • {sys['name']}: {caps} capabilities")

    print("\n❌ FAILED SYSTEMS:")
    for sys in result["systems"]:
        if sys.get("status") == "error":
            error = sys.get("error", "unknown")
            print(f"  • {sys['name']}: {error[:100]}")

    print("\n" + "=" * 70)
    print(f"🎯 {result['activated']}/{result['total']} systems operational")
