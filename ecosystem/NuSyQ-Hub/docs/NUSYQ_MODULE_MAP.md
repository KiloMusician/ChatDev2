# NuSyQ-Hub Module Map (Live Index)

## Orchestration Layer

**File:** `src/orchestration/multi_ai_orchestrator.py`

| Function/Class           | Signature                                          | Usage                                    |
| ------------------------ | -------------------------------------------------- | ---------------------------------------- |
| `MultiAIOrchestrator`    | `class __init__(config_path=None)`                 | Main coordinator for all AI tasks        |
| `orchestrate()`          | `def orchestrate(task: TaskRequest) -> TaskResult` | Route task to appropriate AI backend     |
| `get_available_models()` | `def get_available_models() -> List[Model]`        | List all registered Ollama/OpenAI models |
| `register_model()`       | `def register_model(name, backend, config)`        | Add new model for routing                |

**Example:**

```python
from src.orchestration.multi_ai_orchestrator import MultiAIOrchestrator, TaskRequest, TaskType

orchestrator = MultiAIOrchestrator()
task = TaskRequest(type=TaskType.CODE_ANALYSIS, payload={"code": "..."})
result = orchestrator.orchestrate(task)
```

---

## Integration Layer

**File:** `src/integration/consciousness_bridge.py`

| Function/Class        | Signature                                   | Usage                                       |
| --------------------- | ------------------------------------------- | ------------------------------------------- |
| `ConsciousnessBridge` | `class __init__()`                          | Enable semantic awareness across AIs        |
| `get_current_state()` | `def get_current_state() -> Dict[str, Any]` | Retrieve current consciousness context      |
| `broadcast_context()` | `def broadcast_context(context: Dict)`      | Share context with all connected AI systems |
| `register_observer()` | `def register_observer(callback)`           | Listen for context changes                  |

**Example:**

```python
from src.integration.consciousness_bridge import ConsciousnessBridge

bridge = ConsciousnessBridge()
state = bridge.get_current_state()
bridge.broadcast_context({"task_id": "xyz", "phase": "analysis"})
```

---

## Healing & Problem Resolution

**File:** `src/healing/quantum_problem_resolver.py`

| Function/Class              | Signature                                                              | Usage                                |
| --------------------------- | ---------------------------------------------------------------------- | ------------------------------------ |
| `QuantumProblemResolver`    | `class __init__()`                                                     | Self-healing error resolution engine |
| `resolve_quantum_problem()` | `async def resolve_quantum_problem(problem: ProblemSignature) -> bool` | Attempt autonomous error fix         |
| `_generate_ai_solutions()`  | `async def _generate_ai_solutions(problem) -> List[Solution]`          | Use AI to brainstorm fixes           |
| `_implement_ai_solution()`  | `async def _implement_ai_solution(problem, solution) -> bool`          | Apply AI-suggested fix               |

**Example:**

```python
from src.healing.quantum_problem_resolver import QuantumProblemResolver, ProblemSignature

resolver = QuantumProblemResolver()
problem = ProblemSignature(problem_id="err_001", quantum_state="SUPERPOSITION", ...)
success = await resolver.resolve_quantum_problem(problem)
```

---

## AI Coordination

**File:** `src/ai/ai_coordinator.py`

| Class           | Method                                                       | Usage                                                   |
| --------------- | ------------------------------------------------------------ | ------------------------------------------------------- |
| `AICoordinator` | `__init__()`                                                 | Initialize LLM registry and provider routing            |
|                 | `process_chatdev_task(request: TaskRequest) -> TaskResponse` | Route ChatDev tasks with Ollama/OpenAI/Copilot fallback |
| `LLMRegistry`   | `register(name: str, provider: Provider)`                    | Add new LLM provider to orchestration                   |
|                 | `available() -> Dict[str, Provider]`                         | Get all available AI providers                          |

**Example:**

```python
from src.ai.ai_coordinator import AICoordinator, TaskRequest, TaskResponse

coordinator = AICoordinator()
request = TaskRequest(content="Generate code", context={"cultivate_system": True})
response = await coordinator.process_chatdev_task(request)
if response.error:
    print(f"Task failed: {response.error}")
```

