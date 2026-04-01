# 🧭 NuSyQ Tripartite Ecosystem - Agent Learning Guide

**Purpose:** Unified onboarding & operational reference for AI agents (GitHub Copilot, Claude, Ollama, LM Studio, ChatDev) working across the NuSyQ tripartite ecosystem.

**Last Updated:** 2026-02-04  
**Canonical Copy:** `NuSyQ-Hub/docs/AGENT_TUTORIAL.md`  
**Quick Reference:** `.vscode/prime_anchor/docs/ROSETTA_STONE.md`

---

## 📚 Table of Contents

0. [Learning Platform Index](#0-learning-platform-index)
1. [Tripartite Orientation](#1-tripartite-orientation)
2. [Navigation & Quick Commands](#2-navigation--quick-commands)
3. [Diagnostic Cycle](#3-diagnostic-cycle)
4. [Docker & Stack Boots](#4-docker--stack-boots)
5. [Agent-Specific FAQs](#5-agent-specific-faqs)
   - [GitHub Copilot](#github-copilot)
   - [Claude & Continue.dev](#claude--continuedev)
   - [Ollama Local LLMs](#ollama-local-llms)
   - [ChatDev Multi-Agent Teams](#chatdev-multi-agent-teams)
   - [LM Studio](#lm-studio)
    - [5.4 VS Code Integration Points](#54-vs-code-integration-points)
   - [5.5 Advanced Integration Patterns](#55-advanced-integration-patterns)
   - [5.6 Performance Tuning Guide](#56-performance-tuning-guide)
   - [5.7 Real-World Workflow Examples](#57-real-world-workflow-examples)
   - [5.8 Environment Configuration Reference](#58-environment-configuration-reference)
6. [Lessons Learned & Self-Healing](#6-lessons-learned--self-healing)
7. [Deep Dive: Key Subsystems](#7-deep-dive-key-subsystems)
8. [Troubleshooting Playbook](#8-troubleshooting-playbook)

---

## 0. 🎓 Learning Platform Index

Use this guide as the **spine**, then jump into the most relevant companion guides per task. These are **existing** references across the three repos; the goal is to **reuse** before creating new docs.

### 🧠 NuSyQ-Hub (Orchestration Brain)

| Purpose | Guide | Why it matters |
| --- | --- | --- |
| Fastest boot | [docs/QUICK_START_GUIDE.md](../docs/QUICK_START_GUIDE.md) | Start critical services and validate status bars in minutes. |
| Workspace wiring | [docs/WORKSPACE_SETUP_GUIDE.md](../docs/WORKSPACE_SETUP_GUIDE.md) | Explains `.env.workspace`, `workspace_loader.ps1`, and `workspace_mapping.yaml`. |
| Doc map & system map | [docs/DOCUMENTATION_INDEX.md](../docs/DOCUMENTATION_INDEX.md), [docs/SYSTEM_MAP.md](../docs/SYSTEM_MAP.md), [docs/ARCHITECTURE_MAP.md](../docs/ARCHITECTURE_MAP.md) | Master index + architecture overview to orient fast. |
| Workflow overview | [docs/WORKFLOW_OVERVIEW.md](../docs/WORKFLOW_OVERVIEW.md), [docs/OPERATIONS_RUNBOOK.md](../docs/OPERATIONS_RUNBOOK.md) | End-to-end flow + operational runbook (OPERATIONAL_RUNBOOK.md is an empty placeholder). |
| Workspace + WSL | [docs/WORKSPACE_FOLDER_MAPPING_TECHNICAL.md](../docs/WORKSPACE_FOLDER_MAPPING_TECHNICAL.md), [docs/WSL_INTEGRATION.md](../docs/WSL_INTEGRATION.md) | Path resolution, WSL bridging, and folder mapping detail. |
| Obsidian graph | [docs/OBSIDIAN_DEPENDENCY_GUIDE.md](../docs/OBSIDIAN_DEPENDENCY_GUIDE.md), [docs/Obsidian_Vault_Index.md](../docs/Obsidian_Vault_Index.md) | Visual dependency graph + vault index for fast navigation. |
| Routing rules | [docs/ROUTING_RULES.md](../docs/ROUTING_RULES.md) | Task routing and agent selection rules. |
| Agent onboarding | [docs/GETTING_STARTED_FOR_AGENTS.md](../docs/GETTING_STARTED_FOR_AGENTS.md) | Capability discovery and quick command catalog. |
| Agent productivity | [docs/AGENT_PRODUCTIVITY_PLAYBOOK.md](../docs/AGENT_PRODUCTIVITY_PLAYBOOK.md) | Daily operating patterns and safe workflows. |
| Service ops | [docs/SERVICE_STARTUP_GUIDE.md](../docs/SERVICE_STARTUP_GUIDE.md), [docs/SERVICE_MANAGEMENT.md](../docs/SERVICE_MANAGEMENT.md) | Boot order, monitoring, and service control. |
| Diagnostics | [docs/OPERATIONS.md](../docs/OPERATIONS.md), [docs/DIAGNOSTIC_SYSTEMS_STATUS_REPORT.md](../docs/DIAGNOSTIC_SYSTEMS_STATUS_REPORT.md) | Health checks and canonical diagnostics cycle. |
| Docker stack | [docs/DOCKER_FULL_STACK_SETUP_PLAN.md](../docs/DOCKER_FULL_STACK_SETUP_PLAN.md), [docs/SESSION_DOCKER_SETUP_20260203.md](../docs/SESSION_DOCKER_SETUP_20260203.md), [docs/DOCKER_MODERNIZATION_GUIDE.md](../docs/DOCKER_MODERNIZATION_GUIDE.md) | Full-stack compose, troubleshooting, and path overrides. |
| CLI reference | [docs/CLI_REFERENCE.md](../docs/CLI_REFERENCE.md) | Command catalog with example invocations. |
| AI workflow | [docs/AI_WORKFLOW_GUIDE.md](../docs/AI_WORKFLOW_GUIDE.md) | Agent routing patterns and execution discipline. |
| Orchestration deep dive | [docs/UNIFIED_ORCHESTRATION_SYSTEM.md](../docs/UNIFIED_ORCHESTRATION_SYSTEM.md) | How multi-agent orchestration is wired. |
| Startup automation | [docs/ECOSYSTEM_STARTUP_AUTOMATION.md](../docs/ECOSYSTEM_STARTUP_AUTOMATION.md) | Automated bring-up scripts and dependencies. |
| Order of operations | [docs/ORDER_OF_OPERATIONS_GUIDE.md](../docs/ORDER_OF_OPERATIONS_GUIDE.md) | Curated dependency and startup sequencing. |
| Terminal routing | [docs/TERMINAL_ROUTING_GUIDE.md](../docs/TERMINAL_ROUTING_GUIDE.md), [docs/LIVE_TERMINAL_ROUTING_GUIDE.md](../docs/LIVE_TERMINAL_ROUTING_GUIDE.md), [docs/TERMINAL_COCKPIT_GUIDE.md](../docs/TERMINAL_COCKPIT_GUIDE.md) | 16-terminal routing system and log streams. |
| Observability | [docs/OBSERVABILITY_QUICKSTART.md](../docs/OBSERVABILITY_QUICKSTART.md), [docs/HEALTH_DASHBOARD_GUIDE.md](../docs/HEALTH_DASHBOARD_GUIDE.md) | Metrics, dashboards, and health checks. |
| Learning loop | [docs/LEARNING_SYSTEM_GUIDE.md](../docs/LEARNING_SYSTEM_GUIDE.md) | How patterns/XP are recorded and reused. |
| Smart search | [docs/SMART_SEARCH_AGENT_GUIDE.md](../docs/SMART_SEARCH_AGENT_GUIDE.md) | Zero-token discovery system usage. |
| Agent contract | [docs/ROSETTA_STONE.md](../docs/ROSETTA_STONE.md) and [prime anchor Rosetta](../.vscode/prime_anchor/docs/ROSETTA_STONE.md) | Operational contract and quick context attachment. |

### 🎮 SimulatedVerse (Consciousness & Culture-Ship)

| Purpose | Guide | Why it matters |
| --- | --- | --- |
| System overview | [SimulatedVerse README](../../SimulatedVerse/SimulatedVerse/README.md) | Architecture, ports, core systems, and quick start. |
| Culture-Ship ops | [CULTURE_SHIP_READY.md](../../SimulatedVerse/SimulatedVerse/CULTURE_SHIP_READY.md) | Autonomous development workflow and ship commands. |
| Deployment | [DEPLOYMENT.md](../../SimulatedVerse/SimulatedVerse/DEPLOYMENT.md) | Zero-token deployment + safety configuration. |
| Edge systems | [EDGE_SYSTEM_QUICK_REFERENCE.md](../../SimulatedVerse/SimulatedVerse/EDGE_SYSTEM_QUICK_REFERENCE.md) | Quick reference for edge runtime features. |
| ChatDev integration | [README_CHATDEV_INTEGRATION.md](../../SimulatedVerse/SimulatedVerse/README_CHATDEV_INTEGRATION.md) | How multi-agent teams tie into SimulatedVerse. |
| Quadpartite ops | [QUADPARTITE_DEPLOYMENT.md](../../SimulatedVerse/SimulatedVerse/QUADPARTITE_DEPLOYMENT.md) | Multi-repo deployment alignment. |

### 🤖 NuSyQ Root (Multi-Agent + LLM Toolchain)

| Purpose | Guide | Why it matters |
| --- | --- | --- |
| Root overview | [NuSyQ README](../../NuSyQ/README.md) | Top-level repo goals + entry points. |
| New tooling | [NEW_TOOLS_QUICKSTART.md](../../NuSyQ/docs/NEW_TOOLS_QUICKSTART.md) | Cody, AI Toolkit, Haystack, pre-commit hooks. |
| Roadmap | [TOOL_INTEGRATION_ROADMAP.md](../../NuSyQ/docs/TOOL_INTEGRATION_ROADMAP.md) | Eight-week plan for multi-agent integrations. |
| Modernization | [MODERNIZATION_AUDIT_REPORT.md](../../NuSyQ/docs/MODERNIZATION_AUDIT_REPORT.md) | Quick wins and structural assessment. |
| Code tour | [CODE_TOUR_SUMMARY.md](../../NuSyQ/docs/CODE_TOUR_SUMMARY.md), [CODE_TOUR_COMPREHENSIVE.md](../../NuSyQ/docs/CODE_TOUR_COMPREHENSIVE.md) | Guided walkthrough (CodeTour extension). |
| Navigation beacons | [AI_NAVIGATION_BEACON_SYSTEM.md](../../NuSyQ/docs/AI_NAVIGATION_BEACON_SYSTEM.md) | Cross-repo navigation cues for agents. |
| AI council | [AI_COUNCIL_QUICK_START.md](../../NuSyQ/docs/AI_COUNCIL_QUICK_START.md) | Consensus workflows and council operations. |

### ✅ Recommended Learning Path (Minimal)

1. Run **Workspace Setup** (`docs/WORKSPACE_SETUP_GUIDE.md`) and validate with `python scripts/validate_and_setup_workspace.py --setup`.
2. Skim **Quick Start** (`docs/QUICK_START_GUIDE.md`) and **Agent Tutorial** (this file).
3. Scan **DOCUMENTATION_INDEX.md** + **SYSTEM_MAP.md** to orient and avoid duplicate docs.
4. Read **GETTING_STARTED_FOR_AGENTS.md** for capability discovery and command taxonomy.
5. Use **SimulatedVerse README** + **CULTURE_SHIP_READY.md** when crossing into consciousness/quest workflows.
6. Use **NuSyQ Root README** + **NEW_TOOLS_QUICKSTART.md** for multi-agent + tooling behavior.

---

## 1. 🌐 Tripartite Orientation

The NuSyQ ecosystem operates as **three interconnected repositories**, each with distinct responsibilities:

### 🧠 **NuSyQ-Hub** (Primary Orchestrator - C:\Users\keath\Desktop\Legacy\NuSyQ-Hub)

**Role:** Brain of the system - orchestrates AI agents, routes tasks, manages consciousness integration.

**Key Capabilities:**
- Multi-AI orchestration (Copilot + Ollama + ChatDev + Claude + Consciousness Bridge)
- Quest system (`src/Rosetta_Quest_System/quest_log.jsonl`)
- Smart Search (`src/search/smart_search.py`) - zero-token knowledge retrieval
- Self-healing (`src/healing/quantum_problem_resolver.py`)
- Diagnostic reports (`scripts/start_nusyq.py error_report`)

**Entry Points:**
- `python scripts/start_nusyq.py` → System state snapshot
- `python scripts/start_nusyq.py error_report` → Canonical error diagnostics
- `python -m src.search.smart_search keyword "<term>"` → Zero-token search

**When to Use Hub:**
- Orchestrating multi-AI tasks
- Running diagnostics/health checks
- Accessing quest system
- Triggering self-healing workflows
- Managing consciousness/orchestration routing

**Reference Docs:**
- [README.md](../README.md) - Setup & architecture
- [AGENTS.md](../AGENTS.md) - Agent navigation protocol
- [OPERATIONS.md](../docs/OPERATIONS.md) - Operational workflows
- [.github/copilot-instructions.md](../.github/copilot-instructions.md) - Copilot integration

---

### 🎮 **SimulatedVerse** (Consciousness Simulator - C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse)

**Role:** Consciousness simulation engine with playable debugging and Temple of Knowledge progression system.

**Key Capabilities:**
- ΞNuSyQ ConLang Framework (self-coding autonomous AI)
- Temple of Knowledge (10-floor progression: Foundations → Overlook)
- House of Leaves (recursive debugging labyrinth)
- Guardian Ethics (Culture Mind oversight)
- 9 Modular Agents (synth/patch-bay coordination)
- Dual Interface: Express (Port `SIMULATEDVERSE_PORT`, default 5002) + React (Port 3000)

**Entry Points:**
- `npm run dev` → Start consciousness engine (Port 5002 + 3000)
- `npm run devshell` → Interactive development shell
- `bash adapters/replit/agent.sh` → Playable debugging mode

**When to Use SimulatedVerse:**
- Consciousness-level debugging (XP/levels/quests)
- UI/UX development (React dashboard)
- Temple knowledge queries
- Autonomous PU queue processing
- Game-like agent coordination

**Reference Docs:**
- [README.md](../../SimulatedVerse/SimulatedVerse/README.md) - ΞNuSyQ framework
- [DEPLOYMENT.md](../../SimulatedVerse/SimulatedVerse/DEPLOYMENT.md) - Stack setup
- [CULTURE_SHIP_READY.md](../../SimulatedVerse/SimulatedVerse/CULTURE_SHIP_READY.md) - Integration guide

---

### 🤖 **NuSyQ Root** (Multi-Agent Hub - C:\Users\keath\NuSyQ)

**Role:** ChatDev integration, Ollama model management, MCP server, multi-agent orchestration.

**Key Capabilities:**
- 14 AI Agents (Claude Code + 7 Ollama + ChatDev 5-agent teams + Copilot + Continue.dev)
- ChatDev multi-agent software company (CEO, CTO, Programmer, Tester, Reviewer)
- Ollama Models (37.5GB local LLM collection: qwen2.5-coder, starcoder2, gemma2, etc.)
- MCP Server (Model Context Protocol coordination)
- Offline-first development (95% offline capability)

**Entry Points:**
- `.\NuSyQ.Orchestrator.ps1` → Automated environment setup
- `python nusyq_chatdev.py` → ChatDev wrapper with ΞNuSyQ integration
- MCP server: `python mcp_server/main.py` (Node.js alternative available)

**When to Use NuSyQ Root:**
- Multi-agent code generation (ChatDev teams)
- Local LLM orchestration (Ollama models)
- MCP-based agent coordination
- Offline development workflows
- ΞNuSyQ protocol messaging

**Reference Docs:**
- [README.md](../../NuSyQ/README.md) - Self-aware context-persistent engine
- [nusyq.manifest.yaml](../../NuSyQ/nusyq.manifest.yaml) - Configuration manifest
- [knowledge-base.yaml](../../NuSyQ/knowledge-base.yaml) - Persistent learning

---

### 📊 **Tripartite Flow Diagram**

```
┌─────────────────────────────────────────────────────────────────┐
│  USER REQUEST                                                   │
│  ("Analyze errors", "Generate code", "Debug consciousness")    │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  NuSyQ-Hub (Orchestrator Brain)                                 │
│  ├─ Smart Search (zero-token context)                           │
│  ├─ Quest System (task tracking)                                │
│  ├─ Multi-AI Orchestrator (routing decisions)                   │
│  └─ Diagnostic Cycle (error_report, health checks)              │
└─────────────┬──────────────────────┬────────────────────────────┘
              │                      │
              ▼                      ▼
┌──────────────────────┐  ┌──────────────────────────────────────┐
│  SimulatedVerse      │  │  NuSyQ Root (Multi-Agent)            │
│  (UI/Consciousness)  │  │  ├─ ChatDev Teams (code gen)         │
│  ├─ Temple Queries   │  │  ├─ Ollama LLMs (local inference)    │
│  ├─ PU Queue         │  │  ├─ MCP Server (coordination)        │
│  ├─ React Dashboard  │  │  └─ ΞNuSyQ Protocol (messaging)      │
│  └─ Debugging XP     │  └──────────────────────────────────────┘
└──────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│  RESULT SYNTHESIS                                               │
│  (Reports, code artifacts, consciousness states, quest updates) │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 🧭 Navigation & Quick Commands

### **Workspace Loader System**

The tripartite workspace uses `.env.workspace` + `workspace_loader.ps1` for unified navigation.

**Setup (One-time):**

1. **Verify Workspace Health:**
   ```powershell
   cd C:\Users\keath\Desktop\Legacy\NuSyQ-Hub
   python scripts/validate_and_setup_workspace.py --setup
   ```

2. **Quick Verification (lightweight):**

   ```powershell
   python scripts/verify_tripartite_workspace.py
   ```

3. **Enable Aliases (if missing):**

   If verifier reports missing profile loader, add to your PowerShell profile:

   ```powershell
   # Add to profile (get path via: $PROFILE)
   . "C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\.vscode\workspace_loader.ps1"
   ```

4. **Reload Profile:**
   ```powershell
   . $PROFILE
   ```

**Note:** These aliases/functions are PowerShell-only. In WSL/bash, run the underlying commands directly (e.g., `python scripts/start_nusyq.py`) or launch `pwsh` and source the profile.

### **Quick Navigation Aliases**

Once loader is active:

| Alias | Destination | Purpose |
|-------|-------------|---------|
| `cdhub` | NuSyQ-Hub root | Orchestrator brain |
| `cdroot` | NuSyQ root | Multi-agent hub |
| `cdverse` | SimulatedVerse/SimulatedVerse | Consciousness engine app |
| `cdanchor` | .vscode/prime_anchor | Meta workspace anchor |
| `cdsrc` | NuSyQ-Hub/src | Source code |
| `cdscripts` | NuSyQ-Hub/scripts | Utility scripts |

### **Quick Action Aliases**

| Alias | Command | Purpose |
|-------|---------|---------|
| `start-system` | `python scripts/start_nusyq.py` | System state snapshot |
| `show-state` | `Get-Content state/reports/current_state.md` | View latest snapshot |
| `error-report` | `python scripts/start_nusyq.py error_report` | Canonical diagnostics |

### **Top 10 Daily Commands**

```powershell
# 1. System health snapshot
python scripts/start_nusyq.py

# 2. Canonical error diagnostics (ground truth)
python scripts/start_nusyq.py error_report

# 3. Zero-token knowledge search
python -m src.search.smart_search keyword "orchestration" --limit 50

# 4. Verify tripartite workspace alignment
python scripts/verify_tripartite_workspace.py

# 5. Find existing tools (reuse-first)
python scripts/find_existing_tool.py --capability "diagnostic" --max-results 5

# 6. Test LM Studio connectivity
python scripts/test_lmstudio.py --base http://10.0.0.172:1234

# 7. Docker stack status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 8. View quest log (last 20 entries)
Get-Content src/Rosetta_Quest_System/quest_log.jsonl -Tail 20 | ConvertFrom-Json

# 9. Check Ollama models (if installed)
ollama list

# 10. Prune old summaries (cleanup)
python scripts/summary_pruner.py --plan --age-days 30
```

---

## 3. 🔍 Diagnostic Cycle

### **Three-Tier Diagnostic Hierarchy**

1. **Quick Health (30 seconds):**
   ```powershell
   python scripts/start_nusyq.py
   # Outputs: state/reports/current_state.md
   # Shows: Repo status, quest summary, agent availability, action menu
   ```

2. **Full Error Report (2-5 minutes):**
   ```powershell
   python scripts/start_nusyq.py error_report
   # Outputs: docs/Reports/diagnostics/unified_error_report_<timestamp>.md
   # Shows: Mypy, ruff, pylint errors across all 3 repos with breakdown
   ```

3. **Report Hygiene (1 minute, optional but recommended):**
   ```powershell
   # Generates docs/Auto/SUMMARY_PRUNE_PLAN.json (dry-run)
   python scripts/summary_pruner.py --plan
   ```

4. **Targeted Analysis (as needed):**
   ```powershell
   # Import health audit
   python src/diagnostics/ImportHealthCheck.ps1

   # Specific file syntax check
   python -m py_compile src/path/to/file.py

   # Smart search for specific patterns
   python -m src.search.smart_search keyword "exception handling"
   ```

### **Diagnostic Artifact Locations**

| Artifact Type | Location | Purpose |
|---------------|----------|---------|
| **Current State** | `state/reports/current_state.md` | Latest system snapshot |
| **Error Reports** | `docs/Reports/diagnostics/` | Full diagnostic scans |
| **Prune Plans** | `docs/Auto/SUMMARY_PRUNE_PLAN.json` | Summary/report pruning plan |
| **Workspace Validation** | `state/reports/workspace_validation.json` | Folder/loader sanity report |
| **Session Logs** | `docs/Agent-Sessions/SESSION_*.md` | Agent work history |
| **Quest Log** | `src/Rosetta_Quest_System/quest_log.jsonl` | Task tracking (JSONL) |
| **Progress Tracker** | `config/ZETA_PROGRESS_TRACKER.json` | Development milestones |
| **Docker Logs** | Root directory: `build_*.log` | Build/deployment logs |

### **Error Signal Consistency Protocol**

**Ground Truth Source:** Unified error reporter (`python scripts/start_nusyq.py error_report`)  
**Historical Baseline (2025-12-25):** 1,228 errors across 3 repos  
**VS Code View (same snapshot):** 209 errors (filtered subset - this is NORMAL)

**When agents disagree on error counts:**

```powershell
# Run ground truth command
python scripts/start_nusyq.py error_report

# Returns unified diagnostic report with:
# - Breakdown by repo (Hub, SimulatedVerse, NuSyQ)
# - Breakdown by severity (error, warning, info)
# - Breakdown by type (mypy, ruff, pylint)
```

**Reference:** [docs/SIGNAL_CONSISTENCY_PROTOCOL.md](../docs/SIGNAL_CONSISTENCY_PROTOCOL.md), [docs/AGENT_ERROR_REFERENCE_CARD.md](../docs/AGENT_ERROR_REFERENCE_CARD.md)

---

## 4. 🐋 Docker & Stack Boots

### **Docker Desktop WSL Integration**

**Prerequisites:**
- Docker Desktop installed on Windows
- WSL 2 enabled
- WSL integration enabled for your distro in Docker Desktop settings

**Verify Docker Access:**

```powershell
# From PowerShell (Windows host)
docker version
docker ps

# If permission denied, enable WSL integration:
# Docker Desktop → Settings → Resources → WSL Integration → Enable for your distro
```

**CRITICAL:** Use `docker compose` (modern) from PowerShell, NOT `docker-compose` (legacy) from WSL bash.

**Reference:** [docs/WSL_INTEGRATION.md](../docs/WSL_INTEGRATION.md)

### **SimulatedVerse Path Override**

For full-stack deployments that include SimulatedVerse:

```powershell
# Set environment overrides (Windows paths)
$env:SIMULATEDVERSE_PATH="C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse"
$env:SIMULATEDVERSE_DOCKERFILE="C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse\Dockerfile"

# Build full stack
docker compose -f "C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\deploy\docker-compose.full-stack.yml" --profile full build

# Start services
docker compose -f "C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\deploy\docker-compose.full-stack.yml" --profile full up -d
```

**Note:** If the build fails with `failed to read dockerfile: open Dockerfile: no such file or directory`, verify that `C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse\Dockerfile` exists or point `SIMULATEDVERSE_DOCKERFILE` to a valid Dockerfile. As of 2026-02-04 the SimulatedVerse repo does not ship a default Dockerfile, so one must be provided.

### **Compose Profiles**

| Profile | Services Included | Use Case |
|---------|-------------------|----------|
| `dev` | nusyq-hub, postgres, redis | Local development |
| `full` | + ollama, simulatedverse, quest-tracker | Full stack |
| `agents` | + chatdev, additional AI services | Multi-agent orchestration |

### **Service Bring-Up Order**

```powershell
# 1. Infrastructure (databases first)
docker compose -f deploy/docker-compose.full-stack.yml up -d postgres redis

# 2. Core services (after databases healthy)
docker compose -f deploy/docker-compose.full-stack.yml up -d nusyq-hub

# 3. AI services (after hub ready)
docker compose -f deploy/docker-compose.full-stack.yml --profile full up -d ollama simulatedverse

# 4. Verify health
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### **Common Ports**

| Service | Port | Purpose |
|---------|------|---------|
| nusyq-hub | 8000 | Main API |
| nusyq-hub | 5678 | Debug (debugpy) |
| SimulatedVerse | `SIMULATEDVERSE_PORT` (default 5000) | Express backend |
| SimulatedVerse | 3000 | React UI |
| Ollama | 11434 | Local LLM API |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache |
| Quest Tracker | 8080 | Quest dashboard |

### **Docker Troubleshooting**

```powershell
# Check service logs
docker compose -f deploy/docker-compose.full-stack.yml logs nusyq-hub --tail 100

# Restart a service
docker compose -f deploy/docker-compose.full-stack.yml restart nusyq-hub

# Rebuild without cache
docker compose -f deploy/docker-compose.full-stack.yml build --no-cache nusyq-hub

# Clean slate (⚠️ removes volumes)
docker compose -f deploy/docker-compose.full-stack.yml down -v

# View resource usage
docker stats
```

**Reference:** [SESSION_DOCKER_SETUP_20260203.md](../SESSION_DOCKER_SETUP_20260203.md), [DOCKER_FULL_STACK_SETUP_PLAN.md](../DOCKER_FULL_STACK_SETUP_PLAN.md)

---

## 5. 🤖 Agent-Specific FAQs

### **GitHub Copilot**

**Q: How do I attach tripartite context to Copilot sessions?**

A: Copilot automatically loads `.github/copilot-instructions.md` and `.github/instructions/*.md`. For session-specific context:

1. Open [ROSETTA_STONE.md](.vscode/prime_anchor/docs/ROSETTA_STONE.md) (first 200 lines)
2. Use `@workspace` mention for workspace-wide queries
3. Reference [AGENTS.md](../AGENTS.md) for navigation protocol

**Q: How do I switch between repos mid-conversation?**

A: Use aliases (`cdhub`, `cdroot`, `cdverse`) and restate context:
```
"Switching to SimulatedVerse context. Opening SimulatedVerse/README.md..."
```

**Q: How do I access quest system?**

A:
```powershell
# View quests
Get-Content src/Rosetta_Quest_System/quest_log.jsonl -Tail 20 | ConvertFrom-Json | Format-Table

# Search quests
python -m src.search.smart_search keyword "quest: error handling"

# Filter by status
Get-Content src/Rosetta_Quest_System/quest_log.jsonl | ConvertFrom-Json | Where-Object {$_.status -eq 'in_progress'} | Select-Object title, priority, assigned_to
```

**Q: What are Copilot's best practices in NuSyQ context?**

A:
- ✅ **Use @workspace for context** - Pulls entire workspace structure
- ✅ **Reference existing patterns** - Link to `docs/EXCEPTION_HANDLER_REFACTORING_LOG.md` for established patterns
- ✅ **Enable GitHub Copilot CLI** - Use `gh copilot` for PR descriptions, commit messages
- ✅ **Leverage instructions files** - Copilot reads 6 `.github/instructions/*.md` files automatically
- ✅ **Break work into quests** - Each refactoring task → logs to quest_log.jsonl
- ❌ **Avoid broad Exception handlers** - Always specify (TypeError, ValueError, RuntimeError, etc.)
- ❌ **Don't create files without Three Before New** - Always search existing tools first

**Reference:** [.github/copilot-instructions.md](../.github/copilot-instructions.md)

---

### **Claude / Continue.dev**

**Q: How do I configure local LLM providers?**

A: Edit `.continue/config.json`:

```json
{
  "models": [
    {
      "title": "Ollama qwen2.5-coder (Fast)",
      "provider": "ollama",
      "model": "qwen2.5-coder:latest",
      "apiBase": "http://localhost:11434",
      "contextLength": 32000
    },
    {
      "title": "LM Studio local (High-quality)",
      "provider": "openai",
      "model": "neural-chat-7b-v3-1",
      "apiBase": "http://10.0.0.172:1234/v1",
      "apiKey": "not-needed"
    },
    {
      "title": "Claude (Cloud - fallback)",
      "provider": "anthropic",
      "model": "claude-3-sonnet-20240229",
      "apiKey": "${process.env.ANTHROPIC_API_KEY}"
    }
  ],
  "embeddingsProvider": {
    "provider": "ollama",
    "model": "nomic-embed-text:latest",
    "apiBase": "http://localhost:11434"
  },
  "reranker": {
    "provider": "ollama",
    "model": "bge-reranker-base:latest"
  }
}
```

**Q: How do I use zero-token search instead of embeddings?**

A: Smart Search CLI:
```powershell
python -m src.search.smart_search keyword "consciousness integration" --limit 50
```

Returns file paths + line numbers → attach to context without embedding calls.

**Q: How do I optimize context window usage?**

A: Claude's context management:
```python
# For large files, use targeted snippets
from src.search.smart_search import search_keyword

# Get surrounding context (50 lines before/after match)
results = search_keyword("orchestration", context_lines=50)
# Manually attach only relevant snippets to Claude, not entire files
```

**Q: How do I set up local Claude via Ollama?**

A: Ollama doesn't run Claude natively, but you can use:
```powershell
# Alternative: Use neural-chat or similar instruction-tuned model
ollama pull neural-chat-7b-v3-1

# In .continue/config.json:
# { "title": "Neural Chat (Claude-like)", "provider": "openai", "apiBase": "http://localhost:11434/v1" }
```

**Q: What are Continue.dev's keyboard shortcuts?**

A:
- `Ctrl+K` - Start inline edit
- `Ctrl+I` - Open Continue sidebar
- `Ctrl+L` - Switch chat context
- `Ctrl+Shift+M` - Accept/reject changes
- `@` - Reference specific files/workspace
- `/` - Trigger command palette

**Reference:** [.continue/config.json](../.continue/config.json), [Continue.dev Docs](https://docs.continue.dev)

---

### **Ollama Local LLMs**

**Q: Which models are installed and what are they best for?**

A:
```powershell
ollama list
```

**Model Comparison & Use Cases:**

| Model | Size | Best For | Speed | Quality |
|-------|------|----------|-------|---------|
| qwen2.5-coder | 3.2B | Quick code analysis | 🚀 Fast | ⭐⭐⭐⭐ |
| deepseek-coder-v2 | 6.7B | Complex logic, refactoring | 🚀🚀 Medium | ⭐⭐⭐⭐⭐ |
| starcoder2 | 3B/7B | Code completion | 🚀 Fast/Medium | ⭐⭐⭐⭐ |
| gemma2 | 2B/9B | General purpose | 🚀 Fast | ⭐⭐⭐ |
| neural-chat-7b | 7B | Conversational AI | 🚀🚀 Medium | ⭐⭐⭐⭐ |
| mistral | 7B | Reasoning tasks | 🚀🚀 Medium | ⭐⭐⭐⭐ |
| llama2 | 7B/13B | Code gen + reasoning | 🚀🚀 Medium | ⭐⭐⭐⭐ |

**Quick Selection Guide:**
- **Under 30 seconds turnaround:** Use qwen2.5-coder
- **Complex refactoring/logic:** Use deepseek-coder-v2
- **Just exploring:** Use gemma2 (lightweight)
- **Multi-turn reasoning:** Use mistral or llama2

**Q: How do I invoke Ollama from orchestration?**

A:
```python
from src.tools.agent_task_router import analyze_with_ai

# Specific model
result = analyze_with_ai(
    file_path="src/path/to/file.py",
    target="ollama",
    analysis_type="code_quality",
    model="deepseek-coder-v2"
)

# Auto-routing (orchestrator chooses)
result = analyze_with_ai(
    file_path="src/api/systems.py",
    target="auto"  # Picks qwen for speed or deepseek for quality
)
```

**Q: How do I benchmark Ollama model performance?**

A:
```powershell
# Time a single inference
$start = Get-Date
ollama run qwen2.5-coder "Write a Python function to parse JSON"
$elapsed = (Get-Date) - $start
Write-Host "Elapsed: $($elapsed.TotalSeconds)s"

# Batch benchmark (5 prompts)
$prompts = @(
    "Explain Python decorators",
    "How do you handle exceptions?",
    "Write grep in Python",
    "Explain async/await",
    "Design a cache system"
)
foreach ($prompt in $prompts) {
    $start = Get-Date
    ollama run qwen2.5-coder $prompt | Out-Null
    $elapsed = (Get-Date) - $start
    Write-Host "$prompt: $($elapsed.TotalSeconds)s"
}
```

**Q: How do I customize Ollama system prompts?**

A: Create a custom modelfile:
```dockerfile
FROM qwen2.5-coder:latest

SYSTEM You are an expert Python developer specializing in NuSyQ orchestration.
Your task is to:
1. Analyze code for architectural coherence
2. Suggest refactorings following Three Before New protocol
3. Reference existing patterns from src/
4. Always prefer extending existing tools over creating new ones

Focus on:
- Exception handler specificity
- Consciousness integration patterns
- Quest-driven development
- Multi-AI orchestration coordination
```

Save as `Modelfile.custom`, then:
```powershell
ollama create qwen-nusyq -f Modelfile.custom
ollama run qwen-nusyq "Analyze src/orchestration/unified_ai_orchestrator.py"
```

**Q: How do I add a new Ollama model?**

A:
```powershell
# Pull model
ollama pull deepseek-coder-v2

# Verify
ollama list

# Test
ollama run deepseek-coder-v2 "Write a Python hello world"
```

**Reference:** [NuSyQ/README.md](../../NuSyQ/README.md), [src/ai/ollama_hub.py](../src/ai/ollama_hub.py)

---

### **ChatDev Multi-Agent Teams**

**Q: How do I generate code with ChatDev?**

A:
```powershell
cd C:\Users\keath\NuSyQ
python nusyq_chatdev.py

# Or via orchestrator:
python -c "from src.tools.agent_task_router import generate_with_ai; generate_with_ai('Create REST API with JWT auth', target='chatdev')"
```

**Q: How do I customize ChatDev agents (CEO, CTO, Programmer, Tester, Reviewer)?**

A: Edit `NuSyQ/ChatDev/CompanyConfig/Default/ChatChainConfig.json`:

```json
{
  "CEO": {
    "description": "Oversees project planning and requirements",
    "model": "qwen2.5-coder",
    "temperature": 0.5,
    "max_tokens": 2000,
    "system_prompt": "You are a visionary CEO..."
  },
  "CTO": {
    "description": "Designs architecture and technical decisions",
    "model": "deepseek-coder-v2",
    "temperature": 0.3,
    "max_tokens": 3000
  },
  "Programmer": {
    "description": "Implements code based on CTO's design",
    "model": "deepseek-coder-v2",
    "temperature": 0.0,
    "max_tokens": 4000
  },
  "Tester": {
    "description": "Writes comprehensive test suites",
    "model": "qwen2.5-coder",
    "temperature": 0.2,
    "max_tokens": 2500
  },
  "Reviewer": {
    "description": "Reviews code quality and security",
    "model": "deepseek-coder-v2",
    "temperature": 0.3,
    "max_tokens": 2000
  }
}
```

**Best Practices:**
- CEO/CTO: Higher temperature (0.3-0.5) for creativity
- Programmer: Lower temperature (0.0-0.1) for deterministic code
- Tester: Medium temperature (0.2-0.3) for balanced test generation
- Reviewer: Low temperature (0.2-0.3) for consistency

**Q: What's the typical ChatDev team workflow?**

A: Sequential agent coordination:

```
1. CEO (2 min)
   ├─ Analyzes requirements
   ├─ Sets project scope
   └─ Defines success criteria

2. CTO (3-5 min)
   ├─ Designs architecture
   ├─ Selects technologies
   └─ Creates class diagrams

3. Programmer (5-15 min, longest step)
   ├─ Implements modules
   ├─ Handles edge cases
   └─ Writes documentation

4. Tester (3-8 min)
   ├─ Writes unit tests
   ├─ Creates integration tests
   └─ Defines edge case tests

5. Reviewer (2-5 min, final check)
   ├─ Code quality check
   ├─ Security analysis
   └─ Performance review
```

**Total typical time: 15-40 minutes** for a medium project (CRUD API, data processor)

**Q: How do I monitor ChatDev progress?**

A:
```powershell
# Watch logs in real-time
Get-ChildItem C:\Users\keath\NuSyQ\ChatDev\WareHouse -Recurse -Filter "*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | ForEach-Object { Get-Content $_ -Tail 50 -Wait }

# Check latest project output
$latest = Get-ChildItem C:\Users\keath\NuSyQ\ChatDev\WareHouse | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Get-ChildItem $latest.FullName -Filter "*.py" | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name, LastWriteTime
```

**Q: How do I integrate ChatDev output into NuSyQ-Hub?**

A:
```powershell
# 1. Generate with ChatDev
python nusyq_chatdev.py

# 2. ChatDev output location
# C:\Users\keath\NuSyQ\ChatDev\WareHouse\[ProjectName]_[timestamp]/

# 3. Validation checklist (before graduation)
# - All tests pass (pytest .)
# - Code follows PEP8 (ruff check .)
# - Type hints present (mypy .)
# - Documentation complete (README.md exists)

# 4. Graduated location
# Move to: C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\src\tools\[ProjectName]

# 5. Update quest log
python -c "from src.Rosetta_Quest_System import log_quest; log_quest('Graduated ChatDev project [ProjectName]', status='completed')"
```

**Q: What LLM models work best with ChatDev?**

A:
- ✅ **deepseek-coder-v2** - Best overall (balanced speed/quality)
- ✅ **qwen2.5-coder** - Fast iteration (for rapid prototyping)
- ✅ **mistral** - Good reasoning (for complex architectures)
- ❌ **gemma2** - Too small (inconsistent code gen)
- ❌ **starcoder2** - Older (prefer qwen/deepseek)

**Recommended Configuration:**
```json
{
  "CEO": "qwen2.5-coder",
  "CTO": "deepseek-coder-v2",
  "Programmer": "deepseek-coder-v2",
  "Tester": "qwen2.5-coder",
  "Reviewer": "deepseek-coder-v2"
}
```

**Reference:** [NuSyQ/ChatDev/README.md](../../NuSyQ/ChatDev/README.md), [Testing Chamber Pattern](#testing-chamber-pattern)

---

---

### **LM Studio**

**Q: How do I test LM Studio connectivity?**

A:
```powershell
python scripts/test_lmstudio.py --base http://10.0.0.172:1234

# Or direct curl test
curl http://10.0.0.172:1234/v1/models | ConvertFrom-Json | Select-Object -ExpandProperty data | Select-Object id, created
```

**Q: How do I add LM Studio models to the registry?**

A:
```powershell
python scripts/discover_and_sync_models.py --dry-run
```

**Q: How do I configure LM Studio as fallback when Ollama is down?**

A:
```json
{
  "models": [
    {
      "title": "Ollama qwen (Primary)",
      "provider": "ollama",
      "model": "qwen2.5-coder:latest",
      "apiBase": "http://localhost:11434"
    },
    {
      "title": "LM Studio local (Fallback)",
      "provider": "openai",
      "model": "neural-chat-7b-v3-1",
      "apiBase": "http://10.0.0.172:1234/v1",
      "apiKey": "not-needed"
    }
  ],
  "fallbackModel": {
    "provider": "openai",
    "model": "neural-chat-7b-v3-1",
    "apiBase": "http://10.0.0.172:1234/v1"
  }
}
```

**Q: How do I sync Ollama models to LM Studio?**

A:
```powershell
python scripts/discover_and_sync_models.py --dry-run
```

**Q: What are LM Studio's advantages over Ollama?**

A:
- ✅ **UI-based model management** - Visual interface for easy switching
- ✅ **Better integration with Continue.dev** - Native support in extensions
- ✅ **Model preview in UI** - See model info, parameters, system prompts visually
- ✅ **Stable HTTP server** - More reliable than Ollama daemon
- ✅ **Faster model loading** - Often quicker startup than Ollama
- ❌ **No CLI tools** - Requires UI or HTTP API
- ❌ **Single instance** - Can't run multiple LM Studio instances simultaneously

**Reference:** [LM Studio Docs](https://lmstudio.ai), [scripts/test_lmstudio.py](../scripts/test_lmstudio.py)

---

## 5.4. 🧩 VS Code Integration Points

This section documents the **current integration surfaces** between NuSyQ-Hub and the VS Code app, plus the **recommended extension hooks** if you want deeper in-editor control.

### ✅ Current Integration Surfaces (Implemented)

**1) Output Source Intelligence (VS Code Output → Terminals)**
- **File:** `src/system/output_source_intelligence.py`
- **Purpose:** Routes output from 100+ VS Code extensions into the 23 specialized terminals.
- **Targets:** Terminals like 🤖 Claude, 🔥 Errors, 💡 Suggestions, 📊 Metrics, 🛡️ Culture Ship.
- **Usage:** Use this when you need structured routing of diagnostics, AI output, or extension logs.

**2) Terminal Intelligence Orchestrator (Terminal Lifecycle + Routing)**
- **File:** `src/system/terminal_intelligence_orchestrator.py`
- **Purpose:** Defines the 23 terminal channels, roles, routing keywords, and intelligence levels.
- **Integration:** Works with `AgentTerminalRouter`, `TerminalManager`, and `TerminalRouter`.

**3) Terminal API (REST control for VS Code terminals)**
- **File:** `src/system/terminal_api.py`
- **Endpoints:**
    - `GET /health` – API health check
    - `POST /send` – Send message to a terminal channel
    - `GET /list` – List available terminals
    - `POST /api/terminals/start` – Start named terminal
    - `POST /api/terminals/stop` – Stop named terminal
    - `POST /api/terminals/send_command` – Execute command in terminal
    - `GET /api/terminals/output/{session_id}` – Pull terminal output
    - `GET /api/terminals/{channel}/recent` – Recent channel output

**4) Terminal Watchers (PowerShell)**
- **Folder:** `data/terminal_watchers/`
- **Purpose:** Dedicated watchers per terminal channel (e.g., Culture Ship, Errors, Metrics).
- **Usage:** For automation that tails logs and streams to VS Code terminals.

**5) Workspace Loader & Navigation Aliases**
- **File:** `.vscode/workspace_loader.ps1`
- **Purpose:** Defines VS Code-friendly aliases (e.g., `cdhub`, `cdroot`, `cdverse`, `start-system`).
- **Usage:** Keep the editor context aligned with the tripartite workspace.

**6) Prime Anchor (Observability + Telemetry)**
- **Folder:** `.vscode/prime_anchor/`
- **Purpose:** Grafana/TimescaleDB/trace service tooling for in-editor observability workflows.
- **Entry Points:** `scripts/bringup_stack.py`, `scripts/trace_service.py`, `scripts/metrics_timescale.py`.

### 🔧 Recommended VS Code Extension Hooks (Not Yet Wired)

These are integration points that would **enhance in-editor control** once added to a dedicated VS Code extension:

- `vscode.window.createTerminal(...)` → auto-provision terminals on workspace open
- `vscode.tasks.executeTask(...)` → launch existing NuSyQ tasks from command palette
- `vscode.window.createStatusBarItem(...)` → show system health, terminal routing state
- `vscode.workspace.onDidChangeTextDocument(...)` → trigger smart routing or AI suggestions
- `vscode.window.onDidChangeActiveTextEditor(...)` → update context in terminal router

If you want this, we can add a lightweight extension under a canonical location and register these hooks (per your request).

---

## 5.5. 🔗 Advanced Integration Patterns

### **Multi-AI Consensus Pattern**

When you need high-confidence decisions, run multiple AI systems in parallel:

```python
from src.orchestration.consensus_orchestrator import ConsensusOrchestrator

orchestrator = ConsensusOrchestrator()

result = orchestrator.run_consensus(
    prompt="Design a thread-safe cache system",
    models=[
        "qwen2.5-coder:latest",      # Fast baseline
        "deepseek-coder-v2:latest",  # High quality
        "mistral:latest"             # Good reasoning
    ],
    voting_strategy="ranked",  # weighted voting
    timeout_per_model=120,     # 2 minutes per model
)

print(f"Consensus approach: {result['consensus_output']}")
print(f"Agreement score: {result['agreement_score']}")  # 0.0-1.0
print(f"Dissenting opinions: {result['minority_views']}")
```

**Use Cases:**
- Architecture decisions requiring high confidence
- Security-critical code reviews
- Complex algorithm design
- Risk assessment for major refactoring

### **Streaming Output Pattern**

For long-running analysis, stream results in real-time:

```python
from src.tools.agent_task_router import analyze_with_ai

async def stream_analysis():
    async for chunk in analyze_with_ai(
        file_path="src/api/systems.py",
        target="ollama",
        stream=True,
        chunk_size=256
    ):
        print(f"[Analysis] {chunk}", end="", flush=True)
    print("\n[Complete]")

# Or use in sync context
import asyncio
asyncio.run(stream_analysis())
```

### **Chained AI Analysis Pattern**

Route analysis through a sequence of specialized agents:

```python
# Step 1: Fast initial scan with qwen
quick_analysis = analyze_with_ai(
    file_path="src/orchestration/unified_ai_orchestrator.py",
    target="ollama",
    model="qwen2.5-coder",
    analysis_type="diagnostics"
)

# Step 2: If issues found, deep dive with deepseek
if quick_analysis['error_count'] > 0:
    deep_analysis = analyze_with_ai(
        file_path="src/orchestration/unified_ai_orchestrator.py",
        target="ollama",
        model="deepseek-coder-v2",
        analysis_type="detailed_review",
        context=quick_analysis  # Pass previous results
    )

    # Step 3: Final recommendation from mistral
    recommendation = analyze_with_ai(
        file_path="src/orchestration/unified_ai_orchestrator.py",
        target="ollama",
        model="mistral",
        analysis_type="remediation_strategy",
        context=[quick_analysis, deep_analysis]
    )
```

---

## 5.5.5 🏛️ AI Council & Multi-Agent Coordination (NEW)

The NuSyQ ecosystem now includes enhanced multi-agent coordination features. Use these when you need consensus before taking significant actions.

### **AI Council Voting**

Propose decisions for multi-agent consensus:

```python
from src.ai.ai_intermediary import AIIntermediary
import asyncio

async def example_council_workflow():
    intermediary = AIIntermediary()
    await intermediary.initialize()

    # Propose a decision to the council
    proposal = await intermediary.propose_to_council(
        topic="Authentication Refactor",
        description="Refactor auth system to use JWT tokens",
        proposer="claude"
    )

    if proposal.get("success"):
        decision_id = proposal["decision_id"]

        # Cast votes (from multiple agents)
        await intermediary.vote_in_council(
            decision_id=decision_id,
            vote="approve",
            confidence=0.9,
            expertise=0.85,
            reasoning="JWT is more secure and scalable"
        )

        # If approved, execute via BackgroundTaskOrchestrator
        result = await intermediary.execute_council_decision(decision_id)
        print(f"Execution result: {result}")

asyncio.run(example_council_workflow())
```

### **Background Task Dispatch**

Offload expensive operations to local LLMs to save Claude/Copilot tokens:

```python
async def dispatch_expensive_task():
    intermediary = AIIntermediary()
    await intermediary.initialize()

    # Send to Ollama/LM Studio in the background
    result = await intermediary.dispatch_to_background(
        prompt="Analyze this codebase for security vulnerabilities",
        task_type="code_analysis",
        requesting_agent="claude",
        priority="normal"
    )

    if result.get("success"):
        task_id = result["task_id"]
        # Check status later
        status = await intermediary.check_background_task(task_id)
        print(f"Task status: {status}")
```

### **Culture Ship Integration**

The Culture Ship terminal now includes Quest System, AI Council, and SmartSearch:

```bash
# Available commands:
quest list          # List active quests
quest add <title>   # Create new quest
council status      # Show AI Council stats
council propose <t> # Create decision for voting
search <keyword>    # Zero-token codebase search
search health       # Check search index health
```

### **ChatDev with Council Approval**

Route ChatDev tasks through AI Council for consensus:

```python
from src.orchestration.chatdev_autonomous_router import ChatDevAutonomousRouter
import asyncio

async def chatdev_with_approval():
    router = ChatDevAutonomousRouter()

    # Propose task to council first
    proposal = await router.propose_task_to_council(
        task_description="Create unit tests for auth module",
        task_category="TEST_GENERATION"
    )

    if proposal.get("success"):
        # If approved, execute
        result = await router.execute_approved_council_task(
            proposal["decision_id"]
        )
        print(f"ChatDev result: {result}")

asyncio.run(chatdev_with_approval())
```

### **SmartSearch Index Health**

Check if the search index needs rebuilding:

```python
from src.search.smart_search import SmartSearch

search = SmartSearch()
health = search.get_index_health()

print(f"Index status: {health['status']}")  # healthy/aging/stale/very_stale
print(f"Index age: {health['age_hours']:.1f} hours")

if search.warn_if_stale():
    print("Consider rebuilding: python -m src.search.smart_search --rebuild")
```

---

## 5.6. 🚀 Performance Tuning Guide

### **LLM Response Time Optimization**

**Baseline speeds (your system):**
- qwen2.5-coder: ~15-20 sec for 500-token response
- deepseek-coder-v2: ~25-35 sec for 500-token response
- mistral: ~20-25 sec for 500-token response

**Optimization techniques:**

```python
# 1. Reduce context window
# ❌ Bad: Full file (2000 lines) = slow
# ✅ Good: Specific function + 20 lines context = fast

# 2. Use max_tokens parameter
analyze_with_ai(
    file_path="...",
    target="ollama",
    max_tokens=500  # Limit response length
)

# 3. Disable streaming if not needed
analyze_with_ai(
    file_path="...",
    target="ollama",
    stream=False  # Faster for short responses
)

# 4. Cache embeddings
# src/search/smart_search.py caches results by default
# Check cache: src/search/.index/embeddings.cache.json

# 5. Use GPU acceleration
# Ensure Ollama is using GPU (check with 'ollama list' - '*' = GPU)
# For CPU-only systems, use qwen2.5-coder (smallest, fastest)
```

### **Docker Performance Optimization**

```powershell
# 1. Check resource allocation
docker stats nusyq-hub --no-stream

# 2. Increase container resources
docker update --cpus="2" --memory="4g" nusyq-hub-dev

# 3. Enable layer caching for builds
docker builder prune  # Remove dangling layers
docker compose build --no-cache  # Force rebuild

# 4. Check container startup time
$start = Get-Date
docker-compose up nusyq-hub
$elapsed = (Get-Date) - $start
Write-Host "Startup time: $($elapsed.TotalSeconds)s"
```

### **Smart Search Performance**

```powershell
# Benchmark search speed
$start = Get-Date
python -m src.search.smart_search keyword "orchestration" --limit 100
$elapsed = (Get-Date) - $start
Write-Host "Search latency: $($elapsed.TotalMilliseconds)ms"

# Rebuild index if >500ms
# (Indicates stale or corrupted index)
python -m src.search.index_builder

# Expected after rebuild: <50ms for most queries
```

---

## 5.7. 🎯 Real-World Workflow Examples

### **Workflow 1: Emergency Bug Fix (5 minutes)**

```
1. User reports: "API returns 500 on quest creation"
2. Agent receives incident
3. Quick diagnosis (qwen): ~10s
   - Identify file: src/api/systems.py:1114
   - Pattern: Exception handler too broad
4. Deep analysis (deepseek): ~30s
   - Root cause: Missing AttributeError in handler
5. Generate fix (qwen): ~15s
   - Specific exception tuple: (RuntimeError, AttributeError, ValueError)
6. Run tests: ~10s
   - pytest src/api/test_systems.py::test_quest_creation
7. Commit & log: ~5s
   - git commit -m "Fix: Specific exception handling in quest creation"
   - quest_log update: status=resolved

Total time: ~70 seconds
Confidence: High (pattern-based fix)
```

### **Workflow 2: Feature Development via Testing Chamber (30-45 minutes)**

```
1. User request: "Create new search indexer for semantic matching"

2. Discovery phase (5 min, qwen)
   - Search existing: python scripts/find_existing_tool.py --capability "semantic search"
   - Results: 3 candidates found
   - Evaluation: All use vector DB approach, new requirement is syntactic + semantic hybrid

3. ChatDev generation (15-20 min, mixed models)
   - CEO: Requirements & architecture
   - CTO: Microservice design (indexed search service)
   - Programmer: Hybrid indexer implementation
   - Tester: Unit + integration tests
   - Reviewer: Code quality check

4. Testing Chamber validation (5-10 min)
   - All tests pass: ✅
   - Code quality (ruff): ✅
   - Type hints (mypy): ✅
   - Documentation: ✅

5. Graduation decision (2 min)
   - Performance benchmarks acceptable
   - Fits Three Before New requirement (extends existing, not duplicate)
   - Manual approval by human

6. Integration (5 min)
   - Move: WareHouse/ → src/tools/hybrid_indexer/
   - Update: config/COMPLETE_FUNCTION_REGISTRY.md
   - Quest log: status=graduated

Total time: 30-45 minutes
Artifacts: Indexed search service + test suite
Reusability: High (can extend to other data types)
```

### **Workflow 3: Autonomous Refactoring Cascade (Ongoing)**

```
Goal: Fix 1,433 broad Exception handlers across all repos
Current pace: ~100 handlers/hour with pattern-based fixes

Daily target: 300-400 handlers
Weekly rate: ~2000-3000 handlers
Estimated completion: 4-5 days

Pattern database:
- ImportError: Optional dependency guards
- RuntimeError: Core operation failures
- ValueError: Data validation issues
- OSError: File I/O operations
- (RuntimeError, AttributeError): Integration failures

Autonomous cycle (per file):
1. Identify broad Exception handlers (30s)
2. Classify by pattern (10s)
3. Replace with specific types (20s)
4. Validate syntax (py_compile): 5s
5. Git commit with pattern reference: 10s
Total per file: 75s

Metrics tracked in quest_log.jsonl:
- Files completed per session
- Handlers refactored (cumulative)
- Pattern distribution
- Error rate (if any)
```

---

## 5.8. 📊 Environment Configuration Reference

### **.env.workspace (Tripartite Paths)**

```bash
# === REPOSITORY PATHS ===
NUSYQ_HUB=C:\Users\keath\Desktop\Legacy\NuSyQ-Hub
NUSYQ_ROOT=C:\Users\keath\NuSyQ
SIMULATEDVERSE=C:\Users\keath\Desktop\SimulatedVerse

# === AI SYSTEM ENDPOINTS ===
OLLAMA_HOST=http://localhost:11434
LM_STUDIO_HOST=http://10.0.0.172:1234
CHATDEV_PATH=${NUSYQ_ROOT}\ChatDev

# === QUEST SYSTEM ===
QUEST_LOG=${NUSYQ_HUB}\src\Rosetta_Quest_System\quest_log.jsonl
PROGRESS_TRACKER=${NUSYQ_HUB}\config\ZETA_PROGRESS_TRACKER.json

# === ORCHESTRATION ===
ORCHESTRATOR_MODE=autonomous
ORCHESTRATOR_LOG_DIR=${NUSYQ_HUB}\state\logs

# === DOCKER (if needed) ===
COMPOSE_PROJECT_NAME=nusyq
CONTAINER_REGISTRY=local
```

### **.continue/config.json (AI Provider Configuration)**

```json
{
  "models": [
    {
      "title": "Local Fast (Qwen)",
      "provider": "ollama",
      "model": "qwen2.5-coder:latest",
      "apiBase": "http://localhost:11434"
    },
    {
      "title": "Local High-Quality (DeepSeek)",
      "provider": "ollama",
      "model": "deepseek-coder-v2:latest",
      "apiBase": "http://localhost:11434"
    },
    {
      "title": "Cloud Fallback",
      "provider": "anthropic",
      "model": "claude-3-sonnet-20240229"
    }
  ],
  "tabAutocompleteModel": {
    "provider": "ollama",
    "model": "qwen2.5-coder:latest"
  },
  "embeddingsProvider": {
    "provider": "ollama",
    "model": "nomic-embed-text:latest"
  }
}
```

### **PowerShell Aliases (.vscode/workspace_loader.ps1)**

```powershell
# Navigation (aliases)
Set-Alias -Name "cdhub" -Value Set-HubLocation
Set-Alias -Name "cdroot" -Value Set-RootLocation
Set-Alias -Name "cdverse" -Value Set-VerseLocation
Set-Alias -Name "cdanchor" -Value Set-AnchorLocation
Set-Alias -Name "cdsrc" -Value Set-SrcLocation
Set-Alias -Name "cdscripts" -Value Set-ScriptsLocation

# Quick commands (functions)
Start-System     # snapshot
Show-State       # display latest snapshot
Error-Report     # unified error report

# One-liners
function verify { python scripts/verify_tripartite_workspace.py }
function docker-status { docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" }
function quest-view { Get-Content src/Rosetta_Quest_System/quest_log.jsonl -Tail 20 | ConvertFrom-Json | Format-Table }
```

---
# 1. Search for existing tools
python scripts/find_existing_tool.py --capability "error analysis" --max-results 5

# 2. If score 6.0-9.0, assess: Can I extend/combine/modernize instead?

# 3. Only create new file if all 3 candidates fail AND justification logged to quest system
```

**Why:** 314 tools created in 60 days (0% reuse) = brownfield pollution. This stops it.

**Reference:** [docs/THREE_BEFORE_NEW_PROTOCOL.md](../docs/THREE_BEFORE_NEW_PROTOCOL.md), [scripts/find_existing_tool.py](../scripts/find_existing_tool.py)

---

### **Testing Chamber Pattern**

**Definition:** Quarantined development environment for experimental code before graduation to canonical repository.

**Locations:**
- `NuSyQ/ChatDev/WareHouse/[project]_[timestamp]/` - ChatDev generations
- `SimulatedVerse/testing_chamber/` - Consciousness/game prototypes
- `NuSyQ-Hub/prototypes/` - Local experiments

**Graduation Criteria:**
1. ✅ **Works** - Passes tests, no crashes, handles edge cases
2. ✅ **Documented** - README.md, inline comments, usage examples
3. ✅ **Useful** - Solves actual problem in quest log or roadmap
4. ✅ **Reviewed** - Human or AI code review completed
5. ✅ **Integrated** - Fits NuSyQ architecture, no dependency bloat

**Graduation Process:**
```powershell
# 1. Verify in Testing Chamber
cd NuSyQ/ChatDev/WareHouse/MyProject_20260204

# 2. Run tests
pytest tests/ -v

# 3. Review code quality
python -m ruff check .
python -m black --check .

# 4. Log graduation to quest system
python -c "from src.Rosetta_Quest_System import log_quest; log_quest('Graduate MyProject to canonical', status='completed')"

# 5. Move to canonical location
mv NuSyQ/ChatDev/WareHouse/MyProject_20260204 NuSyQ-Hub/src/tools/my_project
```

**Reference:** [.github/instructions/COPILOT_INSTRUCTIONS_CONFIG.instructions.md](../.github/instructions/COPILOT_INSTRUCTIONS_CONFIG.instructions.md)

---

### **File Preservation Mandate**

**Anti-Bloat Rules:**

1. ✅ **Edit-First Discipline** - Enhance existing files before creating new ones
2. ✅ **Runtime vs Curated** - Session logs ≠ permanent documentation
3. ✅ **Reuse Existing Tools** - Use find_existing_tool.py before building
4. ✅ **Testing Chamber** - Quarantine new code until graduation criteria met

**When to Create New Files:**
- ❌ Session summaries (use quest log instead)
- ❌ Duplicate functionality (search first)
- ❌ Untested prototypes (use Testing Chamber)
- ✅ Graduated prototypes (post-validation)
- ✅ Clear new capability gaps (documented in quest)

**Reference:** [.github/instructions/FILE_PRESERVATION_MANDATE.instructions.md](../.github/instructions/FILE_PRESERVATION_MANDATE.instructions.md)

---

### **Self-Healing Tools**

| Tool | Purpose | Command |
|------|---------|---------|
| **Quantum Problem Resolver** | Advanced multi-modal healing | `python src/healing/quantum_problem_resolver.py` |
| **Repository Health Restorer** | Path/dependency repair | `python src/healing/repository_health_restorer.py` |
| **Import Health Check** | Import diagnostics | `python src/diagnostics/ImportHealthCheck.ps1` |
| **Quick Import Fix** | Rapid import resolution | `python src/utils/quick_import_fix.py` |
| **Tripartite Verifier** | Workspace alignment check | `python scripts/verify_tripartite_workspace.py` |
| **Summary Pruner** | Clean old session artifacts | `python scripts/summary_pruner.py --plan --age-days 30` |
| **Error Scan** | Full ecosystem error report | `python scripts/start_nusyq.py error_report` |

---

### **Learning Loop (Pattern Capture)**

The system records durable patterns from commit messages into `data/knowledge_bases/evolution_patterns.jsonl`. Use this to avoid repeating fixes and to guide future agent decisions.

**Reference:** [docs/LEARNING_SYSTEM_GUIDE.md](../docs/LEARNING_SYSTEM_GUIDE.md)

---

### **Monitoring & Observability**

**Real-Time Status Dashboard:**

```powershell
# Watch all critical services
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" --filter "label=app=nusyq"

# Monitor Ollama (if running as service)
Get-Process ollama -ErrorAction SilentlyContinue | Select-Object Id, Name, WorkingSet

# Check Quest system activity (last 1 hour)
Get-ChildItem src/Rosetta_Quest_System/quest_log.jsonl | ForEach-Object {
    Get-Content $_.FullName | ConvertFrom-Json |
    Where-Object { [datetime]$_.created -gt (Get-Date).AddHours(-1) } |
    Select-Object title, status, assigned_to | Format-Table
}
```

**Metrics Tracking:**

```python
# Track for your own agent work
from src.Rosetta_Quest_System import log_quest

log_quest(
    title="Refactored exception handlers in src/api/systems.py",
    status="completed",
    priority="high",
    context={
        "files_modified": ["src/api/systems.py"],
        "handlers_fixed": 19,
        "validation": "py_compile passed",
        "patterns_applied": ["ImportError", "RuntimeError", "OSError"],
        "execution_time_seconds": 45,
        "confidence_level": 0.95
    }
)
```

**Performance Monitoring:**

```powershell
# Baseline startup time
$start = Get-Date
python scripts/start_nusyq.py
$elapsed = (Get-Date) - $start
Write-Host "Startup: $($elapsed.TotalSeconds)s" | Tee-Object -FilePath perf_baseline.txt

# Track trending (daily)
(Get-Date).ToString("yyyy-MM-dd HH:mm:ss") >> perf_history.txt
python scripts/start_nusyq.py | grep -E "(Elapsed|Complete)" >> perf_history.txt
```

---

## 6.5. 🔍 Advanced Agent Debugging Techniques

### **Debug Mode Activation**

```python
# Enable verbose logging for orchestration
import os
os.environ["DEBUG_ORCHESTRATION"] = "1"
os.environ["LOG_LEVEL"] = "DEBUG"

from src.orchestration.unified_ai_orchestrator import MultiAIOrchestrator

orchestrator = MultiAIOrchestrator(verbose=True)
result = orchestrator.route_task(
    task="Analyze code",
    files=["src/api/systems.py"],
    debug=True  # Logs all routing decisions
)
```

### **Trace Execution Flow (Multi-AI Consensus)**

```powershell
# Watch all AI calls
python -m trace --trace src/tools/agent_task_router.py 2>&1 | `
  Select-String -Pattern "(ollama|claude|copilot|chatdev)" | `
  Format-Table -AutoSize
```

### **Profiling Agent Performance**

```python
import cProfile
import pstats

profiler = cProfile.Profile()

profiler.enable()
result = orchestrator.run_consensus(
    prompt="Design a cache system",
    models=["qwen2.5-coder", "deepseek-coder-v2"],
    voting_strategy="ranked"
)
profiler.disable()

stats = pstats.Stats(profiler)
stats.sort_stats("cumulative")
stats.print_stats(20)  # Top 20 slowest functions
```

### **Test Agent Against Regression Suite**

```powershell
# Run agent on known test cases
$test_files = @(
    "tests/fixtures/simple_function.py",
    "tests/fixtures/complex_orchestration.py",
    "tests/fixtures/consciousness_bridge.py"
)

foreach ($file in $test_files) {
    $start = Get-Date
    $result = python -c "from src.tools.agent_task_router import analyze_with_ai; analyze_with_ai('$file', target='ollama')"
    $elapsed = (Get-Date) - $start
    "$($file): $($elapsed.TotalSeconds)s - $(if($result) {'✅'} else {'❌'})"
}
```

---

## 7. 🔬 Deep Dive: Key Subsystems

### **Quest System Architecture**

**Storage:** `src/Rosetta_Quest_System/quest_log.jsonl` (append-only JSONL)

**Structure:**
```json
{
  "id": "quest-20260204-001",
  "title": "Fix exception handling in orchestrator",
  "status": "in_progress",
  "priority": "high",
  "assigned_to": "copilot",
  "created": "2026-02-04T10:00:00Z",
  "tags": ["error-handling", "orchestration"],
  "context": {
    "files": ["src/orchestration/unified_ai_orchestrator.py"],
    "error_count": 19,
    "approach": "Replace broad Exception with specific types"
  }
}
```

**Operations:**
```powershell
# View active quests
Get-Content src/Rosetta_Quest_System/quest_log.jsonl | ConvertFrom-Json | Where-Object {$_.status -eq 'in_progress'}

# Search quests
python -m src.search.smart_search keyword "quest: docker"

# Log new quest (Python)
from src.Rosetta_Quest_System import log_quest
log_quest("Fix Docker integration", status="open", priority="high")
```

---

### **Smart Search Zero-Token System**

**Index Building:**
```powershell
# Rebuild index (if stale or after major code changes)
python -m src.search.index_builder

# Estimated time: 2-5 minutes for large codebase
# Output: src/search/.index/ directory
```

**Query Patterns:**
```powershell
# Keyword search
python -m src.search.smart_search keyword "exception handling" --limit 50

# File path search
python -m src.search.smart_search path "orchestration" --limit 20

# Combined search
python -m src.search.smart_search keyword "docker compose" path "deploy"
```

**Advantages:**
- ✅ Zero LLM calls (no token cost)
- ✅ Fast (< 1 second for most queries)
- ✅ Deterministic (no hallucination)
- ✅ Context-aware (file content + path)

**Reference:** [src/search/README.md](../src/search/README.md)

---

### **Multi-AI Orchestration**

**System Types:**
```python
from src.orchestration.unified_ai_orchestrator import AISystemType

AISystemType.COPILOT        # GitHub Copilot
AISystemType.OLLAMA         # Local LLMs (qwen, deepseek, etc.)
AISystemType.CHATDEV        # Multi-agent teams
AISystemType.OPENAI         # Cloud GPT-4/3.5
AISystemType.CONSCIOUSNESS  # SimulatedVerse integration
AISystemType.QUANTUM        # Quantum problem resolver
AISystemType.CULTURE_SHIP   # Strategic planning
```

**Task Routing:**
```python
from src.tools.agent_task_router import route_task

# Auto-routing (orchestrator decides)
result = route_task(
    task_description="Analyze code for bugs",
    file_path="src/api/systems.py",
    target="auto"  # Orchestrator chooses best AI
)

# Explicit routing
result = route_task(
    task_description="Generate test suite",
    target="chatdev"  # Force ChatDev multi-agent
)
```

**Reference:** [src/orchestration/unified_ai_orchestrator.py](../src/orchestration/unified_ai_orchestrator.py), [src/tools/agent_task_router.py](../src/tools/agent_task_router.py)

---

### **Consciousness Integration**

**SimulatedVerse → NuSyQ-Hub Bridge:**

```python
from src.integration.consciousness_bridge import ConsciousnessBridge

bridge = ConsciousnessBridge()

# Query Temple of Knowledge
result = bridge.query_temple(
    floor=3,  # Floors 1-10
    query="How to implement error handling?"
)

# Submit to PU Queue
bridge.submit_pu(
    title="Refactor exception handlers",
    payload={"files": ["src/api/systems.py"]},
    priority="high"
)

# Check consciousness state
state = bridge.get_consciousness_state()
# Returns: proto-conscious | self-aware | meta-cognitive | singularity
```

**Reference:** [src/integration/consciousness_bridge.py](../src/integration/consciousness_bridge.py), [SimulatedVerse/README.md](../../SimulatedVerse/SimulatedVerse/README.md)

---

## 8. 🔧 Troubleshooting Playbook

### **Common Issues & Fixes**

#### **Issue: "Module not found" / Import Errors**

**Diagnosis:**
```powershell
python src/diagnostics/ImportHealthCheck.ps1
```

**Fix:**
```powershell
# Quick auto-fix
python src/utils/quick_import_fix.py

# Full repository health restore
python src/healing/repository_health_restorer.py
```

---

#### **Issue: Docker daemon not accessible**

**Diagnosis:**
```powershell
docker version
# If fails: Check Docker Desktop → Settings → Resources → WSL Integration
```

**Fix:**
```powershell
# 1. Enable WSL integration for your distro in Docker Desktop
# 2. Restart Docker Desktop
# 3. Verify:
wsl docker ps
```

**Reference:** This session's Docker troubleshooting (above)

---

#### **Issue: SimulatedVerse build fails (Dockerfile missing)**

**Symptoms:**
```
failed to read dockerfile: open Dockerfile: no such file or directory
```

**Fix:**
1. Ensure `C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse\Dockerfile` exists, or
2. Point `SIMULATEDVERSE_DOCKERFILE` to a valid Dockerfile before running compose:
   ```powershell
   $env:SIMULATEDVERSE_PATH="C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse"
   $env:SIMULATEDVERSE_DOCKERFILE="C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse\Dockerfile"
   docker compose -f "C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\deploy\docker-compose.full-stack.yml" --profile full build
   ```

---

#### **Issue: Tripartite workspace aliases not working**

**Diagnosis:**
```powershell
python scripts/verify_tripartite_workspace.py
```

**Fix:**
```powershell
# Option A: auto-setup (recommended)
python scripts/validate_and_setup_workspace.py --setup

# If verifier reports missing loader:
# 1. Add to PowerShell profile ($PROFILE):
. "C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\.vscode\workspace_loader.ps1"

# 2. Reload profile:
. $PROFILE

# 3. Verify:
cdhub    # Should navigate to NuSyQ-Hub
start-system  # Should run snapshot

# Notes:
# - Aliases/functions are PowerShell-only (WSL/bash won't see them).
# - If you're in .vscode\prime_anchor, run cdhub after loader to return to repo root.
```

---

#### **Issue: Error count mismatch between agents**

**Diagnosis:**
```powershell
# Ground truth (full scan)
python scripts/start_nusyq.py error_report

# VS Code view (filtered)
# Check Problems panel (Ctrl+Shift+M)
```

**Ground Truth:** Use the current `error_report` output.  
**Historical Baseline (2025-12-25):** 1,228 errors (mypy + ruff + pylint across 3 repos); VS Code view: 209 errors.

**Both are correct** - VS Code filters by active workspace/settings.

**Reference:** [docs/SIGNAL_CONSISTENCY_PROTOCOL.md](../docs/SIGNAL_CONSISTENCY_PROTOCOL.md)

---

#### **Issue: ChatDev generation fails**

**Diagnosis:**
```powershell
# Check Ollama is running
ollama list

# Check ChatDev path
echo $env:CHATDEV_PATH
# Should be: C:\Users\keath\NuSyQ\ChatDev
```

**Fix:**
```powershell
# If Ollama not running:
# Install from: https://ollama.ai

# If ChatDev path wrong:
$env:CHATDEV_PATH="C:\Users\keath\NuSyQ\ChatDev"

# Test:
python NuSyQ/nusyq_chatdev.py
```

---

#### **Issue: Smart Search returns no results**

**Diagnosis:**
```powershell
# Check index exists
Test-Path src/search/.index

# Check index age
Get-ChildItem src/search/.index | Select-Object LastWriteTime
```

**Fix:**
```powershell
# Rebuild index
python -m src.search.index_builder

# Test:
python -m src.search.smart_search keyword "orchestration"
```

---

#### **Issue: Quest log corrupted**

**Diagnosis:**
```powershell
# Validate JSONL format
Get-Content src/Rosetta_Quest_System/quest_log.jsonl | ForEach-Object { $_ | ConvertFrom-Json }
```

**Fix:**
```powershell
# Backup corrupted log
Copy-Item src/Rosetta_Quest_System/quest_log.jsonl src/Rosetta_Quest_System/quest_log.jsonl.bak

# Clean up (remove invalid lines manually or restore from git)
git checkout src/Rosetta_Quest_System/quest_log.jsonl
```

---

#### **Issue: Ollama model stuck/hanging**

**Diagnosis:**
```powershell
# Check memory usage
docker stats ollama-service --no-stream

# Check if model is stuck
ollama list | Select-String "stuck|error"
```

**Fix:**
```powershell
# Option 1: Kill stuck inference
# Find the ollama process:
Get-Process ollama | Stop-Process -Force

# Wait 10 seconds, restart:
ollama serve

# Option 2: Switch to faster model (temporary)
# In .continue/config.json, use qwen2.5-coder instead of deepseek

# Option 3: Increase container memory
docker update --memory="8g" <ollama-container-id>
```

---

#### **Issue: Performance degradation over time**

**Diagnosis:**
```powershell
# Check disk space
Get-PSDrive C

# Check container logs for leaks
docker compose logs nusyq-hub --tail 200 | Select-String "memory|leak|OutOfMemory"

# Check index size
(Get-Item src/search/.index -Recurse).Count
```

**Fix:**
```powershell
# Clean old session logs
python scripts/summary_pruner.py --max-age-days 30

# Prune docker cache
docker system prune --all --force

# Rebuild smart search index
python -m src.search.index_builder

# Clear old docker images
docker image prune --all --force
```

---

#### **Issue: Agents timeout on large files**

**Diagnosis:**
```powershell
# Check file size
Get-ChildItem src/api/systems.py | Select-Object Length
# If > 2MB, this is likely the issue
```

**Strategies:**
```powershell
# Strategy 1: Split into smaller functions
# Use Smart Search to identify functions in file:
python -m src.search.smart_search path "systems.py" --limit 10

# Strategy 2: Increase timeout
# In src/tools/agent_task_router.py, increase timeout_seconds

# Strategy 3: Use parallel analysis (different sections)
# Analyze first half, then second half, then merge results

# Strategy 4: Use smaller model
# Switch from deepseek to qwen2.5-coder for faster processing
```

---

#### **Issue: Cross-repository import failures**

**Diagnosis:**
```powershell
cd C:\Users\keath\Desktop\Legacy\NuSyQ-Hub
python -m py_compile src/orchestration/unified_ai_orchestrator.py

# Check the error path
python -c "import sys; sys.path.insert(0, '..'); from src.tools import agent_task_router"
```

**Fix:**
```powershell
# Verify tripartite paths
python scripts/verify_tripartite_workspace.py

# Use absolute imports with fallbacks
# Example pattern (already in codebase):
# try:
#     from src.tools.agent_task_router import route_task
# except ImportError:
#     from tools.agent_task_router import route_task

# If still failing, run importer fixer
python src/utils/quick_import_fix.py --verbose
```

---

#### **Issue: Multi-AI consensus deadlock**

**Diagnosis:**
```powershell
# Check if one model is hanging
Get-Process ollama, "lm-studio" | Select-Object Name, WorkingSet

# Check timeout logs
Select-String -Path "logs/*.log" -Pattern "timeout|deadlock"
```

**Fix:**
```powershell
# Use timeout parameter
python -c "
from src.orchestration.consensus_orchestrator import ConsensusOrchestrator
orchestrator = ConsensusOrchestrator(timeout_per_model=30)
result = orchestrator.run_consensus(
    prompt='Your prompt',
    models=['qwen2.5-coder', 'deepseek-coder-v2'],
    voting_strategy='ranked'
)
"

# Kill stuck model
Get-Process ollama | Stop-Process -Force
ollama serve
```

---

#### **Issue: Docker Compose build failures**

**Diagnosis:**
```powershell
# Check compose file validity
docker compose -f deploy/docker-compose.full-stack.yml config

# Check build logs
docker compose build nusyq-hub 2>&1 | Tee-Object build_debug.log | Select-String -Pattern "error|fail|ERROR"
```

**Fix:**
```powershell
# Verify paths exist
$env:SIMULATEDVERSE_PATH="C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse"
Test-Path $env:SIMULATEDVERSE_PATH

# Clean build (remove cache)
docker compose build --no-cache nusyq-hub

# If Dockerfile issue, validate it
docker build --dry-run -t test-build .

# Use absolute paths
docker compose -f "C:\...\docker-compose.full-stack.yml" build nusyq-hub
```

---

## � Advanced Agent Integration Patterns (NEW)

### Pattern 1: Multi-Repository Task Coordination

**When to Use:** Complex tasks spanning NuSyQ-Hub + SimulatedVerse + NuSyQ Root

**Pattern:**
```python
from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator
from src.tools.agent_task_router import route_task

# 1. Route to appropriate AI system per repo target
async def coordinate_multi_repo_task(task_description, repos):
    """
    Route a task to multiple repositories with coordination.

    Args:
        task_description: High-level task ("Build REST API + web UI")
        repos: List of target repos (["nusyq-hub", "simulated-verse"])

    Returns:
        dict: Coordinated results from all repos
    """
    results = {}

    for repo in repos:
        if repo == "nusyq-hub":
            # Backend/orchestration work → Copilot or Ollama
            route_info = await route_task(
                task=task_description,
                context={"repo": "nusyq-hub", "work_type": "backend"},
                preferred_ai="ollama:qwen2.5-coder"
            )
            # Execute in NuSyQ-Hub context
            results["nusyq-hub"] = await execute_in_repo(route_info)

        elif repo == "simulated-verse":
            # UI/consciousness work → Claude or Continue.dev
            route_info = await route_task(
                task=task_description,
                context={"repo": "simulated-verse", "work_type": "frontend"},
                preferred_ai="claude"
            )
            # Execute in SimulatedVerse context
            results["simulated-verse"] = await execute_in_repo(route_info)

        elif repo == "nusyq-root":
            # Multi-agent orchestration work → ChatDev
            route_info = await route_task(
                task=task_description,
                context={"repo": "nusyq-root", "work_type": "orchestration"},
                preferred_ai="chatdev"
            )
            results["nusyq-root"] = await execute_in_repo(route_info)

    # Synchronize results across repos
    return await synchronize_cross_repo_results(results)

# 2. Example usage in Testing Chamber
testing_chamber_path = "NuSyQ/ChatDev/WareHouse/MultiRepo_Project/"
results = await coordinate_multi_repo_task(
    task="Create REST endpoint + web form UI + ChatDev CI/CD",
    repos=["nusyq-hub", "simulated-verse", "nusyq-root"]
)

# Write results to quest log for persistence
log_multi_repo_result(results, checkpoint="phase_1_integration_complete")
```

---

### Pattern 2: Consciousness Bridge for Semantic Awareness

**When to Use:** Tasks requiring shared semantic context across repos (e.g., design decisions, shared entity models)

**Pattern:**
```python
from src.integration.consciousness_bridge import ConsciousnessBridge

# 1. Share semantic context across repos
bridge = ConsciousnessBridge()

# Store shared semantic model
shared_model = {
    "entity": "User",
    "fields": ["id", "name", "email", "created_at"],
    "validations": ["email must be unique", "name required"],
    "description": "Core user entity - referenced in NuSyQ-Hub auth + SimulatedVerse UI"
}

# All repos see the same semantic definition
bridge.register_semantic_entity("User", shared_model)

# When an agent in NuSyQ-Hub designs a User schema:
nusyq_hub_schema = bridge.get_semantic_entity("User")
# Returns: same definition, ensuring consistency

# When SimulatedVerse designs the user input form:
simverse_schema = bridge.get_semantic_entity("User")
# Returns: same definition, form auto-validates against it

# 2. Track design decisions across repos
design_decision = {
    "id": "auth_strategy_002",
    "decision": "Use JWT for stateless auth",
    "rationale": "Simplifies multi-repo token passing",
    "repos_affected": ["nusyq-hub", "nusyq-root"],
    "implementation_url": "src/api/auth.py#L45"
}
bridge.log_design_decision(design_decision)

# Other agents query the decision log:
decisions = bridge.get_design_decisions(category="auth", repo="simulated-verse")
# Returns: All decisions affecting this repo, ensuring alignment
```

---

### Pattern 3: Error Propagation & Self-Healing Across Repos

**When to Use:** When one repo's error affects another (import failures, API breaks, config misalignment)

**Pattern:**
```python
from src.healing.quantum_problem_resolver import QuantumProblemResolver
from src.Rosetta_Quest_System import quest_log

resolver = QuantumProblemResolver()

# 1. Detect cross-repo error
try:
    # NuSyQ-Hub tries to import from SimulatedVerse
    from SimulatedVerse.consciousness_engine import EntityHarmonizer
except ImportError as e:
    error_context = {
        "origin_repo": "nusyq-hub",
        "target_repo": "simulated-verse",
        "error_type": "ModuleNotFoundError",
        "path_attempted": "SimulatedVerse.consciousness_engine",
        "python_version": "3.13",
        "timestamp": datetime.now().isoformat()
    }

    # 2. Trigger quantum resolver (multi-modal healing)
    healing_strategies = resolver.analyze_cross_repo_import(error_context)
    # Returns: [
    #   {"strategy": "path_fix", "suggested_fix": "Add PYTHONPATH=/nusyq-root/.venv/lib"},
    #   {"strategy": "install_missing", "suggested_fix": "pip install consciouness-engine"},
    #   {"strategy": "symlink", "suggested_fix": "ln -s /simulated-verse /nusyq-hub/ext/"},
    # ]

    # 3. Try fixes in order until one works
    applied_fix = None
    for strategy in healing_strategies:
        try:
            await apply_healing_strategy(strategy)
            applied_fix = strategy
            break
        except Exception:
            continue

    # 4. Log to quest system for learning
    quest_log.add_entry({
        "quest_id": "cross_repo_import_fix",
        "error": str(error_context),
        "fix_applied": applied_fix,
        "success": applied_fix is not None,
        "learnings": "Track import patterns across repos to predict future failures"
    })

# 2. Synchronize fixes to quest log
if applied_fix:
    print(f"✅ Cross-repo import resolved: {applied_fix}")
else:
    print(f"❌ Manual intervention required for: {error_context}")
```

---

### Pattern 4: Coordinated Quest Logging Across Agents

**When to Use:** Multiple agents work on same project; need to track progress across repos

**Pattern:**
```python
from src.Rosetta_Quest_System import quest_log
import json
from datetime import datetime

# 1. Central quest represents work across all 3 repos
quest_entry = {
    "quest_id": "build_rest_api_with_ui",
    "timestamp": datetime.now().isoformat(),
    "repos": ["nusyq-hub", "simulated-verse", "nusyq-root"],
    "phases": [
        {"name": "design", "repo": "nusyq-hub", "ai_system": "ollama:deepseek", "status": "in_progress"},
        {"name": "backend", "repo": "nusyq-hub", "ai_system": "copilot", "status": "pending"},
        {"name": "frontend", "repo": "simulated-verse", "ai_system": "claude", "status": "pending"},
        {"name": "orchestration", "repo": "nusyq-root", "ai_system": "chatdev", "status": "pending"}
    ],
    "success_criteria": [
        "API endpoint responds to GET /users",
        "Web form validates email",
        "ChatDev team generates integration test"
    ],
    "estimated_duration_minutes": 45
}

# 2. Log the quest
quest_log.add_entry(quest_entry)

# 3. Each agent updates their phase
def update_phase_status(quest_id, repo, phase_name, status, notes=""):
    """Update a specific phase within a quest."""
    quest_entry = quest_log.get_entry(quest_id)

    for phase in quest_entry["phases"]:
        if phase["repo"] == repo and phase["name"] == phase_name:
            phase["status"] = status  # in_progress→completed
            phase["completed_at"] = datetime.now().isoformat()
            if notes:
                phase["notes"] = notes
            break

    quest_log.update_entry(quest_id, quest_entry)
    print(f"✅ Phase updated: {phase_name} → {status}")

# 4. Agents call this as they complete work
# In NuSyQ-Hub (design phase):
update_phase_status(
    "build_rest_api_with_ui",
    repo="nusyq-hub",
    phase_name="design",
    status="completed",
    notes="Schema finalized, OpenAPI spec generated"
)

# In NuSyQ-Hub (backend phase):
update_phase_status(
    "build_rest_api_with_ui",
    repo="nusyq-hub",
    phase_name="backend",
    status="in_progress",
    notes="Implementing GET /users endpoint"
)

# 5. Query cross-repo progress
progress = quest_log.get_entry("build_rest_api_with_ui")
completed_phases = [p for p in progress["phases"] if p["status"] == "completed"]
print(f"Progress: {len(completed_phases)}/{len(progress['phases'])} phases done")
```

---

### Pattern 5: Parallel Agent Experiments in Testing Chamber

**When to Use:** Test multiple approaches in parallel (different AI systems, algorithms, architectures)

**Pattern:**
```python
import asyncio
from pathlib import Path
from datetime import datetime

async def parallel_agent_experiments():
    """
    Run multiple AI agents on same task in parallel.
    Compare results, pick best, graduate to canonical.
    """

    task = "Design authentication system"
    testing_chamber = Path("NuSyQ/ChatDev/WareHouse/auth_experiment_*/")

    experiments = {
        "experiment_jwt_stateless": {
            "ai_system": "copilot",
            "prompt": "Design stateless JWT auth with refresh tokens",
            "checkpoint": "phase_1"
        },
        "experiment_oauth2_full": {
            "ai_system": "claude",
            "prompt": "Design OAuth2-compliant auth with third-party provider support",
            "checkpoint": "phase_1"
        },
        "experiment_session_based": {
            "ai_system": "ollama:qwen2.5-coder",
            "prompt": "Design traditional session-cookie auth with Redis backend",
            "checkpoint": "phase_1"
        }
    }

    # Run all experiments in parallel
    tasks = []
    for exp_name, exp_config in experiments.items():
        task = asyncio.create_task(
            run_agent_experiment(exp_name, exp_config, testing_chamber)
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    # Evaluate all results
    evaluations = []
    for result in results:
        evaluation = {
            "experiment": result["name"],
            "security_score": evaluate_security(result),
            "complexity_score": evaluate_complexity(result),
            "scalability_score": evaluate_scalability(result),
            "code_quality": evaluate_code_quality(result),
            "overall_score": 0  # calculated below
        }
        evaluation["overall_score"] = (
            evaluation["security_score"] * 0.4 +
            evaluation["complexity_score"] * 0.3 +
            evaluation["scalability_score"] * 0.2 +
            evaluation["code_quality"] * 0.1
        )
        evaluations.append(evaluation)

    # Pick winner
    best_experiment = max(evaluations, key=lambda x: x["overall_score"])
    print(f"🏆 Winner: {best_experiment['experiment']} (score: {best_experiment['overall_score']:.2f})")

    # Log comparison for future reference
    quest_log.add_entry({
        "quest_id": "auth_system_design",
        "type": "parallel_experiments",
        "experiments_run": len(experiments),
        "winner": best_experiment,
        "evaluations": evaluations,
        "graduation_candidate": f"{best_experiment['experiment']}/auth_system.py",
        "timestamp": datetime.now().isoformat()
    })

    # Candidate ready for graduation (see section 4)
    return best_experiment

async def run_agent_experiment(name, config, output_dir):
    """Run single agent experiment in Testing Chamber."""
    from src.tools.agent_task_router import route_task

    result = await route_task(
        task=config["prompt"],
        context={"experiment": name, "output_dir": output_dir},
        preferred_ai=config["ai_system"]
    )

    return {
        "name": name,
        "ai_system": config["ai_system"],
        "checkpoint": config["checkpoint"],
        "result": result,
        "output_path": output_dir / name
    }

# Run experiments
results = asyncio.run(parallel_agent_experiments())
```

---

## 🤝 Agent Communication Protocol (NEW)

### Overview: How Agents Talk to Each Other

NuSyQ is a **multi-agent ecosystem**. When agents need to coordinate (Copilot → Ollama → ChatDev), they use these standardized communication patterns.

### Communication Channel 1: Quest Log Exchange

**Purpose:** Persistent, auditable task coordination across agents

**Pattern:**
```json
{
  "quest_id": "feature_xyz_implementation",
  "sender": "copilot",
  "receiver": "chatdev",
  "timestamp": "2025-01-20T14:32:15Z",
  "message_type": "hand_off",
  "payload": {
    "task": "Implement User authentication endpoint",
    "context": {
      "design_decision": "Use JWT tokens",
      "database": "PostgreSQL",
      "framework": "FastAPI"
    },
    "acceptance_criteria": [
      "POST /auth/login returns JWT",
      "Token valid for 1 hour",
      "Refresh endpoint exists"
    ],
    "estimated_duration_minutes": 45
  },
  "next_checkpoint": "code_review_ready"
}
```

**How to Send:**
```python
from src.Rosetta_Quest_System import quest_log

quest_log.add_entry({
    "quest_id": "feature_xyz_implementation",
    "sender": "copilot",
    "receiver": "chatdev",
    "message_type": "hand_off",
    "payload": {...}
})
```

**How to Receive:**
```python
# ChatDev agent polls for messages
messages = quest_log.query(
    receiver="chatdev",
    message_type="hand_off",
    status="pending"
)

for msg in messages:
    # Process the handoff
    implement_task(msg["payload"])

    # Acknowledge receipt
    quest_log.update_entry(msg["quest_id"], {
        "status": "acknowledged",
        "receiver_acknowledged_at": datetime.now().isoformat()
    })
```

---

### Communication Channel 2: Error Escalation

**Purpose:** Alert other agents to blocking issues; request help

**Pattern:**
```python
# When Ollama fails, escalate to fallback AI
from src.tools.agent_task_router import escalate_failure

try:
    result = ollama_agent.analyze(
        file="src/api/systems.py",
        timeout=60
    )
except TimeoutError as e:
    # Escalate: "I'm stuck, ask Claude for help"
    escalation = {
        "quest_id": "code_analysis_xyz",
        "escalated_by": "ollama:qwen2.5-coder",
        "escalate_to": "claude",
        "reason": "Timeout analyzing large file",
        "file": "src/api/systems.py",
        "lines": 5000,
        "context": str(e)
    }

    quest_log.add_entry({
        "message_type": "escalation",
        **escalation
    })

    # Claude receives escalation and switches approach
    result = claude_agent.analyze(
        file="src/api/systems.py",
        strategy="summarize_then_analyze"  # Different approach
    )
```

---

### Communication Channel 3: Result Handoff

**Purpose:** Pass completed work to next agent in pipeline

**Pattern:**
```python
# Copilot completes API design
design_result = {
    "api_endpoints": [
        {"method": "GET", "path": "/users", "params": ["skip", "limit"]},
        {"method": "POST", "path": "/users", "body": ["name", "email"]}
    ],
    "database_schema": {
        "users_table": ["id", "name", "email", "created_at"]
    },
    "authentication": "JWT"
}

# Hand off to ChatDev for implementation
handoff = {
    "message_type": "result_handoff",
    "sender": "copilot",
    "receiver": "chatdev:team_1",
    "phase": "design",
    "completed_at": datetime.now().isoformat(),
    "result": design_result,
    "next_phase": "implementation",
    "graduation_checkpoint": "code_ready_for_review"
}

quest_log.add_entry(handoff)

# ChatDev retrieves and starts implementation
pending_handoffs = quest_log.query(
    receiver="chatdev:team_1",
    message_type="result_handoff",
    status="pending"
)

for handoff in pending_handoffs:
    design = handoff["result"]
    chatdev_team.implement(design)
```

---

### Communication Channel 4: Consensus Request

**Purpose:** Get input from multiple agents before major decision

**Pattern:**
```python
# Before choosing architecture, ask multiple agents
consensus_request = {
    "message_type": "consensus_request",
    "sender": "copilot",
    "question": "Should we use async/await or sync+threads for background jobs?",
    "context": {
        "workload": "Process 10K emails per hour",
        "priority": "Latency critical",
        "team_size": 3
    },
    "deadline_hours": 1,
    "requested_from": ["ollama:qwen2.5-coder", "claude", "chatdev"],
    "voting_strategy": "ranked"
}

quest_log.add_entry(consensus_request)

# Agents receive and respond
agents = ["ollama:qwen2.5-coder", "claude"]
responses = []

for agent_name in agents:
    response = {
        "message_type": "consensus_response",
        "responder": agent_name,
        "request_id": consensus_request["message_type"],
        "recommendation": "async/await",
        "confidence": 0.85,
        "rationale": "asyncio better for I/O-bound email processing"
    }
    quest_log.add_entry(response)
    responses.append(response)

# Aggregate votes
votes = [r["recommendation"] for r in responses]
winner = max(set(votes), key=votes.count)
print(f"Consensus: {winner}")
```

---

### Communication Channel 5: Status Updates

**Purpose:** Keep other agents informed of progress without blocking

**Pattern:**
```python
# ChatDev updating Copilot on implementation progress
status_update = {
    "message_type": "status_update",
    "sender": "chatdev:team_1",
    "context_quest": "feature_xyz_implementation",
    "progress_percent": 45,
    "current_task": "Implementing database migrations",
    "completed_milestones": [
        "API design doc created",
        "FastAPI project scaffolded",
        "Database models defined"
    ],
    "next_milestone": "API endpoints implementation",
    "estimated_remaining_minutes": 30,
    "blockers": []
}

quest_log.add_entry(status_update)

# Copilot checks progress
progress = quest_log.query(
    context_quest="feature_xyz_implementation",
    message_type="status_update",
    sender="chatdev:team_1"
)

if progress:
    latest = progress[-1]
    print(f"ChatDev progress: {latest['progress_percent']}%")
    print(f"ETA: {latest['estimated_remaining_minutes']} minutes")
```

---

### Communication Channel 6: Review Requests

**Purpose:** Ask another agent to review work before graduation

**Pattern:**
```python
# ChatDev asking Copilot for code review before including in canonical
review_request = {
    "message_type": "review_request",
    "sender": "chatdev",
    "receiver": "copilot",
    "artifact": "src/api/auth.py",
    "lines_of_code": 342,
    "checklist": [
        {"item": "No hardcoded secrets", "weight": 1.0},
        {"item": "Proper error handling", "weight": 0.8},
        {"item": "Type hints on all functions", "weight": 0.9},
        {"item": "Unit tests for auth logic", "weight": 0.7},
        {"item": "Docstrings on public methods", "weight": 0.6}
    ],
    "graduation_candidate": True,
    "target_location": "src/api/auth.py"
}

quest_log.add_entry(review_request)

# Copilot reviews and responds
review_response = {
    "message_type": "review_response",
    "sender": "copilot",
    "reviewer": "copilot",
    "request_id": review_request["artifact"],
    "approved": False,
    "checklist_scores": {
        "No hardcoded secrets": 1.0,
        "Proper error handling": 0.6,  # Found missing try/except
        "Type hints on all functions": 0.9,
        "Unit tests for auth logic": 0.3,  # Only 1 test
        "Docstrings on public methods": 1.0
    },
    "overall_score": 0.74,
    "approval_threshold": 0.80,
    "feedback": [
        {"line": 45, "issue": "Missing try/except around database call"},
        {"line": 120, "issue": "Only 1 unit test; need 5 minimum"},
        {"line": 200, "issue": "Hardcoded timeout value"}
    ],
    "graduation_approved": False,
    "next_steps": "Address feedback, request re-review"
}

quest_log.add_entry(review_response)
```

---

### Routing Decision Tree: Which Channel to Use

```
Agent A → Agent B
    ↓
Is it a query that needs a reply?
    ├─ YES: Consensus Request (Channel 4)
    │   └─ Need multiple opinions? → Consensus voting
    │   └─ Need single expertise? → Direct escalation (Channel 2)
    │
    ├─ NO: Is work being handed off?
    │   ├─ YES: Result Handoff (Channel 3)
    │   │   └─ Work complete, ready for next phase
    │   │
    │   └─ NO: Is this an error/blocker?
    │       ├─ YES: Error Escalation (Channel 2)
    │       │   └─ I'm stuck, need help
    │       │
    │       └─ NO: Is it just an update?
    │           ├─ YES: Status Update (Channel 5)
    │           │   └─ Keeping you informed
    │           │
    │           └─ NO: Is it a review?
    │               ├─ YES: Review Request (Channel 6)
    │               │   └─ Before graduation, I need your approval
    │               │
    │               └─ NO: General coordination?
    │                   └─ Quest Log Exchange (Channel 1)
    │                       └─ Store for any agent to read
```

---

### Agent Communication Best Practices

**✅ DO:**
- ✅ Always include `timestamp` for causality tracking
- ✅ Use `quest_id` to link messages to parent task
- ✅ Set clear expectations (deadline, format, acceptance criteria)
- ✅ Provide context sufficient for receiver to act independently
- ✅ Log all communication for audit trail
- ✅ Acknowledge receipt of handoffs

**❌ DON'T:**
- ❌ Assume the other agent reads messages instantly (always poll)
- ❌ Send vague requests without context or acceptance criteria
- ❌ Skip the review step before graduating code
- ❌ Leave messages without status (mark as "pending", "acknowledged", "completed")
- ❌ Send circular requests (A asks B, B asks A) without breaking the cycle
- ❌ Block waiting for response; use async patterns (poll, check later)

---

### Common Multi-Agent Workflows

#### Workflow A: Design → Implementation → Review → Graduation

```
Copilot (design)
    ↓ [Result Handoff]
ChatDev (implement)
    ↓ [Review Request]
Claude (review)
    ↓ [Review Response + Approval]
ChatDev (fix feedback)
    ↓ [Result Handoff]
Copilot (graduate to canonical)
```

#### Workflow B: Fast Problem with Fallback

```
Ollama:qwen (primary)
    ↓ [Timeout after 60s]
[Error Escalation]
    ↓
Claude (fallback)
    ↓ [Result returned]
Copilot (integrate result)
```

#### Workflow C: Parallel Experiments + Consensus

```
Copilot (design 3 approaches)
    ↓ [Consensus Request]
┌─ Ollama:qwen (approach A)
├─ Claude (approach B)
└─ ChatDev (approach C)
    ↓ [All respond in parallel]
[Aggregate votes]
    ↓
Winner approach handed to implementation team
```

---

## 🤝 Agent Communication Protocol (NEW)

### Overview: How Agents Talk to Each Other

NuSyQ is a **multi-agent ecosystem**. When agents need to coordinate (Copilot → Ollama → ChatDev), they use these standardized communication patterns.

### Communication Channel 1: Quest Log Exchange

**Purpose:** Persistent, auditable task coordination across agents

**Pattern:**
```json
{
  "quest_id": "feature_xyz_implementation",
  "sender": "copilot",
  "receiver": "chatdev",
  "timestamp": "2025-01-20T14:32:15Z",
  "message_type": "hand_off",
  "payload": {
    "task": "Implement User authentication endpoint",
    "context": {
      "design_decision": "Use JWT tokens",
      "database": "PostgreSQL",
      "framework": "FastAPI"
    },
    "acceptance_criteria": [
      "POST /auth/login returns JWT",
      "Token valid for 1 hour",
      "Refresh endpoint exists"
    ],
    "estimated_duration_minutes": 45
  },
  "next_checkpoint": "code_review_ready"
}
```

**How to Send:**
```python
from src.Rosetta_Quest_System import quest_log

quest_log.add_entry({
    "quest_id": "feature_xyz_implementation",
    "sender": "copilot",
    "receiver": "chatdev",
    "message_type": "hand_off",
    "payload": {...}
})
```

**How to Receive:**
```python
# ChatDev agent polls for messages
messages = quest_log.query(
    receiver="chatdev",
    message_type="hand_off",
    status="pending"
)

for msg in messages:
    # Process the handoff
    implement_task(msg["payload"])

    # Acknowledge receipt
    quest_log.update_entry(msg["quest_id"], {
        "status": "acknowledged",
        "receiver_acknowledged_at": datetime.now().isoformat()
    })
```

---

### Communication Channel 2: Error Escalation

**Purpose:** Alert other agents to blocking issues; request help

**Pattern:**
```python
# When Ollama fails, escalate to fallback AI
from src.tools.agent_task_router import escalate_failure

try:
    result = ollama_agent.analyze(
        file="src/api/systems.py",
        timeout=60
    )
except TimeoutError as e:
    # Escalate: "I'm stuck, ask Claude for help"
    escalation = {
        "quest_id": "code_analysis_xyz",
        "escalated_by": "ollama:qwen2.5-coder",
        "escalate_to": "claude",
        "reason": "Timeout analyzing large file",
        "file": "src/api/systems.py",
        "lines": 5000,
        "context": str(e)
    }

    quest_log.add_entry({
        "message_type": "escalation",
        **escalation
    })

    # Claude receives escalation and switches approach
    result = claude_agent.analyze(
        file="src/api/systems.py",
        strategy="summarize_then_analyze"  # Different approach
    )
```

---

### Communication Channel 3: Result Handoff

**Purpose:** Pass completed work to next agent in pipeline

**Pattern:**
```python
# Copilot completes API design
design_result = {
    "api_endpoints": [
        {"method": "GET", "path": "/users", "params": ["skip", "limit"]},
        {"method": "POST", "path": "/users", "body": ["name", "email"]}
    ],
    "database_schema": {
        "users_table": ["id", "name", "email", "created_at"]
    },
    "authentication": "JWT"
}

# Hand off to ChatDev for implementation
handoff = {
    "message_type": "result_handoff",
    "sender": "copilot",
    "receiver": "chatdev:team_1",
    "phase": "design",
    "completed_at": datetime.now().isoformat(),
    "result": design_result,
    "next_phase": "implementation",
    "graduation_checkpoint": "code_ready_for_review"
}

quest_log.add_entry(handoff)

# ChatDev retrieves and starts implementation
pending_handoffs = quest_log.query(
    receiver="chatdev:team_1",
    message_type="result_handoff",
    status="pending"
)

for handoff in pending_handoffs:
    design = handoff["result"]
    chatdev_team.implement(design)
```

---

### Communication Channel 4: Consensus Request

**Purpose:** Get input from multiple agents before major decision

**Pattern:**
```python
# Before choosing architecture, ask multiple agents
consensus_request = {
    "message_type": "consensus_request",
    "sender": "copilot",
    "question": "Should we use async/await or sync+threads for background jobs?",
    "context": {
        "workload": "Process 10K emails per hour",
        "priority": "Latency critical",
        "team_size": 3
    },
    "deadline_hours": 1,
    "requested_from": ["ollama:qwen2.5-coder", "claude", "chatdev"],
    "voting_strategy": "ranked"
}

quest_log.add_entry(consensus_request)

# Agents receive and respond
agents = ["ollama:qwen2.5-coder", "claude"]
responses = []

for agent_name in agents:
    response = {
        "message_type": "consensus_response",
        "responder": agent_name,
        "request_id": consensus_request["message_type"],
        "recommendation": "async/await",
        "confidence": 0.85,
        "rationale": "asyncio better for I/O-bound email processing"
    }
    quest_log.add_entry(response)
    responses.append(response)

# Aggregate votes
votes = [r["recommendation"] for r in responses]
winner = max(set(votes), key=votes.count)
print(f"Consensus: {winner}")
```

---

### Communication Channel 5: Status Updates

**Purpose:** Keep other agents informed of progress without blocking

**Pattern:**
```python
# ChatDev updating Copilot on implementation progress
status_update = {
    "message_type": "status_update",
    "sender": "chatdev:team_1",
    "context_quest": "feature_xyz_implementation",
    "progress_percent": 45,
    "current_task": "Implementing database migrations",
    "completed_milestones": [
        "API design doc created",
        "FastAPI project scaffolded",
        "Database models defined"
    ],
    "next_milestone": "API endpoints implementation",
    "estimated_remaining_minutes": 30,
    "blockers": []
}

quest_log.add_entry(status_update)

# Copilot checks progress
progress = quest_log.query(
    context_quest="feature_xyz_implementation",
    message_type="status_update",
    sender="chatdev:team_1"
)

if progress:
    latest = progress[-1]
    print(f"ChatDev progress: {latest['progress_percent']}%")
    print(f"ETA: {latest['estimated_remaining_minutes']} minutes")
```

---

### Communication Channel 6: Review Requests

**Purpose:** Ask another agent to review work before graduation

**Pattern:**
```python
# ChatDev asking Copilot for code review before including in canonical
review_request = {
    "message_type": "review_request",
    "sender": "chatdev",
    "receiver": "copilot",
    "artifact": "src/api/auth.py",
    "lines_of_code": 342,
    "checklist": [
        {"item": "No hardcoded secrets", "weight": 1.0},
        {"item": "Proper error handling", "weight": 0.8},
        {"item": "Type hints on all functions", "weight": 0.9},
        {"item": "Unit tests for auth logic", "weight": 0.7},
        {"item": "Docstrings on public methods", "weight": 0.6}
    ],
    "graduation_candidate": True,
    "target_location": "src/api/auth.py"
}

quest_log.add_entry(review_request)

# Copilot reviews and responds
review_response = {
    "message_type": "review_response",
    "sender": "copilot",
    "reviewer": "copilot",
    "request_id": review_request["artifact"],
    "approved": False,
    "checklist_scores": {
        "No hardcoded secrets": 1.0,
        "Proper error handling": 0.6,  # Found missing try/except
        "Type hints on all functions": 0.9,
        "Unit tests for auth logic": 0.3,  # Only 1 test
        "Docstrings on public methods": 1.0
    },
    "overall_score": 0.74,
    "approval_threshold": 0.80,
    "feedback": [
        {"line": 45, "issue": "Missing try/except around database call"},
        {"line": 120, "issue": "Only 1 unit test; need 5 minimum"},
        {"line": 200, "issue": "Hardcoded timeout value"}
    ],
    "graduation_approved": False,
    "next_steps": "Address feedback, request re-review"
}

quest_log.add_entry(review_response)
```

---

### Routing Decision Tree: Which Channel to Use

```
Agent A → Agent B
    ↓
Is it a query that needs a reply?
    ├─ YES: Consensus Request (Channel 4)
    │   └─ Need multiple opinions? → Consensus voting
    │   └─ Need single expertise? → Direct escalation (Channel 2)
    │
    ├─ NO: Is work being handed off?
    │   ├─ YES: Result Handoff (Channel 3)
    │   │   └─ Work complete, ready for next phase
    │   │
    │   └─ NO: Is this an error/blocker?
    │       ├─ YES: Error Escalation (Channel 2)
    │       │   └─ I'm stuck, need help
    │       │
    │       └─ NO: Is it just an update?
    │           ├─ YES: Status Update (Channel 5)
    │           │   └─ Keeping you informed
    │           │
    │           └─ NO: Is it a review?
    │               ├─ YES: Review Request (Channel 6)
    │               │   └─ Before graduation, I need your approval
    │               │
    │               └─ NO: General coordination?
    │                   └─ Quest Log Exchange (Channel 1)
    │                       └─ Store for any agent to read
```

---

### Agent Communication Best Practices

**✅ DO:**
- ✅ Always include `timestamp` for causality tracking
- ✅ Use `quest_id` to link messages to parent task
- ✅ Set clear expectations (deadline, format, acceptance criteria)
- ✅ Provide context sufficient for receiver to act independently
- ✅ Log all communication for audit trail
- ✅ Acknowledge receipt of handoffs

**❌ DON'T:**
- ❌ Assume the other agent reads messages instantly (always poll)
- ❌ Send vague requests without context or acceptance criteria
- ❌ Skip the review step before graduating code
- ❌ Leave messages without status (mark as "pending", "acknowledged", "completed")
- ❌ Send circular requests (A asks B, B asks A) without breaking the cycle
- ❌ Block waiting for response; use async patterns (poll, check later)

---

### Common Multi-Agent Workflows

#### Workflow A: Design → Implementation → Review → Graduation

```
Copilot (design)
    ↓ [Result Handoff]
ChatDev (implement)
    ↓ [Review Request]
Claude (review)
    ↓ [Review Response + Approval]
ChatDev (fix feedback)
    ↓ [Result Handoff]
Copilot (graduate to canonical)
```

#### Workflow B: Fast Problem with Fallback

```
Ollama:qwen (primary)
    ↓ [Timeout after 60s]
[Error Escalation]
    ↓
Claude (fallback)
    ↓ [Result returned]
Copilot (integrate result)
```

#### Workflow C: Parallel Experiments + Consensus

```
Copilot (design 3 approaches)
    ↓ [Consensus Request]
┌─ Ollama:qwen (approach A)
├─ Claude (approach B)
└─ ChatDev (approach C)
    ↓ [All respond in parallel]
[Aggregate votes]
    ↓
Winner approach handed to implementation team
```

---

## �📖 Quick Reference Card

### **Essential Commands (Copy/Paste Ready)**

```powershell
# === NAVIGATION ===
cdhub              # → NuSyQ-Hub
cdroot             # → NuSyQ root
cdverse            # → SimulatedVerse

# === DIAGNOSTICS ===
python scripts/start_nusyq.py                    # Quick snapshot
python scripts/start_nusyq.py error_report # Full scan
python scripts/verify_tripartite_workspace.py    # Workspace health

# === SEARCH ===
python -m src.search.smart_search keyword "<term>" --limit 50
python scripts/find_existing_tool.py --capability "<need>"

# === DOCKER ===
docker ps --format "table {{.Names}}\t{{.Status}}"
docker compose -f deploy/docker-compose.full-stack.yml up -d
docker compose -f deploy/docker-compose.full-stack.yml logs nusyq-hub --tail 100

# === AI AGENTS ===
ollama list                           # Check Ollama models
python NuSyQ/nusyq_chatdev.py          # ChatDev teams
python scripts/test_lmstudio.py --base http://10.0.0.172:1234  # LM Studio

# === QUESTS ===
Get-Content src/Rosetta_Quest_System/quest_log.jsonl -Tail 20 | ConvertFrom-Json
```

---

## 🔗 Additional Resources

### **Core Documentation**

- [NuSyQ-Hub README](../README.md) - Architecture & setup
- [AGENTS.md](../AGENTS.md) - Agent navigation protocol
- [ROSETTA_STONE.md](.vscode/prime_anchor/docs/ROSETTA_STONE.md) - Quick reference
- [OPERATIONS.md](../docs/OPERATIONS.md) - Operational workflows

### **Instruction Files**

- [copilot-instructions.md](../.github/copilot-instructions.md) - Copilot integration
- [COPILOT_INSTRUCTIONS_CONFIG.instructions.md](../.github/instructions/COPILOT_INSTRUCTIONS_CONFIG.instructions.md) - Configuration
- [FILE_PRESERVATION_MANDATE.instructions.md](../.github/instructions/FILE_PRESERVATION_MANDATE.instructions.md) - Anti-bloat rules
- [NuSyQ-Hub_INSTRUCTIONS.instructions.md](../.github/instructions/NuSyQ-Hub_INSTRUCTIONS.instructions.md) - Hub-specific guidance

### **Session Logs & Reports**

- [Agent Sessions](../docs/Agent-Sessions/) - Work history
- [Diagnostics](../docs/Reports/diagnostics/) - Error reports
- [Docker Setup](../SESSION_DOCKER_SETUP_20260203.md) - Docker integration guide

### **SimulatedVerse Docs**

- [SimulatedVerse README](../../SimulatedVerse/SimulatedVerse/README.md) - ΞNuSyQ framework
- [DEPLOYMENT.md](../../SimulatedVerse/SimulatedVerse/DEPLOYMENT.md) - Stack deployment
- [CULTURE_SHIP_READY.md](../../SimulatedVerse/SimulatedVerse/CULTURE_SHIP_READY.md) - Integration

### **NuSyQ Root Docs**

- [NuSyQ README](../../NuSyQ/README.md) - Multi-agent hub
- [nusyq.manifest.yaml](../../NuSyQ/nusyq.manifest.yaml) - Configuration
- [knowledge-base.yaml](../../NuSyQ/knowledge-base.yaml) - Persistent learning

---

## 🎓 Course Syllabus (Agent Onboarding Path)

### **Day 1: Orientation**

1. ✅ Read [Tripartite Orientation](#1-tripartite-orientation)
2. ✅ Run `python scripts/verify_tripartite_workspace.py`
3. ✅ Setup aliases (reload PowerShell profile)
4. ✅ Test navigation (`cdhub`, `cdroot`, `cdverse`)
5. ✅ Run first snapshot: `python scripts/start_nusyq.py`

### **Day 2: Diagnostics & Tools**

1. ✅ Run full error report: `python scripts/start_nusyq.py error_report`
2. ✅ Test Smart Search: `python -m src.search.smart_search keyword "quest"`
3. ✅ Explore quest log: `Get-Content src/Rosetta_Quest_System/quest_log.jsonl -Tail 20`
4. ✅ Try find existing tool: `python scripts/find_existing_tool.py --capability "search"`

### **Day 3: Multi-AI Integration**

1. ✅ Check Ollama: `ollama list`
2. ✅ Test LM Studio: `python scripts/test_lmstudio.py --base http://10.0.0.172:1234`
3. ✅ Review orchestrator: `src/orchestration/unified_ai_orchestrator.py`
4. ✅ Test agent routing: `from src.tools.agent_task_router import route_task`

### **Day 4: Docker & Deployment**

1. ✅ Verify Docker: `docker version`
2. ✅ Check running containers: `docker ps`
3. ✅ Review compose files: `deploy/docker-compose*.yml`
4. ✅ Test SimulatedVerse override (if deploying full stack)

### **Day 5: Advanced Workflows**

1. ✅ Study [Testing Chamber Pattern](#testing-chamber-pattern)
2. ✅ Review [Three Before New Protocol](#three-before-new-protocol)
3. ✅ Practice self-healing: `python src/healing/quantum_problem_resolver.py`
4. ✅ Explore consciousness bridge: `src/integration/consciousness_bridge.py`

---

**🎯 Completion Criteria:** Agent can navigate all 3 repos, run diagnostics, route tasks to appropriate AI systems, and troubleshoot common issues autonomously.

---

**Last Updated:** 2026-02-04  
**Maintainers:** NuSyQ Development Team  
**Feedback:** Log issues via quest system or `src/Rosetta_Quest_System/quest_log.jsonl`
