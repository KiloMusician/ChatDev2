"""Action module: Guild board operations."""

from __future__ import annotations

import json
from collections.abc import Callable

from scripts.nusyq_actions.shared import emit_action_receipt


def handle_guild_status(run_guild: Callable) -> int:
    """Show guild board summary."""
    try:
        from src.guild.guild_cli import board_status

        result = run_guild(board_status())
        print(json.dumps(result, indent=2, default=str))
        emit_action_receipt("guild_status", exit_code=0, metadata={"result": "success"})
        return 0
    except Exception as exc:
        print(f"[ERROR] Guild status failed: {exc}")
        emit_action_receipt("guild_status", exit_code=1, metadata={"error": str(exc)})
        return 1


def handle_guild_render(run_guild: Callable) -> int:
    """Render guild board to docs/GUILD_BOARD.md."""
    try:
        from src.guild.guild_cli import board_render

        result = run_guild(board_render())
        print(json.dumps(result, indent=2, default=str))
        emit_action_receipt("guild_render", exit_code=0)
        return 0
    except Exception as exc:
        print(f"[ERROR] Guild render failed: {exc}")
        emit_action_receipt("guild_render", exit_code=1, metadata={"error": str(exc)})
        return 1


def handle_guild_heartbeat(args: list[str], run_guild: Callable) -> int:
    """Post agent heartbeat to the guild board."""
    if len(args) < 2:
        print("Usage: python start_nusyq.py guild_heartbeat <agent> [status] [quest_id]")
        emit_action_receipt("guild_heartbeat", exit_code=1, metadata={"error": "missing_agent"})
        return 1
    agent = args[1]
    status = args[2] if len(args) > 2 else "idle"
    quest_id = args[3] if len(args) > 3 else None
    try:
        from src.guild.guild_cli import board_heartbeat

        result = run_guild(board_heartbeat(agent, status, quest_id))
        print(json.dumps(result, indent=2, default=str))
        emit_action_receipt(
            "guild_heartbeat",
            exit_code=0,
            metadata={"agent": agent, "status": status, "quest_id": quest_id},
        )
        return 0
    except Exception as exc:
        print(f"[ERROR] Guild heartbeat failed: {exc}")
        emit_action_receipt("guild_heartbeat", exit_code=1, metadata={"error": str(exc)})
        return 1


def handle_guild_claim(args: list[str], run_guild: Callable) -> int:
    """Claim a quest on the guild board."""
    if len(args) < 3:
        print("Usage: python start_nusyq.py guild_claim <agent> <quest_id>")
        emit_action_receipt("guild_claim", exit_code=1, metadata={"error": "missing_args"})
        return 1
    agent = args[1]
    quest_id = args[2]
    try:
        from src.guild.guild_cli import board_claim

        result = run_guild(board_claim(agent, quest_id))
        print(json.dumps(result, indent=2, default=str))
        emit_action_receipt(
            "guild_claim",
            exit_code=0,
            metadata={"agent": agent, "quest_id": quest_id},
        )
        return 0
    except Exception as exc:
        print(f"[ERROR] Guild claim failed: {exc}")
        emit_action_receipt("guild_claim", exit_code=1, metadata={"error": str(exc)})
        return 1


def handle_guild_start(args: list[str], run_guild: Callable) -> int:
    """Start a quest on the guild board."""
    if len(args) < 3:
        print("Usage: python start_nusyq.py guild_start <agent> <quest_id>")
        emit_action_receipt("guild_start", exit_code=1, metadata={"error": "missing_args"})
        return 1
    agent = args[1]
    quest_id = args[2]
    try:
        from src.guild.guild_cli import board_start

        result = run_guild(board_start(agent, quest_id))
        print(json.dumps(result, indent=2, default=str))
        emit_action_receipt(
            "guild_start",
            exit_code=0,
            metadata={"agent": agent, "quest_id": quest_id},
        )
        return 0
    except Exception as exc:
        print(f"[ERROR] Guild start failed: {exc}")
        emit_action_receipt("guild_start", exit_code=1, metadata={"error": str(exc)})
        return 1


