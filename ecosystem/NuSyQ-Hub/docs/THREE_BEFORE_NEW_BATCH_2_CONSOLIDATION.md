# Three Before New: Batch 2 Consolidation - Error Reporting Tools

**Date:** 2025-12-27  
**Target:** Error reporting and scanning tools  
**Tools Identified:** 15 (via discovery CLI)

## Tool Inventory

### Tier 1: Documentation/Templates (KEEP - different domain)

1. `docs/AGENT_ERROR_REPORTING_TEMPLATE.md` (score 9.0) - Template for agents
   reporting errors
   - **Action:** KEEP - documentation, not code

### Tier 2: Specialized Error Scanners (KEEP - specific use cases)

2. `scripts/analyze_errors.py` - Mypy error analysis for Stage 5 targets
3. `scripts/analyze_error_report.py` - Extract details from unified error
   reports
4. `scripts/count_all_errors.py` - Count errors from all linting tools
5. `scripts/full_ecosystem_error_scan.py` - Cross-repo error scanner (3 repos)
6. **`scripts/unified_error_aggregator.py`** - CANONICAL: Single source of truth
   for all errors
   - **Action:** KEEP - This is the canonical aggregator

### Tier 3: Error Fixers (CONSOLIDATE - overlapping auto-fix logic)

7. `scripts/autonomous_error_fixer.py` - Ecosystem-guided repair
8. `scripts/batch_error_fixer.py` - Batch fixing with ruff/black/mypy
9. `scripts/boss_rush_error_crusher.py` - Parallel orchestration, easiest-first
10. `scripts/chug_mode_error_fixer.py` - Non-blocking scanner + fixer
11. `scripts/prioritized_error_scanner.py` - Scan + prioritize by difficulty
12. `scripts/fix_logging_syntax_errors.py` - Specific: logging f-string fixes
13. `scripts/fix_type_errors_batch.py` - Specific: Pylance type errors

### Tier 4: Derivative Tools (DELETE - use canonical)

14. `scripts/auto_quest_from_errors.py` - Convert errors to quests (specialized
    use, KEEP)
15. `scripts/expand_zen_codex_from_errors.py` - Add Zen Codex rules from errors
    (specialized use, KEEP)

## Consolidation Plan

### Phase 1: Analysis

- **Canonical Error Aggregator:** `scripts/unified_error_aggregator.py`
- **Canonical Error Fixer (to create):** `scripts/batch_error_fixer.py`
  (enhance)
- **Specialized Scanners:** Keep `full_ecosystem_error_scan.py`,
  `count_all_errors.py`

### Phase 2: Consolidation Target

Merge **5 auto-fixers** into enhanced `scripts/batch_error_fixer.py`:

1. `autonomous_error_fixer.py` → add ecosystem-guided repair
2. `boss_rush_error_crusher.py` → add parallel orchestration
3. `chug_mode_error_fixer.py` → add non-blocking mode
4. `prioritized_error_scanner.py` → add difficulty prioritization
5. Keep specialized: `fix_logging_syntax_errors.py`, `fix_type_errors_batch.py`

Enhanced `batch_error_fixer.py` will have:

- `--mode fast/parallel/ecosystem` (consolidate autonomous, boss_rush,
  chug_mode)
- `--priority easiest/hardest/count` (from prioritized_error_scanner)
- `--filter logging/type/all` (delegate to specialized fixers)
- Integration with `unified_error_aggregator.py` for source of truth

### Phase 3: Migration & Deletion

1. Enhance `scripts/batch_error_fixer.py`
2. Search for references to deleted tools
3. Update references to use new `batch_error_fixer.py --mode X`
4. Delete 3-4 redundant auto-fixers
5. Log to quest system

## Expected Impact

- **Tool count:** 15 → 11 (27% reduction, 4 files deleted)
- **Consolidation:** 5 auto-fixers → 1 enhanced canonical fixer
- **Lines saved:** ~400-500 lines
- **Compliance:** +1 logged three_before_new entry

## Next Step

Completed: Read and analyzed the 5 auto-fixer tools; consolidated into
`scripts/batch_error_fixer.py` with modes `fast`, `boss`, `ecosystem`, `syntax`;
deleted `autonomous_error_fixer.py`, `boss_rush_error_crusher.py`,
`chug_mode_error_fixer.py`, `prioritized_error_scanner.py`; logged quest entry.
