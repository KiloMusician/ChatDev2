"""Living Guild Board - Coordination substrate for the Adventurer's Guild.

The Guild Board is the canonical state for multi-agent coordination:
- Agents heartbeat to show presence & current work
- Agents claim quests/work items to prevent collision
- Agents post progress notes + receipts
- The board becomes the shared truth + triage queue

Substrates:
1. guild_board.json - Current canonical state (rewritten each update)
2. guild_events.jsonl - Append-only event log (full history)
3. agent_registry.json - Agent capabilities & progression (existing)
4. quest_assignments.json - Current assignments (existing)
5. unified_pu_queue.json - Task backlog (existing)
"""

import asyncio
import contextlib
import json
import logging
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from src.config.orchestration_config_loader import (
    get_guild_automation_config, get_guild_heartbeat_config,
    get_guild_quest_config, get_guild_state_config)

# Type aliases for clarity in guild system APIs
# QuestId: UUID string identifying a quest (e.g., "a1b2c3d4-e5f6-...")
# AgentId: String identifier for an agent (e.g., "claude", "ollama", "copilot")
QuestId = str
AgentId = str

# Keeps strong references to fire-and-forget listener coroutine futures so CPython
# GC cannot cancel them before completion.  Done-callback removes each entry.
_listener_tasks: set[asyncio.Future[Any]] = set()

logger_factory: Callable[[str], logging.Logger] | None
try:
    from src.LOGGING.modular_logging_system import \
        get_logger as _logger_factory

    logger_factory = _logger_factory
except Exception:
    logger_factory = None
logger = logger_factory(__name__) if logger_factory is not None else logging.getLogger(__name__)


class AgentStatus(Enum):
    """Current status of an agent."""

    IDLE = "idle"
    WORKING = "working"
    BLOCKED = "blocked"
    OBSERVING = "observing"
    OFFLINE = "offline"


class QuestState(Enum):
    """Quest lifecycle states."""

    OPEN = "open"  # Available to claim
    CLAIMED = "claimed"  # Agent claimed but not started
    ACTIVE = "active"  # Agent actively working
    DONE = "done"  # Successfully completed
    ABANDONED = "abandoned"  # Agent gave up
    BLOCKED = "blocked"  # Waiting on dependency


@dataclass
class AgentHeartbeat:
    """Agent status message posted to board."""

    agent_id: str
    status: AgentStatus
    current_quest: str | None = None
    capabilities: list[str] = field(default_factory=list)
    confidence_level: float = 1.0  # 0-1, how confident agent is
    blockers: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    consciousness_score: float | None = None  # Back-compat for older board data


@dataclass
class QuestEntry:
    """Quest definition on the board."""

    quest_id: str
    title: str
    description: str
    priority: int  # 1-5, higher = more urgent
    safety_tier: str  # "safe", "standard", "risky", "experimental"
    state: QuestState = QuestState.OPEN
    claimed_by: str | None = None
    claimed_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    closed_at: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    acceptance_criteria: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)  # Other quest IDs
    tags: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)  # Output paths


@dataclass
class BoardPost:
    """Agent post on the guild board (progress note)."""

    post_id: str
    agent_id: str
    quest_id: str | None = None
    message: str = ""
    post_type: str = "progress"  # progress, blockage, discovery, help_wanted
    artifacts: list[str] = field(default_factory=list)  # Links to receipts
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class GuildBoardState:
    """Complete guild board state snapshot."""

    timestamp: str
    agents: dict[str, AgentHeartbeat]
    quests: dict[str, QuestEntry]
    active_work: dict[str, str]  # quest_id -> agent_id currently working
    recent_posts: list[BoardPost]
    signals: list[dict[str, Any]]  # Errors, alerts, drifts
    version: int = 1