def handle_guild_post(args: list[str], run_guild: Callable) -> int:
    """Post a guild board update."""
    if len(args) < 3:
        print("Usage: python start_nusyq.py guild_post <agent> <message> [quest_id] [type]")
        emit_action_receipt("guild_post", exit_code=1, metadata={"error": "missing_args"})
        return 1
    agent = args[1]
    message = args[2]
    quest_id = args[3] if len(args) > 3 else None
    post_type = args[4] if len(args) > 4 else "progress"
    try:
        from src.guild.guild_cli import board_post

        result = run_guild(board_post(agent, message, quest_id, post_type))
        print(json.dumps(result, indent=2, default=str))
        emit_action_receipt(
            "guild_post",
            exit_code=0,
            metadata={"agent": agent, "quest_id": quest_id, "type": post_type},
        )
        return 0
    except Exception as exc:
        print(f"[ERROR] Guild post failed: {exc}")
        emit_action_receipt("guild_post", exit_code=1, metadata={"error": str(exc)})
        return 1


def handle_guild_complete(args: list[str], run_guild: Callable) -> int:
    """Complete a quest on the guild board."""
    if len(args) < 3:
        print("Usage: python start_nusyq.py guild_complete <agent> <quest_id>")
        emit_action_receipt("guild_complete", exit_code=1, metadata={"error": "missing_args"})
        return 1
    agent = args[1]
    quest_id = args[2]
    try:
        from src.guild.guild_cli import board_complete

        result = run_guild(board_complete(agent, quest_id))
        print(json.dumps(result, indent=2, default=str))
        emit_action_receipt(
            "guild_complete",
            exit_code=0,
            metadata={"agent": agent, "quest_id": quest_id},
        )
        return 0
    except Exception as exc:
        print(f"[ERROR] Guild complete failed: {exc}")
        emit_action_receipt("guild_complete", exit_code=1, metadata={"error": str(exc)})
        return 1


def handle_guild_available(args: list[str], run_guild: Callable) -> int:
    """List quests matching agent capabilities."""
    if len(args) < 2:
        print("Usage: python start_nusyq.py guild_available <agent> [cap1,cap2]")
        emit_action_receipt("guild_available", exit_code=1, metadata={"error": "missing_agent"})
        return 1
    agent = args[1]
    capabilities = args[2].split(",") if len(args) > 2 else []
    try:
        from src.guild.guild_cli import board_available_quests

        result = run_guild(board_available_quests(agent, capabilities))
        print(json.dumps(result, indent=2, default=str))
        emit_action_receipt(
            "guild_available",
            exit_code=0,
            metadata={"agent": agent, "capabilities": capabilities},
        )
        return 0
    except Exception as exc:
        print(f"[ERROR] Guild available failed: {exc}")
        emit_action_receipt("guild_available", exit_code=1, metadata={"error": str(exc)})
        return 1


def handle_guild_add_quest(args: list[str], run_guild: Callable) -> int:
    """Add a quest to the guild board."""
    if len(args) < 4:
        print("Usage: python start_nusyq.py guild_add_quest <agent> <title> <description> [priority] [safety] [tags]")
        emit_action_receipt("guild_add_quest", exit_code=1, metadata={"error": "missing_args"})
        return 1
    agent = args[1]
    title = args[2]
    description = args[3]
    # Support both numeric (1-5) and string priorities (low, medium, high, critical)
    priority_map = {"low": 1, "medium": 3, "high": 4, "critical": 5}
    if len(args) > 4:
        raw_priority = args[4].lower()
        priority = priority_map.get(raw_priority, int(raw_priority) if raw_priority.isdigit() else 3)
    else:
        priority = 3
    safety = args[5] if len(args) > 5 else "safe"
    tags = args[6].split(",") if len(args) > 6 else []
    try:
        from src.guild.guild_cli import board_add_quest

        result = run_guild(board_add_quest(agent, title, description, priority=priority, safety_tier=safety, tags=tags))
        print(json.dumps(result, indent=2, default=str))
        emit_action_receipt(
            "guild_add_quest",
            exit_code=0,
            metadata={"agent": agent, "title": title, "priority": priority},
        )
        return 0
    except Exception as exc:
        print(f"[ERROR] Guild add quest failed: {exc}")
        emit_action_receipt("guild_add_quest", exit_code=1, metadata={"error": str(exc)})
        return 1


