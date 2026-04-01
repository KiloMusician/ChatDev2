# Systematic Timeout Replacement Plan

**Created**: October 7, 2025
**Status**: Phase 1 Complete (Adaptive System Built) → Phase 2 Ready (Systematic Replacement)

---

## 📊 Inventory: Hardcoded Timeouts Found

### Total: 10 Hardcoded Timeouts (excluding adaptive_timeout_manager.py)

| # | File | Line | Current Value | Context | Complexity | Priority |
|---|------|------|---------------|---------|------------|----------|
| 1 | `claude_code_bridge.py` | 107 | `timeout: int = 30` | Query function parameter | SIMPLE | HIGH |
| 2 | `claude_code_bridge.py` | 155 | `aiohttp.ClientTimeout(total=5)` | Health check | TRIVIAL | MEDIUM |
| 3 | `claude_code_bridge.py` | (DONE) | ~~`timeout=60`~~ | Orchestration | MODERATE | ✅ COMPLETE |
| 4 | `multi_agent_session.py` | 404 | `timeout=600` | Agent response (10 min) | MODERATE | HIGH |
| 5 | `multi_agent_session.py` | 584 | `timeout=120` | Session execution (2 min) | MODERATE | HIGH |
| 6 | `flexibility_manager.py` | 77 | `timeout=5` | Command execution | TRIVIAL | LOW |
| 7 | `flexibility_manager.py` | 174 | `timeout=10` | Validation check | SIMPLE | LOW |
| 8 | `flexibility_manager.py` | 194 | `timeout=300` | GitHub auth (5 min) | SIMPLE | MEDIUM |
| 9 | `flexibility_manager.py` | 213 | `timeout=30` | Health check | SIMPLE | LOW |
| 10 | `flexibility_manager.py` | 259 | `timeout=60` | Status check | SIMPLE | LOW |

---

## 🎯 Replacement Strategy

### Decision Tree

```
Is this timeout for AI agent execution?
├─ YES → Use AgentType classification
│   ├─ Single local agent → AgentType.LOCAL_FAST / LOCAL_QUALITY
│   ├─ Multiple agents → AgentType.MULTI_AGENT
│   └─ Full orchestration → AgentType.ORCHESTRATOR
│
└─ NO → Is it infrastructure/tool execution?
    ├─ YES → Use TaskComplexity classification
    │   ├─ Quick command → TaskComplexity.TRIVIAL (5-30s)
    │   ├─ Validation/check → TaskComplexity.SIMPLE (10-180s)
    │   └─ Setup/authentication → TaskComplexity.MODERATE (30-1800s)
    │
    └─ Keep hardcoded if external constraint
        └─ Example: API rate limit = 30s (external requirement)
```

### Priority Levels

**HIGH** (Complete ASAP):
- Multi-agent session timeouts (lines 404, 584)
- Claude bridge query timeout (line 107)
- Impact: Direct AI agent execution

**MEDIUM** (Complete this session):
- Health check timeouts (lines 155, 213)
- GitHub auth timeout (line 194)
- Impact: System integration

**LOW** (Complete when time permits):
- Flexibility manager command timeouts (lines 77, 174, 259)
- Impact: Infrastructure operations

---

## 🔧 Replacement Patterns

### Pattern 1: AI Agent Execution

**Before**:
```python
response = await agent.query("Task", timeout=600)  # Why 10 minutes?
```

**After**:
```python
from config.adaptive_timeout_manager import get_timeout_manager, AgentType, TaskComplexity

# Determine agent type and complexity
agent_type = AgentType.LOCAL_QUALITY  # or LOCAL_FAST, MULTI_AGENT, etc.
complexity = TaskComplexity.MODERATE  # based on task description

# Get adaptive timeout
timeout_manager = get_timeout_manager()
timeout_rec = timeout_manager.get_timeout(agent_type, complexity)

logger.debug(
    "Using adaptive timeout: %.1fs (confidence=%.0f%%)",
    timeout_rec.timeout_seconds,
    timeout_rec.confidence * 100
)

# Execute with adaptive timeout
start_time = time.time()
response = await agent.query("Task", timeout=timeout_rec.timeout_seconds)
duration = time.time() - start_time

# Record for learning
timeout_manager.record_execution(
    agent_type=agent_type,
    task_complexity=complexity,
    duration=duration,
    succeeded=(response is not None),
    context={"task": "Query execution"}
)
```

### Pattern 2: Infrastructure Operations

**Before**:
```python
result = subprocess.run(['command'], timeout=30)  # Arbitrary guess
```

