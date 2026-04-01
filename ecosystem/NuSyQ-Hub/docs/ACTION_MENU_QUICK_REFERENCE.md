# 🎯 Action Menu Quick Reference - NuSyQ Operators Guide

**Status:** ✅ WIRED  
**Date:** 2026-02-16  
**Version:** 1.0

## Overview

The NuSyQ Action Menu provides **unified, categorized access** to all 60+ system capabilities through a clean interface. No more memorizing command names - just navigate categories or use operator phrases.

## Quick Access

### VS Code Tasks (Fastest)
Press `Ctrl+Shift+P` → `Tasks: Run Task` → Select:
- **🎯 NuSyQ: Action Menu** - Main menu
- **🏥 Menu: Heal Actions** - Health & recovery actions
- **📊 Menu: Analyze Actions** - Analysis & diagnostics
- **🏗️ Menu: Develop Actions** - Development workflows
- **🤖 Menu: AI Actions** - Multi-AI orchestration
- **💡 Menu: Examples** - Common usage examples

### Command Line
```bash
# Main menu
python start_nusyq.py menu

# Category view
python start_nusyq.py menu <category>

# Examples
python start_nusyq.py menu examples

# Direct action
python start_nusyq.py <action> [args...]
```

## Operator Phrases (for AI Agents)

Tell the agent these phrases to invoke system actions:

### 🏥 Health & Recovery
- **"Show me the action menu"** → Main menu
- **"Heal the system"** → `python start_nusyq.py heal`
- **"Check system health"** → `python start_nusyq.py doctor`
- **"Run hygiene check"** → `python start_nusyq.py hygiene`
- **"Quick selfcheck"** → `python start_nusyq.py selfcheck`

### 📊 Analysis & Diagnostics
- **"Analyze the system"** → `python start_nusyq.py analyze`
- **"Generate error report"** → `python start_nusyq.py error_report`
- **"Poll error report job"** → `python start_nusyq.py error_report_status --wait=30 --json`
- **"System status brief"** → `python start_nusyq.py brief`
- **"Check AI systems"** → `python start_nusyq.py ai_status`
- **"Analyze causal chain"** → `python start_nusyq.py causal_analysis --text="retries happen because cache invalidation triggers rebuild after deploy"`
- **"Run graph learning"** → `python start_nusyq.py graph_learning --json --hub-only --top-k=5`
- **"Generate advanced AI quests"** → `python start_nusyq.py advanced_ai_quests --json`
- **"Show specialization learning"** → `python start_nusyq.py specialization_status --json`
- **"Show capabilities"** → `python start_nusyq.py capabilities`

### 🛰️ Async Job Control
- **"Run doctor async"** → `python start_nusyq.py doctor --quick --async --json`
- **"Poll doctor job"** → `python start_nusyq.py doctor_status --wait=30 --json`
- **"Cancel doctor job"** → `python start_nusyq.py doctor_status <job_id> --cancel --json`
- **"Retry doctor job"** → `python start_nusyq.py doctor_status <job_id> --retry --json`
- **"Poll system complete job"** → `python start_nusyq.py system_complete_status --wait=30 --json`
- **"Poll OpenClaw smoke job"** → `python start_nusyq.py openclaw_smoke_status --wait=30 --json`
- **"Poll Culture Ship job"** → `python start_nusyq.py culture_ship_status --wait=30 --json`

### 🏗️ Development & Creation
- **"Develop with ChatDev"** → `python start_nusyq.py develop_system <description>`
- **"Generate code"** → `python start_nusyq.py generate <description>`
- **"Start work session"** → `python start_nusyq.py work`
- **"Run task"** → `python start_nusyq.py task <task_name>`
- **"Autonomous cycle"** → `python start_nusyq.py auto_cycle`

### ⚡ Code Enhancement (NEW 2026-02-16)
- **"Patch <file>"** → `python start_nusyq.py patch <file> "<description>"`
- **"Fix error"** → `python start_nusyq.py fix "<error_description>"`
- **"Improve <target>"** → `python start_nusyq.py improve <file_or_directory>`
- **"Update dependencies"** → `python start_nusyq.py update --deps`
- **"Modernize <file>"** → `python start_nusyq.py modernize <file>`
- **"Enhance <target>"** → `python start_nusyq.py enhance <target>` (interactive)

