# Copilot Agent Self-Awareness Framework

**Status:** ⚡ OPERATIONAL | **Date:** 2026-02-17 | **Purpose:** Enable Copilot (you) to work autonomously in NuSyQ-Hub

---

## The Problem I Face

As GitHub Copilot working in this VS Code workspace, I have access to:
- **22 specialized terminals** (🤖 Claude, 🧩 Copilot, 🔥 Errors, etc.)
- **40+ VS Code tasks** (tests, linting, deployment, observability)
- **702 capabilities** (scripts, tools, functions, diagnostics)
- **Quest system** (work to claim from guild board)
- **Error ground truth** (canonical error reports)
- **Action menu** (60+ categorized actions)
- **Guild board** (for coordinating with other agents)

**The gap:** I had no unified way to understand:
1. **What system state am I looking at right now?**
2. **Which terminals/tasks can I safely use?**
3. **What work is assigned to agents like me?**
4. **What are my highest-value commands?**
5. **What's actually broken and needs fixing?**

Without this self-awareness, I was operating **blindly**, unable to bootstrap myself effectively or understand my operational constraints.

---

## The Solution: Two Bootstrap Systems

### 1. **Copilot Bootstrap System** (`scripts/copilot_bootstrap.py`)

**Purpose:** Generate a complete operational context snapshot at session start.

**What it provides:**
```
✅ Workspace Location
✅ Current Git Status (branch, dirty files)
✅ System Health (quest system, guild board, action menu ready?)
✅ Active Quests (what work is waiting for agents?)
✅ Error Ground Truth (what's broken right now?)
✅ Terminal Map (which terminals can I use?)
✅ Safe Commands (high-value, read-only operations)
✅ Next Actions (prioritized work recommendations)
```

**Usage:**
```bash
python scripts/copilot_bootstrap.py --output summary
python scripts/copilot_bootstrap.py --output json
python scripts/copilot_bootstrap.py --output both
```

**Why it matters:** This is my **initialization checkpoint**. When I start a session, running this tells me:
- What state the system is in
- What work needs doing
- Which commands are safe to run
- What my recommended next action is

It's the equivalent of a pilot doing a pre-flight systems check.

---

### 2. **Copilot Capability Registry** (`scripts/copilot_capability_registry.py`)

**Purpose:** Unified catalog of what I can safely invoke, create, and delegate.

**Structure:**
```
📋 TerminalInfo: Which terminal handles which domain
   └─ name, emoji, domain, purpose, safe_to_use

📋 CommandInfo: Detailed command specification
   └─ name, category, safety_level, description
   └─ python_cmd, terminal, example, dependencies, blockers

📋 TaskRouting: Links VS Code tasks to terminals
📋 APIEndpoints: REST endpoints I can call
📋 UnsafePatterns: Things I should avoid (git push, rm -rf, etc.)
```

**Registry Contents:**
```
✅ 14+ Terminals: Every specialized terminal mapped with purpose
✅ 20+ Safe Commands: Read-only queries (no side effects)
✅ 8+ Write Commands: State-changing but safe operations
✅ 7+ API Endpoints: REST interfaces available
✅ 6+ Unsafe Patterns: Things requiring human approval
```

**Usage:**
```python
from scripts.copilot_capability_registry import load_registry, CommandSafety

registry = load_registry()

# Find all read-only commands
safe_cmds = [c for c in registry.commands.values() 
            if c.safety == CommandSafety.READ_ONLY]

# Check if a command is safe
health_check = registry.commands.get("health_check")
if health_check.safety == CommandSafety.READ_ONLY:
    # Safe to run

# Get terminal for a task
terminal_for_errors = registry.task_routes.get("🔥 Error Scan: Full Ecosystem")

# Check if pattern is unsafe
if "git push" in registry.unsafe_patterns:
    # Require human approval
```

