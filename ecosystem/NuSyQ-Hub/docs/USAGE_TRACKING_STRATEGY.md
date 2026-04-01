# Orphaned Symbol Usage Tracking Strategy

**Generated:** 2026-02-17  
**Context:** Phase 1 rehabilitation complete, need metrics for adoption

## The Challenge

After rehabilitating 50 orphaned symbols across 5 phases, we need to measure:
1. **Discovery** - Did developers/agents find the capabilities?
2. **Adoption** - Are they being used?
3. **Value** - Did they solve problems?
4. **Retention** - Will they continue being used?

## 10 Usage Tracking Methods

### 1. Action Receipts (Already Implemented ✅)
**Location:** `docs/tracing/RECEIPTS/*.txt`  
**Tracks:** CLI command executions with timestamps, inputs, outputs

```python
# Every start_nusyq.py action emits receipt
receipt_path = emit_receipt(
    action="examples",
    status="success",
    inputs={"argv": ["examples", "--list"]},
    outputs=[]
)
```

**Query:** `grep -r "action.id: examples" docs/tracing/RECEIPTS/ | wc -l`  
**Dashboard:** Count receipts per action, aggregate by week/month

---

### 2. Nogic Call Graph Evolution (Planned)
**Location:** `Reports/nogic_analysis/*.json`  
**Tracks:** Function call references over time

**Before Rehabilitation:**
```json
{
  "symbol": "example_1_basic_ollama",
  "call_count": 0,
  "callers": []
}
```

**After Integration:**
```json
{
  "symbol": "example_1_basic_ollama", 
  "call_count": 2,
  "callers": [
    "scripts/run_examples_interactive.py:run_example",
    "tests/test_examples.py:test_basic_ollama"
  ]
}
```

**Query:** Daily Nogic snapshot → track `call_count` delta  
**Automation:** `scripts/track_symbol_resurrection.py` compares yesterday vs today

---

### 3. Quest Completion Tracking (Culture Ship Integration)
**Location:** `src/Rosetta_Quest_System/quest_log.jsonl`  
**Tracks:** Generated quests like "Try Example: Batch Processing"

**Quest Template:**
```python
{
  "quest_id": "learn-example-batch-processing",
  "title": "Try Example: Batch Processing",
  "status": "completed",  # When user runs `examples --example=9`
  "symbol_rehabilitated": "example_9_batch_processing",
  "completion_time": "2026-02-18T14:32:00Z"
}
```

**Automation:** When action receipt shows `examples --example=9`, auto-complete quest  
**Dashboard:** Track completion rate per orphaned symbol

---

### 4. Test Coverage Delta (pytest-cov)
**Location:** `.coverage` database  
**Tracks:** Which orphaned functions are now exercised by tests

**Before:**
```bash
examples/claude_orchestrator_usage.py::example_1_basic_ollama  0%
```

**After (with tests):**
```bash
examples/claude_orchestrator_usage.py::example_1_basic_ollama  87%
```

**Query:** `pytest --cov=examples --cov-report=json`  
**Metric:** Coverage % for orphaned symbols directory

---

### 5. Git History Analysis (blame & log)
**Location:** `.git/`  
**Tracks:** Which commits reference rehabilitated symbols

```bash
# Find all commits mentioning an orphaned symbol
git log --all --grep="example_1_basic_ollama" --oneline

# Find who's importing the symbol
git grep "from examples.claude_orchestrator_usage import example_1"
```

**Automation:** `scripts/symbol_adoption_history.py` runs git blame on orphan files  
**Metric:** Commits per month that touch orphaned symbols

---

### 6. Import Graph Analysis (AST parsing)
**Location:** All `.py` files  
**Tracks:** Which modules import rehabilitated functions

**Tool:** Python AST walker
```python
import ast

class ImportTracker(ast.NodeVisitor):
    def visit_ImportFrom(self, node):
        if node.module == "examples.claude_orchestrator_usage":
            print(f"Import found: {node.names} in {self.filename}")
```

**Query:** `python scripts/track_orphan_imports.py`  
**Metric:** Number of files importing from `examples/`, `deploy/ollama_mock/`, etc.

---

### 7. Terminal History Mining (Command frequency)
**Location:** PowerShell history, bash history  
**Tracks:** How often users type rehabilitated commands

```powershell
# Parse PowerShell history for "examples" command
Get-Content (Get-PSReadLineOption).HistorySavePath | 
  Select-String "start_nusyq.py examples" | 
  Measure-Object
```

**Metric:** Command frequency per day/week  
**Limitation:** Only captures manual invocations, not programmatic

---

### 8. Observability Traces (OpenTelemetry)
**Location:** `docs/tracing/` spans  
**Tracks:** Function executions with duration, errors, context

**If functions are instrumented:**
```python
from opentelemetry import trace

@trace.get_tracer(__name__).start_as_current_span("example_1_basic_ollama")
def example_1_basic_ollama():
    # ... function body
```

**Query:** Count spans with name matching orphaned symbols  
**Dashboard:** Trace frequency, latency, error rate per symbol

---

### 9. VS Code Task Analytics (If telemetry enabled)
**Location:** VS Code telemetry or custom logging  
**Tracks:** Which tasks users run from `Tasks: Run Task` menu

