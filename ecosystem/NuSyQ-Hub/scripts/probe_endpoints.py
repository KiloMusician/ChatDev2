import json
import os

import requests

endpoints = {
    "ollama": os.environ.get("OLLAMA_HOST", "http://localhost:11434") + "/v1/models",
    "mcp": os.environ.get("MCP_SERVER_URL", "http://localhost:8000") + "/health",
    "lmstudio_local": "http://127.0.0.1:1234/v1/models",
    "lmstudio_remote": "http://10.0.0.172:1234/v1/models",
}
results = {}
for name, url in endpoints.items():
    try:
        r = requests.get(url, timeout=3)
        results[name] = {"status_code": r.status_code, "json": None}
        try:
            results[name]["json"] = r.json()
        except Exception:
            results[name]["text"] = r.text[:1000]
    except Exception as e:
        results[name] = {"error": str(e)}
print(json.dumps(results, indent=2))
