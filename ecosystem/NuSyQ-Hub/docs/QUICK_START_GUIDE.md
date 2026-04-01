# 🚀 NuSyQ Tripartite System - Quick Start Guide

**Last Updated:** 2026-01-15
**For:** VS Code Integration v0.2.0

---

## ⚡ Quick Start (30 seconds)

### 1. Open Workspace
```bash
code "C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\NuSyQ-Ecosystem.code-workspace"
```

### 2. Start Services
**In VS Code:**
- Look at bottom-left status bar: `[? ?/6 svc | ☑ ? quests]`
- Click the status bar
- Select **"🚀 Start All Services"**

**Or via command line:**
```bash
python scripts/start_all_critical_services.py start
```

### 3. Verify Services Running
**In VS Code:**
- Status bar should show: `[✓ 5/6 svc | ☑ 42 quests]`
- Press **`Ctrl+Shift+N Ctrl+S`** for detailed status

**Or via command line:**
```bash
python scripts/start_all_critical_services.py status
```

**You're ready!** 🎉

---

## 📋 Essential Keyboard Shortcuts

| Shortcut | Command | Action |
|----------|---------|--------|
| **`Ctrl+Shift+N Ctrl+M`** | Quick Menu | Open NuSyQ quick menu |
| **`Ctrl+Shift+G Ctrl+G`** | Guild Board | Open quest tracking |
| **`Ctrl+Shift+N Ctrl+S`** | Service Status | Show detailed service info |

---

## 🎛️ Status Bar Guide

### Reading the Status Bar

**Format:** `[icon count | icon count]`

**Example:** `[✓ 5/6 svc | ☑ 42 quests]`

**Breakdown:**
- `✓` = Services healthy (green check)
- `⚠` = Some services down (yellow warning)
- `✗` = All services down (red X)
- `5/6 svc` = 5 out of 6 services running
- `42 quests` = 42 active quests in Guild Board

### Status Bar Actions

**Click status bar** → Opens quick menu with:
- 📊 Show Service Status
- ⚔️ Open Guild Board
- 🚀 Start All Services
- 🔄 Refresh Status Bar
- 🏰 Tripartite Status

---

## 🛠️ Critical Services

### Service Overview

| Service | Purpose | Interval |
|---------|---------|----------|
| **MCP Server** | REST API for AI tools | Always on (port 8081) |
| **Multi-AI Orchestrator** | Coordinates 5 AI systems | Continuous |
| **PU Queue Processor** | Processes 253 work units | Every 5 minutes |
| **Guild Board Renderer** | Updates quest board | Every 60 seconds |
| **Cross Ecosystem Sync** | Syncs to SimulatedVerse | Every 5 minutes |
| **Autonomous Monitor** | System health audits | Every 30 minutes |

### Service Commands

**Start all services:**
```bash
python scripts/start_all_critical_services.py start
```

**Check status:**
```bash
python scripts/start_all_critical_services.py status
```

**Start with auto-restart monitoring:**
```bash
python scripts/start_all_critical_services.py monitor
```

**Test MCP Server:**
```bash
curl http://localhost:8081/health
```

---

## 🤖 AI Agent Quick Reference

### Available AI Assistants

| AI | Status | Location | Usage |
|----|--------|----------|-------|
| **Continue.dev** | ✅ Active | Sidebar | Chat, autocomplete, commands |
| **GitHub Copilot** | ✅ Active | Inline | Code suggestions |
| **Ollama** | ✅ Ready | Continue.dev | Local models (Qwen, DeepSeek) |
| **Claude** | ✅ Active | Continue.dev | Cloud model (Sonnet 3.5) |
| **GPT-4** | ✅ Active | Continue.dev | Cloud model |

### Continue.dev Custom Commands

Type these in Continue.dev chat:

- **`/nusyq-analyze`** - Architecture-aware code analysis
- **`/doctrine-check`** - Validate NuSyQ principles
- **`/wire-action`** - Generate action boilerplate

### MCP Server Tools

Available at `http://localhost:8081/`:

1. **`/analyze_repository`** - Analyze codebase structure
2. **`/get_context`** - Retrieve contextual information
3. **`/orchestrate_task`** - Coordinate complex tasks
4. **`/generate_code`** - Generate code snippets
5. **`/generate_tests`** - Generate test cases
6. **`/check_system_health`** - System health status

---

## ⚔️ Guild Board (Quest Tracking)

### Opening Guild Board

**Option 1:** Press **`Ctrl+Shift+G Ctrl+G`**

