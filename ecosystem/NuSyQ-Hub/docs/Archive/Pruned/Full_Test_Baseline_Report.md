# Full NuSyQ-Hub Test Baseline Report
**Generated:** 2026-02-04 | **Execution Time:** 4 min 31 sec

## Summary Metrics

| Metric | Value | Status |
|--------|-------|--------|
| **Tests Collected** | 1,884 | ✓ Complete inventory |
| **Tests Passed** | 1,586 | ✓ 84.2% pass rate |
| **Tests Failed** | 3 | ⚠️ Needs fix |
| **Tests Skipped** | 56 | ℹ️ Intentional skips |
| **Coverage** | 24.24% | ❌ Below 30% threshold |
| **Duration** | 271.91s | ℹ️ ~4.5 minutes |

---

## Phase Breakdown

| Phase | Test Files | Tests | Status | Notes |
|-------|-----------|-------|--------|-------|
| **Phase 1** | Unknown | ~1,200+ | Mixed | Needs analysis |
| **Phase 2** | Unknown | ~600+ | Mixed | Needs analysis |
| **Phase 3** | 5 files | 92 | ✅ 100% Passing | 54.64% coverage (isolated) |

---

## Broken Tests (3 Failures)

### File: `tests/test_publishing_infrastructure.py`

#### 1. **TestPublishingOrchestrator::test_validate_config_missing_required**
- **Error:** `Failed: DID NOT RAISE <class 'ValueError'>`
- **Line:** tests/test_publishing_infrastructure.py:83
- **Issue:** Test expects `ValueError` to be raised when required config is missing, but validation is not enforcing it
- **Root:** `PublishingOrchestrator.validate_config()` missing validation logic

#### 2. **TestPyPIPublisher::test_setup_py_generation**
- **Error:** `TypeError: PyPIPublisher.__init__() missing 2 required positional arguments: 'project_path' and 'pypi_token'`
- **Line:** tests/test_publishing_infrastructure.py:129
- **Issue:** Test calls `PyPIPublisher()` with no arguments, but constructor requires `project_path` and `pypi_token`
- **Root:** Test fixture/mock not providing required args

#### 3. **TestPyPIPublisher::test_pyproject_toml_generation**
- **Error:** Same as #2 - `TypeError: PyPIPublisher.__init__() missing 2 required positional arguments`
- **Line:** tests/test_publishing_infrastructure.py:147
- **Issue:** Same constructor signature mismatch
- **Root:** Test fixture/mock not providing required args

---

## Coverage Analysis

**Overall Coverage: 24.24%** (Target: 30%)
- Phase 3 (isolated): **54.64%** ✓ Above target
- Phase 1-2 (integrated): **~15-20%** ❌ Below target
- Gap: **~5.76 percentage points** needed to reach 30% threshold

**Key Low-Coverage Areas:**
- `src/tools/agent_task_router.py` - 13% (501/3739 lines)
- `src/tools/maze_solver.py` - 11% (161/1439 lines)
- `src/tools/doc_sync_checker.py` - 9% (135/1479 lines)
- `src/publishing/` - Not well tested
- `src/orchestration/` - Partially tested

---

## Type/Pattern Analysis

### Warning Summary (6 warnings)
1. **PytestCollectionWarning** - `TestResult` class in test_orchestrator_cli.py (has __init__, shouldn't be test class)
2. **PytestReturnNotNoneWarning** - Multiple test functions returning values instead of using assertions
   - `test_culture_ship_smoke.py::test_culture_ship_health` returns dict
   - `test_event_bus_integration.py::test_orchestrator_event_emissions` returns bool
   - `test_event_bus_integration.py::test_router_event_emissions` returns bool
   - `test_event_bus_integration.py::test_event_bus_monitoring_integration` returns bool

### Deprecation Warnings
- `pygame.pkgdata` using deprecated `pkg_resources` API

---

## Immediate Action Items

### 🔴 Critical (Blocking 30% coverage target)
1. **Fix test_publishing_infrastructure.py** (3 failures)
   - Update PyPIPublisher constructor calls to include required arguments
   - Add validation enforcement to PublishingOrchestrator.validate_config()
   - Estimated: 10-15 minutes

### 🟡 High Priority (Better health signals)
1. **Add tests for Phase 1-2 core modules** (agent_task_router, maze_solver, etc.)
   - Current: 9-11% coverage in critical tools
   - Would add ~5-8 percentage points
   - Estimated: 30-45 minutes

2. **Fix test return value warnings** (4 tests)
   - Use assertions instead of returns
   - Estimated: 5 minutes

3. **Fix test class collection issue** (TestResult in test_orchestrator_cli.py)
   - Rename class or move out of test file
   - Estimated: 2 minutes

### 📊 Reporting & Documentation
- Phase 3 remains **isolated strong performer** (54.64%)
- Phase 1-2 inherited legacy has lower test coverage (24.24% overall)
- Coverage gap: 5.76 percentage points to reach 30% threshold

---

## Comparison: Phase 3 vs Full Suite

| Aspect | Phase 3 Only | Full Suite |
|--------|------------|-----------|
| Tests | 92 | 1,884 |
| Pass Rate | 100% | 84.2% |
| Coverage | 54.64% | 24.24% |
| Failures | 0 | 3 |
| Status | ✅ Excellent | ⚠️ Needs work |

**Conclusion:** Phase 3 generators are robust. Inherited Phase 1-2 tests need modernization and better coverage.

---

## Next Steps

### Recommended Sequence
1. **Fix 3 publishing tests** (10 min) → Unblock test suite
2. **Fix 4 return-value warnings** (5 min) → Clean up test patterns
3. **Consider Phase 1-2 test expansion** (future session) → Reach 30% threshold
4. **Proceed to Orchestrator Wiring** (#2) once baseline stabilized

---

**Baseline Established:** ✓ Honest metrics captured. Ready for targeted improvements.
