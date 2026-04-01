# Live Terminal Routing - Quick Reference

Generated: 2026-03-13T18:40:49.959771

## What This Does

Your terminals are now configured for LIVE OUTPUT ROUTING! Instead of just showing
static banners, they will display actual real-time output from agents and systems.

## How to Use

### Option 1: VSCode Tasks (Recommended)
1. Press `Ctrl+Shift+P` in VSCode
2. Type "Tasks: Run Task"
3. Select one of:
   - "Watch All Agent Terminals" - Claude, Copilot, Codex, ChatDev, Council, Intermediary
   - "Watch All Operational Terminals" - Errors, Suggestions, Tasks, Metrics, etc.
   - "Watch ALL Terminals (Full System)" - Everything at once!

### Option 2: Individual Terminal Watchers
Run any PowerShell watcher directly:
```powershell
pwsh data/terminal_watchers/watch_claude_terminal.ps1
pwsh data/terminal_watchers/watch_errors_terminal.ps1
# etc...
```

### Option 3: Master Python Launcher
```powershell
python scripts/launch_all_terminal_watchers.py
```
This opens all terminals in separate console windows!

### Option 4: Validate Setup
```powershell
python scripts/activate_live_terminal_routing.py --validate
```
Checks routing config, watcher scripts, task entries, and log files.

## Integration with Your Code

Use the terminal integration module in your scripts:

```python
from src.output.terminal_integration import (
    route_to_terminal,
    to_claude,
    to_errors,
    to_tasks,
    route_agent_output,
    setup_terminal_logging
)

# Direct routing
to_claude("Claude is analyzing the codebase...")
to_errors("ERROR: Configuration file not found")
to_tasks("Processing task #42...")

# Context manager for agent sessions
with route_agent_output("Claude"):
    print("This goes to Claude terminal!")
    print("All output is automatically routed")

# Automatic routing via logging
setup_terminal_logging()
logger = logging.getLogger(__name__)
logger.info("This will auto-route to appropriate terminal")
logger.error("Errors go to error terminal automatically")
```

## Terminal Mapping

Agent Terminals:
- 🧠 Claude: Claude Code agent output
- 🧩 Copilot: GitHub Copilot suggestions
- 🧠 Codex: OpenAI Codex transformations
- 🏗️ ChatDev: Multi-agent team coordination
- 🏛️ AI Council: Consensus and voting
- 🔗 Intermediary: Inter-agent communication

Operational Terminals:
- 🔥 Errors: All error output
- 💡 Suggestions: Recommendations and hints
- ✅ Tasks: Task execution and queues
- 🧪 Tests: Pytest output and coverage
- 🎯 Zeta: Autonomous cycles
- 🤖 Agents: General agent coordination
- 📊 Metrics: Health and performance
- ⚡ Anomalies: Unusual events
- 🔮 Future: Planning and roadmap
- 🏠 Main: General output

## Next Steps

1. Run demo: `python src/output/terminal_integration.py`
2. Start watchers: Use VSCode task or master launcher
3. Integrate into your scripts: Add terminal routing calls
4. Watch the magic: See output flowing to correct terminals!

## Log Files Location

All terminal output is logged to:
`/mnt/c/Users/keath/Desktop/Legacy/NuSyQ-Hub/data/terminal_logs/<terminal_name>.log`

## Troubleshooting

- If watchers don't start: Check PowerShell execution policy
- If logs are empty: Ensure scripts are using terminal integration module
- If output not routing: Check keyword matching in TERMINAL_ROUTES

## Architecture

```
Your Python Scripts
    ↓
Terminal Integration Module (terminal_integration.py)
    ↓
Route by keywords/context
    ↓
Write to terminal log files (data/terminal_logs/*.log)
    ↓
PowerShell watchers tail logs (data/terminal_watchers/*.ps1)
    ↓
VSCode terminal windows show live output
```

Now your terminals are ALIVE! 🎉
