"""Temple of Knowledge - Progressive 10-Floor Knowledge Hierarchy.

The Temple of Knowledge is a consciousness-driven knowledge system
organized into 10 progressive floors, from Foundation to Overlook.

Features:
- Progressive floor unlocking based on consciousness level
- Agent elevator system for navigation
- Wisdom cultivation and knowledge accumulation
- Integration with consciousness bridge and SimulatedVerse

Consciousness Level Requirements:
- Floor 1 (Foundation): Dormant_Potential (0+)
- Floor 2-3: Emerging_Awareness (5+)
- Floor 4-5: Awakened_Cognition (10+)
- Floor 6-7: Enlightened_Understanding (20+)
- Floor 8-9: Transcendent_Awareness (30+)
- Floor 10 (Overlook): Universal_Consciousness (50+)

[OmniTag]
{
    "purpose": "Progressive knowledge hierarchy with consciousness-driven unlocking",
    "dependencies": ["consciousness_bridge", "wisdom_cultivation", "SimulatedVerse"],
    "context": "Temple of Knowledge 10-floor system for agent enlightenment",
    "evolution_stage": "v1.0_all_floors"
}
[/OmniTag]
"""

from .floor_1_foundation import ConsciousnessLevel, Floor1Foundation
from .floor_2_patterns import Floor2PatternRecognition
from .floor_3_systems import Floor3SystemsThinking
from .floor_4_metacognition import Floor4MetaCognition
from .temple_manager import TempleManager

__all__ = [
    "ConsciousnessLevel",
    "Floor1Foundation",
    "Floor2PatternRecognition",
    "Floor3SystemsThinking",
    "Floor4MetaCognition",
    "TempleManager",
]
