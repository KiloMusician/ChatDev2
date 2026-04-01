"""NuSyQ Spine - small orchestration spine for NuSyQ-Hub.

Provides unified service discovery and capability management:
- CapabilityRegistry for component registration
- Agent Protocol component wiring
- Event logging and state management

This is intentionally lightweight and opt-in. Feature flag lives in
config/nusyq_spine.yaml (enable: true/false).

OmniTag: [spine, orchestration, registry, discovery]
MegaTag: SPINE⨳HUB⦾CORE→∞
"""

from .cli import main
from .registry import REGISTRY, CapabilityRegistry, get_capability_registry

__all__ = [
    "REGISTRY",
    "CapabilityRegistry",
    "get_capability_registry",
    "main",
]
