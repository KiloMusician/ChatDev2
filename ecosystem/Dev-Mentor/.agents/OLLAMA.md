# Ollama — DevMentor / Terminal Depths Integration Guide

## Role in This Project
Ollama provides the local LLM backend for:
- Serena's convergence queries (`/api/serena/query`)
- Agent reflection and error analysis
- Procedural lore generation
- The multi-backend LLM client (`app/ml/llm_client.py`)

## Connecting Ollama
The project auto-detects Ollama at `http://localhost:11434`.
```bash
# Start Ollama (local)
ollama serve

# Pull recommended models
ollama pull qwen2.5-coder:7b     # Best for code tasks
ollama pull deepseek-coder-v2:16b # Best for architecture
ollama pull llama3.1:8b          # Best for lore/narrative
```

## MCP Connection
```json
{
  "mcpServers": {
    "devmentor": {
      "url": "http://localhost:7337/mcp",
      "transport": "sse"
    }
  }
}
```

## Calling the Game via Ollama
```python
import ollama
import requests

# Get game state
state = requests.get("http://localhost:7337/api/game/state?session_id=ollama").json()

# Ask Ollama to interpret the state
response = ollama.chat(model='llama3.1:8b', messages=[{
    'role': 'user',
    'content': f'You are playing Terminal Depths. Current state: {state}. What command should I run next?'
}])

# Execute the suggested command
cmd = response['message']['content'].strip()
result = requests.post("http://localhost:7337/api/game/command", json={"session_id": "ollama", "command": cmd})
```

## Recommended Models for Each Use Case
| Task | Model |
|------|-------|
| Code generation (add commands) | qwen2.5-coder:7b |
| Lore writing | llama3.1:8b |
| Architecture decisions | deepseek-coder-v2:16b |
| Quick tasks | qwen2.5-coder:1.5b |
| Image analysis | qwen2.5-vl:7b |

## LLM Client API (app/ml/llm_client.py)
```python
from app.ml.llm_client import LLMClient
client = LLMClient(backend="ollama", model="qwen2.5-coder:7b")
response = client.generate("Write a cyberpunk haiku about CHIMERA.")
```
