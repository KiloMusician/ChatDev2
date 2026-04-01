#!/usr/bin/env python3
"""Lightweight CLI client for the AI Intermediary HTTP endpoint.

Usage:
  python scripts/intermediary_client.py --prompt "Do X" [--module code_analysis]
"""

from __future__ import annotations

import argparse
import json
from urllib import request


def main() -> None:
    parser = argparse.ArgumentParser(description="Call /api/intermediary")
    parser.add_argument("--url", default="http://127.0.0.1:8000/api/intermediary", help="Intermediary endpoint")
    parser.add_argument("--prompt", required=True, help="User prompt/input")
    parser.add_argument("--module", default="code_analysis_helper", help="Target module")
    parser.add_argument("--metadata", default="{}", help="JSON metadata")
    args = parser.parse_args()

    payload = {
        "prompt": args.prompt,
        "module": args.module,
        "metadata": json.loads(args.metadata),
    }
    data = json.dumps(payload).encode()
    req = request.Request(args.url, data=data, headers={"Content-Type": "application/json"})
    with request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode()
        print(body)


if __name__ == "__main__":
    main()
