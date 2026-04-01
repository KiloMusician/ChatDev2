# server/middleware_normalize.py
from typing import Callable
from .normalizers import ensure_array

LIST_KEYS = {"menu", "windows", "panes", "cascades", "achievements", "tasks", "rows", "agents", "effects", "recentGains"}

def normalize_payload(payload):
    if isinstance(payload, dict):
        return {
            k: ensure_array(v) if k in LIST_KEYS else normalize_payload(v)
            for k, v in payload.items()
        }
    if isinstance(payload, list):
        return [normalize_payload(x) for x in payload]
    return payload

def response_normalizer(next_handler: Callable):
    def _wrap(*args, **kwargs):
        resp = next_handler(*args, **kwargs)
        try:
            if isinstance(resp, dict):
                return normalize_payload(resp)
            if hasattr(resp, "json"):
                data = resp.json
                resp.json = normalize_payload(data)
            return resp
        except Exception:
            return resp
    return _wrap