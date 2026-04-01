#!/usr/bin/env python3
"""Simple CLI to instantiate and display status of CopilotEnhancementBridge.

This command is intentionally lightweight and provides a quick smoke test that
imports the bridge and exercises its basic initialization logic.
"""

import argparse
import sys

from .copilot_enhancement_bridge import CopilotEnhancementBridge


def main() -> None:
    """Instantiate :class:`CopilotEnhancementBridge` and print initialization info."""
    parser = argparse.ArgumentParser(description="Initialize CopilotEnhancementBridge")
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root for the bridge to use",
    )
    args = parser.parse_args()

    bridge = CopilotEnhancementBridge(args.root)
    # Output basic initialization info using stdout to avoid lint "print" warnings
    sys.stdout.write(
        f"Initialized CopilotEnhancementBridge session {bridge.session_id}\n",
    )


if __name__ == "__main__":
    main()
