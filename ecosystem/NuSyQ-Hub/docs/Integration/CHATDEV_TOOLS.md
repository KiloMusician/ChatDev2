# ChatDev Tools Integration

## Overview

This feature allows ChatDev agents to invoke NuSyQ-Hub utilities as tools during their multi-agent workflows.

## Feature Flag

```json
{
  "chatdev_tools_enabled": {
    "description": "Allow ChatDev agents to invoke Hub utilities as tools",
    "default": false,
    "requires_acl": true,
    "dependencies": ["chatdev_mcp_enabled"]
  }
}
```

## Available Tools

When enabled, ChatDev agents can access:

| Tool | Description |
|------|-------------|
| `hub.analyze` | Code analysis and quality checks |
| `hub.search` | Codebase semantic search |
| `hub.quest` | Quest system operations |
| `hub.heal` | Repository healing utilities |

## Security Considerations

- Requires ACL (Access Control List) enforcement
- Tool invocations are logged to quest system
- Sandboxed execution when `sandbox_runner_enabled` is true

## Configuration

### Enable in Development

```python
from src.system.feature_flags import enable_feature

enable_feature("chatdev_tools_enabled", environment="development")
```

### Tool Registration

Tools are registered in `config/chatdev_tools_registry.json`:

```json
{
  "tools": [
    {
      "name": "hub.analyze",
      "module": "src.tools.agent_task_router",
      "function": "analyze_with_ai"
    }
  ]
}
```

## Related Files

- `src/integration/chatdev_integration.py` - ChatDev integration
- `src/tools/agent_task_router.py` - Tool routing implementation
- `config/feature_flags.json` - Feature configuration
