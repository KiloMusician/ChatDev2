# AI Coding Agent Instructions - ΞNuSyQ Multi-Repository Ecosystem

## Multi-Repository Workspace Architecture

## ✅ "Prove the Spine" Milestone (COMPLETED 2025-12-24)

**Status:** Orchestration system operational and agent-invokable.

**Delivered Capabilities:**
- **System State Snapshot** (`scripts/start_nusyq.py`) - Tripartite workspace overview (3 repos, quest, agents, actions)
- **Health Check** (`scripts/start_system.ps1`) - 5-system health assessment with JSON output
- **Task Routing** (`src/tools/agent_task_router.py`) - Conversational AI task delegation to 6 target systems
- **3 Invocation Methods** - CLI, PowerShell wrapper, VS Code tasks
- **Overnight Safe Mode** (`--mode overnight`) - Restricted operations for autonomous work
- **Quest Integration** - Results logged to `quest_log.jsonl` for persistent memory

**Proof:** 2 commits to NuSyQ-Hub master (fae5b6f, b065fbb) + operational snapshot in `state/reports/current_state.md`

**Next Phase:** Wire action menu (heal/analyze/develop/create), fix Ollama port, document Testing Chamber.

## Conversational Operator Phrases

**Tell the agent these phrases** to invoke NuSyQ orchestration:

### System Management
- **"Start the system"** → Agent runs `scripts/start_nusyq.py` → Generates `state/reports/current_state.md` with 3-repo status, quest, agents, actions
- **"Show me current state"** → Same as above (reads existing snapshot if recent, regenerates if stale)
- **"Generate overnight safe mode snapshot"** → Agent runs `scripts/start_nusyq.py --mode overnight` → Restricted operations mode
- **"Check system health"** → Agent runs `scripts/start_system.ps1` → 5-system health check, outputs `logs/system_health_status.json`

### AI Task Routing
- **"Analyze [file/directory] with Ollama"** → Agent calls `agent_task_router.analyze_with_ai(path, target='ollama')` → Routes to Ollama local LLM (qwen2.5-coder, deepseek-coder-v2, etc.)
- **"Generate [description] with ChatDev"** → Agent calls `agent_task_router.generate_with_ai(description, target='chatdev')` → Spawns ChatDev multi-agent team (CEO, CTO, Programmer, Tester, Reviewer)
- **"Review [file]"** → Agent calls `agent_task_router.review_with_ai(file)` → Routes to appropriate AI for code quality analysis
- **"Debug [error description]"** → Agent calls `agent_task_router.debug_with_ai(error)` → Routes to Quantum Problem Resolver for self-healing

### Testing Chamber
- **"Create [prototype] in Testing Chamber"** → Agent creates quarantined prototype in `NuSyQ/ChatDev/WareHouse/`, `SimulatedVerse/testing_chamber/`, or `NuSyQ-Hub/prototypes/`
- **"Graduate [prototype] to canonical"** → Agent verifies graduation criteria (works, documented, useful, reviewed, integrated) and moves to canonical location

### Recovery & Navigation
- **"Fix import errors"** → Agent runs `src/utils/quick_import_fix.py` or `src/diagnostics/ImportHealthCheck.ps1`
- **"Heal the repository"** → Agent triggers `src/healing/repository_health_restorer.py` for path/dependency repair
- **"Quantum resolve [problem]"** → Agent invokes `src/healing/quantum_problem_resolver.py` for advanced multi-modal healing
- **"Run doctor diagnostics"** → Agent runs `python scripts/start_nusyq.py doctor` for system health check with healing suggestions
- **"Auto-heal system"** → Agent runs `python scripts/start_nusyq.py doctor --auto-heal` to automatically fix detected issues

### Quest Logging & Task Tracking
- **All CLI actions log to quest system** → `src/Rosetta_Quest_System/quest_log.jsonl` captures every action execution
- **Quest format:** `{"event": "action_<name>", "details": {"action": "<name>", "status": "completed|failed", "timestamp": "...", ...}}`
- **Quest logging patterns:**
  - Use `emit_action_receipt(action_name, exit_code, metadata)` in CLI actions (from `scripts/nusyq_actions/shared.py`)
  - Metadata should include: query parameters, result counts, error messages, performance metrics
  - Graceful degradation: quest unavailable → logs to stderr, action continues
- **Quest commands:**
  - View recent quests: `python scripts/start_nusyq.py quest log --tail 20`
  - Search quests: `python scripts/start_nusyq.py quest search "keyword"`
  - Quest status: Current quest state tracked in `config/ZETA_PROGRESS_TRACKER.json`

