#!/usr/bin/env python3
"""Check Ollama HTTP API /api/tags and /api/models availability."""

import os

import requests


def main():
    base = os.environ.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434"
    tags_url = base.rstrip("/") + "/api/tags"
    gen_url = base.rstrip("/") + "/api/generate"
    print("Using base URL:", base)
    try:
        r = requests.get(tags_url, timeout=5)
        print("GET /api/tags ->", r.status_code)
        try:
            print(r.json())
        except Exception:
            print("Response not JSON or could not decode")
    except Exception as e:
        print("Tags request failed:", e)

    # quick generate check (without large payload)
    try:
        payload = {"model": "qwen2.5-coder:14b", "prompt": "echo test", "stream": False}
        r = requests.post(gen_url, json=payload, timeout=5)
        print("POST /api/generate ->", r.status_code)
        try:
            print(r.json())
        except Exception:
            print("Generate response not JSON or could not decode")
    except Exception as e:
        print("Generate request failed:", e)


if __name__ == "__main__":
    main()
