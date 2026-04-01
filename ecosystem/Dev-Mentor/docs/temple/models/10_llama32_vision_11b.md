# MODEL CARD — Llama 3.2 Vision 11B Instruct
*Temple of Knowledge — Floor 6: The Model Sanctum*

---

## Identity

- **ID:** `llama3.2-vision:11b` (Ollama)
- **Provider:** Meta AI
- **Parameters:** 11 billion (vision-language)
- **Architecture:** Llama 3.2 Transformer + Cross-attention Vision Encoder
- **Context window:** 128,000 tokens
- **Release:** September 2024

---

## Capabilities

| Capability              | Level   |
|-------------------------|---------|
| Image understanding     | Strong  |
| OCR (text in images)    | Good    |
| Tool use / fn calling   | Partial |
| Code generation         | Good    |
| Document analysis       | Strong  |

**Note on tool use:** Llama 3.2 Vision supports tool calling via Llama's
built-in function call syntax but is less reliable than Qwen2.5-VL or Mistral
for strict schema adherence. Best used for vision-heavy tasks where tools are
optional.

---

## Setup

### Ollama
```bash
ollama pull llama3.2-vision:11b
# ~8GB VRAM
```

---

## Best use cases in Terminal Depths

- Screenshot analysis: `vision <path>` command
- Reading lore images / QR code decoding assistance
- Document summarisation from images
- Less ideal for: strict function calling chains

---

## When to choose Llama 3.2 Vision vs Qwen2.5-VL

| Scenario                    | Choose              |
|-----------------------------|---------------------|
| Vision + strict tool schema | Qwen2.5-VL-7B       |
| Vision + best coding        | Mistral Small 3.1   |
| Vision + fast response      | Llama 3.2 Vision 11B|
| Vision + long document      | Qwen2.5-VL-32B      |

**Unlock XP:** 15 XP
