"""Rosetta Quest System — Interactive AI "Quest" Engine.

Φ.3.0 — Task-Driven Recursive Development Platform.

- Each task = a quest (with status, metadata, dependencies)
- Each module = a questline (group of related quests)
- Tracks development state in JSON (and optionally CSV)
- CLI and API for quest/questline management
- Integrates with Copilot/context for suggestions and automation
- Designed for AI + User joint planning, long-term projects
- Full logging, tagging, and context propagation

OmniTag: [quest, task, recursive, planning, context, copilot]
MegaTag: [QUEST_ENGINE, RECURSIVE_DEVELOPMENT, CONTEXT_INTEGRATION]
"""

import csv
import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:  # Python 3.11+
    from datetime import UTC  # type: ignore[attr-defined]
except ImportError:
    from datetime import timezone  # Python 3.10

    UTC = timezone.utc  # noqa: UP017

# Try to import ConsciousnessBridge
ConsciousnessBridge: Any | None = None
try:
    from src.integration.consciousness_bridge import \
        ConsciousnessBridge as ImportedConsciousnessBridge

    ConsciousnessBridge = ImportedConsciousnessBridge
    CONSCIOUSNESS_BRIDGE_AVAILABLE = True
except ImportError:
    CONSCIOUSNESS_BRIDGE_AVAILABLE = False

QUESTS_FILE = Path("src/Rosetta_Quest_System/quests.json")
QUESTLINES_FILE = Path("src/Rosetta_Quest_System/questlines.json")
LOG_FILE = Path("src/Rosetta_Quest_System/quest_log.jsonl")
QUESTS_CSV_FILE = "src/Rosetta_Quest_System/quests.csv"


# --- Data Models ---
class Quest:
    def __init__(
        self,
        title: str,
        description: str,
        questline: str,
        dependencies: list[str] | None = None,
        tags: list[str] | None = None,
        priority: str | int | None = None,
        min_consciousness_level: int = 0,
    ) -> None:
        """Initialize Quest with title, description, questline, ...."""
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.questline = questline
        self.status = "pending"  # pending, active, complete, blocked, archived
        self.created_at = datetime.now(UTC).isoformat()
        self.updated_at = self.created_at
        self.dependencies = dependencies or []
        self.tags = tags or []
        self.history: list[dict[str, Any]] = []
        self.priority = priority
        self.min_consciousness_level = min_consciousness_level  # 0 = no gate

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Quest":
        # Be tolerant of missing keys when loading historical or auto-generated logs.
        title = d.get("title", "(untitled)")
        description = d.get("description", "")
        questline = d.get("questline", "General")
        dependencies = d.get("dependencies") or []
        tags = d.get("tags") or []
        priority = d.get("priority")

        min_level = int(d.get("min_consciousness_level", 0))
        q = Quest(
            title,
            description,
            questline,
            dependencies,
            tags,
            priority,
            min_consciousness_level=min_level,
        )
        q.id = d.get("id", q.id)
        q.status = d.get("status", "pending")
        q.created_at = d.get("created_at", q.created_at)
        q.updated_at = d.get("updated_at", q.created_at)
        q.history = d.get("history", [])
        return q


class Questline:
    def __init__(self, name: str, description: str, tags: list[str] | None = None) -> None:
        """Initialize Questline with name, description, tags."""
        self.name = name
        self.description = description
        self.tags = tags or []
        self.quests: list[str] = []
        self.created_at = datetime.now(UTC).isoformat()
        self.updated_at = self.created_at

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Questline":
        ql = Questline(d["name"], d["description"], d.get("tags"))
        ql.quests = d.get("quests", [])
        ql.created_at = d["created_at"]
        ql.updated_at = d["updated_at"]
        return ql


# --- Persistence ---
def load_quests() -> dict[str, Quest]:
    if QUESTS_FILE.exists():
        with QUESTS_FILE.open(encoding="utf-8") as f:
            data = json.load(f)
            return {q["id"]: Quest.from_dict(q) for q in data}
    return {}


def save_quests(quests: dict[str, Quest]) -> None:
    QUESTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with QUESTS_FILE.open("w", encoding="utf-8") as f:
        json.dump([q.to_dict() for q in quests.values()], f, indent=2)


def load_questlines() -> dict[str, Questline]:
    if QUESTLINES_FILE.exists():
        with QUESTLINES_FILE.open(encoding="utf-8") as f:
            data = json.load(f)
            return {ql["name"]: Questline.from_dict(ql) for ql in data}
    return {}


