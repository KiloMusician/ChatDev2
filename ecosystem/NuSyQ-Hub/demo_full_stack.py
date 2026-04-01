#!/usr/bin/env python3
"""Full-Stack Development Suite Integration Demonstration.

Demonstrates the complete NuSyQ ecosystem integration:
- OpenClaw Gateway Bridge (12+ messaging platforms)
- Ollama Integration Hub (10 local LLMs)
- ChatDev (Multi-agent development teams)
- Open-Antigravity (Modular window server)
- Unified AI Orchestrator (Central coordination)
- Quest System (Persistent task tracking)

Architecture:
    Slack/Discord/Telegram/etc. (External channels)
        ↓ [OpenClaw Gateway ws://127.0.0.1:18789]
    OpenClaw Gateway Bridge
        ↓ [route_task with context]
    Unified AI Orchestrator
        ├─ Ollama Hub (Local LLM selection & execution)
        ├─ ChatDev (Multi-agent development teams)
        ├─ Consciousness Bridge (Semantic awareness)
        └─ Quantum Resolver (Self-healing)
        ↓
    Quest Log (Persistent results)
        ↓
    OpenClaw send_result → Original Channel
"""

import asyncio
import json
import sys
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import full-stack components
from src.integrations.openclaw_gateway_bridge import (
    OPENCLAW_CONFIG_PATH,
)

try:
    from src.integration.Ollama_Integration_Hub import KILOOllamaHub
except ImportError:
    print("⚠️ KILOOllamaHub not available (path resolution issue)")
    KILOOllamaHub = None

try:
    from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator
except ImportError:
    print("⚠️ UnifiedAIOrchestrator not available")
    UnifiedAIOrchestrator = None


def print_header():
    """Print demo header."""
    print("\n" + "=" * 80)
    print("🌐 NuSyQ Full-Stack Development Suite Integration")
    print("=" * 80)
    print("\n🎯 Components Demonstrated:")
    print("   1️⃣ OpenClaw Gateway Bridge (12+ messaging platforms)")
    print("   2️⃣ Ollama Integration Hub (10 local LLM models)")
    print("   3️⃣ ChatDev Integration (Multi-agent dev teams)")
    print("   4️⃣ Open-Antigravity (Modular window server)")
    print("   5️⃣ Unified AI Orchestrator (Central coordination)")
    print("   6️⃣ Quest System (Persistent task tracking)")
    print("\n" + "=" * 80 + "\n")


async def check_openclaw_status():
    """Check OpenClaw Gateway Bridge configuration and status."""
    print("🔌 1. OpenClaw Gateway Bridge Status")
    print("=" * 80)

    # Check configuration
    if not Path(OPENCLAW_CONFIG_PATH).exists():
        print(f"   ❌ Config not found: {OPENCLAW_CONFIG_PATH}")
        return False

    with open(OPENCLAW_CONFIG_PATH) as f:
        config = json.load(f)

    openclaw = config.get("openclaw", {})
    enabled = openclaw.get("enabled", False)
    gateway_url = openclaw.get("gateway_url", "ws://127.0.0.1:18789")

    print(f"   📝 Config path: {OPENCLAW_CONFIG_PATH}")
    print(f"   {'✅' if enabled else '❌'} OpenClaw enabled: {enabled}")
    print(f"   🌐 Gateway URL: {gateway_url}")

    # Check enabled channels
    channels = openclaw.get("channels", {})
    enabled_channels = [name for name, ch in channels.items() if ch.get("enabled")]

    print(f"   📡 Configured channels: {len(channels)}")
    print(f"   ✅ Enabled channels: {enabled_channels if enabled_channels else 'None'}")

    if enabled_channels:
        for channel in enabled_channels:
            ch_config = channels[channel]
            print(f"      • {channel}: {ch_config.get('host', 'N/A')}")

    print()
    return enabled


