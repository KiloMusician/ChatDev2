"""Simple LM Studio connectivity test script.

Usage:
  python scripts/test_lmstudio.py --base http://10.0.0.172:1234
"""

from __future__ import annotations

import argparse
import json
import sys
from urllib.error import URLError
from urllib.request import urlopen


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://10.0.0.172:1234")
    args = ap.parse_args(argv)

    endpoints = ["/v1/models", "/v1/responses"]
    for ep in endpoints:
        url = args.base.rstrip("/") + ep
        try:
            with urlopen(url, timeout=5) as r:
                data = r.read().decode("utf-8")
                print(f"{url} -> {len(data)} bytes")
                try:
                    obj = json.loads(data)
                    print(json.dumps(obj if isinstance(obj, dict) else obj, indent=2)[:1000])
                except Exception:
                    print(data[:400])
        except URLError as e:
            print(f"Failed to reach {url}: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
