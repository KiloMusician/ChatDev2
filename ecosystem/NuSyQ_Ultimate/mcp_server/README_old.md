# NuSyQ MCP Server

A Model Context Protocol (MCP) server that connects Claude Code to the NuSyQ AI ecosystem, providing access to local Ollama models, file system operations, and development utilities.

## Features

- **Ollama Integration**: Query local AI models (qwen2.5-coder, llama3.1, codellama, phi3.5)
- **File Operations**: Read/write files with proper encoding support
- **System Information**: Get ecosystem status and health checks
- **Jupyter Integration**: Execute code in Jupyter environment
- **Remote Access**: Configurable for remote Claude Code connections
- **Health Monitoring**: Component status and diagnostics

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Server**:
   ```bash
   python main.py
   ```

3. **Configure Claude Code**:
   - Add custom connector in Claude Code
   - Set URL: `http://localhost:3000/mcp`
   - Test connection with health endpoint: `http://localhost:3000/health`

## Available Tools

### `ollama_query`
Query local Ollama models for code generation and analysis.

**Parameters**:
- `model` (required): Model name (e.g., "qwen2.5-coder:7b")
- `prompt` (required): Query prompt
- `max_tokens` (optional): Maximum response tokens (default: 100)

### `file_read`
Read file contents from the local filesystem.

**Parameters**:
- `path` (required): File path
- `encoding` (optional): Text encoding (default: "utf-8")

### `file_write`
Write content to a file.

**Parameters**:
- `path` (required): File path
- `content` (required): File content
- `encoding` (optional): Text encoding (default: "utf-8")

### `system_info`
Get system and AI ecosystem information.

**Parameters**:
- `component` (optional): Component to query ("all", "ollama", "models", "config")

### `run_jupyter_cell`
Execute Python code in Jupyter environment.

**Parameters**:
- `code` (required): Python code to execute
- `kernel` (optional): Kernel type (default: "python3")

## API Endpoints

- `GET /` - Server information
- `POST /mcp` - Main MCP protocol endpoint
- `POST /tools/execute` - Direct tool execution
- `GET /health` - Health check

## Configuration

The server automatically loads configuration from:
- `../nusyq.manifest.yaml` - Main system manifest
- `../knowledge-base.yaml` - Knowledge base configuration
- `../AI_Hub/ai-ecosystem.yaml` - AI ecosystem settings
- `../config/tasks.yaml` - Task definitions

## Remote Access Setup

For remote Claude Code access:

1. **Configure Firewall**: Allow port 3000 through Windows Firewall
2. **Update Host**: Change `host="0.0.0.0"` in `main.py` to bind all interfaces
3. **Security**: Add authentication for production use
4. **SSL/TLS**: Configure HTTPS for secure connections

## Example Usage

```python
import requests

# Query Ollama model
response = requests.post("http://localhost:3000/tools/execute", json={
    "name": "ollama_query",
    "arguments": {
        "model": "qwen2.5-coder:7b",
        "prompt": "Write a Python function to calculate fibonacci numbers"
    }
})

# Read a file
response = requests.post("http://localhost:3000/tools/execute", json={
    "name": "file_read",
    "arguments": {"path": "NuSyQ_Root_README.md"}
})
```

## Health Monitoring

Check server health and component status:

```bash
curl http://localhost:3000/health
```

Response includes:
- Server status
- Ollama connection status
- Configuration load status
- Component health checks

## Development

1. **Install Development Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Tests**:
   ```bash
   pytest
   ```

3. **Start Development Server**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 3000
   ```

## Security Notes

- For production use, implement proper authentication
- Configure CORS settings appropriately
- Use HTTPS for remote connections
- Validate and sanitize all file operations
- Limit resource usage for code execution

## Troubleshooting

**Connection Issues**:
- Verify Ollama is running: `ollama list`
- Check firewall settings
- Confirm port 3000 is available

**Configuration Errors**:
- Validate YAML files: `python -c "import yaml; yaml.safe_load(open('config.yaml'))"`
- Check file permissions
- Review server logs

**Performance Issues**:
- Monitor resource usage
- Adjust timeout settings
- Configure connection pooling
