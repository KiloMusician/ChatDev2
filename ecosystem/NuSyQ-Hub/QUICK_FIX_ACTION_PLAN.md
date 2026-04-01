# Quick Fix Action Plan for NuSyQ-Hub Errors

**Generated:** 2026-01-24
**Target:** Reduce 623 errors to manageable levels
**Strategy:** Fix critical errors first, then systematic cleanup

---

## Phase 1: Critical Fixes (Immediate - 5 minutes)

### Fix 1: Add missing imports to `AI_AGENT_COORDINATION_MASTER.py`

**File:** `C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\AI_AGENT_COORDINATION_MASTER.py`
**Lines:** 23-27 (import section)
**Errors Fixed:** 2 critical errors

**Current imports:**
```python
import json
import logging
import subprocess
from pathlib import Path
from typing import Any
```

**Add these lines:**
```python
import os
import sys
```

**Final import block should be:**
```python
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any
```

**Impact:** Fixes 2 "Name not defined" errors at lines 40, 75, and 519.

---

### Fix 2: Check wizard_navigator syntax error

**File:** Referenced in `docs/errors/wizard_navigator_errors.txt`
**Error:** Unterminated string literal at line 1126

**Action:**
1. Locate the actual wizard_navigator file
2. Check line 1126 for unterminated string
3. Fix the string literal (likely missing closing quote)

**Expected location:**
- `src/navigation/wizard_navigator.py` or
- `src/tools/wizard_navigator_consolidated.py`

---

## Phase 2: High-Impact Fixes (30 minutes)

### Fix 3: Address import sorting issues

**Files affected:** Multiple
**Errors:** 46 linting errors from ruff

**Command:**
```bash
cd "C:\Users\keath\Desktop\Legacy\NuSyQ-Hub"
python -m ruff check --select I --fix .
```

This will automatically fix all import ordering issues.

---

### Fix 4: Add type: ignore comments for complex type issues

For files with many type errors that aren't critical:

**Recommended approach:**
```python
# For entire file (use sparingly):
# type: ignore

# For specific lines:
result = some_complex_function()  # type: ignore[assignment]
```

**Files to consider:**
- `src/diagnostics/ecosystem_startup_sentinel.py` (29 errors)
- `src/ml/neural_quantum_bridge.py` (22 errors)
- `src/consciousness/the_oldest_house.py` (14 errors)

---

## Phase 3: Systematic Cleanup (2-4 hours)

### Fix 5: Top 5 Error Files Deep Dive

Target files (143 errors total):

#### 1. `src/diagnostics/ecosystem_startup_sentinel.py` (29 errors)

**Common issues:**
- Line 32: `config_helper` type issue
- Line 321: Unreachable statement

**Strategy:**
- Add proper type annotations for `config_helper`
- Review control flow for unreachable code
- Add `# type: ignore` where appropriate

---

#### 2. `src/integration/Ollama_Integration_Hub.py` (24 errors)

**Strategy:**
- Review type annotations
- Check for missing imports
- Validate function signatures

---

#### 3. `src/main.py` (24 errors)

**Common issues:**
- Tracing module type issues
- Optional imports

**Strategy:**
- Review lines 57-78 (tracing initialization)
- Add proper type guards for optional modules

---

#### 4. `src/ml/neural_quantum_bridge.py` (22 errors)

**Strategy:**
- This appears to be ML-related code
- Many type errors are likely from numpy/torch
- Consider adding type stubs or `# type: ignore`

---

#### 5. `src/consciousness/the_oldest_house.py` (14 errors)

**Strategy:**
- Review architectural pattern
- Fix type annotations
- Check for missing imports

---

### Fix 6: Exclude archived code from type checking

**Create/update:** `mypy.ini` or `pyproject.toml`

```ini
[mypy]
exclude = [
    "src/legacy/.*",
    "src/interface/archived/.*",
    ".venv/.*",
    ".venv.old/.*",
]
```

This will reduce errors by ~36 immediately.

---

## Phase 4: Infrastructure Setup (1 hour)

### Fix 7: Pre-commit hooks

**Create:** `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--ignore-missing-imports]
```

**Install:**
```bash
pip install pre-commit
pre-commit install
```

---

### Fix 8: VSCode settings

**Update:** `.vscode/settings.json`

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.linting.mypyArgs": [
    "--ignore-missing-imports",
    "--follow-imports=skip"
  ],
  "editor.formatOnSave": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.organizeImports": true,
      "source.fixAll": true
    }
  }
}
```

---

## Expected Results

### After Phase 1 (Critical Fixes):
- **Errors:** 621 (from 623) - 2 critical fixes
- **Time:** 5 minutes
- **Impact:** System can run without import errors

### After Phase 2 (High-Impact):
- **Errors:** ~575 (from 621) - 46 import fixes
- **Time:** 30 minutes
- **Impact:** Cleaner imports, better organization

### After Phase 3 (Systematic Cleanup):
- **Errors:** ~400-450 (from 575)
- **Time:** 2-4 hours
- **Impact:** Major reduction in top error files

### After Phase 4 (Infrastructure):
- **Errors:** Ongoing improvement
- **Time:** 1 hour setup
- **Impact:** Prevents new errors, enforces quality

---

## Progress Tracking Commands

### Check current error count:
```bash
python analyze_errors.py
```

### Run mypy on specific file:
```bash
python -m mypy src/main.py
```

### Run all linters:
```bash
python -m flake8 src/
python -m mypy src/
python -m ruff check src/
```

### Auto-fix imports:
```bash
python -m ruff check --select I --fix .
```

---

## Files Created for This Analysis

1. **`ERROR_ANALYSIS_REPORT.md`** - Comprehensive error breakdown
2. **`analyze_errors.py`** - Script to check current state
3. **`QUICK_FIX_ACTION_PLAN.md`** - This file
4. **`DETAILED_ERRORS.txt`** - Detailed error lists

---

## Monitoring Dashboard

Keep these files updated:
- `state/vscode_diagnostics.json` - Real-time VSCode state
- `state/unified_errors.json` - Linter aggregation
- `state/receipts/error_report_*.json` - Historical snapshots

---

## Tips for Success

1. **Fix one file at a time** - Don't try to fix everything at once
2. **Test after each fix** - Make sure you don't break anything
3. **Use `# type: ignore` strategically** - Some type errors aren't worth fixing
4. **Commit frequently** - Small commits are easier to review/revert
5. **Focus on runtime errors first** - Type errors are good to fix but not urgent
6. **Exclude legacy code** - Don't waste time on archived files

---

## Questions to Answer

Before starting fixes, clarify:

1. **Which files are actively used?** - Don't fix unused code
2. **What's the priority?** - Runtime errors > Type errors > Style issues
3. **Can we exclude legacy code?** - Update mypy config to skip archived files
4. **Do we need strict typing?** - Or is `# type: ignore` acceptable for now?

---

## Success Metrics

- **Phase 1:** System runs without import errors ✓
- **Phase 2:** <600 errors (from 623)
- **Phase 3:** <450 errors (from ~575)
- **Phase 4:** New code has 0 errors (enforced by pre-commit)

**Ultimate Goal:** <100 errors in actively maintained code
