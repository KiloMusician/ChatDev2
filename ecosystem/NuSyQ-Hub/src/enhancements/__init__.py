# File: /copilot-enhancement-bridge-upgrade/copilot-enhancement-bridge-upgrade/src/enhancements/__init__.py

"""Enhancements Module for KILO-FOOLISH Project.

This module contains enhancements for the KILO-FOOLISH project, including
features for search amplification, context retention, and collaborative intelligence.
It integrates the OmniTag and MegaTag functionalities to improve contextual memory
and symbolic cognition.

Modules:
- search_amplification: Enhances search capabilities using accumulated context.
- context_retention: Manages the retention of contextual information across sessions.
- collaborative_intelligence: Amplifies human-AI collaboration.
- omnitag_system: Manages the creation and management of OmniTags.
- megatag_processor: Processes MegaTags and integrates them into the cognitive framework.
- symbolic_cognition: Handles symbolic reasoning and cognition processes.
"""

from src.copilot.megatag_processor import MegaTagProcessor
from src.copilot.symbolic_cognition import SymbolicCognition
from src.tagging.omnitag_system import OmniTagSystem

from .collaborative_intelligence import CollaborativeIntelligence
from .context_retention import ContextRetention
from .search_amplification import SearchAmplification

__all__ = [
    "CollaborativeIntelligence",
    "ContextRetention",
    "MegaTagProcessor",
    "OmniTagSystem",
    "SearchAmplification",
    "SymbolicCognition",
]
