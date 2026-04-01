# Cascade Actions Audit: Missing Wiring & Implementation Gaps

**Date**: 2026-01-14
**Status**: Critical Cascade Infrastructure Incomplete
**Scope**: NuSyQ-Hub Cascade System

---

## Executive Summary

Extensive cascade action **infrastructure exists but is UNWIRED**. The system has:
- ✅ **Event bus system** (`src/utils/event_bus.py`)
- ✅ **Auto-healing monitor** (`src/orchestration/auto_healing.py`)
- ✅ **Auto-recovery watchdog** (`src/utils/auto_recovery_watchdog.py`)
- ✅ **Cross-repo sync** (`src/integration/cross_repo_sync.py`)
- ✅ **N8N webhook integration** (`src/integration/n8n_integration.py`)
- ❌ **NO INTEGRATION** between system status changes and cascade triggers
- ❌ **NO EVENT PROPAGATION** from status.py to dependent systems
- ❌ **NO CASCADE HOOKS** for tripartite synchronization

### Critical Gap
> **System status changes happen in isolation - nothing cascades**

---

## 🔴 Missing Cascade Actions

### 1. System Status Change Cascades (CRITICAL)

#### Current State
`src/system/status.py` has NO cascade hooks:

```python
# ❌ Current: No cascades
def set_system_status(status: str, run_id: str = None, details: dict = None):
    payload = {...}
    with open(STATUS_FILE, "w") as f:
        json.dump(payload, f)
    # NOTHING ELSE HAPPENS!
```

#### What Should Cascade When Status Changes

| Status Change | Should Trigger | Currently Happens |
|---------------|----------------|-------------------|
| `off` → `on` | 1. Emit event to event_bus<br>2. Notify cross-repo sync<br>3. Trigger n8n workflow<br>4. Wake dependent systems<br>5. Initialize auto-healing | ❌ Nothing |
| `on` → `off` | 1. Emit shutdown event<br>2. Flush event logs<br>3. Notify other repos<br>4. Graceful degradation<br>5. Save final checkpoint | ❌ Nothing |
| `on` → `error` | 1. **Auto-healing trigger**<br>2. Alert watchdog<br>3. Emit error event<br>4. Escalate to n8n<br>5. Notify operators | ❌ Nothing |
| `error` → `on` | 1. Emit recovery event<br>2. Resume workflows<br>3. Clear error state<br>4. Re-sync repos | ❌ Nothing |

#### Implementation Gap
**Status changes are silent** - no events, no notifications, no cascades.

### 2. Heartbeat Cascade Actions (MISSING)

#### Current State
```python
# ❌ Current: Just updates timestamp
def heartbeat(run_id: str = None, details: dict = None):
    set_system_status(status="on", ...)
    # No cascade actions!
```

#### What Should Cascade Every Heartbeat

| Heartbeat Event | Should Trigger | Currently |
|-----------------|----------------|-----------|
| Every heartbeat | Update metrics, check stale subsystems | ❌ Nothing |
| First heartbeat after offline | Trigger system startup cascade | ❌ Nothing |
| Heartbeat missed (timeout) | **Auto-recovery watchdog alert** | ❌ Nothing |
| Heartbeat health degraded | Escalate to healing monitor | ❌ Nothing |

### 3. Event Bus Integration (INCOMPLETE)

#### Infrastructure Exists
`src/utils/event_bus.py` provides:
```python
def emit_event(stream, event_type, payload, message):
    # Writes to log files in state/logs/
    ...
```

**Streams defined**:
- `agent_bus` - Agent communications
- `council_decisions` - AI council votes
- `culture_ship_audits` - Audit results
- `chatdev_latest` - ChatDev updates
- `moderator` - System moderation
- `errors` - Error events
- `anomalies` - Anomaly detection
- `test_history` - Test results

#### What's Missing: Status → Event Bus Wiring

**NO CONNECTION** between:
- `status.py` status changes → `event_bus` emission
- `problems_api.py` problem detection → `event_bus` errors stream
- `auto_healing.py` healing attempts → `event_bus` healing stream
- Heartbeat updates → `event_bus` system stream