**Option 2:** Click status bar → "⚔️ Open Guild Board"

**Option 3:** Open file `docs/GUILD_BOARD.md`

### Understanding Quest Status

**Quest Format:**
```markdown
## [Quest Title] - Status

**Difficulty:** ⭐⭐⭐ (3 stars)
**Rewards:** 150 XP, New Integration
**Agent:** claude
**Status:** in_progress
```

**Status Types:**
- `available` - Ready to start
- `in_progress` - Currently working
- `completed` - Finished
- `blocked` - Waiting on dependencies

### Quest Board Updates

- **Auto-renders:** Every 60 seconds
- **Manual render:** Run `python scripts/render_guild_board.py`
- **Quest count:** Shown in status bar (`☑ 42 quests`)

---

## 🏰 Tripartite Workspace

### Repository Structure

**3 Repositories in workspace:**

1. **NuSyQ-Hub** (Primary)
   - Path: `C:\Users\keath\Desktop\Legacy\NuSyQ-Hub`
   - Services: All 6 critical services
   - Role: Central orchestration

2. **SimulatedVerse**
   - Path: `C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse`
   - Services: None (receives syncs)
   - Role: Agent simulation environment

3. **NuSyQ-Root**
   - Path: `C:\Users\keath\Desktop\NuSyQ-Root`
   - Services: None (shared libraries)
   - Role: Core utilities

### Cross-Repo Sync

**Quest Log Sync:**
- Direction: NuSyQ-Hub → SimulatedVerse
- Frequency: Every 5 minutes
- Location: `shared_cultivation/quest_log.jsonl`

**Manual Sync:**
```python
from src.tools.cross_ecosystem_sync import CrossEcosystemSync
sync = CrossEcosystemSync()
sync.sync_quest_logs_to_simverse()
```

---

## 📊 Monitoring & Logs

### Service Logs

**Log Location:** `data/service_logs/`

**View logs:**
```bash
# Orchestrator
tail -f data/service_logs/orchestrator.log

# Autonomous Monitor
tail -f data/service_logs/autonomous_monitor.log

# PU Queue
tail -f data/service_logs/pu_queue.log

# Guild Renderer
tail -f data/service_logs/guild_renderer.log

# Cross Sync
tail -f data/service_logs/cross_sync.log
```

### Service State

**State file:** `state/services/critical_services.json`

**View state:**
```bash
cat state/services/critical_services.json
```

### Health Checks

**MCP Server:**
```bash
curl http://localhost:8081/health
# Expected: {"status": "healthy", "tools": 6}
```

**All Services:**
```bash
python scripts/start_all_critical_services.py status
```

---

## 🔧 Troubleshooting

### Issue: Services not starting

**Check 1: Python available**
```bash
python --version
# Should show Python 3.11+
```

**Check 2: In correct directory**
```bash
pwd
# Should show: C:\Users\keath\Desktop\Legacy\NuSyQ-Hub
```

**Check 3: Start services manually**
```bash
python scripts/start_all_critical_services.py start --no-monitor
```

**Check 4: View error logs**
```bash
tail -n 50 data/service_logs/orchestrator.log
```

### Issue: Status bar shows "?"

**Fix:** Refresh status bar
- Click status bar → "🔄 Refresh Status Bar"
- Or press **`F1`** → type "NuSyQ: Refresh Status Bar"

### Issue: MCP Server shows DOWN

**This is normal!** Thread-based services can't be validated via PID.

**Verify it's running:**
```bash
curl http://localhost:8081/health
```

If no response, restart services:
```bash
python scripts/start_all_critical_services.py start
```

### Issue: Extension commands not working

**Reload VS Code window:**
- Press **`Ctrl+Shift+P`**
- Type "Developer: Reload Window"
- Press Enter

**Or restart VS Code:**
```bash
# Close VS Code, then:
code "C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\NuSyQ-Ecosystem.code-workspace"
```

### Issue: Services crash immediately

**Check for port conflicts:**
```bash
# Check if port 8081 is already in use
netstat -ano | findstr :8081
```

**View crash logs:**
```bash
tail -n 100 data/service_logs/orchestrator.log
```

**Known fixes:**
- Orchestrator crash: Fixed (added persistence loop)
- Autonomous Monitor crash: Fixed (added audit loop)
- Cross Sync crash: Partially fixed (still debugging)

---

## 📚 Documentation

### Essential Docs

1. **`TRIPARTITE_INTEGRATION_COMPLETE.md`** - Complete integration overview
2. **`QUICK_START_GUIDE.md`** - This guide
3. **`GUILD_BOARD.md`** - Quest tracking
4. **`AI_AGENT_INTEGRATION_STATUS.md`** - AI integration details

