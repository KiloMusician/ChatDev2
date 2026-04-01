#!/usr/bin/env python3
"""Call llm_route and swarm_run against a running MCP server."""

from __future__ import annotations

import json
import sys

import httpx


def call(endpoint: str, payload=None):
    url = f"http://127.0.0.1:8899{endpoint}"
    resp = httpx.get(url) if payload is None else httpx.post(url, json=payload)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    try:
        print("Health:", call("/health"))
        print("Manifest keys:", list(call("/manifest").keys()))

        llm = call(
            "/execute",
            {
                "tool": "llm_route",
                "parameters": {
                    "prompt": "Dry-run hello from MCP smoke",
                    "capability_tags": ["code"],
                    "prefer_local": True,
                },
            },
        )
        print("llm_route:", json.dumps(llm, indent=2))

        swarm = call(
            "/execute",
            {
                "tool": "swarm_run",
                "parameters": {
                    "mode": "vote",
                    "steps": [
                        {"prompt": "Option A", "capability_tags": ["code"]},
                        {"prompt": "Option B", "capability_tags": ["code"]},
                    ],
                },
            },
        )
        print("swarm_run:", json.dumps(swarm, indent=2))
    except Exception as e:
        print(f"Smoke failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
