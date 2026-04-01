# AGENT ERROR REPORTING REFERENCE CARD

## Quick Facts

| Metric | Value | Source |
|--------|-------|--------|
| **VS Code Reports** | 209 errors | Problem panel |
| **Ground Truth** | 1,541 diagnostics | Unified scanner |
| **Actual Errors** | 1,228 | mypy + ruff + pylint |
| **Highest Priority** | Type errors (586) | mypy in NuSyQ-Hub |

## The Big Picture

```
┌─────────────────────────────────────────────────────────────┐
│  GROUND TRUTH: 1,541 DIAGNOSTICS (Tool-derived)            │
│  ├─ 1,228 ERRORS (CRITICAL)                                │
│  │  ├─ Type errors: 586 (mypy)                             │
│  │  ├─ Syntax errors: 90 (ruff)                            │
│  │  └─ Linting errors: 552 (ruff + pylint)                 │
│  ├─ 0 WARNINGS                                              │
│  └─ 313 INFOS/HINTS                                        │
│                                                             │
│  VS CODE VIEW: 209 errors (filtered subset)                │
│  Reason: Language server config, file exclusions, etc.     │
└─────────────────────────────────────────────────────────────┘
```

## What Each Tool Reports

### mypy (Type Checking)
- **Where:** NuSyQ-Hub
- **Count:** 586 type errors
- **Severity:** HIGH (breaks runtime)
- **Fixable:** Some auto-fixable, some need manual updates

### ruff (Style + Syntax)
- **Where:** All three repos
- **Count:** 955 style/syntax issues
- **Severity:** MEDIUM (auto-fixable in many cases)
- **Fix command:** `ruff check --fix`

### pylint (Code Quality)
- **Where:** NuSyQ Root
- **Count:** 1 code quality issue
- **Severity:** LOW (maintainability)

## Repository Breakdown

```
NuSyQ-Hub:      749 errors   ← Type-heavy (mostly mypy)
SimulatedVerse: 463 errors   ← Syntax/style-heavy (ruff)
NuSyQ Root:     329 errors   ← Code quality (ruff + pylint)
```

## Honest Assessment

**The user sees 209 errors in VS Code but the codebase actually has 1,228 errors when fully scanned.** This is not a mistake—it's a **filtering difference**:

- VS Code shows errors from enabled language servers
- Full scan includes all tools (mypy, ruff, pylint)
- VS Code might exclude certain file types or directories
- Tools perform **comprehensive, offline** analysis

**Recommendation:** Use the **1,228 number as the true scope** for planning and priority. The 209 in VS Code is just what's currently visible.

## When Reporting to Users

### Template Response

> "The VS Code problem panel shows 209 errors, which is the subset currently configured. However, a comprehensive scan of all three repositories using mypy, ruff, and pylint reveals 1,228 actual errors (1,541 total diagnostics including warnings/infos). Here's the breakdown:
>
> **Critical (Type Errors):** 586 errors from mypy  
> **Medium (Style/Syntax):** 955 errors from ruff  
> **Low (Code Quality):** 1 error from pylint  
>
> To fix highest-impact issues first, I recommend starting with type errors (586), then syntax/style (955)."

## Quick Commands for Agents

```bash
# Get ground truth
python scripts/start_nusyq.py error_report

# Get JSON for programmatic use
python -c "from src.diagnostics.unified_error_reporter import UnifiedErrorReporter as U; import json; print(json.dumps(U().scan_all_repos(), indent=2, default=str))"

# Quick status
python scripts/start_nusyq.py brief
```

## Decision Tree

```
User says: "There are 209 errors in VS Code"
├─ Correct!
├─ But actual codebase scan shows 1,228 errors
├─ Use 1,228 for:
│  ├─ Priority planning
│  ├─ Impact estimates
│  └─ Progress tracking
└─ Use 209 for:
   ├─ Current VS Code display
   └─ What user currently sees
```

## Key Insight

**The discrepancy is NORMAL and EXPECTED.** It means:
- ✅ VS Code is properly filtering (not overwhelming the user)
- ✅ Tools are catching real issues (type errors, style problems)
- ✅ Ground truth scanning is working (1,228 is accurate)
- ✅ There's a clear remediation plan

---

**Use the ground truth (1,228 errors) for technical planning.**  
**Acknowledge VS Code's 209 when communicating with users about their view.**  
**All agents should cite this card when reporting error counts.**