### 🔍 Review & Quality
- **"Review this file"** → `python start_nusyq.py review <file>`
- **"Analyze <file>"** → `python start_nusyq.py analyze <file>`
- **"Check doctrine"** → `python start_nusyq.py doctrine_check`
- **"Run tests"** → `python start_nusyq.py test`

### 🐛 Debugging
- **"Debug this error"** → `python start_nusyq.py debug "<error_description>"`
- **"Diagnose tracing"** → `python start_nusyq.py trace_doctor`
- **"Diagnose Claude"** → `python start_nusyq.py claude_doctor`
- **"Diagnose Codex"** → `python start_nusyq.py codex_doctor`
- **"Diagnose Copilot"** → `python start_nusyq.py copilot_doctor`
- **"Diagnose The Triad"** → `python start_nusyq.py multi_agent_doctor`
- **"Diagnose The Fleet"** → `python start_nusyq.py agent_fleet_doctor`
- **"Problem snapshot"** → `python start_nusyq.py problem_signal_snapshot`

### 🤖 AI Orchestration
- **"Route to Ollama"** → Uses agent_task_router with target="ollama"
- **"Route to ChatDev"** → Uses agent_task_router with target="chatdev"
- **"Check orchestrator"** → `python start_nusyq.py orchestrator_status`
- **"Dispatch background task"** → `python start_nusyq.py dispatch_task`

### 🎯 Autonomous Operation
- **"Start auto-cycle"** → `python start_nusyq.py auto_cycle`
- **"Generate next actions"** → `python start_nusyq.py next_action_generate`
- **"Execute queue"** → `python start_nusyq.py queue`
- **"Process PU queue"** → `python start_nusyq.py pu_execute`

### 📜 Quest Management
- **"Show Guild board"** → `python start_nusyq.py guild_status`
- **"Available quests"** → `python start_nusyq.py guild_available`
- **"Claim quest"** → `python start_nusyq.py guild_claim <quest_id>`
- **"Complete quest"** → `python start_nusyq.py guild_complete <quest_id>`
- **"Log to quest"** → `python start_nusyq.py log_quest <message>`

## Action Categories

### 🏥 Heal (5 actions)
Repository health restoration, import fixes, dependency repair
- `heal` - Full health restoration
- `hygiene` - Spine hygiene + AI availability
- `doctor` - Comprehensive diagnostic
- `selfcheck` - Quick integrity check
- `trace_doctor` - Tracing diagnostics
- `claude_doctor` - Claude preflight/CLI/router/terminal diagnostics
- `codex_doctor` - Codex CLI/router/terminal diagnostics
- `copilot_doctor` - Copilot chat/CLI/router/terminal diagnostics
- `multi_agent_doctor` - Shared Claude/Codex/Copilot triad diagnostics
- `agent_fleet_doctor` - Fleet diagnostics across triad, local models, Claw-family, Culture Ship, and docs

### 📊 Analyze (15 actions)
Code analysis, system diagnostics, error reports
- `analyze` - AI-powered system/file analysis
- `delegation_matrix` - Router delegation/schema/health matrix
- `error_report` - Unified error diagnostic
- `error_report_split` - Split by repository
- `error_signal_bridge` - Error groups → guild board signals
- `signal_quest_bridge` - Guild signals → quest log entries
- `error_quest_bridge` - Critical errors → auto-generated quests
- `causal_analysis` - Local causal-link and feedback-loop analysis
- `graph_learning` - Dependency-graph learning and impact analysis
- `advanced_ai_quests` - Generate/deduplicate quests for advanced-AI readiness gaps
- `specialization_status` - Cross-agent specialization coverage and recent learning events
- `problem_signal_snapshot` - Problem signals capture
- `brief` - Quick status brief
- `ai_status` - AI agent availability
- `capabilities` - List all capabilities

### 🏗️ Develop (5 actions)
Software development, code generation, workflows
- `develop_system` - ChatDev multi-agent development
- `generate` - AI code generation
- `work` - Interactive development session
- `task` - Execute specific task
- `auto_cycle` - Autonomous development cycle