def handle_guild_close_quest(args: list[str], run_guild: Callable) -> int:
    """Close a quest on the guild board."""
    if len(args) < 3:
        print("Usage: python start_nusyq.py guild_close_quest <agent> <quest_id> [status] [reason]")
        emit_action_receipt("guild_close_quest", exit_code=1, metadata={"error": "missing_args"})
        return 1
    agent = args[1]
    quest_id = args[2]
    status = args[3] if len(args) > 3 else "done"
    reason = args[4] if len(args) > 4 else None
    try:
        from src.guild.guild_cli import board_close_quest

        result = run_guild(board_close_quest(agent, quest_id, status, reason))
        print(json.dumps(result, indent=2, default=str))
        emit_action_receipt(
            "guild_close_quest",
            exit_code=0,
            metadata={"agent": agent, "quest_id": quest_id, "status": status},
        )
        return 0
    except Exception as exc:
        print(f"[ERROR] Guild close quest failed: {exc}")
        emit_action_receipt("guild_close_quest", exit_code=1, metadata={"error": str(exc)})
        return 1


def handle_guild_register(args: list[str], run_guild: Callable) -> int:
    """Register an agent on the guild board (via heartbeat with capabilities)."""
    if len(args) < 2:
        print("Usage: python start_nusyq.py guild_register <agent> [capabilities] [status]")
        print("Example: python start_nusyq.py guild_register claude code,analysis,testing idle")
        emit_action_receipt("guild_register", exit_code=1, metadata={"error": "missing_agent"})
        return 1
    agent = args[1]
    capabilities = args[2].split(",") if len(args) > 2 else []
    status = args[3] if len(args) > 3 else "idle"
    try:
        from src.guild.guild_cli import board_heartbeat

        # Register agent by sending heartbeat with capabilities
        result = run_guild(board_heartbeat(agent, status, None, capabilities))
        print(f"✅ Agent '{agent}' registered on guild board")
        print(json.dumps(result, indent=2, default=str))
        emit_action_receipt(
            "guild_register",
            exit_code=0,
            metadata={"agent": agent, "status": status, "capabilities": capabilities},
        )
        return 0
    except Exception as exc:
        print(f"[ERROR] Guild register failed: {exc}")
        emit_action_receipt("guild_register", exit_code=1, metadata={"error": str(exc)})
        return 1


def handle_log_quest(args: list[str]) -> int:
    """Log an event to the Rosetta Quest System quest log."""
    if len(args) < 3:
        print("Usage: python start_nusyq.py log_quest <event> <details_json>")
        print('Example: python start_nusyq.py log_quest "quest_started" \'{"quest_id": "q-123"}\'')
        emit_action_receipt("log_quest", exit_code=1, metadata={"error": "missing_args"})
        return 1
    event = args[1]
    details_str = args[2]
    try:
        details = json.loads(details_str)
    except json.JSONDecodeError:
        # If not valid JSON, treat as simple message
        details = {"message": details_str}
    try:
        from src.Rosetta_Quest_System.quest_engine import log_event

        log_event(event, details)
        print(f"✅ Logged quest event: {event}")
        print(json.dumps({"event": event, "details": details}, indent=2))
        emit_action_receipt("log_quest", exit_code=0, metadata={"event": event})
        return 0
    except Exception as exc:
        print(f"[ERROR] Log quest failed: {exc}")
        emit_action_receipt("log_quest", exit_code=1, metadata={"error": str(exc)})
        return 1
