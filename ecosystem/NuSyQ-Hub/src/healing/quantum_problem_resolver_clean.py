"""Legacy import redirect - Use src.healing.quantum_problem_resolver instead.

This file exists for backward compatibility with legacy code that imported
from src.healing.quantum_problem_resolver_clean. All new code should import
from src.healing.quantum_problem_resolver directly.

Consolidated: 2025-12-28
Canonical location: src/healing/quantum_problem_resolver.py

Evolution History:
- Stage 1 (v4.2.0): Base implementation in src/quantum/ (archived)
- Stage 2 (KILO-FOOLISH): Enhanced in src/healing/quantum_problem_resolver.py ← CANONICAL
- Stage 3 (Clean): Refactored in src/healing/quantum_problem_resolver_clean.py ← YOU ARE HERE (deprecated)
- Stage 4-5 (Unified/Transcendent): Experimental evolutions in src/core/ (archived - API incompatible)

This "clean" version was a refactoring of Stage 2 but never saw production use.
The original KILO-FOOLISH version (Stage 2) is canonical due to widespread adoption.

Original implementation archived to:
src/healing/quantum_problem_resolver_clean_ARCHIVE.py

See: src/quantum/QUANTUM_PROBLEM_RESOLVER_EVOLUTION.md
"""

import warnings

warnings.warn(
    "Importing from src.healing.quantum_problem_resolver_clean is deprecated. "
    "Use src.healing.quantum_problem_resolver instead. "
    "See src/quantum/QUANTUM_PROBLEM_RESOLVER_EVOLUTION.md for evolution history.",
    DeprecationWarning,
    stacklevel=2,
)

from src.healing import quantum_problem_resolver as _canonical
from src.healing.quantum_problem_resolver import *

__all__ = list(getattr(_canonical, "__all__", []))
