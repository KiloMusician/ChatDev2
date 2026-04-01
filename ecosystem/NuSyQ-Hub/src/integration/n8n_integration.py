"""n8n workflow automation integration client."""

from __future__ import annotations

from typing import Any


class N8NClient:
    """Minimal n8n REST API client with normalized response contract."""

    def __init__(self, base_url: str, session: Any = None) -> None:
        self.base_url = base_url.rstrip("/")
        self._session = session
        if session is None:
            try:
                import requests

                self._session = requests.Session()
            except ImportError:
                self._session = None

    def trigger_workflow(self, workflow_id: str, payload: dict) -> dict:
        """POST payload to a workflow trigger endpoint.

        Returns a normalized dict with at minimum:
          {"success": bool, "status": str|int, ...}
        """
        url = f"{self.base_url}/api/v1/workflows/{workflow_id}/trigger"
        response = self._session.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            return {"success": True, **data}
        return {"success": True, "status": response.status_code, "payload": data}
