# NuSyQ Quick Reference - VS Code & Tasks

## 🚀 Quick Commands

### From Command Palette (Ctrl+Shift+P)

```
NuSyQ: List Tasks              (Ctrl+Shift+T)
NuSyQ: System Snapshot         (Ctrl+Shift+S)
NuSyQ: List Active Quests      (Ctrl+Shift+L)
NuSyQ: Add Task
NuSyQ: Run Tests
NuSyQ: Analyze Current File
NuSyQ: Get Suggestions
NuSyQ: Heal System
```

### From Terminal

```bash
# Task management
python scripts/start_nusyq.py task list
python scripts/start_nusyq.py task add "Description"
python scripts/start_nusyq.py task done task_1

# System operations
python scripts/start_nusyq.py snapshot
python scripts/start_nusyq.py suggest
python scripts/start_nusyq.py test
python scripts/start_nusyq.py heal
```

## 📋 Task Queue

**Storage:** `data/tasks.json`

**Task Structure:**

```json
{
  "id": "task_1",
  "title": "Implement REST API",
  "status": "open|completed",
  "created": "2025-12-30T14:53:09.279677",
  "completed": "2025-12-30T14:54:03.338191"
}
```

**Workflow:**

1. Add: `task add "What to do"`
2. List: `task list` (shows open only)
3. Complete: `task done task_1`
4. Data persists in JSON file

## 🎮 VS Code Integration

**Module:** `src/vscode_integration/extension_commands.py`

**Features:**

- 8 command palette commands mapped to NuSyQ actions
- 3 keyboard shortcuts (Ctrl+Shift+T/S/L)
- Configuration export to `.vscode/nusyq-commands.json`
- Full integration with system tracing

**Usage:**

```python
from src.vscode_integration import VSCodeIntegration

vscode = VSCodeIntegration()
vscode.execute_command("nusyq.task.list")
```

## 💡 Suggest Command

**Purpose:** Get actionable system improvement suggestions

**Checks:**

- ✅ GuildBoard health
- ✅ Git state (uncommitted changes)
- ✅ Test failures
- ✅ Active quests
- ✅ Large files
- ✅ Import health
- ✅ Default suggestions if healthy

**Output:** Top 5 prioritized suggestions

## 🔍 Available Actions

```
task              Add, list, complete tasks
snapshot          System state snapshot
suggest           Actionable suggestions
test              Run test suite
analyze           AI analysis of file
review            Code review
debug             Debug issues
heal              System healing
guild_*           Quest system commands
quest_*           Quest-related operations
```

## 🎯 Keyboard Shortcuts

| Shortcut     | Command    | Action                  |
| ------------ | ---------- | ----------------------- |
| Ctrl+Shift+T | task.list  | Show open tasks         |
| Ctrl+Shift+S | snapshot   | Generate state snapshot |
| Ctrl+Shift+L | quest.list | Show active quests      |

## 📦 Configuration Files

- `.vscode/extensions.json` - Extension recommendations & commands
- `.vscode/nusyq-commands.json` - Generated command config (auto)
- `.vscode/settings.json` - VS Code workspace settings
- `data/tasks.json` - Task queue storage (auto)

## 🚀 Getting Started

1. **Open Command Palette:** Ctrl+Shift+P
2. **Type:** "NuSyQ: " to see all commands
3. **Use shortcuts:** Ctrl+Shift+T for tasks
4. **Or terminal:** `python scripts/start_nusyq.py task list`

---

**Last Updated:** 2025-12-30 **Status:** ✅ Production Ready