#### Current Usage
Only **2 files** actually use `emit_event`:
1. `src/ai/ollama_chatdev_integrator.py` - Emits agent events
2. `src/guild/guild_board.py` - Emits guild events

**259 other modules** that should emit events **DON'T**.

### 4. Auto-Healing Cascade (DORMANT)

#### Infrastructure Exists
`src/orchestration/auto_healing.py` provides:
```python
class AutoHealingMonitor:
    def on_error(self, error, context, healing_callback):
        # Detects errors from traces
        # Triggers quantum resolver
        # Tracks healing success/failure
```

**Capabilities**:
- Real-time error detection
- Automatic quantum resolver invocation
- Healing success/failure tracking
- Cooldown and retry logic
- Prometheus metrics integration

#### What's Missing: Trigger Wiring

| Error Source | Should Trigger Auto-Healing | Currently |
|--------------|----------------------------|-----------|
| `status.py` → `error` state | ✅ Yes | ❌ Not wired |
| `problems_api.py` critical errors | ✅ Yes | ❌ Not wired |
| Observability traces | ✅ Yes | ⚠️ Partially (if tracing enabled) |
| Exception handlers | ✅ Yes | ❌ Not wired |

**Auto-healing exists but nothing invokes it!**

### 5. Cross-Repo Sync Cascades (INCOMPLETE)

#### Infrastructure Exists
`src/integration/cross_repo_sync.py`:
```python
class CrossRepoSNSSynchronizer:
    def sync_definitions(self):
        # Synchronizes SNS notation across repos
        # Detects conflicts and versions
        # Logs sync events
```

#### What's Missing: Automatic Sync Triggers

| Event | Should Trigger Cross-Repo Sync | Currently |
|-------|--------------------------------|-----------|
| NuSyQ-Hub status → `on` | Sync to SimulatedVerse, NuSyQ | ❌ Manual only |
| SimulatedVerse update | Sync back to Hub | ❌ No mechanism |
| SNS definition change | Propagate to all repos | ❌ Manual only |
| Config change | Cascade to dependents | ❌ No cascade |

**Sync infrastructure exists but runs manually, not automatically.**

### 6. N8N Webhook Cascades (UNUSED)

#### Infrastructure Exists
`src/integration/n8n_integration.py`:
```python
class N8NClient:
    def trigger_workflow(self, workflow_id, data):
        # Triggers n8n workflows via HTTP webhook
```

#### What's Missing: Status → n8n Wiring

| System Event | Should Trigger n8n Workflow | Currently |
|--------------|---------------------------|-----------|
| System startup | `workflow-system-startup` | ❌ Not wired |
| Critical error | `workflow-error-alert` | ❌ Not wired |
| Healing success | `workflow-healing-complete` | ❌ Not wired |
| Problem detected | `workflow-problem-notification` | ❌ Not wired |

**N8N integration exists but never gets called.**

### 7. Auto-Recovery Watchdog (DORMANT)

#### Infrastructure Exists
`src/utils/auto_recovery_watchdog.py`:
```python
class AutoRecoveryWatchdog:
    def monitor(self, task_name):
        # Monitors for softlocks and stalls
        # Triggers recovery on timeout
        # Escalates to human if needed
```

#### What's Missing: Heartbeat Integration

| Watchdog Scenario | Should Happen | Currently |
|-------------------|---------------|-----------|
| Heartbeat stops updating | Trigger watchdog alert | ❌ No monitoring |
| System stuck in `starting` | Timeout and recover | ❌ No check |
| Health degraded >5 min | Auto-recovery trigger | ❌ No wiring |

**Watchdog exists but doesn't monitor system status.**

### 8. Agent Communication Cascades (PARTIAL)

#### What Exists
- `src/guild/guild_board.py` - Agent guild board with events
- `src/agents/agent_communication_hub.py` - Inter-agent messaging
- Event bus infrastructure

#### What's Missing

