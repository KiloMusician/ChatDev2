# Three Before New: Batch 4a – Type Hint Unification Plan

**Date:** 2026-01-05  
**Target:** Consolidate 11 overlapping type-hint tools into 1 canonical
orchestrator  
**Baseline:** 11 separate scripts with overlapping goals  
**Goal:** 1 canonical `unified_type_fixer.py` + 10 shims with mode delegation

## Tool Consolidation Mapping

### Existing Tools (11 identified)

1. **`scripts/add_type_annotations.py`** (197 lines)

   - Purpose: Add type annotations to functions missing them
   - Method: AST NodeTransformer-based inference
   - Key capability: Infer types from default values and return statements
   - Shim Target: `--mode add-annotations`

2. **`scripts/add_type_hints.py`** (similar scope, duplicate?)

   - Purpose: Add type hints to modules
   - Method: AST-based inference
   - Overlap: Likely duplicate/similar to add_type_annotations
   - Shim Target: `--mode add-hints` (or merge with add-annotations)

3. **`scripts/auto_fix_types.py`** (275 lines)

   - Purpose: Fix common mypy errors (Optional types, -> None, no-any-return)
   - Method: Regex-based pattern fixing
   - Key capability: Mypy-driven fixes
   - **Candidate for canonical base** (most mature logic)
   - Modes needed: Enhance with --mode optional|none-return|no-any|all

4. **`scripts/auto_fix_type_hints.py`**

   - Purpose: Auto-fix type hint errors
   - Method: TBD (need to examine)
   - Overlap: Similar to auto_fix_types

5. **`scripts/add_type_hints_batch.py`**

   - Purpose: Batch application of type hints
   - Method: Likely wraps add_type_hints.py
   - Shim Target: `--mode add-hints --batch` flag

6. **`scripts/batch_type_fixer.py`**

   - Purpose: Batch type fixing
   - Method: TBD
   - Shim Target: Likely wraps auto_fix_types with --batch mode

7. **`scripts/custom_type_fixer.py`**

   - Purpose: Custom type fixing rules
   - Method: Rule engine
   - Shim Target: `--mode custom --rules <file>`

8. **`scripts/surgical_type_fix.py`** (132 lines)

   - Purpose: Aggressive surgical type error fixing
   - Method: Regex-based pattern matching with lookahead
   - Key capability: Return type inference from body inspection
   - Shim Target: `--mode surgical`

9. **`scripts/improve_type_hints.py`**

   - Purpose: Improve existing type hints (e.g., specific instead of generic)
   - Method: TBD
   - Shim Target: `--mode improve`

10. **`scripts/modernize_typing.py`**

    - Purpose: Modernize typing to latest Python (e.g., list → List, dict → Dict
      removal)
    - Method: TBD
    - Shim Target: `--mode modernize`

11. **`scripts/fix_deprecated_typing.py`**
    - Purpose: Fix deprecated typing patterns (e.g., typing.List → list)
    - Method: TBD
    - Shim Target: `--mode fix-deprecated`

## Consolidation Architecture

### Canonical Entrypoint: `scripts/unified_type_fixer.py`

**Purpose:** Single CLI for all type-fixing operations with mode-based
delegation

**Modes (proposed):**

```bash
# Add/Infer type hints
python scripts/unified_type_fixer.py --mode add-annotations [<path>] [--batch]
python scripts/unified_type_fixer.py --mode add-hints [<path>] [--batch]
python scripts/unified_type_fixer.py --mode improve [<path>]

# Fix type errors
python scripts/unified_type_fixer.py --mode fix-mypy [<path>]     # auto_fix_types logic
python scripts/unified_type_fixer.py --mode optional [<path>]     # Fix Optional patterns
python scripts/unified_type_fixer.py --mode none-return [<path>]  # Fix -> None errors
python scripts/unified_type_fixer.py --mode no-any [<path>]       # Fix no-any-return
python scripts/unified_type_fixer.py --mode surgical [<path>]     # Aggressive fixing

# Modernization
python scripts/unified_type_fixer.py --mode modernize [<path>]    # Python 3.9+ style
python scripts/unified_type_fixer.py --mode fix-deprecated [<path>] # typing.List → list

# Batch/Custom
python scripts/unified_type_fixer.py --mode batch [<path>] [--modes add-annotations,surgical]
python scripts/unified_type_fixer.py --mode custom [<path>] --rules <config>

# Utility
python scripts/unified_type_fixer.py --list-modes
python scripts/unified_type_fixer.py --dry-run --mode surgical [<path>]
```

