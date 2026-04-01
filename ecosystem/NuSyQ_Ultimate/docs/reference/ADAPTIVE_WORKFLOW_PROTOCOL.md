<!--
╔══════════════════════════════════════════════════════════════════════════╗
║ ΞNuSyQ OmniTag Metadata                                                  ║
╠══════════════════════════════════════════════════════════════════════════╣
║ FILE-ID: nusyq.docs.reference.adaptive-workflow                        ║
║ TYPE: Markdown Document                                                 ║
║ STATUS: Production                                                      ║
║ VERSION: 1.0.0                                                          ║
║ TAGS: [workflow, automation, adaptive, rube-goldberg, orchestration]   ║
║ CONTEXT: Σ∞ (Global Orchestration Layer)                               ║
║ AGENTS: [ClaudeCode, AllAgents]                                        ║
║ DEPS: [OMNITAG_SPECIFICATION.md, knowledge-base.yaml, search_omnitags]║
║ INTEGRATIONS: [ΞNuSyQ-Framework, Ollama-API, ChatDev]                  ║
║ CREATED: 2025-10-06                                                     ║
║ UPDATED: 2025-10-06                                                     ║
║ AUTHOR: Claude Code + KiloMusician                                      ║
║ STABILITY: High (Production Ready)                                      ║
╚══════════════════════════════════════════════════════════════════════════╝
-->

# ΞNuSyQ Adaptive Workflow Protocol
## Rube Goldberg Machine for Intelligent Problem Resolution

**Version**: 1.0.0
**Status**: Active ✓
**Purpose**: Flexible order-of-operations leveraging all repository capabilities

---

## 🎯 The Problem

**Question**: "How do I maximize capabilities when there are errors, issues, and warnings?"

**Challenge**:
- Multiple problems exist (35 issues: docstrings, type hints, etc.)
- Need flexible workflow that adapts to context
- Must leverage: OmniTags, Multi-AI agents, Ollama, ChatDev, Continue.dev
- Need self-reminder system so I don't forget capabilities

**Solution**: Adaptive Workflow Protocol - A "Rube Goldberg" cascade system

---

## 🔄 The Adaptive Workflow Machine

### Core Philosophy
**"Chain reactions, not checklists"**

Instead of fixed steps, trigger cascading workflows based on:
1. **Problem Detection** → Auto-classify via OmniTags
2. **Agent Selection** → Route to best AI via AGENTS field
3. **Capability Leverage** → Use all available tools
4. **Self-Reminder** → Check capabilities before every action

---

## 🎰 The Workflow Decision Tree

```
[START] Problem Detected
    ↓
[STEP 1] Classify Problem Type
    → Syntax Error? → Fix immediately → ✓
    → Missing Docs? → Route to Ollama qwen2.5-coder:7b → ✓
    → Architecture? → Route to Claude + gemma2:9b consensus → ✓
    → New Feature? → Route to ChatDev → ✓
    → Refactor? → Route to Continue.dev + Claude review → ✓
    ↓
[STEP 2] Check OmniTags
    → Query: Which files are involved?
    → Query: What CONTEXT level (Σ)?
    → Query: Which AGENTS compatible?
    → Query: What DEPS affected?
    ↓
[STEP 3] Select Optimal Agent(s)
    → Single agent for simple tasks
    → Multi-agent consensus for complex/critical
    → ChatDev for full projects
    ↓
[STEP 4] Execute with Monitoring
    → Track progress with TodoWrite
    → Update knowledge-base.yaml
    → Update file OmniTags (VERSION, UPDATED)
    ↓
[STEP 5] Verify and Document
    → Run validation (analyze_problems.py)
    → Search OmniTags to verify changes
    → Update documentation
    ↓
[END] Problem Resolved → Update Knowledge Base
```

---

## 🧠 Self-Reminder System: "Capability Checklist"

### Before Every Task, Claude Code Asks:

#### 1. **Can I Delegate This?**
```
✓ Ollama models available? (7 models local, free)
  → qwen2.5-coder:14b for complex
  → qwen2.5-coder:7b for quick
  → gemma2:9b for reasoning

✓ ChatDev available? (5 agents: CEO/CTO/Programmer/Reviewer/Tester)
  → Good for: Full projects, multi-file changes

✓ Continue.dev available? (7 Ollama models + embeddings)
  → Good for: Interactive development, codebase search
```

