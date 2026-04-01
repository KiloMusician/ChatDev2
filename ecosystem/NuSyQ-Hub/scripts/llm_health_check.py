#!/usr/bin/env python3
"""Comprehensive LLM Backend Health Check

Checks availability of all LLM backends (Ollama, LM Studio) and reports
which models are available for ChatDev and orchestrator use.

Usage:
    python scripts/llm_health_check.py
    python scripts/llm_health_check.py --verbose
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import requests

    from src.config.service_config import ServiceConfig
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("Run: pip install requests")
    sys.exit(1)


def check_ollama(verbose: bool = False) -> dict:
    """Check Ollama service health and available models."""
    url = ServiceConfig.get_ollama_url()
    result = {
        "service": "Ollama",
        "url": url,
        "available": False,
        "models": [],
        "error": None,
    }

    try:
        response = requests.get(f"{url}/api/tags", timeout=3)
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            result["available"] = True
            result["models"] = [m.get("name", m.get("model", "unknown")) for m in models]

            if verbose:
                print(f"\n✅ Ollama ({url})")
                print(f"   Models: {len(result['models'])}")
                for model in result["models"][:5]:  # Show first 5
                    print(f"   - {model}")
                if len(result["models"]) > 5:
                    print(f"   ... and {len(result['models']) - 5} more")
        else:
            result["error"] = f"HTTP {response.status_code}"
    except requests.RequestException as e:
        result["error"] = str(e)
        if verbose:
            print(f"\n❌ Ollama ({url}): {e}")

    return result


def check_lmstudio(verbose: bool = False) -> dict:
    """Check LM Studio service health and available models."""
    url = ServiceConfig.get_lmstudio_url()
    result = {
        "service": "LM Studio",
        "url": url,
        "available": False,
        "models": [],
        "error": None,
    }

    try:
        # Try OpenAI-compatible /v1/models endpoint
        response = requests.get(f"{url}/v1/models", timeout=3)
        if response.status_code == 200:
            data = response.json()
            models_data = data.get("data", [])
            result["available"] = True
            result["models"] = [m.get("id", "unknown") for m in models_data]

            if verbose:
                print(f"\n✅ LM Studio ({url})")
                print(f"   Models: {len(result['models'])}")
                for model in result["models"]:
                    print(f"   - {model}")
        else:
            result["error"] = f"HTTP {response.status_code}"
    except requests.RequestException as e:
        result["error"] = str(e)
        if verbose:
            print(f"\n❌ LM Studio ({url}): {e}")

    return result


def check_chatdev_config(verbose: bool = False) -> dict:
    """Check which LLM backend ChatDev would use based on env vars."""
    import os

    openai_base = os.environ.get("OPENAI_BASE_URL", os.environ.get("BASE_URL", ""))
    openai_key = os.environ.get("OPENAI_API_KEY", "")

    result = {
        "chatdev_backend": "unknown",
        "base_url": openai_base,
        "api_key_set": bool(openai_key),
        "recommendation": "",
    }

    if openai_base:
        if "11434" in openai_base or "ollama" in openai_base.lower():
            result["chatdev_backend"] = "Ollama"
        elif "1234" in openai_base or "lmstudio" in openai_base.lower():
            result["chatdev_backend"] = "LM Studio"
        else:
            result["chatdev_backend"] = "Custom/OpenAI"
    elif openai_key:
        result["chatdev_backend"] = "OpenAI API"
    else:
        result["chatdev_backend"] = "Not configured"
        result["recommendation"] = "Set OPENAI_BASE_URL or BASE_URL env var"

    if verbose:
        print("\n🤖 ChatDev Configuration:")
        print(f"   Backend: {result['chatdev_backend']}")
        if result["base_url"]:
            print(f"   Base URL: {result['base_url']}")
        if result["recommendation"]:
            print(f"   💡 {result['recommendation']}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Check LLM backend health")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    if not args.json and not args.verbose:
        print("🔍 Checking LLM Backend Health...\n")

    # Check all backends
    ollama_result = check_ollama(verbose=args.verbose)
    lmstudio_result = check_lmstudio(verbose=args.verbose)
    chatdev_config = check_chatdev_config(verbose=args.verbose)

    # Compile results
    all_results = {
        "ollama": ollama_result,
        "lmstudio": lmstudio_result,
        "chatdev": chatdev_config,
        "summary": {
            "total_backends_available": sum([ollama_result["available"], lmstudio_result["available"]]),
            "total_models": len(ollama_result["models"]) + len(lmstudio_result["models"]),
        },
    }

    if args.json:
        print(json.dumps(all_results, indent=2))
        return 0

    # Summary output
    if not args.verbose:
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)

        # Ollama
        status = "✅ Available" if ollama_result["available"] else "❌ Unavailable"
        print(f"Ollama:     {status}")
        if ollama_result["available"]:
            print(f"            {len(ollama_result['models'])} models")
        elif ollama_result["error"]:
            print(f"            Error: {ollama_result['error']}")

        # LM Studio
        status = "✅ Available" if lmstudio_result["available"] else "❌ Unavailable"
        print(f"LM Studio:  {status}")
        if lmstudio_result["available"]:
            print(f"            {len(lmstudio_result['models'])} models")
        elif lmstudio_result["error"]:
            print(f"            Error: {lmstudio_result['error']}")

        # ChatDev
        print(f"\nChatDev:    Configured for {chatdev_config['chatdev_backend']}")
        if chatdev_config["recommendation"]:
            print(f"            💡 {chatdev_config['recommendation']}")

        print(
            f"\n📊 Total: {all_results['summary']['total_backends_available']} backends, {all_results['summary']['total_models']} models"
        )
        print("=" * 60)

    # Return status code
    return 0 if all_results["summary"]["total_backends_available"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
