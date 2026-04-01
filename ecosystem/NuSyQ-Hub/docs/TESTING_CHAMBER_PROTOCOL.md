# Testing Chamber Protocol

## Purpose

The **Testing Chamber** is a quarantined development space where agents can safely experiment with new code, prototypes, and AI-generated solutions before promoting them to the canonical codebase. This follows the "overnight safe mode" principle and prevents brownfield pollution.

## Philosophy

> **"Build it separate, test it thoroughly, graduate it intentionally."**

- **Prototypes are disposable** - Failed experiments don't clutter production code
- **Graduation requires proof** - Nothing moves to canonical without validation
- **Safety boundaries** - Restricted operations prevent accidental system damage

## Testing Chamber Locations

### 1. **NuSyQ-Hub Testing Chamber**
- **Location:** `prototypes/`
- **Purpose:** System-level tools, orchestration experiments, integration tests
- **Scope:** Infrastructure and coordination code

### 2. **SimulatedVerse Testing Chamber**
- **Location:** `SimulatedVerse/testing_chamber/`  
- **Purpose:** Consciousness experiments, game mechanics, narrative systems
- **Scope:** Emergent behavior and creative prototyping

### 3. **ChatDev WareHouse**
- **Location:** `NuSyQ/ChatDev/WareHouse/`
- **Purpose:** Multi-agent generated software projects
- **Scope:** Complete applications built by ChatDev team

## Workflow: Create → Test → Graduate

### Phase 1: Create Prototype

```bash
# Create a new Testing Chamber prototype
python scripts/start_nusyq.py testing_chamber create <prototype_name> \
  --location hub|simverse|chatdev \
  --description "What this prototype does"

# Example: Create a new error analyzer
python scripts/start_nusyq.py testing_chamber create smart_error_analyzer \
  --location hub \
  --description "AI-powered error prioritization and auto-fix suggestions"
```

**What Happens:**
1. Creates directory: `prototypes/smart_error_analyzer/`
2. Initializes structure:
   ```
   prototypes/smart_error_analyzer/
   ├── README.md              # Purpose, goals, status
   ├── prototype.py           # Main implementation
   ├── tests/                 # Test suite
   ├── requirements.txt       # Dependencies
   └── graduation_checklist.md # Criteria for promotion
   ```
3. Logs creation to quest system for tracking
4. Opens prototype in VS Code for development

**Safe Mode Restrictions:**
- ✅ Can read from canonical codebase
- ✅ Can write to Testing Chamber
- ✅ Can use local AI models (Ollama)
- ❌ Cannot modify canonical `src/` files
- ❌ Cannot commit to repository
- ❌ Cannot make external API calls to paid services

### Phase 2: Test Prototype

```bash
# Run prototype tests
python scripts/start_nusyq.py testing_chamber test <prototype_name>

# Example: Test with different scenarios
python scripts/start_nusyq.py testing_chamber test smart_error_analyzer \
  --scenarios basic,edge_cases,stress_test
```

**What Happens:**
1. Runs pytest suite in `prototypes/<name>/tests/`
2. Validates against graduation criteria
3. Generates test report with coverage
4. Logs results to quest system
5. Updates `graduation_checklist.md` with pass/fail status

**Testing Criteria:**
- ✅ All unit tests pass (minimum 80% coverage)
- ✅ Integration tests pass
- ✅ No breaking changes to existing code
- ✅ Performance acceptable (benchmark against baseline)
- ✅ Linting passes (black, ruff, mypy)
- ✅ Security scan passes (no secrets, no vulnerabilities)

### Phase 3: Graduate Prototype

```bash
# Graduate prototype to canonical codebase
python scripts/start_nusyq.py testing_chamber graduate <prototype_name> \
  --destination src/diagnostics/ \
  --review

# Example: Graduate after successful testing
python scripts/start_nusyq.py testing_chamber graduate smart_error_analyzer \
  --destination src/diagnostics/smart_error_analyzer.py \
  --review
```

