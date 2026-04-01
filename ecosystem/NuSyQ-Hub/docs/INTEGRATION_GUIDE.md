# NuSyQ Integration Guide

This guide helps you set up and wire all components of the NuSyQ multi-AI
ecosystem.

## Quick Start

### 1. Run Automatic Setup

```powershell
# Detect and configure all systems
python scripts/setup_integrations.py

# Configure VS Code extensions
python scripts/integrate_extensions.py
```

### 2. Source Environment Variables

```powershell
# Load auto-generated environment configuration
. .\scripts\set_env.ps1
```

### 3. Verify Integration

```powershell
# Check system health
python scripts/integration_health_check.py

# Test imports
python -c "from src.tools.agent_task_router import AgentTaskRouter; print('✅ OK')"
```

## System Components

### 1. Ollama (Local LLM)

**Detection**: Auto-detected at `http://localhost:11434`

**Manual Setup**:

1. Download from https://ollama.ai
2. Install models: `ollama pull qwen2.5-coder:14b`
3. Verify: `ollama list`

**Configuration**:

- Environment: `OLLAMA_BASE_URL=http://localhost:11434`
- VS Code: Continue.dev extension configured automatically
- Models: qwen2.5-coder, starcoder2, gemma2, deepseek-coder-v2

### 2. ChatDev (Multi-Agent Dev)

**Location**: `~/NuSyQ/ChatDev`

**Manual Setup**:

```powershell
cd ~/NuSyQ
git clone https://github.com/OpenBMB/ChatDev.git
cd ChatDev
pip install -r requirements.txt
```

**Configuration**:

- Environment: `CHATDEV_PATH=C:/Users/keath/NuSyQ/ChatDev`
- Usage: Via `AgentTaskRouter` with `target_system="chatdev"`

### 3. SimulatedVerse (Consciousness Engine)

**Location**: `~/Desktop/SimulatedVerse/SimulatedVerse`

**Manual Setup**:

```powershell
cd ~/Desktop/SimulatedVerse/SimulatedVerse
npm install
npm run dev  # Starts on port 5002
```

**Configuration**:

- Environment: `SIMULATEDVERSE_PATH=...`
- Server: http://localhost:5002
- React UI: http://localhost:3000

### 4. NuSyQ Root (MCP Server & Orchestration)

**Location**: `~/NuSyQ`

**Manual Setup**:

```powershell
cd ~/NuSyQ
.\NuSyQ.Orchestrator.ps1  # Automated setup
```

**Configuration**:

- Environment: `NUSYQ_ROOT_PATH=C:/Users/keath/NuSyQ`
- MCP Server: `python mcp_server/main.py`

## VS Code Extensions

### Required Extensions

All installed automatically via `.vscode/extensions.json`:

- **ms-python.python** - Python language support
- **ms-python.vscode-pylance** - Type checking and IntelliSense
- **ms-python.black-formatter** - Code formatting
- **charliermarsh.ruff** - Linting
- **ms-toolsai.jupyter** - Notebook support
- **SonarSource.sonarlint-vscode** - Code quality
- **Continue.continue** - AI code assistant
- **GitHub.copilot** - AI pair programmer

### AI Coding Extensions

#### 1. GitHub Copilot

- **Status**: Installed ✅
- **Configuration**: Automatic
- **Features**: Inline suggestions, chat, code review

#### 2. Continue.dev

- **Status**: Installed ✅
- **Configuration**: `.continuerc.json` (auto-generated)
- **Backend**: Ollama (qwen2.5-coder, starcoder2)
- **Features**: Tab autocomplete, chat, embeddings

#### 3. Ollama Extensions

- **warm3snow.vscode-ollama** - Ollama integration
- **10nates.ollama-autocoder** - Autocomplete engine
- **technovangelist.ollamamodelfile** - Modelfile syntax

## Integration Workflows

### 1. Conversational Task Routing

