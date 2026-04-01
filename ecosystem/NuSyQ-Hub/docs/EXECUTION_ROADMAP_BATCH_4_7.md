# 🚀 EXECUTION ROADMAP - Next Steps (Quick Reference)

## ✅ IMMEDIATE (Next 2 hours)

### Batch 4: Final Test & Static Cleanup

**Status**: Ready to execute  
**Files to Modify**: 6  
**Expected Output**: 0 warnings, 91%+ coverage

```bash
# 1. Fix test_advanced_tag_manager.py warnings
#    - Remove unused asyncio import
#    - Fix line break after operator (line 289)
#    - Sort imports
#    - Change protected method access to public OR refactor tests

# 2. Run final validation
python -m pytest tests -q --cov=src --cov-report=term-missing

# 3. Verify static analysis
python scripts/lint_test_check.py

# 4. Commit
git add -A
git commit -m "Batch 4: Final quality cleanup - 91%+ coverage, 0 warnings"
```

---

## 📋 BATCH BREAKDOWN (Detailed Checklist)

### **Batch 4 Tasks** (2-3 hours, ~30 loc changes)

- [ ] **test_advanced_tag_manager.py** (6 fixes)
  - [ ] Line 3: Remove `import asyncio` (unused)
  - [ ] Line 289: Move `+ result.get("omni_tags", [])` to same line as initial expression
  - [ ] Lines 2-7: Sort imports (json, Path, tempfile, pytest, AdvancedTagManager)
  - [ ] Lines 84, 100, 116-118, 131, 134: Either make methods public or refactor tests
  - [ ] Validate: `pytest tests/test_advanced_tag_manager.py -v`

- [ ] **Final Coverage Report**
  - [ ] `python -m pytest tests -q --cov=src --cov-report=term-missing --cov-report=html`
  - [ ] Verify coverage ≥ 91%
  - [ ] Screenshot coverage report for baseline

- [ ] **Static Analysis Cleanup**
  - [ ] Run `python scripts/lint_test_check.py`
  - [ ] Verify 0 errors, 0 warnings in test files
  - [ ] Document any legitimate warnings to suppress

- [ ] **Update Tracking**
  - [ ] `config/ZETA_PROGRESS_TRACKER.json` → Mark "Static Quality Cleanup" as complete
  - [ ] Update `docs/Checklists/PROJECT_STATUS_CHECKLIST.md` → [x] Test cleanup complete
  - [ ] Create baseline snapshot: `cp requirements.txt requirements.baseline.txt`

---

### **Batch 5 Planning** (4-6 hours, architectural design)

**Objective**: Build automation infrastructure

**Design Tasks** (NO CODE YET — design phase):

- [ ] **ZETA Progress Auto-Updater**
  - Input: `src/Rosetta_Quest_System/quest_log.jsonl`
  - Output: Updated `config/ZETA_PROGRESS_TRACKER.json`
  - Logic: Parse quests → extract status → aggregate by phase → write tracker
  - Trigger: Pre-commit hook or scheduled daily

- [ ] **Quest Log Validator**
  - Input: `quest_log.jsonl` entries
  - Checks: Valid JSON, required fields, status enums, date formats
  - Output: Report of missing/invalid entries
  - Trigger: CI/CD pipeline

- [ ] **Documentation Sync Checker**
  - Input: README.md metrics, context.md claims, reality (file count, LOC)
  - Checks: Claims match actual state
  - Output: Drift report highlighting outdated sections
  - Trigger: Weekly GitHub action

- [ ] **Hint Engine**
  - Input: ZETA progress, completed quests, dependencies
  - Logic: Identify unblocked next quests
  - Output: "Next 3 recommended actions" to STDOUT
  - Trigger: Daily morning summary

**Decision**: Start with ZETA Auto-Updater (highest ROI, lowest complexity)

---

### **Batch 6 Testing** (6-8 hours, integration validation)

**Objective**: Prove all major systems work end-to-end

**Test Scripts to Create**:

- [ ] `tests/integration/test_chatdev_e2e.py`
  - Prompt → ChatDev generate → Code produced → Tests pass
  - Success: 2/3 ChatDev runs produce working code

- [ ] `tests/integration/test_consciousness_sync.py`
  - Write data to NuSyQ-Hub → Read from SimulatedVerse
  - Success: Cross-repo data accessible

- [ ] `tests/integration/test_mcp_server.py`
  - MCP server online → Send commands → Receive responses
  - Success: All 8 protocol endpoints respond correctly

- [ ] `tests/integration/test_ollama_routing.py`
  - Task classification → Model selection → Inference
  - Success: <5% performance variance vs baseline

- [ ] `tests/integration/test_terminal_manager_multirepository.py`
  - Execute cmd in NuSyQ-Hub → Terminal manager → Execute in NuSyQ Root
  - Success: Output captured correctly

---

### **Batch 7 Quest Completion** (Phased rollout)

**Quest 1: Zeta03 - Intelligent Model Selection** (2 hours)