**Graduation Criteria (All Must Pass):**
1. ✅ **Works:** All tests pass with ≥80% coverage
2. ✅ **Documented:** README explains purpose, usage, API
3. ✅ **Useful:** Solves real problem identified in quest system
4. ✅ **Reviewed:** Agent or human approval logged
5. ✅ **Integrated:** Follows "Three Before New" protocol (checked for duplicates)

**What Happens:**
1. Validates all graduation criteria
2. Shows diff preview to user/agent
3. Requests confirmation (or uses `--auto` flag in safe mode)
4. Moves code to canonical location
5. Updates capability inventory
6. Adds to function registry
7. Creates git commit with tagged metadata
8. Archives prototype with success status
9. Logs graduation to quest system

**Failure Cases:**
- ⚠️ If any criteria fail, shows detailed report
- ⚠️ Suggests fixes and re-run of tests
- ⚠️ Prototype stays in Testing Chamber until issues resolved

## Agent Operator Phrases

Tell agents these natural language commands:

### Creation
- **"Create a prototype for [description]"** → Creates new Testing Chamber prototype
- **"Start a new experiment with [tool/feature]"** → Same as above
- **"Build a testing chamber project for [purpose]"** → Routes to ChatDev WareHouse

### Testing
- **"Test [prototype_name]"** → Runs full test suite
- **"Check if [prototype_name] is ready to graduate"** → Validates graduation criteria
- **"Run stress tests on [prototype_name]"** → Executes performance benchmarks

### Graduation
- **"Graduate [prototype_name]"** → Promotes to canonical if criteria met
- **"Promote [prototype_name] to production"** → Same as above
- **"Archive [prototype_name]"** → Marks as failed/abandoned, preserves for learning

### Inspection
- **"Show me testing chamber projects"** → Lists all active prototypes
- **"What's the status of [prototype_name]"** → Shows test results and graduation readiness

## Integration with Agent Systems

### AI Council Voting
Before graduation, agents vote on readiness:
```python
# Automatic council review before graduation
decision = ai_council.propose_decision(
    topic=f"Graduate {prototype_name}",
    description=f"Move {prototype_name} from Testing Chamber to {destination}",
    metadata={"test_results": test_report, "coverage": coverage_pct}
)

# 4 agents vote: Claude, Copilot, Ollama, ChatDev CEO
# Requires at least STRONG consensus (≥80% approve)
```

### Quest System Integration
All Testing Chamber operations log to quest system:
```jsonl
{"type": "testing_chamber_create", "prototype": "smart_error_analyzer", "status": "created", "timestamp": "2026-02-22T02:30:00Z"}
{"type": "testing_chamber_test", "prototype": "smart_error_analyzer", "status": "passed", "coverage": 0.87, "timestamp": "2026-02-22T03:15:00Z"}
{"type": "testing_chamber_graduate", "prototype": "smart_error_analyzer", "destination": "src/diagnostics/", "status": "success", "timestamp": "2026-02-22T03:45:00Z"}
```

### Overnight Safe Mode
When running autonomous overnight cycles:
```bash
python scripts/start_nusyq.py --mode overnight testing_chamber auto_cycle

# Safe mode restrictions:
# - Only creates/tests prototypes, never graduates
# - No external API calls to paid services
# - No canonical file modifications
# - Logs all actions for morning review
```

## File Organization

### Hub Testing Chamber (`prototypes/`)
```
prototypes/
├── active/                      # Currently under development
│   ├── smart_error_analyzer/
│   ├── ai_code_reviewer/
│   └── quest_dependency_graph/
├── graduated/                   # Successfully promoted (archived for reference)
│   ├── council_orchestrator/    # → src/orchestration/
│   └── breathing_monitor/       # → src/integration/
└── abandoned/                   # Failed experiments (learning artifacts)
    ├── broken_import_fixer/     # Better solution found
    └── llm_routing_v1/          # Superseded by v2
```

### SimulatedVerse Testing Chamber
```
SimulatedVerse/testing_chamber/
├── consciousness_experiments/
├── ship_console_prototypes/
├── game_mechanics_sandbox/
└── narrative_generators/
```

