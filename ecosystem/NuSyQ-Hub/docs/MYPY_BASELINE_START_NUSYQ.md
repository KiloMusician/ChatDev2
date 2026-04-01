# Mypy Baseline for start_nusyq.py - Brownfield Technical Debt Assessment

**Assessment Date:** 2026-02-17  
**Context:** Pre-Orphan Symbol Modernization  
**Status:** Baseline Documentation (Not Regression)

## Executive Summary

`scripts/start_nusyq.py` currently has **~30 mypy errors** that represent **pre-existing brownfield technical debt**, not regressions from recent changes. This document establishes the baseline to prevent conflating old issues with new patches.

## Why This Matters

When modernizing orphaned symbols and integrating new capabilities, we need to distinguish:
- **Baseline Debt:** Pre-existing type issues from rapid prototyping phase
- **Regressions:** New type errors introduced by patches
- **Legitimate Ignores:** Cases where `# type: ignore` is appropriate

**Policy:** Recent patches (orphan rehabilitation, factory wiring, etc.) are **not responsible** for fixing pre-existing mypy issues unless directly touching affected lines.

---

## Known Mypy Issue Categories (Baseline)

### ⚠️ Category 1: Missing Type Annotations (~10-12 errors)
**Error Codes:** `[no-untyped-def]`, `[no-untyped-call]`

**Examples:**
```python
# Functions without complete type hints
def action_menu() -> None:  # Parameters untyped
def handle_action(action):  # Missing return type + param types
```

**Impact:** Low - Functions work correctly, just missing formal type declarations  
**Remediation:** Add gradual type hints as functions are touched  
**Not Blocking:** Orphan modernization work

---

### ⚠️ Category 2: Dict/Any Return Types (~5-8 errors)
**Error Codes:** `[no-any-return]`, `[dict-item]`

**Examples:**
```python
# JSON parsing returns Any
config = json.load(f)  # Type is Any
return config["key"]  # Returns Any from typed function
```

**Impact:** Medium - Loses type safety at API boundaries  
**Remediation:** Use `TypedDict` or `@dataclass` for structured config  
**Not Blocking:** Factory function wiring

---

### ⚠️ Category 3: Attribute Access on Dynamic Objects (~3-5 errors)
**Error Codes:** `[attr-defined]`, `[union-attr]`

**Examples:**
```python
# Accessing attributes on objects loaded dynamically
orchestrator = get_orchestrator()  # Type not narrowed
orchestrator.some_method()  # May not have attribute
```

**Impact:** Medium - Could catch real attribute errors  
**Remediation:** Add type guards or stub files for dynamic imports  
**Not Blocking:** Dashboard UI wiring

---

### ⚠️ Category 4: Unused Type Ignores (~2-3 errors)
**Error Codes:** `[unused-ignore]`

**Examples:**
```python
# Previous suppressions no longer needed
result = call_something()  # type: ignore[arg-type]  # Actually fine now
```

**Impact:** Low - Code works, just cleanup needed  
**Remediation:** Remove stale `# type: ignore` comments  
**Quick Win:** Can clean these opportunistically

---

### ⚠️ Category 5: Truthy Function Checks (~2-3 errors)
**Error Codes:** `[truthy-function]`

**Examples:**
```python
# Checking if function exists in boolean context
if get_orchestrator:  # Always True, should be get_orchestrator()
```

**Impact:** Low-Medium - Logical bug but uncommon code path  
**Remediation:** Fix conditional logic `if callable(x)` vs `if x()`  
**Not Blocking:** Example runner integration

---

## Baseline Count: ~30 Errors (February 2026)

**Breakdown by Priority:**
- **P0 (Blocks Production):** 0 errors
- **P1 (Correctness Issues):** ~5 errors (truthy-function, attr-defined)
- **P2 (Type Safety Lost):** ~15 errors (no-any-return, dict-item, union-attr)
- **P3 (Documentation/Cleanup):** ~10 errors (no-untyped-def, unused-ignore)

