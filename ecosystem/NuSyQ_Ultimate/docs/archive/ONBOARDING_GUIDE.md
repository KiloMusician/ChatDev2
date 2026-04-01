# NuSyQ AI Ecosystem - Complete Onboarding Guide

## Welcome to NuSyQ! 🚀

Your local AI development ecosystem is now configured and ready for action. This guide will walk you through everything you need to know to get started.

## What's Installed and Configured

### ✅ Core Infrastructure
- **MCP Server**: Bridges Claude Code with local AI models (Port 3000)
- **Python Environment**: Virtual environment with all dependencies
- **Ollama Models**: 7 local AI models for development assistance
- **ChatDev**: Multi-agent software development framework
- **Configuration System**: YAML-based modular configuration management

### ✅ Available AI Models
- **qwen2.5-coder:14b** - Advanced coding model (recommended for complex tasks)
- **qwen2.5-coder:7b** - Lightweight coding model (recommended for speed)
- **codellama:7b** - Meta's code-focused model
- **starcoder2:15b** - Advanced code generation
- **llama3.1:8b** - General purpose language model
- **gemma2:9b** - Google's efficient model
- **phi3.5:latest** - Microsoft's compact model

### ✅ Development Tools
- **VS Code Integration**: Tasks and launch configurations
- **Jupyter Integration**: Code execution and analysis
- **PowerShell Orchestrator**: Automated setup and maintenance
- **Health Monitoring**: Comprehensive system status tracking

## Quick Start Guide

### 1. Verify Everything is Running

```bash
# Check Ollama models
ollama list

# Test MCP server health
curl http://localhost:3000/health

# Or in PowerShell
Invoke-RestMethod -Uri "http://localhost:3000/health"
```

### 2. Start the MCP Server (if not running)

```bash
# Using VS Code task: Ctrl+Shift+P -> "Run Task" -> "Start MCP Server"
# Or manually:
python mcp_server/main.py
```

### 3. Connect Claude Code to Your Local Ecosystem

1. **Open Claude Code**
2. **Go to Settings → Integrations**
3. **Add Custom Connector**:
   - Name: "NuSyQ Local AI"
   - URL: `http://localhost:3000/mcp`
   - Type: Model Context Protocol

### 4. Test Claude Integration

Send this message to Claude Code:
```
Please use the system_info tool to show me the current status of my NuSyQ AI ecosystem.
```

Expected response should include system information and available models.

### 5. Try ChatDev with Local Models

```bash
# Create a simple application using local AI
python nusyq_chatdev.py --task "create a simple calculator web app"

# Check the output
ls ChatDev/WareHouse/
```

## Available Workflows

### 🔧 Direct Model Interaction

Query any Ollama model through Claude Code:
```
Use the ollama_query tool with qwen2.5-coder:7b to write a Python function that reads a CSV file and creates a bar chart.
```

### 🏗️ Multi-Agent Development

Use ChatDev for complex software projects:
```bash
python nusyq_chatdev.py --task "create a task management web application with user authentication"
```

### 📁 File Operations

Manage files through Claude Code:
```
Read the file "config/config_manager.py" and explain its main functions.

Write a new configuration file called "my_config.yaml" with these settings: [describe settings]
```

### 🔬 Code Analysis

Execute and test code through Jupyter:
```
Execute this Python code in Jupyter:
import pandas as pd
df = pd.read_csv('data.csv')
print(df.describe())
```

## Configuration Management

### YAML Configuration Files
- **nusyq.manifest.yaml**: System-wide settings
- **knowledge-base.yaml**: Learning and session tracking
- **AI_Hub/ai-ecosystem.yaml**: AI model configurations
- **config/tasks.yaml**: Workflow definitions

### Modifying Configurations
```bash
# Validate all configurations
python config/config_manager.py

# Edit configurations with VS Code integration
code config/config_manager.py
```

## Troubleshooting

### MCP Server Issues
```bash
# Check if running
netstat -ano | findstr :3000

# Restart server
python mcp_server/main.py

# Debug mode
DEBUG=true python mcp_server/main.py
```

### Ollama Model Issues
```bash
# Check available models
ollama list

# Pull missing models
ollama pull qwen2.5-coder:7b

# Test model directly
ollama run qwen2.5-coder:7b "Hello, write a Python function"
```

### ChatDev Issues
```bash
# Test setup only
python nusyq_chatdev.py --task "test" --setup-only

# Check ChatDev logs
cat ChatDev/WareHouse/*/ChatChainConfig.json
```

## Advanced Usage

### Custom Model Configuration

Edit `AI_Hub/ai-ecosystem.yaml` to add new models or modify settings:
```yaml
local_models:
  primary: "qwen2.5-coder:14b"
  secondary: "codellama:7b"
  experimental: "starcoder2:15b"
```

### Custom ChatDev Workflows

Create new company configurations in `ChatDev/CompanyConfig/`:
```bash
cp -r ChatDev/CompanyConfig/NuSyQ_Ollama ChatDev/CompanyConfig/MyCustom
# Edit the JSON files in MyCustom/
```

### Remote Access (Optional)

Enable remote Claude Code access:
```bash
# Configure firewall
New-NetFirewallRule -DisplayName "NuSyQ MCP" -Direction Inbound -Protocol TCP -LocalPort 3000 -Action Allow

# Update server to bind all interfaces (edit mcp_server/main.py)
# Change host="localhost" to host="0.0.0.0"
```

## Performance Tips

### Model Selection
- **Fast development**: Use `qwen2.5-coder:7b`
- **Complex projects**: Use `qwen2.5-coder:14b`
- **Code review**: Use `codellama:7b`
- **Documentation**: Use `llama3.1:8b`

### Resource Management
- **Monitor CPU/RAM usage** during model inference
- **Use smaller models** for simple tasks
- **Batch similar requests** for efficiency

## Next Steps

### Learning Path
1. **Start with simple Claude Code queries** to test model responses
2. **Create a small project with ChatDev** to understand multi-agent workflow
3. **Experiment with different models** to find your preferences
4. **Build custom tools** by extending the MCP server
5. **Integrate with existing workflows** using VS Code tasks

### Community Resources
- **Documentation**: Check `Reports/` directory for detailed guides
- **Examples**: Explore `ChatDev/WareHouse/` for generated projects
- **Configurations**: Study `config/` directory for customization ideas

## Support and Maintenance

### Regular Maintenance
```bash
# Update models
ollama pull qwen2.5-coder:7b

# Health check
python config/config_manager.py

# Run orchestrator for updates
./NuSyQ.Orchestrator.ps1
```

### Backup Important Data
```bash
# Backup configurations
cp -r config/ backup/config_$(date +%Y%m%d)/

# Backup ChatDev projects
cp -r ChatDev/WareHouse/ backup/projects_$(date +%Y%m%d)/
```

---

🎉 **Congratulations!** Your NuSyQ AI ecosystem is fully configured and ready for productive development. Start with simple queries in Claude Code and gradually explore the more advanced features.

**Happy coding with local AI!** 🤖✨
