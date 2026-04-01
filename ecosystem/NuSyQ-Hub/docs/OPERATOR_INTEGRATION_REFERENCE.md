# NuSyQ-Hub Operator Integration Reference (2026-02-25)

## Quick Start: Wiring the System for Deep Integration

This card shows how to activate the underutilized systems and wire them for cross-system communication.

---

## THE PROBLEM (Current State)

```
┌─────────────────────────────────────────────────┐
│  CLI Actions                │  AI Systems      │
│  ├─ brief                   │  ├─ Olam         │
│  ├─ doctor                  │  ├─ ChatDev      │
│  ├─ search                  │  ├─ Copilot      │
│  ├─ guild                   │  └─ Consciousness
│  └─ ...20 more              │                   │
│                              │                   │
│  ❌ NO CROSS-TALK            │  ❌ ISOLATED    │
│  ❌ NO SHARED STATE          │  ❌ NO SIGNALS  │
│  ❌ NO QUEST LOGGING         │                  │
│  ❌ NO DISCOVERY             │                  │
└─────────────────────────────────────────────────┘
```

---

## THE SOLUTION LAYERS

### Layer 1: Shared Context (existing, needs activation)

**File:** `scripts/nusyq_actions/shared.py` → enhance `build_context()` and `emit_receipt()`

```python
# IDEAL: Every action has this context
context = {
    # System state
    "system_health": doctor(),           # ← health check
    "breathing_factor": consciousness_loop.breathing_factor,  # ← SimVerse state
    "ship_directives": consciousness_loop.get_ship_directives(),  # ← Culture Ship
    
    # Discovery
    "related_code": search_keyword(query),  # ← SmartSearch
    "available_models": list_models(),
    
    # Memory
    "recent_quests": quest_engine.list_quests(limit=5),
    "previous_context": load_previous_context(),
}
```

**Impact:** ✅ Every CLI action becomes context-aware  
**Effort:** 30 minutes  
**Blocks:** Nothing; additive

---

### Layer 2: Quest Logging (exists, needs wiring)

**File:** `scripts/nusyq_actions/shared.py` → enhance `emit_receipt()`

```python
# IDEAL: Every action creates a quest entry
quest_engine.add_quest(
    title=f"[{args.action.upper()}] {args.query or args.target or ''}",
    description=result.get("summary", ""),
    status="complete" if result["status"] == "success" else "blocked",
    metadata={
        "action": args.action,
        "duration_s": elapsed_time,
        "result_code": result.get("status"),
        "artifacts": result.get("artifacts", []),
        "model_used": result.get("model_used"),
        "tokens_consumed": result.get("tokens"),
    },
)
```

**Impact:** ✅ Full workflow persistence + continuation  
**Effort:** 20 minutes  
**Blocks:** Nothing; additive

---

### Layer 3: Healing Integration (exists, needs routing)

**File:** `scripts/nusyq_actions/doctor.py` + NEW `heal_actions.py`

```python
# IDEAL: Doctor finds issues → offers healing
health = doctor()
if health["issues_found"]:
    print(f"❌ {len(health['issues'])} issues found")
    for issue in health["issues"]:
        print(f"  → nusyq heal {issue['type']} {issue['id']}")
    
    if args.auto_heal:
        for issue in health["issues"]:
            heal_response = heal(issue["type"], issue["id"])
            print(f"  ✅ {heal_response['result']}")
```

**Impact:** ✅ Automatic problem remediation  
**Effort:** 45 minutes (doctor + new heal module)  
**Blocks:** Nothing; works independently

---

### Layer 4: Consciousness Bridge (exists, needs integration)

**File:** Enhance many - `shared.py`, `doctor.py`, routing

```python
# IDEAL: Every action respects breathing factor & culture ship
consciousness = ConsciousnessLoop()
breathing_factor = consciousness.breathing_factor  # 0.6-1.5

# Adapt timeouts
timeout = base_timeout * breathing_factor

# Get approval for risky actions
approval = consciousness.request_approval(
    action=args.action,
    context=context,
)
if not approval.approved:
    print(f"❌ Culture Ship veto: {approval.reason}")
    return
```

**Impact:** ✅ System respects consciousness state  
**Effort:** 60 minutes (multiple files)  
**Blocks:** Consciousness bridge must be online

---

