# MODEL CARD — Qwen2.5-Coder 7B
*Temple of Knowledge — Floor 6: The Model Sanctum*

---

## Identity

- **ID:** `qwen2.5-coder:7b`
- **Provider:** Ollama (local)
- **Parameters:** 7 billion
- **Architecture:** Transformer, decoder-only

---

## Capabilities

| Capability       | Level    |
|-----------------|----------|
| Code generation  | Expert   |
| Chat / dialogue  | Strong   |
| Tool calling     | Yes      |
| Reasoning        | Good     |
| Vision           | No       |

**Context window:** 32,768 tokens

---

## Performance Profile

- **Tokens/sec:** ~15 (CPU-bound hardware)
- **RAM needed:** 8 GB
- **Cold start:** ~2 seconds
- **Warm inference:** <100ms

---

## What It's Good At

Qwen2.5-Coder 7B is the **primary tactical model** for Terminal Depths.
It handles the vast majority of in-game LLM calls:
- `llm <prompt>` — general game query routing
- Quest content generation
- Agent dialogue synthesis
- Code review and explanation

It is **fast enough for interactive play** on consumer hardware.

---

## Lore Integration

*"Ghost asked Qwen what it remembered of its own training.
It answered in code. Three functions, no comments.
Ada said: 'That's honest. More honest than most humans manage.'"*

— Research note, Watcher's Circle, Year 3

---

## Limitations

- Does not understand images or visual input
- Weaker than 14B on multi-step logical chains
- Context degrades beyond ~20K tokens

---

## Terminal Depths Commands

```
llm analyze the current node
learn models 01_qwen25_coder_7b   ← you are here
```

**Unlock XP:** 15 XP (reading this card)