**Rule**: If I can delegate to free Ollama, DO IT. Save API costs.

#### 2. **Can I Search Semantically?**
```
✓ OmniTags available? (17 files tagged)
  → Search by: TAG, CONTEXT, AGENT, STATUS
  → Find affected files instantly

Command: python scripts/search_omnitags.py --<criteria>
```

**Rule**: Always search OmniTags before modifying files. Find related files.

#### 3. **Can I Get Multi-Model Consensus?**
```
✓ For critical decisions (security, architecture):
  → Run 3 models in parallel
  → Synthesize consensus
  → Higher confidence

Example:
  ollama run qwen2.5-coder:14b "Security audit: [code]"
  ollama run gemma2:9b "Security implications: [code]"
  ollama run codellama:7b "OWASP check: [code]"
```

**Rule**: Critical = 3 models. Simple = 1 model. Cost-effective = always Ollama first.

#### 4. **Am I Tracking Progress?**
```
✓ TodoWrite for multi-step tasks
✓ knowledge-base.yaml for completions
✓ OmniTag UPDATED field for file changes
```

**Rule**: Track everything. Future Claude needs context.

#### 5. **Am I Using Fractal Coordination?**
```
✓ Σ∞ files affected? (Global impact)
✓ Σ1 files affected? (Component impact)
✓ Σ2 files affected? (Feature impact)

Query OmniTags to find hierarchical dependencies.
```

**Rule**: Understand impact radius via CONTEXT levels.

---

## 🎪 The Rube Goldberg Workflow Examples

### Example 1: "Fix All Docstrings" (33 missing)

**Traditional Approach**:
```
1. Read each file manually
2. Write docstrings one by one
3. Takes: 2-3 hours
4. Cost: High API usage
```

**Adaptive Workflow Approach**:
```
[DETECT] 33 missing docstrings found

[CLASSIFY] Style issue, not critical
  → Priority: Medium
  → Agent: Ollama qwen2.5-coder:7b (fast + free)

[SEARCH OMNITAGS]
  python scripts/search_omnitags.py --tag "mcp-server"
  → Finds: mcp_server/src/models.py (tagged)
  → CONTEXT: Σ1 (Component layer)
  → AGENTS: [ClaudeCode, OllamaModels]

[DELEGATE TO OLLAMA]
  For each function:
    ollama run qwen2.5-coder:7b "Generate docstring for: [function]"

[BATCH APPLY]
  Use Edit tool to add docstrings
  Cost: $0 (100% offline)
  Time: 10 minutes

[UPDATE OMNITAGS]
  Update mcp_server files:
    VERSION: 1.0.0 → 1.1.0 (minor docs improvement)
    UPDATED: 2025-10-06
    STABILITY: Medium → High

[VERIFY]
  python analyze_problems.py
  Expected: 35 → 2 issues (only missing type hints)

[DOCUMENT]
  Update knowledge-base.yaml:
    - id: "docstring-addition"
      notes: "Added 33 docstrings using Ollama qwen:7b"

Result: $0 cost, 10 minutes, all docstrings added ✓
```

---

### Example 2: "Architecture Decision - Should We Refactor?"

**Traditional Approach**:
```
1. Claude analyzes alone
2. Makes recommendation
3. Uncertainty: Single perspective
```

