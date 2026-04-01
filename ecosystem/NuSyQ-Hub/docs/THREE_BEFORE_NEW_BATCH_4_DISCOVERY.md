# Three Before New: Batch 4 Discovery – Auto-Fixers & Healers

**Date:** 2026-01-05  
**Target:** Auto-fixers, type hint appliers, error fixers, and healing tools  
**Status:** DISCOVERY PHASE

## Fixer Tool Inventory (21+ candidates identified)

### Category 1 · Type Hint / Import Fixers

1. `scripts/add_type_annotations.py` – Add type annotations to functions
2. `scripts/add_type_hints.py` – Add type hints to modules
3. `scripts/add_type_hints_batch.py` – Batch type hint application
4. `scripts/auto_fix_types.py` – Auto-fix type-related issues
5. `scripts/auto_fix_type_hints.py` – Auto-fix type hint errors
6. `scripts/batch_type_fixer.py` – Batch type fixing
7. `scripts/custom_type_fixer.py` – Custom type fixing rules
8. `scripts/fix_deprecated_typing.py` – Fix deprecated typing patterns
9. `scripts/improve_type_hints.py` – Improve existing type hints
10. `scripts/modernize_typing.py` – Modernize typing to latest Python
11. `scripts/surgical_type_fix.py` – Surgical type fixes
12. `scripts/auto_fix_imports.py` – Auto-fix import statements
13. `scripts/fix_import_order.py` – Fix import ordering
14. `scripts/fix_future_imports.py` – Fix future imports

### Category 2 · Logging & Syntax Fixers

15. `scripts/fix_logging_calls.py` – Fix logging function calls
16. `scripts/fix_logging_fstrings.py` – Fix f-string logging patterns
17. `scripts/fix_logging_syntax_errors.py` – Fix logging syntax errors
18. `scripts/fix_logging_v2.py` – Logging v2 fixes
19. `scripts/fix_bare_except.py` – Fix bare except clauses

### Category 3 · Code Quality Fixers

20. `scripts/fix_async_patterns.py` – Fix async/await patterns
21. `scripts/fix_coverage_config.py` – Fix pytest coverage config
22. `scripts/fix_file_encoding.py` – Fix file encoding issues
23. `scripts/fix_file_encodings.py` – Batch file encoding fixes
24. `scripts/clean_unused_ignores.py` – Clean unused ignore directives

### Category 4 · Higher-Level Healing / Orchestrators

25. `scripts/autonomous_error_fixer.py` – Autonomous error fixing
26. `scripts/batch_error_fixer.py` – Batch error fixing
27. `scripts/chug_mode_error_fixer.py` – Error fixing in "chug" mode
28. `scripts/surgical_error_fixer.py` – Surgical error fixing
29. `scripts/systematic_error_fixer.py` – Systematic error fixing
30. `scripts/semantic_auto_fixer.py` – Semantic-aware auto fixer
31. `scripts/healing_orchestrator.py` – Healing orchestration
32. `scripts/batch_heal_system.py` – Batch healing system
33. `scripts/auto_heal_config.py` – Auto-heal configuration

### Category 5 · Specialized Domain Fixers

34. `scripts/fix_simulatedverse_fields.py` – SimulatedVerse schema fixes
35. `scripts/fix_simulatedverse_schemas.py` – SimulatedVerse schema fixes
36. `scripts/fix_ollama_hosts.py` – Ollama host configuration fixes
37. `scripts/modernize_file_io.py` – Modernize file I/O patterns
38. `scripts/validate_fixes.py` – Validate applied fixes

## High-Value Consolidation Candidates

### Tier 1 · Core Healing (HIGH PRIORITY)

1. **`scripts/healing_orchestrator.py`** – Main healing coordinator
   - Likely delegates to specific fixers
   - Candidate for canonical entrypoint
2. **`scripts/autonomous_error_fixer.py`** – Primary autonomous fixer

   - Entry point for error-triggered healing
   - Integration with quest system

3. **`scripts/batch_heal_system.py`** – Batch healing harness
   - Likely wraps multiple fixers
   - CI/nightly candidate

### Tier 2 · Type & Import Fixers (MEDIUM PRIORITY)

4. **`scripts/auto_fix_imports.py`** – Import consolidation target

   - Unified import ordering/fixing interface
   - Likely competitors: fix_import_order.py, fix_future_imports.py