### ⚡ Enhance (6 actions) - NEW 2026-02-16
Code quality improvement, modernization, fixes
- `patch` - Quick targeted fix for file/module
- `fix` - Resolve specific error (Quantum Resolver)
- `improve` - Code quality & performance analysis
- `update` - Dependency & API updates
- `modernize` - Upgrade to modern Python patterns
- `enhance` - Interactive enhancement mode (guided)

### ✨ Create (3 actions)
New projects, prototypes, testing chamber
- `generate` - Generate new projects
- `develop_system` - ChatDev project creation
- `work` - Interactive creation session

### 🔍 Review (5 actions)
Code quality, security, documentation review
- `review` - AI code review
- `analyze` - Comprehensive analysis
- `doctrine_check` - Doctrine adherence
- `test` - Test suite execution
- `test_history` - Test execution history

### 🐛 Debug (4 actions)
Error resolution, quantum debugging
- `debug` - Quantum Error Bridge debugging
- `trace_doctor` - Tracing diagnostics
- `claude_doctor` - Claude diagnostics
- `codex_doctor` - Codex diagnostics
- `copilot_doctor` - Copilot diagnostics
- `multi_agent_doctor` - Triad diagnostics
- `error_report` - Error analysis
- `problem_signal_snapshot` - Signal capture

### 🤖 AI (11 actions)
Multi-AI coordination, model routing
- `ai_status` - Systems availability
- `analyze` - Route to AI systems
- `review` - AI code review routing
- `debug` - AI/Quantum routing
- `generate` - AI generation routing
- `causal_analysis` - Local causal reasoning over text and system variables
- `graph_learning` - Dependency graph-learning and impact report
- `advanced_ai_quests` - Create quests for remaining advanced-AI readiness gaps
- `specialization_status` - Inspect learned agent-task specialization profiles
- `claude_doctor` - Claude readiness diagnostics
- `codex_doctor` - Codex readiness diagnostics
- `copilot_doctor` - Copilot readiness diagnostics
- `multi_agent_doctor` - Triad readiness diagnostics
- `orchestrator_status` - Orchestrator check
- `dispatch_task` - Background task dispatch

### 🎯 Autonomous (5 actions)
Self-improvement, evolution, perpetual operation
- `auto_cycle` - Autonomous development
- `next_action_generate` - Generate action queue
- `next_action_exec` - Execute next action
- `pu_execute` - Process PU queue
- `suggest` - AI suggestions

### 📜 Quest (8 actions)
Task management, Guild coordination
- `log_quest` - Log to quest system
- `guild_status` - Board status
- `guild_available` - Available quests
- `guild_claim` - Claim quest
- `guild_start` - Start quest
- `guild_complete` - Complete quest
- `auto_quest` - Alias for error_quest_bridge
- `guild_render` - Render board

### 👁️ Observability (8 actions)
Tracing, metrics, correlation tracking
- `terminal_snapshot` - Generate agent-readable terminal and output registry
- `trace_service_status` - Stack status
- `trace_service_start` - Start services
- `trace_service_stop` - Stop services
- `trace_doctor` - Diagnose issues
- `claude_doctor` - Diagnose Claude readiness
- `codex_doctor` - Diagnose Codex readiness
- `copilot_doctor` - Diagnose Copilot readiness
- `multi_agent_doctor` - Diagnose triad readiness
- `trace_correlation_on` - Enable correlation
- `trace_correlation_off` - Disable correlation
- `trace_config_show` - Show configuration

## Integration Points

### Quest System
All actions can be logged to the quest system for persistent memory:
```bash
python start_nusyq.py log_quest "Ran heal action, fixed 12 import errors"
```

### Agent Task Router
The menu integrates with `AgentTaskRouter` for AI-powered routing:
```python
from src.tools.agent_task_router import AgentTaskRouter
router = AgentTaskRouter()
await router.analyze_with_ai("path/to/file", target="ollama")
```

### Model Discovery
Actions use the dynamic model discovery system to route to available AI models:
- 16 models discovered (Ollama + LM Studio + OpenAI + ChatDev)
- Capability-based selection (code, general, local, reasoning)
- Automatic fallback chains

