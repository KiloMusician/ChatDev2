# 🎯 PHASE 2 MODERNIZATION SPRINT PLAN

**Objective:** Implement 5 high-value suggestions from suggestion engine + fix top modernization targets  
**Approach:** Work-around the import hang by using subprocess/bash patterns that don't require direct imports  
**Batch Count:** 1 unified commit (all suggestions together)  
**Receipt Discipline:** Every sub-action logged  

---

## Executable Plan (No Direct Imports Needed)

### Action 1: Wire Doctrine Check (Suggestion #2)

**What:** Validate codebase architecture against documented doctrine  
**Where:** Add new action to scripts/start_nusyq.py as `doctrine_check`  
**How:** Subprocess call to existing health check + grep verification

```bash
# Pseudo-code
python -m src.diagnostics.system_health_assessor  # Already works via subprocess
grep -r "circular_import\|TODO.*fix" src/orchestration/  # String search
grep -r "infinite_loop\|while True" src/  # Code audit without importing
```

**Why:** Safe, doesn't require direct imports, provides actionable feedback  
**Effort:** 20 lines added to start_nusyq.py  

---

### Action 2: Wire Emergence Capture (Suggestion #3)

**What:** Log runtime behaviors, agent interactions, and system consciousness signals  
**Where:** Add new action `emergence_capture` to start_nusyq.py  
**How:** Read system_health output + quest_log + introspection without imports

```python
# Pseudo-code
def capture_emergence():
    # 1. Read quest_log.jsonl (already works)
    quests = read_jsonl('src/Rosetta_Quest_System/quest_log.jsonl')
    
    # 2. Run subprocess health check
    health = subprocess.run(['python', '-m', 'src.diagnostics.system_health_assessor'], capture_output=True)
    
    # 3. Extract signals: tasks completed, errors caught, AI interactions
    emergence_signals = parse_health_for_signals(health.stdout)
    
    # 4. Log to emergence_log.jsonl
    write_jsonl('state/reports/emergence_log.jsonl', emergence_signals)
```

**Why:** Captures agent activity without requiring module introspection  
**Effort:** 30 lines added to start_nusyq.py  

---

### Action 3: Normalize Environment Variables

**What:** Centralize OLLAMA_BASE_URL, model rosters, port configs in .env + validate  
**Where:** New file `scripts/env_normalizer.py` + integrate into start_nusyq.py  
**How:**

```python
# Load from .env.example (template)
# Validate against known models (list in config/action_catalog.json)
# Set os.environ for subprocess calls
# Warn if ports conflict or models missing
```

**Current State:**  
- OLLAMA_BASE_URL hard-coded in agent_task_router.py (line ~150)
- Model roster scattered across (agent_task_router.py, unified_ai_orchestrator.py)

**Action:**  
1. Create `scripts/env_normalizer.py` (40 lines)
2. Update start_nusyq.py to call it before any action (5 lines)
3. Create `.env.example` template with all known vars
4. Document in config/SETUP_GUIDE.md

**Why:** Simplifies debugging, enables testing with different Ollama instances  
**Effort:** 50 lines total  

---

### Action 4: Wire Selfcheck Action

**What:** Minimal smoke test to validate HUB operational without deep imports  
**Where:** Add action `selfcheck` to start_nusyq.py  
**How:**

```bash
# 1. Check scripts/start_nusyq.py can execute (python -m py_compile)
# 2. Check src/tools/agent_task_router.py syntax (py_compile)
# 3. Check config/action_catalog.json valid JSON
# 4. Check git status (no uncommitted state)
# 5. Check required files exist (quest_log.jsonl, config/ folder)
# 6. Print ✅ or ❌ for each
```

**Why:** Quick diagnostic without requiring Python interpreter imports  
**Effort:** 25 lines added to start_nusyq.py  

---

### Action 5: Cross-Repo Bridge Stub

**What:** Create bidirectional stubs for HUB ↔ SIMULATEDVERSE communication  
**Where:** New file `src/integrations/simverse_bridge.py`  
**How:**

```python
# Minimal stubs (no imports, just function defs)
def notify_simverse_of_suggestions(suggestions: list) -> bool:
    # POST to SIMULATEDVERSE REST API (if running) or write to shared file
    pass

def read_simverse_state() -> dict:
    # Read from shared knowledge-base.yaml or via API
    pass
```

