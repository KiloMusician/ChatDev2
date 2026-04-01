# Agent Task Router API Documentation

## Overview

The `AgentTaskRouter` provides a conversational, natural-language orchestration
interface for AI agents (Copilot, Claude) to route tasks to appropriate backend
systems without manual command execution.

**Module**: `src.tools.agent_task_router`  
**Current Coverage**: 41% (Target: 55%+)  
**Primary Entry Points**: `route_task()`, `analyze_system()`, `heal_system()`,
`develop_system()`

---

## Core Data Types

### ConsciousnessHint

Lightweight container for consciousness enrichment metadata.

```python
@dataclass
class ConsciousnessHint:
    summary: str | None = None
    tags: list[str] | None = None
    confidence: float | None = None
```

**Fields:**

- `summary`: Human-readable summary of consciousness enrichment
- `tags`: Semantic tags from consciousness bridge
- `confidence`: Confidence score (0.0-1.0)

**Usage:**

```python
hint = ConsciousnessHint(
    summary="Code analysis context",
    tags=["python", "testing"],
    confidence=0.85
)
```

---

## Type Literals

### TaskType

Valid task types for routing.

```python
TaskType = Literal[
    "analyze",    # Code/system analysis
    "generate",   # Code generation
    "review",     # Code review
    "debug",      # Debugging assistance
    "plan",       # Planning/architecture
    "test",       # Testing
    "document",   # Documentation
]
```

### TargetSystem

AI backend systems available for task routing.

```python
TargetSystem = Literal[
    "auto",             # Orchestrator decides (recommended)
    "ollama",           # Local LLMs (qwen2.5-coder, deepseek-coder-v2, etc.)
    "chatdev",          # Multi-agent development team
    "copilot",          # GitHub Copilot
    "consciousness",    # Consciousness bridge
    "quantum_resolver", # Advanced problem resolution
]
```

---

## Main Class: AgentTaskRouter

### Initialization

```python
def __init__(self, repo_root: Path | None = None) -> None:
    """Initialize task router.

    Args:
        repo_root: Repository root (defaults to NuSyQ-Hub location)

    Attributes:
        self.repo_root: Path - Repository root directory
        self.orchestrator: UnifiedAIOrchestrator - Main orchestration engine
        self.quest_log_path: Path - Quest log for persistent memory
    """
```

**Example:**

```python
router = AgentTaskRouter()  # Uses default NuSyQ-Hub root
# OR
router = AgentTaskRouter(repo_root=Path("/custom/path"))
```

---

## Core Methods

### route_task() - Main Routing Interface

```python
async def route_task(
    self,
    task_type: TaskType,
    description: str,
    context: dict[str, Any],
    target_system: TargetSystem = "auto",
) -> dict[str, Any]:
    """Route task to appropriate AI system.

    Args:
        task_type: Type of task (analyze, generate, review, etc.)
        description: Natural language task description
        context: Additional context (file paths, metadata, etc.)
        target_system: Target AI system (default: auto)

    Returns:
        dict with:
            - status: "submitted" | "completed" | "failed"
            - task_id: Orchestrator task ID (if submitted)
            - result: Task execution results
            - error: Error message (if failed)
            - receipt_path: Path to execution receipt

    Side Effects:
        - Generates receipt in docs/tracing/RECEIPTS/
        - May append to quest_log.jsonl
        - May create consciousness enrichment
    """
```

**Examples:**

```python
# Analyze code with Ollama
result = await router.route_task(
    task_type="analyze",
    description="Analyze this Python module for issues",
    context={"file": "src/tools/agent_task_router.py"},
    target_system="ollama"
)

# Generate project with ChatDev
result = await router.route_task(
    task_type="generate",
    description="Create REST API with JWT authentication",
    context={"tech_stack": ["FastAPI", "SQLAlchemy"]},
    target_system="chatdev"
)

# Auto-route review task
result = await router.route_task(
    task_type="review",
    description="Review security of authentication module",
    context={"file": "src/auth.py", "consciousness_enrich": True},
    target_system="auto"
)
```

**Result Structure:**

```python
{
    "status": "submitted",
    "task_id": "task_20260104_070500_abc123",
    "receipt_path": "docs/tracing/RECEIPTS/analyze_20260104_070500.txt",
    "consciousness_hint": {
        "summary": "Security-focused analysis",
        "tags": ["authentication", "security"],
        "confidence": 0.92
    }
}
```

---

### analyze_system() - System Health Analysis

```python
async def analyze_system(self, target: str | None = None) -> dict[str, Any]:
    """Run comprehensive system health analysis.

    Args:
        target: Optional specific analysis target

    Returns:
        dict with:
            - status: "success" | "failed"
            - summary: Health metrics
                - total_files: int
                - working_files: int
                - broken_files: int
                - health_score: float (0-1)
            - report_path: Path to detailed report
            - error: Error message (if failed)

    Side Effects:
        - Generates health report in state/reports/
        - Scans repository structure
    """
```

**Example:**

```python
result = await router.analyze_system()
print(f"Health: {result['summary']['health_score']:.1%}")
print(f"Broken files: {result['summary']['broken_files']}")
```

