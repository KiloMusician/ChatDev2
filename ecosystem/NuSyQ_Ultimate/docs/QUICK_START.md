# NuSyQ Quick Start Guide

Get your AI-powered development workspace running in **5 minutes**.

---

## What is NuSyQ?

**NuSyQ** is a local AI development environment that combines:
- 🤖 **Multiple LLMs** - Run Ollama models locally (no API costs)
- 👥 **Multi-Agent Development** - ChatDev for AI-powered software creation
- 🧠 **AI Assistants** - VS Code extensions (Copilot, Continue.dev, Claude Code)
- 📊 **Orchestration** - Automated setup and health monitoring
- 🔧 **Development Tools** - Jupyter, Docker, Kubernetes support

**Zero external API calls required** - everything runs locally on your machine.

---

## Prerequisites (2 minutes)

### Required
- [x] **Windows 10/11**, **macOS 10.15+**, or **Linux**
- [x] **Python 3.8+** ([python.org/downloads](https://python.org/downloads))
- [x] **Git** ([git-scm.com](https://git-scm.com))
- [x] **VS Code** ([code.visualstudio.com](https://code.visualstudio.com))
- [x] **Ollama** ([ollama.ai](https://ollama.ai)) - Local LLM runtime

### Verify Prerequisites
```bash
python --version   # Should show 3.8 or higher
git --version      # Any recent version
code --version     # VS Code CLI
ollama --version   # Ollama runtime
```

---

## Installation (3 minutes)

### Step 1: Clone Repository
```bash
git clone https://github.com/KiloMusician/NuSyQ.git
cd NuSyQ
```

### Step 2: Run Automated Setup
```powershell
# Windows PowerShell
.\NuSyQ.Orchestrator.ps1

# Linux/macOS (with PowerShell Core)
pwsh ./NuSyQ.Orchestrator.ps1
```

The orchestrator will:
1. ✅ Create Python virtual environment
2. ✅ Install dependencies
3. ✅ Pull Ollama models (qwen2.5-coder, gemma2, etc.)
4. ✅ Install VS Code extensions
5. ✅ Configure environment
6. ✅ Run health checks

**Time:** ~3-5 minutes (depends on model download speed)

### Step 3: Verify Installation
```bash
# Activate virtual environment
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # Linux/macOS

# Test MCP server
python mcp_server/main.py
# Should see: "Uvicorn running on http://0.0.0.0:3000"

# Test ChatDev integration
python nusyq_chatdev.py --setup-only
# Should see: "[OK] Setup verification complete!"
```

---

## First Steps

### 1. Start the MCP Server
```bash
python mcp_server/main.py
```

Open http://localhost:3000 in browser - you should see the API welcome page.

### 2. Test Ollama Integration
```bash
# List available models
ollama list

# Should see:
# qwen2.5-coder:14b
# gemma2:9b
# codellama:7b
# ... etc
```

### 3. Create Your First Project with ChatDev
```bash
python nusyq_chatdev.py --task "Create a simple calculator with GUI"
```

ChatDev will:
1. Analyze requirements
2. Design architecture
3. Write code (using Ollama models)
4. Review and test
5. Generate documentation

Output appears in `ChatDev/WareHouse/[ProjectName]/`

### 4. Try Symbolic Tracking (ΞNuSyQ Framework)
```bash
python nusyq_chatdev.py \
  --task "Build a REST API with FastAPI" \
  --symbolic \
  --msg-id 1
```

This enables advanced message tracking with symbolic tags.

---

## VS Code Extensions

Open VS Code in the NuSyQ folder:
```bash
code .
```

### Installed Extensions
The orchestrator installed these AI assistants:

1. **Claude Code** (`anthropic.claude-code`)
   - Advanced AI coding assistant
   - Press `Ctrl+Shift+P` → "Claude Code: Start"

2. **Continue.dev** (`Continue.continue`)
   - Uses local Ollama models
   - Free autocomplete and chat
   - No API key needed!

3. **GitHub Copilot** (`GitHub.copilot`)
   - Requires GitHub account
   - Sign in: `Ctrl+Shift+P` → "GitHub Copilot: Sign In"

4. **Python** (`ms-python.python`)
   - IntelliSense, debugging, testing

5. **Jupyter** (`ms-toolsai.jupyter`)
   - Run `.ipynb` notebooks

---

## Quick Recipes

### Run a Simple Ollama Query
```bash
curl -X POST http://localhost:11434/api/generate -d '{
  "model": "qwen2.5-coder:7b",
  "prompt": "Write a Python function to sort a list",
  "stream": false
}'
```

### Use Multi-Model Consensus
```bash
python nusyq_chatdev.py \
  --task "Optimize this algorithm" \
  --consensus \
  --models qwen2.5-coder:14b,codellama:7b
```

### Check System Health
```bash
curl http://localhost:3000/health
```

Returns status of Ollama, Jupyter, and other components.

### Query via MCP Server
```bash
curl -X POST http://localhost:3000/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "ollama_query",
    "arguments": {
      "model": "qwen2.5-coder:7b",
      "prompt": "Explain async/await in Python"
    }
  }'
```

---

## Configuration

### Key Files
- `nusyq.manifest.yaml` - System manifest (models, extensions, packages)
- `config/environment.json` - Runtime configuration (auto-generated)
- `.vscode/settings.json` - VS Code settings
- `knowledge-base.yaml` - Learning log

### Add a New Model
1. Edit `nusyq.manifest.yaml`:
   ```yaml
   ollama_models:
     - your-new-model:7b
   ```

2. Pull the model:
   ```bash
   ollama pull your-new-model:7b
   ```

3. Verify:
   ```bash
   python nusyq_chatdev.py --setup-only
   ```

### Change Default Coding Model
Edit `nusyq_chatdev.py`:
```python
DEFAULT_CODING_MODEL = "qwen2.5-coder:14b"  # Change this
```

---

## Common Issues

### Ollama Not Running
```bash
# Windows: Check system tray for Ollama icon
# Linux: sudo systemctl start ollama
# macOS: Start Ollama app from Applications

# Verify
ollama list
```

### Port 3000 Already in Use
```bash
# Windows
netstat -ano | findstr :3000

# Linux/macOS
lsof -i :3000

# Kill the process or use different port in mcp_server/main.py
```

### ChatDev API Key Error
This means the Ollama integration fix wasn't applied. Run:
```bash
python nusyq_chatdev.py --setup-only
```

Should show `[OK]` messages. If not, see [CHATDEV_FIX_SUMMARY.md](../CHATDEV_FIX_SUMMARY.md).

### VS Code Extensions Not Working
```bash
# Reinstall extensions
code --install-extension Continue.continue --force
code --install-extension anthropic.claude-code --force

# Reload VS Code
# Press Ctrl+Shift+P → "Developer: Reload Window"
```

### Model Download Slow
Ollama models are large (4-9 GB). Download times:
- **qwen2.5-coder:7b** - 4.7 GB (~5-10 min on fast connection)
- **qwen2.5-coder:14b** - 9 GB (~10-20 min)
- **gemma2:9b** - 5.4 GB (~7-15 min)

Tip: Pull one model at a time:
```bash
ollama pull qwen2.5-coder:7b  # Start with smaller model
```

---

## Next Steps

### Explore Features
- [x] Read [AI_Hub/LLM_Orchestration_Guide.md](../AI_Hub/LLM_Orchestration_Guide.md)
- [x] Try [NUSYQ_CHATDEV_GUIDE.md](../NUSYQ_CHATDEV_GUIDE.md) for advanced usage
- [x] Check [CODE_QUALITY_REPORT.md](../CODE_QUALITY_REPORT.md) for code insights

### Start Building
```bash
# Create a web app
python nusyq_chatdev.py --task "Build a Flask web app with user auth"

# Create a data tool
python nusyq_chatdev.py --task "Create a CSV to JSON converter with GUI"

# Create a game
python nusyq_chatdev.py --task "Create a simple Pong game with Pygame"
```

### Customize Your Setup
- Add more Ollama models to `nusyq.manifest.yaml`
- Install additional VS Code extensions
- Configure `continue.dev` for your preferred models
- Set up Jupyter notebooks in `Jupyter/` folder

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   VS Code IDE                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐   │
│  │ Claude Code│  │Continue.dev│  │  Copilot   │   │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘   │
└────────┼───────────────┼───────────────┼──────────┘
         │               │               │
         └───────────────┴───────────────┘
                         │
            ┌────────────▼────────────┐
            │   MCP Server (FastAPI)  │
            │   http://localhost:3000 │
            └────────────┬────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼─────┐   ┌────▼─────┐   ┌────▼─────┐
    │  Ollama  │   │ ChatDev  │   │ Jupyter  │
    │  Models  │   │Multi-Agent│   │Notebooks │
    └──────────┘   └──────────┘   └──────────┘
```

**Flow:**
1. User writes code in VS Code
2. AI extensions query MCP server
3. MCP server routes to Ollama/ChatDev/Jupyter
4. Results returned to VS Code
5. All local - no external APIs!

---

## Resource Requirements

### Minimum
- **RAM:** 16 GB (8 GB may work with smaller models)
- **Storage:** 50 GB free (for models and projects)
- **CPU:** 4 cores, 2.5 GHz+
- **GPU:** Optional (CPU inference works fine)

### Recommended
- **RAM:** 32 GB (run larger models comfortably)
- **Storage:** 100+ GB SSD
- **CPU:** 8 cores, 3.0 GHz+
- **GPU:** NVIDIA RTX 3060+ or AMD equivalent (10x faster inference)

### Model Sizes
| Model | Size | RAM Required | Speed (CPU) |
|-------|------|--------------|-------------|
| qwen2.5-coder:7b | 4.7 GB | 8 GB | Fast |
| qwen2.5-coder:14b | 9 GB | 16 GB | Medium |
| codellama:7b | 3.8 GB | 8 GB | Fast |
| gemma2:9b | 5.4 GB | 12 GB | Medium |
| deepseek-coder-v2:16b | 9.1 GB | 16 GB | Slow |

Tip: Start with 7B models, upgrade to 14B+ if you have enough RAM.

---

## Getting Help

### Documentation
- **This guide** - Quick start
- [Guide_Contributing_AllUsers.md](../Guide_Contributing_AllUsers.md) - Development guide
- [CODE_QUALITY_REPORT.md](../CODE_QUALITY_REPORT.md) - Code insights
- `AI_Hub/` - Detailed integration guides

### Troubleshooting
1. Check `knowledge-base.yaml` for similar issues
2. Run `python deep_analysis.py` for code analysis
3. Search [GitHub Issues](https://github.com/KiloMusician/NuSyQ/issues)

### Community
- **Issues:** Report bugs on GitHub
- **Discussions:** Ask questions on GitHub Discussions
- **Contributing:** See [Guide_Contributing_AllUsers.md](../Guide_Contributing_AllUsers.md)

---

## What's Next?

You're now ready to use NuSyQ! Try:

1. **Build a project with ChatDev**
   ```bash
   python nusyq_chatdev.py --task "Your idea here"
   ```

2. **Explore VS Code AI features**
   - Use Continue.dev for inline suggestions
   - Try Claude Code for complex refactoring
   - Ask Copilot for code explanations

3. **Customize your workspace**
   - Add more models
   - Install domain-specific extensions
   - Create custom ChatDev configurations

4. **Contribute back**
   - Fix a TODO
   - Add a feature
   - Improve documentation

---

**Happy coding!** 🚀

Questions? Check [Guide_Contributing_AllUsers.md](../Guide_Contributing_AllUsers.md) or open an issue.
