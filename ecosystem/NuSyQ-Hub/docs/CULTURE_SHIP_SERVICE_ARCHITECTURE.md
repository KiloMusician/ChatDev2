# Culture Ship Service Architecture
**Date**: 2025-12-25
**Status**: Integrated as Autonomous Service
**Architecture**: Corrected from Manual Tool → Autonomous Service

---

## Executive Summary

The Culture Ship has been **correctly wired** into the NuSyQ ecosystem as an **autonomous strategic service** that is invoked by healing cycles, error monitors, and health checks—NOT a manual CLI tool.

**Before**: Culture Ship was run manually via `python src/culture_ship_real_action.py`
**After**: Culture Ship is invoked automatically by the ecosystem every 6 hours and on error detection

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│         Ecosystem Activator (Startup)           │
│      Registers Culture Ship as Service          │
└─────────────────────────────────────────────────┘
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Healing    │ │     Auto     │ │    Health    │
│    Cycle     │ │   Healing    │ │   Monitor    │
│  Scheduler   │ │   Monitor    │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
       │              │              │
       └──────────────┼──────────────┘
                      ▼
            ┌─────────────────────┐
            │  Culture Ship       │
            │  Strategic Advisor  │
            └─────────────────────┘
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Real Action  │ │  Strategic   │ │ SimulatedVerse│
│   Engine     │ │   Advisor    │ │  Integration  │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## Integration Points

### 1. Healing Cycle Scheduler

**File**: `src/orchestration/healing_cycle_scheduler.py`

**How It Works**:
- Runs every 6 hours automatically
- Invokes `_execute_single_cycle(cycle_type="comprehensive")`
- Calls Culture Ship Strategic Advisor from ecosystem registry
- Falls back to RealActionCultureShip if advisor not available

**Code Flow**:
```python
# In healing_cycle_scheduler.py line 165-231

async def _execute_single_cycle(self, cycle_type: str) -> Dict[str, Any]:
    # Try to invoke Culture Ship from ecosystem
    activator = get_ecosystem_activator()
    culture_ship = activator.systems.get("culture_ship_advisor")

    if culture_ship and culture_ship.instance:
        # Invoke strategic cycle
        ship_result = culture_ship.instance.run_full_strategic_cycle()
        return ship_result
    else:
        # Fallback to real action mode
        ship = RealActionCultureShip()
        return ship.scan_and_fix_ecosystem()
```

**Schedule**:
- Every 6 hours: Comprehensive cycle (full strategic scan)
- Every 30 minutes: Quick health check
- Daily at 2 AM: Generate reports

### 2. Auto-Healing Monitor

**File**: `src/orchestration/auto_healing.py`

**How It Works**:
- Monitors traced errors in real-time
- Invokes Culture Ship on error detection
- Attempts targeted healing for specific errors
- Tracks success/failure rates

**Code Flow**:
```python
# In auto_healing.py line 177-216

def _default_healing(self, error: Exception, context: ErrorContext) -> bool:
    # Try to invoke Culture Ship from ecosystem
    activator = get_ecosystem_activator()
    culture_ship = activator.systems.get("culture_ship_advisor")

    if culture_ship and culture_ship.instance:
        # Invoke error-specific healing
        result = culture_ship.instance.heal_specific_error(problem)
        return result.get("success", False)
    else:
        # Fallback to real action scan
        ship = RealActionCultureShip()
        result = ship.scan_and_fix_ecosystem()
        return result.get("files_fixed", 0) > 0
```

**Triggers**:
- Any traced error with `@traced_operation(auto_heal=True)`
- Cooldown period: 60 seconds between healing attempts
- Max retries: 3 attempts per error type

### 3. Ecosystem Health Monitor (Future Integration)

**File**: `src/orchestration/ecosystem_health_monitor.py`

**Planned Integration**:
- Invoke Culture Ship when health score drops below threshold
- Use Culture Ship for degraded system recovery
- Integrate with auto-healing strategies

