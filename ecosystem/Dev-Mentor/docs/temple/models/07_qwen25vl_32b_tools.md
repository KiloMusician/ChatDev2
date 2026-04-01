# MODEL CARD — Qwen2.5-VL 32B Instruct
*Temple of Knowledge — Floor 6: The Model Sanctum*

---

## Identity

- **ID:** `qwen2.5vl:32b` (Ollama) / `Qwen/Qwen2.5-VL-32B-Instruct-GGUF` (HF)
- **Provider:** Ollama or LM Studio (GGUF)
- **Parameters:** 32 billion (vision-language + tool calling)
- **Architecture:** Qwen2.5 Transformer + Vision Encoder (ViT)
- **Context window:** 128,000 tokens

---

## WHY THIS MODEL MATTERS: Vision + Tools

This model solves the split we had: Qwen2.5-Coder has tools but no vision.
Qwen2.5-VL-7B has vision but limited tool schema support.

**Qwen2.5-VL-32B has both natively:**

| Capability            | Level   |
|-----------------------|---------|
| Image understanding   | Expert  |
| OCR (text in images)  | Expert  |
| Tool use / fn calling | Expert  |
| Code generation       | Strong  |
| Diagram analysis      | Expert  |
| Multi-image reasoning | Good    |

---

## Setup

### Ollama
```bash
ollama pull qwen2.5vl:32b
# Requires ~22GB VRAM (Q4_K_M quant)
# Or use :7b for 8GB VRAM
```

### LM Studio
Search: `Qwen/Qwen2.5-VL-32B-Instruct-GGUF`
- Recommended quant: `Q4_K_M` (22GB) or `Q3_K_M` (17GB)

### Tool calling format
Uses standard OpenAI tool schema — compatible with ChatDev and llm_client.py.

---

## Replacing qwen2.5-coder:14b

Update `PREFER_LOCAL` routing in `llm_client.py`:
```python
# Old
OLLAMA_DEFAULT_MODEL = "qwen2.5-coder:14b"
# New (vision + tools)
OLLAMA_DEFAULT_MODEL = "qwen2.5vl:7b"  # 8GB VRAM
# or
OLLAMA_DEFAULT_MODEL = "qwen2.5vl:32b" # 22GB VRAM, much better
```

---

## Terminal Depths Integration

```bash
# Test vision + tool use together:
curl http://localhost:11434/api/chat -d '{
  "model": "qwen2.5vl:7b",
  "messages": [{"role":"user","content":"Use the status tool"}],
  "tools": [{"type":"function","function":{"name":"status","parameters":{}}}]
}'
```

**Unlock XP:** 25 XP (reading this card — vision+tools milestone)
