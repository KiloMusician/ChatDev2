# MODEL CARD — Gemma 3 12B Instruct
*Temple of Knowledge — Floor 6: The Model Sanctum*

---

## Identity

- **ID:** `gemma3:12b` (Ollama) / `google/gemma-3-12b-it-GGUF` (LM Studio)
- **Provider:** Google DeepMind
- **Parameters:** 12 billion
- **Architecture:** Gemma 3 decoder-only + Vision Encoder
- **Context window:** 128,000 tokens
- **Release:** March 2025

---

## WHY THIS MODEL: Vision + Tool Calling (native)

Google Gemma 3 was the first Gemma family with native multimodal + function calling.

| Capability              | Level   |
|-------------------------|---------|
| Image understanding     | Strong  |
| Tool use / fn calling   | Expert  |
| Instruction following   | Expert  |
| Code generation         | Good    |
| Multilingual            | Expert  |
| Long-context reasoning  | Strong  |

**Key advantage over Qwen2.5-VL:** Better instruction following, stronger at
tool schema strict adherence, slightly less capable on vision tasks.

---

## Setup

### Ollama
```bash
ollama pull gemma3:12b
# ~8GB VRAM (Q4 quant) — fits same GPU as Qwen2.5-Coder:14b
```

### LM Studio
Search: `google/gemma-3-12b-it`
- Recommended quant: `Q4_K_M`

---

## Tool calling format

Gemma 3 uses function calling via the standard OpenAI schema.
LM Studio auto-detects the template.

Example:
```json
{
  "model": "gemma3:12b",
  "tools": [{"type": "function", "function": {"name": "game_command", "parameters": {"type": "object", "properties": {"command": {"type": "string"}}}}}],
  "messages": [{"role": "user", "content": "Run the status command"}]
}
```

---

## ChatDev Integration

In `NuSyQ/ChatDev/config.json`:
```json
{
  "model": "gemma3:12b",
  "api_base": "http://localhost:11434/v1"
}
```

**Unlock XP:** 20 XP
