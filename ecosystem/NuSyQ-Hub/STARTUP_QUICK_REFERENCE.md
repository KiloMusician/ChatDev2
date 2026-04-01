# 🚀 NuSyQ-Hub Startup Quick Reference

## Instant Health Check

```powershell
python -m src.diagnostics.ecosystem_startup_sentinel
```

## Current Ecosystem Status

| System                   | Auto-Start | Status       | Issue                         |
| ------------------------ | ---------- | ------------ | ----------------------------- |
| 🎯 Performance Monitor   | ✅ Yes     | 🔴 DORMANT   | Import error: relative import |
| 🏗️ Architecture Watcher  | ✅ Yes     | 🔴 DORMANT   | Scanner not found             |
| 📡 Context Monitor       | ✅ Yes     | 🔴 DORMANT   | Cannot import ContextMonitor  |
| 🤖 Multi-AI Orchestrator | ❌ No      | 🟢 AVAILABLE | On-demand (expected)          |
| ⚛️ Quantum Workflow      | ❌ No      | 🟢 AVAILABLE | On-demand (expected)          |
| 🎮 RPG Inventory         | ✅ Yes     | 🟢 ACTIVE    | ✅ Working correctly          |

**Health Score**: 16.7% (1/6 active) 🔴

## Fix Priorities

### 1️⃣ CRITICAL - Fix Import Errors

**File**: `src/diagnostics/performance_monitor.py`  
**Line**: Find relative imports (`from ..utils import ...`)  
**Fix**: Convert to `from src.utils import ...`

**File**: `src/real_time_context_monitor.py`  
**Line**: Check class definition  
**Fix**: Ensure `class ContextMonitor:` exists or fix import name

### 2️⃣ CRITICAL - Restore Missing Component

**File**: `src/core/ArchitectureScanner.py` (missing)  
**Action**:

```powershell
# Search for file
git log --all --full-history --source -- "**/ArchitectureScanner.py"

# Or recreate if lost
grep -r "ArchitectureScanner" src/
```

### 3️⃣ VALIDATE - Re-Run Health Check

After fixes:

```powershell
python -m src.diagnostics.ecosystem_startup_sentinel
```

Target: **>70% health score** (4+ systems active)

## One-Command Activation

### Start All Systems (After Fixes)

```powershell
# Performance Monitor
Start-Process python -ArgumentList "-m", "src.diagnostics.performance_monitor" -NoNewWindow

# Architecture Watcher
Start-Process python -ArgumentList "-m", "src.core.ArchitectureWatcher" -NoNewWindow

# Context Monitor
Start-Process python -ArgumentList "-m", "src.real_time_context_monitor" -NoNewWindow

# RPG Inventory (auto-starts with sentinel)
# python -m src.Rosetta_Quest_System.rpg_inventory
```

### Start On-Demand Systems

```powershell
# Multi-AI Orchestrator (heavy workflows)
python -m src.orchestration.multi_ai_orchestrator --mode=orchestration

# Quantum Workflow (quest-triggered automation)
python -m src.workflows.quantum_workflow_automation
```

## Automatic Startup (VS Code)

✅ **Already Configured!**  
Task runs on `folderOpen` event in `.vscode/tasks.json`

Disable if unwanted:

```json
// Remove this from task definition:
"runOptions": {
  "runOn": "folderOpen"
}
```

## Troubleshooting Commands

### Check System Processes

```powershell
# Find running Python monitors
Get-Process python | Where-Object {$_.CommandLine -like "*monitor*"}
```

### View Startup Logs

```powershell
# Check sentinel output
cat data/ecosystem_startup_status.json | jq
```

### Manual System Test

```python
# Test Performance Monitor
from src.diagnostics.performance_monitor import PerformanceMonitor
monitor = PerformanceMonitor()
monitor.start()

# Test RPG System (working example)
from src.Rosetta_Quest_System.rpg_inventory import RPGSystem
rpg = RPGSystem()
rpg.check_capability("healing_protocols")
```

## Expected Behavior (After Fixes)

### On Workspace Open

1. **Ecosystem Startup Sentinel** runs automatically
2. Checks 6 systems, starts 4 auto-start systems
3. Reports health score to console
4. Saves status to `data/ecosystem_startup_status.json`
5. ✅ Shows "Ecosystem Ready" if score >70%

### Continuous Operation

- **Performance Monitor**: Background process tracking resource usage
- **Architecture Watcher**: Monitors file changes, updates structure
- **Context Monitor**: Generates AI context on code modifications
- **RPG Inventory**: Maintains capability catalog, auto-heals issues

### On-Demand Activation

- **Multi-AI Orchestrator**: Activate when coordinating >2 AI systems
- **Quantum Workflow**: Activate for complex multi-step automation

## Recovery Protocol

If ecosystem health <50%:

1. Run: `python src/healing/repository_health_restorer.py`
2. Run: `python src/diagnostics/system_health_assessor.py`
3. Check output roadmap for specific fixes
4. Re-run sentinel after repairs

## Related Files

- **Sentinel Implementation**: `src/diagnostics/ecosystem_startup_sentinel.py`
- **Full Documentation**: `docs/ECOSYSTEM_STARTUP_AUTOMATION.md`
- **VS Code Tasks**: `.vscode/tasks.json` (line 113+)
- **Healing Protocols**: `src/protocols/healing_protocols.py`

---

**Quick Status Check**: `python -m src.diagnostics.ecosystem_startup_sentinel`  
**Target Health**: 70%+ (4+ systems active)  
**Current Health**: 50.0% (3 systems active) � **IMPROVED!**  
**Last Update**: 2025-10-15 02:37 UTC
