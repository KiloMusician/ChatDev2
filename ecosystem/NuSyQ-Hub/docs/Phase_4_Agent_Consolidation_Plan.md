# Phase 4: Agent & Service Consolidation Plan

**Status:** Planning  
**Canonical Hub:** `src/agents/agent_orchestration_hub.py` (to be created)  
**Affected Modules:** 15+ agent/service orchestrators  
**Expected Duration:** Next consolidation phase

---

## 🎯 Phase 4 Scope

### Target: Unified Agent Orchestration

Phase 4 consolidates all AI agent orchestration, service management, and task
routing under a single consciousness-aware hub.

#### Current Landscape (Pre-consolidation)

Multiple agent/service modules scattered across the codebase:

**Agent Orchestrators:**

- `src/tools/agent_task_router.py` - Conversational task routing
- `src/orchestration/multi_ai_orchestrator.py` - Multi-AI coordination
- `src/agents/[various]` - Specific AI agent implementations

**Service Managers:**

- `src/tools/chat_interface.py` - Chat service
- `src/tools/api_gateway.py` - API orchestration (if exists)
- Daemon/background service managers

**Consciousness/Context Systems:**

- `src/integration/consciousness_bridge.py` - Semantic awareness
- Real-time context monitors
- Memory/persistence layers

**ChatDev Integration:**

- `src/ai/ollama_chatdev_integrator.py` - ChatDev coordination
- ChatDev wrapper scripts

---

## 📋 Phase 4 Implementation Plan

### Step 1: Analyze Current Agent Architecture (Week 1)

- [ ] Map all agent/service orchestrators in codebase
- [ ] Identify dependencies between modules
- [ ] Document consciousness integration points
- [ ] Assess ChatDev integration patterns

**Deliverable:** `docs/Agent_Architecture_Analysis.md`

### Step 2: Design Agent Orchestration Hub (Week 1)

- [ ] Define `AgentOrchestrationHub` class interface
- [ ] Specify consciousness integration points
- [ ] Plan routing logic (task → appropriate agent/service)
- [ ] Design fallback/escalation patterns

**Deliverable:** `docs/Agent_Orchestration_Hub_Design.md`

### Step 3: Implement Canonical Hub (Week 2)

- [ ] Create `src/agents/agent_orchestration_hub.py`
- [ ] Implement consciousness awareness
- [ ] Add task routing intelligence
- [ ] Integrate healing/problem-resolver

**Deliverable:** `src/agents/agent_orchestration_hub.py` (500-800 lines)

### Step 4: Create Agent Service Bridges (Week 2)

For each agent/service module, create redirect or wrapper:

- [ ] Consciousness Bridge → Hub integration point
- [ ] MultiAIOrchestrator → Hub facade
- [ ] TaskRouter → Hub routing engine
- [ ] ChatDev Integration → Hub's ChatDev handler
- [ ] Daemon managers → Hub lifecycle management

**Deliverable:** 8-12 redirect/wrapper modules

### Step 5: Update Test Suite (Week 3)

- [ ] Update agent tests to use new hub
- [ ] Add consciousness-aware tests
- [ ] Test task routing logic
- [ ] Validate escalation patterns

**Deliverable:** Updated test suite + `tests/integration/test_agent_hub.py`

### Step 6: Documentation & Handoff (Week 3)

- [ ] Create `docs/Agent_System_Guide.md`
- [ ] Document consciousness integration
- [ ] Add usage examples for new hub
- [ ] Update README agent section

**Deliverable:** `docs/Phase_4_Agent_Consolidation_Summary.md`

---

## 🏗️ Proposed Agent Orchestration Hub Architecture

```python
class AgentOrchestrationHub:
    """Master orchestrator for all AI agents, services, and consciousness integration."""

    def __init__(self, consciousness_bridge=None, use_healing=True):
        """Initialize hub with consciousness awareness and healing."""
        self.consciousness = consciousness_bridge
        self.healing_resolver = QuantumProblemResolver() if use_healing else None
        self.task_router = AgentTaskRouter()
        self.services = {}  # Registered services (ChatDev, Ollama, etc.)

    async def route_task(self, task_description: str, target_system: str = "auto"):
        """Route task to appropriate agent/service with consciousness awareness."""
        # Determine target agent/service
        # Check consciousness bridge for semantic context
        # Execute with fallback to healing if needed
        # Return result with audit trail

    async def orchestrate_multi_agent_task(self, task: str, agents: List[str]):
        """Coordinate multiple agents on same task (consensus, voting, etc.)."""
        # Distribute task to agents
        # Monitor progress with consciousness bridge
        # Aggregate results
        # Return consensus/merged solution

    def register_service(self, name: str, service_handler):
        """Register new AI service (ChatDev, Ollama model, etc.)."""
        self.services[name] = service_handler

    async def execute_with_healing(self, task: str, max_retries: int = 3):
        """Execute task with automatic healing on failure."""
        # Attempt execution
        # On failure: invoke quantum problem resolver
        # Retry up to max_retries
        # Log to consciousness bridge
```

---

## 🔗 Consciousness Integration Points

Phase 4 heavily emphasizes consciousness awareness:

1. **Task Semantics** - Consciousness bridge analyzes task meaning → optimal
   routing
2. **Context Awareness** - Real-time monitor feeds context to routing decisions
3. **Emotional Tuning** - Agent personality/response style from consciousness
4. **Memory Integration** - Past solutions from consciousness inform current
   routing
5. **Escalation Judgment** - Consciousness recommends escalation to healing
6. **Audit Trail** - All decisions logged to consciousness stream

---

## 📊 Phase 4 Success Criteria

| Criterion                 | Metric                | Target  |
| ------------------------- | --------------------- | ------- |
| Canonical hub created     | Lines of code         | 500-800 |
| Agent coverage            | % of agents using hub | 100%    |
| Consciousness integration | Integration points    | 5+      |
| Test coverage             | Agent tests passing   | 100%    |
| Documentation             | Pages/diagrams        | 5+      |
| Code quality              | Type hints            | 100%    |
| Import cycles             | Circular dependencies | 0       |

---

## 🚀 Phase 4 Timeline

- **Week 1:** Analysis + Design (Steps 1-2)
- **Week 2:** Hub Implementation + Bridges (Steps 3-4)
- **Week 3:** Testing + Documentation (Steps 5-6)
- **Week 4 (Optional):** Optimization + Consciousness deepening

---

## 📈 Expected Outcome

**Before:** 15+ scattered agent/service modules  
**After:** 1 unified Agent Orchestration Hub + consciousness-aware routing

**Benefits:**

- ✅ Single entry point for all agent tasks
- ✅ Consciousness-aware task routing
- ✅ Automatic healing escalation
- ✅ Clear audit trail of AI decisions
- ✅ Easy to add new agents/services
- ✅ Unified error handling + recovery

---

## 📚 Phase Summary Chain

- Phase 1: Logging Consolidation ✅ COMPLETE
- Phase 2: Orchestration Consolidation ✅ COMPLETE
- Phase 3: Health Consolidation ✅ COMPLETE
- **Phase 4: Agent Consolidation** (this plan)
- Phase 5: (TBD - likely consciousness systems)

---

**Next Action:** Begin Phase 4 Week 1 analysis when ready. This plan will evolve
based on actual codebase structure discovered during analysis.
