"""Action module: MJOLNIR Protocol unified agent dispatch.

Bridges ``start_nusyq.py dispatch <subcommand>`` to the standalone
``scripts/nusyq_dispatch.py`` CLI, reusing the same argparse + async
machinery.  Structured JSON output goes to stdout; an action receipt
is emitted for quest tracking.

Usage (via start_nusyq.py):
    python scripts/start_nusyq.py dispatch status --probes
    python scripts/start_nusyq.py dispatch ask ollama "Analyze this"
    python scripts/start_nusyq.py dispatch council "Best approach?" --agents=ollama,lmstudio
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from scripts.nusyq_actions.shared import emit_action_receipt


def _run_async(coro):
    """Run an async coroutine, handling existing event loops gracefully."""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)


def handle_dispatch(args: list[str], paths: Any, run_ai_task: Any = None) -> int:
    """Route ``dispatch <subcommand> ...`` to MjolnirProtocol.

    Reuses the argparse + async runner from ``scripts/nusyq_dispatch.py``
    so all output and exit code semantics are identical.

    Args:
        args: Full CLI args starting with the action name, e.g.
              ``["dispatch", "status", "--probes"]``
        paths: RepoPaths namedtuple (``paths.nusyq_hub`` used for sys.path)
        run_ai_task: Unused — kept for interface consistency with ai_actions
    """
    # Strip the leading "dispatch" action name to get subcommand args
    sub_args = args[1:] if len(args) > 1 else []

    if not sub_args:
        print(
            json.dumps(
                {
                    "mjolnir": "0.1.0",
                    "status": "error",
                    "success": False,
                    "error": "No dispatch subcommand specified. Use: status, ask, council, parallel, chain, delegate, queue",
                },
                indent=2,
            )
        )
        emit_action_receipt("dispatch", exit_code=1, metadata={"error": "no_subcommand"})
        return 1

    # Reuse nusyq_dispatch.py's parser and runner
    try:
        from scripts.nusyq_dispatch import _build_parser, _run

        parser = _build_parser()
        parsed = parser.parse_args(sub_args)

        if not parsed.command:
            parser.print_help()
            emit_action_receipt("dispatch", exit_code=1, metadata={"error": "no_command"})
            return 1

        exit_code = _run_async(_run(parsed))

        emit_action_receipt(
            "dispatch",
            exit_code=exit_code,
            metadata={
                "subcommand": parsed.command,
                "argv": sub_args,
            },
        )
        return exit_code

    except SystemExit as exc:
        # argparse calls sys.exit on --help or bad args
        code = exc.code if isinstance(exc.code, int) else 1
        emit_action_receipt("dispatch", exit_code=code, metadata={"argv": sub_args})
        return code

    except Exception as exc:
        error_msg = f"MJOLNIR dispatch error: {exc}"
        print(
            json.dumps(
                {
                    "mjolnir": "0.1.0",
                    "status": "error",
                    "success": False,
                    "error": error_msg,
                },
                indent=2,
            )
        )
        emit_action_receipt(
            "dispatch",
            exit_code=1,
            metadata={"error": str(exc), "argv": sub_args},
        )
        return 1
