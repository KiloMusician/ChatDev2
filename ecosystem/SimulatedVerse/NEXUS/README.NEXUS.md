# ΞNuSyQ Nexus — Single Source of Truth

**Goal**: kill rediscovery. This folder is the canonical, agent-friendly map of the repo.

## How to Use (Humans & Agents)

- Start here. Then consult `/NEXUS/datasets/index.ndjson` (machine view).
- **4-Action discipline** (Replit, listen): forward → poll → sync → smoke. No manual file edits.
- **Update-over-create**: before creating a file, search `index.ndjson` for similar paths + TAGS.
- **Testing-Chamber first**: invasive edits go to `/testing-chamber/*` with safety contracts from `/NEXUS/playbooks/testing-chamber.md`.
- **Proof-Driven**: success = artifact in proofs registry, not a log line.

## What's in here

- `maps/` → tree snapshot & mermaid module graph (fast mental model)
- `datasets/` → ndjson/parquet indices for LLMs, ChatDev, Jupyter
- `schemas/` → contracts
- `playbooks/` → runbooks for agents, Replit, humans
- `prompts/replit.megaprompt.txt` → paste this into Replit chat before doing anything