### Implementation Strategy

1. **Create `scripts/unified_type_fixer.py`** (new canonical)

   - CLI argument parser with `--mode` flag
   - Dispatcher to specialized functions
   - Preserve logic from all 11 tools (copy their core algorithms)
   - Add `--dry-run`, `--batch`, `--verbose` options
   - Logging to quest system for traceability

2. **Create Shims** (10 files, one per deprecated tool)

   - Each shim imports canonical and delegates via mode flag
   - Example: `add_type_annotations.py` → calls
     `unified_type_fixer.py --mode add-annotations`
   - Include deprecation warnings in output

3. **Integration Points**

   - Update `lint_test_check.py` to use canonical runner for type fixing
   - Update `scripts/auto_modernize.py` if it references type fixers
   - Update `scripts/batch_error_fixer.py` if it references any type fixer
   - Update documentation references

4. **Testing & Validation**
   - Run canonical runner on test files in src/ and tests/
   - Verify shim delegation (check deprecation warnings appear)
   - Compare output of canonical vs old tools (should be identical)
   - Run quest validation smoke test

## Implementation Phases

### Phase 1 · Design & Analysis (THIS DOCUMENT)

- ✅ Tool inventory complete (11 tools)
- ✅ Architecture designed
- 📋 Awaiting validation before proceeding

### Phase 2 · Implementation

- [ ] Examine all 11 tools in detail (read full source)
- [ ] Extract key algorithms and deduplication logic
- [ ] Create `unified_type_fixer.py` with core logic + mode dispatcher
- [ ] Create 10 shims with delegation + deprecation warnings
- [ ] Update integration points

### Phase 3 · Migration

- [ ] Update `lint_test_check.py` references
- [ ] Update docs and task examples
- [ ] Update any other scripts that reference type fixers
- [ ] Run quick smoke test on canonical runner

### Phase 4 · Logging & Validation

- [ ] Log Batch 4a quest entry to quest system
- [ ] Run `unified_type_fixer.py --mode surgical src/` on real codebase
- [ ] Verify shim delegation produces deprecation warnings
- [ ] Final documentation & checklist update

## Expected Impact

- **Before:** 11 overlapping type-fixing tools, unclear which to use,
  maintenance burden
- **After:** 1 canonical entrypoint with 11 modes, consistent UX, clear choice
- **Code Reduction:** ~1,500+ lines of redundant code consolidated to ~800-1,000
  lines (40% reduction)
- **Discoverability:** `--list-modes` shows all capabilities at a glance
- **Backward Compatibility:** All old scripts work (as shims) so existing
  scripts/tasks don't break

## Dependencies & Risks

**Dependencies:**

- All 11 tools must be examined fully to ensure no unique logic is lost
- Ensure canonical runner covers all use cases from old tools

**Risks:**

- If tools have subtle differences in algorithm, consolidation could lose
  precision
  - Mitigation: Create side-by-side test comparing old vs new output
- Some tools may depend on specific CLI patterns
  - Mitigation: Preserve exact behavior via mode delegation; only refactor
    internally

**Mitigation Strategy:**

- Run both old and new tools on same files; compare output
- Keep old tools as reference; don't delete until validation complete
- Document any differences in changelog

## Next Steps

1. **User Confirmation:** Proceed with Batch 4a type hint consolidation?
   (YES/NO)
2. **If YES:**
   - Examine all 11 tools in full (Phase 2 start)
   - Create unified_type_fixer.py with mode dispatcher
   - Create shims and test delegation
   - Log quest and validate
3. **If NO:**
   - Move to Batch 4b (Error Healing) or Batch 4c (Logging)

---

**Recommendation:** Type hints is the largest consolidation opportunity (11
tools). High impact + relatively low risk since most tools are AST-based
(well-defined patterns). Recommend **proceeding with Batch 4a immediately**
after user confirmation.

**Estimated Effort:** 4-6 hours (analysis, implementation, testing,
documentation)

**Timeline:** Can be completed in 1-2 working sessions
