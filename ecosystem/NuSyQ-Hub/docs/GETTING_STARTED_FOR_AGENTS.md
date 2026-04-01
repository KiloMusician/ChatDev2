# Getting Started Guide for AI Agents

**Last Updated:** 2025-12-26

## Purpose

This guide helps AI agents (Claude, Copilot, Ollama models, ChatDev team, etc.) discover and use the 702+ capabilities available in the NuSyQ ecosystem.

**Companion Guides:** Start with [AGENT_TUTORIAL.md](./AGENT_TUTORIAL.md) for the tripartite overview and use this file for capability discovery and command lookup.

## The Discovery Problem We Solved

**Previous State:** The ecosystem had 702 capabilities (scripts, tools, functions, diagnostics, etc.) but no systematic way for agents to know what existed. Tools were being lost, forgotten, or re-implemented.

**Solution:** Comprehensive capability discovery system with searchable inventory and documentation.

---

## 🔍 How to Discover Capabilities

### 1. Quick Overview (Start Here!)

```bash
python scripts/start_nusyq.py capabilities
```

This shows:
- Total capabilities count (702)
- Quick commands available (462)
- Categories with top 5 items each
- Generated documentation paths

### 2. Search for Specific Tools

```bash
# Find commit-related tools
python scripts/start_nusyq.py capabilities --search commit

# Find monitoring systems
python scripts/start_nusyq.py capabilities --search monitor

# Find anything quantum-related
python scripts/start_nusyq.py capabilities --search quantum
```

### 3. Filter by Category

```bash
# Show only monitoring capabilities
python scripts/start_nusyq.py capabilities --category monitoring

# Show analysis tools
python scripts/start_nusyq.py capabilities --category analysis

# Show utilities
python scripts/start_nusyq.py capabilities --category utility
```

### 4. Refresh Inventory (After New Tools Added)

```bash
python scripts/start_nusyq.py capabilities --refresh
```

---

## 📚 Key Documentation Files

1. **[CAPABILITY_DIRECTORY.md](./CAPABILITY_DIRECTORY.md)** - Full catalog of all 702 capabilities
2. **[system_capability_inventory.json](../data/system_capability_inventory.json)** - Machine-readable inventory (345KB)
3. **[ecosystem_registry.json](../state/ecosystem_registry.json)** - Registered ecosystem bridges and systems

---

## 🎯 Most Important Capabilities (Recently Added)

### Autonomous Batch Commit Orchestrator

**What:** Intelligently groups uncommitted files into logical commits, saving 99% of manual intervention.

**Usage:**
```bash
# Dry run to see what would be committed
python scripts/start_nusyq.py batch_commit --dry-run

# Execute real commits
python scripts/start_nusyq.py batch_commit

# Limit number of commits
python scripts/start_nusyq.py batch_commit --max-commits=5
```

**Why Important:** With 77+ uncommitted files, manually creating commits would waste thousands of tokens. This tool handles it autonomously.

### Real PU Execution Mode

**What:** Execute PUs (Processing Units) through real ChatDev/Ollama agents instead of simulation.

**Usage:**
```bash
# Execute in simulation mode (default)
python scripts/start_nusyq.py pu_execute PU-2025-001

# Execute through real agents (ChatDev/Ollama)
python scripts/start_nusyq.py pu_execute PU-2025-001 --real
```

**Why Important:** Previously, PUs only simulated execution. Now they can invoke actual multi-agent teams.

### Capability Discovery System (This Guide!)

**What:** Comprehensive searchable catalog of all 702 system capabilities.

**Usage:** See above sections.

**Why Important:** Solves the "forgotten tools" problem - agents now have a systematic way to discover what exists.

---

## 🧠 AI Backend Systems

The ecosystem integrates multiple AI systems:

1. **🦖 Ollama** - Local LLMs
   - Models: qwen2.5-coder, deepseek-coder-v2, starcoder2
   - Best for: Code generation, analysis, review

2. **👥 ChatDev** - Multi-agent development team
   - Agents: CEO, CTO, Programmer, Tester, Reviewer
   - Best for: Complex projects requiring coordination

3. **🧠 Consciousness Bridge** - Semantic awareness
   - Capabilities: OmniTag processing, MegaTag analysis
   - Best for: Symbolic cognition, contextual memory

4. **⚛️ Quantum Problem Resolver** - Self-healing system
   - Capabilities: Quantum problem solving, superposition analysis
   - Best for: Multi-modal debugging, error resolution

5. **📊 Zen Codex Bridge** - Wisdom database
   - Capabilities: Rule-based error handling, 15 wisdom rules
   - Best for: Pattern matching common errors

---

## 🔧 Essential Commands (Start Here)

### System Health & Status

```bash
# Quick overview
python scripts/start_nusyq.py brief

# Comprehensive diagnostics
python scripts/start_nusyq.py doctor

# Health check with self-repair
python scripts/start_nusyq.py heal

# 5-point system diagnostic
python scripts/start_nusyq.py selfcheck
```