```python
# File: src/ai/model_selection_router.py (expand existing)
# Add:
# - Task classification with 95%+ accuracy
# - Model router with latency optimization
# - Performance tracking per task type
# Test: test_model_selection_router.py (10+ test cases)
```

**Quest 2: Zeta06 - Terminal Management** (3 hours)

```python
# File: src/system/terminal_manager.py (complete)
# Add:
# - Multi-repository command execution
# - Cross-repo context preservation
# - Async terminal pools
# Test: test_terminal_multirepository.py (integration)
```

**Quest 3: Zeta41 - ChatDev Team Coordination** (4 hours)

```python
# File: src/integration/chatdev_team_coordinator.py (new)
# Add:
# - Role assignment (CEO, CTO, Dev, Tester)
# - Meeting orchestration
# - Output validation
# Test: test_chatdev_team_coordination.py (end-to-end)
```

---

## 🎯 PARALLEL WORK OPPORTUNITIES

### Can be done **independently** (no dependencies):

1. **Documentation Refresh** (2 hours)
   - Update README.md with current metrics
   - Refresh docs/STATUS.md with current architecture
   - Update CONTRIBUTING.md with Batch 4-7 expectations

2. **Repository Cleanup** (1.5 hours)
   - Remove deprecated files (Archive/* cleanup)
   - Delete duplicate test files
   - Organize example projects

3. **Performance Baseline** (1 hour)
   - Document current inference times per model
   - Memory usage baseline
   - Token throughput measurements

---

## 📊 Success Criteria Checklist

### Batch 4 Complete When:
- [ ] `pytest tests -q` shows 585+ passing, 0 failures
- [ ] Coverage report shows ≥91%
- [ ] `python scripts/lint_test_check.py` reports 0 errors
- [ ] All 4 test files modified pass without warnings
- [ ] CHANGELOG.md updated with Batch 4 completion

### Batch 5 Complete When:
- [ ] `src/tools/zeta_progress_updater.py` created
- [ ] `quest_log.jsonl` parses without errors
- [ ] Auto-updater produces valid ZETA_PROGRESS_TRACKER.json
- [ ] Hint engine suggests next 3 quests accurately
- [ ] Integration tests pass (3/3)

### Batch 6 Complete When:
- [ ] ChatDev E2E test passes 2 consecutive runs
- [ ] Cross-repo consciousness sync verified
- [ ] MCP server responds to all 8 operations
- [ ] Model selection accuracy >95%
- [ ] Terminal manager executes cross-repo commands

### Batch 7.1 Complete When:
- [ ] Zeta03: Model selection in production use
- [ ] Zeta06: Terminal commands work across all repos
- [ ] All related tests pass
- [ ] Performance metrics documented

---

## 🔄 Automation Setup (After Batch 5)

### Pre-commit Hook
```bash
.git/hooks/pre-commit
- Run: python -m pytest --lf (last-failed)
- Run: zeta_progress_updater.py
- Run: doc_sync_checker.py
- Block commit if any fail
```

### Scheduled Jobs
```yaml
# .github/workflows/nightly.yml
- Daily: Run hint engine, generate summary report
- Weekly: Doc sync check, coverage analysis
- Monthly: Performance regression analysis
```

---

## 💾 Commit Strategy

### Batch 4 Commits
```
1. "Fix test_advanced_tag_manager.py imports and warnings"
2. "Remove unused asyncio import from test files"
3. "Final coverage validation - 91.72% achieved"
4. "Batch 4 complete: Production-ready code quality"
```

### Batch 5 Commits (first iteration)
```
1. "Design ZETA progress automation framework"
2. "Implement zeta_progress_updater.py"
3. "Add quest_log validator"
4. "Create hint engine"
5. "Batch 5.1 complete: Basic automation in place"
```

---

## 📞 Decision Points to Resolve FIRST

Before executing, clarify:

1. **Protected Methods in Tests**:
   - Option A: Make _apply_rules and _rule_matches public (recommended)
   - Option B: Test through public API only
   - Option C: Suppress protected access warnings

2. **Feature vs Infrastructure**:
   - Prioritize: Batch 5 automation OR Batch 6 integration tests?
   - Recommend: Automation first (enables better progress tracking)

3. **Scope Lock**:
   - Confirm Batches 4-6 scope is final before starting Batch 7
   - Any new requests → defer to Batch 8+

4. **Risk Tolerance**:
   - ChatDev integration testing could reveal issues
   - Acceptable risk or should we pilot first?

---

## 🎯 IMMEDIATE ACTION (Next 15 minutes)

**DO NOT MODIFY CODE YET**

1. **Read** `docs/STRATEGIC_ANALYSIS_2025_12_16.md` (this context doc)
2. **Review** this execution roadmap
3. **Decide** Batch 4 → 5 → 6 → 7 is acceptable order
4. **Approve** decision points above
5. **Start** with Batch 4 if approved

---

**Status**: Analysis Complete ✅  
**Ready to Execute**: YES  
**Estimated Total Time**: 20-30 hours (spread over 2-3 weeks)  
**Team Coordination**: Can be parallelized at Batch 5+ phases
