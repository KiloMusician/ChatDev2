# Agent Context Integration

This document describes the lightweight Agent Context CLI and patterns for integrating local contexts into the NuSyQ ecosystem.

Files added:

- `scripts/agent_context_cli.py` - CLI to register local files into `AgentContextManager` and optionally push to MCP.

Quick usage:

```powershell
python scripts/agent_context_cli.py --namespace kilo --path src/tools/kilo_discovery_system.py
```

To push to MCP (if running):

```powershell
python scripts/agent_context_cli.py --namespace kilo --path src/tools/kilo_discovery_system.py --push-mcp http://localhost:8000/mcp
```

Design notes:
- The CLI uses the existing `AgentContextManager` in `src/tools` so contexts are persisted under the repo.
- The MCP push is optional and best-effort; a running MCP server is required to accept the post.
