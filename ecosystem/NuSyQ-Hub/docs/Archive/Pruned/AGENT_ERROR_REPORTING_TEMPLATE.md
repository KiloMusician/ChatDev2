# AGENT ERROR REPORTING TEMPLATE

Use this template when reporting on errors, diagnostics, or code quality issues.

---

## Template: Error Status Report

```
🔍 ERROR STATUS REPORT
=======================
Generated: [timestamp]
Ground Truth Source: python scripts/start_nusyq.py error_report

📊 CANONICAL NUMBERS (All Repos)
─────────────────────────────────
Total Diagnostics:  1,541
├─ Errors:          1,228  ← Critical path
├─ Warnings:            0  
└─ Infos/Hints:       313

⚠️  NOTE: VS Code shows ~209 errors (filtered view)
    Full scan shows 1,228 errors (comprehensive analysis)
    ➜ Use 1,228 for planning. 209 is what user currently sees.

📁 BY REPOSITORY
─────────────────────────────────
NuSyQ-Hub:       749 (mostly type errors from mypy)
SimulatedVerse:  463 (mostly style/syntax from ruff)
NuSyQ Root:      329 (code quality + style)

🔨 TOOLS REPORT
─────────────────────────────────
mypy (Type checking):    586 errors in NuSyQ-Hub
ruff (Style + syntax):   955 errors across all repos
pylint (Code quality):     1 error in NuSyQ

🎯 IMPACT PRIORITY
─────────────────────────────────
HIGH   | Type errors (586)      | Break runtime behavior
MEDIUM | Syntax/style (955)     | Auto-fixable, clarity issues
LOW    | Code quality (1)       | Maintainability concerns

💡 NEXT ACTIONS
─────────────────────────────────
1. Fix type errors: mypy errors in NuSyQ-Hub (HIGH IMPACT)
2. Fix syntax: ruff auto-fix across all repos
3. Improve code quality: pylint suggestions
```

---

## Template: Error Progress Report

```
✅ ERROR REDUCTION PROGRESS
============================
Previous Scan: [date] - 1,541 total diagnostics
Current Scan:  [date] - [X] total diagnostics
Progress:      [Y] fixed (-Z%) ✓

📊 BREAKDOWN BY CATEGORY
───────────────────────────────────
Type Errors (mypy):
  Before: 586 → After: [X] → Fixed: [Y] (-Z%)
  Status: [On track / Behind / Ahead]
  
Style/Syntax (ruff):
  Before: 955 → After: [X] → Fixed: [Y] (-Z%)
  Status: [On track / Behind / Ahead]
  
Code Quality (pylint):
  Before: 1 → After: [X] → Fixed: [Y] (-Z%)
  Status: [On track / Behind / Ahead]

📁 BY REPOSITORY
───────────────────────────────────
NuSyQ-Hub:       [X] → [Y] (-Z%)
SimulatedVerse:  [X] → [Y] (-Z%)
NuSyQ Root:      [X] → [Y] (-Z%)

🎯 NEXT 10 BLOCKERS
───────────────────────────────────
1. [Error type]: [file]: [message]
2. [Error type]: [file]: [message]
... (top 10)

🚀 RECOMMENDED NEXT STEPS
───────────────────────────────────
1. Run: ruff check --fix (auto-fix style issues)
2. Review: mypy errors in NuSyQ-Hub (manual fixes needed)
3. Action: Fix top blocker - [specific error]
```

---

## Template: Discrepancy Resolution

**When two agents report different error counts:**

```
🔄 SIGNAL SYNCHRONIZATION
===========================

Agent A reports:  [X] errors
Agent B reports:  [Y] errors
Discrepancy:      [Z] errors difference

🧠 DIAGNOSIS
─────────────────────────────────
Likely causes:
□ Different tools used
□ Different scan scope
□ Different file filtering
□ Outdated cached data
□ Configuration differences

🔍 GROUND TRUTH CHECK
─────────────────────────────────
Running canonical source:
$ python scripts/start_nusyq.py error_report

Ground Truth Result: [1,228 errors]
Canonical Source: Unified Error Reporter
Tools Used: mypy (586), ruff (955), pylint (1)

✅ RESOLUTION
─────────────────────────────────
Agent A: [Reason for difference]
Agent B: [Reason for difference]
Canonical: [X] errors is correct because [reason]

→ Both agents should now report: [X] errors
  (Cite: docs/SIGNAL_CONSISTENCY_PROTOCOL.md)
```

---

## Template: Error Analysis for Specific File

```
🔎 ERROR ANALYSIS: [filename]
=============================

File: [path/to/file.py]
Language: [Python/TypeScript/etc.]
Total Issues: [X]

📊 ISSUE BREAKDOWN
─────────────────────────────────
Type:     [error type]  Count: [X]  Severity: [HIGH/MEDIUM/LOW]
Tool:     [mypy/ruff/pylint]
Status:   [Critical/Fixable/Optional]

🚨 CRITICAL ERRORS ([X])
─────────────────────────────────
1. Line [N]: [error message]
   Tool: [mypy/ruff/pylint]
   Impact: [what breaks if not fixed]
   Fix: [suggested fix]

... (top 3-5)

⚡ QUICK FIXES ([X])
─────────────────────────────────
1. Line [N]: [error message]
   Command: ruff check --fix
   Auto-fixable: [Yes/No]

💡 RECOMMENDATIONS
─────────────────────────────────
Priority order:
1. [specific error] - [reason]
2. [specific error] - [reason]
3. [specific error] - [reason]
```

---

## Key Points for All Agents

✅ **Always include:**
- Timestamp of scan
- Ground truth command (`python scripts/start_nusyq.py error_report`)
- Breakdown by repository
- Distinction between VS Code view (209) and full scan (1,228)

✅ **When reporting progress:**
- Use previous numbers as baseline
- Show % improvement
- List top blockers that remain
- Suggest next actions with impact estimates

✅ **When errors don't match:**
- Run ground truth command immediately
- Document the discrepancy
- Use canonical numbers going forward
- Explain why the difference exists

❌ **Never:**
- Report conflicting numbers without checking ground truth
- Ignore the VS Code vs. scan difference
- Claim 209 is the "true" count without explaining filtering
- Use outdated error counts without re-scanning

---

## Integration Example

```python
# In agent code:
from src.diagnostics.unified_error_reporter import UnifiedErrorReporter
from pathlib import Path

def report_errors():
    reporter = UnifiedErrorReporter(Path("."))
    report = reporter.scan_all_repos()
    
    # Use report to inform agent decisions
    total = report["total_diagnostics"]
    errors = report["by_severity"]["errors"]
    
    print(f"Ground Truth: {total} diagnostics ({errors} errors)")
    print("Using this for all downstream decisions")
```

---

**Version:** 1.0  
**Last Updated:** 2025-12-25  
**Used by:** All NuSyQ System Agents  
**Reference:** docs/SIGNAL_CONSISTENCY_PROTOCOL.md
