# Phase 3: Health & Diagnostics Consolidation Plan

**Status:** Active  
**Canonical Health Module:** `src/diagnostics/integrated_health_orchestrator.py`
(+ supporting modules)  
**Affected Files:** 40+ legacy health/diagnostic files  
**Approach:** Redirect bridges + import validation

---

## 🎯 Phase 3 Consolidation Strategy

### Tier 1: Canonical Health Modules (KEEP - No Redirect Needed)

These modules form the backbone of health diagnostics:

1. **`src/diagnostics/integrated_health_orchestrator.py`**

   - Master orchestrator connecting diagnostics → AI coordination → healing
   - Integrates: `ActionableIntelligenceAgent` + `MultiAIOrchestrator` +
     `QuantumProblemResolver`
   - Entry point for all health operations

2. **`src/diagnostics/system_health_assessor.py`**

   - Core health assessment engine
   - Provides: `SystemHealthAssessment` dataclass + assessment logic
   - No dependencies on other health modules

3. **`src/diagnostics/health_grading_system.py`**

   - Health scoring + grade assignment (A-F scale)
   - Pure computation, no orchestration required
   - Dependency: `SystemHealthAssessment`

4. **`src/diagnostics/health_monitor_daemon.py`**

   - Continuous monitoring + background health checks
   - Dependency: `SystemHealthAssessor` + `HealthGradeSystem`
   - Can run as background task

5. **`src/diagnostics/health_cli.py`**
   - CLI interface to health system
   - Dependency: `IntegratedHealthOrchestrator`
   - Entry point for command-line operations

### Tier 2: Legacy Health Files → Redirect Bridges

**Redirect targets:** Legacy files that appear to duplicate or partially overlap
Tier 1

| Legacy File                     | Purpose                | Canonical Target                    | Action                                  |
| ------------------------------- | ---------------------- | ----------------------------------- | --------------------------------------- |
| `audit_full.txt`                | Audit output (static)  | `state/reports/`                    | Move to archive, reference from current |
| `quick_system_analysis.py`      | Quick diagnostics      | `system_health_assessor.py`         | Create redirect wrapper                 |
| `health_monitor.py`             | Monitoring (if exists) | `health_monitor_daemon.py`          | Create redirect wrapper                 |
| `diagnostics_daemon.py`         | Background diagnostics | `integrated_health_orchestrator.py` | Create redirect wrapper                 |
| Any `*_health*.py` in root      | Health-related files   | `src/diagnostics/`                  | Create redirect wrapper                 |
| Any `*_diagnostics*.py` in root | Diagnostic-related     | `src/diagnostics/`                  | Create redirect wrapper                 |

---

## 📋 Implementation Steps (In Order)

### Step 1: Identify All Legacy Health Files

**Command:**

```bash
find . -name "*health*" -o -name "*diagnostic*" -o -name "*audit*" | grep -v ".git" | sort
```

**Expected output:** List of all 40+ files to consolidate

### Step 2: Create Redirect Bridge Templates

For each legacy file identified, create a redirect bridge:

```python
# Legacy file: old_module.py
# REDIRECT: This module is deprecated. Use the canonical health system instead.
#
# Old import:  from old_module import SomeClass
# New import:  from src.diagnostics.integrated_health_orchestrator import IntegratedHealthOrchestrator
#
# See: docs/Phase_3_Health_Consolidation_Plan.md

import warnings
from src.diagnostics.integrated_health_orchestrator import IntegratedHealthOrchestrator

warnings.warn(
    f"{__name__} is deprecated. Use src.diagnostics.integrated_health_orchestrator instead.",
    DeprecationWarning,
    stacklevel=2
)

# Provide backward-compatible API
__all__ = ["IntegratedHealthOrchestrator"]
```

### Step 3: Verify All Imports in Codebase

**Goal:** Ensure no code imports from legacy health modules

**Command:**

```bash
grep -r "from.*audit\|from.*health\|from.*diagnostic" src/ --include="*.py" | grep -v "src/diagnostics" | sort
```

**Expected:** No matches (or only legitimate imports from `src/diagnostics/`)

### Step 4: Consolidate Documentation

- Gather all legacy health docs into
  `docs/Phase_3_Health_Consolidation_Archive/`
- Create unified health system documentation in `docs/Health_System_Guide.md`
- Update main README.md to reference consolidated health system

### Step 5: Create Health Module Index

**File:** `src/diagnostics/README.md`

```markdown
# Health & Diagnostics Module Index

## Core Modules

- `integrated_health_orchestrator.py` - Master orchestrator
- `system_health_assessor.py` - Assessment engine
- `health_grading_system.py` - Scoring + grading
- `health_monitor_daemon.py` - Continuous monitoring
- `health_cli.py` - CLI interface

## Supporting Modules

- `actionable_intelligence_agent.py` - AI-driven diagnostics
- ...others...

## Legacy Redirects (Deprecated)

See `docs/Phase_3_Health_Consolidation_Plan.md` for legacy file mappings.
```

### Step 6: Run Validation Tests

**Test 1: Import validation**

```python
# src/diagnostics/test_health_consolidation.py
from src.diagnostics.integrated_health_orchestrator import IntegratedHealthOrchestrator
from src.diagnostics.system_health_assessor import SystemHealthAssessment
from src.diagnostics.health_grading_system import HealthGrade
from src.diagnostics.health_monitor_daemon import HealthMonitorDaemon
from src.diagnostics.health_cli import main as health_main

assert all([IntegratedHealthOrchestrator, SystemHealthAssessment, HealthGrade, HealthMonitorDaemon, health_main])
print("✅ All 5 canonical health modules import successfully")
```

**Test 2: Circular dependency check**

```bash
python -m pydeps src/diagnostics --exclude src.tests --show-dependencies
```

---

## 🚦 Success Criteria

- [x] Identify canonical health modules (Tier 1)
- [ ] Map legacy files to canonical targets (Tier 2)
- [ ] Create redirect bridges for all legacy imports
- [ ] Run import validation across codebase
- [ ] Move legacy files to archive (or keep with deprecation warnings)
- [ ] Update documentation with unified health system guide
- [ ] Run pytest on health module tests
- [ ] Commit consolidation with summary message

---

## 📊 Expected Outcome

**Before:** 40+ scattered health/diagnostic files  
**After:** 5 canonical modules + 35+ redirect bridges/archives  
**Benefit:** Clear dependency graph, easier to maintain, no circular imports

---

## References

- Phase 1 (Logging): `docs/Phase_1_Logging_Consolidation_Summary.md` ✅
- Phase 2 (Orchestration): `docs/Phase_2_Orchestration_Consolidation_Summary.md`
  ✅
- Phase 3 (Health): `docs/Phase_3_Health_Consolidation_Plan.md` (this file)
- Phase 4 (Agents): `docs/Phase_4_Agent_Consolidation_Plan.md` (planned)
