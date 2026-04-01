# ChatDev MCP Server Integration

## Overview

The ChatDev MCP (Model Context Protocol) Server exposes ChatDev as a uniform agent coordination endpoint for the NuSyQ ecosystem.

## Feature Flag

```json
{
  "chatdev_mcp_enabled": {
    "description": "Expose ChatDev as MCP server for uniform agent coordination",
    "default": true,
    "status": "production-ready"
  }
}
```

## Configuration

### Environment Variables

- `CHATDEV_PATH`: Path to ChatDev installation (typically `NuSyQ/ChatDev/`)
- `MCP_SERVER_PORT`: Port for MCP server (default: 8081)

### Feature Dependencies

- Requires MCP server to be running
- ChatDev installation must be available

## Usage

### Starting the MCP Server

```bash
python -m src.integration.mcp_server
```

### Invoking ChatDev via MCP

```python
from src.integration.mcp_server import MCPClient

client = MCPClient("http://localhost:8081")
result = await client.invoke("chatdev.generate", {
    "task": "Create a Python CLI tool",
    "project_name": "my_tool"
})
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   NuSyQ-Hub     │────▶│   MCP Server    │────▶│    ChatDev      │
│   Orchestrator  │     │   (Port 8081)   │     │   Multi-Agent   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Related Files

- `src/integration/mcp_server.py` - MCP server implementation
- `src/integration/chatdev_integration.py` - ChatDev integration layer
- `config/feature_flags.json` - Feature flag configuration

## See Also

- [CHATDEV2_INTEGRATION.md](./CHATDEV2_INTEGRATION.md) - Legacy ChatDev integration docs
- [ChatDev Documentation](https://github.com/OpenBMB/ChatDev)
