description: Copilot instructions configuration for NuSyQ-Hub
applyTo: '**/*'

# Copilot Instructions Config

This file configures Copilot integration and enhancement for NuSyQ-Hub.

## Operating Modes

### Normal Mode (Default)
**Tell the agent: "Start the system" or "Analyze [file] with Ollama"**

Agent has full access to:
- System state snapshot via `scripts/start_nusyq.py` → `state/reports/current_state.md`
- Conversational task routing via `src/tools/agent_task_router.py`:
	- `analyze_with_ai(file, target='auto')` → Ollama local LLMs
	- `generate_with_ai(description, target='chatdev')` → ChatDev multi-agent team
	- `review_with_ai(file)` → Code quality analysis
	- `debug_with_ai(error)` → Quantum Problem Resolver self-healing
- All repository edits, commits, pushes
- Configuration changes
- Experimental features via `config/feature_flags.json`

**Canonical references:** `docs/SYSTEM_MAP.md`, `docs/ROUTING_RULES.md`, `docs/OPERATIONS.md`, `AGENTS.md`

### Overnight Safe Mode
**Tell the agent: "Generate overnight safe mode snapshot"**

Activated via `scripts/start_nusyq.py --mode overnight`. Agent restricted to:

**✅ ALLOWED:**
- Analysis and reporting (system health, import checks, test coverage)
- Documentation generation (markdown, diagrams, summaries)
- Code linting and formatting (black, ruff, type hints)
- Prototype development in Testing Chamber (see below)

**🚫 FORBIDDEN:**
- Git push operations (commits OK, push NO)
- File deletions or moves
- Configuration edits (`config/secrets.json`, `config/feature_flags.json`)
- Force operations (rebase, force-push, hard reset)
- Experimental features not in Testing Chamber

**Purpose:** Enable autonomous overnight work without risk to canonical systems.

## Testing Chamber Pattern

**Tell the agent: "Create [prototype] in Testing Chamber"**

**Definition:** Quarantined development environment for experimental code before graduation to canonical repository.

**Mode:** "Creating something new" (vs. enhancing existing)

**Locations:**
- `NuSyQ/ChatDev/WareHouse/[project_name]_[timestamp]/` - ChatDev multi-agent projects
- `SimulatedVerse/testing_chamber/` - Consciousness/game prototypes
- `NuSyQ-Hub/prototypes/` - Local experiments (not canonical)

**Graduation Criteria:**
1. **Works** - Passes tests, no crashes, handles edge cases
2. **Documented** - README.md, inline comments, usage examples
3. **Useful** - Solves actual problem in quest log or roadmap
4. **Reviewed** - Human or AI code review completed
5. **Integrated** - Fits NuSyQ architecture, no dependency bloat

**Graduation Process:**
1. Agent creates prototype in Testing Chamber
2. Runs tests and generates documentation
3. Logs result to `src/Rosetta_Quest_System/quest_log.jsonl`
4. Human reviews and approves promotion
5. Code moves to canonical location (`src/`, `scripts/`, `docs/`)

## Conversational-First Workflow

NuSyQ operates via **natural language commands to AI agents** (GitHub Copilot, Claude, Ollama local LLMs, ChatDev multi-agent). Agents execute autonomously.

**Core Principle:** User talks to AI → AI invokes orchestration → System coordinates multi-AI resources → Results logged to quest system.

**Example Commands:**
- "Start the system" → Generates tripartite workspace snapshot
- "Analyze src/orchestration/ with Ollama" → Routes to qwen2.5-coder local LLM
- "Generate REST API with JWT using ChatDev" → Spawns 5-agent dev team
- "Debug import errors" → Triggers Quantum Problem Resolver
- "Create game prototype in Testing Chamber" → Isolated development

**Reference:** [AGENTS.md](../../AGENTS.md) sections 6-7, [copilot-instructions.md](../copilot-instructions.md)