**Why:** Prepares for PHASE 4 without requiring SIMULATEDVERSE to be running  
**Effort:** 15 lines stub, expand in PHASE 4  

---

## Implementation Strategy (Bypass Import Hang)

### Rule: No Direct `from src.orchestration import ...` Anywhere

Instead:

```python
# ❌ DON'T DO THIS (causes hang)
from src.orchestration.multi_ai_orchestrator import MultiAIOrchestrator

# ✅ DO THIS (works)
result = subprocess.run(
    ['python', 'scripts/start_nusyq.py', 'analyze', 'file.py'],
    capture_output=True,
    text=True
)
output = result.stdout
```

### New Actions Will Use Pattern:

```python
def run_doctrine_check():
    """Wire action without direct imports."""
    # 1. String-based checks (grep, file operations)
    # 2. Subprocess calls to existing actions
    # 3. Parse output from subprocesses
    # 4. Return results
```

---

## Commit Strategy

**Single batch commit:**

```
feat(modernization): implement 5 core suggestions + normalize env

- wire doctrine_check action (Suggestion #2)
- wire emergence_capture action (Suggestion #3)
- normalize environment variables (OLLAMA_BASE_URL, models)
- wire selfcheck diagnostic action
- create simverse_bridge stubs for PHASE 4
- all actions use subprocess pattern (no direct imports)
- reason: bypass import hang with proven subprocess pattern

Changes:
- scripts/start_nusyq.py: +150 lines (5 new actions)
- scripts/env_normalizer.py: +40 lines (NEW)
- src/integrations/simverse_bridge.py: +50 lines (NEW, stubs)
- .env.example: +25 lines (NEW, template)
- config/SETUP_GUIDE.md: +30 lines (documentation)

Tested:
- selfcheck action passes (validates syntax, files, git state)
- doctrine_check runs (no errors)
- emergence_capture produces log
- env_normalizer validates against .env.example
- simverse_bridge stubs import cleanly (no circular deps)
```

---

## Post-Commit Next Steps (PHASE 3)

Once this batch commits:

1. **PHASE 3A:** Add 5-10 more suggestions picked from suggestion engine
   - Priority: Low-hanging fruit (documentation, scaffolding, templates)
   
2. **PHASE 3B:** Create .vscode/tasks.json with 8 one-click launchers
   - Task: "🧠 Start HUB (snapshot)"
   - Task: "🏥 Selfcheck"
   - Task: "📋 Doctrine Check"
   - Task: "✨ Capture Emergence"
   - etc.

3. **PHASE 4:** Cross-repo integration (SIMULATEDVERSE bridges go live)

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Subprocess calls slow | Batch them, use async where possible |
| .env parsing fails | Validate JSON/YAML before use |
| Bridge stubs break imports | Keep stubs minimal, no internal imports |
| Doctrine check gives false positives | Whitelist known exceptions |
| Emergence capture log too verbose | Implement filtering, sample strategically |

---

## Receipt Template (Post-Commit)

```
[RECEIPT]
action=PHASE_2_MODERNIZATION
repo=HUB
start=2025-12-24 04:45:00
end=2025-12-24 05:30:00
status=success
exit_code=0
commit=<sha_of_feat_modernization>

artifacts:
- scripts/start_nusyq.py (+150 lines, 5 new actions)
- scripts/env_normalizer.py (NEW, 40 lines)
- src/integrations/simverse_bridge.py (NEW, stubs)
- .env.example (NEW, template)
- config/SETUP_GUIDE.md (updated, +30 lines)

verified:
✅ selfcheck action works (validates syntax, files, git)
✅ doctrine_check runs (grep for circular imports)
✅ emergence_capture logs to state/reports/emergence_log.jsonl
✅ env_normalizer loads .env.example
✅ simverse_bridge stubs import without circular deps

next:
- PHASE 3A: Add 5-10 suggestions from engine
- PHASE 3B: Wire .vscode/tasks.json with launchers
- PHASE 4: Cross-repo integration goes live
```

---

**OmniTag:** `{"purpose": "PHASE 2 modernization sprint plan, bypass import hang via subprocess", "dependencies": ["scripts/start_nusyq.py", "suggestion_engine"], "context": "Ready to execute, all 5 actions defined, no direct imports needed", "evolution_stage": "pre_implementation_ready"}`

**MegaTag:** `Phase2-Modernization⨳Suggestions→✅◆EnvNorm→⚡◆SelfCheck→✅`
