"""Run a non-interactive Terminal Depths demo.

This script instantiates a GameSession and runs a few commands to show the game engine
responding. It is intended to be used in automated/scripted environments (like this agent).

To play interactively in your own terminal, run:
    python -m cli.devmentor play

"""

import os
import sys

# Ensure Dev-Mentor root is on the import path (for running from other cwd)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.game_engine.session import GameSession

session = GameSession("demo-session")
cmds = session.cmds

# Sample commands to execute
commands = [
    "pwd",
    "ls",
    "whoami",
    "id",
    "uname -a",
    "help",
    "tutorial",
    "inventory",
    "skills",
    "story",
    "challenge list",
]

for c in commands:
    print("\n===", c, "===")
    out = cmds.execute(c)
    for line in out:
        print(line.get("s", ""))