class GuildBoard:
    """Manages the living guild board state and events."""

    def __init__(
        self,
        state_dir: Path = Path("state/guild"),
        data_dir: Path = Path("data"),
    ):
        """Initialize GuildBoard with state_dir and data_dir."""
        self.root = Path(__file__).resolve().parents[2]
        self.state_dir = state_dir
        self.data_dir = data_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.board_file = self.state_dir / "guild_board.json"
        self.events_file = self.state_dir / "guild_events.jsonl"

        # Load configuration from orchestration_defaults.json
        heartbeat_config = get_guild_heartbeat_config()
        quest_config = get_guild_quest_config()
        state_config = get_guild_state_config()
        automation_config = get_guild_automation_config()

        # Configure heartbeat behavior
        self.heartbeat_required = bool(
            heartbeat_config.get("heartbeat_required_before_claim", True)
        )
        self.heartbeat_interval_seconds = int(
            heartbeat_config.get("heartbeat_interval_seconds", 300) or 300
        )
        self.default_agent_status = str(heartbeat_config.get("default_new_agent_status", "idle"))
        self.heartbeat_timeout_minutes = int(
            heartbeat_config.get("auto_release_timeout_minutes", 10) or 10
        )
        self.auto_release_claim_on_heartbeat_timeout = bool(
            heartbeat_config.get("auto_release_claim_on_heartbeat_timeout", True)
        )
        inactive_claim_seconds = heartbeat_config.get("inactive_claim_timeout_seconds", 0)
        try:
            self.claim_timeout_minutes = max(0.0, float(inactive_claim_seconds) / 60.0)
        except (TypeError, ValueError):
            self.claim_timeout_minutes = 0.0

        # Configure quest management
        self.quest_id_format = quest_config.get(
            "quest_id_format", "quest_{YYYYMMDD}_{HHMMSS}_{slug}"
        )
        self.allow_multi_agent_claim = bool(quest_config.get("allow_multi_agent_claim", False))
        self.party_concept_enabled = bool(quest_config.get("party_concept_enabled", True))
        self.sprint_field_enabled = bool(quest_config.get("sprint_field_enabled", False))

        # Configure board state behavior
        self.auto_archive_days = int(
            state_config.get("auto_archive_completed_after_days", 14) or 14
        )
        self.long_running_alert_hours = int(
            state_config.get("long_running_quest_alert_hours", 24) or 24
        )
        self.mirror_to_simulatedverse = bool(state_config.get("mirror_to_simulatedverse", False))
        self.recent_posts_limit = int(state_config.get("recent_posts_window_size", 50) or 50)

        # Configure automation behavior
        # Note: auto_heartbeat_agents lives in heartbeat_config (where it semantically belongs)
        self.auto_heartbeat_agents = list(heartbeat_config.get("auto_heartbeat_agents", []))
        self.post_throttle_per_minute = int(
            automation_config.get("post_throttle_max_per_minute", 5) or 5
        )

        self.board: GuildBoardState = GuildBoardState(
            timestamp=datetime.now().isoformat(),
            agents={},
            quests={},
            active_work={},
            recent_posts=[],
            signals=[],
        )

        self._lock = asyncio.Lock()
        # Event listeners: callables invoked after every _emit_event write.
        # Signature: async fn(event_type: str, data: dict) -> None
        # Errors in listeners are swallowed so board ops are never blocked.
        self._event_listeners: list[Callable] = []
        self._load_board()

    def _serialize_board(self) -> dict[str, Any]:
        """Serialize board state to JSON-safe structure."""
        return {
            "timestamp": datetime.now().isoformat(),
            "version": self.board.version,
            "agents": {
                aid: {
                    **asdict(a),
                    "status": a.status.value,
                }
                for aid, a in self.board.agents.items()
            },
            "quests": {
                qid: {
                    **asdict(q),
                    "state": q.state.value,
                }
                for qid, q in self.board.quests.items()
            },
            "active_work": self.board.active_work,
            "recent_posts": [asdict(p) for p in self.board.recent_posts],
            "signals": self.board.signals,
        }

    def _write_json_atomic(self, target: Path, payload: dict[str, Any]) -> None:
        """Write JSON atomically to avoid truncated/corrupt state files."""
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_suffix(target.suffix + ".tmp")
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
            f.flush()
        temp.replace(target)

    def post_message(self, agent_name: str, message: str) -> None:
        """Simple synchronous message posting for testing/diagnostics."""
        from uuid import uuid4

        post = BoardPost(
            post_id=f"post_{uuid4().hex[:8]}",
            agent_id=agent_name,
            message=message,
            post_type="diagnostic",
        )
        self.board.recent_posts.append(post)
        # Keep only last 10 posts
        self.board.recent_posts = self.board.recent_posts[-10:]
        # Sync save with shared serializer + atomic write.
        with contextlib.suppress(Exception):  # Silent fail for diagnostic method
            self._write_json_atomic(self.board_file, self._serialize_board())

    def _parse_timestamp(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def _heartbeat_is_recent(self, agent_id: str, max_age_minutes: int) -> bool:
        if max_age_minutes <= 0:
            return True
        heartbeat = self.board.agents.get(agent_id)
        if not heartbeat:
            return False
        ts = self._parse_timestamp(heartbeat.timestamp)
        if not ts:
            return False
        return (datetime.now() - ts) <= timedelta(minutes=max_age_minutes)

    def _is_post_throttled(self, agent_id: str, now: datetime) -> bool:
        if self.post_throttle_per_minute <= 0:
            return False
        window_start = now - timedelta(seconds=60)
        recent = [
            post
            for post in self.board.recent_posts
            if post.agent_id == agent_id
            and (self._parse_timestamp(post.timestamp) or now) >= window_start
        ]
        return len(recent) >= self.post_throttle_per_minute

    def _slugify(self, text: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower())
        return cleaned.strip("-") or "quest"

    async def _release_stale_claims_locked(self, now: datetime) -> None:
        stale: list[tuple[str, str]] = []
        for quest_id, quest in self.board.quests.items():
            if quest.state not in {QuestState.CLAIMED, QuestState.ACTIVE}:
                continue
            if not quest.claimed_by:
                continue
            claimed_at = self._parse_timestamp(quest.claimed_at)
            if (
                quest.state == QuestState.CLAIMED
                and self.claim_timeout_minutes > 0
                and claimed_at
                and now - claimed_at >= timedelta(minutes=self.claim_timeout_minutes)
            ):
                stale.append((quest_id, "claim_timeout"))
                continue
            if (
                self.auto_release_claim_on_heartbeat_timeout
                and self.heartbeat_timeout_minutes > 0
                and not self._heartbeat_is_recent(quest.claimed_by, self.heartbeat_timeout_minutes)
            ):
                stale.append((quest_id, "heartbeat_timeout"))

        for quest_id, reason in stale:
            quest = self.board.quests[quest_id]
            quest.claimed_by = None
            quest.state = QuestState.OPEN
            quest.claimed_at = None
            quest.started_at = None
            if quest_id in self.board.active_work:
                del self.board.active_work[quest_id]
            await self._emit_event(
                "quest_released",
                {"quest_id": quest_id, "reason": reason},
            )

    async def _archive_completed_quests_locked(self, now: datetime) -> None:
        if self.auto_archive_days <= 0:
            return
        cutoff = now - timedelta(days=self.auto_archive_days)
        archive_ids = []
        for quest_id, quest in self.board.quests.items():
            if quest.state != QuestState.DONE:
                continue
            completed_at = self._parse_timestamp(quest.completed_at)
            if completed_at and completed_at < cutoff:
                archive_ids.append(quest_id)

        for quest_id in archive_ids:
            try:
                quest = self.board.quests.pop(quest_id)
            except KeyError:
                continue
            await self._emit_event(
                "quest_archived",
                {"quest_id": quest_id, "completed_at": quest.completed_at},
            )

    def _load_board(self) -> None:
        """Load existing board state from disk."""
        if self.board_file.exists():
            try:
                with open(self.board_file, encoding="utf-8") as f:
                    data = json.load(f)
                # Reconstruct board from JSON
                agents = {}
                for aid, agent_data in data.get("agents", {}).items():
                    status_value = agent_data.get("status", AgentStatus.IDLE.value)
                    try:
                        status_enum = AgentStatus(status_value)
                    except ValueError:
                        status_enum = AgentStatus.IDLE
                    allowed_agent_fields = {f.name for f in fields(AgentHeartbeat)}
                    # Filter out legacy/unknown keys to avoid constructor errors
                    filtered = {k: v for k, v in agent_data.items() if k in allowed_agent_fields}
                    filtered["status"] = status_enum
                    agents[aid] = AgentHeartbeat(**filtered)

                quests = {}
                for qid, quest_data in data.get("quests", {}).items():
                    state_value = quest_data.get("state", QuestState.OPEN.value)
                    try:
                        state_enum = QuestState(state_value)
                    except ValueError:
                        state_enum = QuestState.OPEN
                    quest_data = {**quest_data, "state": state_enum}
                    quests[qid] = QuestEntry(**quest_data)

                self.board = GuildBoardState(
                    timestamp=data.get("timestamp", datetime.now().isoformat()),
                    agents=agents,
                    quests=quests,
                    active_work=data.get("active_work", {}),
                    recent_posts=[BoardPost(**p) for p in data.get("recent_posts", [])],
                    signals=data.get("signals", []),
                )
                logger.info(
                    "📜 Guild board loaded: %d agents, %d quests",
                    len(self.board.agents),
                    len(self.board.quests),
                )
            except Exception as e:
                logger.warning("Failed to load board: %s, starting fresh", e)
                try:
                    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    corrupt = self.board_file.with_suffix(f".corrupt.{stamp}.json")
                    self.board_file.replace(corrupt)
                    logger.warning("Corrupt guild board moved to %s", corrupt)
                except Exception:
                    logger.debug("Suppressed Exception", exc_info=True)

    async def agent_heartbeat(
        self,
        agent_id: str,
        status: AgentStatus,
        current_quest: str | None = None,
        capabilities: list[str] | None = None,
        blockers: list[str] | None = None,
    ) -> AgentHeartbeat:
        """Agent posts heartbeat showing presence + current work."""
        async with self._lock:
            now = datetime.now()
            heartbeat = AgentHeartbeat(
                agent_id=agent_id,
                status=status,
                current_quest=current_quest,
                capabilities=capabilities or [],
                blockers=blockers or [],
            )
            self.board.agents[agent_id] = heartbeat

            # Convert to dict with enum serialization
            heartbeat_dict = asdict(heartbeat)
            heartbeat_dict["status"] = status.value  # Convert enum to string

            await self._release_stale_claims_locked(now)
            await self._archive_completed_quests_locked(now)
            await self._emit_event("agent_heartbeat", heartbeat_dict)
            await self._save_board()

        logger.info("💓 %s heartbeat: %s", agent_id, status.value)
        return heartbeat

    async def claim_quest(self, quest_id: str, agent_id: str) -> tuple[bool, str | None]:
        """Agent claims a quest (atomically prevents double-claim)."""
        async with self._lock:
            now = datetime.now()
            await self._release_stale_claims_locked(now)
            if self.heartbeat_required:
                freshness = self.heartbeat_timeout_minutes or 60
                if not self._heartbeat_is_recent(agent_id, freshness):
                    return False, "Heartbeat required before claim"
            if quest_id not in self.board.quests:
                return False, "Quest not found"

            quest = self.board.quests[quest_id]
            if quest.state not in [QuestState.OPEN, QuestState.BLOCKED]:
                return False, f"Quest is {quest.state.value}, cannot claim"

            if quest.claimed_by and quest.claimed_by != agent_id:
                return False, f"Already claimed by {quest.claimed_by}"

            # Claim successful
            quest.claimed_by = agent_id
            quest.claimed_at = now.isoformat()
            quest.state = QuestState.CLAIMED
            self.board.active_work[quest_id] = agent_id

            await self._emit_event(
                "quest_claimed",
                {"quest_id": quest_id, "agent_id": agent_id},
            )
            await self._save_board()

        logger.info("✋ %s claimed quest: %s", agent_id, quest_id)
        return True, "Quest claimed"

    async def start_quest(self, quest_id: str, agent_id: str) -> tuple[bool, str | None]:
        """Agent starts working on claimed quest."""
        async with self._lock:
            if quest_id not in self.board.quests:
                return False, "Quest not found"

            quest = self.board.quests[quest_id]
            if quest.claimed_by != agent_id:
                return False, f"Not claimed by {agent_id}"

            quest.state = QuestState.ACTIVE
            quest.started_at = datetime.now().isoformat()
            await self._emit_event(
                "quest_started",
                {"quest_id": quest_id, "agent_id": agent_id},
            )
            await self._save_board()

        return True, "Quest started"

    async def post_on_board(
        self,
        agent_id: str,
        message: str,
        quest_id: str | None = None,
        post_type: str = "progress",
        artifacts: list[str] | None = None,
    ) -> BoardPost:
        """Agent posts progress note or alert."""
        async with self._lock:
            now = datetime.now()
            if self._is_post_throttled(agent_id, now):
                logger.info("Post throttled for %s", agent_id)
                return BoardPost(
                    post_id=f"{agent_id}_{now.timestamp()}",
                    agent_id=agent_id,
                    quest_id=quest_id,
                    message="Post throttled: slow down to avoid flooding.",
                    post_type="throttled",
                    artifacts=artifacts or [],
                    timestamp=now.isoformat(),
                )
            post = BoardPost(
                post_id=f"{agent_id}_{now.timestamp()}",
                agent_id=agent_id,
                quest_id=quest_id,
                message=message,
                post_type=post_type,
                artifacts=artifacts or [],
            )
            self.board.recent_posts.append(post)
            # Keep only recent N
            self.board.recent_posts = self.board.recent_posts[-self.recent_posts_limit :]

            await self._emit_event("board_post", asdict(post))
            await self._save_board()

        logger.info("📝 %s posted: %s", agent_id, message[:50])
        return post

    async def complete_quest(
        self, quest_id: str, agent_id: str, artifacts: list[str] | None = None
    ) -> tuple[bool, str | None]:
        """Agent marks quest complete."""
        async with self._lock:
            if quest_id not in self.board.quests:
                return False, "Quest not found"

            quest = self.board.quests[quest_id]
            if quest.claimed_by != agent_id:
                return False, "Not claimed by this agent"

            quest.state = QuestState.DONE
            quest.completed_at = datetime.now().isoformat()
            if artifacts:
                quest.artifacts.extend(artifacts)

            if quest_id in self.board.active_work:
                del self.board.active_work[quest_id]

            await self._emit_event(
                "quest_completed",
                {"quest_id": quest_id, "agent_id": agent_id, "artifacts": artifacts},
            )
            await self._archive_completed_quests_locked(datetime.now())
            await self._save_board()

        logger.info("✅ %s completed quest: %s", agent_id, quest_id)

        try:
            from src.system.agent_awareness import emit as _emit

            _emit(
                "agents",
                f"Guild quest done: {quest_id[:40]} by={agent_id} artifacts={len(artifacts or [])}",
                level="INFO",
                source="guild_board",
            )
        except Exception:
            pass

        return True, "Quest completed"

    async def add_quest(
        self,
        quest_id: str | None,
        title: str,
        description: str,
        priority: int = 3,
        safety_tier: str = "safe",
        tags: list[str] | None = None,
        dependencies: list[str] | None = None,
        acceptance_criteria: list[str] | None = None,
    ) -> tuple[bool, str]:
        """Add a new quest to the board."""
        async with self._lock:
            if not quest_id:
                now = datetime.now()
                token_map = {
                    "timestamp": int(now.timestamp()),
                    "slug": self._slugify(title),
                }
                try:
                    quest_id = self.quest_id_format.format(**token_map)
                except KeyError:
                    quest_id = f"quest_{token_map['timestamp']}"
            assert quest_id is not None
            # If quest_id collides, try to generate a unique one by appending a suffix
            if quest_id in self.board.quests:
                base = quest_id
                suffix = 1
                while quest_id in self.board.quests:
                    quest_id = f"{base}_{suffix}"
                    suffix += 1

            quest = QuestEntry(
                quest_id=quest_id,
                title=title,
                description=description,
                priority=max(1, min(priority, 5)),
                safety_tier=safety_tier,
                tags=tags or [],
                dependencies=dependencies or [],
                acceptance_criteria=acceptance_criteria or [],
            )
            self.board.quests[quest_id] = quest

            await self._emit_event(
                "quest_added",
                {
                    "quest_id": quest_id,
                    "title": title,
                    "priority": quest.priority,
                    "safety_tier": safety_tier,
                },
            )
            await self._save_board()

        logger.info("+ Quest added: %s", quest_id)
        return True, quest_id

    async def close_quest(
        self,
        quest_id: str,
        agent_id: str | None = None,
        status: QuestState = QuestState.DONE,
        artifacts: list[str] | None = None,
        reason: str | None = None,
    ) -> tuple[bool, str | None]:
        """Close a quest as done/abandoned/blocked."""
        async with self._lock:
            if quest_id not in self.board.quests:
                return False, "Quest not found"

            quest = self.board.quests[quest_id]
            quest.state = status
            quest.closed_at = datetime.now().isoformat()
            if artifacts:
                quest.artifacts.extend(artifacts)

            if quest_id in self.board.active_work:
                del self.board.active_work[quest_id]

            await self._emit_event(
                "quest_closed",
                {
                    "quest_id": quest_id,
                    "agent_id": agent_id,
                    "status": status.value,
                    "reason": reason,
                },
            )
            await self._save_board()

        logger.info("🔒 Quest closed: %s (%s)", quest_id, status.value)
        return True, status.value

    async def add_signal(
        self, signal_type: str, severity: str, message: str, context: dict | None = None
    ) -> None:
        """Post a system signal (error, alert, drift detection)."""
        async with self._lock:
            signal = {
                "type": signal_type,
                "severity": severity,
                "message": message,
                "context": context or {},
                "timestamp": datetime.now().isoformat(),
            }
            self.board.signals.append(signal)
            # Keep only recent 50
            self.board.signals = self.board.signals[-50:]

            await self._emit_event("signal", signal)
            await self._save_board()

    async def get_available_quests(self, agent_capabilities: list[str]) -> list[QuestEntry]:
        """Get quests that match agent's capabilities and are not claimed."""
        async with self._lock:
            available = [
                q
                for q in self.board.quests.values()
                if q.state == QuestState.OPEN
                and (not q.tags or any(tag in agent_capabilities for tag in q.tags))
            ]
            return sorted(available, key=lambda q: q.priority, reverse=True)

    async def get_board_summary(self) -> dict[str, Any]:
        """Get high-level board summary for display."""
        async with self._lock:
            return {
                "timestamp": self.board.timestamp,
                "agents_online": sum(
                    1 for a in self.board.agents.values() if a.status != AgentStatus.OFFLINE
                ),
                "quests_open": sum(
                    1 for q in self.board.quests.values() if q.state == QuestState.OPEN
                ),
                "quests_active": sum(
                    1 for q in self.board.quests.values() if q.state == QuestState.ACTIVE
                ),
                "quests_blocked": sum(
                    1 for q in self.board.quests.values() if q.state == QuestState.BLOCKED
                ),
                "critical_signals": [s for s in self.board.signals if s["severity"] == "critical"],
                "recent_posts": [asdict(p) for p in self.board.recent_posts[-10:]],
            }

    async def _save_board(self) -> None:
        """Persist board state to JSON."""
        self._write_json_atomic(self.board_file, self._serialize_board())

    # ── Event listener registry ──────────────────────────────────────────────

    def register_event_listener(self, callback: Callable) -> None:
        """Register a callback invoked after every guild event is emitted.

        The callback signature must be::

            async def on_guild_event(event_type: str, data: dict) -> None

        Listeners are fire-and-forget; any exception is logged and swallowed
        so board operations are never blocked or broken by a bad listener.

        Args:
            callback: Async callable matching the signature above.
        """
        if callback not in self._event_listeners:
            self._event_listeners.append(callback)
            logger.debug(
                "Guild event listener registered: %s", getattr(callback, "__qualname__", callback)
            )

    def unregister_event_listener(self, callback: Callable) -> None:
        """Remove a previously registered event listener.

        Args:
            callback: The exact callable that was registered.
        """
        try:
            self._event_listeners.remove(callback)
            logger.debug(
                "Guild event listener removed: %s", getattr(callback, "__qualname__", callback)
            )
        except ValueError:
            pass  # Already removed — idempotent

    async def save_state(self) -> None:
        """Compatibility wrapper for callers expecting a public save method."""
        await self._save_board()

    async def _emit_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Append event to append-only log, DuckDB, and registered listeners."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data,
        }
        # Write to JSONL
        with open(self.events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

        # Dual-write to DuckDB for realtime queries
        try:
            from src.duckdb_integration.dual_write import insert_single_event

            db_path = Path("data/state.duckdb")
            insert_single_event(
                db_path, {"timestamp": event["timestamp"], "event": event_type, "details": data}
            )
        except Exception as e:
            logger.warning(f"Failed to write event to DuckDB: {e}")

        # Notify registered listeners (fire-and-forget; never blocks board ops)
        for listener in list(self._event_listeners):
            try:
                result = listener(event_type, data)
                if asyncio.iscoroutine(result):
                    fut = asyncio.ensure_future(result)
                    _listener_tasks.add(fut)
                    fut.add_done_callback(_listener_tasks.discard)
            except Exception as exc:
                logger.debug("Guild event listener error (suppressed): %s", exc)


# Singleton instance
_board: GuildBoard | None = None
_openclaw_attached: bool = False
_terminal_attached: bool = False


async def get_board() -> GuildBoard:
    """Get or create the singleton guild board.

    On first call also auto-attaches the OpenClaw notifier (guild→messaging platforms)
    and the terminal notifier (guild→VS Code terminal logs) — both best-effort.
    """
    global _board, _openclaw_attached, _terminal_attached
    if _board is None:
        _board = GuildBoard()
    if not _openclaw_attached:
        try:
            from src.guild.guild_openclaw_notifier import \
                attach_to_board  # lazy to avoid circular

            attach_to_board(_board)
            _openclaw_attached = True
        except Exception as exc:  # gateway offline or import unavailable — non-fatal
            logger.debug("Guild→OpenClaw auto-attach skipped: %s", exc)
    if not _terminal_attached:
        try:
            from src.guild.guild_terminal_notifier import \
                attach_to_board as _attach_terminals

            _attach_terminals(_board)
            _terminal_attached = True
        except Exception as exc:  # terminal system unavailable — non-fatal
            logger.debug("Guild→Terminal auto-attach skipped: %s", exc)
    return _board


async def init_board() -> GuildBoard:
    """Initialize the guild board."""
    board = await get_board()
    return board
