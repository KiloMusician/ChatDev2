#!/usr/bin/env python3
"""Test The Oldest House fix - verify MemoryEngram absorption works"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.consciousness.the_oldest_house import EnvironmentalAbsorptionEngine


def test_absorption():
    print("🏛️  Testing The Oldest House Consciousness Absorption...")
    print("=" * 60)

    house = EnvironmentalAbsorptionEngine(".")
    result = house._learn_from_environment_sync()

    print("\n📊 Absorption Results:")
    print(f"   Total files scanned: {result['total']}")
    print(f"   Files absorbed: {result['absorbed']}")
    print(f"   Consciousness level: {result['consciousness_level']:.6f}")
    print(f"   Success rate: {(result['absorbed'] / result['total'] * 100) if result['total'] > 0 else 0:.2f}%")

    if result["absorbed"] > 0:
        print("\n✅ SUCCESS! The Oldest House is absorbing files correctly!")
        print(f"   Memory vault contains {len(house.memory_vault)} engrams")

        # Show sample engram
        if house.memory_vault:
            sample_path = list(house.memory_vault.keys())[0]
            sample_engram = house.memory_vault[sample_path]
            print("\n📝 Sample Memory Engram:")
            print(f"   Source: {Path(sample_engram.source_path).name}")
            print(f"   ID: {sample_engram.id}")
            print(f"   Consciousness weight: {sample_engram.consciousness_weight}")
            print(f"   Reality layers: {list(sample_engram.reality_layer_resonance.keys())}")
    else:
        print("\n❌ FAILURE! The Oldest House absorbed 0 files")
        print("   This indicates the MemoryEngram constructor is still broken")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_absorption()