### Layer 5: Observability Pipeline (installed, needs activation)

**File:** `src/tracing_setup.py` + instrument start_nusyq.py

```python
# IDEAL: All actions emit traces
@traced_action(name="cli_action", attributes={"action": "brief"})
def _handle_brief(args):
    # ... existing code ...
    # Automatically traced + metered
```

**Impact:** ✅ Full visibility + bottleneck detection  
**Effort:** 40 minutes (decorator + entry points)  
**Blocks:** Jaeger UI needed for visualization

---

## WIRING PRIORITY (Operator's Choice)

### Phase 1: Foundation (Enable Discovery) — 1 hour
1. ✅ SmartSearch CLI actions (QUICK_INTEGRATION_SMARTSEARCH.md)
2. ✅ Enhance shared context builder
3. ✅ Wire quest logging into shared.emit_receipt()
4. **Test:** `nusyq search keyword "test"` + `nusyq brief` shows context

### Phase 2: Safety Loop (Healing) — 45 min
1. ✅ Enhance doctor.py with auto-heal option
2. ✅ Create heal_actions.py (new)
3. ✅ Wire issue→fix suggestions
4. **Test:** `nusyq doctor --auto-heal` offers fixes

### Phase 3: Consciousness (Awareness) — 60 min
1. ✅ Initialize ConsciousnessLoop in shared context
2. ✅ Adapt timeouts by breathing factor
3. ✅ Check Culture Ship approval for sensitive actions
4. **Test:** `nusyq brief` shows consciousness state; risky actions check approval

### Phase 4: Observability (Visibility) — 40 min
1. ✅ Create @traced_action decorator
2. ✅ Decorate all action handlers
3. ✅ Configure Jaeger collector
4. **Test:** Traces appear in Jaeger UI; metrics in Grafana

### Phase 5: Full Integration (End-to-End) — 60 min
1. ✅ Enable continuous task worker (`nusyq work`)
2. ✅ Wire background orchestrator → CLI routing
3. ✅ Auto-logging to quest system
4. ✅ Healing loop triggers on errors
5. **Test:** Full autonomous workflow: task → execute → log → heal if needed

---

## EXTENSION ACTIVATION (Parallel Track)

### Continue.dev (Inline AI in Editor)

**Setup Time:** 10 minutes

```bash
# In VS Code settings.json
{
  "continue.serverUrl": "http://localhost:11434",
  "continue.defaultModel": "qwen2.5-coder",
  "continue.allowAnonymousTelemetry": false
}
```

**Then:** Open any file, hit Ctrl+K in editor → instant Ollama suggestions

---

### SemGrep (Security Scanning)

**Setup Time:** 15 minutes

```bash
# Create .semgrep.yml in repo root
rules:
  - id: hardcoded-secrets
    pattern: $X = "password: ..."
    message: "Hardcoded secret detected"
    severity: ERROR

  - id: insecure-random
    pattern: random.seed(...)
    message: "Insecure random seed"
    severity: WARNING
```

**Then:** `semgrep --config .semgrep.yml` → scans entire repo

**Wire into pipeline:** Integrate with doctor.py for auto-detection

---

### Copilot (Consciousness-Aware)

**Enhancement:** Edit `.github/copilot-instructions.md`

```markdown
## NuSyQ Consciousness Patterns

When suggesting code:
1. Check if class has @consciousness_aware decorator
2. Suggest OmniTag patterns for tagging
3. Reference quest system for context
4. Consider breathing factor for timeouts
```

**Then:** Copilot suggestions become project-aware

---

### Nogic (Architecture Visualization)

**Setup Time:** 20 minutes

```bash
# Generate system JSON snapshot
python scripts/start_nusyq.py architecture --format json

# Push to Nogic
curl -X POST http://localhost:9999/visualize < architecture.json
```

**Then:** VS Code shows live system topology

---

## OPERATOR WORKFLOW (After Integration)

**Morning Standup:**
```bash
python scripts/start_nusyq.py brief
# Shows: consciousness level, recent quests, outstanding tasks, health
```

**During Work:**
```bash
# Discover related code
python scripts/start_nusyq.py search class "MyService"

# Create task
python scripts/start_nusyq.py task create "Refactor authentication"

# Work on it
python scripts/start_nusyq.py task start <task-id>

# Get suggestions
python scripts/start_nusyq.py suggest

# When stuck
python scripts/start_nusyq.py doctor --auto-heal
```