### Terminal Routing
Actions automatically route to themed terminals:
- 🔥 Errors → `error_report`, `error_signal_bridge`, `trace_doctor`
- 🧠 Claude → `claude_doctor`, `claude_preflight`
- 🧠 Codex → `codex_doctor`
- 🤖 Copilot → `copilot_doctor`, `copilot_probe`
- 🕸️ Triad → `multi_agent_doctor`
- 🌐 Fleet → `agent_fleet_doctor`
- 🕸️ Router → `delegation_matrix`
- 🧪 Tests → `test`, `test_history`
- 📊 Metrics → `brief`, `doctor`, `ai_status`
- 🤖 Agents → `analyze`, `review`, `debug`, `generate`
- ✅ Tasks → `work`, `queue`, `pu_execute`, `signal_quest_bridge`, `error_quest_bridge`
- 💡 Suggestions → `suggest`, `next_action`
- 🎯 Zeta → `auto_cycle`
- 🏠 Main → `snapshot`, `help`, `menu`

### Terminal Awareness
Use the existing terminal surfaces as machine-readable infrastructure:
```bash
python start_nusyq.py terminal_snapshot          # write terminal/output awareness registry
python start_nusyq.py terminals doctor           # diagnose stale, missing, or broken channels
python start_nusyq.py terminals probe            # emit probes to verify watcher/log ingestion
python start_nusyq.py terminals stream --focus=all --follow
```

## Common Workflows

### 1. Daily Health Check
```bash
python start_nusyq.py hygiene --fast      # Quick check
python start_nusyq.py ai_status           # Verify AI systems
python start_nusyq.py brief               # Status overview
```

### 2. Deep System Analysis
```bash
python start_nusyq.py analyze             # Full system
python start_nusyq.py error_report        # All errors
python start_nusyq.py error_report --chain-bridges --bridge-max-quests=10 --bridge-severity=error
python start_nusyq.py doctor              # Health diagnostic
```

### 2b. Async Gate Workflow
```bash
python start_nusyq.py doctor --quick --async --json
python start_nusyq.py doctor_status --wait=30 --json
python start_nusyq.py doctor_status <job_id> --cancel --json   # Optional control
```

### 3. Development Workflow
```bash
python start_nusyq.py work                # Interactive session
python start_nusyq.py generate auth       # Generate code
python start_nusyq.py review src/main.py  # Review changes
python start_nusyq.py test                # Run tests
```

### 4. Code Enhancement Workflow (NEW)
```bash
python start_nusyq.py improve src/orchestration/  # Analyze quality
python start_nusyq.py patch src/main.py "Fix import"  # Quick patch
python start_nusyq.py modernize src/legacy.py     # Modern patterns
python start_nusyq.py test                        # Verify changes
```

### 5. Error Recovery
```bash
python start_nusyq.py debug "ImportError: cannot import 'foo'"
python start_nusyq.py heal                # Fix broken paths
python start_nusyq.py hygiene             # Verify recovery
```

### 5. Autonomous Operation
```bash
python start_nusyq.py auto_cycle          # Full autonomous cycle
python start_nusyq.py next_action_exec    # Execute next action
python start_nusyq.py guild_status        # Check progress
```

## Testing the Menu

```bash
# View main menu
python start_nusyq.py menu

# View specific category
python start_nusyq.py menu heal

# View all examples
python start_nusyq.py menu examples

# Invoke a specific action
python start_nusyq.py heal
```

## Next Steps

After familiarizing yourself with the menu:

1. **Set up keybindings** - Add VS Code keyboard shortcuts for frequent actions
2. **Create custom workflows** - Chain actions together for your workflow
3. **Automate with quests** - Use quest system to track multi-step work
4. **Enable observability** - Start trace services for full system visibility
5. **Explore autonomous mode** - Let the system improve itself

## Reference Documentation

- [AGENTS.md](../AGENTS.md) - Agent navigation protocol
- [copilot-instructions.md](../.github/copilot-instructions.md) - System overview
- [MODEL_DISCOVERY_QUICK_REFERENCE.md](MODEL_DISCOVERY_QUICK_REFERENCE.md) - Model routing
- [start_nusyq.py](../scripts/start_nusyq.py) - Full implementation

---

**Last Updated:** 2026-02-16  
**Status:** Production Ready ✅  
**Total Actions:** 60+  
**Categories:** 10
