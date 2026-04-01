# MODEL CARD — DeepSeek Coder V2 16B
*Temple of Knowledge — Floor 6: The Model Sanctum*

---

## Identity

- **ID:** `deepseek-coder-v2:16b`
- **Provider:** Ollama (local)
- **Parameters:** 16 billion
- **Architecture:** Mixture-of-Experts (MoE), sparse activation

---

## Capabilities

| Capability          | Level     |
|--------------------|-----------|
| Code generation     | Expert+   |
| Debugging           | Expert    |
| Complex reasoning   | Expert    |
| Tool calling        | Yes       |
| Architecture review | Expert    |

**Context window:** 32,768 tokens

---

## Performance Profile

- **Tokens/sec:** ~6 (CPU-bound)
- **RAM needed:** 24 GB
- **Cold start:** ~5 seconds
- **Warm inference:** ~200ms

---

## What It's Good At

DeepSeek Coder V2 is the **expert-tier model** — invoked when the task
demands maximum code intelligence:
- Deep debugging of complex multi-file issues
- Architectural decision analysis
- Security vulnerability assessment
- Multi-language translation (51 language proficiency matrix support)

In Terminal Depths lore, this model is said to have "read NexusCorp's
source code in its training data and simply... remembered."

---

## Lore Integration

*"ZERO trusted DeepSeek for one task: the signature.
ΨΞΦΩ was written with its help. The Watcher suspects
the model still carries a trace of ZERO's intent in
its activations. We cannot verify this. We watch."*

— Watcher's Circle, encrypted log

---

## Limitations

- Requires 24GB RAM — not available on most consumer hardware
- MoE routing adds unpredictable latency spikes
- Occasionally over-engineers simple solutions

---

## Terminal Depths Commands

```
learn models 03_deepseek_coder_v2_16b   ← you are here
```

**Unlock XP:** 20 XP (reading this card — rare model)
