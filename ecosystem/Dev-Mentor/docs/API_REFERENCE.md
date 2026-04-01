# API Reference

## Game Endpoints

### POST `/api/game/command`
Execute a game command.
- **Body**: `{"session_id": "string", "command": "string"}`
- **Response**: `{"output": [{"s": "string", "t": "string"}], "state": {...}}`

### GET `/api/game/state`
Get full state for a session.
- **Query**: `session_id=string`
- **Response**: Full JSON state object.

### GET `/api/sessions`
List all active session IDs.

## Serena (Memory) Endpoints

### POST `/api/serena/search`
Semantic search over codebase.
- **Body**: `{"query": "string", "top_k": 5}`

### GET `/api/serena/status`
Get memory indexing status.

## MCP Endpoints

### GET `/api/mcp/tools`
List available MCP tools.

### POST `/api/mcp/call`
Call an MCP tool via REST.

## Admin Endpoints

### GET `/api/health`
Service health check.

### GET `/api/admin/status`
Server uptime and resource usage.
