"""Game development prototyping utilities.

Lightweight components for prototyping game mechanics — combat system
with abstract action interface and particle effects system.

For production game systems, see src.games for the full ecosystem.

OmniTag: {
    "purpose": "game_dev_prototyping",
    "tags": ["Games", "Prototyping", "Combat", "Particles"],
    "category": "game_systems",
    "evolution_stage": "v1.0"
}
"""

from .combat_system import (Action, AttackAction, Character, CombatSystem,
                            DefendAction, SkillAction)
from .particle_system import Particle, ParticleEmitter

__all__ = [
    # Combat
    "Action",
    "AttackAction",
    "Character",
    "CombatSystem",
    "DefendAction",
    # Particles
    "Particle",
    "ParticleEmitter",
    "SkillAction",
]