**Custom Implementation:**
```jsonc
// .vscode/tasks.json
{
  "label": "📚 NuSyQ: Interactive Examples",
  "command": "python",
  "args": ["scripts/start_nusyq.py", "examples"],
  "problemMatcher": [],
  // Custom: Log to file when task starts
  "dependsOn": "log-task-invocation"
}
```

**Metric:** Task run count per symbol category

---

### 10. Lifecycle Catalog Metrics (System-wide usage)
**Location:** `docs/lifecycle_catalog_latest.json`  
**Tracks:** High-level system events, potentially including function calls

**Schema:**
```json
{
  "event": "function_invocation",
  "function": "example_1_basic_ollama",
  "timestamp": "2026-02-18T10:30:00Z",
  "caller": "run_examples_interactive.py",
  "result": "success"
}
```

**Automation:** If we add lifecycle logging to orphaned functions  
**Dashboard:** Aggregate invocations per function per day

---

## Recommended Implementation Priority

### Immediate (No Code, Query Existing Data)
1. ✅ **Action Receipts** - Already working, just grep RECEIPTS/
2. ✅ **Git History** - One-liner: `git log --all --grep="examples"`
3. ✅ **Import Graph** - One-liner: `git grep "from examples"`

### Quick Win (1-2 Hours)
4. **Nogic Call Graph Delta** - Run Nogic daily, diff JSON results
5. **Test Coverage Delta** - `pytest --cov=examples` before/after
6. **Terminal History** - Parse PowerShell history with Select-String

### Strategic (Half-Day Each)
7. **Quest Completion Tracking** - Wire quest auto-completion to receipts
8. **Observability Traces** - Instrument orphaned functions with @trace
9. **VS Code Task Analytics** - Custom logging for task invocations

### Advanced (Future)
10. **Lifecycle Catalog Metrics** - Full event stream for all functions

---

## Success Dashboard (Mockup)

```
╔════════════════════════════════════════════════════════════════╗
║ Orphaned Symbol Resurrection Metrics - Week 7, 2026           ║
╠════════════════════════════════════════════════════════════════╣
║ Phase 1: Documentation Examples (12 symbols)                  ║
║   📚 Total Executions:           47 (via action receipts)      ║
║   👤 Unique Users:                3 (via git history)          ║
║   🧪 Test Coverage:              +42% (0% → 42%)               ║
║   📞 Call References:            +8 (Nogic delta)              ║
║   ⭐ Most Popular:               example_1_basic_ollama (18x)  ║
║                                                                ║
║ Phase 2: Factory Functions (4 symbols)                        ║
║   🏭 Total Invocations:          12 (via receipts)            ║
║   📞 Call References:            +4 (Nogic delta)              ║
║   🧪 Test Coverage:              +25% (0% → 25%)               ║
║                                                                ║
║ Phase 3: Mock Infrastructure (6 symbols)                      ║
║   🎭 Pytest Fixture Uses:        23 (via test logs)           ║
║   ✅ CI/CD Speedup:              -45% runtime (mock vs real)   ║
║                                                                ║
║ Overall:                                                       ║
║   Orphaned Symbols: 50 → 28 (-44% through integration)        ║
║   Adoption Rate:    22/22 rehabilitated (100% used at least 1x)║
╚════════════════════════════════════════════════════════════════╝
```

---

## Automation: `scripts/symbol_resurrection_dashboard.py`

**Concept:**
```python
#!/usr/bin/env python3
"""Track adoption of rehabilitated orphaned symbols."""

import subprocess
from pathlib import Path
import json

class SymbolResurrectionTracker:
    def __init__(self, orphan_list_file: Path):
        self.orphans = json.loads(orphan_list_file.read_text())
    
    def check_action_receipts(self):
        """Count action receipts for each symbol."""
        receipts = Path("docs/tracing/RECEIPTS").glob("*.txt")
        counts = {}
        for symbol in self.orphans:
            count = sum(1 for r in receipts if symbol in r.read_text())
            counts[symbol] = count
        return counts
    
    def check_nogic_calls(self):
        """Compare call graph from last week."""
        # Load latest Nogic snapshot
        # Compare to snapshot from 7 days ago
        # Return delta per symbol
        pass
    
    def check_test_coverage(self):
        """Run pytest-cov on orphaned symbols only."""
        result = subprocess.run(
            ["pytest", "--cov=examples", "--cov-report=json"],
            capture_output=True
        )
        # Parse coverage data
        return {}
    
    def generate_dashboard(self):
        """Combine all metrics into markdown dashboard."""
        receipts = self.check_action_receipts()
        calls = self.check_nogic_calls()
        coverage = self.check_test_coverage()
        
        # Render ASCII dashboard like above
        print("╔" + "═" * 62 + "╗")
        # ...
```

**Usage:**
```bash
# Daily cron job
python scripts/symbol_resurrection_dashboard.py > Reports/symbol_adoption.md
```

---

## Related Documents
- `docs/ORPHANED_SYMBOLS_MODERNIZATION_PLAN.md` - Rehabilitation strategy
- `docs/PHASE_1_COMPLETE_EXAMPLES_INTEGRATION.md` - First 12 symbols
- `src/Rosetta_Quest_System/quest_log.jsonl` - Quest completion data

**Next:** Implement Phases 2-5, then add tracking for each.
