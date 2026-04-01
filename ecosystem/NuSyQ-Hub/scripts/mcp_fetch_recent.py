#!/usr/bin/env python3
"""Fetch recent terminal messages for a channel from MCP Terminal API.

Usage: python scripts/mcp_fetch_recent.py [channel]
"""

import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main():
    channel = sys.argv[1] if len(sys.argv) > 1 else "nusyq-experiments"
    url = f"http://127.0.0.1:8001/api/terminals/{channel}/recent"
    req = Request(url, method="GET")
    try:
        with urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            try:
                data = json.loads(body)
            except Exception:
                print(body)
                return
            print(json.dumps(data, indent=2))
    except HTTPError as e:
        print("HTTPError", e.code, e.read().decode("utf-8"))
    except URLError as e:
        print("URLError", e)


if __name__ == "__main__":
    main()