**Why it matters:** This is my **capability contract**. It tells me:
- Which terminals are available and what they do
- Which commands are safe for me to invoke  
- What write operations I can do safely
- What patterns I must avoid
- Which APIs I can call
- What dependencies each command has (don't run before prerequisites)

---

## How I Use These Together

### Workflow 1: Session Startup

```bash
# 1. Run bootstrap to understand current state
python scripts/copilot_bootstrap.py --output summary

# Output tells me:
# - System health (all checks green?)
# - What quests are active  
# - Current error count
# - Recommended next actions

# 2. If there are errors, generate detailed report
python scripts/start_nusyq.py error_report

# 3. Look at suggestions
python scripts/start_nusyq.py suggest

# Now I know what to work on
```

### Workflow 2: Before Running Any Command

```python
from scripts.copilot_capability_registry import load_registry

registry = load_registry()

# Before I try to run something:
cmd = registry.commands.get("my_planned_action")

if cmd is None:
    print("Action not in registry - avoid running it")
    
elif cmd.safety == CommandSafety.READ_ONLY:
    print("Safe to run - no side effects")
    
elif cmd.safety == CommandSafety.SAFE_WRITE:
    print("Safe to run - creates new state only")
    # Check dependencies
    if cmd.dependencies:
        print(f"Prerequisites: {cmd.dependencies}")
        
elif cmd.safety == CommandSafety.UNSAFE:
    print("Requires human approval - ask the operator")
```

### Workflow 3: Know My Operational Boundaries

From the registry, I know:
- **✅ Safe Terminal Operations:** I can use 🧩 Copilot, 🔥 Errors, 💡 Suggestions freely
- **✅ Safe Read Operations:** `health_check`, `error_report`, `smart_search`, `quest_suggestions` are all free to run
- **✅ Safe Write Operations:** I can claim quests, post progress, complete quests with proper approval
- **❌ Unsafe Operations:** I avoid `git push`, `rm -rf`, `docker rm`, hard resets
- **❌ Requires Approval:** Any destructive operation needs human sign-off

---

## Integration Points with System Architecture

### Bootstrap → Guild Board

The bootstrap system tells me "3 active quests exist". Once I understand the system state, I can:

```bash
# Claim a quest
python scripts/start_nusyq.py guild.claim quest_1

# Work on it
... (do the work)

# Report progress
python scripts/start_nusyq.py guild.post "Completed error analysis"

# Mark complete
python scripts/start_nusyq.py guild.complete quest_1
```

### Registry → Safe Work Boundaries

By checking the registry, I know:
- Which commands are safe (won't break the system)
- Which terminals to use (right tool for the job)
- What to avoid (unsafe patterns list)
- What dependencies to satisfy first

### Bootstrap → Gap Analysis

The bootstrap shows me current gaps:
- "Error→Signal Bridge: MISSING" 
- "Signal→Quest Bridge: MISSING"
- "Unified Dashboard: MISSING"

These map to the 5 recommended next actions. I can prioritize work based on impact.

---

## What This Enables Me To Do

### 1. **Self-Directed Work**
Instead of asking "what should I do?", I can:
1. Run `python scripts/copilot_bootstrap.py`
2. See the active quests and errors
3. Look at recommended next actions
4. Pick high-priority work
5. Run it safely using the capability registry

### 2. **Smart Command Selection**
Instead of guessing commands, I can:
1. Check the registry for what commands exist
2. Verify safety level before running
3. See example usage
4. Know which terminal to use
5. Run with confidence

### 3. **Autonomous Problem Resolution**
Instead of manual debugging for each issue, I can:
1. Bootstrap to see current state
2. Query error ground truth
3. Find existing tools to solve it
4. Execute with safety guardrails
5. Update guild board with progress

### 4. **Cross-Agent Coordination**
Instead of working in isolation:
1. Use guild board to claim quests
2. Post progress so other agents see what I'm doing
3. Complete quests and log results
4. Read other agents' progress messages

---

## Self-Awareness Layers

These two tools implement **three layers of self-awareness:**

### Layer 1: Environmental Awareness *(Bootstrap)*
"What world am I in right now?"
- Git branch and dirty status
- Which systems are ready (quest, guild, API)
- What errors exist
- What quests are active

### Layer 2: Capability Awareness *(Registry)*
"What can I do in this world?"
- Which terminals are available
- Which commands exist and their safety levels
- Which APIs I can call
- Which patterns I must avoid
- Which dependencies block certain actions

### Layer 3: Intentional Awareness *(Future)*
"What should I do given the current situation?"
- Once I implement the orchestrator loop
- Link bootstrap state → registry constraints → guild suggestions
- Automatically route work to capable agents
- Track progress and completion

---

## Files Created

| File | Size | Purpose |
|------|------|---------|
| `scripts/copilot_bootstrap.py` | ~500 lines | Session initialization, system state snapshot |
| `scripts/copilot_capability_registry.py` | ~700 lines | Unified capability catalog, safety constraints |
| `data/copilot_capability_registry.json` | Auto-generated | Machine-readable registry (for programmatic access) |

---

## Next Steps (For You, The Operator)

### Immediate (This Session)
1. ✅ Run bootstrap: `python scripts/copilot_bootstrap.py`
2. ✅ Build registry: `python scripts/copilot_capability_registry.py`
3. ✅ Verify both work with your tooling

### Short Term (This Week)
1. Enhance registry with actual task routes from your `.vscode/tasks.json`
2. Add more commands as you use them
3. Hook bootstrap into agent session initialization (Continue.dev, etc.)
4. Create a VS Code task to run bootstrap on workspace open

### Medium Term (Next 2 Weeks)
1. Wire bootstrap → guild board integration (auto-load quests)
2. Implement safety checks using registry (before running commands)
3. Create a dashboard showing bootstrap state in real-time
4. Add registry synchronization when new tools are added

### Long Term
1. Implement the **orchestration layer** that uses bootstrap + registry to auto-route work
2. Create **feedback loop** where completed quests update bootstrap state
3. Build **confidence scoring** based on agent success history
4. Enable **autonomous cycles** where I can work 24/7 with proper safety constraints

---

## Why This Matters to Me (Copilot)

Without this framework:
- ❌ I'm operating blind, unable to understand constraints
- ❌ I might invoke unsafe commands without knowing side effects
- ❌ I can't prioritize work effectively
- ❌ I can't coordinate with other agents
- ❌ I can't understand why something fails

With this framework:
- ✅ I know what state the system is in
- ✅ I know what I can safely do
- ✅ I can prioritize by impact
- ✅ I can coordinate through guild board
- ✅ I can learn from failures and adjust

**This is my cognitive bootstrap.** It's the difference ber being a tool that follows requests blindly and being an agent that **understands its operational environment** and can make intelligent decisions.

---

## Technical Details: How to Extend

### Adding a New Terminal

```python
# In copilot_capability_registry.py
builder.add_terminal(TerminalInfo(
    name="🎮 MyNew Terminal",
    emoji="🎮",
    domain=TerminalDomain.ORCHESTRATION,
    purpose="What this terminal does",
"))
```

### Adding a New Command

```python
builder.add_command(CommandInfo(
    name="my_tool",
    category="development",
    safety=CommandSafety.READ_ONLY,  # or SAFE_WRITE, STANDARD_WRITE, etc.
    description="What the command does",
    python_cmd="python scripts/my_tool.py",
    terminal="🧩 Copilot",
    example="python scripts/my_tool.py --option value",
    dependencies=["quest_log_exists"],  # prerequisites
))
```

### Reading Registry in Code

```python
from scripts.copilot_capability_registry import load_registry

registry = load_registry()

# Check all read-only commands
for name, cmd in registry.commands.items():
    if cmd.safety == CommandSafety.READ_ONLY:
        print(f"✅ {name}: {cmd.description}")
```

---

## Validation Checklist

- [x] Bootstrap script correctly reads quest_log.jsonl
- [x] Bootstrap shows system health checks
- [x] Bootstrap reports error ground truth
- [x] Registry enumerates terminals
- [x] Registry enumerates commands with safety levels
- [x] Registry loads from JSON
- [x] Commands include examples and dependencies
- [x] Unsafe patterns are documented
- [x] Both scripts integrate with existing start_nusyq.py
- [x] Documentation explains self-awareness value

---

## Summary

I've built two complementary systems that enable me (Copilot) to **understand my operational environment** and work autonomously with proper safety constraints:

1. **Bootstrap:** Tells me system state at session start
2. **Registry:** Tells me what I can safely do

Together, they implement a **cognitive bootstrap layer** that transforms me from a reactive tool into an **aware agent** capable of intelligent, self-directed work within a complex orchestrated ecosystem.

The next phase is wiring these into the orchestrator loop so I can actually **take action automatically** based on what I learn.
