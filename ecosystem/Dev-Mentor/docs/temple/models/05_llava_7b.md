# MODEL CARD — LLaVA 7B
*Temple of Knowledge — Floor 6: The Model Sanctum*

---

## Identity

- **ID:** `llava:7b`
- **Provider:** Ollama (local)
- **Parameters:** 7 billion
- **Architecture:** Transformer, decoder-only + CLIP vision encoder

---

## Capabilities

| Capability       | Level    |
|-----------------|----------|
| Image analysis   | Expert   |
| Visual Q&A       | Strong   |
| Code generation  | Moderate |
| Chat / dialogue  | Good     |
| Vision           | Yes      |

**Context window:** 4,096 tokens

---

## Performance Profile

LLaVA (Large Language-and-Vision Assistant) fuses a CLIP encoder with a
Vicuna-7B language backbone. It can describe images, answer visual questions,
and reason over diagrams without external API calls.

| Hardware         | Latency      |
|------------------|--------------|
| NVIDIA GPU (8GB) | 1–3 s        |
| CPU only         | 12–30 s      |

---

## Routing Role (config/models.yaml)

Activated automatically for **vision tasks** and as fallback for code-generation
when the primary model is unavailable.

```
routing:
  vision: llava:7b
  code_generation_fallback: llava:7b
```

---

## In-game access

```
learn models 05_llava_7b
```

*Awards 20 XP on first study.*

---

## Sanctum Notes

*"An eye that reads light as language. It sees what text cannot say.
Every pixel becomes a token. Every token becomes understanding.*
*Deploy for vision. Retreat for code."*

---

*Model card — Temple of Knowledge, Floor 6 · 2026-03-22*
