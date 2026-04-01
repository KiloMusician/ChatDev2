---
name: Agent registry and MJOLNIR dispatch system
description: 20-agent registry, aliases, MJOLNIR CLI commands, and dispatch test invariants
type: project
---

## 20 Agents in Registry (as of 2026-03-16)
12 original: ollama, lmstudio, chatdev, codex, claude_cli, copilot, consciousness, quantum_resolver, factory, openclaw, intermediary, skyclaw
4 MCP bridges: dbclient, devtool, gitkraken, huggingface
Special: neural_ml, hermes, optimizer, metaclaw

## Key Aliases (src/dispatch/mjolnir.py AGENT_ALIASES)
- `lms` → lmstudio
- `claude` → claude_cli
- `sv` → consciousness
- `qr`/`quantum` → quantum_resolver
- `ml`/`neural`/`nn` → neural_ml
- `hermes_agent`/`openrouter`/`autonomous_agent` → hermes
- `trace_agent`/`observability`/`bounty_agent` → metaclaw
- `intermediary`/`ai`/`bridge` → intermediary

## MJOLNIR CLI Commands
```bash
python scripts/nusyq_dispatch.py status --probes           # Probe all 20
python scripts/nusyq_dispatch.py ask ollama "prompt"       # Single agent
python scripts/nusyq_dispatch.py ask codex "review this"  # Delegate to Codex CLI
python scripts/nusyq_dispatch.py council "question" --agents=ollama,lmstudio
python scripts/nusyq_dispatch.py chain "analyze then fix" --agents=ollama,codex --steps=analyze,generate
python scripts/nusyq_dispatch.py queue "task" --priority=HIGH   # Persistent via BTO
python scripts/nusyq_dispatch.py delegate "task" --agent=ollama # Guild quest (ephemeral)
python scripts/nusyq_dispatch.py poll <id> [--type=queue|delegate]
python scripts/nusyq_dispatch.py recall <tag> [--limit=10]
python scripts/nusyq_dispatch.py skyclaw status|start|stop
```

## SNS Compression
- `--sns` compresses prompts (41-85% token reduction)
- Global `sns_enabled=false` in feature_flags.json does NOT block MJOLNIR SNS usage

## Queue vs Delegate
- `queue()` → BackgroundTaskOrchestrator (persistent, survives restarts)
- `delegate()` → GuildBoard only (ephemeral quest tracking)

## Dispatch Test Invariants (test_dispatch.py)
When adding agents to AGENT_PROBES, update ALL THREE:
1. `test_registry_has_all_agents` — expected set (add agent name)
2. `test_status_no_probes` — count assertion (currently `len == 20`)
3. `test_display_names_match_probes` — checks AGENT_DISPLAY_NAMES ↔ AGENT_PROBES parity

## Context Auto-Detection
- `ContextDetector.detect()` returns ECOSYSTEM (CWD under NuSyQ-Hub), GAME (SimulatedVerse), PROJECT (elsewhere)
- Override with `--context=game`

## Copilot Rate-Limit Detection
- `_route_to_copilot()` distinguishes 429/rate-limit from auth failure
- Returns `copilot_cli_rate_limited` with suggestion to use --agent raptor or triad fallback

## Memory/Recall
- `ask()` stores interactions tagged with agent + task_type in MemoryPalace
- `council()` stores decisions tagged with agent names + consensus level
- `recall(tag)` merges in-process MemoryPalace + `state/memory_chronicle.jsonl` (cross-process)
- Culture Ship cycle appends to chronicle after each run
