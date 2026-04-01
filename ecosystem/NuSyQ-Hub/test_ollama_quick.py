#!/usr/bin/env python3
"""Quick Ollama connectivity test"""

import os
import sys

import requests

try:
    from src.utils.config_helper import get_ollama_host
except ImportError:
    get_ollama_host = None

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def _get_ollama_url() -> str:
    """Resolve Ollama URL from config/env."""
    if get_ollama_host:
        try:
            host = get_ollama_host()
            if host:
                return host if "://" in host else f"http://{host}"
        except (AttributeError, TypeError, RuntimeError):
            pass

    base = os.getenv("OLLAMA_BASE_URL")
    if base:
        return base if "://" in base else f"http://{base}"

    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1")
    port = os.getenv("OLLAMA_PORT", "11434")
    if "://" not in host:
        host = f"http://{host}"
    if ":" not in host.split("://")[1]:
        host = f"{host}:{port}"
    return host


def test_ollama():
    """Test Ollama connectivity and generate a simple response"""
    print("[*] Testing Ollama Connectivity...")
    print("=" * 50)

    ollama_url = _get_ollama_url()
    print(f"[*] Using Ollama URL: {ollama_url}")

    # Test 1: Check Ollama is running
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"[OK] Ollama is running with {len(models)} models:")
            for model in models[:3]:
                print(f"   - {model['name']}")
        else:
            print(f"[FAIL] Ollama responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Failed to connect to Ollama: {e}")
        return False

    # Test 2: Generate a simple response
    print("\n[*] Testing code generation with qwen2.5-coder:7b...")
    try:
        payload = {
            "model": "qwen2.5-coder:7b",
            "prompt": "Write a Python function to calculate fibonacci numbers:",
            "stream": False,
        }

        response = requests.post(f"{ollama_url}/api/generate", json=payload, timeout=30)

        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "")
            print(f"[OK] Generated {len(generated_text)} characters")
            print(f"\n[OUTPUT] Sample:\n{generated_text[:300]}...")
            return True
        else:
            print(f"[FAIL] Generation failed with status {response.status_code}")
            return False

    except Exception as e:
        print(f"[FAIL] Generation failed: {e}")
        return False


if __name__ == "__main__":
    success = test_ollama()
    print("\n" + "=" * 50)
    if success:
        print("[SUCCESS] Ollama is OPERATIONAL and ready for ChatDev integration!")
    else:
        print("[ERROR] Ollama test failed - check configuration")
    print("=" * 50)
