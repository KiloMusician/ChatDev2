"""Perpetual Next-Action Generator.

Wires multiple intelligence signals into a continuous feedback loop:
- Current state snapshots (current_state.md changes)
- Lifecycle catalog (task progression)
- Problem diagnostics (errors, failures)
- Quest system (work routing)
- Coverage metrics (test progress)
- Error signals (consistency protocol)

Generates "always have next action" by analyzing:
1. What changed (state delta)
2. What's pending (lifecycle, quests)
3. What's broken (diagnostics)
4. What's highest priority (scoring)

Produces ranked action queue for auto_cycle perpetual chug.
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    from datetime import UTC  # type: ignore[attr-defined]
except ImportError:
    from datetime import timezone

    UTC = timezone.utc  # noqa: UP017


class ActionType(Enum):
    """Categories of next actions."""

    FIX_ERROR = "fix_error"  # Diagnostics-driven
    EXPAND_COVERAGE = "expand_coverage"  # Coverage metrics-driven
    RESOLVE_QUEST = "resolve_quest"  # Quest system-driven
    HEAL_REPOSITORY = "heal_repository"  # Health check-driven
    VALIDATE_MODULE = "validate_module"  # Import/module availability
    SCALE_ORCHESTRATION = "scale_orchestration"  # Orchestration tests
    INTEGRATE_CROSS_REPO = "integrate_cross_repo"  # Multi-repo coordination
    IMPROVE_ARCHITECTURE = "improve_architecture"  # Architecture issues


class Priority(Enum):
    """Action priority levels."""

    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    DEFERRED = 1


class NextAction:
    """Represents a single next action with scoring."""

    def __init__(
        self,
        title: str,
        action_type: ActionType,
        priority: Priority,
        estimated_effort: str,
        source_signal: str,
        context: dict[str, Any],
    ):
        """Initialize NextAction with title, action_type, priority, ...."""
        self.title = title
        self.action_type = action_type
        self.priority = priority
        self.estimated_effort = estimated_effort
        self.source_signal = source_signal
        self.context = context
        self.score = priority.value

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "type": self.action_type.value,
            "priority": self.priority.name,
            "effort": self.estimated_effort,
            "source": self.source_signal,
            "score": self.score,
            "context": self.context,
        }


class SignalAnalyzer:
    """Analyzes individual intelligence signals."""

    def __init__(self, repo_root: Path):
        """Initialize SignalAnalyzer with repo_root."""
        self.repo_root = repo_root

    @staticmethod
    def _normalize_title(title: str) -> str:
        return " ".join(title.strip().lower().split())

    @staticmethod
    def _parse_timestamp(ts: str) -> datetime | None:
        if not ts:
            return None
        candidate = ts.strip()
        if candidate.endswith("Z"):
            candidate = candidate[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    def analyze_current_state(self) -> dict[str, Any]:
        """Parse current_state.md for recent changes."""
        state_file = self.repo_root / "state" / "reports" / "current_state.md"
        if not state_file.exists():
            return {}

        try:
            content = state_file.read_text()
            return {
                "exists": True,
                "size": len(content),
                "mtime": state_file.stat().st_mtime,
                "sections": self._parse_sections(content),
            }
        except Exception as e:
            return {"error": str(e)}

    def _parse_sections(self, content: str) -> list[str]:
        """Extract main sections from markdown."""
        sections = []
        for line in content.split("\n"):
            if line.startswith("## "):
                sections.append(line.replace("## ", "").strip())
        return sections

    def analyze_lifecycle_catalog(self) -> dict[str, Any]:
        """Parse lifecycle_catalog.json for pending tasks."""
        catalog_file = self.repo_root / "docs" / "lifecycle_catalog.json"
        if not catalog_file.exists():
            return {}

        try:
            catalog = json.loads(catalog_file.read_text())
            pending = [t for t in catalog.get("tasks", []) if t.get("status") == "pending"]
            in_progress = [t for t in catalog.get("tasks", []) if t.get("status") == "in_progress"]
            return {
                "total_tasks": len(catalog.get("tasks", [])),
                "pending": len(pending),
                "in_progress": len(in_progress),
                "sample_pending": pending[:3],
            }
        except Exception as e:
            return {"error": str(e)}

    def analyze_quest_system(self) -> dict[str, Any]:
        """Parse quest_log.jsonl for active quests."""
        quest_file = self.repo_root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        if not quest_file.exists():
            return {}

        try:
            raw_lines = quest_file.read_text(encoding="utf-8", errors="replace").splitlines()
            max_events = int(os.getenv("NUSYQ_NEXT_ACTION_MAX_QUEST_EVENTS", "50000"))
            candidate_lines = raw_lines[-max_events:] if max_events > 0 else raw_lines

            latest_by_key: dict[str, dict[str, str]] = {}
            processed_events = 0
            for line in candidate_lines:
                if not line.strip():
                    continue
                raw_quest = json.loads(line)
                if not isinstance(raw_quest, dict):
                    continue
                quest: dict[str, Any] = raw_quest
                processed_events += 1

                raw_details = quest.get("details")
                details: dict[str, Any] = raw_details if isinstance(raw_details, dict) else {}
                quest_id = str(
                    details.get("id")
                    or details.get("quest_id")
                    or quest.get("id")
                    or quest.get("quest_id")
                    or ""
                ).strip()
                title = str(
                    details.get("title")
                    or details.get("quest")
                    or details.get("name")
                    or quest.get("title")
                    or quest.get("quest")
                    or quest.get("name")
                    or ""
                ).strip()
                status = (
                    str(
                        details.get("status")
                        or details.get("new_status")
                        or quest.get("status")
                        or quest.get("state")
                        or "unknown"
                    )
                    .strip()
                    .lower()
                )
                timestamp = str(quest.get("timestamp") or details.get("updated_at") or "").strip()

                key = quest_id or self._normalize_title(title)
                if not key:
                    continue
                latest_by_key[key] = {
                    "title": title or key,
                    "status": status,
                    "timestamp": timestamp,
                }

            # Collapse duplicate IDs that represent the same quest title.
            latest_by_title: dict[str, dict[str, str]] = {}
            untitled_entries: list[dict[str, str]] = []
            for item in latest_by_key.values():
                title = item["title"].strip()
                if not title:
                    untitled_entries.append(item)
                    continue
                normalized = self._normalize_title(title)
                existing = latest_by_title.get(normalized)
                if not existing:
                    latest_by_title[normalized] = item
                    continue

                existing_ts = self._parse_timestamp(existing.get("timestamp", ""))
                candidate_ts = self._parse_timestamp(item.get("timestamp", ""))
                if existing_ts is None and candidate_ts is None:
                    if item.get("timestamp", "") > existing.get("timestamp", ""):
                        latest_by_title[normalized] = item
                elif candidate_ts is not None and (
                    existing_ts is None or candidate_ts >= existing_ts
                ):
                    latest_by_title[normalized] = item

            compacted_entries = list(latest_by_title.values()) + untitled_entries
            active_statuses = {"active", "in_progress", "open", "TODO"}
            pending_statuses = {"pending"}
            completed_statuses = {"completed", "complete", "success", "done", "closed", "resolved"}
            failed_statuses = {"failed", "error"}
            terminal_statuses = completed_statuses | failed_statuses | {"cancelled", "canceled"}
            quest_window_days = int(os.getenv("NUSYQ_NEXT_ACTION_QUEST_WINDOW_DAYS", "21"))
            cutoff = datetime.now(UTC) - timedelta(days=quest_window_days)

            quests: dict[str, Any] = {
                "active": [],
                "pending": [],
                "completed": [],
                "failed": [],
            }
            active_total = 0
            pending_total = 0
            stale_backlog = 0
            stale_titles: list[str] = []
            for item in compacted_entries:
                status = item["status"]
                title = item["title"]
                timestamp = item.get("timestamp", "")
                parsed_ts = self._parse_timestamp(timestamp)
                is_recent = parsed_ts is not None and parsed_ts >= cutoff

                if status in active_statuses:
                    active_total += 1
                    if is_recent:
                        quests["active"].append(title)
                    else:
                        stale_backlog += 1
                        if title:
                            stale_titles.append(title)
                elif status in pending_statuses:
                    pending_total += 1
                    if is_recent:
                        quests["pending"].append(title)
                    else:
                        stale_backlog += 1
                        if title:
                            stale_titles.append(title)
                elif status in completed_statuses:
                    quests["completed"].append(title)
                elif status in failed_statuses:
                    quests["failed"].append(title)
                elif status in terminal_statuses:
                    # Recognized terminal status but not included in completed/failed collections.
                    continue

            quests["raw_event_count"] = len(raw_lines)
            quests["processed_event_count"] = processed_events
            quests["deduped_count"] = len(compacted_entries)
            quests["active_total_count"] = active_total
            quests["pending_total_count"] = pending_total
            quests["active_recent_count"] = len(quests["active"])
            quests["pending_recent_count"] = len(quests["pending"])
            quests["stale_backlog_count"] = stale_backlog
            quests["stale_sample"] = stale_titles[:5]
            quests["quest_window_days"] = quest_window_days
            return quests
        except Exception as e:
            return {"error": str(e)}

    def analyze_diagnostics(self) -> dict[str, Any]:
        """Read diagnostics/gate artifacts without running expensive scans."""
        diagnostics: dict[str, Any] = {
            "available": False,
            "errors": 0,
            "warnings": 0,
            "infos": 0,
            "ruff_count": 0,
            "import_like_count": 0,
            "gate_failed_checks": [],
            "gate_skipped_count": 0,
        }

        unified_report = (
            self.repo_root / "docs" / "Reports" / "diagnostics" / "unified_error_report_latest.json"
        )
        if unified_report.exists():
            try:
                payload = json.loads(unified_report.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    diagnostics["available"] = True
                    ground = payload.get("ground_truth", {})
                    if isinstance(ground, dict):
                        diagnostics["errors"] = int(ground.get("errors", 0) or 0)
                        diagnostics["warnings"] = int(ground.get("warnings", 0) or 0)
                        diagnostics["infos"] = int(ground.get("infos", 0) or 0)

                    by_repo = payload.get("by_repo", {})
                    if isinstance(by_repo, dict):
                        ruff_count = 0
                        for repo_summary in by_repo.values():
                            if not isinstance(repo_summary, dict):
                                continue
                            by_source = repo_summary.get("by_source", {})
                            if isinstance(by_source, dict):
                                ruff_count += int(by_source.get("ruff", 0) or 0)
                        diagnostics["ruff_count"] = ruff_count

                    details = payload.get("diagnostic_details", [])
                    if isinstance(details, list):
                        import_like = 0
                        for row in details:
                            if not isinstance(row, dict):
                                continue
                            message = str(row.get("message") or "").lower()
                            if (
                                "import" in message
                                or "module not found" in message
                                or "cannot import" in message
                            ):
                                import_like += 1
                        diagnostics["import_like_count"] = import_like
            except Exception as e:
                diagnostics["artifact_error"] = str(e)

        system_complete_gate = (
            self.repo_root / "state" / "reports" / "system_complete_gate_latest.json"
        )
        if system_complete_gate.exists():
            try:
                gate = json.loads(system_complete_gate.read_text(encoding="utf-8"))
                checks = gate.get("checks", []) if isinstance(gate, dict) else []
                if isinstance(checks, list):
                    failed_checks: list[dict[str, Any]] = []
                    skipped_count = 0
                    for check in checks:
                        if not isinstance(check, dict):
                            continue
                        if check.get("passed") is True:
                            continue
                        if check.get("skipped") is True:
                            skipped_count += 1
                            continue
                        failed_checks.append(
                            {
                                "name": str(check.get("name") or "unknown"),
                                "cmd": check.get("cmd"),
                                "stderr_tail": str(check.get("stderr_tail") or ""),
                            }
                        )
                    diagnostics["gate_failed_checks"] = failed_checks
                    diagnostics["gate_skipped_count"] = skipped_count
            except Exception as e:
                diagnostics["gate_error"] = str(e)

        return diagnostics

    def analyze_coverage(self) -> dict[str, Any]:
        """Parse coverage metrics from last test run."""
        coverage_file = self.repo_root / ".coverage_full.log"
        if not coverage_file.exists():
            return {"status": "no_coverage_log"}

        try:
            content = coverage_file.read_text()
            lines = content.split("\n")

            # Extract coverage percentage from output
            coverage_pct = None
            for line in lines:
                if "%" in line and ("coverage" in line.lower() or "TOTAL" in line):
                    # Try to extract percentage
                    import re

                    match = re.search(r"(\d+(?:\.\d+)?)%", line)
                    if match:
                        coverage_pct = float(match.group(1))
                        break

            return {
                "current": coverage_pct or 54.25,
                "target": 70,
                "gap": (70 - (coverage_pct or 54.25)),
                "last_updated": coverage_file.stat().st_mtime,
            }
        except Exception as e:
            return {"error": str(e)}

    def analyze_module_availability(self) -> dict[str, Any]:
        """Check which core modules are importable."""
        modules_to_check = [
            "src.quantum.quantum_problem_resolver",
            "src.orchestration.unified_ai_orchestrator",
            "src.core.claude_copilot_orchestrator",
            "src.integration.consciousness_bridge",
            "src.integration.ollama_integration",
        ]

        availability = {}
        for module in modules_to_check:
            try:
                __import__(module)
                availability[module] = "available"
            except ImportError as e:
                availability[module] = f"unavailable: {str(e)[:50]}"
            except Exception as e:
                availability[module] = f"error: {str(e)[:50]}"

        return availability


class ActionGenerator:
    """Generates next actions from signals."""

    def __init__(self, repo_root: Path):
        """Initialize ActionGenerator with repo_root."""
        self.repo_root = repo_root
        self.analyzer = SignalAnalyzer(repo_root)

    def generate_actions(self) -> list[NextAction]:
        """Generate prioritized action queue from all signals."""
        actions = []

        # Signal 1: Coverage gap
        coverage = self.analyzer.analyze_coverage()
        if isinstance(coverage.get("gap"), (int, float)) and coverage["gap"] > 0:
            gap = coverage["gap"]
            effort = "2-4h" if gap < 10 else "1 week"
            priority = Priority.HIGH if gap > 15 else Priority.MEDIUM
            actions.append(
                NextAction(
                    title=f"Expand test coverage (gap: {gap:.1f}% → 70%)",
                    action_type=ActionType.EXPAND_COVERAGE,
                    priority=priority,
                    estimated_effort=effort,
                    source_signal="coverage_metrics",
                    context=coverage,
                )
            )

        # Signal 2: Module availability
        modules = self.analyzer.analyze_module_availability()
        unavailable = [m for m, s in modules.items() if "unavailable" in s]
        if unavailable:
            actions.append(
                NextAction(
                    title=f"Fix module availability ({len(unavailable)} modules)",
                    action_type=ActionType.VALIDATE_MODULE,
                    priority=Priority.HIGH,
                    estimated_effort="2-4h",
                    source_signal="module_availability",
                    context={
                        "unavailable_modules": unavailable,
                        "recommended_command": "python scripts/start_nusyq.py doctor --quick --json",
                    },
                )
            )

        # Signal 3: Diagnostics and gate blockers
        diagnostics = self.analyzer.analyze_diagnostics()
        failed_checks = diagnostics.get("gate_failed_checks", [])
        if isinstance(failed_checks, list) and failed_checks:
            top = failed_checks[0] if isinstance(failed_checks[0], dict) else {}
            top_name = str(top.get("name") or "system_complete_check")
            top_cmd = top.get("cmd")
            command = ""
            if isinstance(top_cmd, list):
                tokens = [str(token) for token in top_cmd]
                if tokens:
                    head = Path(tokens[0]).name.lower()
                    if "python" in head:
                        tokens[0] = "python"
                    command = " ".join(tokens)
            actions.append(
                NextAction(
                    title=f"Unblock gate failure: {top_name}",
                    action_type=ActionType.FIX_ERROR,
                    priority=Priority.CRITICAL,
                    estimated_effort="15-45m",
                    source_signal="system_complete_gate",
                    context={
                        "failed_count": len(failed_checks),
                        "top_failed_check": top_name,
                        "recommended_command": command
                        or "python scripts/start_nusyq.py system_complete --async --budget-s=1200 --json",
                        "stderr_tail": str(top.get("stderr_tail") or ""),
                    },
                )
            )

        if int(diagnostics.get("errors", 0)) > 0 or int(diagnostics.get("warnings", 0)) > 0:
            actions.append(
                NextAction(
                    title=(
                        f"Triage diagnostics: {int(diagnostics.get('errors', 0))} errors, "
                        f"{int(diagnostics.get('warnings', 0))} warnings"
                    ),
                    action_type=ActionType.FIX_ERROR,
                    priority=Priority.HIGH,
                    estimated_effort="30-90m",
                    source_signal="diagnostics",
                    context={
                        "errors": int(diagnostics.get("errors", 0)),
                        "warnings": int(diagnostics.get("warnings", 0)),
                        "infos": int(diagnostics.get("infos", 0)),
                        "recommended_command": "python scripts/start_nusyq.py error_report --quick --json",
                    },
                )
            )

        if int(diagnostics.get("ruff_count", 0)) > 0:
            actions.append(
                NextAction(
                    title=f"Burn down lint backlog ({int(diagnostics.get('ruff_count', 0))} findings)",
                    action_type=ActionType.FIX_ERROR,
                    priority=Priority.MEDIUM,
                    estimated_effort="1-3h",
                    source_signal="ruff_diagnostics",
                    context={
                        "ruff_findings": int(diagnostics.get("ruff_count", 0)),
                        "recommended_command": "python scripts/quality_orchestrator.py --skip-analysis",
                    },
                )
            )

        # Signal 4: Quest system
        quests = self.analyzer.analyze_quest_system()
        actionable_quest_count = int(
            quests.get("active_recent_count", len(quests.get("active", [])))
        ) + int(quests.get("pending_recent_count", len(quests.get("pending", []))))
        stale_backlog_count = int(quests.get("stale_backlog_count", 0))
        quest_window_days = int(quests.get("quest_window_days", 21))
        if actionable_quest_count > 0:
            actions.append(
                NextAction(
                    title=f"Advance active quests ({actionable_quest_count} recent)",
                    action_type=ActionType.RESOLVE_QUEST,
                    priority=Priority.HIGH,
                    estimated_effort="variable",
                    source_signal="quest_system",
                    context={
                        "active": quests.get("active", [])[:3],
                        "pending": quests.get("pending", [])[:3],
                        "window_days": quest_window_days,
                        "stale_backlog_count": stale_backlog_count,
                        "recommended_command": "python scripts/start_nusyq.py work",
                    },
                )
            )
        elif stale_backlog_count > 0:
            actions.append(
                NextAction(
                    title=f"Triage stale quest backlog ({stale_backlog_count} stale > {quest_window_days}d)",
                    action_type=ActionType.RESOLVE_QUEST,
                    priority=Priority.MEDIUM,
                    estimated_effort="1-2h",
                    source_signal="quest_system",
                    context={
                        "window_days": quest_window_days,
                        "stale_backlog_count": stale_backlog_count,
                        "stale_sample": quests.get("stale_sample", [])[:3],
                        "recommended_command": "python scripts/start_nusyq.py guild_available",
                    },
                )
            )

        # Signal 5: Lifecycle
        lifecycle = self.analyzer.analyze_lifecycle_catalog()
        if lifecycle.get("in_progress"):
            actions.append(
                NextAction(
                    title=f"Complete in-progress tasks ({lifecycle['in_progress']} active)",
                    action_type=ActionType.EXPAND_COVERAGE,
                    priority=Priority.MEDIUM,
                    estimated_effort="1-2h",
                    source_signal="lifecycle_catalog",
                    context={
                        **lifecycle,
                        "recommended_command": "python scripts/start_nusyq.py lifecycle_catalog",
                    },
                )
            )

        # Signal 6+: Baseline architecture actions only when queue is sparse
        if len(actions) < 3:
            actions.append(
                NextAction(
                    title="Scale AI orchestration tests (integration ready)",
                    action_type=ActionType.SCALE_ORCHESTRATION,
                    priority=Priority.MEDIUM,
                    estimated_effort="2-4h",
                    source_signal="architecture_roadmap",
                    context={
                        "reason": "3 orchestration test files created, need module debugging",
                        "recommended_command": "python -m pytest tests/test_orchestration_comprehensive.py -q",
                    },
                )
            )

            actions.append(
                NextAction(
                    title="Plan cross-repository integration (foundation laid)",
                    action_type=ActionType.INTEGRATE_CROSS_REPO,
                    priority=Priority.MEDIUM,
                    estimated_effort="4-6h",
                    source_signal="architecture_roadmap",
                    context={
                        "repos": ["NuSyQ-Hub", "SimulatedVerse", "NuSyQ"],
                        "coordination": "MCP server + consciousness bridge",
                        "recommended_command": "python scripts/start_nusyq.py cross_sync",
                    },
                )
            )

        return sorted(actions, key=lambda a: a.score, reverse=True)

    def save_action_queue(self, actions: list[NextAction], output_file: Path | None = None):
        """Save action queue to file for consumption by auto_cycle."""
        if output_file is None:
            output_file = self.repo_root / "state" / "next_action_queue.json"

        output_file.parent.mkdir(parents=True, exist_ok=True)

        queue = {
            "generated_at": datetime.utcnow().isoformat(),
            "refresh_interval_minutes": 30,
            "total_actions": len(actions),
            "by_priority": {p.name: len([a for a in actions if a.priority == p]) for p in Priority},
            "actions": [a.to_dict() for a in actions],
        }

        output_file.write_text(json.dumps(queue, indent=2))
        return output_file


def main():
    """Generate next-action queue for perpetual chug loop."""
    repo_root = Path(__file__).parent.parent.parent
    generator = ActionGenerator(repo_root)

    logger.info("\n🎯 Next-Action Generator - Analyzing Intelligence Signals")
    logger.info("=" * 70)

    # Analyze all signals
    logger.info("\n📊 Analyzing signals...")
    logger.info("   ├─ Current state snapshot")
    logger.info("   ├─ Lifecycle catalog")
    logger.info("   ├─ Quest system")
    logger.info("   ├─ Diagnostics")
    logger.info("   ├─ Coverage metrics")
    logger.info("   └─ Module availability")

    # Generate actions
    logger.info("\n🔄 Generating action queue...")
    actions = generator.generate_actions()

    # Save queue
    output_file = generator.save_action_queue(actions)
    logger.info(f"\n✅ Queue saved: {output_file.relative_to(repo_root)}")

    # Display results
    logger.info(f"\n📋 Top {min(5, len(actions))} Next Actions:\n")
    for i, action in enumerate(actions[:5], 1):
        logger.info(f"{i}. [{action.priority.name}] {action.title}")
        logger.info(f"   Type: {action.action_type.value}")
        logger.info(f"   Effort: {action.estimated_effort}")
        logger.info(f"   Source: {action.source_signal}")
        if action.context:
            context_preview = json.dumps(action.context, indent=6)[:100]
            logger.info(f"   Context: {context_preview}...")
        logger.info()

    # Summary
    logger.info("=" * 70)
    logger.info(f"Total Actions Generated: {len(actions)}")
    logger.info("Queue by Priority:")
    for priority in sorted(Priority, key=lambda p: p.value, reverse=True):
        count = len([a for a in actions if a.priority == priority])
        if count > 0:
            logger.info(f"  • {priority.name}: {count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
