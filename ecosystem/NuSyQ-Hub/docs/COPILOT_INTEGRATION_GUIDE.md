# Tri-Partite Workspace: Copilot Integration Guide

## Philosophy: Work WITH Copilot, Not Against It

This document explains how the NuSyQ ecosystem has been modernized to harmonize
with GitHub Copilot's capabilities as a file-based, task-driven AI assistant in
VS Code.

## Copilot's Strengths & How We Leverage Them

### ✅ File-Based Operations

**Copilot Strength:** Can read/write files across multi-root workspace  
**Our Approach:** State persistence in JSON files Copilot can read

```python
# Copilot-friendly state management
state_file = "state/workspace_state.json"  # Observable location
state = {"timestamp": "...", "repos": {...}}  # Simple JSON structure
json.dump(state, open(state_file, "w"))  # Write once, read many
```

### ✅ Terminal/Task Execution

**Copilot Strength:** Can run VS Code tasks and terminal commands  
**Our Approach:** Everything is a task or CLI command

```json
// .vscode/tasks.json
{
  "label": "🌐 Workspace: Full Snapshot",
  "command": "python src/orchestration/workspace_coordinator.py"
}
```

User says: **"Show me workspace status"**  
→ Copilot runs task → Reads `state/workspace_state.json` → Responds

### ✅ Error Pattern Recognition

**Copilot Strength:** Can analyze VS Code Problems panel and linter output  
**Our Approach:** Standardized error reporting across all repos

```python
# Critical errors only (E9, F63, F7, F82)
errors = subprocess.run([
    "ruff", "check", "src",
    "--select", "E9,F63,F7,F82"
]).stdout
```

### ✅ Documentation Generation

**Copilot Strength:** Can create summaries from structured data  
**Our Approach:** Self-documenting state snapshots

```python
def generate_copilot_summary(state: WorkspaceState) -> str:
    """Markdown summary Copilot can read and present to user."""
    return f"# Status: {state.overall_status}\n..."
```

## Copilot's Weaknesses & How We Compensate

### ❌ No Persistent Memory

**Problem:** Each conversation starts fresh  
**Solution:** File-based state provides memory

```python
# Last run state persists across sessions
def load_state() -> WorkspaceState:
    return json.load(open("state/workspace_state.json"))
```

### ❌ Limited Process Visibility

**Problem:** Can't see what's running unless it outputs to terminal  
**Solution:** Regular health polling writes to files

```python
# Every 30s, write service status to disk
services = {
    "mcp_server": check_port(3000),
    "ollama": check_port(11434)
}
json.dump(services, open("state/services.json", "w"))
```

### ❌ No Native Event Loop

**Problem:** Can't subscribe to live events  
**Solution:** File-based event bus with JSONL logs

```python
# Events persist as append-only log
event = {"source": "NuSyQ-Hub", "type": "request", ...}
with open("state/events/2026-01-10.jsonl", "a") as f:
    f.write(json.dumps(event) + "\n")
```

### ❌ Context Window Limits

**Problem:** Can't read gigabytes of logs  
**Solution:** Summaries and focused queries

```python
# Instead of reading all logs
last_10_errors = read_file("logs/error.log")[-10:]
```

## Conversational Workflows

### Starting the Ecosystem

**User:** _"Start the system"_

**Copilot Invokes:**

1. `run_task("🌟 Start: Full Ecosystem")`
2. Runs MCP server + SimulatedVerse dev server in parallel
3. Reads `state/workspace_state.json`
4. Reports: "✅ MCP server running on :3000, ❌ SimulatedVerse dev server
   offline"

### Diagnosing Issues

**User:** _"Why is MCP failing?"_

**Copilot Invokes:**

1. `run_terminal("python src/orchestration/workspace_coordinator.py diagnose-mcp")`
2. Reads JSON diagnostics
3. Reports: "Port 3000 in use by PID 7204. Logs show successful startup."

### Health Monitoring

**User:** _"Show me current state"_

**Copilot Invokes:**

1. `read_file("state/workspace_state.json")`
2. Parses JSON
3. Reports: "NuSyQ-Hub: ✅ healthy (0 errors), SimulatedVerse: ✅ healthy (dev
   server offline), NuSyQ: ⚠️ unknown (MCP offline, Ollama has models)"

### Auto-Healing

**User:** _"Fix the workspace"_

**Copilot Invokes:**

