#!/usr/bin/env python3
"""NuSyQ-Hub Tool Dashboard CLI: Enumerate and invoke analyzers/fixers."""

import argparse
import asyncio

from src.orchestration.healing_cycle_scheduler import (
    run_batch_4_fast_analyzer,
    run_batch_4_unused_imports_fixer,
    run_quantum_problem_resolver,
    run_quest_based_auditor,
)

tool_map = {
    "batch_4_fast_analyzer": run_batch_4_fast_analyzer,
    "batch_4_unused_imports_fixer": run_batch_4_unused_imports_fixer,
    "quest_based_auditor": run_quest_based_auditor,
    "quantum_problem_resolver": run_quantum_problem_resolver,
}


def list_tools():
    print("Available analyzers/fixers:")
    for name in tool_map:
        print(f"- {name}")


def main():
    parser = argparse.ArgumentParser(description="NuSyQ-Hub Tool Dashboard CLI")
    parser.add_argument("--list", action="store_true", help="List all available tools")
    parser.add_argument("--run", type=str, help="Run a specific tool by name")
    args = parser.parse_args()

    if args.list:
        list_tools()
        return

    if args.run:
        tool = tool_map.get(args.run)
        if not tool:
            print(f"Tool '{args.run}' not found.")
            list_tools()
            return
        print(f"Running tool: {args.run}\n---")
        result = asyncio.run(tool())
        print("---\nResult:")
        print(result)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