**Result:**

```python
{
    "status": "success",
    "summary": {
        "total_files": 555,
        "working_files": 548,
        "broken_files": 7,
        "health_score": 0.987
    },
    "report_path": "state/reports/health_20260104_070600.json"
}
```

---

### heal_system() - Automated System Healing

```python
async def heal_system(
    self,
    auto_confirm: bool = False,
    target: str | None = None
) -> dict[str, Any]:
    """Heal detected system issues.

    Args:
        auto_confirm: If True, apply fixes automatically
        target: Optional specific healing target

    Returns:
        dict with:
            - status: "success" | "failed"
            - actions_taken: list[str] - Healing actions performed
            - report_path: Path to healing report
            - health_report: Post-healing health metrics
            - error: Error message (if failed)

    Side Effects:
        - May modify files (import fixes, path normalization)
        - Generates healing report in state/reports/
        - Updates health state

    Safety:
        - auto_confirm=False: Preview mode (no changes)
        - auto_confirm=True: Applies fixes (use with caution)
    """
```

**Example:**

```python
# Preview healing actions
preview = await router.heal_system(auto_confirm=False)
print(f"Would perform: {len(preview['actions_taken'])} actions")

# Apply healing
result = await router.heal_system(auto_confirm=True)
print(f"Healed: {result['actions_taken']}")
```

**Result:**

```python
{
    "status": "success",
    "actions_taken": [
        "Fixed 3 circular imports",
        "Normalized 5 paths",
        "Resolved 2 missing dependencies"
    ],
    "report_path": "state/reports/healing_20260104_070700.json",
    "health_report": {
        "broken_files": 0,
        "working_files": 555
    }
}
```

---

### develop_system() - Autonomous Development Loop

```python
async def develop_system(
    self,
    max_iterations: int = 3,
    halt_on_error: bool = False
) -> dict[str, Any]:
    """Run autonomous development loop (analyze → heal → capture intent → plan).

    The "cultivation bundle" rewards emergent system intent:
    1. Analyze system health
    2. Heal detected issues
    3. Capture intent events when goals achieved
    4. Plan next safe steps (1-3 items max)

    Args:
        max_iterations: Maximum loop iterations (default 3)
        halt_on_error: Stop on first error vs. continue

    Returns:
        dict with:
            - status: "success" | "failed"
            - iterations: int - Number of iterations completed
            - log_path: Path to development log
            - intent_events: int - Intent events captured
            - quest_wired: int - Events wired to quest log
            - work_queue_updated: dict - Work queue updates
            - session_log: Path to session log
            - results: list[dict] - Iteration details

    Side Effects:
        - Multiple analyze/heal cycles
        - Appends to quest_log.jsonl
        - Generates development reports
        - May modify system (if healing enabled)
    """
```

**Example:**

```python
# Run 3 iterations with halt-on-error
result = await router.develop_system(
    max_iterations=3,
    halt_on_error=True
)

print(f"Completed {result['iterations']} iterations")
print(f"Captured {result['intent_events']} intent events")
print(f"Quest log updated: {result['quest_wired']} entries")
```

**Result:**

```python
{
    "status": "success",
    "iterations": 2,  # Stopped early (healthy state)
    "log_path": "state/reports/develop_system_20260104_070800.json",
    "intent_events": 1,
    "quest_wired": 1,
    "work_queue_updated": {
        "plans_promoted": 3,
        "items": ["Document recovery", "Validate workflows", "Plan experiment"]
    },
    "session_log": "docs/Agent-Sessions/SESSION_20260104.md",
    "results": [...]  # Detailed iteration logs
}
```

---

## Synchronous Helper Functions

### route_analysis_task()

```python
def route_analysis_task(context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Synchronous wrapper for basic analysis tasks.

    Provides stable import surface for CLI/tests that expect synchronous API.

    Args:
        context: Optional context dict with:
            - description: Task description
            - target: Target system

    Returns:
        dict with task results (see route_task())

    Error Handling:
        Falls back to error dict instead of raising exceptions.
    """
```

**Example:**

```python
# Synchronous usage (no async/await needed)
result = route_analysis_task({
    "description": "Analyze workspace health",
    "target": "auto"
})
```

---

## Private Methods (Internal API)

### \_emit_receipt()

Generates execution receipt for traceability.

```python
def _emit_receipt(
    action_id: str,
    inputs: dict[str, Any],
    outputs: list[str],
    status: str,
    exit_code: int,
    next_steps: list[str] | None = None,
) -> Path
```

### \_consciousness_enrich()

Enriches task context with consciousness bridge signals.

```python
async def _consciousness_enrich(
    description: str,
    context: dict[str, Any]
) -> ConsciousnessHint | None
```

### \_route_by_system()

Delegates task to specific AI system.

```python
async def _route_by_system(
    task: OrchestrationTask,
    target_system: TargetSystem
) -> dict[str, Any]
```

### \_capture_intent()

Captures emergent intent events when system achieves health goals.

```python
def _capture_intent(
    broken_count: int,
    iteration_index: int,
    current_state: dict[str, Any],
    heal_log: dict[str, Any],
) -> dict[str, Any] | None
```