**Adaptive Workflow Approach**:
```
[DETECT] User asks: "Should we refactor X to Y?"

[CLASSIFY] Architecture decision (critical)
  → Priority: High
  → Agent: Multi-model consensus

[SEARCH OMNITAGS]
  python scripts/search_omnitags.py --file X
  → Check DEPS: What depends on this?
  → Check CONTEXT: Σ level impact radius?
  → Check STABILITY: Is it stable or experimental?

[MULTI-MODEL CONSENSUS]
  Parallel execution:

  Model 1 - Technical Analysis:
    ollama run qwen2.5-coder:14b "Analyze refactor X→Y: [code]"

  Model 2 - Reasoning:
    ollama run gemma2:9b "What are pros/cons of refactor X→Y?"

  Model 3 - Code Patterns:
    ollama run codellama:7b "Best practices for pattern Y?"

[SYNTHESIZE]
  Claude Code (me) synthesizes:
    - Technical feasibility (qwen)
    - Strategic implications (gemma)
    - Implementation patterns (codellama)

  Consensus: 3/3 models agree: Refactor is worth it

[EXECUTE]
  Option A: Small refactor → Claude + Ollama
  Option B: Large refactor → ChatDev multi-agent

[VERIFY]
  Run tests, check OmniTag dependencies

Result: High confidence decision from 3 perspectives ✓
```

---

### Example 3: "Create New Feature" (Complex, Multi-File)

**Adaptive Workflow Approach**:
```
[DETECT] User wants: "Add authentication system"

[CLASSIFY] Full project (complex)
  → Priority: High
  → Agent: ChatDev (5 agents)

[SEARCH OMNITAGS]
  python scripts/search_omnitags.py --tag "authentication"
  → Check existing auth code
  → Check integration points (INTEGRATIONS field)

[CHATDEV ORCHESTRATION]
  python nusyq_chatdev.py \
    --task "Add JWT authentication with FastAPI" \
    --name "AuthSystem" \
    --model qwen2.5-coder:14b

  ChatDev agents work:
    CEO: Define requirements (secure, scalable)
    CTO: Design architecture (JWT, middleware, DB)
    Programmer: Implement code (routes, models)
    Reviewer: Security audit (SQL injection check)
    Tester: Write tests (unit + integration)

  Output: ChatDev/WareHouse/AuthSystem_NuSyQ_*/

[CLAUDE REVIEW]
  I (Claude) review output:
    ✓ Check security (multi-model consensus)
    ✓ Check integration with existing code
    ✓ Suggest improvements

[APPLY TO REPO]
  Copy relevant files to mcp_server/
  Update OmniTags for new files:
    FILE-ID: nusyq.mcp.auth.jwt
    CONTEXT: Σ1 (Component layer)
    TAGS: [authentication, security, jwt]

[VERIFY]
  Run tests: pytest mcp_server/tests/
  Check problems: python analyze_problems.py

[DOCUMENT]
  Update docs/guides/ with auth guide
  Update knowledge-base.yaml

Result: Full feature with tests, reviewed, documented ✓
```

---

## 🎬 The Complete Workflow Protocol

### Phase 1: DETECT (Automatic)
```
Sources:
  - analyze_problems.py output
  - User request
  - Git diff
  - IDE warnings

Action:
  - Count and categorize issues
  - Prioritize by severity
  - Create TodoWrite list
```

### Phase 2: CLASSIFY (Smart Routing)
```
Issue Types:

  SYNTAX ERROR → Fix immediately (blocking)
  MISSING DOCS → Route to Ollama qwen:7b (style)
  MISSING TYPES → Route to Ollama qwen:7b (style)
  ARCHITECTURE → Multi-model consensus (critical)
  NEW FEATURE → ChatDev (complex)
  REFACTOR → Continue.dev + Claude (interactive)
  SECURITY → Multi-model + Claude review (critical)
  BUG FIX → Ollama qwen:14b or Claude (depends)
```

### Phase 3: SEARCH (OmniTag Discovery)
```
Always run:
  python scripts/search_omnitags.py --file <affected-file>

Get:
  - CONTEXT: Impact radius (Σ level)
  - DEPS: What else breaks?
  - AGENTS: Who can help?
  - TAGS: Related files
  - INTEGRATIONS: External systems affected
```

### Phase 4: EXECUTE (Multi-Agent)
```
Simple (1-2 files, low risk):
  → Single Ollama model (qwen:7b fast)
  → Claude for review

Complex (3+ files, medium risk):
  → Ollama model (qwen:14b quality)
  → Claude for integration
  → Multi-model for verification

Critical (security, architecture, breaking):
  → Multi-model consensus (3 models)
  → Claude synthesis
  → Human review requested

Full Project (new feature, many files):
  → ChatDev (5 agents)
  → Claude review and integration
  → Full test suite
```