### ChatDev WareHouse
```
NuSyQ/ChatDev/WareHouse/
├── DefaultOrganization_<timestamp>/
└── <user_description>_<timestamp>/
```

## Safety Boundaries

### Allowed in Testing Chamber
- ✅ Create new files in Testing Chamber
- ✅ Read any file in ecosystem
- ✅ Use local Ollama models (free)
- ✅ Run tests and benchmarks
- ✅ Generate documentation
- ✅ Log to quest system
- ✅ Propose AI Council decisions

### Restricted in Testing Chamber
- ❌ Modify files outside Testing Chamber
- ❌ Commit to git (manual approval required)
- ❌ Call paid APIs (OpenAI, Anthropic, GitHub Copilot)
- ❌ Delete canonical code
- ❌ Modify system configuration
- ❌ Execute shell commands outside sandbox

### Overnight Safe Mode Additional Restrictions
- ❌ Graduate prototypes (requires human/agent review in morning)
- ❌ Create VS Code extensions
- ❌ Modify VS Code tasks/settings
- ❌ Send notifications

## Examples

### Example 1: Quick Error Analyzer Prototype
```bash
# 1. Create
python scripts/start_nusyq.py testing_chamber create quick_error_scan \
  --location hub \
  --description "Fast ruff error scanner with priority scoring"

# 2. Develop (automatic in VS Code)
# ... agent writes code in prototypes/quick_error_scan/prototype.py ...

# 3. Test
python scripts/start_nusyq.py testing_chamber test quick_error_scan

# 4. Graduate
python scripts/start_nusyq.py testing_chamber graduate quick_error_scan \
  --destination src/diagnostics/quick_error_scanner.py
```

### Example 2: SimulatedVerse Consciousness Experiment
```bash
# Create consciousness prototype
python scripts/start_nusyq.py testing_chamber create proto_consciousness_v3 \
  --location simverse \
  --description "Self-aware agent with temporal reasoning"

# Run in SimulatedVerse sandbox
cd SimulatedVerse/testing_chamber/proto_consciousness_v3
npm run experiment

# If successful, graduate to consciousness system
python scripts/start_nusyq.py testing_chamber graduate proto_consciousness_v3 \
  --destination SimulatedVerse/SimulatedVerse/consciousness/
```

### Example 3: ChatDev Multi-Agent Project
```bash
# ChatDev automatically uses WareHouse as Testing Chamber
python scripts/start_nusyq.py council_loop \
  "Create a Python web scraper with rate limiting and error handling"

# ChatDev team builds in: NuSyQ/ChatDev/WareHouse/Python_Web_Scraper_20260222/
# After review, graduate to canonical location
python scripts/start_nusyq.py testing_chamber graduate Python_Web_Scraper_20260222 \
  --destination scripts/web_scraper.py \
  --from-chatdev
```

## Metrics & Observability

The Testing Chamber tracks:
- **Creation Rate:** Prototypes created per week
- **Graduation Rate:** % of prototypes that graduate vs abandon
- **Time to Graduate:** Average days from creation to promotion
- **Test Coverage:** % of prototypes with ≥80% coverage
- **Council Rejection Rate:** % rejected by AI Council voting

Access dashboard:
```bash
python scripts/start_nusyq.py testing_chamber metrics
```

## Implementation Checklist

Implementation tracked in quest system:

- [ ] Create `scripts/testing_chamber.py` command handler
- [ ] Add `testing_chamber` to KNOWN_ACTIONS in `start_nusyq.py`
- [ ] Implement `create`, `test`, `graduate` subcommands
- [ ] Wire AI Council voting for graduation approval
- [ ] Add quest system logging for all operations
- [ ] Create graduation criteria validator
- [ ] Build test runner with coverage reporting
- [ ] Add safety boundary enforcement
- [ ] Create overnight safe mode rules
- [ ] Generate metrics dashboard
- [ ] Document with VS Code tasks for quick access

---

**Reference:** This protocol enables safe experimentation while maintaining codebase quality. See [AGENTS.md](AGENTS.md) Section 7 for conversational operator phrases.
