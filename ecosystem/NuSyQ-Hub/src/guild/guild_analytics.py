"""Guild Analytics - Advanced metrics and insights for agent collaboration.

Provides:
- Agent performance tracking
- Quest completion analytics
- Collaboration patterns
- Bottleneck detection
- Predictive task assignment
"""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.guild.guild_board import GuildBoard, QuestState
from src.guild.guild_board import _board as _global_board
from src.guild.guild_board import get_board


@dataclass
class AgentPerformanceMetrics:
    """Performance metrics for an agent."""

    agent_id: str
    quests_claimed: int = 0
    quests_completed: int = 0
    quests_abandoned: int = 0
    average_completion_time: float = 0.0
    success_rate: float = 0.0
    collaboration_count: int = 0
    specialty_tags: list[str] = field(default_factory=list)
    last_active: str | None = None


@dataclass
class QuestAnalytics:
    """Analytics for quest patterns."""

    total_quests: int = 0
    open_quests: int = 0
    active_quests: int = 0
    completed_quests: int = 0
    abandoned_quests: int = 0
    blocked_quests: int = 0
    average_time_to_claim: float = 0.0
    average_completion_time: float = 0.0
    most_common_tags: list[tuple[str, int]] = field(default_factory=list)
    bottleneck_quests: list[str] = field(default_factory=list)