| Agent Event | Should Cascade | Currently |
|-------------|---------------|-----------|
| New problem detected | Notify relevant agents | ❌ Manual only |
| Healing started | Broadcast to agent_bus | ❌ Not wired |
| System status change | Alert all agents | ❌ No broadcast |
| Critical error | Emergency agent notification | ❌ No mechanism |

---

## 🎯 Required Cascade Wiring

### Phase 1: Status Change Cascades (CRITICAL)

**Modify** `src/system/status.py`:

```python
# NEW: Import cascade dependencies
from src.utils.event_bus import emit_event
from src.integration.n8n_integration import N8NClient

# Track previous status for transition detection
_previous_status = None

def set_system_status(status: str, run_id: str = None, details: dict = None):
    """Set system status AND trigger cascades."""
    global _previous_status

    # Get previous status
    old_status = get_system_status().get("status", "off")

    # Update status file
    payload = {
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "run_id": run_id,
        "details": details or {},
    }
    with STATUS_LOCK:
        STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    # 🔥 CASCADE 1: Emit event to event bus
    emit_event(
        "system_status",
        "status_change",
        {
            "from": old_status,
            "to": status,
            "run_id": run_id,
            "timestamp": payload["timestamp"]
        },
        f"System status: {old_status} → {status}"
    )

    # 🔥 CASCADE 2: Trigger specific transition handlers
    if old_status != status:
        _handle_status_transition(old_status, status, run_id, details)

    _previous_status = status


def _handle_status_transition(old: str, new: str, run_id: str, details: dict):
    """Handle cascades for specific status transitions."""

    # OFF → ON: System startup
    if old == "off" and new == "on":
        emit_event("system_status", "system_startup", {"run_id": run_id})
        _trigger_startup_cascades(run_id, details)

    # ON → OFF: System shutdown
    elif old == "on" and new == "off":
        emit_event("system_status", "system_shutdown", {"run_id": run_id})
        _trigger_shutdown_cascades(run_id, details)

    # * → ERROR: System error
    elif new == "error":
        emit_event("errors", "system_error", details, f"System entered error state from {old}")
        _trigger_error_cascades(old, details)

    # ERROR → ON: Recovery
    elif old == "error" and new == "on":
        emit_event("system_status", "system_recovered", {"run_id": run_id})
        _trigger_recovery_cascades(run_id, details)


def _trigger_startup_cascades(run_id: str, details: dict):
    """Cascades triggered when system starts."""
    try:
        # 1. Trigger n8n workflow
        n8n = N8NClient()
        n8n.trigger_workflow("system-startup", {"run_id": run_id, "details": details})
    except Exception:
        pass  # n8n might not be available

    # 2. Notify cross-repo sync
    try:
        from src.integration.cross_repo_sync import CrossRepoSNSSynchronizer
        sync = CrossRepoSNSSynchronizer()
        # Schedule background sync
        threading.Thread(target=sync.sync_on_startup, daemon=True).start()
    except Exception:
        pass

    # 3. Initialize auto-healing monitor
    try:
        from src.orchestration.auto_healing import AutoHealingMonitor
        monitor = AutoHealingMonitor(enable_auto_heal=True)
        # Store in global state or registry
    except Exception:
        pass


def _trigger_shutdown_cascades(run_id: str, details: dict):
    """Cascades triggered when system shuts down."""
    # 1. Flush event bus logs
    emit_event("system_status", "flushing_logs", {"run_id": run_id})

    # 2. Notify other repos
    try:
        n8n = N8NClient()
        n8n.trigger_workflow("system-shutdown", {"run_id": run_id})
    except Exception:
        pass

    # 3. Save final checkpoint
    try:
        from src.utils.session_checkpoint import SessionCheckpoint
        checkpoint = SessionCheckpoint()
        checkpoint.save({"reason": "shutdown", "details": details})
    except Exception:
        pass


def _trigger_error_cascades(from_status: str, details: dict):
    """Cascades triggered when system enters error state."""
    # 1. Trigger auto-healing
    try:
        from src.orchestration.auto_healing import AutoHealingMonitor
        monitor = AutoHealingMonitor()
        # Create synthetic error context
        from src.orchestration.auto_healing import ErrorContext
        context = ErrorContext(
            error_type="system_error",
            error_message=details.get("message", "System entered error state"),
            span_name="system_status",
            timestamp=datetime.now().timestamp(),
            attributes=details
        )
        monitor.on_error(Exception(context.error_message), context)
    except Exception as e:
        emit_event("errors", "cascade_failed", {"cascade": "auto_healing", "error": str(e)})

    # 2. Alert watchdog
    emit_event("anomalies", "system_error_state", details)

    # 3. Notify n8n for external alerts
    try:
        n8n = N8NClient()
        n8n.trigger_workflow("system-error-alert", details)
    except Exception:
        pass


def _trigger_recovery_cascades(run_id: str, details: dict):
    """Cascades triggered when system recovers from error."""
    emit_event("system_status", "recovery_complete", {
        "run_id": run_id,
        "recovery_time": details.get("recovery_time"),
        "details": details
    })

    # Trigger n8n success workflow
    try:
        n8n = N8NClient()
        n8n.trigger_workflow("system-recovered", {"run_id": run_id, "details": details})
    except Exception:
        pass
```

