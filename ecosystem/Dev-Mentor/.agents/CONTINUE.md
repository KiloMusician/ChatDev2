# Continue.dev — DevMentor / Terminal Depths Integration Guide

## Current Config
`.vscode/continue/config.json` is pre-configured for this project.
It points to Ollama as the default model and includes DevMentor context providers.

## Setup
1. Install Continue extension in VS Code
2. Config is already at `.vscode/continue/config.json`
3. Run the game server: `python -m cli.devmentor serve --host 0.0.0.0 --port 7337`

## Context Providers for This Project
Add to `.vscode/continue/config.json`:
```json
{
  "contextProviders": [
    {"name": "file", "params": {}},
    {"name": "codebase", "params": {"nFinal": 25}},
    {"name": "docs", "params": {"startUrl": "http://localhost:7337/docs"}},
    {"name": "url", "params": {"staticUrls": ["http://localhost:7337/api/mcp/tools"]}}
  ]
}
```

## Slash Commands
Add custom slash commands for game development:
```json
{
  "slashCommands": [
    {
      "name": "addcmd",
      "description": "Add a new Terminal Depths game command",
      "prompt": "Read CONTEXT.md first. Add a new game command called {input} to commands.py following the established patterns. Register in dispatch, create man page."
    },
    {
      "name": "addlore",
      "description": "Add VFS lore content",
      "prompt": "Add new lore content to filesystem.py for path /opt/library/{input}. 10-15 lines of cyberpunk narrative."
    }
  ]
}
```

## Best Prompts in VS Code with Continue
- `@CONTEXT.md how do I add a new faction?`
- `@commands.py explain the _cmd_hive method`  
- `@filesystem.py add a new VFS file at /opt/profiles/herald.txt with Herald's backstory`
- Highlight a method → `cmd+shift+R` → "Refactor this to handle edge cases"

## Model Recommendations
- Code completion: `qwen2.5-coder:7b` (fast, accurate for Python)
- Chat/explanation: `llama3.1:8b`
- Architecture: `deepseek-coder-v2:16b`
