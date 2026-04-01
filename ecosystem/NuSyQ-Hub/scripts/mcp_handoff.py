#!/usr/bin/env python3
"""Send a small handoff message to local MCP terminal API (/api/terminals/send).

Usage: python scripts/mcp_handoff.py
"""

import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def load_handoff_yaml(path: Path) -> dict:
    # we don't need full YAML parsing for the scaffold; if file missing return minimal meta
    if not path.exists():
        return {"note": "no handoff file present", "path": str(path)}
    try:
        import yaml

        return yaml.safe_load(path.read_text())
    except Exception:
        # fallback: return file text
        return {"raw": path.read_text()}


def main():
    url = "http://127.0.0.1:8001/api/terminals/send"
    handoff_path = Path(".ai-context/claude-handoff.yaml")
    meta = load_handoff_yaml(handoff_path)
    payload = {
        "channel": "nusyq-experiments",
        "level": "info",
        "message": "claude-handoff-test",
        "meta": {"handoff_summary": meta},
    }
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            print("Status:", resp.status)
            print(body)
    except HTTPError as e:
        print("HTTPError", e.code, e.read().decode("utf-8"))
    except URLError as e:
        print("URLError", e)


if __name__ == "__main__":
    main()
