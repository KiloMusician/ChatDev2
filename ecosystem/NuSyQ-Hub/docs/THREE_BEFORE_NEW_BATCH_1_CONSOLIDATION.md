# Three Before New - Batch 1: Health Check Consolidation

**Date:** 2026-01-04  
**Objective:** Consolidate 10 duplicate health check tools into 1-2 canonical
implementations  
**Expected Impact:** Reduce tool count by 8, improve compliance from 0% → 8%

## Problem Analysis

**Discovery Results:** Found **10 health check tools** doing similar work:

### Tier 1: Redundant implementations (DELETE after migration)

1. `scripts/tmp_sim_health_check.py` - Temporary tool, should be removed
2. `scripts/health_dashboard.py` - Redundant with system status reporting
3. `scripts/daily_health_cycle.py` - Overlaps with orchestration system

### Tier 2: Consolidate into canonical tool

4. `scripts/integration_health_check.py` - JSON output, good for automation
5. `scripts/quick_health_check.py` - Fast pre-commit checks
6. `scripts/startup_with_health_check.py` - Startup wrapper

**Canonical Target:** Enhance `scripts/integration_health_check.py` to handle
all use cases

### Tier 3: Keep (specialized purposes)

7. `src/healthcheck_server.py` - HTTP endpoint for Docker (specialized)
8. `src/diagnostics/ImportHealthCheck.ps1` - PowerShell import-specific
   (specialized)
9. `src/utils/import_health_checker.py` - Python import validation (specialized)
10. `scripts/check_integrations.py` - Integration-specific checks (specialized)

## Consolidation Plan

### Phase 1: Document existing capabilities (CURRENT)

- [x] Run discovery to find all health check tools
- [x] Categorize by redundancy tier
- [ ] Log to quest system with Three Before New justification

### Phase 2: Create unified health checker

- [ ] Enhance `scripts/integration_health_check.py` with:
  - Fast mode (for pre-commit, <30s)
  - Full mode (comprehensive, ~2min)
  - JSON output (for automation)
  - Human output (for terminals)
  - Startup wrapper mode (for boot checks)

### Phase 3: Migrate users

- [ ] Update all references to deleted tools
- [ ] Update documentation
- [ ] Update VS Code tasks
- [ ] Test migration

### Phase 4: Remove redundant tools

- [ ] Delete `tmp_sim_health_check.py`
- [ ] Delete `health_dashboard.py`
- [ ] Delete `daily_health_cycle.py`
- [ ] Delete `quick_health_check.py`
- [ ] Delete `startup_with_health_check.py`

### Phase 5: Document compliance

- [ ] Log consolidation to quest system
- [ ] Update metrics dashboard
- [ ] Verify compliance rate increased

## Expected Outcome

**Before:**

- 10 health check tools
- 0% Three Before New compliance
- High maintenance burden
- Developer confusion ("which one do I use?")

**After:**

- 5 tools (1 canonical + 4 specialized)
- 5 tools consolidated (compliance improvement)
- Clear ownership and purpose
- Single source of truth for health checking

## Three Before New Compliance Log

```python
from src.Rosetta_Quest_System.quest_engine import log_three_before_new

log_three_before_new(
    tool_name="Consolidated health checking (removed 5 duplicates)",
    capability="health check, system status, diagnostic reporting",
    candidates=[
        {"path": "scripts/integration_health_check.py", "notes": "CANONICAL - enhanced"},
        {"path": "scripts/quick_health_check.py", "notes": "Merged into canonical"},
        {"path": "scripts/startup_with_health_check.py", "notes": "Merged into canonical"},
        {"path": "scripts/tmp_sim_health_check.py", "notes": "Deleted (temporary)"},
        {"path": "scripts/health_dashboard.py", "notes": "Deleted (redundant)"},
        {"path": "scripts/daily_health_cycle.py", "notes": "Deleted (redundant)"},
    ],
    justification="Consolidating 6 redundant health check tools into 1 canonical implementation. Specialized tools (HTTP server, import checkers) retained for their specific use cases."
)
```

## Next Batches (Pipeline)

**Batch 2:** Error reporting consolidation (12+ tools found)  
**Batch 3:** Test runner consolidation (9+ tools found)  
**Batch 4:** Import fixer consolidation (12+ tools found)  
**Batch 5:** Orchestrator consolidation (5+ tools found)

---

**Status:** Planning complete, ready to execute Phase 2