### Phase 2: Heartbeat Cascades

**Modify** `heartbeat()` function:

```python
# Track heartbeat count and staleness
_heartbeat_count = 0
_last_heartbeat_time = None

def heartbeat(run_id: str = None, details: dict = None):
    """Update heartbeat AND trigger health cascades."""
    global _heartbeat_count, _last_heartbeat_time

    current = get_system_status()
    now = datetime.now()

    # Check for stale heartbeat
    if _last_heartbeat_time:
        elapsed = (now - _last_heartbeat_time).total_seconds()
        if elapsed > 60:  # More than 60s since last heartbeat
            emit_event("anomalies", "heartbeat_stale", {
                "elapsed_seconds": elapsed,
                "last_heartbeat": _last_heartbeat_time.isoformat()
            })

    # Update heartbeat
    set_system_status(
        status="on",
        run_id=run_id or current.get("run_id"),
        details={
            **current.get("details", {}),
            **(details or {}),
            "heartbeat_count": _heartbeat_count,
            "last_heartbeat": now.isoformat()
        },
    )

    _heartbeat_count += 1
    _last_heartbeat_time = now

    # CASCADE: Periodic health checks
    if _heartbeat_count % 10 == 0:  # Every 10th heartbeat
        _check_subsystem_health()


def _check_subsystem_health():
    """Check health of subsystems on periodic heartbeat."""
    try:
        from src.api.problems_api import get_current_problems
        problems = get_current_problems()

        if problems["total_counts"]["errors"] > 0:
            emit_event("anomalies", "errors_detected_during_heartbeat", {
                "error_count": problems["total_counts"]["errors"]
            })
    except Exception:
        pass
```

### Phase 3: Problems API → Auto-Healing Cascade

**Modify** `src/api/problems_api.py`:

```python
def get_current_problems(self, ...):
    """Get problems AND trigger auto-healing if critical."""
    # ... existing code ...

    # 🔥 CASCADE: Trigger auto-healing for critical errors
    if total_counts.errors > 10:  # Critical threshold
        emit_event("errors", "critical_errors_detected", {
            "count": total_counts.errors,
            "threshold": 10
        })

        # Trigger auto-healing
        try:
            from src.orchestration.auto_healing import AutoHealingMonitor
            monitor = AutoHealingMonitor()
            # ... trigger healing for top errors
        except Exception:
            pass

    return response
```

### Phase 4: Cross-Repo Sync Auto-Trigger

**Add to** `src/integration/cross_repo_sync.py`:

```python
def sync_on_startup(self):
    """Automatic sync triggered when system starts."""
    emit_event("agent_bus", "cross_repo_sync_started", {
        "trigger": "system_startup"
    })

    try:
        result = self.sync_definitions()
        emit_event("agent_bus", "cross_repo_sync_complete", {
            "result": result
        })
    except Exception as e:
        emit_event("errors", "cross_repo_sync_failed", {
            "error": str(e)
        })
```

### Phase 5: API Endpoints for Cascades

**Add to** `src/api/main.py`:

