# MODEL CARD — GPT-OSS 20B
*Temple of Knowledge — Floor 6: The Model Sanctum*

---

## Identity

- **ID:** `gpt-oss-20b`
- **Provider:** LM Studio (local)
- **Parameters:** 20 billion
- **Architecture:** GPT-class transformer, decoder-only
- **Endpoint:** `http://localhost:8000/v1/chat/completions` (OpenAI-compatible)

---

## Capabilities

| Capability         | Level    |
|--------------------|----------|
| Long-context reasoning | Expert |
| Instruction following | Expert |
| Code generation        | Strong |
| Summarisation          | Strong |
| Vision                 | No     |

**Context window:** 16,384 tokens

---

## Performance Profile

GPT-OSS 20B exposes an OpenAI-compatible endpoint — drop-in replacement for
GPT-3.5-class tasks with no API cost or data egress.

| Hardware    | Latency     | Throughput   |
|-------------|-------------|--------------|
| NVIDIA A100 | 20–50 ms    | ~50 tok/sec  |
| CPU (8-core)| 800–1200 ms | ~6 tok/sec   |

---

## Routing Role (config/models.yaml)

Selected automatically when `task_complexity > 0.8` and GPU is available.
Primary model for **complex reasoning** and long-context batch jobs.

```
routing:
  complex_reasoning: gpt-oss-20b
```

---

## In-game access

```
learn models 06_gpt_oss_20b
```

*Awards 25 XP on first study.*

---

## Sanctum Notes

*"Twenty billion weights trained on the open record of human thought.*
*It speaks in long arcs. Ask it the hard questions — the ones that*
*take three paragraphs to pose and a page to answer correctly.*
*It will not fail you. It will not rush you."*

---

*Model card — Temple of Knowledge, Floor 6 · 2026-03-22*
