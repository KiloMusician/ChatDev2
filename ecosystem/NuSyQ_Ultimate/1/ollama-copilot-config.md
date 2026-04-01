# Configuring VS Code Copilot with Ollama Models

## Overview
This guide explains how to configure GitHub Copilot and other VS Code AI extensions to work with local Ollama models as alternative agents.

## ⚠️ Current Limitations

**GitHub Copilot** does not natively support custom model backends. It uses GitHub's proprietary infrastructure. However, there are several workarounds:

### Option 1: Continue.dev Extension (Recommended)
[Continue](https://continue.dev/) is an open-source AI coding assistant that supports Ollama.

**Installation:**
```bash
# Install Continue extension in VS Code
code --install-extension Continue.continue
```

**Configuration** (`.continue/config.json`):
```json
{
  "models": [
    {
      "title": "Qwen2.5 Coder 14B",
      "provider": "ollama",
      "model": "qwen2.5-coder:14b",
      "apiBase": "http://localhost:11434"
    },
    {
      "title": "Qwen2.5 Coder 7B (Fast)",
      "provider": "ollama",
      "model": "qwen2.5-coder:7b",
      "apiBase": "http://localhost:11434"
    },
    {
      "title": "CodeLlama 7B",
      "provider": "ollama",
      "model": "codellama:7b",
      "apiBase": "http://localhost:11434"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Fast Autocomplete",
    "provider": "ollama",
    "model": "qwen2.5-coder:7b"
  },
  "embeddingsProvider": {
    "provider": "ollama",
    "model": "nomic-embed-text"
  }
}
```

### Option 2: Twinny Extension
[Twinny](https://marketplace.visualstudio.com/items?itemName=rjmacarthy.twinny) - AI code completion with Ollama support.

**Installation:**
```bash
code --install-extension rjmacarthy.twinny
```

**VS Code Settings:**
```json
{
  "twinny.apiProvider": "ollama",
  "twinny.ollamaApiUrl": "http://localhost:11434",
  "twinny.fimModel": "qwen2.5-coder:7b",
  "twinny.chatModel": "qwen2.5-coder:14b"
}
```

### Option 3: Codeium (Supports Custom Endpoints)
Codeium can be configured to use custom inference endpoints.

**Installation:**
```bash
code --install-extension Codeium.codeium
```

### Option 4: Ollama Copilot (Community Extension)
Search for "Ollama" in VS Code extensions marketplace for community-developed integrations.

## Recommended Setup for NuSyQ

### 1. Install Continue.dev
```powershell
# Install Continue extension
code --install-extension Continue.continue

# Install required Ollama models
ollama pull qwen2.5-coder:14b
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text
```

### 2. Configure Continue for NuSyQ
Create `~/.continue/config.json`:

```json
{
  "models": [
    {
      "title": "🚀 Qwen2.5 Coder 14B (Primary)",
      "provider": "ollama",
      "model": "qwen2.5-coder:14b",
      "apiBase": "http://localhost:11434",
      "contextLength": 32768
    },
    {
      "title": "⚡ Qwen2.5 Coder 7B (Fast)",
      "provider": "ollama",
      "model": "qwen2.5-coder:7b",
      "apiBase": "http://localhost:11434",
      "contextLength": 32768
    },
    {
      "title": "🧠 Gemma2 9B (Reasoning)",
      "provider": "ollama",
      "model": "gemma2:9b",
      "apiBase": "http://localhost:11434"
    },
    {
      "title": "💡 CodeLlama 7B (Code Specialist)",
      "provider": "ollama",
      "model": "codellama:7b",
      "apiBase": "http://localhost:11434"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Autocomplete",
    "provider": "ollama",
    "model": "qwen2.5-coder:7b",
    "apiBase": "http://localhost:11434"
  },
  "embeddingsProvider": {
    "provider": "ollama",
    "model": "nomic-embed-text",
    "apiBase": "http://localhost:11434"
  },
  "reranker": {
    "name": "llm",
    "params": {
      "modelTitle": "Qwen2.5 Coder 7B (Fast)"
    }
  },
  "contextProviders": [
    {
      "name": "code",
      "params": {}
    },
    {
      "name": "docs",
      "params": {}
    },
    {
      "name": "diff",
      "params": {}
    },
    {
      "name": "terminal",
      "params": {}
    },
    {
      "name": "problems",
      "params": {}
    },
    {
      "name": "folder",
      "params": {}
    },
    {
      "name": "codebase",
      "params": {}
    }
  ],
  "slashCommands": [
    {
      "name": "edit",
      "description": "Edit selected code"
    },
    {
      "name": "comment",
      "description": "Add comments to code"
    },
    {
      "name": "share",
      "description": "Export conversation"
    },
    {
      "name": "cmd",
      "description": "Generate shell command"
    },
    {
      "name": "commit",
      "description": "Generate commit message"
    }
  ]
}
```

### 3. Update VS Code Settings
Add to `.vscode/settings.json`:

```json
{
  "continue.telemetryEnabled": false,
  "continue.enableTabAutocomplete": true,
  "continue.manuallyPassedConfiguration": {
    "allowAnonymousTelemetry": false
  },

  // Keep existing AI extensions active
  "github.copilot.enable": {
    "*": true,
    "yaml": true,
    "markdown": true
  },

  // Claude Code remains primary
  "anthropic.claude-code.autoShowChatOnStart": false
}
```

## Usage Patterns

### Continue.dev Workflow:
1. **Inline Code Completion**: Press `Tab` to accept suggestions from `qwen2.5-coder:7b`
2. **Chat Interface**: `Ctrl+L` (or `Cmd+L` on Mac) to open chat
3. **Edit Selection**: Highlight code → Right-click → "Continue: Edit"
4. **Code Explanation**: `/explain` in chat
5. **Generate Tests**: `/test` command
6. **Generate Docs**: `/comment` command

### Multi-AI Strategy:
- **Claude Code**: Complex architecture, design decisions, code reviews
- **Continue (Ollama)**: Fast code completion, refactoring, documentation
- **GitHub Copilot**: Additional suggestions, pattern matching
- **ChatDev (Ollama)**: Full software project generation

## Performance Optimization

### Model Selection by Task:
- **Autocomplete**: `qwen2.5-coder:7b` (fast, sub-second responses)
- **Chat/Refactor**: `qwen2.5-coder:14b` (better quality)
- **Architecture**: `gemma2:9b` (reasoning-focused)
- **Code Review**: `qwen2.5-coder:14b` or Claude Code

### Hardware Considerations:
- **8GB VRAM**: Use 7B models exclusively
- **12GB VRAM**: Mix of 7B (autocomplete) + 14B (chat)
- **16GB+ VRAM**: Use 14B+ models freely
- **CPU Only**: Stick to 7B models, expect slower inference

## Integration with NuSyQ MCP Server

The MCP server can coordinate between all AI systems:

```python
# Example: Query multiple models for consensus
from mcp_server import NuSyQMCPServer

server = NuSyQMCPServer()

# Get suggestions from multiple models
models = ["qwen2.5-coder:14b", "codellama:7b", "gemma2:9b"]
prompt = "Optimize this database query: ..."

results = [
    server._ollama_query({"model": m, "prompt": prompt})
    for m in models
]

# Aggregate responses for best answer
```

## Troubleshooting

### Continue.dev Not Connecting:
1. Verify Ollama is running: `ollama list`
2. Check endpoint: `curl http://localhost:11434/api/tags`
3. Restart VS Code
4. Check Continue logs: `Ctrl+Shift+P` → "Continue: Show Logs"

### Slow Performance:
1. Use smaller models for autocomplete (7B)
2. Reduce context length in config
3. Enable GPU acceleration if available
4. Close unused AI extensions

### Model Not Found:
```bash
# Pull missing models
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5-coder:14b
ollama pull nomic-embed-text
```

## Recommended Extensions Stack

**Primary AI Coding (Choose one or combine):**
- ✅ **Continue.dev** - Full Ollama support (Recommended)
- ✅ **Twinny** - Lightweight, Ollama-native
- ⚠️ **GitHub Copilot** - No Ollama support, but works alongside

**Supporting Extensions:**
- **Claude Code** - Primary chat interface
- **Kilo Code** - Additional AI assistance
- **Ollama** - Official Ollama VS Code extension

## Future Integration: GitHub Copilot with Ollama

GitHub is exploring custom model support. Watch these developments:
- Copilot for Business (may allow custom endpoints)
- OpenAI-compatible proxies (redirect Copilot → Ollama)
- Community bridges (experimental)

For now, Continue.dev + Ollama provides the best local AI coding experience.
