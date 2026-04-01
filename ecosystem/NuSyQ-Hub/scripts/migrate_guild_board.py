#!/usr/bin/env python3
"""Migrate guild board to new schema format"""

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def migrate_guild_board():
    """Migrate old guild board format to new AgentHeartbeat format."""
    board_file = ROOT / "state" / "guild" / "guild_board.json"
    backup_file = ROOT / "state" / "guild" / "guild_board.json.backup"

    if not board_file.exists():
        print("❌ Guild board file not found")
        return

    # Backup existing file
    if board_file.exists():
        import shutil

        shutil.copy(board_file, backup_file)
        print(f"✅ Backed up to {backup_file}")

    # Load old format
    with open(board_file) as f:
        old_data = json.load(f)

    # Create new format
    new_data = {
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "agents": {},
        "quests": {},
        "recent_posts": [],
        "active_work": {},
    }

    # Migrate agents
    for agent_id, agent_data in old_data.get("agents", {}).items():
        # Convert to AgentHeartbeat format
        status_map = {
            "working": "working",
            "idle": "idle",
            "observing": "observing",
            "offline": "offline",
        }

        new_data["agents"][agent_id] = {
            "agent_id": agent_id,
            "status": status_map.get(agent_data.get("status", "idle"), "idle"),
            "current_quest": None,
            "capabilities": agent_data.get("capabilities", []),
            "confidence_level": 1.0,
            "blockers": [],
            "timestamp": datetime.now().isoformat(),
        }

    # Write new format
    with open(board_file, "w") as f:
        json.dump(new_data, f, indent=2)

    print(f"✅ Migrated {len(new_data['agents'])} agents to new format")
    print("📝 New schema version: 2.0.0")


if __name__ == "__main__":
    migrate_guild_board()
