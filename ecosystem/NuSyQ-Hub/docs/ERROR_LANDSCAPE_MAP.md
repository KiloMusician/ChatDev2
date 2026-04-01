# Error Landscape Map (Grounded)

Ground truth report:
- docs/Reports/diagnostics/unified_error_report_20260108_231504.md
- docs/Reports/diagnostics/unified_error_report_20260108_231504.json

## 1) Canonical Counts (Tool Scan)

From `docs/Reports/diagnostics/unified_error_report_20260108_231504.md`:
- Total diagnostics: 2856
- Errors: 64
- Warnings: 118
- Infos: 2674
- Repo coverage:
  - nusyq-hub: 2856 (errors 64, warnings 118, infos 2674)
  - simulated-verse: 0
  - nusyq: 0
- Types: linting 2796, type 60
- Sources: ruff 2796, mypy 60

Note: The unified report only embeds the first 50 diagnostic details. Use the
detail extraction workflow below to group errors by root cause.

## 2) Error Detail Extraction (Repeatable)

Command used to extract error details:
```bash
python - <<'PY'
from pathlib import Path
from collections import Counter
import re
from src.diagnostics.unified_error_reporter import UnifiedErrorReporter, ErrorSeverity

hub = Path('.').resolve()
reporter = UnifiedErrorReporter(hub_path=hub)
reporter.scan_all_repos(quick=False)
errors = [d for d in reporter.all_diagnostics if d.severity == ErrorSeverity.ERROR]

code_re = re.compile(r"\\[([a-z0-9\\-]+)\\]\\s*$", re.IGNORECASE)
code_counts = Counter()
for d in errors:
    match = code_re.search(d.message or "")
    code = match.group(1) if match else "unknown"
    code_counts[code] += 1

file_counts = Counter(str(d.file_path) for d in errors)
print("errors_total", len(errors))
print("code_counts", code_counts)
print("file_counts", file_counts)
PY
```

Observed on-demand scan (same toolchain, full mode):
- Errors total: 60 (all mypy type errors)
- Top error codes:
  - attr-defined: 10
  - return-value: 7
  - assignment: 6
  - unreachable: 6
  - no-any-return: 5
  - operator: 4
  - no-redef: 4
  - var-annotated: 4
  - import: 4
  - func-returns-value: 3
  - union-attr: 2
  - arg-type: 1
  - unused-ignore: 1

Discrepancy note:
- Canonical report shows 64 errors; the detailed scan above produced 60.
- Re-run `python scripts/start_nusyq.py error_report --force` to refresh the
  canonical report, then re-run the detail extraction to reconcile.

## 3) Error Hotspots (By File)

Top files by error count from the on-demand scan:
- src/analysis/broken_paths_analyzer.py: 10
- src/ai/ollama_chatdev_integrator.py: 6
- src/analysis/quantum_analyzer.py: 5
- src/tools/agent_task_router.py: 4
- src/healing/quantum_problem_resolver.py: 4
- src/ai/ChatDev-Party-System.py: 4
- src/automation/auto_theater_audit.py: 4
- src/setup/secrets.py: 3
- src/analysis/repository_analyzer.py: 3
- src/Rosetta_Quest_System/quest_engine.py: 2
- src/ai/ai_intermediary.py: 2
- src/agents/autonomous_development_agent.py: 2

## 4) Root Cause Groups + Fix Strategy

Type-only errors dominate the current scan. Recommended fixes by code:

- attr-defined: missing attributes or dynamic members
  - Add attributes to classes, or annotate with Protocols/TypedDicts.
- return-value / func-returns-value: missing or incorrect return statements
  - Ensure functions return declared types on all paths.
- assignment: incompatible type assignments
  - Align variable annotations with assigned values.
- unreachable: dead code paths
  - Remove or refactor conditional logic.
- no-any-return: functions declared with concrete types return Any
  - Add explicit casts or narrower types.
- operator: invalid operations between types
  - Add type guards or convert operands.
- no-redef: name redefinitions in same scope
  - Rename or deduplicate definitions.
- var-annotated: missing variable annotations
  - Add type annotations to module-level variables.
- import: missing stubs or unresolved imports
  - Add stubs (e.g., `types-PyYAML`, `types-aiofiles`) or guard imports.
- union-attr: optional values used without null check
  - Add `if x is None` guards or use `assert x is not None`.
- unused-ignore: remove unnecessary type ignores
  - Delete unused ignores or fix underlying type issue.

## 5) Next Actions (Grounded)

1) Refresh canonical report:
   - `python scripts/start_nusyq.py error_report --force`
2) Re-run detail extraction to sync counts.
3) Triage hotspots in order (broken_paths_analyzer, ollama_chatdev_integrator,
   quantum_analyzer, agent_task_router).
