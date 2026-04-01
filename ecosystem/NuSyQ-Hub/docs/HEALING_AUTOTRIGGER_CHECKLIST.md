# Healing Auto-Trigger Integration Checklist

**Integration:** Doctor → Heal Auto-Loop  
**Estimated Time:** 45 minutes  
**Capability Multiplier:** 3X (doctor finds issue, system auto-suggests fix, automatic validation)  
**Foundation:** SmartSearch integration ✅, Quest logging pending  

---

## Phase 1: Understand Current Systems (10 min)

- [ ] **Read doctor.py structure**
  - File: `scripts/nusyq_actions/doctor.py`
  - Purpose: Runs 5 diagnostic checks (code quality, imports, tests, coverage, security)
  - Output: Dict with `issues` list (each issue has `path`, `severity`, `type`, `description`, `suggestion`)
  - Pattern: Writes results to `state/reports/doctor_report.json`

- [ ] **Read heal_actions.py structure**
  - File: `scripts/nusyq_actions/heal_actions.py`
  - Purpose: Provides healing functions (`heal_auto_fix`, `heal_syntax`, `heal_imports`, etc.)
  - Trigger: `nusyq heal <subcommand>`
  - Status: Fully functional, but isolated from doctor

- [ ] **Understand current flow**
  - Current: Doctor finds → User must manually run `nusyq heal <specific_subcommand>`
  - Desired: Doctor finds → System suggests `nusyq heal <specific_issue>` → Auto-apply if approved

---

## Phase 2: Design Auto-Trigger Loop (10 min)

- [ ] **Map doctor issue types to heal subcommands**
  ```
  Doctor Issue Type → Heal Subcommand Mapping:
  - code_quality → heal_ruff_issues
  - import_error → heal_imports
  - test_failure → heal_tests
  - coverage_low → (suggest, don't auto-fix)
  - security → heal_security_issues
  ```

- [ ] **Design loop sequence**
  ```
  1. Doctor runs → Issues found
  2. Doctor formats issues for Healer
  3. Healer auto-applies fixes for CRITICAL/HIGH severity
  4. Healer suggests fixes for MEDIUM/LOW severity
  5. Create feedback loop: Doctor re-runs to validate fixes
  6. Log all actions to quest system (pending quest logging integration)
  ```

- [ ] **Identify safety boundaries**
  - Which issue types are safe to auto-fix? (import errors, ruff issues)
  - Which require approval? (test failures, security issues, coverage)
  - Severity threshold for auto-apply (CRITICAL only? CRITICAL+HIGH?)

---

## Phase 3: Enhance Doctor Output (15 min)

**File:** `scripts/nusyq_actions/doctor.py`

- [ ] **Add issue classification**
  - Add field to each issue: `heal_command` (what command would fix this)
  - Example: `{"type": "import_error", "heal_command": "heal_imports", "auto_applicable": True}`

- [ ] **Add healing suggestion to output**
  - When issues found, append section:
    ```
    SUGGESTED NEXT STEP:
    
    Auto-fixable issues (3):
      nusyq heal ruff_issues          # Fix 2 ruff violations
      nusyq heal imports               # Fix 1 import error
    
    Requires review (2):
      nusyq heal tests --manual        # 1 test failure (MEDIUM severity)
      nusyq heal security --review     # 1 security hotspot (HIGH severity)
    ```

- [ ] **Add --auto-heal flag**
  - `nusyq doctor --auto-heal` → Doctor + auto-apply all fixable issues
  - `nusyq doctor --auto-heal --skip-imports` → Doctor + auto-heal except imports
  - Validates fixes after each heal pass

---

## Phase 4: Enhance Heal Actions (15 min)

**File:** `scripts/nusyq_actions/heal_actions.py`

- [ ] **Add auto-detection of issue source**
  - Heal function should accept `--from-doctor` flag
  - Reads latest `doctor_report.json` to understand context
  - Example: `heal_ruff_issues(from_doctor=True)` → Only fixes issues doctor found

