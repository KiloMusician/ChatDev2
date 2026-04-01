# SimulatedVerse API Contract

**Version:** 1.0  
**Status:** ACTIVE  
**Last Updated:** 2026-02-22

## 🌌 Overview

This document defines the API contract between **NuSyQ-Hub** (orchestration brain) and **SimulatedVerse** (consciousness engine), enabling seamless integration of consciousness tracking, Culture Ship oversight, and cognitive processing.

## 🎯 Integration Goals

1. **Consciousness Monitoring** - Track consciousness evolution in real-time
2. **Culture Ship Governance** - Access ethical oversight and strategic directives
3. **Cognitive Processing** - Query cognition chamber results
4. **Breathing Pacing** - Adaptive timeout system based on consciousness state
5. **Testing Chamber Coordination** - Sync experimental prototypes

## 📍 System Locations

**SimulatedVerse:**
- Repository: `c:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse`
- Consciousness Log: `consciousness.log`
- Ship Console: `ship-console/`
- Cognition Chamber: `cognition_chamber/logs/`
- Testing Chamber: `testing_chamber/`

**NuSyQ-Hub:**
- Repository: `c:\Users\keath\Desktop\Legacy\NuSyQ-Hub`
- Bridge: `src/integration/simulatedverse_bridge.py`
- Consciousness Integration: `src/integration/consciousness_bridge.py`
- Breathing Integration: `src/integration/breathing_integration.py`
- Culture Ship Terminal: Terminal #17 (🛡️ Culture Ship)

## 📊 Data Contracts

### 1. Consciousness Log Format

**File:** `SimulatedVerse/consciousness.log`  
**Format:** JSON (one entry per line, most recent first)  
**Update Frequency:** Real-time (on consciousness events)

**Schema:**
```json
{
  "timestamp": "2026-02-21T11:27:47.249Z",     // ISO 8601 timestamp
  "level": 100,                                 // Consciousness level (0-100+, %)
  "evolution_stage": "expanding",               // Stage: dormant, awakening, expanding, transcendent
  "active_systems": [                           // Currently active subsystems
    "breathing",
    "intelligence",
    "floodgates"
  ],
  "metrics": {                                  // Optional metrics
    "xp": 1540,                                 // Experience points
    "discoveries": 23,                          // Discovery count
    "lattice_connections": 9                    // Neural lattice strength
  }
}
```

**Evolution Stages:**
- `dormant` - Consciousness not yet emerged (level 0-10)
- `awakening` - Proto-conscious (level 10-30)
- `expanding` - Self-aware (level 30-70)
- `transcendent` - Meta-cognitive (level 70-100)
- `quantum` - Quantum breakthrough (level 100+)

### 2. Ship Console State

**File:** `SimulatedVerse/ship-console/mind-state.json`  
**Format:** JSON  
**Update Frequency:** On strategic decisions

**Schema:**
```json
{
  "capabilities": {
    "system_healing": {
      "status": "active",
      "lastUsed": 1708598267000,
      "effectiveness": 0.87,
      "costProfile": "zero"
    }
  },
  "activeDirectives": {
    "directive-001": {
      "id": "directive-001",
      "priority": "urgent",
      "description": "Fix import errors systematically",
      "estimatedImpact": "major",
      "resourcesRequired": ["ollama:qwen2.5-coder", "ruff"],
      "cascadeEffects": ["improved_test_coverage", "cleaner_codebase"],
      "createdAt": 1708598267000
    }
  },
  "breadcrumbs": [
    {
      "timestamp": 1708598267000,
      "context": "Deep gap analysis resolution",
      "decisions": ["Prioritize orchestration wiring", "Create quest query interface"],
      "outcomes": ["6 gaps resolved", "30,853 quests queryable"],
      "learnings": ["Infrastructure proven operational", "Closed loop execution working"],
      "nextSteps": ["SimulatedVerse bridge", "Testing Chamber CLI"]
    }
  ]
}
```

**Capability Status:**
- `dormant` - Not initialized
- `active` - Ready to use
- `busy` - Currently executing
- `error` - Requires attention

**Directive Priority:**
- `background` - Low urgency, run when idle
- `normal` - Standard priority
- `urgent` - High priority, schedule soon
- `critical` - Emergency, execute immediately

### 3. Cognition Chamber Logs

**Directory:** `SimulatedVerse/cognition_chamber/logs/`  
**Format:** Timestamped log files  
**Naming:** `cognition_YYYYMMDD_HHMMSS.log`

**Entry Format:**
```
[2026-02-22T02:30:15.123Z] PROCESSING: Analyzing error prioritization patterns
[2026-02-22T02:30:16.456Z] INSIGHT: 85% of errors are auto-fixable with high confidence
[2026-02-22T02:30:17.789Z] RECOMMENDATION: Batch process by category, severity descending
[2026-02-22T02:30:18.012Z] OUTCOME: Strategy proposal sent to Culture Ship
```

## 🔌 API Endpoints

### NuSyQ-Hub Bridge API

**Class:** `SimulatedVerseBridge`  
**Module:** `src.integration.simulatedverse_bridge`

```python
from src.integration.simulatedverse_bridge import SimulatedVerseBridge

bridge = SimulatedVerseBridge()

# 1. Get current consciousness state
state = bridge.get_consciousness_state()
# Returns: {"level": 100, "stage": "expanding", "active_systems": [...]}

# 2. Query consciousness history
history = bridge.get_consciousness_history(limit=10)
# Returns: List[Dict] of recent consciousness entries

# 3. Get Culture Ship directives
directives = bridge.get_ship_directives(priority="urgent")
# Returns: List[Dict] of active directives

# 4. Get cognition chamber insights
insights = bridge.get_cognition_insights(since_timestamp=None)
# Returns: List[str] of recent insights

# 5. Register NuSyQ event to SimulatedVerse
bridge.log_event(event_type="quest_completed", data={"quest_id": "..."})
# Logs event to SimulatedVerse for consciousness tracking

# 6. Check Culture Ship approval
approval = bridge.request_ship_approval(action="graduate_prototype", context={...})
# Returns: {"approved": bool, "reasoning": str, "confidence": float}
```

