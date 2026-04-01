# Claude Code Integration Guide

## Quick Setup

### 1. Verify MCP Server is Running
```bash
# Check server status
curl http://localhost:3000/health

# Or in PowerShell
Invoke-RestMethod -Uri "http://localhost:3000/health"
```

### 2. Configure Claude Code
1. Open Claude Code
2. Go to Settings → Integrations
3. Add Custom Connector:
   - **Name**: NuSyQ MCP Server
   - **URL**: `http://localhost:3000/mcp`
   - **Type**: Model Context Protocol

### 3. Test Connection
Send this message to Claude Code after connecting:
```
Please use the system_info tool to show me the status of the NuSyQ AI ecosystem.
```

Expected response should include:
- System information
- Available Ollama models
- Configuration status

### 4. Test AI Model Integration
```
Use the ollama_query tool with the qwen2.5-coder:7b model to write a Python function that calculates the factorial of a number.
```

## Available Tools in Claude Code

Once connected, Claude can use these tools:

### `ollama_query`
Query local AI models for code generation, analysis, and assistance.

**Example usage:**
```
Use ollama_query with model "qwen2.5-coder:14b" to refactor this Python code: [paste code here]
```

### `file_read` / `file_write`
Read and write files in the NuSyQ workspace.

**Example usage:**
```
Read the file "config/config_manager.py" and explain its structure.
```

### `system_info`
Get information about the AI ecosystem, models, and configuration.

**Example usage:**
```
Show me the current system information and available AI models.
```

### `run_jupyter_cell`
Execute Python code in the Jupyter environment.

**Example usage:**
```
Execute this Python code in Jupyter:
import numpy as np
print(np.array([1, 2, 3]) * 2)
```

## Troubleshooting

### Connection Issues
1. **Server not responding**: Check if MCP server is running with VS Code task "Start MCP Server"
2. **Wrong URL**: Ensure Claude Code is configured with `http://localhost:3000/mcp`
3. **Firewall**: Check Windows Firewall allows connections on port 3000

### Model Issues
1. **Ollama not available**: Run `ollama list` to check models
2. **Model not found**: Check available models with `system_info` tool
3. **Slow responses**: Consider using smaller models like `qwen2.5-coder:7b`

### Debug Mode
Start MCP server in debug mode:
```bash
# Use VS Code launch configuration "Debug MCP Server"
# Or set environment variable
DEBUG=true python mcp_server/main.py
```

## Remote Access (Optional)

To access from remote Claude Code instances:

1. **Configure Firewall**:
   ```powershell
   New-NetFirewallRule -DisplayName "NuSyQ MCP Server" -Direction Inbound -Protocol TCP -LocalPort 3000 -Action Allow
   ```

2. **Update Server Configuration**:
   - Edit `mcp_server/main.py`
   - Change `host="localhost"` to `host="0.0.0.0"`

3. **Use External IP**:
   - Find your external IP: `Get-NetIPAddress -AddressFamily IPv4`
   - Configure Claude Code with: `http://YOUR_IP:3000/mcp`

**Security Note**: Only enable remote access on trusted networks.

---
*Ready to bridge Claude Code with your local AI ecosystem!*
