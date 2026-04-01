# Ruff Configuration Fix - Error Reporting Alignment

**Date:** 2026-01-02  
**Issue:** Ruff was reporting 1,310 E402 + E501 errors despite `ignore` rules in
`pyproject.toml`  
**Root Cause:** Deprecated ruff configuration syntax in `pyproject.toml`  
**Status:** ✅ FIXED

## Problem

The `pyproject.toml` used the deprecated `[tool.ruff]` and
`[tool.ruff.per-file-ignores]` syntax, which modern ruff (0.1.x+) no longer
respects fully. When running `ruff check` with `--output-format json`, all
violations were reported regardless of the `ignore` rules.

### Error Distribution Before Fix

```
Total Violations Reported: 1,310
├── E402 (module-level-import-not-at-top): 438 errors
└── E501 (line-too-long): 872 errors
```

These were intentional design patterns (defensive imports in functions, long
docstrings) that should have been suppressed by the config.

## Solution

### 1. Updated Ruff Configuration Syntax

Changed from deprecated syntax:

```toml
[tool.ruff]
select = [...]
ignore = [...]
per-file-ignores = { ... }

[tool.ruff.pydocstyle]
convention = "google"
```

To modern syntax:

```toml
[tool.ruff]
line-length = 120
exclude = [...]

[tool.ruff.lint]
select = [...]
ignore = [...]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = [...]
"tests/**/*.py" = [...]
...

[tool.ruff.lint.pydocstyle]
convention = "google"
```

### 2. Updated UnifiedErrorReporter

Modified
[`src/diagnostics/unified_error_reporter.py`](src/diagnostics/unified_error_reporter.py#L408-L422)
to explicitly pass the `--config` flag:

```python
def _scan_with_ruff(self, repo_name: RepoName, repo_path: Path) -> list[ErrorDiagnostic]:
    """Scan repository with ruff."""
    ...
    config_file = repo_path / "pyproject.toml"
    cmd = [
        "python", "-m", "ruff", "check",
        *[str(target) for target in targets],
        "--output-format", "json",
    ]
    if config_file.exists():
        cmd.extend(["--config", str(config_file)])  # ← Ensures config is loaded
    ...
```

## Results

### Error Report After Fix

```
CANONICAL GROUND TRUTH (tool_scan):
  • Total:    2310
  • Errors:   5
  • Warnings: 57
  • Infos:    2248
```

**What Changed:**

- ✅ E402 + E501 errors **NO LONGER reported** by ruff (properly suppressed)
- ✅ Remaining errors are legitimate violations (D415, T201, D107, RUF100,
  UP035, UP006)
- ✅ Error counts now stable and consistent across all agents

### Suppressed Error Codes

| Code      | Description                    | Reason                                        | Count             |
| --------- | ------------------------------ | --------------------------------------------- | ----------------- |
| E402      | Module-level import not at top | Defensive fallback imports are intentional    | ~438 (suppressed) |
| E501      | Line too long                  | Handled by line-length setting                | ~872 (suppressed) |
| F401      | Unused imports                 | Re-exports in `__init__.py` are intentional   | Per-file rule     |
| E741      | Ambiguous variable name        | Used intentionally in comprehensions          | Global rule       |
| D100-D103 | Missing docstrings             | Legacy files being refactored                 | Global rule       |
| N802-N806 | Naming conventions             | Culture-Ship uses PascalCase, Unicode symbols | Global rule       |
| C901      | Function too complex           | Quantum resolvers are inherently complex      | Global rule       |
| B008      | Mutable defaults               | Handled correctly in code                     | Global rule       |

## Files Modified

1. **`pyproject.toml`** - Updated ruff configuration syntax to modern format
2. **`src/diagnostics/unified_error_reporter.py`** - Added explicit `--config`
   flag to ruff command

## Verification

To verify the fix is working:

```bash
# Run unified error report
python scripts/start_nusyq.py error_report --quick

# Or run ruff directly with config
cd C:\Users\keath\Desktop\Legacy\NuSyQ-Hub
python -m ruff check src/ --config pyproject.toml --output-format json
```

Expected output: No E402 or E501 errors reported.

## Impact on Error Signal Consistency

This fix ensures that:

- ✅ All agents (Copilot, Claude, Ollama) see the same error counts
- ✅ VS Code Problems panel reflects intentional design choices
- ✅ Error reports from `error_report` command are authoritative
- ✅ Configuration is maintainable and follows modern ruff standards

## Related Documentation

- **SIGNAL_CONSISTENCY_PROTOCOL.md** - How all agents synchronize on error
  counts
- **AGENT_ERROR_REFERENCE_CARD.md** - Quick reference for error categories
- **docs/AGENTS.md** - Agent navigation and self-healing protocol
