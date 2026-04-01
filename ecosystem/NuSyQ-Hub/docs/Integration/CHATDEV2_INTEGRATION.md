# ChatDev2 Fork Integration

## Overview

NuSyQ-Hub integrates with the canonical **ChatDev2** fork maintained at:
- **Repository**: https://github.com/KiloMusician/ChatDev2
- **Branch**: `main`
- **Installation**: `C:/Users/keath/NuSyQ/ChatDev`

## Key Enhancements in ChatDev2

The ChatDev2 fork includes NuSyQ-specific customizations:

1. **Ollama Integration**: Modified to work with local Ollama models
2. **ΞNuSyQ Protocol**: Symbolic message framework for multi-agent coordination
3. **Memory System**: Enhanced context preservation across sessions
4. **Lazy Client Loading**: Web spider and API clients load only when needed
5. **Configuration Customizations**: NuSyQ-specific config files

## Dependencies Alignment

ChatDev2 requirements are aligned with NuSyQ-Hub:

| Package | ChatDev2 Version | Hub Version | Status |
|---------|-----------------|-------------|---------|
| Flask | >=2.3.2,<4.0.0 | >=2.3.0 | ✅ Compatible |
| Flask-SocketIO | >=5.3.4,<6.0.0 | >=5.3.4,<6.0.0 | ✅ Aligned |
| Werkzeug | >=3.0.3,<4.0.0 | >=3.0.3,<4.0.0 | ✅ Aligned |
| openai | >=1.47.1,<2.0.0 | >=1.0.0 | ✅ Compatible |
| tiktoken | >=0.8.0,<1.0.0 | >=0.8.0 | ✅ Compatible |
| requests | >=2.31.0 | >=2.31.0 | ✅ Aligned |
| tenacity | >=8.2.2,<9.0.0 | >=8.2.2 | ✅ Compatible |

## Integration Architecture

```
NuSyQ-Hub
├── src/config/chatdev2_config.py         # Configuration utilities
├── src/ai/ollama_chatdev_integrator.py   # Ollama-ChatDev bridge
├── src/orchestration/chatdev_testing_chamber.py  # Testing environment
└── src/utils/setup_chatdev_integration.py  # Setup script

Integration Flow:
1. User requests AI task
2. AgentTaskRouter delegates to ChatDev
3. ChatDev2Config resolves installation path
4. OllamaChatDevIntegrator bridges to local models
5. ChatDev multi-agent team executes task
6. Results returned to Testing Chamber
```

## Usage

### Basic Integration

```python
from src.config.chatdev2_config import get_chatdev2_config

# Get configuration
config = get_chatdev2_config()

# Verify installation
if config.verify_installation():
    print("ChatDev2 ready!")
    
# Get run command
cmd = config.get_run_command(
    task="Create a REST API with JWT auth",
    model="qwen2.5-coder:14b"
)
```

### Via Orchestration

```python
from src.tools.agent_task_router import AgentTaskRouter

router = AgentTaskRouter()

# Delegate to ChatDev2
result = await router.generate_with_ai(
    description="Build a web scraper",
    target="chatdev"
)
```

### Environment Variables

Set `CHATDEV_PATH` to override default installation location:

```bash
# PowerShell
$env:CHATDEV_PATH="C:\CustomPath\ChatDev"

# Bash
export CHATDEV_PATH="/path/to/chatdev"
```

## Recent Updates (2025-02-11)

Latest commits in ChatDev2 fork:
- `670c805`: Fix web_spider lazy loading (no OPENAI_API_KEY required for --help)
- `3a7596e`: Add Memory stub to unblock chatdev imports
- `af2b49d`: Merge conflict resolution for NuSyQ customizations
- `ec4fd11`: ChatDev workspace local development sync

## Testing Chamber Integration

ChatDev2 projects are developed in isolated testing chambers:

```
testing_chamber/
├── ollama_integration/     # Ollama-ChatDev bridge projects
├── api_fallback/          # API fallback mechanisms
├── modules/               # Generated modules
└── tests/                 # Test scripts
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `CHATDEV_PATH` is set or using default path
2. **Ollama Connection**: Verify Ollama is running on port 11434
3. **API Fallback**: Check OpenAI API key in `config/secrets.json`

### Verification Script

```bash
python -c "from src.config.chatdev2_config import verify_chatdev2_fork; print(verify_chatdev2_fork())"
```

## See Also

- [ChatDev Original](https://github.com/OpenBMB/ChatDev) - Upstream project
- [NuSyQ Orchestration](../AGENTS.md#7-system-state-snapshot) - Multi-AI coordination
- [Testing Chamber](../docs/Testing_Chamber_Pattern.md) - Prototype workflow
