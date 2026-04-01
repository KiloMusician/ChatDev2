# 🚀 NuSyQ AI Ecosystem - Quick Start Guide

## 📋 Prerequisites

✅ **Windows 10/11** with PowerShell 7+
✅ **Python 3.9+** installed
✅ **VS Code** installed
✅ **Ollama** installed and running
✅ **Git** installed

---

## ⚡ 5-Minute Setup

### Step 1: Install Ollama Models (2 minutes)

```powershell
# Install primary coding models
ollama pull qwen2.5-coder:14b   # Best quality (9GB)
ollama pull qwen2.5-coder:7b    # Fast autocomplete (4.7GB)
ollama pull nomic-embed-text    # Embeddings for Continue.dev
```

### Step 2: Configure ChatDev for Ollama (30 seconds)

```powershell
# Navigate to ChatDev
cd ChatDev

# Load Ollama environment variables
Get-Content .env.ollama | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
    }
}
```

### Step 3: Install Continue.dev Extension (1 minute)

```powershell
# Install Continue extension for VS Code
code --install-extension Continue.continue
```

**Configure Continue** (create `~/.continue/config.json`):

```json
{
  "models": [{
    "title": "Qwen2.5 Coder 14B",
    "provider": "ollama",
    "model": "qwen2.5-coder:14b",
    "apiBase": "http://localhost:11434"
  }],
  "tabAutocompleteModel": {
    "provider": "ollama",
    "model": "qwen2.5-coder:7b"
  }
}
```

### Step 4: Start MCP Server (30 seconds)

```powershell
# Open new terminal
cd mcp_server
python main.py
```

The MCP server will start on `http://localhost:3000`

---

## 🎯 First AI-Powered Project

### Generate a Full Application with ChatDev

```powershell
cd ChatDev

# Create a calculator app
python run_ollama.py --task "Create a calculator with GUI" \
                     --name "Calculator" \
                     --model qwen2.5-coder:14b
```

**What happens:**
1. AI agents analyze requirements
2. CEO, CTO, Programmer agents collaborate
3. Code is generated with tests
4. Output: `WareHouse/Calculator_NuSyQ_<timestamp>/`

### Open in VS Code with AI Assistants

```powershell
# Open generated project
code ../WareHouse/Calculator_NuSyQ_*/
```

**AI Tools Now Active:**
- ✅ **Claude Code**: Chat panel (right side)
- ✅ **Continue.dev**: Inline suggestions (Tab to accept)
- ✅ **GitHub Copilot**: Pattern suggestions
- ✅ **MCP Server**: Background AI orchestration

---

## 🔧 Using the AI Tools

### 1. Continue.dev (Local Ollama)

**Autocomplete:**
- Start typing → See suggestions
- Press `Tab` to accept
- `Esc` to dismiss

**Chat:**
- Press `Ctrl+L` (Windows) or `Cmd+L` (Mac)
- Type your question
- Get instant local AI responses

**Quick Commands:**
```
/edit     - Edit selected code
/comment  - Add documentation
/test     - Generate tests
/explain  - Explain code
/cmd      - Generate shell command
```

### 2. Claude Code (Cloud AI)

- Click Chat icon in VS Code
- Ask complex architectural questions
- Get detailed code reviews
- Architecture planning

### 3. ChatDev (Multi-Agent)

```powershell
# Generate new features
python run_ollama.py --task "Add login system to Calculator" \
                     --name "CalculatorAuth" \
                     --config "incremental" \
                     --path "../WareHouse/Calculator_NuSyQ_*/"
```

### 4. MCP Server (API Access)

```python
import requests

# Query Ollama via MCP
response = requests.post("http://localhost:3000/tools/execute", json={
    "name": "ollama_query",
    "arguments": {
        "model": "qwen2.5-coder:14b",
        "prompt": "Write a Python sorting algorithm"
    }
})

print(response.json()["result"]["response"])
```

---

## 🎨 Workflow Examples

### Example 1: REST API Development

```powershell
# 1. Generate API with ChatDev
cd ChatDev
python run_ollama.py --task "Create REST API for task management with SQLite" \
                     --name "TaskAPI" \
                     --model qwen2.5-coder:14b

# 2. Open in VS Code
code ../WareHouse/TaskAPI_NuSyQ_*/

# 3. Use Continue.dev for enhancements
# - Ctrl+L: "Add authentication to the API"
# - Select code → Right-click → Continue: Edit
# - Tab for autocomplete
```

### Example 2: Learning Python

```powershell
# 1. Generate learning projects
cd ChatDev
python run_ollama.py --task "Create tutorial project for Python async/await" \
                     --name "AsyncTutorial"

# 2. Explore with AI
# - Open in VS Code
# - Use Continue.dev: /explain on confusing code
# - Ask Claude Code for deeper explanations
```

