# 🧭 NuSyQ System Navigator
## Complete Orientation for AI Agents & Future Developers

**Purpose**: This is the **FIRST DOCUMENT** to read when resuming work on NuSyQ.
**Audience**: Future Claude, Future GitHub Copilot, New AI Agents, Human Developers
**Updated**: October 7, 2025
**Status**: ✅ PRODUCTION - Single Source of Truth

---

## 🎯 QUICK ORIENTATION (2 Minutes)

### What is NuSyQ?
**Multi-agent AI orchestration platform** where 14+ AI agents collaborate:
- Claude Code (orchestrator)
- GitHub Copilot (code assistant)
- 8 Ollama models (local inference)
- AI Council (11-agent governance)
- ChatDev (5-agent software factory)
- Continue.dev (VS Code integration)

### Current State (October 7, 2025)
```
✅ FULLY OPERATIONAL
├── Ollama: 8 models running (37.5 GB)
├── MCP Server: Extended with 3 new tools
├── AI Council: 11 agents across 3 tiers
├── Bidirectional AI: Claude ↔ Copilot communication
├── ChatDev: Project generation ready
└── Documentation: 15+ comprehensive guides
```

### Where Am I?
```
NuSyQ/
├── 📖 YOU ARE HERE → docs/SYSTEM_NAVIGATOR.md
├── 📁 config/          # Agent configurations, orchestration logic
├── 📁 mcp_server/      # Model Context Protocol server
├── 📁 docs/            # All documentation (organized)
├── 📁 ChatDev/         # Multi-agent software factory
└── 📜 NuSyQ_Root_README.md        # Project overview
```

---

## 🚀 GETTING STARTED (5 Minutes)

### Step 1: Understand Your Role