**After**:
```python
from config.adaptive_timeout_manager import get_timeout_manager, AgentType, TaskComplexity

# Infrastructure operations use TaskComplexity directly
timeout_manager = get_timeout_manager()
timeout_rec = timeout_manager.get_timeout(
    agent_type=AgentType.LOCAL_FAST,  # Infrastructure is fast
    task_complexity=TaskComplexity.SIMPLE  # Most commands are simple
)

result = subprocess.run(['command'], timeout=timeout_rec.timeout_seconds)
```

### Pattern 3: Health Checks (Keep Short)

**Before**:
```python
timeout = aiohttp.ClientTimeout(total=5)  # Health checks should be fast
```

**After** (Special case - keep short but make explicit):
```python
# Health checks should remain fast (5-10s) to detect issues quickly
# Use TRIVIAL complexity with LOCAL_FAST agent type
timeout_manager = get_timeout_manager()
timeout_rec = timeout_manager.get_timeout(
    agent_type=AgentType.LOCAL_FAST,
    task_complexity=TaskComplexity.TRIVIAL
)

# Ensure timeout is capped at 10s for health checks
health_timeout = min(timeout_rec.timeout_seconds, 10)
timeout = aiohttp.ClientTimeout(total=health_timeout)
```

---

## 📋 Implementation Checklist

### Phase 2A: HIGH Priority (Complete Today)

#### 1. `multi_agent_session.py` Line 404 ✅ Ready
```python
# Current: timeout=600  # 10 minute timeout
# Agent: LOCAL_QUALITY or MULTI_AGENT based on agent count
# Complexity: MODERATE (most multi-agent tasks)
# Expected adaptive: 300-1800s based on history
```

**Replacement**:
- [ ] Add import of adaptive_timeout_manager
- [ ] Calculate timeout based on agent_count and task complexity
- [ ] Record execution after completion
- [ ] Test with various agent combinations

#### 2. `multi_agent_session.py` Line 584 ✅ Ready
```python
# Current: timeout=120
# Agent: Depends on session type
# Complexity: Depends on task
# Expected adaptive: 30-600s based on history
```

**Replacement**:
- [ ] Add adaptive timeout calculation
- [ ] Use session parameters (mode, agent_count) to determine AgentType
- [ ] Record execution metrics
- [ ] Test with different session modes

#### 3. `claude_code_bridge.py` Line 107 ✅ Ready
```python
# Current: timeout: int = 30 (function parameter default)
# Agent: REMOTE_API (Claude Code)
# Complexity: Variable based on query
# Expected adaptive: 30-600s based on query type
```

**Replacement**:
- [ ] Change parameter to Optional[float] = None
- [ ] Calculate adaptive timeout if None provided
- [ ] Use query priority to determine complexity
- [ ] Record execution for learning

### Phase 2B: MEDIUM Priority (Complete This Session)

#### 4. `claude_code_bridge.py` Line 155 ⏸️ Consider
```python
# Current: timeout=aiohttp.ClientTimeout(total=5)
# Context: Health check (should remain fast)
# Decision: Keep short but use TRIVIAL complexity
# Expected adaptive: 5-10s (capped at 10s for health)
```

**Replacement**:
- [ ] Use TRIVIAL + LOCAL_FAST
- [ ] Cap at 10s maximum for health checks
- [ ] Consider: Keep hardcoded 5s (health checks need fast failure)

#### 5. `flexibility_manager.py` Line 194 ✅ Ready
```python
# Current: timeout=300  # GitHub auth
# Agent: LOCAL_FAST (infrastructure)
# Complexity: MODERATE (user interaction required)
# Expected adaptive: 120-600s
```

**Replacement**:
- [ ] Use LOCAL_FAST + MODERATE
- [ ] GitHub auth can take variable time (user input)
- [ ] Record execution for learning

### Phase 2C: LOW Priority (When Time Permits)

#### 6-10. `flexibility_manager.py` Lines 77, 174, 213, 259 ⏸️ Evaluate
```python
# Context: Infrastructure health checks, validations
# Current: 5s, 10s, 30s, 60s
# Decision: These may be appropriate as-is
# Reason: Infrastructure timeouts often have external constraints
```

**Action**:
- [ ] Review each timeout context
- [ ] Determine if external constraint or arbitrary
- [ ] Replace arbitrary, keep external constraints
- [ ] Document decision for each

---

## 🚀 Execution Plan

### Step 1: HIGH Priority Replacements (Now)

1. **multi_agent_session.py** - 2 timeouts
   - Impact: Core multi-agent functionality
   - Time: 30-45 minutes
   - Risk: Medium (test thoroughly)

2. **claude_code_bridge.py** Line 107 - 1 timeout
   - Impact: Claude Code integration
   - Time: 15-20 minutes
   - Risk: Low (already tested pattern)

### Step 2: MEDIUM Priority Replacements (Today)