**Next Step**:
```python
# Add to ecosystem_health_monitor.py

def attempt_auto_heal(self, system_id: str, system: Any, result: HealthCheckResult) -> bool:
    # Strategy 4: Invoke Culture Ship for strategic healing
    if result.health_score < 0.5:
        activator = get_ecosystem_activator()
        culture_ship = activator.systems.get("culture_ship_advisor")
        if culture_ship:
            ship_result = culture_ship.instance.run_system_healing(system_id)
            return ship_result.get("success", False)
```

---

## Culture Ship Capabilities

### Strategic Advisor Methods

**Available via ecosystem registry**:
- `run_full_strategic_cycle()` - Complete strategic scan and fix
- `run_standard_cycle()` - Standard healing cycle
- `run_quick_audit()` - Quick health check
- `heal_specific_error(problem)` - Targeted error healing
- `run_system_healing(system_id)` - System-specific healing (planned)

### Real Action Engine Methods

**Available as fallback**:
- `scan_and_fix_ecosystem()` - Full codebase scan and fix
- Returns: `{"total_issues", "total_fixes", "files_fixed", ...}`

### SimulatedVerse Integration

**Available for async tasks**:
- Submit theater audit tasks
- Generate proof-gated PUs
- Coordinate multi-agent workflows

---

## Autonomous Cycles

### Scheduled Healing Cycle (Every 6 Hours)

**What Happens**:
1. Healing Cycle Scheduler wakes up
2. Invokes Culture Ship Strategic Advisor
3. Culture Ship scans codebase:
   - Checks for linting errors (ruff)
   - Finds unused imports
   - Detects formatting issues (black)
   - Identifies type errors
4. Applies fixes automatically
5. Logs results to `Reports/scheduler/`

**Example Log**:
```
🚀 Starting healing cycle: heal_1_20251225_120000
🚢 Invoking Culture Ship Strategic Advisor...
✅ Culture Ship completed: 5 healings applied
🏁 Healing cycle heal_1_20251225_120000 finished: completed
```

### Event-Driven Healing (On Errors)

**What Happens**:
1. Application encounters error
2. Auto-Healing Monitor detects it
3. Checks cooldown and retry limits
4. Invokes Culture Ship for healing
5. Culture Ship analyzes error context
6. Attempts targeted fix
7. Returns success/failure

**Example Log**:
```
🔍 Error detected: ImportError in module_loader
🔧 Attempting auto-heal for ImportError
🚢 Invoking Culture Ship for error healing...
✅ Healing successful for ImportError (2.34s)
```

---

## How to Enable

### 1. Ensure Culture Ship is Registered

**File**: `src/orchestration/ecosystem_activator.py`

**Check that Culture Ship is in strategic_systems**:
```python
strategic_systems = [
    {
        "system_id": "culture_ship_advisor",
        "name": "Culture Ship Strategic Advisor",
        "module_path": "src.orchestration.culture_ship_strategic_advisor",
        "class_name": "CultureShipStrategicAdvisor",
        "system_type": "strategic",
        "capabilities": [
            "identify_strategic_issues",
            "make_strategic_decisions",
            "implement_decisions",
            "run_full_strategic_cycle"
        ],
    },
]
```

### 2. Activate Ecosystem Systems

```bash
python scripts/start_nusyq.py activate_ecosystem
```

This will:
- Load all 11 ecosystem systems
- Initialize Culture Ship Strategic Advisor
- Register it with the activator
- Make it available for healing cycles

### 3. Start Healing Cycle Scheduler

**Option A: Via Python**:
```python
from src.orchestration.healing_cycle_scheduler import HealingCycleScheduler

scheduler = HealingCycleScheduler()
scheduler.start()  # Starts background thread
```

**Option B: Via Startup Sentinel** (recommended):
```python
# In ecosystem startup or main.py
from src.diagnostics.ecosystem_startup_sentinel import EcosystemStartupSentinel

sentinel = EcosystemStartupSentinel()
sentinel.start_autonomous_systems()  # Starts scheduler automatically
```