5. **`scripts/auto_fix_types.py`** or **`scripts/add_type_hints.py`** – Type
   consolidation target

   - Unify ~10 type-related tools under one canonical interface
   - Competitors: add_type_annotations.py, auto_fix_type_hints.py,
     surgical_type_fix.py, modernize_typing.py, improve_type_hints.py,
     fix_deprecated_typing.py, custom_type_fixer.py, batch_type_fixer.py,
     add_type_hints_batch.py

6. **`scripts/fix_logging_calls.py`** – Logging consolidation target
   - Unify logging fixers: fix_logging_fstrings.py,
     fix_logging_syntax_errors.py, fix_logging_v2.py

### Tier 3 · Domain-Specific (KEEP SEPARATE)

7. `scripts/fix_simulatedverse_fields.py` – Domain-specific, keep separate
8. `scripts/fix_ollama_hosts.py` – Domain-specific, keep separate
9. `scripts/fix_async_patterns.py` – Domain-specific, keep separate

## Consolidation Opportunities

### Opportunity 1: Type Hint Unification (9 tools → 1 canonical + modes)

- **Scope:** add_type_annotations, add_type_hints, add_type_hints_batch,
  auto_fix_types, auto_fix_type_hints, batch_type_fixer, custom_type_fixer,
  surgical_type_fix, improve_type_hints, modernize_typing, fix_deprecated_typing
- **Canonical Target:** `scripts/auto_fix_types.py` or
  `scripts/unified_type_fixer.py` (TBD)
- **Modes:** `--mode add|improve|fix-deprecated|modernize|batch`
- **Expected Impact:** Reduce ~11 overlapping tools to 1 entry point with
  subcommands

### Opportunity 2: Import Management (4 tools → 1 canonical)

- **Scope:** auto_fix_imports, fix_import_order, fix_future_imports,
  clean_unused_ignores
- **Canonical Target:** `scripts/auto_fix_imports.py` (enhance existing)
- **Modes:** `--mode order|future|clean-unused|full`
- **Expected Impact:** Reduce 4 tools to 1 with consistent UI

### Opportunity 3: Logging Fixers (4 tools → 1 canonical)

- **Scope:** fix_logging_calls, fix_logging_fstrings, fix_logging_syntax_errors,
  fix_logging_v2
- **Canonical Target:** `scripts/unified_logging_fixer.py` (new or enhance
  existing)
- **Modes:** `--mode calls|fstrings|syntax|v2|all`
- **Expected Impact:** Reduce 4 overlapping tools to 1

### Opportunity 4: Error Healing Orchestration (6 tools → 1 canonical)

- **Scope:** autonomous_error_fixer, batch_error_fixer, chug_mode_error_fixer,
  surgical_error_fixer, systematic_error_fixer, semantic_auto_fixer
- **Canonical Target:** `scripts/healing_orchestrator.py` (enhance as
  orchestrator)
- **Modes:** `--mode autonomous|batch|chug|surgical|systematic|semantic|full`
- **Expected Impact:** Reduce 6 error fixers to 1 orchestrator with mode-based
  delegation
- **Integration:** Connect to quest system, error_report tool

## Next Steps (Batch 4 Plan)

1. **Analysis** (this phase): Complete tool inventory and category mapping ✅
2. **Selection**: Choose 2-3 highest-impact consolidation targets
   - Primary: Type hints (9 tools, high overlap)
   - Secondary: Error healing (6 tools, quest integration)
   - Tertiary: Logging (4 tools, domain-specific)
3. **Design**: Create detailed plan for each consolidation (similar to Batch 3)
4. **Implementation**:
   - Enhance canonical runners with mode support
   - Create shims for deprecated tools
   - Migrate references in docs/tasks
5. **Validation**: Run smoke tests, verify shim delegation, log quest entry

## Status

- ✅ Discovery: 38 fixer tools identified across 5 categories
- 📋 Analysis: Candidates grouped by type, prioritized by overlap and value
- ⏳ Design: Selection of targets and planning phase pending user confirmation
- ⏳ Implementation: Awaiting design review before proceeding

**Estimated Impact if All 3 Consolidations Complete:**

- 19+ overlapping fixer tools → 3-4 canonical orchestrators
- Unified CLI interface for error fixing, type hints, imports, logging
- ~2-3 days of development + testing + documentation
- Significant improvement in code quality + healing pipeline coherence

---

**Recommendation for User:** Choose which category to tackle first (Type Hints
is highest value due to 9-tool overlap). Proceed with Batch 4a (Type Hints) →
Batch 4b (Error Healing) → Batch 4c (Logging).
