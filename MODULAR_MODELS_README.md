# 🤖 NuSyQ Modular Agent Model System

## Overview

The Modular Agent Model System enables **per-agent Ollama model assignment** in ChatDev multi-agent workflows. Instead of using a single model for all agents, each agent can be assigned the optimal model for their role.

This enables:
- **Performance Optimization**: Assign best models to critical roles
- **Cost Efficiency**: Use smaller models for simple tasks, larger for complex
- **A/B Testing**: Compare different model combinations
- **Performance Tracking**: Monitor which models excel at which roles
- **Continuous Improvement**: Evolve assignments based on performance data

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   NuSyQ ChatDev Wrapper                     │
│              (nusyq_chatdev.py)                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│            Modular Model Adapter                            │
│       (chatdev/modular_model_adapter.py)                    │
│                                                             │
│  • Patches ChatChain to use per-agent models                │
│  • Creates OllamaModelType wrapper                          │
│  • Tracks model usage and performance                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│         Modular Agent Model Manager                         │
│       (chatdev/modular_agent_models.py)                     │
│                                                             │
│  • Loads RoleConfig_Modular.json                            │
│  • Returns model for each agent role                        │
│  • Logs interactions and metrics                            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              RoleConfig_Modular.json                        │
│    (CompanyConfig/NuSyQ_Ollama/)                            │
│                                                             │
│  Role → Model assignments with reasoning                    │
│  CEO: qwen2.5-coder:14b                                     │
│  Programmer: qwen2.5-coder:14b                              │
│  Code Reviewer: starcoder2:15b                              │
│  Tester: codellama:7b                                       │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Enable Modular Models (Default)

```bash
# Modular models enabled by default
python nusyq_chatdev.py --task "Create a calculator app"
```

Output:
```
[🤖] Modular Agent Models: ENABLED
[>>] Per-agent model assignments will be loaded from config
[✅] Modular model system activated
🤖 NuSyQ Modular Agent-Model Assignments
═══════════════════════════════════════
Chief Executive Officer:
  Model: qwen2.5-coder:14b
  Reasoning: Strategic thinking and decision-making...

Programmer:
  Model: qwen2.5-coder:14b
  Reasoning: Code generation is the core task...
```

### 2. Disable Modular Models (Single Model)

```bash
# Use single model for all agents
python nusyq_chatdev.py --task "Simple task" --no-modular-models --model gemma2:9b
```

### 3. Check Model Assignments

```bash
cd ChatDev
python -m chatdev.modular_agent_models
```

Output shows current role-to-model assignments with reasoning.

## Configuration

### RoleConfig_Modular.json Structure

```json
{
  "Agent Role Name": {
    "prompt": ["System prompt", "lines..."],
    "model": "ollama-model:tag",
    "model_reasoning": "Why this model for this role"
  }
}
```

### Default Model Assignments

| Agent Role | Model | Reasoning |
|------------|-------|-----------|
| **Chief Executive Officer** | qwen2.5-coder:14b | Strategic thinking, architecture decisions |
| **Chief Technology Officer** | qwen2.5-coder:14b | Technical strategy, system design |
| **Programmer** | qwen2.5-coder:14b | Code generation is core task, needs best coding model |
| **Code Reviewer** | starcoder2:15b | Code analysis benefits from starcoder's expertise |
| **Software Test Engineer** | codellama:7b | Test generation, efficient for this focused task |
| **Chief Product Officer** | gemma2:9b | Balanced reasoning and creative thinking |
| **Chief Human Resource Officer** | gemma2:9b | Communication, empathy, people management |
| **Chief Creative Officer** | gemma2:9b | Creative problem-solving |
| **Counselor** | llama3.1:8b | Communication, empathy, conflict resolution |

### Customizing Assignments

Edit `ChatDev/CompanyConfig/NuSyQ_Ollama/RoleConfig_Modular.json`:

```json
{
  "Programmer": {
    "prompt": [...],
    "model": "qwen2.5-coder:32b",  // Upgrade to larger model
    "model_reasoning": "Using 32B for complex coding tasks"
  }
}
```

## Performance Tracking

### Session Logs

The system automatically tracks:
- Which model was used by each agent
- Number of interactions per agent
- Token consumption per agent
- Average response time per agent

### Generate Performance Report

```python
from chatdev.modular_model_adapter import get_session_performance_report, save_performance_report
from pathlib import Path

# Get report
report = get_session_performance_report()
print(report)

# Save to file
save_performance_report(Path("performance_report.json"))
```

### Example Report

```json
{
  "agent_performance": {
    "Programmer": {
      "model": "qwen2.5-coder:14b",
      "usage_count": 5,
      "total_tokens": 2500,
      "avg_response_time": 2.3,
      "reasoning": "Code generation is the core task..."
    },
    "Code Reviewer": {
      "model": "starcoder2:15b",
      "usage_count": 3,
      "total_tokens": 1200,
      "avg_response_time": 1.8,
      "reasoning": "Code review benefits from starcoder..."
    }
  },
  "model_usage": {
    "qwen2.5-coder:14b": {
      "roles": ["Chief Executive Officer", "Programmer", "Chief Technology Officer"],
      "total_usage_count": 12,
      "total_tokens": 5000,
      "avg_response_time": 2.5
    },
    "starcoder2:15b": {
      "roles": ["Code Reviewer"],
      "total_usage_count": 3,
      "total_tokens": 1200,
      "avg_response_time": 1.8
    }
  }
}
```