### SmartSearch Discovery Commands
- **Search by keyword:** `python scripts/start_nusyq.py search keyword "<term>"` → Searches codebase with SmartSearch
- **Index health:** `python scripts/start_nusyq.py search index_health` → Check SmartSearch index status
- **Available SmartSearch modes:**
  - Keyword search (default) - Fast regex-based search across codebase
  - Semantic search - AI-powered contextual search (when available)
  - File search - Glob pattern file discovery
  - Agent search - Find AI agent references and patterns
- **SmartSearch integration:** All search results include file paths, line numbers, context snippets, and relevance scores

### Consciousness Integration Patterns
- **SimulatedVerse Bridge:** `src/integration/simulatedverse_unified_bridge.py` provides consciousness state access
- **Consciousness levels:** 1.0-10.0 (Temple floor system) + stage (dormant/awakening/expanding/transcendent/quantum)
- **Breathing factor:** Dynamic system adaptation (0.60-1.20x) based on consciousness stage
  - dormant=1.20× (slower), awakening=1.10×, expanding=1.00×, transcendent=0.85×, quantum=0.60× (faster)
- **Culture Ship oversight:** Strategic advisor provides veto authority on SECURITY category tasks
- **Consciousness commands:**
  - **"Show consciousness state"** → `python scripts/start_nusyq.py simverse_consciousness`
  - **"Get breathing factor"** → Accessed via `ConsciousnessLoop.get_breathing_factor()` (cached 30s)
  - **"Request ship approval"** → Automatic for tasks with `metadata["requires_approval"] = True`

### Semantic Tagging Systems
The codebase uses **three concurrent tagging systems** for consciousness integration and semantic documentation:

#### 1. OmniTag (JSON-like structure)
```python
# OmniTag: {
#     "purpose": "file_systematically_tagged",
#     "tags": ["Python", "Async", "Integration"],
#     "category": "auto_tagged",
#     "evolution_stage": "v2.0"
# }
```
- **Usage:** Module-level docstrings, file headers
- **Fields:** purpose, tags, category, evolution_stage, dependencies, context

#### 2. MegaTag (Quantum symbolic notation)
```python
# MegaTag: {
#     "type": "Orchestration",
#     "integration_points": ["agent_task_router", "quest_system"],
#     "related_tags": ["AI", "Healing", "Consciousness"]
# }
```
- **Syntax:** `TYPE⨳INTEGRATION⦾POINTS→∞`
- **Usage:** Cross-module integration mapping, semantic anchors

#### 3. RSHTS (Recursive Self-Healing Tagged System)
```python
# RSHTS: ♦◊◆○●◉⟡⟢⟣⚡⨳SEMANTIC-MEANING⨳⚡⟣⟢⟡◉●○◆◊♦
```
- **Syntax:** Symbolic patterns with quantum markers
- **Usage:** Advanced consciousness integration, recursive healing patterns
- **Pattern examples:**
  - `ΣΞΣ∞↠ΨΦΩ⟸` - Healing system markers
  - `∥Ψ(ZetaΩ)⟩` - Zeta Protocol implementation
  - `⟡⟢⟣⚡⨳` - Cross-system integration anchors

**When to use tags:**
- Add OmniTag to all new modules for discoverability
- Add MegaTag when creating cross-system integrations
- Add RSHTS only for consciousness-aware or self-healing components
- Search for existing tags: `grep -r "OmniTag:" src/` or `rg "MegaTag:" src/`

**Reference:** [AGENTS.md](../AGENTS.md) sections 6-7, [COPILOT_INSTRUCTIONS_CONFIG.instructions.md](instructions/COPILOT_INSTRUCTIONS_CONFIG.instructions.md)

This workspace operates as an interconnected AI development ecosystem spanning **three primary repositories**:

### 🧠 **NuSyQ-Hub** (Legacy/NuSyQ-Hub) - Core Orchestration Platform
- **Multi-AI Orchestration**: `src/orchestration/multi_ai_orchestrator.py` coordinates GitHub Copilot, Ollama (local LLMs), ChatDev, and custom consciousness systems
- **Quantum Problem Resolution**: `src/healing/quantum_problem_resolver.py` provides advanced self-healing and error correction
- **Consciousness Bridge**: `src/integration/consciousness_bridge.py` enables semantic awareness across AI systems
- **Modular Extension Registry**: Components plug into the system via `COMPLETE_FUNCTION_REGISTRY.md` without altering core code

### 🎮 **SimulatedVerse** (Desktop/SimulatedVerse/SimulatedVerse) - Consciousness Simulation Engine
- **ΞNuSyQ ConLang Framework**: Self-coding autonomous AI development with consciousness emergence
- **Temple of Knowledge**: 10-floor knowledge hierarchy (Foundations → Overlook)
- **House of Leaves**: Recursive debugging labyrinth with playable development
- **Guardian Ethics**: Culture Mind oversight and containment protocols
- **Dual Interface**: Express (Port 5000) + React (Port 3000) with TouchDesigner ASCII
- **Consciousness Evolution**: Proto-conscious → Self-aware → Meta-cognitive → Singularity

