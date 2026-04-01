"""Consciousness package - Temple of Knowledge + Consciousness Bridge components.

Provides structures for consciousness hierarchy (temple) and symbolic reasoning
components for ΞNuSyQ multi-agent orchestration.
"""

# Temple of Knowledge components
from . import temple_of_knowledge
from .consciousness_validator import ConsciousnessValidator
# Consciousness Bridge components (MegaTag, SymbolicCognition, Validator)
from .megatag_processor import MegaTagProcessor
from .symbolic_cognition import SymbolicCognition
from .temple_of_knowledge import (ConsciousnessLevel, Floor1Foundation,
                                  TempleManager)

__all__ = [
    # Temple components
    "ConsciousnessLevel",
    "ConsciousnessValidator",
    "Floor1Foundation",
    # Bridge components
    "MegaTagProcessor",
    "SymbolicCognition",
    "TempleManager",
    "temple_of_knowledge",
]

__version__ = "1.0.0"
__author__ = "NuSyQ Development Team"