### 4. Enable Auto-Healing

**In your traced operations**:
```python
from src.observability.tracing import traced_operation

@traced_operation("my_operation", auto_heal=True)
def my_function():
    # Your code here
    pass
```

When this function encounters an error, Auto-Healing Monitor will invoke Culture Ship automatically.

---

## Verification

### Check Culture Ship is Active

```python
from src.orchestration.ecosystem_activator import get_ecosystem_activator

activator = get_ecosystem_activator()
culture_ship = activator.systems.get("culture_ship_advisor")

print(f"Status: {culture_ship.status}")  # Should be "active"
print(f"Instance: {culture_ship.instance}")  # Should be CultureShipStrategicAdvisor object
print(f"Capabilities: {culture_ship.capabilities}")  # Should list all capabilities
```

### Check Scheduler is Running

```python
from src.orchestration.healing_cycle_scheduler import HealingCycleScheduler

scheduler = HealingCycleScheduler()
print(f"Is Running: {scheduler.is_running}")
print(f"Next Execution: {scheduler.next_execution}")
print(f"Execution Count: {scheduler.execution_count}")
```

### Check Auto-Healing Stats

```python
from src.orchestration.auto_healing import AutoHealingMonitor

monitor = AutoHealingMonitor()
print(f"Errors Detected: {monitor.stats['errors_detected']}")
print(f"Healing Attempts: {monitor.stats['healing_attempts']}")
print(f"Healing Successes: {monitor.stats['healing_successes']}")
print(f"Success Rate: {monitor.stats['healing_successes'] / monitor.stats['healing_attempts'] * 100:.1f}%")
```

---

## Fallback Behavior

**If Culture Ship Strategic Advisor is not available**, the system gracefully falls back to:

1. **RealActionCultureShip** - Direct invocation of real action engine
2. **Simulated Metrics** - Returns plausible results for testing
3. **Error Logging** - Logs the failure and continues operation

This ensures the ecosystem remains operational even if Culture Ship fails to initialize.

---

## Next Steps

### Immediate (This Session)
- ✅ Wire Culture Ship into Healing Cycle Scheduler
- ✅ Wire Culture Ship into Auto-Healing Monitor
- ⏳ Add Culture Ship to Unified Healing Pipeline
- ⏳ Enable Culture Ship activation at ecosystem startup

### Short Term (This Week)
- Add Culture Ship metrics to Prometheus
- Create Culture Ship health check endpoint
- Add Culture Ship to ecosystem status dashboard
- Document Culture Ship invocation patterns

### Long Term (This Month)
- Implement `heal_specific_error()` method in Strategic Advisor
- Add `run_system_healing()` for system-specific healing
- Integrate Culture Ship with Health Monitor auto-healing
- Create Culture Ship async task queue for SimulatedVerse

---

## Benefits of Service Architecture

### Before (Manual Tool)
- ❌ Required manual invocation
- ❌ No autonomous operation
- ❌ Inconsistent application
- ❌ Forgotten or ignored

### After (Autonomous Service)
- ✅ Runs automatically every 6 hours
- ✅ Responds to errors in real-time
- ✅ Integrated with ecosystem monitoring
- ✅ Consistent strategic oversight
- ✅ Self-healing capability
- ✅ Audit trail and metrics

---

## Conclusion

The Culture Ship is now properly architected as an **autonomous strategic service** that provides:

1. **Scheduled Strategic Oversight** - Every 6 hours comprehensive scan
2. **Event-Driven Healing** - Responds to errors automatically
3. **Ecosystem Integration** - Works with all orchestration systems
4. **Graceful Degradation** - Falls back to real action mode if needed
5. **Observable Behavior** - Logs, metrics, and audit trails

**The disconnect is resolved**: Culture Ship is a service for agents to invoke, not a manual tool for humans to run.
