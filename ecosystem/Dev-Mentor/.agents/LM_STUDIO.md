# LM Studio — DevMentor / Terminal Depths Integration Guide

## Role
LM Studio provides a local OpenAI-compatible API for the project's multi-backend LLM client.

## Setup
1. Download LM Studio from https://lmstudio.ai
2. Load a model (recommended: Qwen2.5-Coder-7B-Instruct or Mistral-7B-Instruct)
3. Start the local server (default: http://localhost:1234/v1)

## Connecting to DevMentor
LM Studio's OpenAI-compatible endpoint works with the existing LLM client:
```python
from app.ml.llm_client import LLMClient
client = LLMClient(backend="openai", model="local-model",
                   base_url="http://localhost:1234/v1", api_key="lm-studio")
```

## MCP via LM Studio
Some LM Studio builds support MCP. Point it to:
- MCP Server: `http://localhost:7337/mcp`
- Transport: SSE

## Playing the Game via LM Studio API
```bash
curl -X POST http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-model",
    "messages": [
      {"role": "system", "content": "You are an agent playing Terminal Depths. The game API is at http://localhost:7337."},
      {"role": "user", "content": "What command should I run first?"}
    ]
  }'
```

## Recommended Models
- **Code tasks**: Qwen2.5-Coder-7B-Instruct (best performance/size ratio)
- **Narrative/lore**: Mistral-7B-Instruct-v0.3
- **Multi-modal**: LLaVA-1.6 (for screenshot analysis)