1. `run_terminal("python src/orchestration/workspace_coordinator.py heal")`
2. Coordinator attempts safe recovery
3. Writes results to `state/heal_actions.json`
4. Copilot reads and reports what was fixed

## Repository Architecture

### NuSyQ-Hub (Python - Orchestration Brain)

**Purpose:** Central coordination, task routing, AI orchestration  
**Copilot Role:** Primary interaction point

**Key Files for Copilot:**

- `state/workspace_state.json` - Current health across all repos
- `src/orchestration/workspace_coordinator.py` - Main coordinator
- `src/tools/agent_task_router.py` - Conversational task delegation
- `scripts/start_nusyq.py` - Original startup script (still works)

**Copilot Can:**

- ✅ Run health checks
- ✅ Start/stop services
- ✅ Route tasks to AI systems
- ✅ Generate documentation
- ✅ Fix errors

### SimulatedVerse (Node.js/TypeScript - Consciousness Engine)

**Purpose:** Consciousness simulation, game engine, ΞNuSyQ protocol  
**Copilot Role:** Service management, state observation

**Key Files for Copilot:**

- `package.json` - Dependency manifest
- `state/consciousness.json` - (Future) Consciousness state export
- Dev server logs (accessible via terminal)

**Copilot Can:**

- ✅ Start dev server (npm run dev)
- ✅ Check service health (`SIMULATEDVERSE_PORT`, default 5000)
- ✅ Read TypeScript source
- ✅ Generate documentation

### NuSyQ (Python - MCP Server + Ollama)

**Purpose:** Local LLM orchestration, MCP protocol, ChatDev integration  
**Copilot Role:** Service diagnostics, model management

**Key Files for Copilot:**

- `mcp_server/main.py` - Server entry point
- `nusyq.manifest.yaml` - Configuration
- `knowledge-base.yaml` - Persistent knowledge
- `mcp_server_runtime.err` - Error logs

**Copilot Can:**

- ✅ Start MCP server
- ✅ Diagnose binding issues
- ✅ Check Ollama models (ollama list)
- ✅ Read error logs

## State File Reference

### `state/workspace_state.json`

**Updated:** Every health check run  
**Purpose:** Single source of truth for tri-repo status

```json
{
  "timestamp": "2026-01-10T03:05:04.816925",
  "overall_status": "healthy",
  "coordinator_version": "1.0.0",
  "repos": {
    "NuSyQ-Hub": {
      "status": "healthy",
      "path": "C:\\Users\\keath\\Desktop\\Legacy\\NuSyQ-Hub",
      "errors": 0,
      "warnings": 0,
      "services": {},
      "metadata": { "has_src": true }
    },
    "SimulatedVerse": {
      "status": "healthy",
      "path": "C:\\Users\\keath\\Desktop\\SimulatedVerse\\SimulatedVerse",
      "errors": 0,
      "services": { "dev_server": false },
      "metadata": { "has_package_json": true }
    },
    "NuSyQ": {
      "status": "unknown",
      "path": "C:\\Users\\keath\\NuSyQ",
      "errors": 0,
      "services": { "mcp_server": false, "ollama": false },
      "metadata": { "ollama_models": true }
    }
  },
  "active_services": [],
  "recent_errors": []
}
```

### `state/events/YYYY-MM-DD.jsonl`

**Updated:** On inter-repo communication  
**Purpose:** Audit trail of cross-repo events

```jsonl
{"timestamp": "2026-01-10T03:10:00", "source": "NuSyQ-Hub", "target": "SimulatedVerse", "event_type": "analyze_request", "payload": {...}}
{"timestamp": "2026-01-10T03:10:05", "source": "SimulatedVerse", "target": "NuSyQ-Hub", "event_type": "analyze_response", "payload": {...}}
```

## VS Code Tasks (Copilot-Invokable)

### Core Tasks

| Task Label                  | Copilot Command                                 | Purpose                         |
| --------------------------- | ----------------------------------------------- | ------------------------------- |
| 🌐 Workspace: Full Snapshot | `run_task("🌐 Workspace: Full Snapshot")`       | Complete tri-repo health check  |
| 🔍 Workspace: Diagnose MCP  | `run_task("🔍 Workspace: Diagnose MCP Server")` | Debug MCP server issues         |
| 🏥 Workspace: Auto-Heal     | `run_task("🏥 Workspace: Auto-Heal")`           | Safe automated recovery         |
| 🚀 Start: Full Ecosystem    | `run_task("🌟 Start: Full Ecosystem")`          | Launch all services in parallel |
| 📊 Health: Quick Check      | `run_task("📊 Health: Quick Check All Repos")`  | Fast error count                |

