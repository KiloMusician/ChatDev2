#!/usr/bin/env python3
"""Direct ChatDev Test - Enhanced Interactive Context Browser
Test the ChatDev integration by running a development task
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append("src")


def analyze_current_browser() -> None:
    """Analyze the current Interactive Context Browser"""
    print("\n🔍 Analyzing current Interactive Context Browser...")

    browser_path = Path("src/interface/Enhanced-Interactive-Context-Browser.py")

    if not browser_path.exists():
        print(f"❌ Browser file not found at {browser_path}")
        return

    with open(browser_path, "r", encoding="utf-8") as f:
        content = f.read()

    print("📊 Current browser stats:")
    print(f"  Lines of code: {len(content.splitlines())}")
    print(f"  File size: {len(content)} characters")

    # Basic analysis
    import_count = content.count("import ")
    class_count = content.count("class ")
    function_count = content.count("def ")

    print(f"  Imports: {import_count}")
    print(f"  Classes: {class_count}")
    print(f"  Functions: {function_count}")

    # Check for key technologies
    technologies = {
        "Streamlit": "streamlit" in content,
        "Pandas": "pandas" in content,
        "Plotly": "plotly" in content,
        "NetworkX": "networkx" in content,
        "KILO-FOOLISH": "KILO" in content,
    }

    print("  Technologies detected:")
    for tech, present in technologies.items():
        status = "✅" if present else "❌"
        print(f"    {status} {tech}")


def test_chatdev_integration() -> None:
    """Attempt to initialize ChatDev integration if available; doesn't fail if missing."""
    print("🚀 Testing ChatDev Integration for Interactive Context Browser Enhancement")
    print("=" * 70)

    try:
        # Import lazily via importlib to avoid static import resolution errors
        import importlib

        chatdev_mod = importlib.import_module("integration.chatdev_integration")
        manager_cls = getattr(chatdev_mod, "ChatDevIntegrationManager", None)
        session_func = getattr(chatdev_mod, "launch_chatdev_session", None)

        if manager_cls is None or session_func is None:
            print("Info: ChatDev integration symbols missing; skipping integration run.")
            return

        manager = manager_cls()
        print("\n📋 Initializing ChatDev Integration...")
        status = manager.initialize_chatdev_integration()
        print("\n🔍 Integration Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")

        if not status.get("launcher_available", False):
            print("\nInfo: ChatDev launcher not available; skipping session launch.")
            return

        task_description = (
            "Enhance the Interactive Context Browser with modern UI, repository analytics, "
            "and performance optimizations."
        )
        print("\n🎯 Launching ChatDev session for Interactive Context Browser enhancement...")
        print(f"Task: {task_description[:100]}...")

        result = session_func(
            task_description=task_description,
            output_dir="chatdev_output/enhanced_browser",
        )
        print("\n📊 ChatDev Session Result:")
        for key, value in result.items():
            print(f"  {key}: {value}")

    except ImportError:
        # Integration not available in this environment; this test is non-blocking
        print("Info: ChatDev integration module not available; skipping integration run.")
        return
