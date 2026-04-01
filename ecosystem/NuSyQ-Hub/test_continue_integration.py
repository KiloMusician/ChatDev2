"""Test Continue.dev integration with Ollama to diagnose output quality issues.

This script tests the Continue.dev API to see how it interacts with Ollama models.
"""

import json
import os
from typing import Any, Dict

import requests

try:
    from src.utils.config_helper import get_ollama_host
except ImportError:
    get_ollama_host = None


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


def test_ollama_direct() -> Dict[str, Any]:
    """Test Ollama API directly (proven working)."""
    url = f"{_get_ollama_url()}/api/generate"
    payload = {
        "model": "qwen2.5-coder:7b",
        "prompt": "Write a Python function to reverse a string:",
        "stream": False,
    }

    response = requests.post(url, json=payload, timeout=30)
    return {
        "status": "success" if response.status_code == 200 else "failed",
        "response": response.json() if response.status_code == 200 else response.text,
    }


def test_continue_config() -> Dict[str, Any]:
    """Validate Continue.dev configuration."""
    config_path = r"C:\Users\keath\.continue\config.ts"

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_content = f.read()

        # Check for key configuration elements
        ollama_url = _get_ollama_url()
        checks = {
            "has_ollama_models": ollama_url.replace("http://", "").replace("https://", "")
            in config_content
            or "11434" in config_content,
            "has_qwen_coder": "qwen2.5-coder" in config_content,
            "has_starcoder": "starcoder2:15b" in config_content,
            "has_tab_autocomplete": "tabAutocompleteModel" in config_content,
            "has_embeddings": "embeddingsProvider" in config_content,
        }

        return {
            "status": "success",
            "config_path": config_path,
            "checks": checks,
            "all_passed": all(checks.values()),
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def diagnose_continue_issues() -> Dict[str, Any]:
    """Diagnose potential Continue.dev integration issues."""
    issues = []
    recommendations = []

    ollama_url = _get_ollama_url()

    # Check 1: Ollama API accessibility
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code != 200:
            issues.append("Ollama API not accessible")
            recommendations.append("Ensure Ollama service is running: 'ollama serve'")
    except Exception as e:
        issues.append(f"Cannot connect to Ollama: {e}")
        recommendations.append("Start Ollama service")

    # Check 2: Continue.dev config exists
    config_path = r"C:\Users\keath\.continue\config.ts"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_content = f.read()

        # Check for common issues
        if (
            ollama_url.replace("http://", "").replace("https://", "") not in config_content
            and "11434" not in config_content
        ):
            issues.append("Ollama API base URL not configured correctly")
            recommendations.append(f"Update config.ts with apiBase: '{ollama_url}'")

        if config_content.count("apiBase") < 7:
            issues.append("Not all models have apiBase configured")
            recommendations.append("Ensure all Ollama models specify apiBase")

    except FileNotFoundError:
        issues.append("Continue.dev config.ts not found")
        recommendations.append(f"Create {config_path}")

    return {
        "issues_found": len(issues),
        "issues": issues,
        "recommendations": recommendations,
        "status": "healthy" if len(issues) == 0 else "needs_attention",
    }


if __name__ == "__main__":
    print("=" * 80)
    print("Continue.dev + Ollama Integration Diagnostic")
    print("=" * 80)

    # Test 1: Direct Ollama API
    print("\n[1/3] Testing Ollama API directly...")
    ollama_test = test_ollama_direct()
    print(f"Status: {ollama_test['status']}")
    if ollama_test["status"] == "success":
        response_text = ollama_test["response"].get("response", "")[:200]
        print(f"Sample output: {response_text}...")

    # Test 2: Continue.dev config validation
    print("\n[2/3] Validating Continue.dev configuration...")
    config_test = test_continue_config()
    print(f"Status: {config_test['status']}")
    if config_test["status"] == "success":
        print(f"Config checks: {json.dumps(config_test['checks'], indent=2)}")

    # Test 3: Diagnose integration issues
    print("\n[3/3] Diagnosing integration issues...")
    diagnosis = diagnose_continue_issues()
    print(f"Status: {diagnosis['status']}")
    print(f"Issues found: {diagnosis['issues_found']}")

    if diagnosis["issues"]:
        print("\nIssues:")
        for issue in diagnosis["issues"]:
            print(f"  - {issue}")
        print("\nRecommendations:")
        for rec in diagnosis["recommendations"]:
            print(f"  - {rec}")

    print("\n" + "=" * 80)
    print("DIAGNOSIS COMPLETE")
    print("=" * 80)

    # Summary
    print("\nSUMMARY:")
    print(f"  Ollama API: {ollama_test['status']}")
    print(f"  Continue.dev Config: {config_test['status']}")
    print(f"  Integration Health: {diagnosis['status']}")

    if diagnosis["status"] == "healthy" and ollama_test["status"] == "success":
        print("\n✅ All systems operational!")
        print("\nPossible causes of 'wonky output' in VS Code:")
        print("  1. Continue.dev extension cache - try reloading VS Code window")
        print("  2. Model context window size - check Continue.dev settings")
        print("  3. Prompt formatting - Continue.dev may be modifying prompts")
        print("  4. Response parsing - extension may be truncating/reformatting")
        print("\nRecommended next steps:")
        print("  - Reload VS Code window (Ctrl+Shift+P → 'Developer: Reload Window')")
        print("  - Check Continue.dev extension output panel for errors")
        print("  - Try different models (starcoder2, codellama, gemma2)")
        print("  - Compare raw Ollama output vs Continue.dev output for same prompt")