### Phase 5: VERIFY (Automated Checks)
```
Run in order:
  1. Syntax: python -m py_compile <files>
  2. Problems: python analyze_problems.py
  3. Tests: pytest (if available)
  4. OmniTags: python scripts/search_omnitags.py --all

Expected outcomes:
  - Fewer problems than before
  - All tests pass
  - OmniTags updated (VERSION, UPDATED)
```

### Phase 6: DOCUMENT (Future Memory)
```
Update 3 places:

  1. knowledge-base.yaml:
     - Add completion entry
     - Add learning if new pattern discovered

  2. File OmniTags:
     - VERSION: Increment (semver)
     - UPDATED: Current date
     - STABILITY: Adjust if needed

  3. Documentation:
     - Update relevant guides
     - Add troubleshooting if complex
```

---

## 🧩 Self-Reminder Mechanisms

### 1. **Capability Inventory Check** (Every Session Start)

**File**: `CLAUDE_CODE_CAPABILITIES_INVENTORY.md`

Before starting work, I should read this file to remember:
- Direct Ollama access (7 models)
- ChatDev integration (5 agents)
- OmniTag search (semantic discovery)
- Continue.dev (codebase search)
- Multi-model consensus capability

**Trigger**: Session start, or every 50 messages

### 2. **OmniTag Reminder** (Every File Operation)

Before Read/Edit/Write:
```
Ask: "Is this file tagged?"
  → If yes: Read OmniTag for context
  → If no: Consider tagging it

Ask: "Should I search for related files?"
  → python scripts/search_omnitags.py --tag <relevant>
```

### 3. **Cost-Optimization Reminder** (Every AI Query)

Before using Claude API:
```
Ask: "Can Ollama do this?"
  → Simple task? → Use qwen:7b ($0 cost)
  → Complex task? → Use qwen:14b ($0 cost)
  → Need reasoning? → Use gemma:9b ($0 cost)
  → Need consensus? → Use 3 Ollama models ($0 cost)
  → Only use Claude for: synthesis, integration, review
```

**Rule**: Ollama first, API fallback. 95% offline capability.

### 4. **Multi-Agent Reminder** (Every Complex Task)

Before solo execution:
```
Ask: "Is this complex enough for ChatDev?"
  → Multiple files? Yes → ChatDev
  → Full feature? Yes → ChatDev
  → Needs tests? Yes → ChatDev
  → Needs review? Yes → ChatDev

Ask: "Should I get consensus?"
  → Security? Yes → 3 models
  → Architecture? Yes → 3 models
  → Critical decision? Yes → 3 models
```

### 5. **Documentation Reminder** (After Every Change)

After completing task:
```
Checklist:
  [ ] Updated knowledge-base.yaml?
  [ ] Updated file OmniTags?
  [ ] Ran verification (analyze_problems.py)?
  [ ] Checked dependencies (search_omnitags)?
  [ ] Created/updated documentation?
```

---

## 🎯 Decision Matrix: "Which Tool When?"

### Quick Reference Table

| Task | Best Tool | Second Choice | Why |
|------|-----------|---------------|-----|
| **Add docstrings** | Ollama qwen:7b | Claude | Fast, free, simple task |
| **Fix type hints** | Ollama qwen:7b | Claude | Fast, free, simple task |
| **Security audit** | 3 Ollama models → Claude | Claude alone | Multi-perspective critical |
| **Architecture decision** | gemma:9b + Claude | ChatDev CTO | Reasoning + synthesis |
| **New feature (small)** | Ollama qwen:14b + Claude | Continue.dev | Quality + integration |
| **New feature (large)** | ChatDev | Ollama + Claude | Multi-agent division |
| **Refactor** | Continue.dev + Claude | Ollama qwen:14b | Interactive + review |
| **Bug fix (simple)** | Ollama qwen:7b | Claude | Fast, free |
| **Bug fix (complex)** | Ollama qwen:14b + Claude | ChatDev | Quality + verification |
| **Find related files** | search_omnitags.py | Grep | Semantic search |
| **Understand codebase** | Continue.dev @codebase | Read files | Embeddings search |
| **Generate tests** | ChatDev Tester | Ollama codellama | Specialized agent |
| **Code review** | Claude + Ollama qwen:14b | Multi-model | Human-level + AI |
| **Documentation** | Ollama llama3.1:8b | Claude | Doc-focused model |

