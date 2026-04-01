# MODEL CARD — Qwen2.5-VL 7B
*Temple of Knowledge — Floor 6: The Model Sanctum*

---

## Identity

- **ID:** `qwen2.5-vl:7b`
- **Provider:** Ollama (local)
- **Parameters:** 7 billion (vision-language)
- **Architecture:** Transformer + Vision Encoder

---

## Capabilities

| Capability             | Level   |
|-----------------------|---------|
| Image understanding    | Expert  |
| Visual localization    | Strong  |
| OCR (text in images)   | Expert  |
| Code screenshot review | Strong  |
| Diagram interpretation | Good    |

**Context window:** 32,768 tokens (text + image tokens)

---

## Performance Profile

- **Tokens/sec:** ~10 (vision tasks are heavier)
- **RAM needed:** 12 GB
- **Cold start:** ~3 seconds
- **Image processing overhead:** ~500ms per image

---

## What It's Good At

Qwen2.5-VL 7B is the **primary vision model** for Terminal Depths:
- `vision <image_path>` — analyze a screenshot or diagram
- Game state visual analysis from terminal screenshots
- Reading code from image files
- Interpreting network topology diagrams

In practice: if a player screenshots their terminal and feeds it
to the game, VL-7B processes it and Serena can respond to the
visual context.

---

## Lore Integration

*"The vision model looked at the CHIMERA UI mockup.
It said: 'There are seventeen surveillance indicators
in this interface and only one exit button.'
Nobody had counted. It was right."*

— Ada's notes, Week 9

---

## Limitations

- Cannot process video (single frames only)
- Image tokens consume significant context budget
- Performance drops on very small or blurry images

---

## Terminal Depths Commands

```
vision /path/to/screenshot.png
learn models 04_qwen25_vl_7b   ← you are here
```

**Unlock XP:** 15 XP (reading this card)
