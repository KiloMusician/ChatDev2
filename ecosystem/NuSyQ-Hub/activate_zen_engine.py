#!/usr/bin/env python3
"""Zen-Engine Activation Script.

Quick-start script to activate and demonstrate the Zen-Engine.

Usage:
    python activate_zen_engine.py
    python activate_zen_engine.py --demo
    python activate_zen_engine.py --check "your command here"

OmniTag: [zen-engine, activation, quickstart]
"""

import argparse
import json
import sys
from pathlib import Path

# Ensure zen_engine is in path
sys.path.insert(0, str(Path(__file__).parent))


def print_banner():
    """Print activation banner."""
    print("\n" + "🧘" * 40)
    print(
        """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║           ZEN-ENGINE: RECURSIVE WISDOM SYSTEM            ║
    ║                                                          ║
    ║     Observe → Learn → Prevent → Evolve → ∞              ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    )
    print("🧘" * 40 + "\n")


def check_installation():
    """Check if Zen-Engine is properly installed."""
    print("🔍 Checking Zen-Engine installation...\n")

    checks = {
        "Codex file": Path("zen_engine/codex/zen.json"),
        "Agents module": Path("zen_engine/agents"),
        "Systems module": Path("zen_engine/systems"),
        "CLI tools": Path("zen_engine/cli"),
        "Documentation": Path("zen_engine/README.md"),
        "Glyph Lexicon": Path("zen_engine/codex/lore/glyph_lexicon.md"),
    }

    all_good = True
    for name, path in checks.items():
        exists = path.exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {name}: {path}")
        if not exists:
            all_good = False

    print()
    return all_good


def show_system_info():
    """Display system information."""
    try:
        # Import after path is set
        sys.path.insert(0, str(Path(__file__).parent))

        print("📊 System Information:\n")

        # Try to load codex
        codex_path = Path("zen_engine/codex/zen.json")
        if codex_path.exists():
            with open(codex_path, encoding="utf-8") as f:
                codex = json.load(f)

            print(f"  Version: {codex['meta']['version']}")
            print(f"  Rules: {len(codex['rules'])}")
            print(f"  Rule Clusters: {len(codex.get('rule_clusters', {}))}")
            print(f"  Last Updated: {codex['meta']['last_updated']}")

            print("\n📚 Available Rules:")
            for rule in codex["rules"][:5]:
                print(f"  - {rule['id']}: {rule['lesson']['short']}")

            if len(codex["rules"]) > 5:
                print(f"  ... and {len(codex['rules']) - 5} more")
        else:
            print("  ⚠️  Codex not found")

        print()

    except Exception as e:
        print(f"  ⚠️  Could not load system info: {e}\n")


def quick_check(command: str, shell: str = "powershell"):
    """Quick command check."""
    try:
        from zen_engine.agents.reflex import ReflexEngine

        print(f"\n🔍 Checking: {command}")
        print(f"   Shell: {shell}\n")
        print("-" * 60)

        reflex = ReflexEngine()
        response = reflex.check_command(command, shell=shell)

        if response.status == "ok":
            print("✅ Command looks good!")
        else:
            print(f"⚠️  {response.message}")
            if response.suggested_command:
                print(f"\n💡 Suggested:\n   {response.suggested_command}")

        print()

    except Exception as e:
        print(f"❌ Error during check: {e}\n")


def run_demo():
    """Run the full demonstration."""
    try:
        print("🎬 Running full Zen-Engine demonstration...\n")
        print("This will showcase all system capabilities.\n")

        import zen_engine.demo_zen_engine as demo

        demo.main()

    except Exception as e:
        print(f"❌ Demo error: {e}")
        print("\nTry running: python zen_engine/demo_zen_engine.py")


def main():
    """Main activation script."""
    parser = argparse.ArgumentParser(
        description="Zen-Engine Activation and Quick-Start",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python activate_zen_engine.py
  python activate_zen_engine.py --demo
  python activate_zen_engine.py --check "import os" --shell powershell
  python activate_zen_engine.py --info
        """,
    )

    parser.add_argument("--demo", action="store_true", help="Run full demonstration")
    parser.add_argument("--check", help="Quick command check")
    parser.add_argument("--shell", default="powershell", help="Shell for command check")
    parser.add_argument("--info", action="store_true", help="Show system information")

    args = parser.parse_args()

    print_banner()

    # Check installation
    if not check_installation():
        print("⚠️  Some components are missing. Please check the installation.\n")
        print("Expected structure:")
        print("  zen_engine/")
        print("    ├── codex/")
        print("    │   └── zen.json")
        print("    ├── agents/")
        print("    ├── systems/")
        print("    └── cli/\n")
        return

    print("✅ Zen-Engine is properly installed!\n")

    # Execute requested action
    if args.demo:
        run_demo()
    elif args.check:
        quick_check(args.check, args.shell)
    elif args.info:
        show_system_info()
    else:
        # Default: show info and usage
        show_system_info()

        print("🚀 Quick Start Guide:\n")
        print("  1. Run full demo:")
        print("     python activate_zen_engine.py --demo\n")
        print("  2. Check a command:")
        print('     python activate_zen_engine.py --check "import os"\n')
        print("  3. Interactive mode:")
        print("     python zen_engine/cli/zen_check.py --interactive\n")
        print("  4. Capture errors:")
        print('     python zen_engine/cli/zen_capture.py --text "your error"\n')
        print("  5. Read documentation:")
        print("     zen_engine/README.md\n")

        print("🧘 May your code flow like water, and your errors teach like masters.\n")


if __name__ == "__main__":
    main()
