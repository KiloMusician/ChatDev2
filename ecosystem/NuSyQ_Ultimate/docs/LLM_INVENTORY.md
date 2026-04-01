# LLM Inventory & Mapping

This file documents the output of `scripts/discover_llms.py` and recommended
practices for mapping installed models to task categories.

Run discovery:

```bash
python scripts/discover_llms.py --ollama http://127.0.0.1:11434 --lmstudio http://127.0.0.1:1234
```

Output is written to `state/llm_inventory.json`.

Heuristics used by the discovery script (can be modernized later):
- model name contains "coder", "code", "qwen", "codellama" → code_generation, debugging, code_review
- model name contains "mistral", "llama", "phi" → general_conversation, creative
- otherwise → general_conversation

Recommendations:
- Keep discovery dynamic: orchestrators should consult `state/llm_inventory.json` at startup.
- Avoid hard-coded paths; prefer env vars (`OLLAMA_BASE_URL`, `LMSTUDIO_BASE_URL`).
- Provide a small UI or CLI to tag models with project-specific roles (low-latency, code-focused, reasoning).
