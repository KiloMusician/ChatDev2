"""🗂️ Repository Dictionary System.

Unified repository organization and mapping system.

OmniTag: {
    "purpose": "Centralized repository dictionary and organization system",
    "dependencies": ["RepositoryCoordinator", "Repository-Context-Compendium-System", "system inventories"],
    "context": "Master repository knowledge and organization hub",
    "evolution_stage": "v1.0"
}

MegaTag: {
    "type": "DictionarySystem",
    "integration_points": ["repository_mapping", "system_inventory", "file_organization", "consciousness_bridges"],
    "related_tags": ["RepositoryManager", "SystemCoordinator", "OrganizationHub"]
}

RSHTS: ΞΨΩΣ∞⟨DICTIONARY⟩→ΦΣΣ⟨REPOSITORY⟩→∞⟨ORGANIZATION-HUB⟩
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from .consciousness_bridge import \
        ConsciousnessBridge as ConsciousnessBridgeType
    from .repository_dictionary import \
        RepositoryDictionary as RepositoryDictionaryType
    from .system_organizer import SystemOrganizer as SystemOrganizerType
    from .unified_mapper import UnifiedMapper as UnifiedMapperType

RepositoryDictionary: type[RepositoryDictionaryType] | None
try:
    _repo_module = importlib.import_module(".repository_dictionary", __package__)
    RepositoryDictionary = cast(type["RepositoryDictionaryType"], _repo_module.RepositoryDictionary)
except (ImportError, AttributeError, TypeError):
    RepositoryDictionary = None

SystemOrganizer: type[SystemOrganizerType] | None
try:
    _organizer_module = importlib.import_module(".system_organizer", __package__)
    SystemOrganizer = cast(type["SystemOrganizerType"], _organizer_module.SystemOrganizer)
except (ImportError, AttributeError, TypeError):
    SystemOrganizer = None

UnifiedMapper: type[UnifiedMapperType] | None
try:
    _mapper_module = importlib.import_module(".unified_mapper", __package__)
    UnifiedMapper = cast(type["UnifiedMapperType"], _mapper_module.UnifiedMapper)
except (ImportError, AttributeError, TypeError):
    UnifiedMapper = None

ConsciousnessBridge: type[ConsciousnessBridgeType] | None
try:
    _bridge_module = importlib.import_module(".consciousness_bridge", __package__)
    ConsciousnessBridge = cast(type["ConsciousnessBridgeType"], _bridge_module.ConsciousnessBridge)
except (ImportError, AttributeError, TypeError):
    ConsciousnessBridge = None

__all__ = [
    "ConsciousnessBridge",
    "RepositoryDictionary",
    "SystemOrganizer",
    "UnifiedMapper",
]

__version__ = "1.0.0"
__status__ = "Operational"
