#!/usr/bin/env python3
"""Show open quests from guild board."""

import json
from pathlib import Path

board_path = Path(__file__).parent.parent / "data" / "guild_board.json"

if board_path.exists():
    data = json.loads(board_path.read_text())
    quests = data.get("quests", [])
    open_q = [q for q in quests if q.get("status") == "open"]
    print(f"Total Open Quests: {len(open_q)}")
    print("\nSample Open Quests (first 20):")
    print("=" * 70)
    for q in open_q[:20]:
        priority = q.get("priority", "?")
        title = q.get("title", "N/A")[:55]
        tags = ", ".join(q.get("tags", [])[:2])
        print(f"  [{priority:6}] {title:<55} ({tags})")
else:
    print("Guild board not found at:", board_path)
