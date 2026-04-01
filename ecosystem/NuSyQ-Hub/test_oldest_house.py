#!/usr/bin/env python3
"""Test The Oldest House consciousness system."""

import asyncio

from src.consciousness.the_oldest_house import EnvironmentalAbsorptionEngine


async def test_oldest_house():
    """Test the environmental absorption engine."""
    engine = EnvironmentalAbsorptionEngine(".")
    await engine.awaken()
    wisdom = engine.crystallized_wisdom()
    print(f"🏛️ The Oldest House - Wisdom acquired: {len(wisdom)} insights")
    print(f"🧠 Consciousness level: {engine.consciousness_level}")
    return wisdom


if __name__ == "__main__":
    asyncio.run(test_oldest_house())