### Example 3: Code Refactoring

```powershell
# 1. Open existing project
code my-project/

# 2. Select messy code
# 3. Continue.dev: /edit
# 4. Prompt: "Refactor this to be more maintainable"
# 5. Review with Claude Code
```

---

## 📊 Model Selection Guide

| Task | Recommended Model | Why |
|------|-------------------|-----|
| **Autocomplete** | qwen2.5-coder:7b | Fast, low latency |
| **Code Gen** | qwen2.5-coder:14b | Best quality |
| **Architecture** | Claude Code | Complex reasoning |
| **Quick Fixes** | Continue.dev (7B) | Instant responses |
| **Full Projects** | ChatDev (14B) | Multi-agent collaboration |

---

## 🎯 Keyboard Shortcuts

### Continue.dev
- `Ctrl+L` / `Cmd+L` - Open chat
- `Ctrl+I` / `Cmd+I` - Inline edit
- `Tab` - Accept suggestion
- `Esc` - Dismiss

### VS Code with AI
- `Ctrl+Shift+P` - Command palette
- `Ctrl+K Ctrl+I` - Show hover info
- `F12` - Go to definition (AI-enhanced)

---

## 🐛 Troubleshooting

### Ollama Not Responding
```powershell
# Check Ollama status
ollama list

# Restart Ollama service (Windows)
# Stop and start from Services, or:
ollama serve
```

### Continue.dev No Suggestions
```powershell
# Pull models
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5-coder:14b

# Restart VS Code
# Check Continue logs: Ctrl+Shift+P → "Continue: Show Logs"
```

### ChatDev Errors
```powershell
# Verify environment
cd ChatDev
Get-Content .env.ollama

# Check Ollama API
curl http://localhost:11434/api/tags

# Re-run with debug
python run_ollama.py --task "..." --name "..." --model qwen2.5-coder:14b
```

### MCP Server Not Starting
```powershell
# Install dependencies
cd mcp_server
pip install -r requirements.txt

# Check port availability
netstat -an | findstr ":3000"

# Start on different port
python main.py  # Edit main.py to change port if needed
```

---

## 🚀 Advanced Usage

### Multi-Model Consensus

```python
# Query multiple models for best answer
import requests

models = ["qwen2.5-coder:14b", "codellama:7b", "gemma2:9b"]
prompt = "Optimize this database query: SELECT * FROM users WHERE ..."

for model in models:
    response = requests.post("http://localhost:3000/tools/execute", json={
        "name": "ollama_query",
        "arguments": {"model": model, "prompt": prompt}
    })
    print(f"\n{model}:")
    print(response.json()["result"]["response"])
```

### Custom ChatDev Workflows

```powershell
# Human-in-the-loop development
python run_ollama.py --task "Create game" --config "Human" --name "Game"

# Art mode (with image generation)
python run_ollama.py --task "Create UI mockup" --config "Art" --name "UIDesign"

# Incremental development
python run_ollama.py --task "Add feature" \
                     --config "incremental" \
                     --path "./existing-project"
```

---

## 📚 Next Steps

1. **Explore Documentation:**
   - [LLM_Orchestration_Guide.md](AI_Hub/LLM_Orchestration_Guide.md) - Complete orchestration guide
   - [ollama-copilot-config.md](AI_Hub/ollama-copilot-config.md) - Detailed Copilot setup
   - [ChatDev/NuSyQ_Root_README.md](ChatDev/NuSyQ_Root_README.md) - ChatDev documentation

2. **Join the Community:**
   - Share your AI-generated projects
   - Contribute workflows and configurations
   - Report issues and suggest improvements

3. **Advanced Features:**
   - Set up ΞNuSyQ ∆ΨΣ framework integration
   - Configure multi-agent collaboration
   - Build custom AI pipelines

---

## ✨ Success Indicators

You're set up correctly when:

✅ `ollama list` shows your models
✅ Continue.dev shows suggestions in VS Code
✅ ChatDev generates projects without errors
✅ MCP server responds at `http://localhost:3000/health`
✅ Claude Code answers questions in VS Code

**🎉 Congratulations! You now have a fully functional local AI development ecosystem!**

---

## 📞 Support

- **Issues**: Report at project repository
- **Questions**: Check [LLM_Orchestration_Guide.md](AI_Hub/LLM_Orchestration_Guide.md)
- **Community**: Join Discord/forum (if available)
- **Documentation**: Browse [AI_Hub/](AI_Hub/) folder

**Happy AI-Powered Coding! 🚀🤖**