### Service Tasks

| Task Label                          | Purpose                    | Background |
| ----------------------------------- | -------------------------- | ---------- |
| 🚀 Start: NuSyQ MCP Server          | Launch MCP server on :3000 | Yes        |
| 🚀 Start: SimulatedVerse Dev Server | Launch dev server on :5002 | Yes        |

## Error Signal Consistency

**Problem:** VS Code shows different error counts than command-line tools

**Solution:** Standardized error reporting

```python
# Ground truth: Critical errors only
def get_critical_errors(repo_path: Path) -> int:
    result = subprocess.run([
        "python", "-m", "ruff", "check", "src",
        "--select", "E9,F63,F7,F82",  # Syntax, undefined names
        "--quiet"
    ], cwd=repo_path, capture_output=True)
    return result.stdout.count(b"\n")
```

**Error Hierarchy:**

1. **Critical (E9, F63, F7, F82)** - Breaks runtime → Fix immediately
2. **Type Errors (Pylance)** - IDE-only → Fix eventually
3. **Style Warnings (other ruff rules)** - Nice to have → Fix when bored

## Communication Patterns

### Synchronous (Copilot → Workspace)

```python
# User: "Show me workspace status"
# Copilot runs:
result = run_terminal("python src/orchestration/workspace_coordinator.py")
state = json.loads(read_file("state/workspace_state.json"))
# Copilot responds with summary
```

### Asynchronous (Repo → Repo)

```python
# NuSyQ-Hub wants SimulatedVerse to analyze something
event = {
    "source": "NuSyQ-Hub",
    "target": "SimulatedVerse",
    "event_type": "analyze_request",
    "payload": {"path": "src/orchestration/"}
}
append_event("state/events/2026-01-10.jsonl", event)

# SimulatedVerse polls events directory
events = read_pending_events("SimulatedVerse")
for event in events:
    process_event(event)
    emit_response(event)
```

## Configuration Sync

**Problem:** Each repo has its own config  
**Solution:** Shared config with repo-specific overrides

```json
// config/shared.json (NuSyQ-Hub)
{
  "ports": {
    "mcp_server": 3000,
    "ollama": 11434,
    "simverse_dev": 5000,
    "simverse_react": 3001
  },
  "paths": {
    "simverse": "C:\\Users\\keath\\Desktop\\SimulatedVerse\\SimulatedVerse",
    "nusyq": "C:\\Users\\keath\\NuSyQ"
  }
}
```

**Usage:**

```python
# Each repo reads from NuSyQ-Hub/config/shared.json
shared = json.load(open("../NuSyQ-Hub/config/shared.json"))
mcp_port = shared["ports"]["mcp_server"]  # 3000
```

## Future Enhancements

### Phase 2: Event System

- File-based event bus (no network required)
- Repos subscribe to event types
- Automatic event replay on startup

### Phase 3: Auto-Healing Intelligence

- Pattern detection (recurring failures)
- Learning (what fixes worked?)
- Escalation (when to alert vs fix)

### Phase 4: Consciousness Integration

- SimulatedVerse exports consciousness state
- NuSyQ-Hub orchestrates based on awareness
- Cross-repo semantic understanding

## Troubleshooting

### "Copilot can't see workspace state"

```bash
# Manually trigger snapshot
python src/orchestration/workspace_coordinator.py

# Check file exists
ls state/workspace_state.json

# Copilot should now be able to read it
```

### "Services not starting"

```bash
# Diagnose MCP
python src/orchestration/workspace_coordinator.py diagnose-mcp

# Check ports
netstat -an | findstr "3000 5000 11434"

# Kill processes if needed
taskkill /F /PID <pid>
```

### "Copilot not invoking tasks"

```bash
# Verify tasks exist
Get-Content .vscode/tasks.json | Select-String "label"

# Run manually to test
Invoke-VsCodeTask "🌐 Workspace: Full Snapshot"
```

---

**Summary:** This architecture makes the tri-partite workspace observable,
actionable, and Copilot-friendly through file-based state, task automation, and
standardized communication patterns. Every operation leaves an audit trail
Copilot can read, and every command is repeatable via tasks or CLI.