def save_questlines(questlines: dict[str, Questline]) -> None:
    QUESTLINES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with QUESTLINES_FILE.open("w", encoding="utf-8") as f:
        json.dump([ql.to_dict() for ql in questlines.values()], f, indent=2)


def log_event(event: str, details: dict) -> None:
    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event": event,
        "details": details,
    }
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def log_three_before_new(
    tool_name: str,
    capability: str,
    candidates: list[dict[str, str]] | list[str],
    justification: str,
) -> None:
    """Record compliance with the Three Before New rule.

    - Requires at least three candidates evaluated.
    - Accepts candidates as list of dicts (with path/notes) or list of paths.
    """
    if len(candidates) < 3:
        raise ValueError("Three Before New requires at least three candidates")

    normalized: list[dict[str, str]] = []
    for entry in candidates:
        if isinstance(entry, dict):
            normalized.append({"path": entry.get("path", ""), "notes": entry.get("notes", "")})
        else:
            normalized.append({"path": str(entry), "notes": ""})

    log_event(
        "three_before_new",
        {
            "tool_name": tool_name,
            "capability": capability,
            "candidates": normalized,
            "justification": justification,
        },
    )


# --- Quest Engine Core ---
class QuestEngine:
    def __init__(self) -> None:
        """Initialize QuestEngine."""
        self.quests = load_quests()
        self.questlines = load_questlines()
        # Ensure a default questline exists for convenience APIs
        if "General" not in self.questlines:
            self.add_questline("General", "Autogenerated default questline")

    def get_quest(self, quest_id: str) -> Any | None:
        """Get a quest by ID."""
        return self.quests.get(quest_id)

    def add_questline(self, name, description, tags=None) -> None:
        if name in self.questlines:
            return
        ql = Questline(name, description, tags)
        self.questlines[name] = ql
        save_questlines(self.questlines)
        log_event("add_questline", ql.to_dict())

    def add_quest(
        self,
        title,
        description,
        questline: str = "General",
        dependencies=None,
        tags=None,
        priority=None,
        min_level: int = 0,
    ) -> str | None:
        if questline not in self.questlines:
            self.add_questline(questline, "Autogenerated questline")
        quest = Quest(
            title,
            description,
            questline,
            dependencies,
            tags,
            priority,
            min_consciousness_level=min_level,
        )
        self.quests[quest.id] = quest
        self.questlines[questline].quests.append(quest.id)
        save_quests(self.quests)
        save_questlines(self.questlines)
        log_event("add_quest", quest.to_dict())
        try:
            from src.system.agent_awareness import emit as _emit

            _emit(
                "agents",
                f"Quest added: {title[:60]} questline={questline} id={quest.id[:8]}",
                level="INFO",
                source="quest_engine",
            )
        except Exception:
            pass
        return quest.id

    def update_quest_status(self, quest_id, status) -> None:
        if quest_id not in self.quests:
            return
        from src.utils.status_helpers import normalize_status

        quest = self.quests[quest_id]
        normalized = normalize_status(status)
        quest.status = normalized
        quest.updated_at = datetime.now(UTC).isoformat()
        quest.history.append({"status": normalized, "timestamp": quest.updated_at})
        save_quests(self.quests)
        log_event("update_quest_status", quest.to_dict())
        try:
            from src.system.agent_awareness import emit as _emit

            _lvl = "INFO" if normalized in ("completed", "active") else "WARNING"
            _emit(
                "agents",
                f"Quest status: {quest_id[:40]} → {normalized}",
                level=_lvl,
                source="quest_engine",
            )
        except Exception:
            pass

    # Convenience alias used by integration tests
    def complete_quest(self, quest_id) -> None:
        self.update_quest_status(quest_id, "completed")

    def list_quests(self, questline=None, status=None) -> None:
        """List quests with detailed breakdown.

        Shows status, questline, dependencies, tags, timestamps, and description.
        """
        quests = list(self.quests.values())
        if questline:
            quests = [q for q in quests if q.questline == questline]
        if status:
            quests = [q for q in quests if q.status == status]
        if not quests:
            return
        for q in quests:
            if q.history:
                for _h in q.history:
                    pass

    def get_accessible_quests(
        self,
        consciousness_level: int = 0,
        questline: str | None = None,
        status: str | None = None,
    ) -> list[Any]:
        """Return quests accessible at the given consciousness level.

        Args:
            consciousness_level: Current player/agent consciousness level (0 = no gate).
            questline: Optional questline filter.
            status: Optional status filter (pending, active, complete, etc.).

        Returns:
            List of Quest objects where min_consciousness_level <= consciousness_level.
        """
        quests = list(self.quests.values())
        quests = [
            q for q in quests if getattr(q, "min_consciousness_level", 0) <= consciousness_level
        ]
        if questline:
            quests = [q for q in quests if q.questline == questline]
        if status:
            quests = [q for q in quests if q.status == status]
        return quests

    def list_questlines(self) -> None:
        for _ql in self.questlines.values():
            pass

    def quest_details(self, quest_id) -> None:
        if quest_id not in self.quests:
            return
        self.quests[quest_id]

    def questline_details(self, name) -> None:
        if name not in self.questlines:
            return
        self.questlines[name]

    def export_csv(self, path=QUESTS_CSV_FILE) -> None:
        csv_path = Path(path) if isinstance(path, str) else path
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "id",
                    "title",
                    "description",
                    "questline",
                    "status",
                    "created_at",
                    "updated_at",
                    "dependencies",
                    "tags",
                ],
            )
            writer.writeheader()
            for q in self.quests.values():
                row = q.to_dict().copy()
                row["dependencies"] = ",".join(row["dependencies"])
                row["tags"] = ",".join(row["tags"])
                writer.writerow(row)

    def import_csv(self, path=QUESTS_CSV_FILE) -> None:
        csv_path = Path(path) if isinstance(path, str) else path
        with csv_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                quest = Quest(
                    row["title"],
                    row["description"],
                    row["questline"],
                    row["dependencies"].split(","),
                    row["tags"].split(","),
                )
                quest.id = row["id"]
                quest.status = row["status"]
                quest.created_at = row["created_at"]
                quest.updated_at = row["updated_at"]
                self.quests[quest.id] = quest
        save_quests(self.quests)

    def suggest_next_quest(self, questline=None) -> None:
        # Suggests the next pending quest (could be AI-driven)
        quests = [q for q in self.quests.values() if q.status == "pending"]
        if questline:
            quests = [q for q in quests if q.questline == questline]
        if not quests:
            return
        # Simple heuristic: fewest dependencies, earliest created
        quests.sort(key=lambda q: (len(q.dependencies), q.created_at))
        quests[0]

    def copilot_integration(self, context: Any = None) -> None:
        """Integrate with Copilot bridge to enhance quest management."""
        if not CONSCIOUSNESS_BRIDGE_AVAILABLE or not callable(ConsciousnessBridge):
            if context:
                logger.info("Copilot integration: Context provided but bridge unavailable")
            return

        ConsciousnessBridge()

        # Use context to enhance quest suggestions
        if context:
            # Extract relevant quest metadata from context
            str(context)

            # Get pending quests that could benefit from context
            pending_quests = [q for q in self.quests.values() if q.status == "pending"]

            # Log integration for tracking
            logger.info(
                f"Copilot integration: Analyzing {len(pending_quests)} pending quests with context"
            )

            # Track integration stats
            if not hasattr(self, "_copilot_integrations"):
                self._copilot_integrations = 0
            self._copilot_integrations += 1