## Optimization Strategies

### 1. Assign Best Models to Critical Roles

**Programmer** and **Code Reviewer** are critical for code quality:
- Programmer: Use largest/best coding model (qwen2.5-coder:14b or 32b)
- Code Reviewer: Use specialized analysis model (starcoder2:15b)

### 2. Use Smaller Models for Support Roles

**Counselor** and **CHRO** don't need massive coding models:
- Use efficient models like llama3.1:8b or gemma2:9b
- Saves resources, maintains quality

### 3. Experiment with Combinations

Try different model combinations and compare results:

```bash
# Version A: All qwen2.5-coder:14b
python nusyq_chatdev.py --task "Create API" --no-modular-models --model qwen2.5-coder:14b

# Version B: Modular (mixed models)
python nusyq_chatdev.py --task "Create API" --modular-models
```

Compare:
- Code quality
- Execution time
- Resource usage
- Test coverage

### 4. A/B Testing Framework

```json
{
  "_metadata": {
    "experiment": "A/B Test - Code Reviewer Models",
    "variants": {
      "A": "starcoder2:15b",
      "B": "qwen2.5-coder:14b"
    }
  },
  "Code Reviewer": {
    "model": "starcoder2:15b",  // Change this for variant B
    "model_reasoning": "Testing which model provides better code review"
  }
}
```

Run multiple times with each variant, compare results.

## Advanced Usage

### Programmatic Access

```python
from chatdev.modular_agent_models import get_manager, get_model_for_role

# Get manager instance
manager = get_manager()

# Get model for specific role
programmer_model = get_model_for_role("Programmer")
print(f"Programmer uses: {programmer_model}")

# Log interaction
manager.log_agent_interaction(
    role="Programmer",
    model="qwen2.5-coder:14b",
    tokens=500,
    response_time=2.5
)

# Get performance summary
summary = manager.get_performance_summary()
print(summary)

# Print all assignments
manager.print_model_assignments()
```

### Integration with ΞNuSyQ Framework

The modular model system integrates with ΞNuSyQ symbolic tracking:

```bash
# Modular models + symbolic tracking
python nusyq_chatdev.py \
  --task "Complex system" \
  --modular-models \
  --symbolic \
  --msg-id 1.2.3

# Modular models + multi-model consensus
python nusyq_chatdev.py \
  --task "Critical feature" \
  --modular-models \
  --consensus \
  --models qwen2.5-coder:14b,codellama:7b
```

## Troubleshooting

### Models Not Loading

**Problem**: Modular models fail to load, falls back to single model

**Solution**:
1. Check `RoleConfig_Modular.json` exists in `ChatDev/CompanyConfig/NuSyQ_Ollama/`
2. Verify JSON is valid (use `python -m json.tool RoleConfig_Modular.json`)
3. Ensure ChatDev path is correct

### Model Not Found

**Problem**: Ollama model specified in config not found

**Solution**:
```bash
# Check available models
ollama list

# Pull missing model
ollama pull qwen2.5-coder:14b
```

### Performance Issues

**Problem**: Workflow is slow with modular models

**Solution**:
1. Check which models are assigned to high-usage roles
2. Consider using smaller models for less critical roles
3. Monitor model response times in performance report
4. Adjust assignments based on bottlenecks

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'chatdev.modular_agent_models'`

**Solution**:
```bash
# Ensure you're in NuSyQ root directory
cd C:\Users\keath\NuSyQ

# Verify file exists
ls ChatDev/chatdev/modular_agent_models.py

# Run with explicit path
python -c "import sys; sys.path.insert(0, 'ChatDev'); from chatdev.modular_agent_models import get_manager; get_manager().print_model_assignments()"
```

## Best Practices

### 1. Start with Defaults
Use the default assignments first, they're optimized based on role requirements.

### 2. Track Performance
Always save performance reports to guide optimization decisions.

### 3. Iterate Gradually
Change one model assignment at a time to isolate impact.

### 4. Document Experiments
Use `_metadata` section in config to document what you're testing.

### 5. Balance Cost vs Quality
- Critical roles: Use best models (14B+)
- Support roles: Use efficient models (7B-9B)
- Experiment: Test to find optimal balance

### 6. Monitor Resource Usage
```bash
# Check Ollama resource usage
ollama ps

# Monitor during workflow
watch -n 1 ollama ps
```

## Future Enhancements

### Planned Features
- [ ] Auto-optimization based on performance data
- [ ] Dynamic model selection based on task complexity
- [ ] Model warm-up and caching for faster responses
- [ ] Cost tracking per model/agent
- [ ] Integration with model performance database
- [ ] Automatic A/B testing framework
- [ ] Model recommendation engine

### Contributing
To add new features or improve model assignments, edit:
- `chatdev/modular_agent_models.py` - Core manager
- `chatdev/modular_model_adapter.py` - ChatDev integration
- `CompanyConfig/NuSyQ_Ollama/RoleConfig_Modular.json` - Model assignments

## References

- [ChatDev Documentation](https://github.com/OpenBMB/ChatDev)
- [Ollama Model Library](https://ollama.ai/library)
- [NuSyQ Framework](../README.md)
- [ΞNuSyQ Protocol](../docs/ΞNuSyQ_Protocol.md)

---

**Status**: ✅ Production Ready  
**Version**: 1.0.0  
**Last Updated**: 2025-10-11  
**Maintainer**: NuSyQ Development Team