```python
from src.tools.agent_task_router import AgentTaskRouter
import asyncio

router = AgentTaskRouter()

# Analyze with Ollama
result = asyncio.run(router.route_task(
    task_type="analyze",
    file_path="src/example.py",
    target_system="ollama"
))

# Generate with ChatDev
result = asyncio.run(router.route_task(
    task_type="generate",
    description="Create REST API with JWT",
    target_system="chatdev"
))
```

### 2. Multi-AI Orchestration

```python
from src.orchestration.multi_ai_orchestrator import MultiAIOrchestrator

orchestrator = MultiAIOrchestrator()
result = await orchestrator.coordinate_task(
    task="Review codebase for security issues",
    systems=["ollama", "consciousness", "github_copilot"]
)
```

### 3. Ecosystem Activation

```python
from src.orchestration.ecosystem_activator import EcosystemActivator

activator = EcosystemActivator()
status = await activator.activate_full_ecosystem()
# Starts Ollama, checks ChatDev, wires consciousness bridge
```

## Environment Variables

Auto-configured by `scripts/setup_integrations.py`:

```powershell
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:CHATDEV_PATH = "C:/Users/keath/NuSyQ/ChatDev"
$env:SIMULATEDVERSE_PATH = "C:/Users/keath/Desktop/SimulatedVerse/SimulatedVerse"
$env:NUSYQ_ROOT_PATH = "C:/Users/keath/NuSyQ"
```

**Persistence**: Add to PowerShell profile or `.env` file

## Testing Integration

### 1. Import Health Check

```powershell
python -c "
from src.tools.agent_task_router import AgentTaskRouter
from src.orchestration.multi_ai_orchestrator import MultiAIOrchestrator
from src.orchestration.ecosystem_activator import EcosystemActivator
print('✅ All core imports successful')
"
```

### 2. Run Integration Tests

```powershell
# Full test suite
python -m pytest tests/test_agent_task_router.py -v

# Quick smoke test
python -m pytest tests/test_agent_task_router.py::test_router_initialization -v
```

### 3. System Health Assessment

```powershell
# Comprehensive health check
python src/diagnostics/system_integration_checker.py

# Quick status
python scripts/integration_health_check.py
```

## Troubleshooting

### Ollama Not Detected

```powershell
# Check service
ollama list

# Start server (if needed)
ollama serve

# Test API
curl http://localhost:11434/api/tags
```

### ChatDev Import Errors

```powershell
# Verify path
$env:CHATDEV_PATH
ls $env:CHATDEV_PATH

# Install dependencies
cd $env:CHATDEV_PATH
pip install -r requirements.txt
```

### Extension Conflicts

```powershell
# Check installed
code --list-extensions

# Reinstall if needed
code --uninstall-extension Continue.continue
code --install-extension Continue.continue
```

## Advanced Configuration

### Custom Ollama Models

```powershell
# Pull additional models
ollama pull deepseek-coder-v2:16b
ollama pull codellama:34b

# Update Continue.dev config
# Edit .continuerc.json to add new models
```

### ChatDev Custom Roles

Edit `ChatDev/CompanyConfig/Default/RoleConfig.json` to customize agent roles.

### Consciousness Bridge

Located in `src/integration/consciousness_bridge.py` - connects SimulatedVerse
semantic awareness with NuSyQ-Hub orchestration.

## Support

- **Documentation**: `/docs`
- **Agent Sessions**: `/docs/Agent-Sessions`
- **System Map**: `/docs/SYSTEM_MAP.md`
- **Routing Rules**: `/docs/ROUTING_RULES.md`

## Next Steps

1. ✅ Run `python scripts/setup_integrations.py`
2. ✅ Source environment: `. .\scripts\set_env.ps1`
3. ✅ Install extensions: `code --install-extension Continue.continue`
4. 🚀 Start using: `python scripts/start_nusyq.py snapshot`
5. 🎯 Try routing: See conversational operator phrases in `AGENTS.md`

---

**Last Updated**: 2025-12-30 **System Version**: NuSyQ-Hub v4.0 Multi-AI
Integration
