#!/usr/bin/env python3
"""Interactive Example Runner - Surface Orphaned Documentation Examples

This script rehabilitates the 18 orphaned example functions in examples/
by creating an interactive CLI menu. Instead of deleting valuable tutorial
code, we make it discoverable.

Usage:
    python scripts/run_examples_interactive.py
    python scripts/run_examples_interactive.py --example=1
    python scripts/run_examples_interactive.py --list
"""

import argparse
import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class Example:
    """Represents a runnable code example."""

    id: int
    name: str
    description: str
    module: str
    function_name: str
    is_async: bool = False


# Registry of all orphaned examples across the codebase
EXAMPLES = [
    Example(
        1,
        "Basic Ollama",
        "Simple local LLM inference with Ollama",
        "examples.claude_orchestrator_usage",
        "example_1_basic_ollama",
        is_async=True,
    ),
    Example(
        2,
        "Code Review",
        "Multi-AI code review with consensus voting",
        "examples.claude_orchestrator_usage",
        "example_2_code_review",
        is_async=True,
    ),
    Example(
        3,
        "Multi-AI Consensus",
        "Parallel Claude + Ollama consensus decision",
        "examples.claude_orchestrator_usage",
        "example_3_multi_ai_consensus",
        is_async=True,
    ),
    Example(
        4,
        "Obsidian Logging",
        "Structured logging to markdown knowledge base",
        "examples.claude_orchestrator_usage",
        "example_4_obsidian_logging",
        is_async=True,
    ),
    Example(
        5,
        "Health Check",
        "System health diagnostics with rate limiting",
        "examples.claude_orchestrator_usage",
        "example_5_health_check",
        is_async=True,
    ),
    Example(
        6,
        "List Models",
        "Discover available Ollama models",
        "examples.claude_orchestrator_usage",
        "example_6_list_models",
        is_async=True,
    ),
    Example(
        7,
        "ChatDev Spawn",
        "Launch multi-agent software development team",
        "examples.claude_orchestrator_usage",
        "example_7_chatdev_spawn",
        is_async=True,
    ),
    Example(
        8,
        "Traced Operations",
        "OpenTelemetry distributed tracing examples",
        "examples.claude_orchestrator_usage",
        "example_8_traced_operations",
        is_async=True,
    ),
    Example(
        9,
        "Batch Processing",
        "Parallel task processing with progress tracking",
        "examples.claude_orchestrator_usage",
        "example_9_batch_processing",
        is_async=True,
    ),
    Example(
        10,
        "Error Handling",
        "Graceful degradation and retry patterns",
        "examples.claude_orchestrator_usage",
        "example_10_error_handling",
        is_async=True,
    ),
    Example(
        11,
        "Structured Logging with Rate Limiting",
        "Health check with structured log integration",
        "examples.observability.structured_logging_integration",
        "example_health_check_with_rate_limiting",
        is_async=True,
    ),
    Example(
        12,
        "SNS Orchestrator Quick Demo",
        "Fast demonstration of orchestration capabilities",
        "examples.sns_orchestrator_demo",
        "quick_demo",
        is_async=True,
    ),
]


def print_menu():
    """Display interactive example menu."""
    print("\n" + "=" * 70)
    print("🎓 NuSyQ-Hub Interactive Examples - Tutorial Mode")
    print("=" * 70)
    print("\nAvailable Examples:\n")

    for example in EXAMPLES:
        status = "⚡ async" if example.is_async else "🔄 sync"
        print(f"  [{example.id:2d}] {example.name:<30} {status}")
        print(f"       {example.description}")
        print()

    print("=" * 70)


def list_examples():
    """List all examples in machine-readable format."""
    for example in EXAMPLES:
        print(f"{example.id}|{example.name}|{example.module}|{example.function_name}")


async def run_example(example_id: int) -> None:
    """Run a specific example by ID.

    Args:
        example_id: Example number (1-N)
    """
    # Find example
    example = next((ex for ex in EXAMPLES if ex.id == example_id), None)
    if not example:
        print(f"❌ Example {example_id} not found. Valid range: 1-{len(EXAMPLES)}")
        return

    print("\n" + "=" * 70)
    print(f"🚀 Running Example {example.id}: {example.name}")
    print("=" * 70)
    print(f"Description: {example.description}")
    print(f"Module: {example.module}")
    print(f"Function: {example.function_name}")
    print("=" * 70 + "\n")

    # Dynamic import
    try:
        module = __import__(example.module, fromlist=[example.function_name])
        func = getattr(module, example.function_name)

        # Execute
        if example.is_async:
            await func()
        else:
            func()

        print("\n" + "=" * 70)
        print(f"✅ Example {example.id} completed successfully")
        print("=" * 70 + "\n")

    except ImportError as e:
        print(f"❌ Failed to import {example.module}.{example.function_name}: {e}")
        print("   Check that dependencies are installed and module exists.")
    except Exception as e:
        print(f"❌ Error running example: {e}")
        import traceback

        traceback.print_exc()


async def interactive_mode():
    """Run in interactive menu mode."""
    while True:
        print_menu()
        try:
            choice = input(f"Select example (1-{len(EXAMPLES)}, 'q' to quit): ")

            if choice.lower() in ["q", "quit", "exit"]:
                print("👋 Exiting tutorial mode")
                break

            example_id = int(choice)
            if 1 <= example_id <= len(EXAMPLES):
                await run_example(example_id)
                input("\nPress Enter to continue...")
            else:
                print(f"❌ Invalid choice. Please enter 1-{len(EXAMPLES)}")

        except ValueError:
            print("❌ Invalid input. Please enter a number or 'q' to quit")
        except KeyboardInterrupt:
            print("\n👋 Interrupted. Exiting...")
            break


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Interactive runner for NuSyQ-Hub code examples",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_examples_interactive.py              # Interactive menu
  python scripts/run_examples_interactive.py --list       # List all examples
  python scripts/run_examples_interactive.py --example=1  # Run example 1
  python scripts/run_examples_interactive.py --example=7  # Run ChatDev spawn
        """,
    )

    parser.add_argument(
        "--example",
        type=int,
        help=f"Run specific example by ID (1-{len(EXAMPLES)})",
        metavar="N",
    )

    parser.add_argument("--list", action="store_true", help="List all examples in machine-readable format")

    args = parser.parse_args()

    if args.list:
        list_examples()
    elif args.example:
        await run_example(args.example)
    else:
        await interactive_mode()


if __name__ == "__main__":
    asyncio.run(main())