### \_build_plan()

Constructs conservative plan based on current system health.

```python
def _build_plan(
    broken_count: int,
    prev_state: dict[str, Any] | None
) -> dict[str, Any]
```

---

## Common Workflows

### 1. Analyze Code with Ollama

```python
router = AgentTaskRouter()
result = await router.route_task(
    task_type="analyze",
    description="Analyze error handling patterns",
    context={"file": "src/main.py"},
    target_system="ollama"
)
```

### 2. Generate Project with ChatDev

```python
result = await router.route_task(
    task_type="generate",
    description="Create a CLI tool for file processing",
    context={
        "language": "Python",
        "features": ["argparse", "logging", "config"]
    },
    target_system="chatdev"
)
```

### 3. Full System Health Cycle

```python
# 1. Analyze
analysis = await router.analyze_system()

# 2. Heal if needed
if analysis["summary"]["broken_files"] > 0:
    healing = await router.heal_system(auto_confirm=True)

# 3. Verify
final_check = await router.analyze_system()
assert final_check["summary"]["broken_files"] == 0
```

### 4. Autonomous Development

```python
# Run autonomous loop
result = await router.develop_system(
    max_iterations=5,
    halt_on_error=False
)

# Check intent capture
print(f"System achieved goals: {result['intent_events']} times")
print(f"Work queue updated with {result['work_queue_updated']['plans_promoted']} tasks")
```

---

## Error Handling

All methods return status dicts instead of raising exceptions:

```python
{
    "status": "failed",
    "error": "Descriptive error message",
    "recommendations": [
        "Verify orchestrator dependencies",
        "Run scripts/start_nusyq.py hygiene"
    ]
}
```

**Best Practice:**

```python
result = await router.route_task(...)
if result["status"] == "failed":
    logger.error(f"Task failed: {result['error']}")
    for rec in result.get("recommendations", []):
        logger.info(f"  - {rec}")
```

---

## Configuration

Router uses these configuration files:

- `config/orchestration_defaults.json` - Orchestrator settings
- `src/Rosetta_Quest_System/quest_log.jsonl` - Quest persistence
- `docs/tracing/RECEIPTS/` - Execution receipts
- `state/reports/` - Analysis/healing reports

**Environment Variables:**

- `NUSYQ_RUN_ID`: Custom run identifier
- `NUSYQ_ECOSYSTEM_EFFICIENCY_FORCE`: Force efficiency hints (0/1)

---

## Testing

### Unit Test Coverage Areas

1. **Initialization** - Router setup, path configuration
2. **Task Routing** - All task types and target systems
3. **Receipt Generation** - Traceability and logging
4. **Consciousness Enrichment** - Context enhancement
5. **File Operations** - JSON write, line append
6. **System Analysis** - Health checking
7. **System Healing** - Auto-fix workflows
8. **Development Loop** - Iteration logic
9. **Intent Capture** - Goal achievement detection
10. **Plan Building** - Next-step generation
11. **Quest Wiring** - Persistent memory integration
12. **Error Handling** - Graceful degradation

### Example Test

```python
@pytest.mark.asyncio
async def test_route_task_analyze(tmp_path):
    router = AgentTaskRouter(repo_root=tmp_path)
    result = await router.route_task(
        task_type="analyze",
        description="Test analysis",
        context={},
        target_system="auto"
    )
    assert result["status"] in ["submitted", "completed", "failed"]
    assert "task_id" in result or "error" in result
```

---

## API Contract Summary

| Method                    | Async | Returns    | Side Effects         | Idempotent |
| ------------------------- | ----- | ---------- | -------------------- | ---------- |
| `__init__()`              | No    | None       | Creates orchestrator | Yes        |
| `route_task()`            | Yes   | dict       | Receipt, quest log   | No         |
| `analyze_system()`        | Yes   | dict       | Report generation    | Yes        |
| `heal_system()`           | Yes   | dict       | File modifications   | No         |
| `develop_system()`        | Yes   | dict       | Multiple cycles      | No         |
| `_emit_receipt()`         | No    | Path       | File write           | No         |
| `_consciousness_enrich()` | Yes   | Hint\|None | Consciousness state  | Yes        |
| `_capture_intent()`       | No    | dict\|None | None                 | Yes        |
| `_build_plan()`           | No    | dict       | None                 | Yes        |

---

## Version History

- **v1.0** (2025-12-24): Initial orchestration interface
- **v1.1** (2026-01-03): Added cultivation bundle (intent + plan)
- **v1.2** (2026-01-04): Enhanced API documentation, test coverage

---

## Related Documentation

- [AGENTS.md](../../AGENTS.md) - Agent navigation protocol
- [copilot-instructions.md](../../.github/copilot-instructions.md) - Copilot
  integration
- [unified_ai_orchestrator.py](../orchestration/unified_ai_orchestrator.py) -
  Orchestrator API
- [quest_log.jsonl](../Rosetta_Quest_System/quest_log.jsonl) - Quest format

---

**Last Updated**: 2026-01-04  
**Maintainer**: KiloMusician  
**Test Coverage**: 41% → Target: 55%+