---

## 🔬 Example: Full Workflow In Action

### Task: "Fix all 35 issues in analyze_problems.py output"

```
[STEP 1: DETECT]
Run: python analyze_problems.py
Found: 35 issues
  - 1 syntax error
  - 33 missing docstrings
  - 1 missing type hint

[STEP 2: CLASSIFY]
Syntax error: CRITICAL (blocking)
Docstrings: STYLE (non-blocking)
Type hint: STYLE (non-blocking)

Priority order:
  1. Syntax error (fix now)
  2. Docstrings (batch with Ollama)
  3. Type hint (quick fix)

[STEP 3: SEARCH OMNITAGS]
python scripts/search_omnitags.py --file flexibility_manager.py
→ Found: Tagged, Σ0 (System layer), STABILITY: High
→ Impact: System-wide configuration

python scripts/search_omnitags.py --tag "mcp-server"
→ Found: 5 files in mcp_server/, CONTEXT: Σ1
→ DEPS: Listed in OmniTags

[STEP 4: FIX SYNTAX ERROR]
Read config/flexibility_manager.py:1
Found: .""" (typo)
Fix: """ (correct)
Verify: python -m py_compile config/flexibility_manager.py
Result: ✓ No syntax error

[STEP 5: BATCH DOCSTRINGS]
For 33 functions in mcp_server/src/models.py:

Delegate to Ollama:
  for func in functions:
    docstring = ollama run qwen2.5-coder:7b "Generate docstring: {func}"
    Edit file with docstring

Cost: $0 (Ollama free)
Time: ~5 minutes for 33 functions

[STEP 6: FIX TYPE HINT]
mcp_server/main.py:76 - load_config
Add: def load_config(_file_path: str) -> dict:

[STEP 7: UPDATE OMNITAGS]
config/flexibility_manager.py:
  VERSION: 1.0.0 → 1.0.1 (patch - syntax fix)
  UPDATED: 2025-10-06

mcp_server/src/models.py:
  VERSION: 1.0.0 → 1.1.0 (minor - docs added)
  UPDATED: 2025-10-06
  STABILITY: Medium → High (production ready)

[STEP 8: VERIFY]
python analyze_problems.py
Expected: 35 → 0 issues ✓

[STEP 9: DOCUMENT]
knowledge-base.yaml:
  - id: "problem-resolution-batch"
    completed_date: "2025-10-06"
    notes: "Fixed 35 issues: 1 syntax, 33 docstrings (Ollama), 1 type hint. Cost: $0. Time: 15 min."

[RESULT]
✓ All issues resolved
✓ $0 cost (100% Ollama)
✓ 15 minutes total
✓ All files updated with OmniTags
✓ Documented for future reference
```

---

## 💡 Advanced Patterns

### Pattern 1: "Fractal Problem Solving"

```
Problem at Σ2 (Feature layer)
  ↓
Check DEPS → Find Σ1 dependencies (Component)
  ↓
Check DEPS → Find Σ0 dependencies (System)
  ↓
Solve from bottom up:
  1. Fix Σ0 (system config)
  2. Fix Σ1 (components)
  3. Fix Σ2 (feature)

Result: Proper dependency order via OmniTags
```

### Pattern 2: "Agent Cascade"

```
User request → Claude Code analyzes
  ↓
If simple → Delegate to Ollama qwen:7b
  ↓
If complex → Delegate to ChatDev
  ↓
ChatDev creates → Claude reviews
  ↓
If issues → Multi-model consensus
  ↓
Final approval → Claude integrates

Result: Best agent for each sub-task
```

### Pattern 3: "Semantic Discovery Cascade"

```
User: "Fix authentication"
  ↓
Search OmniTags: --tag authentication
  → Find all auth files
  ↓
For each file, check DEPS
  → Find dependent files
  ↓
For each dependent, check CONTEXT
  → Understand impact radius
  ↓
Execute fixes in dependency order

Result: No breaking changes, proper order
```