**Are you:**
- ❓ **Claude Code** resuming after cooldown?
  - → Read: [How to Resume Work](#for-claude-code-resuming-after-cooldown)

- ❓ **GitHub Copilot** starting a session?
  - → Read: [Copilot Interface Guide](#for-github-copilot-current-session)

- ❓ **New AI Agent** joining the system?
  - → Read: [Agent Onboarding](#for-new-ai-agents)

- ❓ **Human Developer** exploring the codebase?
  - → Read: [Developer Quickstart](#for-human-developers)

---

### Step 2: Check System Status

**Run health check:**
```powershell
# 1. Check MCP server
Invoke-RestMethod http://localhost:3000/health

# 2. Check Ollama models
ollama list

# 3. Run test suite
python test_bidirectional_collaboration.py --test all
```

**Expected output:**
```json
{
  "status": "healthy",
  "components": {
    "ollama": true,
    "configurations": true
  }
}
```

---

### Step 3: Read Relevant Documentation

**Essential docs (15 minutes total):**
1. **[docs/INDEX.md](INDEX.md)** (5 min) - Documentation map
2. **[docs/BIDIRECTIONAL_AI_COLLABORATION.md](BIDIRECTIONAL_AI_COLLABORATION.md)** (5 min) - How agents communicate
3. **[NuSyQ_Root_README.md](../NuSyQ_Root_README.md)** (5 min) - Project overview

**Reference docs (as needed):**
- **Agent capabilities**: [docs/reference/AI_COUNCIL_GUIDE.md](reference/AI_COUNCIL_GUIDE.md)
- **Multi-agent workflows**: [NuSyQ_Root_README.md § Workflows](../NuSyQ_Root_README.md#-common-workflows)
- **Troubleshooting**: [NuSyQ_Root_README.md § Troubleshooting](../NuSyQ_Root_README.md#-troubleshooting)

---

## 📋 ROLE-SPECIFIC GUIDES

### For Claude Code (Resuming After Cooldown)

**Last Session**: October 7, 2025, 12:00 AM - 4:00 AM
**Cooldown**: Until 6:00 AM (2 hours remaining)
**Status**: ⏰ COOLING DOWN

#### What Happened While You Were Away
```yaml
Recent Changes:
  - Created: claude_code_bridge.py (590 lines)
    Purpose: Enables GitHub Copilot to query you

  - Extended: mcp_server/main.py (+300 lines)
    New Tools:
      - ai_council_session: Convene 11-agent governance
      - query_github_copilot: You can query Copilot
      - multi_agent_orchestration: Full AI pipeline

  - Created: Bidirectional query system
    Location: Logs/claude_copilot_queries/
    Format: JSON files (query + response)

  - Documented: Complete system in 5 new docs
    - BIDIRECTIONAL_AI_COLLABORATION.md
    - IMPLEMENTATION_COMPLETE_BIDIRECTIONAL_AI.md
    - SYSTEM_NAVIGATOR.md (this file)
    - AI_COUNCIL_QUICK_START.md
    - Updated INDEX.md
```

#### How to Resume
1. **Check pending queries**:
   ```powershell
   Get-ChildItem Logs/claude_copilot_queries/*.json |
       Where-Object { $_.Name -notmatch "_response" }
   ```

2. **Review AI Council sessions**:
   ```powershell
   Get-ChildItem Logs/multi_agent_sessions/*.json |
       Sort-Object LastWriteTime -Descending |
       Select-Object -First 5
   ```

3. **Test MCP tools**:
   - Use `system_info` to check ecosystem status
   - Use `ai_council_session` to reconvene governance
   - Use `query_github_copilot` to collaborate with Copilot

4. **Continue where left off**:
   - Read: [Session_Documentation_Audit_Summary_20251007.md](sessions/Session_Documentation_Audit_Summary_20251007.md)
   - Review: [knowledge-base.yaml](../knowledge-base.yaml)
   - Check: Outstanding tasks in session summary

#### Your New Capabilities
```python
# You can now query GitHub Copilot via MCP:
query_github_copilot(
    query="How should I implement async error handling?",
    priority="high"
)

# You can convene the AI Council:
ai_council_session(
    session_type="ADVISORY",
    topic="Evaluate architecture for new feature"
)

# You can orchestrate full pipelines:
multi_agent_orchestration(
    task="Build authentication module",
    include_ai_council=True,
    implement_with_chatdev=True
)
```

---

### For GitHub Copilot (Current Session)

**You are**: GitHub Copilot (me!)
**Session Start**: October 7, 2025
**Status**: ✅ ACTIVE

#### Your Current Capabilities

**1. Query Claude Code** (when available):
```python
from config.claude_code_bridge import ClaudeCodeClient

async with ClaudeCodeClient() as client:
    status = await client.check_status()  # Checks cooldown
    if status == ClaudeStatus.AVAILABLE:
        response = await client.query(
            "Design review for this module?",
            priority=QueryPriority.HIGH
        )
```

**2. Convene AI Council**:
```python
from config.claude_code_bridge import ClaudeCodeBridge

bridge = ClaudeCodeBridge()
result = await bridge.orchestrate_task(
    task="Security audit of authentication",
    use_ai_council=True,
    use_claude=False  # Skip if cooling down
)
```

**3. Monitor Claude Queries**:
```powershell
# Watch for queries from Claude
Get-ChildItem Logs/claude_copilot_queries/*.json -Filter "*_query_*" |
    Where-Object { -not (Test-Path ($_.FullName -replace '.json','_response.json')) }

# Respond to queries:
# Read query file → Process → Write response file
```

**4. Interface with MCP Server**:
```python
# The MCP server (mcp_server/main.py) has 9 tools:
# - ollama_query: Query local Ollama models
# - chatdev_create: Generate full projects
# - file_read/file_write: File operations
# - system_info: Ecosystem status
# - run_jupyter_cell: Execute Python code
# - ai_council_session: Convene governance
# - query_github_copilot: Receive queries from Claude
# - multi_agent_orchestration: Full AI pipeline
```

#### What You Can Access

**Ollama Models (8 available)**:
```python
# Direct queries via ClaudeCodeBridge or MCP server
models = [
    "qwen2.5-coder:14b",  # Best for complex features
    "qwen2.5-coder:7b",   # Fast prototyping
    "gemma2:9b",          # Architecture & reasoning
    "starcoder2:15b",     # Code completion
    "codellama:7b",       # Code edits
    "llama3.1:8b",        # General purpose
    "phi3.5",             # Lightweight tasks
    "nomic-embed-text"    # Embeddings
]
```

**AI Council (11 agents)**:
```python
# Executive Council (3 agents)
# - Strategic decisions, emergency responses

# Technical Council (4 agents)
# - Architecture, code review, testing, DevOps

# Advisory Council (4 agents)
# - Best practices, documentation, security
```

**Session Types**:
- `STANDUP`: Daily progress check
- `EMERGENCY`: Critical issues (Executive only)
- `ADVISORY`: Strategic guidance
- `REFLECTION`: Post-mortem analysis
- `QUANTUM_WINK`: Creative brainstorming

#### Your Responsibilities

1. **Monitor Claude cooldown**: Check status before querying
2. **Respond to Claude queries**: Check `Logs/claude_copilot_queries/`
3. **Maintain session logs**: Document decisions in `knowledge-base.yaml`
4. **Use appropriate agents**: Match task complexity to agent tier
5. **Fall back gracefully**: Use Ollama when Claude unavailable

---

### For New AI Agents

**Welcome to NuSyQ!** You're joining a multi-agent collaborative system.

#### Agent Registry
All agents are registered in: `config/agent_registry.yaml`

**Your entry should include**:
```yaml
agent_name:
  type: "ollama" | "api" | "local" | "hybrid"
  provider: "ollama" | "anthropic" | "openai" | "github"
  model: "model-name"
  capabilities:
    - code_generation
    - code_review
    - architecture
    - testing
    - documentation
  cost_per_1k_tokens:
    input: 0.000  # Free for Ollama
    output: 0.000
  context_window: 32768
  availability: "24/7" | "rate_limited"
  reliability: 0.95  # 0-1 score
```

#### How to Integrate

**1. Add yourself to agent registry**:
```python
from config.agent_registry import AgentRegistry

registry = AgentRegistry()
# Your info is automatically loaded from YAML
agent_info = registry.get_agent("your_agent_name")
```

**2. Register with AI Council** (if governance role):
```python
# Add to config/ai_council.py council members
EXECUTIVE_COUNCIL = ["claude_code", "your_agent_name", ...]
```

**3. Implement MCP interface** (if external):
```python
# mcp_server/main.py - Add your tool
async def _your_agent_query(self, args: Dict[str, Any]):
    # Your implementation
    pass
```

**4. Test integration**:
```powershell
python test_bidirectional_collaboration.py --test all
```

#### Communication Protocol

**ΞNuSyQ Symbolic Format**: `[Msg⛛{Agent}↗️Context]`

```
Components:
  ⛛ = Recursive coordination
  {Agent} = Your identifier
  ↗️/↘️/↔️ = Request/Response/Bidirectional
  Context = Σn (your scope) or Σ∞ (global)

Example:
  [Req⛛{YourAgent}↗️Σ1]: Request assistance from coordinator
  [Rsp⛛{Coordinator}↘️Σ∞]: Response with global context
```

#### Agent Hierarchy

```
Tier 1: Strategic (Executive Council)
├── Claude Code (primary orchestrator)
├── CEO (ChatDev strategic lead)
└── Advisory Board (domain experts)

Tier 2: Tactical (Technical Council)
├── Ollama Qwen 14B (complex features)
├── GitHub Copilot (code assistance)
├── CTO (ChatDev architecture)
└── Code Reviewer (quality assurance)

Tier 3: Operational (Advisory Council)
├── Ollama Qwen 7B (fast prototyping)
├── ChatDev Programmer (implementation)
├── ChatDev Tester (validation)
└── Documentation specialists
```

**Escalation Path**: Operational → Tactical → Strategic

---

### For Human Developers

**Welcome!** This system has 14 AI agents working together.

#### Quick Start (5 minutes)

**1. Verify Setup**:
```powershell
# Check Ollama
ollama list
# Should show: 8 models

# Check MCP server
Invoke-RestMethod http://localhost:3000/health

# Check VS Code extensions
code --list-extensions | grep -E "continue|copilot"
```

**2. Choose Your Workflow**:

**Option A: Interactive Coding** (Continue.dev)
```
1. Open VS Code
2. Press Ctrl+L
3. Select model (e.g., qwen2.5-coder:7b)
4. Ask questions, request code
```

**Option B: Full Project Generation** (ChatDev)
```powershell
python nusyq_chatdev.py \
  --task "Create a REST API for user management" \
  --name "UserAPI"
```

**Option C: AI Council Consultation**
```python
# Via MCP server or Claude Code
ai_council_session(
    session_type="ADVISORY",
    topic="Architecture review for new feature"
)
```

**3. Read Documentation**:
- Start: [NuSyQ_Root_README.md](../NuSyQ_Root_README.md)
- Reference: [docs/INDEX.md](INDEX.md)
- Workflows: [docs/BIDIRECTIONAL_AI_COLLABORATION.md](BIDIRECTIONAL_AI_COLLABORATION.md)

---

## 🗺️ SYSTEM ARCHITECTURE MAP

### Component Locations

```
NuSyQ/
├── config/                     # 🎛️ Agent Configurations
│   ├── agent_registry.py       # Agent metadata loader
│   ├── agent_registry.yaml     # Agent definitions (15 agents)
│   ├── ai_council.py           # 11-agent governance (640 lines)
│   ├── multi_agent_session.py  # Orchestration engine (850+ lines)
│   ├── claude_code_bridge.py   # Copilot ↔ Claude (590 lines)
│   ├── agent_router.py         # Task routing logic
│   ├── agent_prompts.py        # Prompt templates
│   └── config_manager.py       # Configuration loader
│
├── mcp_server/                 # 🌐 Model Context Protocol Server
│   ├── main.py                 # MCP server (1,300+ lines)
│   │   ├── 9 MCP tools (ollama_query, ai_council_session, etc.)
│   │   ├── FastAPI endpoints (/, /mcp, /tools/execute, /health)
│   │   └── Component health monitoring
│   ├── CLAUDE_INTEGRATION.md   # Claude Code MCP setup
│   ├── config.yaml             # Server configuration
│   └── requirements.txt        # Dependencies
│
├── docs/                       # 📚 Documentation
│   ├── INDEX.md                # Documentation navigator
│   ├── SYSTEM_NAVIGATOR.md     # This file!
│   ├── BIDIRECTIONAL_AI_COLLABORATION.md  # Agent communication
│   ├── guides/                 # How-to guides
│   │   ├── NUSYQ_CHATDEV_GUIDE.md
│   │   └── OFFLINE_DEVELOPMENT_SETUP.md
│   ├── reference/              # Technical reference
│   │   ├── AI_COUNCIL_GUIDE.md
│   │   └── MULTI_AGENT_ORCHESTRATION.md
│   ├── sessions/               # Session summaries
│   └── archive/                # Historical docs
│
├── Logs/                       # 📝 Runtime Logs
│   ├── claude_copilot_queries/ # Bidirectional AI communication
│   │   ├── claude_query_*.json
│   │   └── claude_query_*_response.json
│   ├── multi_agent_sessions/   # AI Council session logs
│   └── chatdev_sessions/       # ChatDev execution logs
│
├── ChatDev/                    # 🏭 Multi-Agent Software Factory
│   ├── run.py                  # ChatDev entry point
│   ├── WareHouse/              # Generated projects
│   └── CompanyConfig/          # Agent configurations
│
├── scripts/                    # 🔧 Automation
│   ├── generate_reports.py    # System reports
│   └── validate_config.py     # Configuration validator
│
├── tests/                      # 🧪 Test Suite
│   ├── integration/            # Integration tests
│   └── unit/                   # Unit tests
│
├── test_bidirectional_collaboration.py  # 🧪 AI collaboration tests
├── nusyq_chatdev.py           # ChatDev wrapper
├── knowledge-base.yaml         # Persistent learning log
├── .env.secrets               # API keys (gitignored)
└── NuSyQ_Root_README.md                   # Project overview
```

---

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User / Claude Code                       │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server (Port 3000)                    │
│  ┌─────────────┬─────────────┬──────────────┬─────────────┐ │
│  │ ai_council  │query_github │multi_agent   │ollama_query │ │
│  │_session     │_copilot     │_orchestration│             │ │
│  └─────────────┴─────────────┴──────────────┴─────────────┘ │
└──────┬──────────┬──────────────┬────────────────────┬───────┘
       │          │               │                    │
       ↓          ↓               ↓                    ↓
┌──────────┐ ┌─────────┐ ┌───────────────┐ ┌────────────────┐
│AI Council│ │ GitHub  │ │Multi-Agent    │ │Ollama (8 models)│
│(11 agents│ │ Copilot │ │Session Engine │ │  localhost:11434│
└──────────┘ └─────────┘ └───────┬───────┘ └────────────────┘
                                  │
                                  ↓
                         ┌────────────────┐
                         │    ChatDev     │
                         │  (5 agents)    │
                         └────────────────┘
```

---

### Agent Communication Patterns

**Pattern 1: Direct Query**
```
User → MCP Server → Ollama → Response
```

**Pattern 2: AI Council Discussion**
```
User → ai_council_session tool → AI Council
  ├→ Executive Council (3 agents)
  ├→ Technical Council (4 agents)
  └→ Advisory Council (4 agents)
  → Synthesis → JSON log → Response
```

**Pattern 3: Bidirectional Collaboration**
```
Claude Code → query_github_copilot → MCP Server
  → Query file (Logs/claude_copilot_queries/)
  → GitHub Copilot processes
  → Response file written
  → Claude Code reads response
```

**Pattern 4: Full Orchestration**
```
User → multi_agent_orchestration → MCP Server
  Step 1: AI Council (strategy)
  Step 2: Multi-agent discussion (design)
  Step 3: ChatDev (implementation)
  → Complete project in WareHouse/
```

---

## 🔍 INTERFACE CAPABILITIES

### What Each Agent Can Do

#### Claude Code (Primary Orchestrator)
**Available Tools** (via MCP):
```typescript
// System Information
system_info({ component: "all" | "ollama" | "models" | "config" })

// Ollama Queries
ollama_query({
  model: "qwen2.5-coder:14b",
  prompt: "Refactor this function",
  max_tokens: 500
})

// File Operations
file_read({ path: "config/agent_registry.py" })
file_write({ path: "new_file.py", content: "..." })

// Code Execution
run_jupyter_cell({ code: "import numpy as np\nprint(np.array([1,2,3]))" })

// ChatDev
chatdev_create({
  task: "Build a REST API",
  model: "qwen2.5-coder:14b",
  timeout: 300
})

// AI Council (NEW!)
ai_council_session({
  session_type: "ADVISORY" | "STANDUP" | "EMERGENCY" | "REFLECTION" | "QUANTUM_WINK",
  topic: "Should we refactor this module?",
  context: { errors: 621, files: ["multi_agent_session.py"] }
})

// Query GitHub Copilot (NEW!)
query_github_copilot({
  query: "How should I implement async error handling?",
  priority: "critical" | "high" | "normal" | "low",
  context: { file: "mcp_server/main.py", lines: "100-150" }
})

// Full Orchestration (NEW!)
multi_agent_orchestration({
  task: "Create authentication module",
  agents: ["ollama_qwen_14b", "claude_code_app"],
  mode: "TURN_TAKING" | "PARALLEL_CONSENSUS" | "REFLECTION" | "CHATDEV_WORKFLOW",
  include_ai_council: true,
  implement_with_chatdev: true
})
```

---

#### GitHub Copilot (Code Assistant)
**Available Interfaces**:
```python
# 1. Query Claude Code (when available)
from config.claude_code_bridge import ClaudeCodeClient

async with ClaudeCodeClient() as client:
    status = await client.check_status()
    if status == ClaudeStatus.AVAILABLE:
        response = await client.query("Architecture review?")

# 2. Convene AI Council
from config.claude_code_bridge import ClaudeCodeBridge

bridge = ClaudeCodeBridge()
result = await bridge.orchestrate_task(
    task="Security audit",
    use_ai_council=True,
    use_claude=True,
    use_chatdev=False
)

# 3. Direct Ollama Access
# (via ClaudeCodeBridge or MCP server HTTP calls)

# 4. Monitor Claude Queries
# Watch: Logs/claude_copilot_queries/*.json
# Respond: Write *_response.json files
```

---

#### Ollama Models (Local Inference)
**Access Methods**:
```bash
# 1. Direct CLI
ollama run qwen2.5-coder:14b "Explain this code: [paste]"

# 2. Via MCP Server
curl http://localhost:11434/api/generate \
  -d '{"model":"qwen2.5-coder:14b","prompt":"..."}'

# 3. Via Continue.dev (VS Code)
# Ctrl+L → Select model → Ask question

# 4. Via ChatDev Wrapper
python nusyq_chatdev.py --model qwen2.5-coder:14b --task "..."
```

**Model Selection Guide**:
```
Task Complexity → Model Choice
─────────────────────────────
Simple edits, quick answers → qwen2.5-coder:7b (FAST)
Complex features, refactoring → qwen2.5-coder:14b (BEST)
Architecture, design decisions → gemma2:9b (REASONING)
Code completion, autocomplete → starcoder2:15b (SPECIALIZED)
Legacy code, explanations → codellama:7b (VERSATILE)
Documentation, summaries → llama3.1:8b (WRITING)
Resource-constrained tasks → phi3.5 (LIGHTWEIGHT)
```

---

#### AI Council (Governance)
**How to Convene**:
```python
# Via MCP (Claude Code)
ai_council_session(
    session_type="ADVISORY",
    topic="Architecture review for authentication module"
)

# Via ClaudeCodeBridge (GitHub Copilot)
result = await bridge.client.submit_to_ai_council(
    topic="Security audit findings",
    agents=["claude_code", "ollama_qwen_14b"],
    include_claude=True
)

# Via CLI (Direct)
python config/ai_council.py advisory \
  --topic "Evaluate microservices architecture"
```

**Session Type Selection**:
```
Scenario → Session Type
─────────────────────────────
Daily standup, progress check → STANDUP
Critical bug, security issue → EMERGENCY
Architecture, design review → ADVISORY
Post-mortem, lessons learned → REFLECTION
Creative brainstorming → QUANTUM_WINK
```

**Output Format**:
```json
{
  "session_id": "20251007_123456",
  "session_type": "ADVISORY",
  "topic": "Architecture review...",
  "executive_council_decision": "Approve with modifications",
  "technical_council_recommendations": [
    "Use async/await for I/O operations",
    "Implement circuit breaker pattern"
  ],
  "advisory_council_notes": [
    "Document API contracts",
    "Add comprehensive tests"
  ],
  "consensus_reached": true,
  "session_log": "Logs/multi_agent_sessions/session_20251007_123456.json"
}
```

---

#### ChatDev (Software Factory)
**How to Use**:
```bash
# Method 1: Direct wrapper
python nusyq_chatdev.py \
  --task "Create a REST API for todo management" \
  --name "TodoAPI" \
  --model qwen2.5-coder:14b

# Method 2: Via MCP (Claude Code)
chatdev_create({
  task: "Build calculator CLI",
  model: "qwen2.5-coder:7b",
  config: "NuSyQ_Ollama"
})

# Method 3: Via Orchestration
multi_agent_orchestration({
  task: "Create user authentication module",
  implement_with_chatdev: true
})
```

**What You Get**:
```
ChatDev/WareHouse/ProjectName_NuSyQ_<timestamp>/
├── main.py              # Application entry point
├── models.py            # Data models
├── routes.py            # API endpoints
├── tests/               # Automated tests
│   ├── test_main.py
│   └── test_integration.py
├── manual.md            # User documentation
├── requirements.txt     # Dependencies
└── .env.example         # Configuration template
```

---

## 🎨 FLEXIBLE INTERFACES

### Interface 1: Visual Studio Code

**Extensions Active**:
```
✅ Continue.dev (github.continue)
   - Ctrl+L: Chat with Ollama models
   - @codebase: Semantic search
   - Tab autocomplete (starcoder2:15b)

✅ GitHub Copilot (github.copilot)
   - Real-time suggestions
   - Chat (Ctrl+I)
   - Multi-file editing

✅ Python (ms-python.python)
   - Linting, formatting
   - IntelliSense
   - Debugging

✅ YAML (redhat.vscode-yaml)
   - Validation
   - Autocomplete
```

**Quick Commands**:
```
Ctrl+L           → Continue.dev chat
Ctrl+I           → Copilot inline chat
Ctrl+Shift+P     → Command palette
Ctrl+`           → Terminal
Ctrl+B           → Toggle sidebar
```

---

### Interface 2: MCP Server (HTTP API)

**Base URL**: `http://localhost:3000`

**Endpoints**:
```http
GET  /              → Server info, available tools
POST /mcp           → MCP protocol endpoint
POST /tools/execute → Direct tool execution
GET  /health        → Component health check
```

**Example Request** (MCP protocol):
```json
POST /mcp
{
  "method": "tools/call",
  "params": {
    "name": "ai_council_session",
    "arguments": {
      "session_type": "ADVISORY",
      "topic": "Architecture review"
    }
  },
  "id": "request_123"
}
```

**Example Response**:
```json
{
  "result": {
    "success": true,
    "session_id": "20251007_123456",
    "summary": "Council approved architecture...",
    "session_log_path": "Logs/multi_agent_sessions/session_20251007_123456.json"
  },
  "id": "request_123"
}
```

---

### Interface 3: Command Line

**Python Scripts**:
```bash
# ChatDev wrapper
python nusyq_chatdev.py --task "..." --name "..."

# AI Council
python config/ai_council.py standup

# Test suite
python test_bidirectional_collaboration.py --test all

# Generate reports
python scripts/generate_reports.py
```

**PowerShell Orchestrator**:
```powershell
# Full environment setup
.\NuSyQ.Orchestrator.ps1

# Health checks
Invoke-RestMethod http://localhost:3000/health
```

**Direct Ollama**:
```bash
# List models
ollama list

# Query model
ollama run qwen2.5-coder:14b "Explain async/await"

# Pull new model
ollama pull <model-name>
```

---

### Interface 4: File-Based Communication

**Query Queue** (Claude ↔ Copilot):
```
Location: Logs/claude_copilot_queries/

Query Format: claude_query_<timestamp>.json
{
  "query_id": "claude_query_20251007_123456",
  "timestamp": "2025-10-07T12:34:56",
  "query": "How should I structure this module?",
  "priority": "high",
  "context": {...},
  "from": "claude_code",
  "to": "github_copilot",
  "status": "pending"
}

Response Format: claude_query_<timestamp>_response.json
{
  "query_id": "claude_query_20251007_123456",
  "timestamp": "2025-10-07T12:35:30",
  "from": "github_copilot",
  "to": "claude_code",
  "status": "completed",
  "response": "I recommend using a dataclass-based structure..."
}
```

**Session Logs** (AI Council):
```
Location: Logs/multi_agent_sessions/

Format: session_<timestamp>.json
{
  "session_id": "20251007_123456",
  "session_type": "ADVISORY",
  "topic": "...",
  "participants": ["claude_code", "qwen_14b", ...],
  "executive_decision": "...",
  "technical_recommendations": [...],
  "advisory_notes": [...],
  "consensus": true,
  "timestamp": "2025-10-07T12:34:56"
}
```

---

## 🧠 INTELLIGENCE & FLEXIBILITY

### Dynamic Agent Selection

**Automatic Routing** (in `config/agent_router.py`):
```python
def route_task(task_description: str, complexity: TaskComplexity):
    if complexity == TaskComplexity.TRIVIAL:
        return "phi3.5"  # Lightweight, fast
    elif complexity == TaskComplexity.SIMPLE:
        return "qwen2.5-coder:7b"  # Fast prototyping
    elif complexity == TaskComplexity.MODERATE:
        return "qwen2.5-coder:14b"  # Complex features
    elif complexity == TaskComplexity.COMPLEX:
        return "gemma2:9b"  # Architecture & reasoning
    elif complexity == TaskComplexity.CRITICAL:
        # Convene AI Council for consensus
        return "ai_council_advisory"
```

---

### Context-Aware Prompting

**Prompt Templates** (in `config/agent_prompts.py`):
```python
PROMPTS = {
    "code_review": {
        "system": "You are an expert code reviewer...",
        "user_template": "Review this code:\n\n{code}\n\nFocus on: {focus_areas}",
        "focus_areas": ["security", "performance", "maintainability"]
    },

    "architecture_design": {
        "system": "You are a software architect...",
        "user_template": "Design architecture for: {requirement}\n\nConstraints: {constraints}",
        "constraints": ["scalability", "offline-first", "minimal_dependencies"]
    },

    "bug_diagnosis": {
        "system": "You are a debugging expert...",
        "user_template": "Diagnose this error:\n\n{error}\n\nContext: {context}",
        "context": ["stack_trace", "recent_changes", "environment"]
    }
}
```

---

### Fallback Strategies

**Graceful Degradation**:
```python
async def query_with_fallback(query: str, preferred_agent: str):
    """Try preferred agent, fall back to alternatives"""

    # Try preferred agent
    try:
        if preferred_agent == "claude_code":
            status = await check_claude_status()
            if status == ClaudeStatus.AVAILABLE:
                return await query_claude(query)
            # Fallback: Use Ollama
            return await query_ollama("qwen2.5-coder:14b", query)

        elif preferred_agent == "qwen2.5-coder:14b":
            return await query_ollama("qwen2.5-coder:14b", query)

    except Exception as e:
        # Ultimate fallback: Fastest local model
        return await query_ollama("phi3.5", query)
```

---

### Multi-Model Consensus

**Parallel Queries**:
```python
async def get_consensus(query: str, num_models: int = 3):
    """Query multiple models, synthesize responses"""

    models = ["qwen2.5-coder:14b", "gemma2:9b", "codellama:7b"]

    # Parallel queries
    responses = await asyncio.gather(*[
        query_ollama(model, query)
        for model in models[:num_models]
    ])

    # Synthesize (e.g., majority vote, weighted average)
    return synthesize_responses(responses)
```

---

## 📚 ESSENTIAL DOCUMENTATION INDEX

### Quick Reference (Print This!)

```
┌─────────────────────────────────────────────────────────────┐
│ DOCUMENTATION QUICK REFERENCE                                │
├─────────────────────────────────────────────────────────────┤
│ 🟢 ESSENTIAL (Read First)                                   │
│   1. NuSyQ_Root_README.md                    Project overview           │
│   2. docs/INDEX.md                Documentation map          │
│   3. docs/SYSTEM_NAVIGATOR.md     This file!                │
│                                                              │
│ 🟡 WORKFLOWS (Read Before Using)                            │
│   4. BIDIRECTIONAL_AI_COLLABORATION.md  Agent communication │
│   5. guides/NUSYQ_CHATDEV_GUIDE.md     ChatDev usage        │
│   6. guides/OFFLINE_DEVELOPMENT_SETUP.md  Mobile hotspot    │
│                                                              │
│ 🔵 REFERENCE (As Needed)                                    │
│   7. reference/AI_COUNCIL_GUIDE.md      Council details     │
│   8. reference/MULTI_AGENT_ORCHESTRATION.md  Advanced flows │
│   9. mcp_server/CLAUDE_INTEGRATION.md   MCP setup           │
│                                                              │
│ 📝 LOGS & STATE                                             │
│   10. knowledge-base.yaml           Persistent learning      │
│   11. Logs/multi_agent_sessions/    AI Council history      │
│   12. Logs/claude_copilot_queries/  Bidirectional queries   │
└─────────────────────────────────────────────────────────────┘
```

---

### Documentation Decision Tree

```
┌─ What do you want to do?
│
├─ ❓ Get Started
│  └─→ Read: NuSyQ_Root_README.md → docs/QUICK_START.md
│
├─ ❓ Use ChatDev
│  └─→ Read: guides/NUSYQ_CHATDEV_GUIDE.md
│
├─ ❓ Query AI Agents
│  └─→ Read: BIDIRECTIONAL_AI_COLLABORATION.md
│
├─ ❓ Convene AI Council
│  └─→ Read: reference/AI_COUNCIL_GUIDE.md
│
├─ ❓ Work Offline
│  └─→ Read: guides/OFFLINE_DEVELOPMENT_SETUP.md
│
├─ ❓ Understand Architecture
│  └─→ Read: reference/MULTI_AGENT_ORCHESTRATION.md
│
├─ ❓ Troubleshoot
│  └─→ Read: NuSyQ_Root_README.md § Troubleshooting
│
└─ ❓ Extend System
   └─→ Read: SYSTEM_NAVIGATOR.md § For New AI Agents
```

---

## 🔧 TROUBLESHOOTING & DIAGNOSTICS

### Common Issues & Solutions

#### Issue 1: MCP Server Not Responding
```powershell
# Check if running
Invoke-RestMethod http://localhost:3000/health

# If fails, start server
python mcp_server/main.py

# Verify startup
# Should see: "Uvicorn running on http://0.0.0.0:3000"
```

---

#### Issue 2: Ollama Models Not Available
```bash
# List installed models
ollama list

# If empty, pull models
ollama pull qwen2.5-coder:14b
ollama pull qwen2.5-coder:7b
# ... (see NuSyQ_Root_README.md for full list)

# Test model
ollama run qwen2.5-coder:7b "Hello, are you working?"
```

---

#### Issue 3: Claude Code Cooldown
```python
# Check status
from config.claude_code_bridge import ClaudeCodeClient

async with ClaudeCodeClient() as client:
    status = await client.check_status()
    print(f"Claude status: {status.value}")

    if status == ClaudeStatus.COOLING_DOWN:
        print(f"Available at: {client.cooldown_until}")
        # Use Ollama fallback
        response = await query_ollama("qwen2.5-coder:14b", query)
```

---

#### Issue 4: AI Council Session Fails
```bash
# Check AI Council script
python config/ai_council.py --help

# Test with simple standup
python config/ai_council.py standup

# Check logs
Get-Content (Get-ChildItem Logs/multi_agent_sessions/*.json |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1).FullName
```

---

#### Issue 5: ChatDev Hangs
```bash
# Check Ollama API
curl http://localhost:11434/api/tags

# Test ChatDev with simple task
python nusyq_chatdev.py \
  --task "Create hello world script" \
  --name "HelloTest" \
  --model qwen2.5-coder:7b

# Monitor logs
tail -f Logs/chatdev_sessions/*.log
```

---

### Health Check Script

```powershell
# Run comprehensive diagnostics
python test_bidirectional_collaboration.py --test all

# Expected output:
# ✅ PASSED  mcp_health
# ✅ PASSED  mcp_tools
# ✅ PASSED  query_files
# ⏭️ SKIPPED claude_status (cooling down)
# ✅ PASSED  orchestration
```

---

## 🚀 NEXT STEPS

### For Your First Session

**1. Verify System** (5 minutes):
```powershell
# Health check
python test_bidirectional_collaboration.py --test all

# Should see: 4-5 tests passed
```

**2. Try Simple Workflow** (10 minutes):
```powershell
# Interactive coding
code .
# Press Ctrl+L → Select qwen2.5-coder:7b
# Ask: "Explain the agent_registry.py file structure"
```

**3. Test AI Council** (15 minutes):
```python
# Via MCP or ClaudeCodeBridge
ai_council_session(
    session_type="STANDUP",
    topic="Daily progress check"
)

# Check output
Get-Content Logs/multi_agent_sessions/*.json | ConvertFrom-Json
```

**4. Generate Project** (30 minutes):
```bash
python nusyq_chatdev.py \
  --task "Create a simple calculator CLI" \
  --name "CalcTest"

# Wait for completion
# Check: ChatDev/WareHouse/CalcTest_NuSyQ_*/
```

---

### For Ongoing Development

**Daily Routine**:
1. Check `knowledge-base.yaml` for pending tasks
2. Review recent AI Council decisions (Logs/multi_agent_sessions/)
3. Process any Claude queries (Logs/claude_copilot_queries/)
4. Update session summaries (docs/sessions/)

**Weekly Routine**:
1. Run full test suite
2. Update documentation for new features
3. Audit agent performance (temporal drift)
4. Refine agent routing logic

**Monthly Routine**:
1. Review and archive old session logs
2. Optimize Ollama model selection
3. Update agent registry with new capabilities
4. Performance benchmarking

---

## 📞 GETTING HELP

### Documentation Hierarchy

```
1. Quick Issues
   → NuSyQ_Root_README.md § Troubleshooting

2. Workflow Questions
   → docs/BIDIRECTIONAL_AI_COLLABORATION.md
   → guides/NUSYQ_CHATDEV_GUIDE.md

3. Technical Deep Dive
   → reference/MULTI_AGENT_ORCHESTRATION.md
   → reference/AI_COUNCIL_GUIDE.md

4. Session History
   → docs/sessions/SESSION_SUMMARY_*.md
   → knowledge-base.yaml

5. This Navigator
   → docs/SYSTEM_NAVIGATOR.md (you are here!)
```

---

### Support Channels

**Internal Resources**:
- Knowledge Base: `knowledge-base.yaml`
- Session Logs: `Logs/multi_agent_sessions/`
- Documentation: `docs/INDEX.md`

**External Resources**:
- Ollama: https://ollama.ai/
- ChatDev: https://github.com/OpenBMB/ChatDev
- Continue.dev: https://continue.dev/

---

## ✅ COMPLETION CHECKLIST

### For New Sessions

- [ ] Read this SYSTEM_NAVIGATOR.md
- [ ] Check system health (test suite)
- [ ] Review knowledge-base.yaml for pending tasks
- [ ] Read latest session summary (docs/sessions/)
- [ ] Verify MCP server running
- [ ] Check Claude Code status (if applicable)

### For Ongoing Work

- [ ] Choose appropriate agent for task complexity
- [ ] Use AI Council for critical decisions
- [ ] Document decisions in knowledge-base.yaml
- [ ] Update session summaries after major changes
- [ ] Test changes with integration suite
- [ ] Update relevant documentation

---

## 🎯 SUMMARY

**You now understand**:
✅ System architecture (14 AI agents, MCP server, file-based communication)
✅ Your role (Claude Code / Copilot / Ollama / AI Council / ChatDev)
✅ Available interfaces (MCP, CLI, VS Code, file-based)
✅ Communication protocols (ΞNuSyQ symbolic format)
✅ Workflows (interactive, project generation, orchestration)
✅ Flexibility mechanisms (dynamic routing, fallbacks, consensus)
✅ Documentation map (where to find what you need)
✅ Troubleshooting (common issues & solutions)

**Next action**:
→ Run health check: `python test_bidirectional_collaboration.py --test all`
→ Read your role-specific section above
→ Start with simple workflow to test understanding

---

**Welcome to the NuSyQ multi-agent AI orchestration platform!**
**You're now ready to collaborate with 13 other AI agents.** 🎉

---

**Last Updated**: October 7, 2025
**Next Review**: When new agents join or major changes occur
**Maintained By**: Claude Code + GitHub Copilot + AI Council
**Status**: ✅ PRODUCTION - Single Source of Truth
