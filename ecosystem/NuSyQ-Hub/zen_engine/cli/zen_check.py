#!/usr/bin/env python3
"""zen-check - Command Safety Checker

Check commands against the ZenCodex before execution.
Provides warnings, suggestions, and auto-fix options.

Usage:
    zen-check "import os"
    zen-check "git checkout main" --shell bash
    zen-check --file commands.txt
    zen-check --interactive

OmniTag: [zen-engine, cli, safety-check]
MegaTag: ZEN_ENGINE⨳CLI⦾COMMAND_CHECK→∞
"""

import argparse
import sys
from pathlib import Path

# Add zen-engine to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from zen_engine.agents import ReflexEngine


def check_single_command(command: str, shell: str, auto_fix: bool = False):
    """Check a single command."""
    reflex = ReflexEngine()

    print(f"\n🔍 Checking command: {command}")
    print(f"   Shell: {shell}")
    print("-" * 60)

    final_cmd, advice = reflex.intercept_and_advise(command, shell=shell, auto_apply_fix=auto_fix)

    if advice:
        print(advice)

    if final_cmd != command:
        print(f"\n🔄 Modified command: {final_cmd}")
    elif final_cmd:
        print("\n✅ Command approved")
    else:
        print("\n🛑 Command blocked")

    return final_cmd


def check_file(file_path: Path, shell: str):
    """Check commands from a file."""
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return

    with open(file_path, encoding="utf-8") as f:
        commands = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    reflex = ReflexEngine()
    report = reflex.generate_safety_report(commands, shell=shell)
    print(report)


def interactive_mode(shell: str):
    """Interactive command checking."""
    print("🧘 Zen-Check Interactive Mode")
    print("Enter commands to check (Ctrl+C to exit)")
    print("-" * 60)

    reflex = ReflexEngine()

    try:
        while True:
            command = input("\n💻 Command: ")
            if not command:
                continue

            final_cmd, advice = reflex.intercept_and_advise(
                command, shell=shell, auto_apply_fix=False
            )

            if advice:
                print(advice)

            if final_cmd != command:
                print(f"\n🔄 Suggested: {final_cmd}")
                apply = input("Apply fix? (y/n): ")
                if apply.lower() == "y":
                    print(f"✅ Execute: {final_cmd}")
            elif final_cmd:
                print("✅ OK")
            else:
                print("🛑 Blocked")

    except KeyboardInterrupt:
        print("\n\n👋 Exiting interactive mode")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Zen-Check: Validate commands against ZenCodex wisdom",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  zen-check "import os"
  zen-check "git checkout main" --shell bash
  zen-check --file script.sh --shell bash
  zen-check --interactive --shell powershell
        """,
    )

    parser.add_argument("command", nargs="?", help="Command to check")
    parser.add_argument(
        "--shell", default="powershell", help="Shell environment (default: powershell)"
    )
    parser.add_argument("--file", "-f", type=Path, help="File containing commands to check")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--auto-fix", action="store_true", help="Automatically apply fixes")

    args = parser.parse_args()

    if args.interactive:
        interactive_mode(args.shell)
    elif args.file:
        check_file(args.file, args.shell)
    elif args.command:
        check_single_command(args.command, args.shell, args.auto_fix)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
