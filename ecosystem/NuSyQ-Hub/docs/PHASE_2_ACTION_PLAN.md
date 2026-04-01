# 🚀 PHASE 2 ACTION PLAN - Terminal Routing Integration

*Ready to execute immediately*

---

## 📋 Phase 2 Overview

**Goal:** Wire terminal routing system to orchestration_defaults.json and enable guild board event routing

**Duration:** 2-4 hours (full session or split across 2)

**Systems Affected:**
- `src/system/agent_terminal_router.py` — Load config, apply routing strategy
- Guild board event emission → Route to specific terminals
- Terminal audit logging → Per-message audit trail

---

## 🎯 Core Task: Update Agent Terminal Router

**File:** `src/system/agent_terminal_router.py`

### Step 1: Add Config Imports

```python
from src.config.orchestration_config_loader import (
    get_terminal_routing_config,
    get_config_value,
)
```

### Step 2: Load Config in Router Initialization

```python
class AgentTerminalRouter:
    def __init__(self):
        # Load routing configuration
        routing_config = get_terminal_routing_config()

        self.routing_strategy = routing_config.get("routing_strategy", "explicit_then_keyword")
        self.priority_terminals = routing_config.get("priority_visibility_terminals", [])
        self.keyword_routes = routing_config.get("keyword_routes", {})
        self.always_log_agents = routing_config.get("always_log_to_agent_terminals", [])
        self.per_message_audit = routing_config.get("per_message_audit_log", False)
        self.audit_log_path = routing_config.get("audit_log_path", "state/terminals/audit.jsonl")
```

### Step 3: Implement Routing Strategy

```python
async def route_message(self, message: dict, agent_id: str) -> dict:
    """
    Route a terminal message based on explicit_then_keyword strategy:
    1. Try explicit channel (if specified)
    2. Try keyword heuristics (CRITICAL, BLOCKED, COMPLETE, etc.)
    3. Try event type routing
    4. Fall back to default agent terminal
    """

    # Strategy: explicit_then_keyword
    if self.routing_strategy == "explicit_then_keyword":
        # 1. Check for explicit channel
        if "channel" in message and message["channel"]:
            target = message["channel"]

        # 2. Try keyword routing
        elif "keyword" in message:
            keyword = message["keyword"].upper()
            target = self.keyword_routes.get(keyword, self._default_terminal(agent_id))

        # 3. Try event type routing
        elif "event_type" in message:
            target = self._route_by_event_type(message["event_type"])

        # 4. Default
        else:
            target = self._default_terminal(agent_id)

    # Log the routing decision
    if self.per_message_audit:
        self._log_audit(agent_id, message, target)

    return {**message, "routed_to": target}
```

### Step 4: Implement Guild Board Routing

```python
async def route_guild_event(self, event_type: str, agent_id: str, data: dict) -> None:
    """
    Route guild board events to appropriate terminals:
    - heartbeat → 🤖 Agents (or 🎯 Zeta if configured)
    - claim → ✓ Tasks
    - progress → 💡 Suggestions
    - blockage → 🔥 Errors
    - complete → ✓ Tasks + 📊 Metrics
    """

    routing_map = {
        "heartbeat": "🎯 Zeta",      # from config: terminal_group
        "claim": "✓ Tasks",
        "progress": "💡 Suggestions",
        "blockage": "🔥 Errors",
        "complete": ["✓ Tasks", "📊 Metrics"],
        "error_detected": "🔥 Errors",
        "dependency_missing": "🔥 Errors",
        "service_down": "⚡ Anomalies",
    }

    target = routing_map.get(event_type, "🏠 Main")

    message = {
        "agent_id": agent_id,
        "event_type": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat(),
    }

    await self.route_message(message, agent_id)
```

---

## 🔧 Integration Points

### Guild Board → Terminal Router

**In guild_board.py:**
```python
async def heartbeat(self, agent_id: str, status: AgentStatus) -> None:
    # ... heartbeat logic ...

    # Route to terminal
    from src.system.agent_terminal_router import router
    await router.route_guild_event(
        event_type="heartbeat",
        agent_id=agent_id,
        data={"status": status.value}
    )
```

**In guild_board.py (claim):**
```python
async def claim_quest(self, agent_id: str, quest_id: str) -> bool:
    # ... claim logic ...

    # Route to terminal
    from src.system.agent_terminal_router import router
    await router.route_guild_event(
        event_type="claim",
        agent_id=agent_id,
        data={"quest_id": quest_id}
    )
```

### Terminal Audit Logging

**New file:** `state/terminals/audit.jsonl`