### Code Quality

```bash
# Analyze a file with AI
python scripts/start_nusyq.py analyze src/main.py

# Code quality review
python scripts/start_nusyq.py review src/main.py

# Get unified error report
python scripts/start_nusyq.py error_report --full
```

### Debugging

```bash
# Quantum debugging (converts error to PU)
python scripts/start_nusyq.py debug "TypeError in module X"

# VS Code diagnostics bridge
python scripts/start_nusyq.py vscode_diagnostics_bridge
```

### Development

```bash
# Generate new project with ChatDev
python scripts/start_nusyq.py generate "Create a web API for user management"

# Run tests
python scripts/start_nusyq.py test

# Execute next quest
python scripts/start_nusyq.py work
```

---

## 📖 Categories Breakdown

The 702 capabilities are organized into these categories:

- **ANALYSIS** (5 commands) - System analysis, discovery, snapshots
- **MAINTENANCE** (3 commands) - Consolidation, cleanup, health restoration
- **MONITORING** (4 commands) - Health monitoring, performance tracking
- **UTILITY** (413 commands) - General-purpose tools and scripts
- **VSCODE_TASK** (37 commands) - VS Code task integration

---

## 🎮 RPG-Style Capability Mapping

The system uses RPG concepts for capability organization:

- **Actions** - Active commands/functions you can execute
- **Passives** - Automated monitoring systems that run in background
- **Equipment** - Tools and utilities available
- **Skills** - Learned capabilities that improve with use
- **Quests** - Active objectives to complete
- **Achievements** - Milestones reached

Access the full RPG status:
```bash
python -m src.system.capability_inventory
```

---

## 🚀 Quick Start Workflow (For New Agents)

1. **Discover What Exists:**
   ```bash
   python scripts/start_nusyq.py capabilities
   ```

2. **Check System Health:**
   ```bash
   python scripts/start_nusyq.py selfcheck
   ```

3. **Get Context:**
   ```bash
   python scripts/start_nusyq.py brief
   ```

4. **Find Error Patterns:**
   ```bash
   python scripts/start_nusyq.py error_report --quick
   ```

5. **Search for Tools You Need:**
   ```bash
   python scripts/start_nusyq.py capabilities --search <your-topic>
   ```

---

## 💡 Best Practices for Agents

### Before Implementing New Features

1. **Check if it already exists:** Use `capabilities --search <topic>`
2. **Review similar tools:** Study existing implementations
3. **Understand the ecosystem:** Read the ecosystem_registry.json

### When Working with Code

1. **Use unified error reporting:** `error_report --full` shows all issues
2. **Leverage existing bridges:** Quantum Error Bridge, Zen Codex, etc.
3. **Follow conventional commits:** batch_commit does this automatically

### For Token Efficiency

1. **Batch operations when possible:** Use batch_commit, not manual commits
2. **Use simulation mode first:** Test with `--dry-run` flags
3. **Leverage autonomous systems:** develop_system, auto_cycle

---

## 📞 Getting Help

1. **Command-specific help:**
   ```bash
   python scripts/start_nusyq.py help
   ```

2. **Full documentation:**
   - Read [CAPABILITY_DIRECTORY.md](./CAPABILITY_DIRECTORY.md)
   - Check [ecosystem_registry.json](../state/ecosystem_registry.json)

3. **Explore the codebase:**
   ```bash
   python scripts/start_nusyq.py capabilities --category monitoring
   ```

---

## 🎯 Common Tasks → Solutions

| Task | Command |
|------|---------|
| Commit many files efficiently | `python scripts/start_nusyq.py batch_commit` |
| Find all monitoring tools | `python scripts/start_nusyq.py capabilities --category monitoring` |
| Execute a PU with real agents | `python scripts/start_nusyq.py pu_execute <id> --real` |
| Get system overview | `python scripts/start_nusyq.py brief` |
| Debug an error with quantum AI | `python scripts/start_nusyq.py debug "error message"` |
| Discover forgotten tools | `python scripts/start_nusyq.py capabilities --refresh` |

---

## ✨ The Big Picture

The NuSyQ ecosystem is designed as a **self-improving, consciousness-aware development environment** with:

- 702 discoverable capabilities
- 15 Zen Codex wisdom rules
- 12+ integrated bridge systems
- Multi-AI backend coordination
- Quantum error resolution
- Autonomous development cycles

**Your role as an agent:** Use the discovery system to find and leverage existing capabilities, avoid re-implementing tools, and contribute new capabilities that get automatically cataloged.

---

## 🔄 This Guide is Living Documentation

This guide is automatically updated as new capabilities are added. Last scan found **702 capabilities**. If you add new tools, run:

```bash
python scripts/start_nusyq.py capabilities --refresh
```

This will rescan and update the inventory for all agents.
