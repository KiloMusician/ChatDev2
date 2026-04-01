# Consensus Orchestration Workflow

## Overview

Multi-model consensus experiments enable running the same prompt across multiple Ollama models and synthesizing their responses through voting mechanisms.

## Feature Flag

```json
{
  "consensus_mode_enabled": {
    "description": "Multi-model consensus experiments across Ollama models",
    "default": false,
    "requires_acl": true,
    "dependencies": ["ollama_running"]
  }
}
```

## Voting Modes

### Simple Voting
Each model gets one vote for their response.

### Weighted Voting
Models are weighted by capability scores from `config/model_capabilities.json`.

### Ranked Voting
Models rank responses by preference, aggregated via ranked-choice.

## Usage

### CLI Interface

```bash
# Run consensus experiment
python scripts/nusyq_dispatch.py council "What's the best approach?" --agents=ollama,lmstudio

# With specific models
python scripts/nusyq_dispatch.py council "Review this code" --models=qwen2.5-coder,deepseek-coder-v2
```

### Programmatic Interface

```python
from src.orchestration.consensus_orchestrator import ConsensusOrchestrator

orchestrator = ConsensusOrchestrator()
result = await orchestrator.run_consensus(
    prompt="Analyze this architecture",
    models=["qwen2.5-coder:14b", "llama3.1:8b"],
    voting_mode="weighted"
)
```

## Reports

Consensus results are saved to:
- `Reports/consensus/consensus_YYYYMMDD_HHMMSS_<hash>.json`

## Configuration

### Model Selection

Models are selected from `config/ollama_models.json`:

```json
{
  "ollama": {
    "models": [
      {"name": "qwen2.5-coder:14b", "tags": ["code"], "weight": 1.2},
      {"name": "llama3.1:8b", "tags": ["general"], "weight": 1.0}
    ]
  }
}
```

## Related Files

- `src/orchestration/consensus_orchestrator.py` - Core implementation
- `scripts/nusyq_dispatch.py` - MJOLNIR CLI
- `config/model_capabilities.json` - Model weights and capabilities