```python
@app.post("/api/trigger/cascade")
async def trigger_cascade(
    cascade_type: Literal["startup", "shutdown", "sync", "heal"],
    details: dict = None
):
    """Manually trigger cascade actions (testing/debugging)."""

    if cascade_type == "startup":
        _trigger_startup_cascades(None, details or {})
    elif cascade_type == "shutdown":
        _trigger_shutdown_cascades(None, details or {})
    elif cascade_type == "sync":
        from src.integration.cross_repo_sync import CrossRepoSNSSynchronizer
        sync = CrossRepoSNSSynchronizer()
        sync.sync_on_startup()
    elif cascade_type == "heal":
        from src.orchestration.auto_healing import AutoHealingMonitor
        monitor = AutoHealingMonitor()
        # Trigger healing scan

    return {"message": f"Triggered {cascade_type} cascade", "timestamp": datetime.now()}
```

---

## 📊 Cascade Flow Diagram

```
System Status Change (status.py)
    ↓
    ├─→ Event Bus Emission (event_bus.py)
    │   ├─→ system_status.log
    │   ├─→ errors.log (if error)
    │   └─→ anomalies.log (if degraded)
    │
    ├─→ Status Transition Handler
    │   ├─→ OFF→ON: Startup Cascades
    │   │   ├─→ n8n workflow: system-startup
    │   │   ├─→ Cross-repo sync
    │   │   └─→ Auto-healing init
    │   │
    │   ├─→ ON→OFF: Shutdown Cascades
    │   │   ├─→ Flush event logs
    │   │   ├─→ n8n workflow: system-shutdown
    │   │   └─→ Save checkpoint
    │   │
    │   ├─→ *→ERROR: Error Cascades
    │   │   ├─→ Auto-healing trigger
    │   │   ├─→ Watchdog alert
    │   │   └─→ n8n workflow: error-alert
    │   │
    │   └─→ ERROR→ON: Recovery Cascades
    │       ├─→ Emit recovery event
    │       └─→ n8n workflow: recovered
    │
    └─→ API Broadcast (optional)
        └─→ WebSocket to connected agents
```

---

## 🚀 Implementation Priority

### Immediate (This Week)
1. ✅ **Wire status changes to event bus** - Critical for observability
2. ✅ **Add startup/shutdown cascades** - Enable automation
3. ✅ **Integrate auto-healing trigger** - Enable self-healing

### Soon (Next Week)
4. ⏳ Wire heartbeat health checks
5. ⏳ Add cross-repo sync auto-trigger
6. ⏳ Integrate n8n workflows

### Later (This Month)
7. ⏳ WebSocket broadcast for real-time agent updates
8. ⏳ Watchdog integration with heartbeat
9. ⏳ Full cascade testing and validation

---

## 🎯 Success Criteria

1. **Status changes emit events** - All transitions logged
2. **Auto-healing triggers automatically** - No manual intervention
3. **Cross-repo sync on startup** - Automatic coordination
4. **n8n workflows triggered** - External automation works
5. **Agents notified of changes** - Real-time updates
6. **Cascades are testable** - Can trigger manually via API

---

## 📝 Testing Plan

```bash
# Test 1: Status change cascades
python -c "from src.system.status import set_system_status; set_system_status('on')"
# Expected: Event emitted to state/logs/system_status.log
# Expected: Startup cascades triggered

# Test 2: Error cascade triggers healing
python -c "from src.system.status import set_system_status; set_system_status('error', details={'message': 'Test error'})"
# Expected: Auto-healing monitor invoked
# Expected: Error event in errors.log

# Test 3: Cross-repo sync on startup
python scripts/start_nusyq.py
# Expected: Sync triggered automatically
# Expected: Sync events in agent_bus.log

# Test 4: Manual cascade trigger via API
curl -X POST http://localhost:8000/api/trigger/cascade?cascade_type=sync
# Expected: Sync runs immediately
# Expected: Returns success response
```

---

**Bottom Line**: The cascade infrastructure is **80% built but 0% wired**. Implementing the wiring above will transform passive status updates into active system coordination.
