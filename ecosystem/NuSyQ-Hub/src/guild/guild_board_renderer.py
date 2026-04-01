"""Guild Board Renderer - Generates human-readable views from board state.

Produces stable Markdown output that can be viewed in Obsidian/Markdown viewers.
Single filename (GUILD_BOARD.md) gets overwritten, so no file churn.
"""

import html
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Ensure src/ is on sys.path for both direct and module execution
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

import logging

from src.guild.guild_board import AgentStatus, GuildBoard, QuestState

logger = logging.getLogger(__name__)


class GuildBoardRenderer:
    """Renders guild board state to various formats."""

    def __init__(self, board: GuildBoard, output_dir: Path = Path("docs")):
        """Initialize GuildBoardRenderer with board, output_dir."""
        self.board = board
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def render_markdown(self) -> str:
        """Render board as Markdown."""
        lines = [
            "# ⚔️ Adventurer's Guild Board",
            "",
            f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
        ]

        # Summary
        summary = await self.board.get_board_summary()
        completed_counts: dict[str, int] = {}
        for quest in self.board.board.quests.values():
            if quest.state == QuestState.DONE and quest.claimed_by:
                completed_counts[quest.claimed_by] = completed_counts.get(quest.claimed_by, 0) + 1
        lines.extend(
            [
                "## 📊 Status Summary",
                "",
                f"- **Agents Online:** {summary['agents_online']}",
                f"- **Open Quests:** {summary['quests_open']}",
                f"- **Active Quests:** {summary['quests_active']}",
                f"- **Blocked Quests:** {summary['quests_blocked']}",
                "",
            ]
        )

        if completed_counts:
            lines.extend(
                [
                    "## ?? Scoreboard",
                    "",
                ]
            )
            for agent_id, count in sorted(
                completed_counts.items(), key=lambda item: item[1], reverse=True
            )[:5]:
                lines.append(f"- **{agent_id}**: {count} quests")
            lines.append("")

        # Critical Signals
        if summary["critical_signals"]:
            lines.extend(
                [
                    "## 🚨 Critical Signals",
                    "",
                ]
            )
            for signal in summary["critical_signals"]:
                lines.append(f"- **[{signal['type']}]** {signal['message']}")
            lines.append("")

        # Agents
        lines.extend(
            [
                "## 👥 Agents",
                "",
            ]
        )
        for agent_id, heartbeat in self.board.board.agents.items():
            status_emoji = {
                AgentStatus.IDLE: "🟢",
                AgentStatus.WORKING: "🟡",
                AgentStatus.BLOCKED: "🔴",
                AgentStatus.OBSERVING: "👁️",
                AgentStatus.OFFLINE: "⚫",
            }.get(heartbeat.status, "❓")

            lines.append(f"### {status_emoji} {agent_id}")
            lines.append(f"- **Status:** {heartbeat.status.value}")
            if heartbeat.current_quest:
                lines.append(f"- **Working on:** {heartbeat.current_quest}")
            if heartbeat.capabilities:
                lines.append(f"- **Capabilities:** {', '.join(heartbeat.capabilities)}")
            if heartbeat.blockers:
                lines.append(f"- **Blockers:** {', '.join(heartbeat.blockers)}")
            lines.append("")

        # Active Work
        if self.board.board.active_work:
            lines.extend(
                [
                    "## ⚙️ Active Work",
                    "",
                ]
            )
            for quest_id, agent_id in self.board.board.active_work.items():
                if quest_id in self.board.board.quests:
                    quest = self.board.board.quests[quest_id]
                    lines.append(f"- **{agent_id}** working on: {quest.title} (P{quest.priority})")
            lines.append("")

        # Open Quests
        open_quests = [q for q in self.board.board.quests.values() if q.state == QuestState.OPEN]
        if open_quests:
            lines.extend(
                [
                    "## 📜 Available Quests",
                    "",
                ]
            )
            for quest in sorted(open_quests, key=lambda q: q.priority, reverse=True):
                priority_emoji = (
                    "🔴" if quest.priority >= 4 else "🟡" if quest.priority >= 3 else "🟢"
                )
                lines.append(f"### {priority_emoji} {quest.title}")
                lines.append(f"- **ID:** `{quest.quest_id}`")
                lines.append(f"- **Priority:** {quest.priority}/5")
                lines.append(f"- **Safety:** {quest.safety_tier}")
                if quest.description:
                    lines.append(f"- **Description:** {quest.description}")
                if quest.tags:
                    lines.append(f"- **Tags:** {', '.join(quest.tags)}")
                if quest.acceptance_criteria:
                    lines.append("- **Acceptance Criteria:**")
                    for criterion in quest.acceptance_criteria:
                        lines.append(f"  - {criterion}")
                lines.append("")

        # Recent Posts
        if self.board.board.recent_posts:
            lines.extend(
                [
                    "## 📝 Recent Posts",
                    "",
                ]
            )
            for post in reversed(self.board.board.recent_posts[-20:]):
                type_emoji = {
                    "progress": "📍",
                    "blockage": "🚧",
                    "discovery": "🔍",
                    "help_wanted": "🆘",
                }.get(post.post_type, "📌")

                lines.append(
                    f"{type_emoji} **{post.agent_id}** ({post.timestamp.split('T')[0]}): {post.message}"
                )
                if post.artifacts:
                    lines.append(f"   *Artifacts:* {', '.join(post.artifacts)}")
            lines.append("")

        # Footer
        lines.extend(
            [
                "---",
                "",
                "*Guild Board - Living coordination substrate for the Adventurer's Party*",
                "",
                "**Board Actions:** `heartbeat` | `claim` | `start` | `post` | `complete`",
            ]
        )

        return "\n".join(lines)

    async def save_markdown(self) -> Path:
        """Save board to stable GUILD_BOARD.md filename."""
        output_file = self.output_dir / "GUILD_BOARD.md"
        content = await self.render_markdown()

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

        return output_file

    async def render_json(self) -> str:
        """Render board as JSON for machine consumption."""
        return json.dumps(
            {
                "timestamp": datetime.now().isoformat(),
                "agents": {
                    aid: {
                        "status": a.status.value,
                        "current_quest": a.current_quest,
                        "capabilities": a.capabilities,
                        "blockers": a.blockers,
                    }
                    for aid, a in self.board.board.agents.items()
                },
                "quests": {
                    qid: {
                        "title": q.title,
                        "state": q.state.value,
                        "claimed_by": q.claimed_by,
                        "priority": q.priority,
                        "safety_tier": q.safety_tier,
                    }
                    for qid, q in self.board.board.quests.items()
                },
                "active_work": self.board.board.active_work,
                "signals": self.board.board.signals,
            },
            indent=2,
            default=str,
        )

    async def save_json(self) -> Path:
        """Save board as JSON."""
        output_file = self.output_dir / "guild_board.json"
        content = await self.render_json()

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

        return output_file

    async def render_html(self) -> str:
        """Render board as HTML for quick viewing."""
        content = await self.render_markdown()
        escaped = html.escape(content)
        return (
            "<!doctype html>"
            '<html><head><meta charset="utf-8">'
            "<title>Guild Board</title>"
            "<style>body{font-family:Segoe UI,Arial,sans-serif;margin:24px;}pre{white-space:pre-wrap;}</style>"
            "</head><body><pre>"
            f"{escaped}"
            "</pre></body></html>"
        )

    async def save_html(self) -> Path:
        """Save board as HTML."""
        output_file = self.output_dir / "guild_board.html"
        content = await self.render_html()
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        return output_file


async def render_and_save(board: GuildBoard, output_dir: Path = Path("docs")) -> None:
    """Render and save guild board in all formats."""
    renderer = GuildBoardRenderer(board, output_dir)
    md_file = await renderer.save_markdown()
    json_file = await renderer.save_json()
    html_file = await renderer.save_html()

    logger.info("✅ Guild Board rendered:")
    logger.info(f"   - Markdown: {md_file}")
    logger.info(f"   - JSON: {json_file}")
    logger.info(f"   - HTML: {html_file}")
