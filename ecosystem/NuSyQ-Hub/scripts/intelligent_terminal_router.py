#!/usr/bin/env python3
"""Intelligent Terminal Router CLI

Provides a tiny wrapper to exercise the intelligent terminal orchestration stack.
- "demo" (default): emits sample messages to key terminals so you can see routing
- "state": saves orchestrator state to data/agent_terminals/orchestrator_state.json
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Sequence
from pathlib import Path

# Make src/ importable when executed as a script
if __package__ in {None, ""}:
    REPO_ROOT = Path(__file__).resolve().parents[1]
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

from src.system.agent_terminal_router import get_router
from src.system.multi_agent_terminal_orchestrator import (
    AgentType,
    TerminalType,
    init_orchestrator,
)


async def _run_demo() -> int:
    orchestrator = await init_orchestrator()
    router = await get_router()

    await router.route_agent_output(
        AgentType.CLAUDE,
        "🧠 Intelligent terminal router demo: Claude channel alive",
    )
    await router.route_event(
        event_type="task_started",
        source_agent=AgentType.COPILOT,
        message="Task started (demo)",
        context={"task_id": "demo-task", "status": "started"},
    )
    await router.route_event(
        event_type="task_completed",
        source_agent=AgentType.COPILOT,
        message="Task completed (demo)",
        context={"task_id": "demo-task", "status": "completed"},
    )
    await router.route_error(
        agent=AgentType.CODEX,
        error_message="Demo error routed to Errors terminal",
        error_type="DemoError",
    )
    await orchestrator.write_to_terminal(
        agent=AgentType.INTERMEDIARY,
        terminal=TerminalType.MAIN,
        message="📋 Demo complete - check dedicated terminals or logs/agent_terminals/*.log",
    )
    await orchestrator.save_state()
    return 0


async def _save_state() -> int:
    orchestrator = await init_orchestrator()
    await orchestrator.save_state()
    state_path = orchestrator.state_dir / "orchestrator_state.json"
    print(f"📄 Saved orchestrator state: {state_path}")
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Intelligent Terminal Router CLI")
    parser.add_argument(
        "command",
        nargs="?",
        default="demo",
        choices=["demo", "state"],
        help="demo: send sample routes | state: save orchestrator state",
    )
    return parser.parse_args(argv)


async def _main_async(command: str) -> int:
    if command == "state":
        return await _save_state()
    return await _run_demo()


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return asyncio.run(_main_async(args.command))
    except KeyboardInterrupt:
        print("Interrupted.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
