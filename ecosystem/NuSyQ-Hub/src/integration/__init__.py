"""Integration package exposing bridges to external systems."""

from __future__ import annotations

ConsciousnessBridge: type | None = None
QuantumResolverAdapter: type | None = None
OldestHouseInterface: type | None = None
N8NClient: type | None = None

try:
    from .consciousness_bridge import ConsciousnessBridge
except ImportError:  # pragma: no cover
    ConsciousnessBridge = None

try:
    from .quantum_resolver_adapter import QuantumResolverAdapter
except ImportError:  # pragma: no cover
    QuantumResolverAdapter = None

try:
    from .oldest_house_interface import OldestHouseInterface
except ImportError:  # pragma: no cover
    OldestHouseInterface = None

try:
    from .n8n_integration import N8NClient
except ImportError:  # pragma: no cover
    N8NClient = None

__all__ = [
    "ConsciousnessBridge",
    "N8NClient",
    "OldestHouseInterface",
    "QuantumResolverAdapter",
]