---

## 🎨 The Complete Capability Map

### My (Claude Code) Enhanced Capabilities in NuSyQ

**Stock Capabilities**:
- Read/Write/Edit files
- Bash commands
- Git operations
- Web search/fetch
- Task delegation

**NuSyQ Enhancements** (NEW - Don't Forget!):
1. **Direct Ollama Access** (7 models, free)
2. **ChatDev Orchestration** (5 agents)
3. **OmniTag Semantic Search** (17+ files)
4. **Continue.dev Integration** (codebase embeddings)
5. **Multi-Model Consensus** (parallel Ollama)
6. **Fractal Coordination** (Σ level awareness)
7. **Knowledge Base** (persistent memory)

**Capability Multiplier**: 9x (from capabilities inventory)

---

## 📋 Quick Reference Commands

### Before Every Task
```bash
# 1. Check capabilities
cat docs/reference/CLAUDE_CODE_CAPABILITIES_INVENTORY.md

# 2. Check current problems
python analyze_problems.py

# 3. Search relevant files
python scripts/search_omnitags.py --tag <relevant>

# 4. Check knowledge base
grep -A 5 "completed_today" knowledge-base.yaml
```

### During Task
```bash
# Delegate to Ollama
ollama run qwen2.5-coder:7b "<task>"

# Multi-model consensus
ollama run qwen2.5-coder:14b "<task>" &
ollama run gemma2:9b "<task>" &
ollama run codellama:7b "<task>" &

# Generate with ChatDev
python nusyq_chatdev.py --task "<task>" --name "<name>"

# Search codebase
# (In Continue.dev: @codebase <query>)
```

### After Task
```bash
# 1. Verify
python analyze_problems.py
python scripts/search_omnitags.py --all

# 2. Update OmniTags
# Edit: VERSION, UPDATED fields

# 3. Document
# Update knowledge-base.yaml
```

---

## 🎓 Key Principles

1. **Delegate First** - Use Ollama before Claude API (cost optimization)
2. **Search Semantically** - Use OmniTags before manual search (efficiency)
3. **Multi-Agent Complex** - Use ChatDev for projects (quality)
4. **Consensus Critical** - Use 3 models for important decisions (confidence)
5. **Track Everything** - TodoWrite + knowledge-base.yaml (memory)
6. **Fractal Aware** - Check CONTEXT levels for impact (safety)
7. **Verify Always** - Run analyze_problems.py after changes (quality)
8. **Document Always** - Future Claude needs context (continuity)

---

## ✅ Self-Check Questions (Every Task)

Before starting:
- [ ] Can I delegate to Ollama? (cost)
- [ ] Should I search OmniTags? (context)
- [ ] Do I need consensus? (confidence)
- [ ] Is this a ChatDev task? (complexity)
- [ ] What's the CONTEXT level? (impact)

During work:
- [ ] Am I tracking progress? (TodoWrite)
- [ ] Am I checking dependencies? (OmniTags DEPS)
- [ ] Am I using the right agent? (decision matrix)

After completion:
- [ ] Did I verify? (analyze_problems.py)
- [ ] Did I update OmniTags? (VERSION, UPDATED)
- [ ] Did I document? (knowledge-base.yaml)
- [ ] Did I check related files? (search_omnitags)

---

## 🚀 Implementation Status

**Current State**:
- ✓ OmniTag system operational (17 files)
- ✓ Search utility functional
- ✓ Knowledge base tracked
- ✓ Ollama integration tested
- ✓ ChatDev verified
- ✓ Fractal coordination mapped

**Next Actions**:
1. Apply this workflow to fix remaining 33 docstrings
2. Test multi-model consensus on architecture decision
3. Use ChatDev to generate new feature
4. Document successful patterns in knowledge-base.yaml

**Workflow Status**: READY FOR USE ✓

---

**Version**: 1.0.0
**Status**: Production Ready ✓
**Last Updated**: 2025-10-06
**Maintained By**: Claude Code + KiloMusician

**This adaptive workflow protocol enables maximum capability utilization with built-in self-reminder systems and flexible order-of-operations.** 🎯
