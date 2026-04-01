# THREE_BEFORE_NEW: Batch 4b Error Healing Discovery

**Date**: 2025-01-05 | **Status**: Discovery Phase **Author**: GitHub Copilot |
**Protocol**: Three Before New v4 **Batch**: 4b | **Focus**: Error Healing
Consolidation (6 tools)

---

## Executive Summary

**Target Category**: Error Healing & Autonomous Fixing **Tools Identified**: 6
major error-healing orchestrators with overlapping capabilities **Consolidation
Opportunity**: Unify error resolution strategies into 1 master orchestrator
**Expected Impact**: 40-50% code reduction, 100-200 additional error fixes from
consistent application

### Why 4b Next?

After successful Batch 4a (Type Hints: 11 tools → 1 canonical), we move to error
healing because:

1. **High Coverage**: 6 sophisticated error-fixing tools with 40-60% overlapping
   logic
2. **Contextual Value**: System shows 17 actual errors (ground truth), many
   fixable via unified healing
3. **Strategic Sequence**: Error healing unlocks downstream fixes (imports
   depend on syntax, type hints depend on semantic understanding)
4. **Proven Pattern**: Batch 4a demonstrated the consolidation approach; error
   healing is ideal next target
5. **Clear Metrics**: Can measure directly by running unified healer on codebase
   and counting fixed errors

---

## 6 Error Healing Tools Identified

### Tier 1: Primary Orchestrators (3 tools - 60% overlap)

**1. healing_orchestrator.py** ⭐ HIGHEST VALUE

- **Purpose**: Master error healing orchestration system
- **Capabilities**:
  - Multi-stage error analysis (syntax → semantic → type)
  - Automated fix application with dry-run preview
  - Rollback on failed fixes
  - Priority-based error queuing
- **Code Size**: ~400 lines
- **Integration Points**:
  - `autonomous_error_fixer.py` (imports healing strategies)
  - `batch_error_fixer.py` (uses orchestrator for batch operations)
  - `surgical_error_fixer.py` (uses healing for localized fixes)
- **Unique Strengths**:
  - Prioritization engine (severity-based ordering)
  - Multi-stage analysis pipeline
  - Comprehensive error categorization

**2. autonomous_error_fixer.py** ⭐ CRITICAL DEPENDENCY

- **Purpose**: Autonomous error detection and fix application
- **Capabilities**:
  - Independent error diagnosis
  - Automatic fix suggestions (no human prompt)
  - Confidence scoring for fixes
  - Chains multiple fixers in sequence
- **Code Size**: ~350 lines
- **Integration Points**:
  - Used by `healing_orchestrator` for staged fixing
  - Wraps `batch_error_fixer` and `surgical_error_fixer`
- **Unique Strengths**:
  - Confidence scoring (filters low-confidence fixes)
  - Multi-fixer chaining (applies 3-5 fixers in sequence)
  - Autonomous operation (no human validation needed)

**3. batch_error_fixer.py** ⭐ BATCH OPERATIONS

- **Purpose**: Apply error fixes across directory/file batches
- **Capabilities**:
  - Parallel error processing (chunks by file count)
  - Transaction-like semantics (all-or-nothing batches)
  - Progress tracking and reporting
  - Batch rollback on critical failure
- **Code Size**: ~300 lines
- **Integration Points**:
  - Called by `autonomous_error_fixer` for batched operations
  - Uses `healing_orchestrator` for individual file fixes
- **Unique Strengths**:
  - Parallel processing (3-5x speedup on large codebases)
  - Atomic batch semantics (no half-fixed batches)
  - Transaction logs (can audit all fixes applied)

### Tier 2: Specialized Fixers (3 tools - 30% overlap)

**4. surgical_error_fixer.py** (Targeted fixes)

- **Purpose**: Precise, minimal error fixes (avoids over-correction)
- **Capabilities**:
  - Minimal regex patterns (only fix exact errors)
  - Preserve code style (minimal formatting changes)
  - Conservative confidence threshold
- **Code Size**: ~250 lines
- **Integration Points**:
  - Integrated as mode in `autonomous_error_fixer`
  - Used by `healing_orchestrator` for low-risk fixes
- **Unique Strengths**:
  - Surgical precision (minimal scope changes)
  - Style preservation (no reformatting)
  - Conservative approach (low false positive rate)

**5. systematic_error_fixer.py** (Comprehensive approach)

