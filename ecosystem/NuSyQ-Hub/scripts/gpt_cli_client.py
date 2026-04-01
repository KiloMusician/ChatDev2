#!/usr/bin/env python3
"""Simple GPT CLI client examples for NuSyQ ChatGPT bridge.

Usage examples:
  python scripts/gpt_cli_client.py send-terminal "Errors" "error" "Something broke"
  python scripts/gpt_cli_client.py submit-pu "Run tests" '{"tests": ["tests/test_core.py"]}'
  python scripts/gpt_cli_client.py execute "analyze src/main.py" '{"target_system":"ollama"}'
"""

from __future__ import annotations

import json
import os
import sys

import requests

BASE = os.environ.get("NUSYQ_CHATGPT_BRIDGE_URL", "http://127.0.0.1:8765")


def _headers() -> dict[str, str]:
    token = os.environ.get("NUSYQ_BRIDGE_TOKEN")
    if token:
        return {"x-bridge-token": token}
    return {}


def send_terminal(channel: str, level: str, message: str):
    url = f"{BASE}/api/terminals/send"
    payload = {"channel": channel, "level": level, "message": message}
    r = requests.post(url, json=payload, headers=_headers(), timeout=10)
    print(r.status_code, r.json())


def submit_pu(title: str, payload_json: str):
    url = f"{BASE}/api/pu/submit"
    payload = {"title": title, "payload": json.loads(payload_json)}
    r = requests.post(url, json=payload, headers=_headers(), timeout=10)
    print(r.status_code, r.json())


def execute(command: str, args_json: str = "{}"):
    url = f"{BASE}/api/execute"
    payload = {"command": command, "args": json.loads(args_json)}
    r = requests.post(url, json=payload, headers=_headers(), timeout=30)
    print(r.status_code, r.json())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: send-terminal|submit-pu|execute ...")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "send-terminal":
        send_terminal(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "submit-pu":
        submit_pu(sys.argv[2], sys.argv[3])
    elif cmd == "execute":
        execute(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "{}")
    else:
        print("Unknown command")