class GuildAnalytics:
    """Advanced analytics for guild board operations."""

    def __init__(self, guild_board: GuildBoard | None = None):
        """Initialize GuildAnalytics with guild_board."""
        # Resolve the GuildBoard instance. `get_board` is async; prefer an
        # existing global instance, otherwise attempt to synchronously create
        # one. If an event loop is already running and no instance exists,
        # require the caller to pass `guild_board` explicitly.
        if guild_board is not None:
            self.board = guild_board
        elif _global_board is not None:
            self.board = _global_board
        else:
            try:
                self.board = asyncio.run(get_board())
            except RuntimeError as exc:  # Raised when a loop is already running
                raise RuntimeError(
                    "Guild board not initialized and an event loop is running; pass guild_board explicitly"
                ) from exc

        self.analytics_dir = Path("state/guild/analytics")
        self.analytics_dir.mkdir(parents=True, exist_ok=True)

    def analyze_agent_performance(self) -> dict[str, AgentPerformanceMetrics]:
        """Analyze performance metrics for all agents."""
        metrics: dict[str, AgentPerformanceMetrics] = {}
        board_state = self.board.board
        events = self._load_events()
        agent_events = self._group_events_by_agent(events)
        for agent_id in board_state.agents:
            metrics[agent_id] = self._compute_agent_metrics(agent_id, agent_events, board_state)
        return metrics

    def _group_events_by_agent(
        self, events: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        agent_events: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for event in events:
            agent_id = event.get("agent_id")
            if agent_id:
                agent_events[agent_id].append(event)
        return agent_events

    def _compute_agent_metrics(
        self, agent_id: str, agent_events: dict[str, list[dict[str, Any]]], board_state
    ) -> AgentPerformanceMetrics:
        agent_metric = AgentPerformanceMetrics(agent_id=agent_id)
        self._count_agent_events(agent_metric, agent_events.get(agent_id, []))
        if agent_metric.quests_claimed > 0:
            agent_metric.success_rate = agent_metric.quests_completed / agent_metric.quests_claimed
        agent_metric.specialty_tags = self._calculate_specialty_tags(
            agent_id, agent_events, board_state
        )
        agent_heartbeat = board_state.agents.get(agent_id)
        if agent_heartbeat:
            agent_metric.last_active = agent_heartbeat.timestamp
        return agent_metric

    def _count_agent_events(
        self, agent_metric: AgentPerformanceMetrics, events: list[dict[str, Any]]
    ) -> None:
        for event in events:
            event_type = event.get("event_type")
            if event_type == "quest_claimed":
                agent_metric.quests_claimed += 1
            elif event_type == "quest_completed":
                agent_metric.quests_completed += 1
            elif event_type == "quest_abandoned":
                agent_metric.quests_abandoned += 1
            elif event_type == "collaboration":
                agent_metric.collaboration_count += 1

    def _calculate_specialty_tags(
        self, agent_id: str, agent_events: dict[str, list[dict[str, Any]]], board_state
    ) -> list[str]:
        specialty_tags: dict[str, int] = defaultdict(int)
        for event in agent_events.get(agent_id, []):
            if event.get("event_type") == "quest_completed":
                quest_id = event.get("quest_id")
                quest = None
                if isinstance(quest_id, str):
                    quest = board_state.quests.get(quest_id)
                if quest:
                    for tag in quest.tags:
                        specialty_tags[tag] += 1
        return [
            tag for tag, _ in sorted(specialty_tags.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

    def analyze_quests(self) -> QuestAnalytics:
        """Analyze quest patterns and metrics."""
        analytics = QuestAnalytics()
        board_state = self.board.board
        analytics.total_quests = len(board_state.quests)
        self._populate_quest_state_counts(analytics, board_state)
        claim_times, completion_times = self._collect_quest_times(board_state)
        if claim_times:
            analytics.average_time_to_claim = sum(claim_times) / len(claim_times)
        if completion_times:
            analytics.average_completion_time = sum(completion_times) / len(completion_times)
        analytics.most_common_tags = self._get_most_common_tags(board_state)
        analytics.bottleneck_quests = self._find_bottleneck_quests(board_state)
        return analytics

    def _populate_quest_state_counts(self, analytics: QuestAnalytics, board_state) -> None:
        for quest in board_state.quests.values():
            if quest.state == QuestState.OPEN:
                analytics.open_quests += 1
            elif quest.state == QuestState.ACTIVE:
                analytics.active_quests += 1
            elif quest.state == QuestState.DONE:
                analytics.completed_quests += 1
            elif quest.state == QuestState.ABANDONED:
                analytics.abandoned_quests += 1
            elif quest.state == QuestState.BLOCKED:
                analytics.blocked_quests += 1

    def _collect_quest_times(self, board_state) -> tuple[list[float], list[float]]:
        completion_times: list[float] = []
        claim_times: list[float] = []
        for quest in board_state.quests.values():
            if quest.claimed_at and quest.created_at:
                created = datetime.fromisoformat(quest.created_at)
                claimed = datetime.fromisoformat(quest.claimed_at)
                claim_times.append((claimed - created).total_seconds())
            if quest.completed_at and quest.started_at:
                started = datetime.fromisoformat(quest.started_at)
                completed = datetime.fromisoformat(quest.completed_at)
                completion_times.append((completed - started).total_seconds())
        return claim_times, completion_times

    def _get_most_common_tags(self, board_state) -> list[tuple[str, int]]:
        tag_counts: dict[str, int] = defaultdict(int)
        for quest in board_state.quests.values():
            for tag in quest.tags:
                tag_counts[tag] += 1
        return sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    def _find_bottleneck_quests(self, board_state) -> list[str]:
        now = datetime.now()
        bottlenecks: list[str] = []
        for quest in board_state.quests.values():
            if quest.state == QuestState.OPEN:
                created = datetime.fromisoformat(quest.created_at)
                if (now - created) > timedelta(hours=24):
                    bottlenecks.append(quest.quest_id)
        return bottlenecks

    def recommend_agent_for_quest(self, quest_id: str) -> list[tuple[str, float]]:
        """Recommend best agents for a quest based on performance and specialty."""
        board_state = self.board.board
        quest = board_state.quests.get(quest_id)
        if not quest:
            return []

        agent_metrics = self.analyze_agent_performance()
        recommendations: list[tuple[str, float]] = []

        for agent_id, metrics in agent_metrics.items():
            score = 0.0
            score += metrics.success_rate * 50

            matching_tags = set(quest.tags) & set(metrics.specialty_tags or [])
            score += len(matching_tags) * 10

            current_quests = sum(
                1
                for q in board_state.quests.values()
                if q.claimed_by == agent_id and q.state == QuestState.ACTIVE
            )
            score -= current_quests * 5

            if metrics.last_active:
                last_active = datetime.fromisoformat(metrics.last_active)
                hours_since_active = (datetime.now() - last_active).total_seconds() / 3600
                if hours_since_active < 24:
                    score += 10

            recommendations.append((agent_id, score))

        return sorted(recommendations, key=lambda x: x[1], reverse=True)

    def detect_collaboration_opportunities(self) -> list[dict[str, Any]]:
        """Identify quests that would benefit from collaboration."""
        board_state = self.board.board
        opportunities: list[dict[str, Any]] = []

        for quest in board_state.quests.values():
            if quest.state not in [QuestState.OPEN, QuestState.BLOCKED]:
                continue

            if quest.priority >= 4:
                recommendations = self.recommend_agent_for_quest(quest.quest_id)
                if len(recommendations) >= 2:
                    opportunities.append(
                        {
                            "quest_id": quest.quest_id,
                            "quest_title": quest.title,
                            "priority": quest.priority,
                            "recommended_agents": [r[0] for r in recommendations[:3]],
                            "confidence": recommendations[0][1] if recommendations else 0,
                        }
                    )

        return sorted(opportunities, key=lambda x: x["priority"], reverse=True)

    def generate_daily_report(self) -> str:
        """Generate a daily analytics report."""
        agent_metrics = self.analyze_agent_performance()
        quest_analytics = self.analyze_quests()
        collaboration_opps = self.detect_collaboration_opportunities()

        report: list[str] = []
        report.append("# Guild Analytics Daily Report")
        report.append(f"\n**Generated:** {datetime.now().isoformat()}\n")

        report.append("## Agent Performance\n")
        for agent_id, metrics in agent_metrics.items():
            report.append(f"### {agent_id}\n")
            report.append(f"- Quests claimed: {metrics.quests_claimed}")
            report.append(f"- Quests completed: {metrics.quests_completed}")
            report.append(f"- Success rate: {metrics.success_rate:.1%}")
            report.append(f"- Specialties: {', '.join(metrics.specialty_tags or [])}")
            report.append("")

        report.append("## Quest Analytics\n")
        report.append(f"- Total quests: {quest_analytics.total_quests}")
        report.append(f"- Open: {quest_analytics.open_quests}")
        report.append(f"- Active: {quest_analytics.active_quests}")
        report.append(f"- Completed: {quest_analytics.completed_quests}")
        report.append(f"- Avg time to claim: {quest_analytics.average_time_to_claim / 3600:.1f}h")
        report.append(
            f"- Avg completion time: {quest_analytics.average_completion_time / 3600:.1f}h"
        )
        report.append("")

        if quest_analytics.most_common_tags:
            report.append("### Most Common Tags\n")
            for tag, count in quest_analytics.most_common_tags:
                report.append(f"- {tag}: {count}")
            report.append("")

        if quest_analytics.bottleneck_quests:
            report.append("### Bottlenecks (>24h open)\n")
            for quest_id in quest_analytics.bottleneck_quests:
                quest = self.board.board.quests.get(quest_id)
                if quest:
                    report.append(f"- {quest.title} ({quest_id})")
            report.append("")

        if collaboration_opps:
            report.append("## Collaboration Opportunities\n")
            for opp in collaboration_opps:
                report.append(f"### {opp['quest_title']}\n")
                report.append(f"- Priority: {opp['priority']}")
                report.append(f"- Recommended agents: {', '.join(opp['recommended_agents'])}")
                report.append("")

        report_text = "\n".join(report)
        report_file = self.analytics_dir / f"daily_report_{datetime.now().strftime('%Y%m%d')}.md"
        report_file.write_text(report_text, encoding="utf-8")
        return report_text

    def _load_events(self) -> list[dict[str, Any]]:
        """Load guild board events from JSONL log."""
        events: list[dict[str, Any]] = []
        events_file = self.board.events_file

        if events_file.exists():
            with open(events_file, encoding="utf-8") as f:
                for line in f:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        return events

    def export_metrics(self) -> dict[str, Any]:
        """Export all metrics as JSON."""
        agent_metrics = self.analyze_agent_performance()
        quest_analytics = self.analyze_quests()

        return {
            "timestamp": datetime.now().isoformat(),
            "agents": {agent_id: asdict(metrics) for agent_id, metrics in agent_metrics.items()},
            "quests": asdict(quest_analytics),
            "recommendations": {
                quest_id: self.recommend_agent_for_quest(quest_id)
                for quest_id in list(self.board.board.quests.keys())[:10]
            },
        }
