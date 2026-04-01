# Fine-tuning Pipeline Guide

## Overview

`scripts/finetune.py` builds a structured instruction-following dataset from Terminal Depths player command data, suitable for fine-tuning local LLMs (Ollama, LM Studio) or any Alpaca-format compatible trainer.

## Data Source

The pipeline reads from `state/feature_store.db` — a SQLite database written by `services/feature_store.py` as players interact with the game server.

**Tables used:**
- `feature_events` — raw event stream (event_type, features JSON, session_id, ts)
- `player_profiles` — aggregated per-session stats (commands_run, top_commands)

**Relevant event types:**
| Event Type | Description |
|---|---|
| `command` | Player ran a terminal command (features: `cmd`, `node`) |
| `xp_gain` | Player earned XP |
| `quest_complete` | A quest was completed |
| `beat_triggered` | A story beat fired |
| `achievement` | An achievement was unlocked |

## Output Format

`state/finetune_dataset.jsonl` — one JSON object per line, Alpaca instruction format:

```json
{"instruction": "What does the player do after running 'scan' on node-1?", "input": "", "output": "exploit node-1"}
{"instruction": "Given the command sequence: scan → exploit → exfil — what command comes next?", "input": "", "output": "ls"}
{"instruction": "What does the 'scan' command do in Terminal Depths?", "input": "", "output": "Scans a network node to reveal its services and vulnerabilities."}
```

## Running the Pipeline

```bash
# Generate dataset + print report
python scripts/finetune.py

# Generate and test a sample inference against Ollama
python scripts/finetune.py --test-inference

# Point at a custom DB or output path
python scripts/finetune.py --db /path/to/feature_store.db --out /path/to/out.jsonl
```

If `state/feature_store.db` is missing or empty, the script uses a built-in mock dataset so the pipeline can always be validated end-to-end.

## Training Pair Strategy

Three pair types are generated:

1. **Consecutive-pair prediction** — for each pair of sequential commands within a session, create: "Given player ran A, what comes next?" → B
2. **Sequence prediction** — for sessions with 4+ commands, use a 3-command context window to predict the 4th
3. **Command description** — for all commands that have a description mapping, generate: "What does X do?" → description

## Inference Validation (--test-inference)

With `--test-inference`, the script:
1. Selects a representative pair from the dataset
2. Formats it as an Alpaca prompt (`### Instruction / ### Input / ### Response`)
3. POSTs to `http://localhost:11434/api/generate` using `qwen2.5-coder:14b`
4. Prints the model's response alongside the expected output

This validates that the local model can follow the instruction format before any fine-tuning run.

## Extending the Pipeline

**Add more event types:** Edit `_build_instruction_pairs()` in `scripts/finetune.py` to process `quest_complete`, `achievement`, or `beat_triggered` events.

**Add command descriptions:** Extend the `_DESCS` dict in `_cmd_description()`.

**Hook into a trainer:** Feed `state/finetune_dataset.jsonl` to any Alpaca-compatible trainer:
- [axolotl](https://github.com/OpenAccess-AI-Collective/axolotl) — supports JSONL Alpaca format directly
- [unsloth](https://github.com/unslothai/unsloth) — fast LoRA fine-tuning
- [llama.cpp finetune](https://github.com/ggerganov/llama.cpp) — for GGUF models

**Register the fine-tuned model:** After training, register it in the ecosystem:
```bash
# Add to LM Studio model library, then update llm_client.py priority order
# or load in Ollama:
ollama create terminal-depths-ft -f Modelfile
```

## Dataset Growth

| Sessions | Approx. pairs |
|---|---|
| 10 | ~150 |
| 50 | ~800 |
| 200 | ~3,500 |
| 1,000 | ~18,000 |

A useful fine-tune typically needs 500-5,000 high-quality pairs. Let the game server accumulate real player data before training.
