"""Small CLI wrapper to emit structured terminal messages from shell scripts.

Usage:
  python scripts/emit_terminal.py Errors error "message" '{"k": "v"}'
"""

import json
import logging
import sys

# Best-effort wire terminal logging so CLI emitter messages appear in TerminalManager
try:
    from src.system.init_terminal import init_terminal_logging

    try:
        init_terminal_logging(channel="Auto-Wired", level=logging.INFO)
    except Exception:
        pass
except Exception:
    pass


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) < 3:
        print("Usage: emit_terminal.py <channel> <level> <message> [meta-json]")
        return 2
    channel, level, message = argv[0], argv[1], argv[2]
    meta = {}
    if len(argv) >= 4:
        try:
            meta = json.loads(argv[3])
        except Exception:
            meta = {}

    try:
        from src.system.enhanced_terminal_ecosystem import TerminalManager

        tm = TerminalManager.get_instance()
        tm.send(channel, level, message, meta=meta)
        return 0
    except Exception as e:
        print("Failed to send terminal message:", e)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