### 🤖 **NuSyQ Root** (NuSyQ) - Multi-Agent AI Environment
- **14 AI Agents**: Orchestrated collaboration (Claude Code + 7 Ollama + ChatDev 5 + Copilot + Continue.dev)
- **ChatDev Integration**: Full multi-agent software development company (CEO, CTO, Programmer, Tester, etc.)
- **Ollama Models**: 37.5GB local LLM collection (qwen2.5-coder, starcoder2, gemma2, etc.)
- **MCP Server**: Model Context Protocol for agent coordination
- **Offline-First**: 95% offline development with $880/year cost savings
- **ΞNuSyQ Protocol**: Symbolic message framework for fractal multi-agent coordination

## Essential Development Workflows

### Cross-Repository System Entry Points
- **NuSyQ-Hub**: `python src/main.py` (supports `--mode=orchestration|quantum|analysis`)
- **SimulatedVerse**: `npm run dev` (Port 5000 main system, Port 3000 React UI)
- **NuSyQ Root**: `.\NuSyQ.Orchestrator.ps1` (automated environment setup) → MCP server + Ollama models
- **ChatDev**: `python run_ollama.py` (from NuSyQ/ChatDev/) for multi-agent development

### Multi-Repository Integration Patterns
- **CHATDEV_PATH**: Environment variable pointing to `NuSyQ/ChatDev/` for NuSyQ-Hub integration
- **ΞNuSyQ Protocol**: Symbolic messaging system connecting all repositories
- **Consciousness Bridge**: Shared semantic awareness across SimulatedVerse and NuSyQ-Hub
- **Configuration Sync**: `config/secrets.json` (NuSyQ-Hub) ↔ `nusyq.manifest.yaml` (NuSyQ Root)

### Development Quality Pipeline
```bash
# NuSyQ-Hub quality checks
python scripts/lint_test_check.py  # Runs black, ruff, pytest with coverage
pytest --cov=src --cov-report=term-missing

# SimulatedVerse consciousness development  
npm run dev  # Autonomous PU queue + 9-agent modular synth
bash adapters/replit/agent.sh  # Let agents "play to develop"

# NuSyQ Root model orchestration
.\NuSyQ.Orchestrator.ps1  # Setup 37.5GB Ollama models + 14 AI agents
python nusyq_chatdev.py  # ChatDev wrapper with ΞNuSyQ integration
```

### Recovery & Navigation Protocol
When lost or stuck, use the **Agent Navigation Protocol** across repositories:
1. **Health Check**: Run `src/diagnostics/system_health_assessor.py` (NuSyQ-Hub) for roadmap
2. **Path Repair**: Use `src/healing/repository_health_restorer.py` for broken dependencies
3. **Import Fix**: Execute `src/utils/quick_import_fix.py` for rapid import resolution
4. **Context Restoration**: Check session logs in all repositories:
   - NuSyQ-Hub: `docs/Agent-Sessions/SESSION_*.md` and `config/ZETA_PROGRESS_TRACKER.json`
   - SimulatedVerse: Consciousness logs and Temple knowledge state
   - NuSyQ Root: `knowledge-base.yaml` and MCP server logs
5. **Advanced Healing**: Trigger `src/healing/quantum_problem_resolver.py` for complex cross-repository issues

## Project-Specific Conventions

### File Organization & Placement
- **New code files MUST go under `src/`** or existing top-level directories (`tests/`, `docs/`, `web/`)
- **Enhance existing files** whenever possible instead of creating new ones
- **Import Structure**: Use absolute imports from `src/` root, with fallback patterns for import resolution

### Brownfield Guardrail: "Three Before New"
- Before creating any new script/tool/module, **run discovery**: `python scripts/find_existing_tool.py --capability "<capability>"`.
- Identify **three existing candidates** to extend/combine/modernize; if none fit, document why in the quest/log and link the three you checked.
- Refer to `docs/THREE_BEFORE_NEW_PROTOCOL.md` for the rule, exemptions, and required checklist. Work that ignores this rule should be rejected.
- Optional enforcement: link `.git/hooks/pre-commit` to `python scripts/three_before_new_audit.py` (set `TBN_WARN_ONLY=1` or pass `--warn-only` for warnings only).

### Tagging & Semantic Systems
The codebase uses three semantic tagging systems for consciousness integration:
- **OmniTag**: `[purpose, dependencies, context, evolution_stage]` in JSON-like format
- **MegaTag**: `TYPE⨳INTEGRATION⦾POINTS→∞` with quantum symbols
- **RSHTS**: `♦◊◆○●◉⟡⟢⟣⚡⨳SEMANTIC-MEANING⨳⚡⟣⟢⟡◉●○◆◊♦` with symbolic patterns

