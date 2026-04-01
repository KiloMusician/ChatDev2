# n8n and Base44 Integration

This repository provides optional helpers for workflow automation and compact data encoding.

## n8n
- Module: `src/integration/n8n_integration.py`
- Class `N8NClient` triggers n8n workflows via HTTP webhooks.
- Configure the base URL with the `N8N_URL` environment variable.

Example:
```python
from integration.n8n_integration import N8NClient
client = N8NClient()
client.trigger_workflow("my-workflow", {"hello": "world"})
```

## Base44 Encoding
- Module: `src/utils/base44.py`
- Functions `encode` and `decode` convert between bytes and a custom base44 string.
- Useful for compact payloads within workflow steps.

```python
from utils import base44
encoded = base44.encode(b"data")
original = base44.decode(encoded)
```
