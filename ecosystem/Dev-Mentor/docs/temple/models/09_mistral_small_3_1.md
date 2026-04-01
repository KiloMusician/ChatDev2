# MODEL CARD — Mistral Small 3.1 24B Instruct
*Temple of Knowledge — Floor 6: The Model Sanctum*

---

## Identity

- **ID:** `mistral-small:24b` (Ollama) / `mistralai/Mistral-Small-3.1-24B-Instruct-GGUF` (LM Studio)
- **Provider:** Mistral AI
- **Parameters:** 24 billion
- **Architecture:** Mistral sliding-window attention + Vision Encoder
- **Context window:** 128,000 tokens
- **Release:** March 2025

---

## WHY THIS MODEL: Vision + Tools + Strong Reasoning

Mistral Small 3.1 beats many 70B models on coding benchmarks while fitting
in ~16GB VRAM (Q4). Crucially it has **native vision AND tool calling**.

| Capability              | Level   |
|-------------------------|---------|
| Image understanding     | Strong  |
| Tool use / fn calling   | Expert  |
| Code generation         | Expert  |
| Instruction following   | Expert  |
| Reasoning               | Expert  |
| Context utilization     | Expert  |

**Key advantage:** Best coding model in the vision+tools category for local use.
LM Studio's `openai/gpt-oss-20b` can be replaced by this.

---

## Setup

### Ollama
```bash
ollama pull mistral-small:24b
# ~16GB VRAM (Q4_K_M) — needs more than the 7B models
```

### LM Studio
Search: `Mistral-Small-3.1-24B-Instruct`
- LM Studio has the official GGUF
- Recommended: `Q4_K_M` (16GB) or `Q3_K_M` (12GB)

---

## Replacing openai/gpt-oss-20b in LM Studio

`gpt-oss-20b` has tools but no vision. Mistral Small 3.1 has both and is
better at code tasks.

In `llm_client.py`:
```python
LM_STUDIO_MODEL = "mistral-small-3.1-24b-instruct"
```

---

## Vision format

```python
# Image + tool call together:
messages = [
    {"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
        {"type": "text", "text": "Analyse this screenshot and run the status command"}
    ]}
]
```

**Unlock XP:** 25 XP