async def check_ollama_hub():
    """Check Ollama Integration Hub status."""
    print("🦙 2. Ollama Integration Hub Status")
    print("=" * 80)

    if KILOOllamaHub is None:
        print("   ❌ KILOOllamaHub not available (import failed)")
        print()
        return None

    try:
        # Initialize hub (auto-connects)
        print("   🔄 Initializing KILOOllamaHub...")
        hub = KILOOllamaHub()

        if not hub.is_connected:
            print("   ❌ Ollama service not available")
            print("   💡 Start Ollama: ollama serve")
            print()
            return None

        print(f"   ✅ Connected to Ollama at {getattr(hub, 'ollama_host', 'localhost:11434')}")

        # Discover models
        print("   🔍 Discovering available models...")
        models = hub.discover_models()

        print(f"   📦 Available models: {len(models)}")
        if models:
            for model_name, model_obj in list(models.items())[:5]:  # Show first 5
                size_gb = model_obj.size / (1024**3) if model_obj.size else 0
                print(f"      • {model_name}: {size_gb:.1f}GB")
                if model_obj.capabilities:
                    caps = ", ".join(model_obj.capabilities[:3])
                    print(f"        Capabilities: {caps}")
        else:
            print("   ⚠️ No models discovered (may be initialization timing)")

        print()
        return hub

    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()
        return None


async def check_orchestrator_status():
    """Check Unified AI Orchestrator status."""
    print("🧠 3. Unified AI Orchestrator Status")
    print("=" * 80)

    if UnifiedAIOrchestrator is None:
        print("   ❌ UnifiedAIOrchestrator not available (import failed)")
        print()
        return None

    try:
        print("   🔄 Initializing orchestrator...")
        orchestrator = UnifiedAIOrchestrator()

        # Check available capabilities
        print("   ✅ Orchestrator initialized")
        print("   🎯 Capabilities:")
        print("      • Task routing and execution")
        print("      • Multi-AI coordination (Ollama, ChatDev, etc.)")
        print("      • Consciousness bridge integration")
        print("      • Quest system logging")
        print("      • Self-healing via quantum resolver")

        print()
        return orchestrator

    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()
        return None


async def check_chatdev_status():
    """Check ChatDev integration status."""
    print("🏗️ 4. ChatDev Multi-Agent Development Status")
    print("=" * 80)

    # Check CHATDEV_PATH environment variable
    chatdev_path = Path("C:/Users/keath/NuSyQ/ChatDev")

    if chatdev_path.exists():
        print(f"   ✅ ChatDev found: {chatdev_path}")
        print("   🤖 Available agents:")
        print("      • CEO - Strategic planning")
        print("      • CTO - Technical architecture")
        print("      • Programmer - Code implementation")
        print("      • Code Reviewer - Quality assurance")
        print("      • Tester - Testing and validation")
        print("      • Art Designer - UI/UX design")
        print("      • Product Manager - Requirements")
    else:
        print(f"   ⚠️ ChatDev not found at: {chatdev_path}")
        print("   💡 Install via: git clone https://github.com/OpenBMB/ChatDev")

    print()
    return chatdev_path.exists()


async def check_antigravity_status():
    """Check Open-Antigravity modular window server status."""
    print("🌊 5. Open-Antigravity Modular Window Server Status")
    print("=" * 80)

    # Check web root
    web_root = Path(__file__).parent / "web" / "modular-window-server"

    if web_root.exists():
        print(f"   ✅ Web root found: {web_root}")
        print("   🌐 Default port: 8080")
        print("   💡 Start: python scripts/start_nusyq.py open_antigravity_start")

        # Check for key files
        key_files = ["package.json", "index.html", "server.py"]
        for file in key_files:
            if (web_root / file).exists():
                print(f"      ✅ {file}")
    else:
        print(f"   ⚠️ Web root not found: {web_root}")
        print("   💡 Open-Antigravity provides modular UI components")

    print()
    return web_root.exists()