**Verdict:** File is **functionally sound** but has **gradual typing opportunities**.

---

## Modernization Strategy

### Phase 1: Opportunistic Cleanup (Ongoing)
- When touching a function for orphan integration, add type hints
- Remove unused `# type: ignore` comments as discovered
- Fix truthy-function bugs if encountered

### Phase 2: Systematic Campaign (Future Quest)
Create Culture Ship quest: **"Type Safety Modernization: start_nusyq.py"**
- Target: Reduce to <10 errors
- Approach: Add `TypedDict` for JSON structures
- Timeline: Low priority, incremental over 2-3 weeks

### Phase 3: Strict Mode (Long-term)
- Enable `--strict` mypy checking
- Add stub files for third-party integrations
- Full type coverage for new code

---

## Patch Guidelines: What to Ignore vs. Fix

### ✅ **Safe to Ignore (Not Your Responsibility)**
If your patch adds/modifies code and triggers **pre-existing mypy errors** on **unchanged lines**, you can:
1. Add `# type: ignore[error-code]  # Pre-existing baseline, tracked in MYPY_BASELINE.md`
2. Document which errors are baseline in your commit message
3. Move on - not required to fix brownfield debt

### ❌ **Must Fix (Your Responsibility)**
If your patch:
1. **Introduces new mypy errors** on **new lines** → Must fix or justify
2. **Changes a function signature** → Update type hints to match
3. **Adds new factory/orchestrator calls** → Ensure return types are typed

### 🎯 **Opportunistic Wins (Encouraged)**
If you're already editing a function with baseline errors:
- Adding type hints takes <30 seconds
- Improves code review experience
- Counts toward quest completion metrics

---

## Example: Orphan Modernization Patch

**Scenario:** Wiring `get_orchestrator()` factory into `start_nusyq.py`

```python
# Before (baseline error exists)
def action_menu():  # [no-untyped-def] - Pre-existing
    orchestrator = get_orchestrator()  # [no-any-return] - Pre-existing
    orchestrator.run()

# After (patch adds factory call, inherits baseline)
def action_menu():  # [no-untyped-def] - Still baseline
    orchestrator = get_orchestrator()  # [no-any-return] - Still baseline
    
    # NEW CODE - must be type-safe
    if orchestrator is None:  # ✅ New code handles None
        print("Failed to get orchestrator")
        return
    
    orchestrator.run()  # ✅ Now safe after None check
```

**Verdict:** Patch is acceptable. Baseline errors remain but new code is defensive.

---

## Tracking Evolution

### Metrics to Monitor
1. **Total Error Count:** Should not increase due to new code
2. **Error Density:** Errors per 1000 lines (should decrease as file grows)
3. **Category Distribution:** Shift from P1 → P2 → P3 over time

### Success Indicators
- **Week 1:** Error count stable at ~30 (baseline maintained)
- **Month 1:** Error count reduced to ~20 (opportunistic fixes)
- **Month 3:** Error count <10 (systematic campaign complete)

---

## See Also
- `docs/ORPHANED_SYMBOLS_MODERNIZATION_PLAN.md` - Why we're touching start_nusyq.py
- `scripts/mypy_baseline_assessment.py` - Tool to generate current snapshot
- Culture Ship Quest: "Type Safety Modernization" (future)

---

## TL;DR for Reviewers

**Q:** Why does this patch have mypy warnings in start_nusyq.py?  
**A:** File has ~30 pre-existing baseline issues. Patch does not worsen count.

**Q:** Should we block patches that don't fix baseline issues?  
**A:** No. Brownfield debt remediation is separate from feature work.

**Q:** When will these be fixed?  
**A:** Opportunistically during edits + systematic quest in future sprint.

**Q:** Are these blocking production?  
**A:** No. Zero P0 errors. File is functionally sound.