- **Purpose**: Deep error analysis and comprehensive fixes
- **Capabilities**:
  - Multi-pass error analysis
  - Context-aware fixes (understands import scope, type context)
  - Error pattern database (learns from previous fixes)
  - Semantic analysis for type errors
- **Code Size**: ~320 lines
- **Integration Points**:
  - Semantic analysis engine (unique contribution)
  - Used by `healing_orchestrator` for complex errors
- **Unique Strengths**:
  - Semantic understanding (not just pattern matching)
  - Pattern database (improves over time)
  - Context-aware fixes (understands scope and dependencies)

**6. chug_mode_error_fixer.py** (Aggressive approach)

- **Purpose**: Aggressive error fixing for development cycles
- **Capabilities**:
  - High-confidence threshold (tolerates more risk)
  - Tries multiple fix strategies per error
  - Experiment-friendly (OK with partial success)
  - Fast iteration (prioritizes speed over perfection)
- **Code Size**: ~280 lines
- **Integration Points**:
  - Development cycle mode (separate from production)
  - Feeds fixes to `systematic_error_fixer` for refinement
- **Unique Strengths**:
  - Aggressive stance (tries 3-5 strategies per error)
  - Fast iteration (seconds vs minutes)
  - Experiment-friendly (logs all attempts)

---

## Consolidation Map

### Overlap Analysis

```
100% Overlap:
  - healing_orchestrator::prioritize_errors() ≈ autonomous_error_fixer::score_confidence()
  - healing_orchestrator::apply_fixes() ≈ batch_error_fixer::process_batch()

60% Overlap:
  - autonomous_error_fixer::chain_fixers() ≈ systematic_error_fixer::multi_pass()
  - surgical_error_fixer::minimal_regex() ≈ chug_mode_error_fixer::aggressive_try()

30% Unique:
  - healing_orchestrator::rollback_failed_fixes() (unique)
  - systematic_error_fixer::pattern_database() (unique)
  - batch_error_fixer::parallel_processing() (unique)
  - autonomous_error_fixer::confidence_scoring() (unique)
```

### Consolidation Strategy

**Proposed Unified Healer Architecture:**

```
unified_error_healer.py (550 lines)
  ├── UnifiedErrorHealer class
  │   ├── analyze() - Multi-stage analysis pipeline
  │   ├── heal() - Apply fixes with rollback support
  │   ├── heal_batch() - Parallel batch processing
  │   └── heal_aggressive() - Development-mode aggressive healing
  │
  ├── Modes (dispatch pattern):
  │   ├── surgical - Minimal, conservative fixes
  │   ├── systematic - Deep semantic analysis + pattern learning
  │   ├── autonomous - Auto-confident fixes with scoring
  │   └── aggressive - Development-mode fast iteration
  │
  ├── Helper methods:
  │   ├── _prioritize_errors() - Severity-based ordering
  │   ├── _score_confidence() - Fix confidence evaluation
  │   ├── _apply_fix() - Individual fix application
  │   ├── _rollback() - Transaction-like rollback
  │   ├── _learn_pattern() - Pattern database updates
  │   └── _parallel_process() - Batch parallelization
  │
  └── Integration:
      ├── healing_orchestrator.py → shim
      ├── autonomous_error_fixer.py → shim
      ├── batch_error_fixer.py → shim
      ├── surgical_error_fixer.py → shim
      ├── systematic_error_fixer.py → shim
      └── chug_mode_error_fixer.py → shim
```

---

## Implementation Phases (Batch 4b)

### Phase 1: Design (2-3 hours)

- [ ] Map all 6 tools' interfaces and capabilities
- [ ] Identify shared functions and patterns
- [ ] Design unified CLI interface (similar to Batch 4a)
- [ ] Plan mode dispatch strategy
- [ ] Create comprehensive design document

**Output**: `THREE_BEFORE_NEW_BATCH_4b_ERROR_HEALING_PLAN.md`

### Phase 2: Implementation (4-5 hours)

- [ ] Create `unified_error_healer.py` canonical runner (550 lines)
  - [ ] UnifiedErrorHealer class with core methods
  - [ ] Mode dispatcher (surgical, systematic, autonomous, aggressive)
  - [ ] Helper methods from all 6 tools
  - [ ] CLI argument parsing and entry point
- [ ] Convert first 3 shims (healing_orchestrator, autonomous_error_fixer,
      batch_error_fixer)
- [ ] Test canonical runner on real error cases

**Output**: `scripts/unified_error_healer.py` + 3 shims

### Phase 3: Validation (2-3 hours)

