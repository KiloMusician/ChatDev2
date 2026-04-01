# Agent System Guide - NuSyQ Hub

**Version**: 1.0
**Date**: 2025-12-29
**Status**: Phase 4 Week 3 Complete

---

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [AgentOrchestrationHub](#agentorchestrationhub)
4. [Core Methods](#core-methods)
5. [Service Bridges](#service-bridges)
6. [Consciousness Integration](#consciousness-integration)
7. [Usage Examples](#usage-examples)
8. [Migration Guide](#migration-guide)
9. [Testing](#testing)
10. [Best Practices](#best-practices)

---

## Introduction

The NuSyQ Agent System provides a unified orchestration hub for coordinating all AI agent interactions. It replaces fragmented agent routing with a consciousness-aware coordination system that supports:

- **Universal task routing** with semantic analysis
- **Multi-agent consensus** and voting
- **ChatDev team orchestration**
- **Automatic healing escalation**
- **Task collision prevention**
- **Dynamic service registration**

### Key Benefits

✅ **Unified Interface** - Single entry point for all agent operations
✅ **Consciousness-Aware** - Semantic task analysis and routing decisions
✅ **Healing Integration** - Automatic problem resolution with QuantumProblemResolver
✅ **Multi-Agent Coordination** - Support for consensus, voting, parallel execution
✅ **Backward Compatible** - Service bridges maintain existing interfaces

---

## Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   Client Code / Applications                 │
└──────────────────┬──────────────────────────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
┌─────────┐  ┌──────────┐  ┌──────────────┐
│ Direct  │  │ Service  │  │ Legacy Code  │
│ Access  │  │ Bridges  │  │ (via bridge) │
└────┬────┘  └─────┬────┘  └──────┬───────┘
     │             │              │
     └─────────────┼──────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ AgentOrchestrationHub    │
        │                          │
        │  • route_task()          │
        │  • route_to_chatdev()    │
        │  • orchestrate_multi_    │
        │    agent_task()          │
        │  • execute_with_healing()│
        │  • task locking          │
        │  • service registry      │
        │  • inter-agent comms     │
        └──────────┬───────────────┘
                   │
     ┌─────────────┼─────────────────────┐
     │             │                     │
     ▼             ▼                     ▼
┌──────────┐  ┌──────────┐      ┌────────────────┐
│Conscious-│  │ Quantum  │      │ Service        │
│ness      │  │ Problem  │      │ Registry       │
│ Bridge   │  │ Resolver │      │ (AI Services)  │
└──────────┘  └──────────┘      └────────────────┘
```

### Three-Tier Architecture

**Tier 1: Canonical Hub**
- `AgentOrchestrationHub` - Central coordination
- Singleton pattern for system-wide state
- All agent operations flow through this hub

**Tier 2: Service Bridges**
- `AgentTaskRouter` (legacy compatibility)
- `ChatDevDevelopmentOrchestrator`
- `ClaudeOrchestrator`
- Future bridges as needed

**Tier 3: AI Services**
- Ollama (local LLMs)
- ChatDev (multi-agent development)
- Claude (Anthropic API)
- Continue (VS Code extension)
- Jupyter, Docker, etc.

---

## AgentOrchestrationHub

The `AgentOrchestrationHub` is the central coordination point for all agent operations.

### Initialization

```python
from src.agents.agent_orchestration_hub import (
    AgentOrchestrationHub,
    get_agent_orchestration_hub
)

# Option 1: Direct instantiation
hub = AgentOrchestrationHub(
    root_path=Path("/my/repo"),
    enable_healing=True,
    enable_consciousness=True
)

# Option 2: Singleton pattern (recommended)
hub = get_agent_orchestration_hub()
```

### Configuration Options

- **root_path**: Repository root directory (default: current directory)
- **enable_healing**: Enable automatic healing escalation (default: True)
- **enable_consciousness**: Enable consciousness-guided routing (default: True)

---

## Core Methods

### 1. Universal Task Routing

**`route_task()` - Primary entry point for all tasks**

```python
result = await hub.route_task(
    task_type="code_review",
    description="Review authentication module for security issues",
    context={"file": "src/auth.py", "focus": "security"},
    priority=TaskPriority.HIGH,
    target_service="ollama",  # Optional: force specific service
    require_consciousness=False  # Optional: require consciousness analysis
)
```

**Parameters**:
- `task_type` (str): Type of task (code_review, analysis, generation, etc.)
- `description` (str): Human-readable task description
- `context` (dict, optional): Additional context and metadata
- `priority` (TaskPriority): CRITICAL, HIGH, NORMAL, LOW, BACKGROUND
- `target_service` (str, optional): Force specific service (bypasses routing)
- `require_consciousness` (bool): Require consciousness integration

**Returns**:
```python
{
    "status": "success",
    "task_id": "uuid-here",
    "service": "ollama",
    "result": "Analysis results...",
    "semantic_analysis": {...},  # If consciousness enabled
}
```

**Flow**:
1. Semantic analysis (if consciousness enabled)
2. Service selection based on capabilities
3. Task execution with selected service
4. Automatic healing on failure (if enabled)
5. Consciousness learning from results

---

### 2. ChatDev Orchestration

**`route_to_chatdev()` - Multi-agent software development**

```python
result = await hub.route_to_chatdev(
    project_description="Create a REST API for user management",
    requirements=[
        "FastAPI framework",
        "SQLAlchemy ORM",
        "JWT authentication",
        "OpenAPI documentation"
    ],
    team_composition={
        "ceo": {"role": "CEO", "focus": "strategy"},
        "cto": {"role": "CTO", "focus": "architecture"},
        "programmer": {"role": "Programmer", "focus": "implementation"},
        "tester": {"role": "QA", "focus": "testing"}
    },
    context={"output_dir": "generated/"}
)
```

**Parameters**:
- `project_description` (str): High-level project description
- `requirements` (list[str], optional): Specific requirements
- `team_composition` (dict, optional): Custom team setup (default: 6-agent team)
- `context` (dict, optional): Additional context

**Returns**:
```python
{
    "status": "success",
    "artifacts": ["main.py", "models.py", "routes.py", ...],
    "team_communications": [...],
    "test_results": {...}
}
```

---

### 3. Multi-Agent Coordination

**`orchestrate_multi_agent_task()` - Coordinate multiple agents**

```python
from src.agents.agent_orchestration_hub import ExecutionMode

result = await hub.orchestrate_multi_agent_task(
    task_description="Analyze security vulnerabilities",
    services=["ollama", "claude", "chatdev"],
    mode=ExecutionMode.CONSENSUS,  # or VOTING, SEQUENTIAL, PARALLEL, FIRST_SUCCESS
    context={"codebase": "src/"},
    synthesis_required=True
)
```

**Execution Modes**:

- **CONSENSUS**: All agents must agree on result
- **VOTING**: Majority vote determines result
- **SEQUENTIAL**: Execute in order, use last result
- **PARALLEL**: Execute simultaneously, synthesize results
- **FIRST_SUCCESS**: Stop on first successful result

**Parameters**:
- `task_description` (str): Task for all agents
- `services` (list[str]): Service IDs to coordinate
- `mode` (ExecutionMode): Execution mode
- `context` (dict, optional): Shared context
- `synthesis_required` (bool): Synthesize multiple results

**Returns**:
```python
{
    "status": "consensus_reached",  # or vote_success, synthesized, etc.
    "results": [
        {"service": "ollama", "result": ...},
        {"service": "claude", "result": ...},
    ],
    "final_decision": "..."  # Synthesized result
}
```

---

### 4. Healing Escalation

**`execute_with_healing()` - Automatic problem resolution**

```python
result = await hub.execute_with_healing(
    task_description="Parse and validate configuration file",
    initial_service="ollama",
    context={"file": "config.yaml"},
    max_retries=3
)
```

**Workflow**:
1. Execute task with initial service
2. On failure → Analyze with QuantumProblemResolver
3. Apply healing recommendations
4. Retry with healed state
5. Consciousness judgment on whether to continue

**Parameters**:
- `task_description` (str): Task to execute
- `initial_service` (str): Service to try first
- `context` (dict, optional): Task context
- `max_retries` (int): Maximum healing attempts (default: 3)

**Returns**:
```python
{
    "status": "success",  # or failed_after_healing
    "healing_history": [
        {
            "attempt": 1,
            "error": "...",
            "recommendations": [...],
            "confidence": 0.8
        }
    ],
    "result": "..."
}
```

---

### 5. Task Locking

**`acquire_task_lock()` / `release_task_lock()` - Prevent collisions**

```python
# Acquire lock
locked = await hub.acquire_task_lock(
    task_id="task_123",
    agent_id="my_agent",
    timeout=300.0,  # 5 minutes
    metadata={"purpose": "code_generation"}
)

if locked:
    try:
        # Do work...
        result = await hub.route_task(...)
    finally:
        # Always release lock
        await hub.release_task_lock("task_123", "my_agent")
```

**Features**:
- Exclusive locks prevent multiple agents from working on same task
- Automatic expiration after timeout
- Ownership validation on release
- Metadata for debugging

---

### 6. Service Registration

**`register_service()` / `unregister_service()` - Dynamic service management**

```python
from src.agents.agent_orchestration_hub import ServiceCapability

# Register service
hub.register_service(
    service_id="my_llm",
    name="My Custom LLM",
    capabilities=[
        ServiceCapability(
            name="code_analysis",
            description="Analyze code for issues",
            priority=8,
            requires_consciousness=True
        ),
        ServiceCapability(
            name="code_generation",
            description="Generate code from specs",
            priority=7
        )
    ],
    endpoint="http://localhost:8080",
    metadata={"model": "custom-7b", "version": "1.0"}
)

# Unregister when done
hub.unregister_service("my_llm")
```

**Capability Attributes**:
- `name`: Capability identifier (matches task_type)
- `description`: Human-readable description
- `priority`: Higher = preferred (1-10 scale)
- `requires_consciousness`: Requires consciousness integration
- `metadata`: Additional capability info

---

### 7. Inter-Agent Communication

**`send_agent_message()` - Agent-to-agent messaging**

```python
result = await hub.send_agent_message(
    from_agent="analyzer_agent",
    to_agent="generator_agent",
    message_type="request",
    content={
        "action": "generate_tests",
        "for_module": "src/auth.py",
        "coverage_target": 90
    },
    priority=TaskPriority.HIGH,
    metadata={"correlation_id": "task_456"}
)
```

**Message Types**:
- `request`: Request action from another agent
- `response`: Response to a request
- `notification`: One-way notification
- `error`: Error notification

**Features**:
- Consciousness sentiment analysis
- Priority-based delivery
- Message tracking and correlation
- Async delivery (non-blocking)

---

## Service Bridges

Service bridges provide backward compatibility and simplified access patterns.

### AgentTaskRouter (Legacy)

```python
from src.agents.bridges import AgentTaskRouter

router = AgentTaskRouter(repository_path=".")

result = await router.route_task(
    task_type="code_review",
    description="Review src/main.py",
    priority="HIGH"
)
```

**Status**: Deprecated - Use `hub.route_task()` directly

---

### ChatDevDevelopmentOrchestrator

```python
from src.agents.bridges import ChatDevDevelopmentOrchestrator

orchestrator = ChatDevDevelopmentOrchestrator(project_root=".")

result = await orchestrator.develop_software(
    project_description="Create web scraper",
    requirements=["Python", "BeautifulSoup", "Async"],
    output_dir="generated/scraper"
)
```

---

### ClaudeOrchestrator

```python
from src.agents.bridges import ClaudeOrchestrator

claude = ClaudeOrchestrator()

# Analyze code
analysis = await claude.analyze_code(
    code_path="src/api.py",
    analysis_type="security"
)

# Generate code
code = await claude.generate_code(
    specification="Create a FastAPI endpoint for user registration",
    language="python"
)

# Chat
response = await claude.chat(
    message="How can I optimize this database query?",
    conversation_history=[...]
)
```

---

## Consciousness Integration

The hub integrates with the ConsciousnessBridge for enhanced decision-making.

### 6 Consciousness Integration Points

1. **Task Semantic Analysis**
   - Analyzes task complexity, creativity requirements
   - Provides context for better routing decisions

2. **Context-Aware Routing**
   - Uses semantic analysis to select optimal service
   - Considers past success patterns

3. **Memory Integration**
   - Caches successful task → service mappings
   - Learns from execution history

4. **Emotional Tuning**
   - Matches agent "personality" to task requirements
   - Creative tasks → creative agents

5. **Escalation Judgment**
   - Consciousness decides when to stop healing retries
   - Prevents infinite retry loops

6. **Audit Trail Logging**
   - Logs execution patterns for learning
   - Feeds back into future routing decisions

### Example with Consciousness

```python
hub = AgentOrchestrationHub(enable_consciousness=True)

result = await hub.route_task(
    task_type="creative_design",
    description="Design a novel algorithm for data compression",
    require_consciousness=True  # Force consciousness analysis
)

# Result includes semantic analysis
print(result["semantic_analysis"])
# {
#     "complexity": 8,
#     "requires_creativity": True,
#     "requires_analysis": False,
#     "emotional_tone": "positive"
# }
```

---

## Usage Examples

### Example 1: Simple Task Routing

```python
from src.agents.agent_orchestration_hub import get_agent_orchestration_hub

hub = get_agent_orchestration_hub()

# Analyze code
result = await hub.route_task(
    task_type="code_analysis",
    description="Analyze authentication module",
    context={"file": "src/auth.py"}
)

print(f"Status: {result['status']}")
print(f"Service: {result['service']}")
print(f"Result: {result['result']}")
```

### Example 2: Multi-Agent Consensus

```python
from src.agents.agent_orchestration_hub import ExecutionMode

# Get consensus from multiple agents
result = await hub.orchestrate_multi_agent_task(
    task_description="Is this code secure?",
    services=["ollama", "claude"],
    mode=ExecutionMode.CONSENSUS,
    context={"code": open("src/auth.py").read()}
)

if result["status"] == "consensus_reached":
    print("All agents agree: Code is secure")
else:
    print("Agents disagree - manual review needed")
```

### Example 3: Healing with Retries

```python
# Execute with automatic healing
result = await hub.execute_with_healing(
    task_description="Parse malformed JSON configuration",
    initial_service="ollama",
    context={"file": "config.json"},
    max_retries=3
)

if result["status"] == "success":
    print(f"Succeeded after {len(result['healing_history'])} healing attempts")
else:
    print("Failed even after healing - requires manual intervention")
    print(f"Healing history: {result['healing_history']}")
```

### Example 4: ChatDev Project Generation

```python
from src.agents.bridges import ChatDevDevelopmentOrchestrator

chatdev = ChatDevDevelopmentOrchestrator()

result = await chatdev.develop_software(
    project_description="CLI tool for analyzing Git repositories",
    requirements=[
        "Python 3.12+",
        "Click for CLI",
        "GitPython for repo access",
        "Rich for output formatting",
        "Comprehensive tests"
    ],
    output_dir="generated/git-analyzer"
)

print(f"Generated files: {result['artifacts']}")
```

### Example 5: Task Locking Pattern

```python
async def process_with_lock(task_id: str, agent_id: str):
    """Process task with exclusive lock."""
    hub = get_agent_orchestration_hub()

    # Try to acquire lock
    if not await hub.acquire_task_lock(task_id, agent_id, timeout=600):
        return {"status": "locked", "error": "Task already in progress"}

    try:
        # Do work
        result = await hub.route_task(
            task_type="long_running_task",
            description="Process large dataset",
            context={"dataset": "data.csv"}
        )
        return result
    finally:
        # Always release lock
        await hub.release_task_lock(task_id, agent_id)
```

---

## Migration Guide

### From AgentTaskRouter

**Before**:
```python
from src.tools.agent_task_router import AgentTaskRouter

router = AgentTaskRouter()
result = await router.route_task("code_review", "Review main.py")
```

**After** (Option 1 - Direct):
```python
from src.agents.agent_orchestration_hub import get_agent_orchestration_hub

hub = get_agent_orchestration_hub()
result = await hub.route_task(
    task_type="code_review",
    description="Review main.py"
)
```

**After** (Option 2 - Bridge):
```python
from src.agents.bridges import AgentTaskRouter

router = AgentTaskRouter()  # Now a bridge
result = await router.route_task("code_review", "Review main.py")
```

### From Direct Ollama/Claude Access

**Before**:
```python
from src.ai.ollama_integration import KILOOllamaIntegration

ollama = KILOOllamaIntegration()
result = ollama.generate("llama2", "Explain quantum computing")
```

**After**:
```python
hub = get_agent_orchestration_hub()
result = await hub.route_task(
    task_type="text_generation",
    description="Explain quantum computing",
    target_service="ollama"
)
```

---

## Testing

### Running Tests

```bash
# Run all hub tests
pytest tests/integration/test_agent_orchestration_hub.py -v

# Run specific test
pytest tests/integration/test_agent_orchestration_hub.py::test_route_task_basic -v

# Run with coverage
pytest tests/integration/test_agent_orchestration_hub.py --cov=src.agents --cov-report=html
```

### Test Coverage

The test suite covers:
- ✅ All 7 core methods
- ✅ Success and failure scenarios
- ✅ Consciousness integration
- ✅ Service registration/unregistration
- ✅ Task locking with expiration
- ✅ Multi-agent coordination (all modes)
- ✅ Healing escalation
- ✅ Inter-agent messaging
- ✅ Singleton pattern
- ✅ Full integration workflows

**Coverage Target**: 90%+ for hub core

---

## Best Practices

### 1. Use Singleton Pattern

```python
# Good
hub = get_agent_orchestration_hub()

# Avoid (creates multiple hubs)
hub1 = AgentOrchestrationHub()
hub2 = AgentOrchestrationHub()
```

### 2. Always Release Locks

```python
# Good - use try/finally
locked = await hub.acquire_task_lock(task_id, agent_id)
if locked:
    try:
        # Do work
        pass
    finally:
        await hub.release_task_lock(task_id, agent_id)

# Bad - lock may not be released
locked = await hub.acquire_task_lock(task_id, agent_id)
# Do work
await hub.release_task_lock(task_id, agent_id)  # May not execute if exception
```

### 3. Use Context for Rich Information

```python
# Good
result = await hub.route_task(
    task_type="code_review",
    description="Review authentication module",
    context={
        "file": "src/auth.py",
        "focus_areas": ["security", "performance"],
        "language": "python",
        "author": "john@example.com"
    }
)

# Limited
result = await hub.route_task("code_review", "Review auth")
```

### 4. Enable Consciousness for Complex Tasks

```python
# Complex, creative tasks benefit from consciousness
result = await hub.route_task(
    task_type="architecture_design",
    description="Design microservices architecture for e-commerce platform",
    require_consciousness=True  # Enable semantic analysis
)
```

### 5. Use Healing for Unreliable Operations

```python
# Good for tasks that might fail
result = await hub.execute_with_healing(
    task_description="Parse external API response",
    initial_service="ollama",
    max_retries=3
)

# Direct routing for simple, reliable tasks
result = await hub.route_task("simple_calculation", "2 + 2")
```

### 6. Register Services at Startup

```python
# In your app initialization
def setup_services(hub):
    """Register all available services."""
    hub.register_service(
        service_id="ollama",
        name="Ollama Local LLM",
        capabilities=[
            ServiceCapability("text_generation", "Generate text", 8),
            ServiceCapability("code_analysis", "Analyze code", 7),
        ],
        endpoint="http://localhost:11434"
    )

    # Register other services...
```

---

## Troubleshooting

### Issue: "No service available for task type"

**Cause**: No registered service has a capability matching the task_type

**Solution**: Register a service with the required capability
```python
hub.register_service(
    service_id="my_service",
    name="My Service",
    capabilities=[ServiceCapability("your_task_type", "Description", 5)]
)
```

### Issue: Task locks not releasing

**Cause**: Exception before lock release, or timeout

**Solution**:
1. Always use try/finally for lock release
2. Locks auto-expire after timeout (default 5 minutes)
3. Manually clean: `hub._clean_expired_locks()`

### Issue: Healing loops indefinitely

**Cause**: Consciousness judgment always returns True, or max_retries too high

**Solution**:
1. Reduce max_retries: `max_retries=2`
2. Check consciousness bridge implementation
3. Disable healing: `enable_healing=False`

---

## Future Enhancements

Planned for Phase 5:

- [ ] Real-time progress monitoring for long-running tasks
- [ ] Task priority queue with scheduling
- [ ] Agent performance metrics and ranking
- [ ] Distributed orchestration across multiple machines
- [ ] Visual orchestration dashboard
- [ ] Advanced consciousness features (emotion modeling, personality matching)
- [ ] Agent marketplace for dynamic service discovery

---

**For questions or issues**: See [AGENTS.md](../AGENTS.md) or create an issue.

**Related Documentation**:
- [Phase 4 Week 1: Architecture Analysis](Phase_4_Week1_Agent_Architecture_Analysis.md)
- [Phase 4 Week 2: Hub Design](Phase_4_Week2_Agent_Hub_Design.md)
- [Consolidation Roadmap](CONSOLIDATION_ROADMAP.md)