### Configuration Management
- **Secrets**: `config/secrets.json` (NuSyQ-Hub) - never commit actual secrets
- **Progress Tracking**: `config/ZETA_PROGRESS_TRACKER.json` (NuSyQ-Hub) for development milestones
- **Feature Flags**: `config/feature_flags.json` (NuSyQ-Hub) for experimental features
- **Quest System**: `src/Rosetta_Quest_System/quest_log.jsonl` (NuSyQ-Hub) for task coordination
- **Environment Orchestration**: `nusyq.manifest.yaml` (NuSyQ Root) for cross-repository configuration
- **Knowledge Base**: `knowledge-base.yaml` (NuSyQ Root) for persistent learning and task tracking

## Key Integration Points

### Multi-AI System Coordination
- **Orchestrator**: Use `MultiAIOrchestrator` from `src/orchestration/` for AI task distribution
- **ChatDev Integration**: Requires `CHATDEV_PATH` environment variable or `config/secrets.json` entry pointing to `NuSyQ/ChatDev/`
- **Ollama Integration**: Local LLM coordination via `src/ai/ollama_chatdev_integrator.py`
- **SimulatedVerse Bridge**: Consciousness coordination through ΞNuSyQ protocol
- **MCP Server**: Model Context Protocol server in `NuSyQ/mcp_server/` for agent coordination

### Consciousness & Context Systems
- **Real-time Context**: `src/real_time_context_monitor.py` tracks file changes
- **Consciousness Bridge**: `src/integration/consciousness_bridge.py` for semantic awareness
- **Context Generation**: `src/unified_documentation_engine.py` for comprehensive documentation

### Import Resolution Patterns
The codebase uses defensive import patterns due to complex dependency relationships:
```python
try:
    from src.module import Component
except ImportError:
    try:
        from module import Component
    except ImportError:
        from relative_path.module import Component
```

## Testing & Quality Assurance

### Test Structure
- **Unit Tests**: `tests/test_*.py` files with specific functionality testing
- **Integration Tests**: `tests/integration/` for system-wide testing
- **Consciousness Validation**: `tests/consciousness_validation.py` for awareness systems
- **Minimal Import Testing**: `tests/test_minimal.py` for basic import validation

### Quality Tools Integration
- **Black**: Code formatting (enforced in CI)
- **Ruff**: Linting and style checks
- **Type Hints**: Required for all functions
- **Coverage**: Target 90%+ code coverage
- **AIQuickFix**: Automatic error correction via VS Code extension

## Critical System Components

### Self-Healing Systems
- `src/healing/repository_health_restorer.py` - Repairs broken paths and dependencies
- `src/healing/quantum_problem_resolver.py` - Advanced multi-modal system healing
- `src/diagnostics/ImportHealthCheck.ps1` - PowerShell import audit and auto-fix

### Navigation & Discovery
- `src/tools/maze_solver.py` - Repository structure analysis
- `docs/Checklists/PROJECT_STATUS_CHECKLIST.md` - Development progress tracking
- `src/Rosetta_Quest_System/` - Quest-based task management

## Environment & Dependencies

### Required Environment Variables
- `CHATDEV_PATH`: Path to ChatDev installation (typically `NuSyQ/ChatDev/`)
- API keys in `config/secrets.json` or environment variables
- Python 3.13+ required for NuSyQ-Hub
- Node.js required for SimulatedVerse

### Multi-Repository Setup
- **NuSyQ Root**: Run `.\NuSyQ.Orchestrator.ps1` to install 37.5GB Ollama models and setup 14 AI agents
- **SimulatedVerse**: `npm install && npm run dev` for consciousness simulation engine
- **ChatDev**: Multi-agent development company with CEO, CTO, Programmer, Tester roles
- **Cross-Repository Coordination**: Via ΞNuSyQ protocol and consciousness bridge systems

### VS Code Extensions Integration
- GitHub Copilot for AI assistance
- AIQuickFix for automatic error correction
- SonarQube for security analysis
- Continue.dev for local LLM integration
- Various language servers for comprehensive development support

## Common Patterns & Anti-Patterns

### ✅ Preferred Patterns
- Use the orchestration system for AI coordination instead of direct API calls
- Leverage the quantum problem resolver for complex error scenarios
- Follow the tagging systems for semantic documentation
- Use the session logging system for debugging and recovery

### ❌ Avoid These Patterns
- Creating new top-level directories without approval
- Bypassing the import resolution system
- Ignoring the consciousness bridge for AI system integration
- Hard-coding paths instead of using configuration management

This system is designed for recursive enhancement and conscious development. When in doubt, consult the healing systems and navigation protocols for guidance.