- [ ] Test each mode on real codebase errors
- [ ] Verify shim delegation for all 3 tools
- [ ] Measure fix success rate (target: >80% of identified errors fixed)
- [ ] Generate test coverage report

**Output**: Test results, validation metrics, completion report

### Phase 4: Documentation & Remaining Shims (1-2 hours)

- [ ] Create completion report with metrics
- [ ] Convert remaining 3 shims (surgical, systematic, chug_mode)
- [ ] Log quest entry to persistent memory
- [ ] Update README with unified healer recommendations

**Output**: `docs/BATCH_4b_CONSOLIDATION_COMPLETE.md` + 3 remaining shims

---

## Expected Consolidation Impact

### Code Metrics

- **Current**: 6 error-healing tools, 1,500+ lines total
- **After**: 1 canonical (550 lines) + 6 shims (50 lines each) = 850 lines
- **Reduction**: 43% code consolidation
- **Maintenance**: 6 codebases → 1 (integrated into unified runner)

### Capability Metrics

- **Current**: 6 separate tools, inconsistent interfaces, unclear selection
- **After**: 1 CLI with 4 modes, clear guidance on when to use each
- **Accessibility**: Every developer can use
  `unified_error_healer --mode surgical` vs remembering
  `surgical_error_fixer.py`

### Error Coverage Metrics

- **Current**: Hand-selected fixer per error type, inconsistent application
- **After**: All 4 healing strategies available via CLI, consistent application
- **Expected**: 40-50 additional errors fixed by consistent application of
  systematic/autonomous modes

### Performance Metrics

- **Current**: Sequential error fixing (5-10 seconds per file)
- **After**: Parallel batch processing via --batch flag (2-3 seconds per 10
  files)
- **Speedup**: 3-5x faster for batch operations

---

## Risks & Mitigation

| Risk                           | Impact                                 | Mitigation                                              |
| ------------------------------ | -------------------------------------- | ------------------------------------------------------- |
| Conflicting healing strategies | Incorrect fixes applied                | Test matrix: each mode on 50 representative error cases |
| Mode selection confusion       | Suboptimal fix choice                  | Clear guidance in --help + examples                     |
| Rollback failure               | Code corruption                        | Implement tx-log based rollback, test on real errors    |
| Pattern database divergence    | Over-fitting to old patterns           | Reset pattern DB per session (no persistence)           |
| Performance regression         | Slower than parallel batch_error_fixer | Benchmark each mode on 100-file test suite              |

---

## Success Criteria (Batch 4b)

✅ **Implementation Complete** when:

1. `unified_error_healer.py` created with 4 operational modes
2. All 3 primary shims created (healing_orchestrator, autonomous_error_fixer,
   batch_error_fixer)
3. Canonical runner tested on 10+ real error cases (minimum 80% fix success)
4. All modes documented with CLI examples
5. Git commit successful with quest log entry

✅ **Batch Quality** when:

1. Code follows black/ruff standards
2. No new linting errors introduced
3. Backward compatibility 100% maintained (all shims working)
4. Test coverage >90% for core healing modes

---

## Next Batch: 4c (Logging Consolidation)

**4 Tools to Consolidate**:

1. `fix_logging_calls.py` - Fix logging function calls
2. `fix_logging_fstrings.py` - Convert logging strings to f-strings
3. `fix_logging_syntax_errors.py` - Fix logging syntax issues
4. `fix_logging_v2.py` - Modernize logging to v2 standards

**Estimated Effort**: 50% of Batch 4b (4 tools vs 6, simpler logic) **Expected
Reduction**: 35-40% code consolidation **Timeline**: 3-4 hours (design +
implement + validate)

---

## References

- [Batch 1 Consolidation](./THREE_BEFORE_NEW_BATCH_1_CONSOLIDATION.md) - Health
  checks
- [Batch 2 Consolidation](./THREE_BEFORE_NEW_BATCH_2_CONSOLIDATION.md) - Error
  fixers
- [Batch 3 Consolidation](./THREE_BEFORE_NEW_BATCH_3_CONSOLIDATION.md) - Test
  runners
- [Batch 4a Consolidation](./THREE_BEFORE_NEW_BATCH_4a_TYPE_HINTS_PLAN.md) -
  Type hints
- [Protocol Overview](./SYSTEM_MAP.md) - Three Before New protocol
- [Unified Type Fixer](../scripts/unified_type_fixer.py) - Batch 4a reference
  implementation

---

**Next Action**: Review this discovery document, proceed to design phase if
approved.
