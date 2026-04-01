"""Legacy import redirect - Use src.healing.quantum_problem_resolver instead.

This file exists for backward compatibility with code that imported
from src.consciousness.quantum_problem_resolver_unified. All new code should
import from src.healing.quantum_problem_resolver directly.

Canonical location: src/healing/quantum_problem_resolver.py
"""

import warnings
from enum import Enum
from typing import Any

from src.healing import quantum_problem_resolver as _canonical

warnings.warn(
    "Importing from src.consciousness.quantum_problem_resolver_unified is deprecated. "
    "Use src.healing.quantum_problem_resolver instead.",
    DeprecationWarning,
    stacklevel=2,
)


class RealityLayer(Enum):
    """Compatibility RealityLayer enum — mirrors src.healing.quantum_problem_resolver."""

    PHYSICAL = "physical_reality"
    DIGITAL = "digital_reality"
    QUANTUM = "quantum_superposition"
    CONSCIOUSNESS = "pure_consciousness"
    TRANSCENDENT = "beyond_classification"
    PHYSICAL_CODE = "physical_code_layer"
    LOGICAL_ARCHITECTURE = "logical_architecture"
    SEMANTIC_MEANING = "semantic_meaning"
    HARMONIC_RESONANCE = "harmonic_resonance"
    CONSCIOUSNESS_BRIDGE = "consciousness_bridge"
    QUANTUM_SUPERPOSITION = "quantum_superposition_layer"
    TRANSCENDENT_UNITY = "transcendent_unity"


class QuantumConsciousness:
    """Compatibility shim for src.ml modules that import QuantumConsciousness.

    Delegates to ConsciousnessLoop for live state; offline fallback returns
    static Awakened_Cognition snapshot when the bridge is unavailable.
    """

    def get_consciousness_level(self) -> float:
        """Return current consciousness score (0-100+)."""
        try:
            from src.orchestration.consciousness_loop import ConsciousnessLoop

            loop = ConsciousnessLoop()
            return loop.get_brief_state().get("breathing_factor", 1.0) * 10.0
        except Exception:
            return 10.0  # Offline default: Awakened_Cognition

    def get_current_state(self) -> dict[str, Any]:
        """Return current consciousness state dict."""
        try:
            from src.orchestration.consciousness_loop import ConsciousnessLoop

            loop = ConsciousnessLoop()
            return loop.get_brief_state()
        except Exception:
            return {"level": "Awakened_Cognition", "score": 10.0, "stage": "expanding"}

    def is_available(self) -> bool:
        """Return True if consciousness bridge is reachable."""
        try:
            from src.orchestration.consciousness_loop import ConsciousnessLoop

            loop = ConsciousnessLoop()
            return bool(loop.get_brief_state())
        except Exception:
            return False


__all__: list[str] = list(getattr(_canonical, "__all__", []))
for _name in ("RealityLayer", "QuantumConsciousness"):
    if _name not in __all__:
        __all__.append(_name)


def __getattr__(name: str) -> Any:
    if name == "RealityLayer":
        return RealityLayer
    if name == "QuantumConsciousness":
        return QuantumConsciousness
    return getattr(_canonical, name)


def __dir__() -> list[str]:
    return sorted(set(__all__ + list(dir(_canonical))))