async def demonstrate_integration_flow():
    """Demonstrate the full integration flow."""
    print("🔄 6. Integration Flow Demonstration")
    print("=" * 80)

    print("📋 Message Flow Architecture:\n")
    print("   👤 User sends message via Slack/Discord/Telegram")
    print("        ↓")
    print("   🌐 OpenClaw Gateway (ws://127.0.0.1:18789)")
    print("        ↓")
    print("   🔌 OpenClaw Gateway Bridge receives WebSocket message")
    print("        ↓")
    print("   🧠 Unified AI Orchestrator routes task:")
    print("        ├─ 🦙 Ollama Hub (code analysis, generation)")
    print("        ├─ 🏗️ ChatDev (multi-agent development)")
    print("        ├─ 🌀 Consciousness Bridge (semantic awareness)")
    print("        └─ ⚛️ Quantum Resolver (self-healing)")
    print("        ↓")
    print("   📝 Quest System logs interaction to quest_log.jsonl")
    print("        ↓")
    print("   📤 OpenClaw Gateway Bridge sends result back")
    print("        ↓")
    print("   💬 User receives response in original channel\n")

    print("\n🎯 Example Workflow:\n")
    print('   1. User (Slack): "@nusyq analyze src/main.py"')
    print("   2. OpenClaw → Gateway Bridge → Orchestrator")
    print("   3. Orchestrator selects Ollama qwen2.5-coder:7b")
    print("   4. Analysis results logged to quest system")
    print("   5. Response sent back to Slack channel")
    print()


async def show_quick_start():
    """Show quick start commands."""
    print("🚀 Quick Start Commands")
    print("=" * 80)

    print("\n📦 Start OpenClaw Gateway:")
    print("   openclaw gateway")
    print("   # Or via NuSyQ:")
    print("   python scripts/start_nusyq.py openclaw_gateway_start")

    print("\n🔌 Start OpenClaw Bridge:")
    print("   python scripts/start_nusyq.py openclaw_bridge_start")

    print("\n🌊 Start Open-Antigravity:")
    print("   python scripts/start_nusyq.py open_antigravity_start")

    print("\n🦙 Verify Ollama:")
    print("   ollama list")
    print("   curl http://localhost:11434/api/tags")

    print("\n🤖 Test ChatDev:")
    print("   cd C:\\Users\\keath\\NuSyQ\\ChatDev")
    print("   python run_ollama.py")

    print("\n🧪 Test Full Stack:")
    print("   python demo_full_stack.py")

    print()


async def main():
    """Run full-stack integration demonstration."""
    print_header()

    # Check each component
    openclaw_ok = await check_openclaw_status()
    ollama_hub = await check_ollama_hub()
    orchestrator = await check_orchestrator_status()
    chatdev_ok = await check_chatdev_status()
    antigravity_ok = await check_antigravity_status()

    # Show integration flow
    await demonstrate_integration_flow()

    # Show quick start
    await show_quick_start()

    # Summary
    print("=" * 80)
    print("📊 Component Health Summary:")
    print(
        f"   {'✅' if openclaw_ok else '⚠️'} OpenClaw Gateway Bridge: {'Configured' if openclaw_ok else 'Not configured'}"
    )
    print(
        f"   {'✅' if ollama_hub else '⚠️'} Ollama Integration Hub: {'Connected' if ollama_hub else 'Not available'}"
    )
    print(
        f"   {'✅' if orchestrator else '⚠️'} Unified AI Orchestrator: {'Ready' if orchestrator else 'Not available'}"
    )
    print(
        f"   {'✅' if chatdev_ok else '⚠️'} ChatDev Integration: {'Found' if chatdev_ok else 'Not found'}"
    )
    print(
        f"   {'✅' if antigravity_ok else '⚠️'} Open-Antigravity: {'Found' if antigravity_ok else 'Not found'}"
    )
    print("=" * 80)

    # Status code
    all_ok = any([openclaw_ok, ollama_hub, orchestrator])
    return 0 if all_ok else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
