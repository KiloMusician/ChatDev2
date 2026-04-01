#!/usr/bin/env python3
import json
import sys

try:
    import requests
except Exception:
    requests = None

payload = {
    "path": r"C:\Users\keath\\.lmstudio\\models\\gpt-oss-20b-MXFP4.gguf",
    "name": "gpt-oss-20b-MXFP4",
    "provider": "lmstudio",
    "format": "gguf",
    "size_bytes": 123456789,
    "apply": True,
}
url = "http://127.0.0.1:8700/register"
models_url = "http://127.0.0.1:8700/models"

if requests is not None:
    try:
        r = requests.post(url, json=payload, timeout=10)
        print("POST", r.status_code)
        try:
            print(r.json())
        except Exception:
            print(r.text)
    except Exception as e:
        print("POST request failed:", e, file=sys.stderr)
        sys.exit(2)

    try:
        r = requests.get(models_url, timeout=10)
        print("\nGET /models", r.status_code)
        try:
            print(r.json())
        except Exception:
            print(r.text)
    except Exception as e:
        print("GET request failed:", e, file=sys.stderr)
        sys.exit(3)
else:
    # fallback to urllib
    import urllib.request

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            print("POST", resp.status)
            print(resp.read().decode("utf-8"))
    except Exception as e:
        print("POST request failed:", e, file=sys.stderr)
        sys.exit(2)
    try:
        with urllib.request.urlopen(models_url, timeout=10) as resp:
            print("\nGET /models", resp.status)
            print(resp.read().decode("utf-8"))
    except Exception as e:
        print("GET request failed:", e, file=sys.stderr)
        sys.exit(3)
