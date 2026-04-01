# MODEL CARD — Qwen3-VL-8B Instruct
*Temple of Knowledge — Floor 6: The Model Sanctum*

---

## Identity

- **ID:** `qwen3-vl:8b` (Ollama) / `lmstudio-community/Qwen3-VL-8B-Instruct-GGUF` (LM Studio)
- **Provider:** Alibaba Qwen Team
- **Parameters:** 8.7B
- **Architecture:** Qwen3 Transformer + Vision Encoder
- **Context window:** 256,000 tokens (4× larger than Qwen2.5-VL-7B)
- **Release:** 2025 (newer than Qwen2.5-VL)

---

## Capabilities

| Capability              | Level   |
|-------------------------|---------|
| Image understanding     | Strong  |
| Video understanding     | Strong  |
| GUI agent (PC/mobile)   | Strong  |
| Tool use / fn calling   | Strong  |
| Code generation         | Strong  |
| Document analysis       | Strong  |
| Spatial reasoning       | Strong  |

**Tool use confirmed:** Chat template has explicit `{%- if tools %}` block — outputs
`tool_calls` JSON with `function.name` and `function.arguments`. Compatible with
ChatDev's Qwen-family tool schema.

---

## Setup

### Ollama
```bash
ollama pull qwen3-vl:8b
# ~5GB VRAM (Q4_K_M)
```

### LM Studio
Search: `lmstudio-community/Qwen3-VL-8B-Instruct-GGUF`
or: `unsloth/Qwen3-VL-8B-Instruct-GGUF`

---

## Update llm_client.py

```python
# In llm_client.py — replace qwen2.5-coder:14b as default:
OLLAMA_DEFAULT_MODEL = "qwen3-vl:8b"   # vision + tools, 256K ctx
LMSTUDIO_DEFAULT_MODEL = "lmstudio-community/Qwen3-VL-8B-Instruct-GGUF"
```

---

## Best use cases in Terminal Depths

- Screenshot analysis: `vision <path>` command
- Code generation with tool orchestration
- GUI agent tasks (clicking, navigating, describing screens)
- Replacing qwen2.5-coder:14b as the default Ollama model

---

## Qwen3-VL-8B vs Qwen2.5-VL-7B

| Scenario                      | Choose                    |
|-------------------------------|---------------------------|
| Proven stability + high dl    | Qwen2.5-VL-7B             |
| Newest architecture + 256K ctx| Qwen3-VL-8B ← **recommended** |
| 32B quality                   | Qwen3-VL-32B (20GB VRAM) |
| Document/OCR specialty        | MiniCPM-V (`ollama pull minicpm-v`) |

**Recommended pull sequence:**
```bash
ollama pull qwen2.5vl:7b   # proven workhorse
ollama pull qwen3-vl:8b    # newer, 256K ctx, better reasoning
```

**Unlock XP:** 20 XP