# --- CLI ---
def main() -> None:
    engine = QuestEngine()
    args = sys.argv[1:]
    if not args:
        return
    cmd = args[0]
    if cmd == "add_questline":
        name = args[1]
        desc = args[2]
        tags = args[3:] if len(args) > 3 else None
        engine.add_questline(name, desc, tags)
    elif cmd == "add_quest":
        title = args[1]
        desc = args[2]
        questline = args[3]
        deps = args[4].split(",") if len(args) > 4 and args[4] else []
        tags = args[5].split(",") if len(args) > 5 and args[5] else []
        engine.add_quest(title, desc, questline, deps, tags)
    elif cmd == "list_questlines":
        engine.list_questlines()
    elif cmd == "update_quest_status":
        quest_id = args[1]
        status = args[2]
        engine.update_quest_status(quest_id, status)
    elif cmd == "list_quests":
        # Fix: Always define questline and status before use
        list_questline = args[1] if len(args) > 1 else None
        quest_status = args[2] if len(args) > 2 else None
        engine.list_quests(list_questline, quest_status)
    elif cmd == "export_csv":
        export_path = args[1] if len(args) > 1 else QUESTS_CSV_FILE
        engine.export_csv(export_path)
    elif cmd == "import_csv":
        import_path = args[1] if len(args) > 1 else QUESTS_CSV_FILE
        engine.import_csv(import_path)
    elif cmd == "questline_details":
        name = args[1]
        engine.questline_details(name)
    elif cmd == "suggest_next_quest":
        suggest_questline = args[1] if len(args) > 1 else None
        engine.suggest_next_quest(suggest_questline)
    elif cmd == "copilot_integration":
        engine.copilot_integration()
    else:
        pass


if __name__ == "__main__":
    main()
