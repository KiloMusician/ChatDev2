"""Ollama HTTP adapter with normalized response contract."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class OllamaAdapter:
    """Thin wrapper around the Ollama HTTP API."""

    def __init__(self, base_url: str, model: str = "qwen2.5-coder:14b") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def query(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """POST a generate request. Returns normalized {success, ...} dict."""
        if not self.base_url:
            return {"success": False, "status": "error", "error": "base_url not set"}
        url = f"{self.base_url}/api/generate"
        payload = json.dumps({"model": self.model, "prompt": prompt, "stream": False, **kwargs})
        req = urllib.request.Request(
            url, data=payload.encode(), headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    return {"success": True, **data}
                return {"success": True, "status": "ok", "payload": data}
            except json.JSONDecodeError:
                return {"success": True, "status": "ok", "raw": raw}
        except urllib.error.HTTPError as exc:
            return {"success": False, "status": "error", "code": exc.code, "error": str(exc)}
        except Exception as exc:
            return {"success": False, "status": "error", "error": str(exc)}