- [ ] **Add validation callback**
  - After heal → Doctor runs again on affected files
  - Validates fix success
  - Tracks "fixes attempted vs fixes successful" in quest log

- [ ] **Add summary output**
  - When healing completes:
    ```
    ✅ Healing Results:
    - 2/2 import errors fixed ✅
    - 5/5 ruff violations fixed ✅
    - 1/1 test failure fixed ✅
    
    Next: nusyq doctor to validate
    ```

---

## Phase 5: Wire Auto-Loop in start_nusyq.py (5 min)

**File:** `scripts/start_nusyq.py`

- [ ] **Add new action: "doctor_with_heal"**
  - Route: `nusyq doctor_heal` or add `--with-heal` flag to `nusyq doctor`
  - Logic: Doctor → Parse issues → Auto-heal → Doctor (validate)
  - Output: Full report showing all steps

- [ ] **Integrate with quest logging** (after quest logging PR merges)
  - Log each healing attempt: `log_action_to_quest("doctor_heal", status="completed", metadata={"fixes_applied": 5, "validation_passed": True})`

---

## Phase 6: Testing (5 min)

- [ ] **Create test case: test_doctor_heal_loop.py**
  ```python
  def test_doctor_heal_auto_fixes_imports():
      # Create test file with bad import
      # Run nusyq doctor_heal
      # Verify import fixed
      # Verify doctor re-run shows no import errors
  ```

- [ ] **Manual smoke test**
  - Run `nusyq doctor` on current repo
  - Manually run `nusyq heal <suggestion>`
  - Verify issue resolved
  - Verify doctor re-run confirms fix

---

## Success Criteria

| Criteria | Status | Evidence |
|----------|--------|----------|
| Doctor identifies issues | ✅ (existing) | `nusyq doctor` returns detailed report |
| Doctor suggests fixes | ⏭️ | Output section with `heal` commands |
| Healer auto-applies fixes | ⏭️ | `nusyq heal <type>` runs without user review |
| Validation loop works | ⏭️ | Doctor re-runs after heal, shows fixes applied |
| Loop is safe | ⏭️ | Only auto-fixes marked `auto_applicable: True` |
| Quest logs all steps | ⏭️ | After quest logging integration |

---

## Integration with SmartSearch (Bonus)

After quest logging, developers will be able to:
- `nusyq search keyword "doctor_heal"` → Find all doctor-heal logs
- `nusyq search patterns "auto_healing"` → Find all healing patterns in code
- Full audit trail of system self-improvements

---

## Code Placement Reference

```
MODIFIED FILES:
1. scripts/nusyq_actions/doctor.py
   - Line ~150: Add heal_command field to issues
   - Line ~200: Add healing suggestion output section
   - Line ~20: Add --auto-heal flag parsing

2. scripts/nusyq_actions/heal_actions.py
   - Line ~50: Add --from-doctor flag support
   - Line ~80: Add validation callback after heal
   - Line ~150: Add healing results summary

3. scripts/start_nusyq.py
   - Line ~440: Add "doctor_heal" to KNOWN_ACTIONS
   - Line ~13300: Add _handle_doctor_heal() function
   - Line ~13600: Add dispatch routing for doctor_heal

4. tests/test_doctor_heal_loop.py (NEW)
   - Create comprehensive test for auto-loop
```

---

## Why Now?

1. SmartSearch integration proved the connection pattern ✅
2. Foundation stable (no blockers, clear path) ✅
3. Doctor already exists (no building needed, just wiring) ✅
4. High value (3X capability multiplier) ✅
5. Safe (can validate each fix before applying) ✅
6. Enables Phase 2 (quest logging will trace all auto-improvements) ✅

---

## Continuation Signal

When user is ready:
1. User says: **"Implement healing auto-trigger"** → Agent proceeds with Phase 1-6
2. Or: **"Show me doctor.py structure first"** → Agent reads and explains current system
3. Or: **"Start with just the suggestion output"** → Agent implements Phase 3 only

**Default:** Proceed autonomously if user has approved this roadmap.
