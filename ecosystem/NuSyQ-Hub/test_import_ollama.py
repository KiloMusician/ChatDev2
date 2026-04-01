#!/usr/bin/env python
"""Quick test: Does Ollama module import without hanging?

Guarded to avoid calling sys.exit() at import time during pytest
collection.
"""
import sys
import time


def run_import_check() -> int:
    start = time.time()
    try:
        from src.integration.Ollama_Integration_Hub import get_ollama_url

        elapsed = time.time() - start
        print(f"✅ Import OK in {elapsed:.2f}s")
        url = get_ollama_url()
        print(f"   URL: {url}")
        return 0
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Import failed after {elapsed:.2f}s: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run_import_check())
