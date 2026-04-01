# Copilot Primer — NuSyQ-Hub Reuse-First Development

**You are inside a modular Python multi-AI orchestration ecosystem.**

Before proposing code or files:

1. **Prefer editing existing modules** over creating new ones.
2. **Use published APIs** listed in `docs/NUSYQ_MODULE_MAP.md`.
3. New files require explicit discussion in PR or task description.

## Core Contracts

- Configuration-driven behavior (use `config/*.json` and `*.yaml`).
- Pure functions where possible; no ad-hoc globals.
- Tests + docstrings required for any behavior change.
- Use existing orchestration layers; don't duplicate coordination logic.

## Essential Reuse Index

| Module                                       | Purpose                              | Key Functions                                |
| -------------------------------------------- | ------------------------------------ | -------------------------------------------- |
| `src/orchestration/multi_ai_orchestrator.py` | Route tasks to AI backends           | `orchestrate()`, `get_available_models()`    |
| `src/integration/consciousness_bridge.py`    | Semantic awareness across AI systems | `get_current_state()`, `broadcast_context()` |
| `src/healing/quantum_problem_resolver.py`    | Self-healing error resolution        | `resolve_problem()`, `apply_solution()`      |
| `src/ai/ai_coordinator.py`                   | Unified AI task coordination         | `KILOFoolishAICoordinator` class             |
| `src/utils/timeout_config.py`                | Environment-driven timeouts          | `get_timeout()`, `get_http_timeout()`        |
| `src/LOGGING/modular_logging_system.py`      | Structured logging                   | `log_info()`, `log_error()`                  |

## When to Extend vs. Create

**Extend if:**

- Adding a new model type → extend `AICoordinator.register_model()`.
- New error pattern → add handler to
  `QuantumProblemResolver._generate_solutions()`.
- New healing tactic → add method to healing system, register in config.

**Create only if:**

- Completely isolated subsystem (e.g., new research component).
- Explicitly approved in task description.
- Documented in `docs/NUSYQ_MODULE_MAP.md` with rationale.

## Quick Import Pattern

```python
from src.orchestration.multi_ai_orchestrator import MultiAIOrchestrator
from src.integration.consciousness_bridge import ConsciousnessBridge
from src.healing.quantum_problem_resolver import QuantumProblemResolver
from src.utils.timeout_config import get_timeout
from src.LOGGING.modular_logging_system import log_info, log_error
```

This is the "one obvious way" to integrate new features.
