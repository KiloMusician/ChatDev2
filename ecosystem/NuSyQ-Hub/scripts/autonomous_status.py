#!/usr/bin/env python3
"""Autonomous System Status Checker - Quick Health Assessment

Quickly check if all autonomous components are available and healthy.

Usage:
    python scripts/autonomous_status.py
    python scripts/autonomous_status.py --verbose
"""

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))


def check_component(name: str, import_path: str) -> dict[str, Any]:
    """Check if a component can be imported.

    Args:
        name: Component display name
        import_path: Python import path (e.g., "src.automation.autonomous_loop")

    Returns:
        Status dict with availability and details
    """
    result = {
        "name": name,
        "status": "unknown",
        "available": False,
        "details": "",
    }

    try:
        parts = import_path.split(".")
        module_name = ".".join(parts[:-1])
        class_name = parts[-1]

        module = __import__(module_name, fromlist=[class_name])
        component_class = getattr(module, class_name)

        result["status"] = "available"
        result["available"] = True
        result["details"] = f"{component_class.__module__}.{component_class.__name__}"

        # Check for key methods
        if hasattr(component_class, "__init__"):
            result["instantiable"] = True

    except ImportError as e:
        result["status"] = "import_failed"
        result["details"] = str(e)
    except AttributeError as e:
        result["status"] = "class_not_found"
        result["details"] = str(e)
    except Exception as e:
        result["status"] = "error"
        result["details"] = str(e)

    return result


def check_file_exists(name: str, file_path: str) -> dict[str, Any]:
    """Check if a file exists.

    Args:
        name: File display name
        file_path: Relative path from root

    Returns:
        Status dict with existence and size
    """
    full_path = ROOT / file_path
    result = {
        "name": name,
        "path": file_path,
        "exists": full_path.exists(),
        "size": 0,
    }

    if result["exists"]:
        result["size"] = full_path.stat().st_size
        result["size_kb"] = f"{result['size'] / 1024:.1f} KB"

    return result


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Check autonomous system status")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed information")
    args = parser.parse_args()

    print("=" * 80)
    print("🤖 AUTONOMOUS SYSTEM STATUS CHECK")
    print("=" * 80)
    print("")

    # Check core components
    print("📦 Core Components:")
    print("-" * 80)

    components = [
        ("Autonomous Loop", "automation.autonomous_loop.AutonomousLoop"),
        ("Autonomous Monitor", "automation.autonomous_monitor.AutonomousMonitor"),
        (
            "Autonomous Quest Orchestrator",
            "orchestration.autonomous_quest_orchestrator.AutonomousOrchestrator",
        ),
        ("Quantum Problem Resolver", "healing.quantum_problem_resolver.QuantumProblemResolver"),
        ("Multi-AI Orchestrator", "orchestration.unified_ai_orchestrator.UnifiedAIOrchestrator"),
        ("PU Queue", "automation.unified_pu_queue.UnifiedPUQueue"),
        ("Quest Engine", "Rosetta_Quest_System.quest_engine.QuestEngine"),
    ]

    available_count = 0
    for name, import_path in components:
        result = check_component(name, import_path)
        status_icon = "✅" if result["available"] else "❌"
        print(f"{status_icon} {name}")

        if args.verbose and not result["available"]:
            print(f"   Error: {result['details']}")

        if result["available"]:
            available_count += 1

    print(f"\n📊 Components Available: {available_count}/{len(components)}")

    # Check key files
    print("\n📄 Key Files:")
    print("-" * 80)

    files = [
        ("Autonomous Loop Source", "src/automation/autonomous_loop.py"),
        ("Autonomous Monitor Source", "src/automation/autonomous_monitor.py"),
        ("Integration Tests", "scripts/wire_autonomous_system.py"),
        ("Startup Script", "scripts/start_autonomous_systems.ps1"),
        ("Quick Start Guide", "docs/AUTONOMOUS_QUICK_START.md"),
        ("System Analysis", "docs/AUTONOMOUS_SYSTEM_ANALYSIS.md"),
    ]

    files_exist = 0
    for name, file_path in files:
        result = check_file_exists(name, file_path)
        status_icon = "✅" if result["exists"] else "❌"
        print(f"{status_icon} {name}")

        if args.verbose and result["exists"]:
            print(f"   Size: {result['size_kb']}")

        if result["exists"]:
            files_exist += 1

    print(f"\n📊 Files Present: {files_exist}/{len(files)}")

    # Check external dependencies
    print("\n🔌 External Dependencies:")
    print("-" * 80)

    # Check Ollama
    try:
        import requests

        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ Ollama: {len(models)} models available")
            if args.verbose:
                for model in models[:5]:  # Show first 5
                    print(f"   - {model['name']}")
                if len(models) > 5:
                    print(f"   ... and {len(models) - 5} more")
        else:
            print("❌ Ollama: Service running but API error")
    except Exception:
        print("❌ Ollama: Not available (http://127.0.0.1:11434)")

    # Check ChatDev (multiple possible locations)
    chatdev_locations = [
        Path.home() / "NuSyQ" / "ChatDev",  # Primary: C:\Users\{user}\NuSyQ\ChatDev
        ROOT.parent.parent / "NuSyQ" / "ChatDev",  # Fallback: within Desktop
        ROOT / "ChatDev",  # Fallback: within NuSyQ-Hub
    ]
    chatdev_path = None
    for location in chatdev_locations:
        if location.exists():
            chatdev_path = location
            print(f"✅ ChatDev: Found at {chatdev_path}")
            break
    if chatdev_path is None:
        print("❌ ChatDev: Not found in expected locations")

    # Check SimulatedVerse
    sv_path = Path.home() / "Desktop" / "SimulatedVerse" / "SimulatedVerse"
    if sv_path.exists():
        print(f"✅ SimulatedVerse: Found at {sv_path}")
    else:
        print("⚠️  SimulatedVerse: Not found in expected location")

    # Overall health
    print("\n" + "=" * 80)
    total_health = (available_count / len(components)) * 100

    if total_health >= 80:
        health_icon = "✅"
        health_status = "HEALTHY"
    elif total_health >= 50:
        health_icon = "⚠️"
        health_status = "DEGRADED"
    else:
        health_icon = "❌"
        health_status = "CRITICAL"

    print(f"{health_icon} Overall Health: {total_health:.0f}% - {health_status}")
    print("=" * 80)

    # Recommendations
    if total_health < 100:
        print("\n💡 Recommendations:")
        if available_count < len(components):
            print("  • Run: pip install -r requirements.txt")
            print("  • Check Python version: python --version (requires 3.12+)")
        if chatdev_path is None:
            print("  • Install ChatDev or verify location at C:\\Users\\{user}\\NuSyQ\\ChatDev")
        print("")
    else:
        print("\n🚀 System ready! Next steps:")
        print("  • Run integration tests: python scripts/wire_autonomous_system.py --test-mode")
        print("  • Start supervised mode: .\\scripts\\start_autonomous_systems.ps1")
        print("  • Read quick start: docs/AUTONOMOUS_QUICK_START.md")
        print("")

    # Exit code based on health
    exit_code = 0 if total_health >= 80 else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
