"""Legacy import redirect - Use src.healing.quantum_problem_resolver instead.

This file exists for backward compatibility with legacy code that imported
from src.quantum.quantum_problem_resolver. All new code should import
from src.healing.quantum_problem_resolver directly.

Canonical location: src/healing/quantum_problem_resolver.py
Compute implementation: src/quantum/quantum_problem_resolver_compute.py
"""

import warnings

warnings.warn(
    "Importing from src.quantum.quantum_problem_resolver is deprecated. "
    "Use src.healing.quantum_problem_resolver instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.healing import quantum_problem_resolver as _canonical
from src.healing.quantum_problem_resolver import *

__all__ = list(getattr(_canonical, "__all__", []))
