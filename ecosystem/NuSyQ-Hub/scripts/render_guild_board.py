#!/usr/bin/env python3
"""Guild Board Markdown Renderer - Export guild state to docs/GUILD_BOARD.md"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.guild.guild_board import GuildBoard
from src.utils.terminal_output import to_metrics


def render_guild_board_markdown(output_path: Path | None = None) -> str:
    """Render guild board to markdown format."""
    if output_path is None:
        output_path = Path(__file__).parent.parent / "docs" / "GUILD_BOARD.md"

    try:
        board = GuildBoard()
    except Exception as e:
        return f"ERROR: Failed to load guild board: {e}"

    # Build markdown
    lines = []
    lines.append("# 🏰 Adventurer's Guild Board")
    lines.append("")
    lines.append(f"*Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Active Agents
    lines.append("## 🤖 Active Agents")
    lines.append("")

    if board.board.agents:
        agent_count = len(board.board.agents)
        lines.append(f"**Total Agents**: {agent_count}")
        lines.append("")

        for agent_id, heartbeat in board.board.agents.items():
            status_emoji = {
                "idle": "💤",
                "working": "⚙️",
                "blocked": "🚫",
                "observing": "👀",
                "offline": "📴",
            }.get(heartbeat.status.value, "❓")

            lines.append(f"### {status_emoji} {agent_id}")
            lines.append(f"- **Status**: {heartbeat.status.value}")
            if heartbeat.current_quest:
                lines.append(f"- **Current Quest**: `{heartbeat.current_quest}`")
            if heartbeat.capabilities:
                lines.append(f"- **Capabilities**: {', '.join(heartbeat.capabilities)}")
            if heartbeat.confidence_level < 1.0:
                lines.append(f"- **Confidence**: {heartbeat.confidence_level:.0%}")
            if heartbeat.blockers:
                lines.append(f"- **Blockers**: {', '.join(heartbeat.blockers)}")
            lines.append(f"- **Last Seen**: {heartbeat.timestamp}")
            lines.append("")
    else:
        lines.append("*No agents currently registered*")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Quest Status
    lines.append("## 📋 Quest Status")
    lines.append("")

    if board.board.quests:
        # Group by state
        by_state = {}
        for quest_id, quest in board.board.quests.items():
            state = quest.state.value
            if state not in by_state:
                by_state[state] = []
            by_state[state].append((quest_id, quest))

        # Summary
        lines.append("### Summary")
        lines.append("")
        for state in ["open", "claimed", "active", "done", "blocked", "abandoned"]:
            count = len(by_state.get(state, []))
            if count > 0:
                emoji = {
                    "open": "📌",
                    "claimed": "✋",
                    "active": "⚙️",
                    "done": "✅",
                    "blocked": "🚫",
                    "abandoned": "❌",
                }.get(state, "❓")
                lines.append(f"- {emoji} **{state.title()}**: {count}")
        lines.append("")

        # Active/Claimed Quests
        if by_state.get("active") or by_state.get("claimed"):
            lines.append("### 🎯 In Progress")
            lines.append("")

            for state in ["active", "claimed"]:
                for quest_id, quest in by_state.get(state, []):
                    lines.append(f"#### {quest.title}")
                    lines.append(f"- **ID**: `{quest_id}`")
                    lines.append(f"- **State**: {quest.state.value}")
                    lines.append(f"- **Priority**: {'⭐' * quest.priority}")
                    if quest.claimed_by:
                        lines.append(f"- **Assigned**: {quest.claimed_by}")
                    lines.append(f"- **Safety**: {quest.safety_tier}")
                    if quest.description:
                        lines.append(f"- **Description**: {quest.description}")
                    if quest.tags:
                        lines.append(f"- **Tags**: {', '.join(quest.tags)}")
                    lines.append("")

        # Open Quests
        if by_state.get("open"):
            lines.append("### 📌 Available Quests")
            lines.append("")

            for quest_id, quest in sorted(by_state.get("open", []), key=lambda x: -x[1].priority):
                lines.append(f"#### {quest.title}")
                lines.append(f"- **ID**: `{quest_id}`")
                lines.append(f"- **Priority**: {'⭐' * quest.priority}")
                lines.append(f"- **Safety**: {quest.safety_tier}")
                if quest.description:
                    lines.append(f"- **Description**: {quest.description}")
                if quest.acceptance_criteria:
                    lines.append("- **Acceptance Criteria**:")
                    for criterion in quest.acceptance_criteria:
                        lines.append(f"  - {criterion}")
                if quest.tags:
                    lines.append(f"- **Tags**: {', '.join(quest.tags)}")
                lines.append("")

        # Completed Quests (last 10)
        if by_state.get("done"):
            lines.append("### ✅ Recently Completed")
            lines.append("")

            completed = sorted(by_state.get("done", []), key=lambda x: x[1].completed_at or "", reverse=True)[:10]

            for quest_id, quest in completed:
                lines.append(f"- **{quest.title}** (`{quest_id}`)")
                if quest.claimed_by:
                    lines.append(f"  - Completed by: {quest.claimed_by}")
                if quest.completed_at:
                    lines.append(f"  - Completed: {quest.completed_at}")
                lines.append("")

    else:
        lines.append("*No quests available*")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Recent Activity
    lines.append("## 📢 Recent Activity")
    lines.append("")

    if board.board.recent_posts:
        for post in reversed(board.board.recent_posts[-10:]):
            lines.append(f"### {post.agent_id}")
            lines.append(f"*{post.timestamp}*")
            lines.append("")
            lines.append(f"{post.message}")
            lines.append("")
    else:
        lines.append("*No recent activity*")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Generated by Guild Board Renderer*")

    markdown = "\n".join(lines)

    # Write to file
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        to_metrics(f"📊 Guild board rendered: {len(board.board.quests)} quests, {len(board.board.agents)} agents")
        return f"✅ Rendered to {output_path}"
    except Exception as e:
        return f"❌ Failed to write file: {e}"


def main():
    """Main entry point."""
    print("=" * 70)
    print("🏰 RENDERING GUILD BOARD")
    print("=" * 70)
    print()

    result = render_guild_board_markdown()
    print(result)

    # Also print summary
    try:
        board = GuildBoard()
        print()
        print("📊 Board State:")
        print(f"   - Agents: {len(board.board.agents)}")
        print(f"   - Quests: {len(board.board.quests)}")
        print(f"   - Recent Posts: {len(board.board.recent_posts)}")
    except Exception as e:
        print(f"⚠️  Could not load board: {e}")


if __name__ == "__main__":
    main()