### Session Reports

5. **`SESSION_VSCODE_INTEGRATION_COMPLETE.md`** - Session 1 (audit + MCP)
6. **`SESSION_SERVICE_FIXES_COMPLETE.md`** - Session 2 (stability)

### Advanced Docs

7. **`VSCODE_EXTENSION_AUDIT.md`** - 200+ extension audit
8. **`CAPABILITY_DIRECTORY.md`** - 763 system capabilities
9. **`CODE_STYLE.md`** - Development standards

---

## 🎯 Common Workflows

### Workflow 1: Start Work Session

```bash
# 1. Open workspace
code "C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\NuSyQ-Ecosystem.code-workspace"

# 2. Start services (in VS Code)
# Click status bar → "🚀 Start All Services"

# 3. Open Guild Board
# Press Ctrl+Shift+G Ctrl+G

# 4. Start coding!
```

### Workflow 2: Check Quest Status

```bash
# 1. Open Guild Board
# Press Ctrl+Shift+G Ctrl+G

# 2. Find your quest
# Search for "[Quest Title]"

# 3. Update quest status
# Edit quest status in Guild Board markdown

# 4. Board auto-renders in 60 seconds
# Or run: python scripts/render_guild_board.py
```

### Workflow 3: Monitor Services

```bash
# 1. Check status bar
# Look at bottom-left: [✓ 5/6 svc | ☑ 42 quests]

# 2. Detailed service info
# Press Ctrl+Shift+N Ctrl+S

# 3. View logs
tail -f data/service_logs/orchestrator.log

# 4. Restart if needed
python scripts/start_all_critical_services.py start
```

### Workflow 4: Use Continue.dev

```bash
# 1. Open Continue.dev sidebar
# Click Continue icon on left sidebar

# 2. Ask a question
# "Analyze the architecture of src/orchestration/"

# 3. Use custom commands
# /nusyq-analyze - Architectural analysis
# /doctrine-check - Principle validation

# 4. Get autocomplete
# Start typing code, Qwen Coder provides suggestions
```

---

## 💡 Pro Tips

### Tip 1: Quick Service Restart
Instead of stopping and starting, just run:
```bash
python scripts/start_all_critical_services.py start
```
It will detect running services and skip them.

### Tip 2: Status Bar as Command Center
The status bar is your mission control. Click it for instant access to all major functions.

### Tip 3: Use Continue.dev Commands
The custom commands are architecture-aware:
- `/nusyq-analyze` knows about your system structure
- `/doctrine-check` validates against NuSyQ principles

### Tip 4: Monitor Quest Count
The quest count in status bar is your progress metric. Watch it decrease as you complete quests!

### Tip 5: Keep Services Running
Services are designed to run continuously. Don't stop them unless necessary. They'll recover from errors automatically.

---

## 🆘 Getting Help

### In VS Code
- Press **`Ctrl+Shift+P`**
- Type "NuSyQ" to see all available commands
- Use **`Ctrl+Shift+N Ctrl+M`** for quick menu

### Documentation
- See `docs/TRIPARTITE_INTEGRATION_COMPLETE.md` for complete overview
- Check `docs/AI_AGENT_INTEGRATION_STATUS.md` for AI details
- Review session reports for troubleshooting examples

### Service Issues
- View logs: `data/service_logs/`
- Check state: `state/services/critical_services.json`
- Run status: `python scripts/start_all_critical_services.py status`

---

## ✅ System Health Checklist

**Use this to verify everything is working:**

- [ ] VS Code workspace opens: `NuSyQ-Ecosystem.code-workspace`
- [ ] Status bar visible: `[? svc | ☑ quests]`
- [ ] 5/6 services running: Click status bar → verify
- [ ] MCP Server responding: `curl http://localhost:8081/health`
- [ ] Guild Board accessible: Press `Ctrl+Shift+G Ctrl+G`
- [ ] Continue.dev working: Open sidebar, send test message
- [ ] Quick menu works: Press `Ctrl+Shift+N Ctrl+M`
- [ ] Service status shows: Press `Ctrl+Shift+N Ctrl+S`

**If all checked ✅ - You're fully operational!** 🎉

---

**Guide Version:** 1.0
**Last Updated:** 2026-01-15
**For Questions:** See `docs/TRIPARTITE_INTEGRATION_COMPLETE.md`

---

*Happy coding with your AI-augmented tripartite system!* 🚀
