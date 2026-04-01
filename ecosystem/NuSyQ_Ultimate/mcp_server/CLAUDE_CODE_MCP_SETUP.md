# Claude Code MCP Client Configuration

## Quick Setup Guide

### Step 1: Start the MCP Server

**Option A: VS Code Task (Recommended)**
```
Ctrl+Shift+P → "Tasks: Run Task" → "🚀 Quick Start: MCP + Ollama"
```

**Option B: Manual Terminal**
```powershell
cd C:\Users\keath\NuSyQ
.\.venv\Scripts\python.exe scripts\start_mcp_server.py
```

**Verify Server is Running:**
- You should see: `Uvicorn running on http://127.0.0.1:8765`
- Check: `http://localhost:8765/health` in browser

---

### Step 2: Configure Claude Code MCP Client

**In VS Code Settings (JSON mode):**

Press `Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)"

Add this configuration:

```json
{
  "anthropic.claude-code.mcp": {
    "servers": {
      "nusyq-local": {
        "command": "python",
        "args": [
          "C:/Users/keath/NuSyQ/scripts/start_mcp_server.py"
        ],
        "env": {
          "PYTHONPATH": "C:/Users/keath/NuSyQ",
          "MCP_SERVER_PORT": "8765"
        }
      }
    }
  }
}
```

**Alternative: Direct HTTP Connection**

If Claude Code supports HTTP MCP servers:

```json
{
  "anthropic.claude-code.mcp": {
    "servers": {
      "nusyq-http": {
        "url": "http://localhost:8765/mcp",
        "apiKey": ""  // Leave empty for local server
      }
    }
  }
}
```

---

### Step 3: Restart Claude Code / Reload Window

```
Ctrl+Shift+P → "Developer: Reload Window"
```

---

### Step 4: Verify MCP Connection

**Test the connection:**

In Claude Code chat, try:
```
@nusyq-local What Ollama models are available?
```

Or use the MCP tools directly:
```
Call tool: ollama_query
  model: "qwen2.5-coder:7b"
  prompt: "Hello, are you working?"
```

---

## Available MCP Tools

Once connected, Claude Code can use these tools:

### 1. `ollama_query`
Query local Ollama models for code generation.

**Example:**
```json
{
  "model": "qwen2.5-coder:7b",
  "prompt": "Write a Python function to parse JSON",
  "max_tokens": 500
}
```

### 2. `file_read`
Read files from the NuSyQ workspace.

**Example:**
```json
{
  "path": "C:/Users/keath/NuSyQ/config/manifest.yaml",
  "encoding": "utf-8"
}
```

### 3. `file_write`
Write content to files (use with caution).

**Example:**
```json
{
  "path": "C:/Users/keath/NuSyQ/test_output.txt",
  "content": "Test content",
  "encoding": "utf-8"
}
```

### 4. `get_system_info`
Get NuSyQ ecosystem status.

**Example:**
```json
{}
```

### 5. `jupyter_execute`
Execute Python code in Jupyter environment.

**Example:**
```json
{
  "code": "import sys; print(sys.version)"
}
```

---

## Troubleshooting

### Server Won't Start

**Check Python environment:**
```powershell
C:\Users\keath\NuSyQ\.venv\Scripts\python.exe --version
```

**Check dependencies:**
```powershell
cd C:\Users\keath\NuSyQ
.\.venv\Scripts\pip.exe install -r mcp_server\requirements.txt
```

**Check port availability:**
```powershell
netstat -ano | findstr :8765
```

If port 8765 is in use, kill the process:
```powershell
taskkill /PID <process_id> /F
```

### Claude Code Can't Connect

**Check server logs:**
```
C:\Users\keath\NuSyQ\Logs\mcp_server.log
```

**Verify health endpoint:**
```powershell
curl http://localhost:8765/health
```

Expected response:
```json
{
  "status": "healthy",
  "ollama": true,
  "configurations": true
}
```

### MCP Tools Not Appearing

**Restart MCP connection:**
```
Ctrl+Shift+P → "MCP: Restart Server" → Select "nusyq-local"
```

**Check MCP Developer Tools:**
```
Ctrl+Shift+P → "MCP: Open Developer Settings"
```

Look for "nusyq-local" server status and any error messages.

---

## Advanced Configuration

### Custom Port

Edit `C:\Users\keath\NuSyQ\mcp_server\main.py`:

```python
if __name__ == "__main__":
    app = create_app()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=3001,  # Change port here
        log_level="debug",
    )
```

Then update MCP client config accordingly.

### Remote Access

**⚠️ Security Warning:** Only enable remote access on trusted networks.

Edit server to bind to specific IP:
```python
uvicorn.run(
    app,
    host="192.168.1.100",  # Your machine's IP
    port=8765,
)
```

Add authentication middleware (recommended for production).

---

## Quick Reference

| Action | Command |
|--------|---------|
| Start Server | `Tasks: Run Task` → `🚀 Quick Start: MCP + Ollama` |
| Stop Server | `Ctrl+C` in MCP Server terminal |
| Check Health | `http://localhost:8765/health` |
| View Logs | `C:\Users\keath\NuSyQ\Logs\mcp_server.log` |
| Restart Connection | `MCP: Restart Server` |
| Test Ollama | `curl http://localhost:11434/api/tags` |

---

## Support

If issues persist:

1. Check `mcp_server.log` for detailed error messages
2. Verify Ollama is running: `ollama list`
3. Test MCP endpoint directly: `curl http://localhost:8765/mcp -X POST -H "Content-Type: application/json" -d '{"method":"tools/list","params":{}}'`
4. Review server startup output in terminal

**Last Updated:** 2026-01-10
