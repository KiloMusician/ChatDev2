#!/usr/bin/env python3
"""
Discover installed LLM runtimes (Ollama, LM Studio) and produce a JSON inventory.

This script is non-destructive and uses only HTTP endpoints. It writes
`state/llm_inventory.json` with discovered models and a simple capability map
to be used by orchestrators and ChatDev adapters.

Usage:
  python scripts/discover_llms.py --ollama http://127.0.0.1:11434 --lmstudio http://127.0.0.1:1234

Environment variables used (fallbacks provided):
  OLLAMA_BASE_URL, LMSTUDIO_BASE_URL
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

import requests


def query_ollama(base: str, timeout: int = 5) -> List[Dict[str, Any]]:
    try:
        r = requests.get(f"{base.rstrip('/')}/api/tags", timeout=timeout)
        if r.status_code == 200:
            payload = r.json()
            return payload.get("models", []) if isinstance(payload, dict) else []
    except requests.RequestException:
        pass
    return []


def query_lmstudio(base: str, timeout: int = 5) -> List[Dict[str, Any]]:
    # LM Studio exposes OpenAI-compatible /v1/models in many setups.
    # Try a short list of candidate endpoints and return the first successful
    # parsed model list.
    base_root = base.rstrip("/")
    candidates = [f"{base_root}/v1/models", f"{base_root}/models"]

    for url in candidates:
        try:
            r = requests.get(url, timeout=timeout)
        except requests.RequestException:
            r = None

        if not r:
            continue

        if r.status_code != 200:
            continue

        try:
            payload = r.json()
        except ValueError:
            continue

        # payload can be dict with 'data' or 'models', or a raw list
        if isinstance(payload, dict):
            if "data" in payload and isinstance(payload["data"], list):
                return payload["data"]
            if "models" in payload and isinstance(payload["models"], list):
                return payload["models"]
        if isinstance(payload, list):
            return payload

    return []


def map_model_to_tasks(name: str) -> List[str]:
    n = name.lower()
    tasks = []
    if any(k in n for k in ("coder", "code", "codellama", "starcoder", "qwen")):
        tasks.append("code_generation")
        tasks.append("debugging")
        tasks.append("code_review")
    if any(k in n for k in ("mistral", "llama", "phi", "llama2", "llama3")):
        tasks.append("general_conversation")
        tasks.append("creative")
    if any(k in n for k in ("reason", "rationale", "phi")):
        tasks.append("reasoning")
    if not tasks:
        tasks.append("general_conversation")
    return list(dict.fromkeys(tasks))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Discover local LLMs (Ollama, LM Studio)"
    )
    parser.add_argument(
        "--ollama", default=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    )
    parser.add_argument(
        "--lmstudio", default=os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234")
    )
    parser.add_argument("--out", default=str(Path("state") / "llm_inventory.json"))
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    inventory: Dict[str, Any] = {
        "ollama": {"base_url": args.ollama, "models": []},
        "lmstudio": {"base_url": args.lmstudio, "models": []},
    }

    # Query Ollama
    ollama_models = query_ollama(args.ollama)
    for m in ollama_models:
        name = m.get("name") if isinstance(m, dict) else str(m)
        inventory["ollama"]["models"].append(
            {"name": name, "raw": m, "capabilities": map_model_to_tasks(name)}
        )

    # Query LM Studio
    lm_models = query_lmstudio(args.lmstudio)
    for m in lm_models:
        # LMStudio responses vary; try common fields
        if isinstance(m, dict):
            name = m.get("id") or m.get("name") or m.get("model") or json.dumps(m)
        else:
            name = str(m)
        inventory["lmstudio"]["models"].append(
            {"name": name, "raw": m, "capabilities": map_model_to_tasks(name)}
        )

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)

    # Print summary
    print("Discovered LLMs:")
    for provider in ("ollama", "lmstudio"):
        models = inventory[provider]["models"]
        print(
            f"  {provider}: {len(models)} model(s) at {inventory[provider]['base_url']}"
        )
        for m in models:
            caps = ", ".join(m.get("capabilities", []))
            print(f"    - {m.get('name')} -> {caps}")


if __name__ == "__main__":
    main()