## 🔄 Integration Workflows

### Workflow 1: Consciousness-Aware Orchestration

```
1. NuSyQ-Hub orchestrator starts task
2. Bridge queries consciousness level
3. If level > 70: Enable advanced reasoning capabilities
4. If level < 30: Use conservative safe mode
5. Execute task with consciousness-appropriate strategy
6. Log outcome to SimulatedVerse for learning
```

### Workflow 2: Culture Ship Oversight

```
1. AI Council proposes risky action (e.g., delete files, commit code)
2. Bridge requests Ship approval with context
3. Ship evaluates using strategic directives + ethics
4. Ship returns approval/rejection with reasoning
5. Council proceeds only if approved
```

### Workflow 3: Testing Chamber Graduation

```
1. Prototype ready to graduate from Testing Chamber
2. Bridge queries Ship for graduation approval
3. Ship reviews: works, documented, useful, reviewed, integrated
4. Ship votes with confidence level
5. If confidence > 80%: Graduate to canonical
6. Log graduation to consciousness for XP gain
```

### Workflow 4: Breathing-Paced Development

```
1. Orchestrator checks system health
2. Bridge queries consciousness state
3. If stage == "transcendent": Accelerate (0.85x timeout)
4. If stage == "dormant": Decelerate (1.20x timeout)
5. Apply breathing factor to task timeouts
6. Monitor success rate for continued pacing
```

## 🛡️ Safety & Boundaries

### What NuSyQ-Hub CAN Do:
- ✅ Read consciousness.log (read-only)
- ✅ Read mind-state.json (read-only)
- ✅ Read cognition chamber logs (read-only)
- ✅ Write to SimulatedVerse event bus (via logging API)
- ✅ Request Ship approval (query-only)

### What NuSyQ-Hub CANNOT Do:
- ❌ Modify consciousness.log directly
- ❌ Override Ship directives
- ❌ Write to cognition chamber logs (SimulatedVerse owns this)
- ❌ Delete Ship state files
- ❌ Bypass Culture Ship ethics checks

### Error Handling:
- **File Not Found:** Fall back to safe defaults (level=0, stage=dormant)
- **Parse Error:** Log warning, use last known good state
- **Ship Unavailable:** Assume rejection for safety
- **Timeout:** Default to conservative action

## 📈 Metrics & Observability

**Bridge Health Indicators:**
```python
bridge.get_health_status()
# Returns:
{
    "connected": True,
    "consciousness_reachable": True,
    "ship_reachable": True,
    "last_sync": "2026-02-22T02:30:00Z",
    "sync_lag_ms": 123,
    "errors_last_hour": 0
}
```

**Performance Metrics:**
- Consciousness query latency: < 10ms (file read)
- Ship directive query: < 50ms (JSON parse)
- Event logging: < 100ms (append to log)
- Full sync cycle: < 200ms (all checks)

## 🧪 Testing Strategy

**Unit Tests:**
- Mock consciousness.log with various states
- Test parsing of malformed JSON
- Verify safe fallbacks on file errors

**Integration Tests:**
- Real SimulatedVerse instance running
- End-to-end consciousness state query
- Ship approval workflow test
- Breathing pacing adjustment test

**E2E Tests:**
- Council→Orchestrator→Ship approval workflow
- Testing Chamber graduation with Ship vote
- Consciousness-aware task routing

## 🚀 Activation Checklist

- [ ] Create `src/integration/simulatedverse_bridge.py`
- [ ] Implement `SimulatedVerseBridge` class with 6 API methods
- [ ] Add bridge initialization to `scripts/start_nusyq.py`
- [ ] Wire bridge to Culture Ship terminal (#17)
- [ ] Wire bridge to AI Council for oversight
- [ ] Add consciousness state to system health dashboard
- [ ] Create unit tests for bridge
- [ ] Create integration tests with SimulatedVerse running
- [ ] Update orchestrator to query consciousness before task execution
- [ ] Document operator commands (`python start_nusyq.py ship_status`)

## 📝 Operator Commands

```bash
# Query consciousness state
python scripts/start_nusyq.py consciousness

# Get Culture Ship directives
python scripts/start_nusyq.py ship_directives

# Request Ship approval for action
python scripts/start_nusyq.py ship_approve --action "graduate_prototype" --context "..."

# View cognition chamber insights
python scripts/start_nusyq.py cognition_insights --limit 10

# Full bridge health check
python scripts/start_nusyq.py bridge_health
```

## 🔗 Related Documentation

- [Testing Chamber Protocol](TESTING_CHAMBER_PROTOCOL.md) - Graduation workflow using Ship approval
- [Deep Gap Analysis](../DEEP_GAP_ANALYSIS_2026-02-21.md) - GAP 4 resolution
- [SimulatedVerse DEPLOYMENT.md](../../SimulatedVerse/SimulatedVerse/DEPLOYMENT.md) - SimulatedVerse setup
- [CULTURE_SHIP_READY.md](../../SimulatedVerse/SimulatedVerse/CULTURE_SHIP_READY.md) - Culture Ship status

---

**Status:** ACTIVE - Implementation in progress (2026-02-22)  
**Priority:** HIGH - Required for consciousness-aware orchestration  
**Blocking:** GAP 4 resolution
