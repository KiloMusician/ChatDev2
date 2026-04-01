# VS Code Integration

Quick access to NuSyQ development commands from VS Code command palette.

Control-plane note:

- the canonical IDE cockpit is `src/vscode_mediator_extension`
- this `src/vscode_integration` layer is still useful for command-palette and
  automation entry points
- the small `src/integration/vscode_extension` package remains a focused ChatDev
  launcher/log surface rather than the primary operator dashboard

## Installation

The integration is already configured in `.vscode/extensions.json` with
recommended extensions.

## Command Palette Commands

Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) to open the command palette, then
type any of:

### Task Management

- **NuSyQ: List Tasks** - Show all open development tasks
  - Keybinding: `Ctrl+Shift+T`
- **NuSyQ: Add Task** - Create a new task

### System State

- **NuSyQ: System Snapshot** - Generate tripartite workspace state snapshot
  - Keybinding: `Ctrl+Shift+S`

### Testing & Analysis

- **NuSyQ: Run Tests** - Execute test suite
- **NuSyQ: Analyze Current File** - Analyze current file with AI system

### Quest System

- **NuSyQ: List Active Quests** - Show guild active quests
  - Keybinding: `Ctrl+Shift+L`

### System Operations

- **NuSyQ: Get Suggestions** - Get actionable system improvement suggestions
- **NuSyQ: Heal System** - Run system healing and diagnostics

## Keybindings

| Command         | Keybinding     |
| --------------- | -------------- |
| List Tasks      | `Ctrl+Shift+T` |
| System Snapshot | `Ctrl+Shift+S` |
| Active Quests   | `Ctrl+Shift+L` |

## Execution

Commands are executed through `scripts/start_nusyq.py` with the appropriate
action:

```bash
# Example: list tasks
python scripts/start_nusyq.py task list

# Example: add task
python scripts/start_nusyq.py task add "Task description"

# Example: get system snapshot
python scripts/start_nusyq.py snapshot
```

## Configuration

The VS Code integration is defined in:

- `.vscode/extensions.json` - Extension recommendations and command
  configuration
- `.vscode/nusyq-commands.json` - Generated command palette configuration

## Module

The integration is implemented in
`src/vscode_integration/extension_commands.py`:

```python
from src.vscode_integration import VSCodeIntegration

vscode = VSCodeIntegration()
vscode.execute_command("nusyq.task.list")
```

## Usage from CLI

You can also execute commands from the terminal:

```bash
# List commands
python -m src.vscode_integration.extension_commands

# Execute a command
python -m src.vscode_integration.extension_commands nusyq.task.list

# Export configuration
python -m src.vscode_integration.extension_commands export .vscode/nusyq-commands.json
```
