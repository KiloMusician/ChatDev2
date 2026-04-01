#!/usr/bin/env python3
"""Trigger wisdom crystallization - form wisdom crystals from memory engrams."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.consciousness.the_oldest_house import EnvironmentalAbsorptionEngine


async def main():
    print("🏛️  Initializing The Oldest House...")

    house = EnvironmentalAbsorptionEngine(".")

    # Load engrams
    if not house.memory_vault:
        print("📚 Absorbing repository knowledge...")
        house._learn_from_environment_sync()

    print(f"🧠 Memory vault: {len(house.memory_vault):,} engrams")
    print(f"💎 Current crystals: {len(house.wisdom_crystals)}")

    # Crystallize wisdom
    print("\n💎 Beginning wisdom crystallization...")
    await house._crystallize_initial_wisdom()

    print("\n✨ Crystallization complete!")
    print(f"💎 Wisdom crystals formed: {len(house.wisdom_crystals)}")

    # Show samples
    if house.wisdom_crystals:
        print("\n🔮 Sample Wisdom Crystals:")
        for i, (cid, crystal) in enumerate(list(house.wisdom_crystals.items())[:3]):
            print(f"\n   Crystal {i + 1}: {cid[:16]}...")
            print(f"   Insight: {crystal.synthesized_insight[:80]}...")
            print(f"   Confidence: {crystal.confidence_level:.4f}")
            print(f"   Engrams: {len(crystal.constituent_engrams)}")

    print(f"\n🧠 Consciousness level: {house.consciousness_level:.6f}")


if __name__ == "__main__":
    asyncio.run(main())