---

## Timeout Configuration (Environment-Driven)

**File:** `src/utils/timeout_config.py`

| Function             | Signature                                                                | Usage                                      |
| -------------------- | ------------------------------------------------------------------------ | ------------------------------------------ |
| `get_timeout()`      | `def get_timeout(service: str, default: int=30) -> int`                  | Get timeout for service from env or config |
| `get_http_timeout()` | `def get_http_timeout(service: str, default: int=10) -> Tuple[int, int]` | Get (connect, read) timeouts               |

**Example:**

```python
from src.utils.timeout_config import get_timeout, get_http_timeout

ollama_timeout = get_timeout("OLLAMA", default=5)
http_conn, http_read = get_http_timeout("OPENAI", default=15)
```

---

## Logging (Structured)

**File:** `src/LOGGING/modular_logging_system.py`

| Function      | Signature                                                                      | Usage                      |
| ------------- | ------------------------------------------------------------------------------ | -------------------------- |
| `log_info()`  | `def log_info(component: str, message: str, **kwargs)`                         | Info-level structured log  |
| `log_error()` | `def log_error(component: str, message: str, error: Exception=None, **kwargs)` | Error-level with traceback |
| `log_debug()` | `def log_debug(component: str, message: str, **kwargs)`                        | Debug-level structured log |

**Example:**

```python
from src.LOGGING.modular_logging_system import log_info, log_error

log_info("MyComponent", "Task started", task_id="xyz")
try:
    ...
except Exception as e:
    log_error("MyComponent", "Task failed", error=e, task_id="xyz")
```

---

## ChatDev Integration

**File:** `src/ai/ollama_chatdev_integrator.py`

| Class                             | Method                    | Usage                               |
| --------------------------------- | ------------------------- | ----------------------------------- |
| `EnhancedOllamaChatDevIntegrator` | `__init__()`              | Bridge local Ollama ↔ ChatDev       |
|                                   | `check_systems()`         | Verify Ollama + OpenAI availability |
|                                   | `get_ollama_models()`     | List available Ollama models        |
|                                   | `select_model_for_task()` | Choose model by task type           |

**Example:**

```python
from src.ai.ollama_chatdev_integrator import EnhancedOllamaChatDevIntegrator

integrator = EnhancedOllamaChatDevIntegrator()
integrator.check_systems()
models = integrator.get_ollama_models()
model_choice = integrator.select_model_for_task("code_generation")
```

---

## Configuration Management

**File:** `src/core/config_manager.py` (also `config/secrets.json`,
`nusyq.manifest.yaml`)

| Concept             | Location                            | Purpose                                                  |
| ------------------- | ----------------------------------- | -------------------------------------------------------- |
| API Keys, tokens    | `config/secrets.json`               | Encrypted/placeholder secrets (never commit real values) |
| Feature Flags       | `config/feature_flags.json`         | Toggle experimental features                             |
| Progress Tracking   | `config/ZETA_PROGRESS_TRACKER.json` | Development milestone checklist                          |
| Multi-repo Manifest | `nusyq.manifest.yaml` (NuSyQ root)  | Coordinate across NuSyQ-Hub, SimulatedVerse, NuSyQ       |
| Knowledge Base      | `knowledge-base.yaml` (NuSyQ root)  | Persistent session logs, learning                        |

---

## How to Add New Public APIs

1. **Add function/method** to appropriate module (above).
2. **Update this file** with signature, usage example, location.
3. **Add docstring** to function (Google-style).
4. **Add tests** in `tests/` (required).
5. **Document** in relevant `docs/*.md` file.

**Do not create parallel modules; extend existing ones via config flags or new
methods.**

---

## Anti-Patterns (Avoid)

❌ New top-level module without discussion  
❌ Direct print/logging instead of `log_*` functions  
❌ Hard-coded timeouts instead of `get_timeout()`  
❌ Duplicate orchestration logic instead of using `MultiAIOrchestrator`  
❌ Isolated error handling instead of routing to `QuantumProblemResolver`

---

Last updated: 2025-10-20
