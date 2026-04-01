# 🔍 Model Discovery System - Quick Reference

## Overview

The NuSyQ-Hub model discovery system provides **flexible, zero-configuration model selection** across Ollama, LM Studio, OpenAI, and ChatDev. Models are discovered dynamically at runtime with intelligent capability-based routing.

## System Status ✅

**Last Tested:** 2026-02-16  
**Status:** All systems operational  
**Models Discovered:** 16 total (14 dynamic + 2 static)

### Provider Status
- ✅ **Ollama** - Running at `http://localhost:11434` (13 models)
- ✅ **LM Studio** - Running at `http://localhost:1234` (2 models) 
- ✅ **OpenAI** - Configured (1 model)
- ✅ **ChatDev** - Integrated (1 team)

## Quick Start

### 1. Discovery is Automatic
```python
from src.integration.universal_llm_gateway import load_model_capabilities

# Discovers models from all providers
capabilities = load_model_capabilities()
print(f"Found {len(capabilities)} models")
```

### 2. Capability-Based Selection
```python
from src.integration.universal_llm_gateway import UniversalLLMGateway

gateway = UniversalLLMGateway()

# Select best code model (prefers local)
code_model = gateway.select_model(
    model_hint=None,
    capability_tags=["code", "local"],
    prefer_local=True
)

# Select general model (no preference)
general_model = gateway.select_model(
    model_hint=None,
    capability_tags=["general"],
    prefer_local=False
)
```

### 3. Task Routing
```python
from src.tools.agent_task_router import AgentTaskRouter

router = AgentTaskRouter()

# Routes to appropriate model automatically
await router.analyze_with_ai("Analyze this Python code", target="ollama")
```

## Configuration

### Environment Variables (.env)
```bash
# Discovery settings
NUSYQ_MODEL_DISCOVERY=1                # Enable dynamic discovery (default: 1)
NUSYQ_MODEL_CAPS_TTL_SECONDS=300      # Cache TTL in seconds (default: 300)
NUSYQ_LLM_DISCOVERY_TIMEOUT=5         # API timeout in seconds (default: 5)
NUSYQ_MODEL_CAPS_PERSIST=1            # Persist to config file (default: 1)
```

### Model Roster Location
**File:** `config/model_capabilities.json`  
**Format:** Dict with `provider:model` keys  
**Purpose:** Human-readable roster + static model definitions

## Capability Tags

### Available Tags
- `code` - Code generation/analysis
- `general` - General purpose tasks
- `local` - Runs locally (Ollama/LM Studio)
- `reasoning` - Complex reasoning tasks
- `light` - Small/fast models
- `multi-agent` - Multi-agent systems (ChatDev)
- `codegen` - Code generation pipelines
- `pipeline` - Multi-stage workflows

### Tag Assignment
Tags are **automatically inferred** from model names using heuristics:
- Models with "coder", "code" → `code` tag
- Models with "embed" → `embedding` tag  
- Models < 10B params → `light` tag
- Ollama/LM Studio → `local` tag

## Current Model Roster (Live)

### OpenAI Models (1)
- `openai:gpt-4o-mini` - Tags: code, general

### Ollama Models (13)
- `ollama:qwen2.5-coder:7b` - Tags: local, code
- `ollama:qwen2.5-coder:14b` - Tags: local, code
- `ollama:deepseek-coder-v2:16b` - Tags: local, code
- `ollama:starcoder2:15b` - Tags: local, code
- `ollama:codellama:7b` - Tags: local, code, general
- `ollama:phi3:3.8b` - Tags: code, local, light
- `ollama:phi3.5:latest` - Tags: local, general
- `ollama:llama3:8b` - Tags: code, general, local
- `ollama:llama3.1:8b` - Tags: local, general
- `ollama:gemma2:9b` - Tags: local, general
- `ollama:gpt-3.5-turbo-16k:latest` - Tags: local
- `ollama:nomic-embed-text:latest` - Tags: local

### LM Studio Models (2)
- `lmstudio:openai/gpt-oss-20b` - Tags: local
- `lmstudio:text-embedding-nomic-embed-text-v1.5` - Tags: local

### ChatDev Teams (1)
- `chatdev:chatdev-team` - Tags: multi-agent, codegen, pipeline

## Performance

### Discovery Speed
- **First call:** ~3s (API queries to Ollama + LM Studio)
- **Cached calls:** <0.01s (300s TTL)
- **Timeout:** 5s per provider (fail-safe)

### Selection Speed
- **Model selection:** <1ms (in-memory filtering)
- **No API calls** during selection

## Troubleshooting

### No Models Discovered
```bash
# Check if services are running
curl http://localhost:11434/api/tags     # Ollama
curl http://localhost:1234/v1/models     # LM Studio

# Check logs in terminal output for:
# "HTTP Request: GET http://localhost:11434/api/tags"
```

### Cache Not Working
```bash
# Verify environment variable
echo $NUSYQ_MODEL_CAPS_TTL_SECONDS

# Or force cache refresh by restarting Python session
```

### Persistence Not Working
```bash
# Check if file exists
ls config/model_capabilities.json

# Verify environment variable
echo $NUSYQ_MODEL_CAPS_PERSIST

# Manually trigger persistence:
python -c "from src.integration.universal_llm_gateway import load_model_capabilities; load_model_capabilities()"
```

## Testing

### Run Integration Tests
```bash
python test_model_discovery_integration.py
```

Expected output:
- ✅ Dynamic model discovery (16 models)
- ✅ Cache working (<0.01s second load)
- ✅ Persistence to config file
- ✅ Capability-based routing
- ✅ Provider availability (Ollama + LM Studio)
- ✅ Environment configuration

## Architecture

### Components
1. **Discovery** (`universal_llm_gateway.py`)
   - `_discover_ollama_models()` - Query Ollama API
   - `_discover_lmstudio_models()` - Query LM Studio API
   - `_merge_capabilities()` - Deduplicate and merge

2. **Caching** (in-memory)
   - Global `_CAPS_CACHE` with TTL
   - Prevents redundant API calls

3. **Persistence** (optional)
   - Writes to `config/model_capabilities.json`
   - Human-readable dict format
   - Static models preserved

4. **Routing** (`agent_task_router.py`)
   - Task → Tags → Model selection
   - Preference-based filtering (local, cost, latency)

### Data Flow
```
Provider APIs → Discovery → Cache → Merge → Persist → Select → Route
     ↓              ↓         ↓       ↓        ↓        ↓       ↓
  Ollama        Heuristic  In-mem  Dedup   JSON file  Filter  LLM call
  LM Studio     tagging    300s    resolve  (optional) by tags
```

## Future Enhancements

- [ ] Model benchmarking (latency/quality metrics)
- [ ] Automatic fallback chains (try local → cloud)
- [ ] Cost tracking per model usage
- [ ] Model health monitoring
- [ ] Custom tag definitions in config

## Related Documentation

- [Agent Task Router](../src/tools/agent_task_router.py) - Task routing logic
- [Universal LLM Gateway](../src/integration/universal_llm_gateway.py) - Discovery implementation
- [Multi-AI Orchestrator](../src/orchestration/multi_ai_orchestrator.py) - System integration
- [Copilot Instructions](../.github/copilot-instructions.md) - Operator phrases

---

**Last Updated:** 2026-02-16  
**Maintainer:** ΞNuSyQ Systems  
**Status:** Production Ready ✅