3. **Health checks** - 2 timeouts
   - Impact: System monitoring
   - Time: 20-30 minutes
   - Risk: Low (keep conservative)

4. **GitHub auth** - 1 timeout
   - Impact: Setup/configuration
   - Time: 10-15 minutes
   - Risk: Very Low (one-time operation)

### Step 3: LOW Priority Evaluation (Future Session)

5. **flexibility_manager.py** - 5 timeouts
   - Impact: Infrastructure operations
   - Time: 1-2 hours (thorough evaluation)
   - Risk: Low (mostly independent operations)

---

## 📊 Success Metrics

### Quantitative

- [ ] **10 → 0 hardcoded timeouts** (100% replacement or documented exception)
- [ ] **100% test coverage** on adaptive timeout calculations
- [ ] **>80% prediction accuracy** after 20 executions per agent+complexity
- [ ] **0 timeout-related test failures**

### Qualitative

- [ ] **All timeouts have reasoning** (no more "arbitrary guesses")
- [ ] **System learns continuously** (performance_metrics.json grows)
- [ ] **Confidence increases over time** (30% → 90%+)
- [ ] **Documentation complete** (knowledge-base.yaml updated)

---

## 🎓 Decision Log

### Keep Hardcoded When...

1. **External Constraint**: API rate limit, network protocol requirement
2. **Safety Critical**: Health checks must fail fast (5-10s reasonable)
3. **User Experience**: Interactive operations need reasonable timeouts
4. **Infrastructure**: Some system operations have known, stable durations

### Replace With Adaptive When...

1. **AI Agent Execution**: Varies by agent type, task complexity, system load
2. **Arbitrary Guess**: "Seemed reasonable" or "I don't know, 60 seconds?"
3. **Observed Variance**: Historical data shows wide range of durations
4. **Learning Valuable**: System can improve predictions over time

### Document Always

- **Decision**: Keep hardcoded or replace with adaptive
- **Reasoning**: Why this decision makes sense
- **Evidence**: Data supporting the decision (if available)
- **Review Date**: When to reconsider (3-6 months)

---

## 📝 Template: Replacement Commit Message

```
Replace hardcoded timeout with adaptive calculation in [FILE]

Context:
- Line [LINE]: timeout=[OLD_VALUE]
- Usage: [DESCRIPTION]

Changes:
- Agent Type: [LOCAL_FAST|LOCAL_QUALITY|REMOTE_API|MULTI_AGENT|ORCHESTRATOR]
- Task Complexity: [TRIVIAL|SIMPLE|MODERATE|COMPLEX|CRITICAL]
- Expected Range: [MIN-MAX]s (based on defaults)

Impact:
- Before: Hardcoded [OLD_VALUE]s (arbitrary)
- After: Adaptive [EXPECTED]s (data-driven, confidence=[X]%)

Testing:
- [ ] Existing tests pass
- [ ] Execution recorded to performance_metrics.json
- [ ] Timeout adapts based on historical data

Part of systematic timeout replacement initiative.
See: NuSyQ_Adaptive_Timeout_Complete_20251006.md
```

---

## 🔍 Next Session Preview

**Immediate**: Replace HIGH priority timeouts (multi_agent_session.py, claude_code_bridge.py)

**After That**: Search for other arbitrary constraints:
```bash
# Max turns
grep -r "max_turns.*=.*[0-9]" config/

# Max tokens
grep -r "max_tokens.*=.*[0-9]" config/

# Retry attempts
grep -r "max_retries.*=.*[0-9]" config/

# Buffer sizes
grep -r "buffer_size.*=.*[0-9]" config/
```

**Long-term**: Create generalized constraint management system
- AdaptiveTimeoutManager (✅ done)
- AdaptiveTokenLimitManager (future)
- AdaptiveRetryManager (future)
- AdaptiveBufferManager (future)

---

## ✅ Completion Criteria

### Phase 2 Complete When:

- [ ] All HIGH priority timeouts replaced (3 timeouts)
- [ ] All MEDIUM priority timeouts evaluated (3 timeouts)
- [ ] All LOW priority timeouts documented (4 timeouts)
- [ ] Tests passing with adaptive timeouts
- [ ] Performance metrics accumulating data
- [ ] knowledge-base.yaml updated with session
- [ ] SYSTEMATIC_REPLACEMENT_COMPLETE.md created

### System Ready When:

- [ ] 100% timeouts adaptive or justified as hardcoded
- [ ] Prediction accuracy >80% (after sufficient data)
- [ ] Confidence levels increasing over time
- [ ] No timeout-related test failures
- [ ] Other arbitrary constraints identified
- [ ] Generalized constraint management planned

---

*Next AI Agent: Start with HIGH priority replacements in multi_agent_session.py. Use patterns from this document. Record all executions for learning.*