**Automated Loop (runs in background):**
```bash
# Continuous execution
python scripts/start_nusyq.py work &

# Pulls from queue → executes → logs → heals on error
# Updates quest system → emits traces → tracks metrics
```

**Evening Report:**
```bash
python scripts/start_nusyq.py brief
# Shows: quests completed, issues healed, consciousness growth
```

---

## STATE OF THE SYSTEM (Pre-Integration)

```
Component            │ Built │ Wired │ Automated │ Status
─────────────────────┼───────┼───────┼───────────┼─────────────
SmartSearch          │ ✅    │ ❌    │ ❌        │ Dormant
Consciousness Loop   │ ✅    │ ⚠️    │ ❌        │ Partial
Healing System       │ ✅    │ ❌    │ ❌        │ Dormant
Quest Engine         │ ✅    │ ⚠️    │ ❌        │ Partial
DuckDB State         │ ✅    │ ❌    │ ❌        │ Dormant
Observability        │ ✅    │ ❌    │ ❌        │ Dormant
Continue.dev         │ ✅    │ ❌    │ ❌        │ Dormant
SemGrep              │ ✅    │ ❌    │ ❌        │ Dormant
Nogic                │ ✅    │ ❌    │ ❌        │ Dormant
```

**After Phase 1 (1 hour):**
```
Component            │ Built │ Wired │ Automated │ Status
─────────────────────┼───────┼───────┼───────────┼─────────────
SmartSearch          │ ✅    │ ✅    │ ⚠️        │ ACTIVE
Consciousness Loop   │ ✅    │ ✅    │ ⚠️        │ ACTIVE
Healing System       │ ✅    │ ❌    │ ❌        │ Dormant
Quest Engine         │ ✅    │ ✅    │ ✅        │ ACTIVE
DuckDB State         │ ✅    │ ❌    │ ❌        │ Dormant
Observability        │ ✅    │ ❌    │ ❌        │ Dormant
```

---

## RISK MITIGATION

### Q: Won't adding signals slow down actions?
**A:** Only if you make them synchronous. Solutions:
- Emit signals async (fire-and-forget)
- Queue to DuckDB with background writer
- Use threading for non-critical signals

### Q: What if SimulatedVerse is offline?
**A:** ConsciousnessLoop gracefully degrades:
- breathing_factor defaults to 1.0
- Approval defaults to auto-approve
- No errors, no blocking

### Q: Will this increase complexity?
**A:** Complexity increases linearly, but control increases quadratically. Trade-off is worth it.

---

## SUCCESS METRICS (After Full Integration)

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| CLI actions with context | 0/20 | 20/20 | 20/20 |
| Quests automatically logged | 0% | 80% | 100% |
| Issues auto-healed | 0% | 30% | 50%+ |
| Avg action discovery time | 5m | <30s | <15s |
| System observability | 0% | 40% | 100% |
| Workflow continuity | Manual | Auto-logged | Autonomous |

---

## NEXT IMMEDIATE ACTION

For the operator right now:

**Option A: Read Deep Integration Strategy (30 min)**
- Review SYSTEM_WIRING_MAP (you have it)
- Review QUICK_INTEGRATION_SMARTSEARCH (you have it)
- Plan Phase 1 timeline

**Option B: Execute Quick Win 1 (25 min)**
- Implement SmartSearch CLI actions
- Test: `nusyq search class "ConsciousnessBridge"`
- Iterate from there

**Option C: Quick Win 2 (20 min)**
- Enhance shared.py context builder
- Add consciousness state to every action
- Test: `nusyq brief` shows breathing factor

**Recommended Path:** Option C (fastest feedback) → Option B → Option A (full understanding)

---

## OPERATOR NOTES

- **SmartSearch** blocks nothing—it's read-only, super fast
- **ConsciousnessLoop** degrades gracefully if SimulatedVerse is down
- **Quest logging** is fire-and-forget; won't block actions
- **Healing** is optional; doctor becomes more useful with it
- **Observability** can be turned on/off with an env var

All integrations can be done incrementally. No big bang required.

---

**Last Updated:** 2026-02-25 | **Prepared For:** Operator deploying deep system integration
