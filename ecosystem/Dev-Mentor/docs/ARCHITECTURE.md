# Terminal Depths Architecture

## Overview
Terminal Depths is a distributed AI-native RPG system. It consists of a virtual terminal environment where players (and AI agents) interact with a simulated world through commands.

## System Diagram
```
[ Player / AI Agent ] 
      │
      ▼
[ MCP / REST API ] <────> [ Serena Memory ]
      │
      ▼
[ FastAPI Backend ] <───> [ SQLite DB ]
      │
      ▼
[ Game Engine ] <───────> [ VFS (Filesystem) ]
      │
      ▼
[ Game State ] <────────> [ Story Engine ]
```

## Core Components
- **Command Registry**: Located in `app/game_engine/commands.py`. Dispatches input strings to method calls.
- **Virtual Filesystem (VFS)**: Located in `app/game_engine/filesystem.py`. A nested dictionary representing the in-game directory structure.
- **Game State**: Located in `app/game_engine/gamestate.py`. Manages session persistence, XP, levels, and flags.
- **Story Engine**: Located in `app/game_engine/story.py`. Manages narrative progression through "story beats".
- **MCP Server**: Located in `mcp/server.py`. Bridges LLM tool-calling capabilities to game commands.

## Extension Patterns
### Adding a Command
1. Define `_cmd_<name>(self, args)` in `CommandRegistry`.
2. Return a list of stylized dictionaries: `[{"s": "text", "t": "type"}]`.
3. Register the command in the `aliases` dictionary.

### Adding VFS Files
1. Edit the `VFS` dictionary in `filesystem.py`.
2. Paths are nested dictionaries; leaf nodes with `content` keys are files.

## Data Flow
1. **Request**: A client sends a POST to `/api/game/command`.
2. **Dispatch**: `CommandRegistry` finds the corresponding method.
3. **Execution**: The method modifies `GameState` and/or interacts with `VFS`.
4. **Response**: Stylized output is returned to the client.