**Format:**
```json
{
  "timestamp": "2025-12-26T06:00:00Z",
  "agent_id": "copilot",
  "message_type": "guild_event",
  "event_type": "heartbeat",
  "keyword": null,
  "explicit_channel": null,
  "routed_to": "🎯 Zeta",
  "strategy": "explicit_then_keyword",
  "routing_decision": "default_routing"
}
```

---

## 📊 Testing Phase 2

### Test 1: Config Loading
```python
# Verify terminal routing config loads
from src.config.orchestration_config_loader import get_terminal_routing_config
cfg = get_terminal_routing_config()
assert cfg["routing_strategy"] == "explicit_then_keyword"
assert cfg["priority_visibility_terminals"] == ["Claude", "Copilot", "Codex"]
```

### Test 2: Message Routing
```python
# Send test message with explicit channel
message = {"channel": "✓ Tasks", "content": "Test"}
result = await router.route_message(message, "copilot")
assert result["routed_to"] == "✓ Tasks"
```

### Test 3: Keyword Routing
```python
# Send CRITICAL keyword message
message = {"keyword": "CRITICAL", "content": "Error alert"}
result = await router.route_message(message, "copilot")
assert result["routed_to"] in ["🔥 Errors", "⚡ Anomalies"]
```

### Test 4: Guild Event Routing
```python
# Send guild event
await router.route_guild_event("heartbeat", "copilot", {"status": "working"})
# Verify audit log created
audit_file = Path("state/terminals/audit.jsonl")
assert audit_file.exists()
```

### Test 5: Audit Trail
```python
# Verify audit trail is complete
import json
with open("state/terminals/audit.jsonl") as f:
    records = [json.loads(line) for line in f]
assert len(records) > 0
assert records[-1]["agent_id"] == "copilot"
```

---

## 🎯 Success Criteria

| Criterion | Expected | How to Verify |
|-----------|----------|---------------|
| Config loads | ✅ | `get_terminal_routing_config()` returns dict |
| Routing strategy active | explicit_then_keyword | Message routes to correct terminal |
| Guild events route | heartbeat→Zeta, claim→Tasks | Event appears in correct terminal |
| Audit log created | audit.jsonl exists | File present at state/terminals/audit.jsonl |
| Per-message audit | Enabled | Each message logged to audit |
| Priority terminals | [Claude, Copilot, Codex] | Terminal shows agent-scoped messages |

---

## 📈 Expected Outcomes

**After Phase 2:**

1. ✅ Terminal routing is configuration-driven
2. ✅ All guild board events route to correct terminals
3. ✅ Complete audit trail of routing decisions
4. ✅ Easy to adjust routing via config changes
5. ✅ Clear visibility into agent coordination

**New Capabilities:**

```bash
# Test routing with explicit channel
python scripts/start_nusyq.py terminal_route --agent copilot --channel "✓ Tasks" --message "Test"

# View audit log
python scripts/start_nusyq.py terminal_audit --limit 10 --agent copilot

# Test guild event routing
python scripts/start_nusyq.py guild_heartbeat copilot working  # Routes to 🎯 Zeta
```

---

## ⏱️ Estimated Timeline

| Task | Duration | Status |
|------|----------|--------|
| Understand router current state | 15 min | Ready |
| Add config imports | 5 min | Ready |
| Load config in __init__ | 10 min | Ready |
| Implement routing strategy | 30 min | Ready |
| Integrate with guild board | 30 min | Ready |
| Add audit logging | 20 min | Ready |
| Write tests (5 tests) | 45 min | Ready |
| Test in integration | 30 min | Ready |
| Document Phase 2 | 15 min | Ready |
| **Total** | **~3 hours** | Ready |

---

## 🚦 Go/No-Go Checklist

**Go if:**
- [ ] Phase 1 validation complete (✅ YES)
- [ ] Config loader working (✅ YES)
- [ ] Guild board integrated (✅ YES)
- [ ] Current router status known
- [ ] Test environment ready

**Ready to start Phase 2:** ✅ **YES**

---

## 📝 Quick Reference: Files to Modify

**Primary:**
- `src/system/agent_terminal_router.py` — Add config loading, implement routing

**Supporting:**
- `src/guild/guild_board.py` — Add router calls in key methods
- `state/terminals/audit.jsonl` — Created on first routing decision

**Testing:**
- `tests/test_terminal_routing_phase_2.py` — New test file (5 tests)

**Documentation:**
- `docs/TERMINAL_ROUTING_PHASE_2_COMPLETE.md` — Phase 2 completion report

---

## 🎯 Next Command

When ready, execute:

```bash
# Start Phase 2 immediately
python scripts/start_nusyq.py phase_2_terminal_routing

# Or manually:
cd c:\Users\keath\Desktop\Legacy\NuSyQ-Hub
python -m src.system.agent_terminal_router --validate-config
```

---

**Phase 2 Ready to Execute Immediately** ✅
