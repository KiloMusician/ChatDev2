#!/usr/bin/env python3
"""Agent Status Dashboard - Shows which agents can access which LLMs.

Displays the complete agent ecosystem status including:
- AI Coordinator provider availability (Ollama, OpenAI, Copilot)
- Unified AI Orchestrator registered systems
- ChatDev backend configuration
- Agent busy states and load

Usage:
    python scripts/agent_status_check.py
    python scripts/agent_status_check.py --json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.config.service_config import ServiceConfig
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)


def check_ai_coordinator_status():
    """Check AI Coordinator provider availability."""
    try:
        from src.ai.ai_coordinator import get_coordinator

        coordinator = get_coordinator()
        available_providers = coordinator.get_available_providers()
        all_providers = {
            "ollama": coordinator._provider_objects.get("ollama") is not None,
            "openai": coordinator._provider_objects.get("openai") is not None,
            "copilot": coordinator._provider_objects.get("copilot") is not None,
        }

        return {
            "available": True,
            "providers_registered": len(all_providers),
            "providers_available": len(available_providers),
            "providers": {
                name: {
                    "registered": all_providers.get(name, False),
                    "available": name in available_providers,
                }
                for name in ["ollama", "openai", "copilot"]
            },
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
            "providers_registered": 0,
            "providers_available": 0,
        }


def check_orchestrator_status():
    """Check Unified AI Orchestrator status."""
    try:
        from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator

        orchestrator = UnifiedAIOrchestrator()
        systems_status = orchestrator.get_system_status()

        ai_systems = systems_status.get("systems", {})
        return {
            "available": True,
            "total_systems": len(ai_systems),
            "systems": {
                name: {
                    "type": info.get("type"),
                    "health": info.get("health_score", 0.0),
                    "load": info.get("current_load", 0),
                    "max_tasks": info.get("max_concurrent_tasks", 0),
                    "utilization": f"{info.get('utilization', 0) * 100:.1f}%",
                }
                for name, info in ai_systems.items()
            },
            "active_tasks": systems_status.get("active_tasks", 0),
            "queue_size": systems_status.get("queue_size", 0),
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
            "total_systems": 0,
        }


def check_chatdev_backend():
    """Check which backend ChatDev is configured to use."""
    import os

    base_url = os.environ.get("OPENAI_BASE_URL", os.environ.get("BASE_URL", ""))
    api_key = os.environ.get("OPENAI_API_KEY", "")

    backend = "Not configured"
    if base_url:
        if "11434" in base_url or "ollama" in base_url.lower():
            backend = "Ollama"
        elif "1234" in base_url or "lmstudio" in base_url.lower():
            backend = "LM Studio"
        else:
            backend = "Custom/OpenAI"
    elif api_key:
        backend = "OpenAI API"

    return {
        "configured_backend": backend,
        "base_url": base_url or "Not set",
        "api_key_configured": bool(api_key),
    }


def main():
    parser = argparse.ArgumentParser(description="Agent Status Dashboard")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    # Gather all status
    coordinator_status = check_ai_coordinator_status()
    orchestrator_status = check_orchestrator_status()
    chatdev_config = check_chatdev_backend()

    # Check LLM backend availability
    ollama_available = ServiceConfig.is_service_available("ollama", timeout=2)
    lmstudio_available = ServiceConfig.is_service_available("lmstudio", timeout=2)

    results = {
        "ai_coordinator": coordinator_status,
        "unified_orchestrator": orchestrator_status,
        "chatdev": chatdev_config,
        "llm_backends": {
            "ollama": {"available": ollama_available, "url": ServiceConfig.get_ollama_url()},
            "lmstudio": {
                "available": lmstudio_available,
                "url": ServiceConfig.get_lmstudio_url(),
            },
        },
    }

    if args.json:
        print(json.dumps(results, indent=2))
        return 0

    # Pretty print results
    print("=" * 70)
    print("AGENT STATUS DASHBOARD")
    print("=" * 70)

    # AI Coordinator
    print("\n🤖 AI Coordinator")
    if coordinator_status["available"]:
        print(
            f"   Providers: {coordinator_status['providers_available']}/{coordinator_status['providers_registered']} available"
        )
        for name, info in coordinator_status.get("providers", {}).items():
            status = "✅" if info["available"] else "❌"
            print(f"   {status} {name.capitalize()}")
    else:
        print(f"   ❌ Error: {coordinator_status.get('error', 'Unknown')}")

    # Unified Orchestrator
    print("\n⚙️  Unified AI Orchestrator")
    if orchestrator_status["available"]:
        print(f"   Systems: {orchestrator_status['total_systems']}")
        print(f"   Active tasks: {orchestrator_status['active_tasks']}")
        print(f"   Queue size: {orchestrator_status['queue_size']}")
        for name, info in list(orchestrator_status.get("systems", {}).items())[:5]:
            print(f"   • {name}: {info['utilization']} utilized")
    else:
        print(f"   ❌ Error: {orchestrator_status.get('error', 'Unknown')}")

    # ChatDev
    print("\n🔧 ChatDev Configuration")
    print(f"   Backend: {chatdev_config['configured_backend']}")
    if chatdev_config["base_url"] != "Not set":
        print(f"   Base URL: {chatdev_config['base_url']}")

    # LLM Backends
    print("\n🧠 LLM Backend Availability")
    ollama_status = "✅ Available" if ollama_available else "❌ Unavailable"
    lmstudio_status = "✅ Available" if lmstudio_available else "❌ Unavailable"
    print(f"   Ollama:     {ollama_status} ({results['llm_backends']['ollama']['url']})")
    print(f"   LM Studio:  {lmstudio_status} ({results['llm_backends']['lmstudio']['url']})")

    print("\n" + "=" * 70)

    # Return 0 if at least one backend is available
    return 0 if (ollama_available or lmstudio_available) else 1


if __name__ == "__main__":
    sys.exit(main())
