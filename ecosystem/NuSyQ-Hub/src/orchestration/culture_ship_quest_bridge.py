"""Bridge Culture Ship strategic decisions to Quest system.

This module connects Culture Ship's strategic analysis to the quest tracking system,
making strategic improvements visible, trackable, and gamified.

OmniTag: [culture-ship, quest-system, strategic-tracking, autonomous-improvement]
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def calculate_strategic_xp(decision: dict[str, Any]) -> int:
    """Calculate XP for strategic decision based on impact.

    Args:
        decision: Strategic decision dictionary
            {
                "decision": str,
                "priority": "critical" | "high" | "medium" | "low",
                ...
            }

    Returns:
        XP value based on priority and impact
    """
    base_xp = 250  # Medium difficulty base

    # Multipliers based on priority
    priority_multiplier = {"critical": 2.0, "high": 1.5, "medium": 1.0, "low": 0.5}

    multiplier = priority_multiplier.get(decision.get("priority", "medium"), 1.0)
    return int(base_xp * multiplier)


def _read_json(path: Path, default: Any) -> Any:
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _write_ticket_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# Culture Ship Strategic Tickets")
    lines.append("")
    lines.append(f"Generated: {payload.get('generated_at')}")
    lines.append(f"Source cycle: {payload.get('source_cycle_timestamp')}")
    lines.append(f"Ticket count: {payload.get('ticket_count', 0)}")
    lines.append("")

    for ticket in payload.get("tickets", []):
        if not isinstance(ticket, dict):
            continue
        lines.append(f"## {ticket.get('order')}. {ticket.get('title')}")
        lines.append(f"- Ticket ID: `{ticket.get('ticket_id')}`")
        lines.append(f"- Quest ID: `{ticket.get('quest_id')}`")
        lines.append(f"- Owner: `{ticket.get('owner')}`")
        lines.append(
            f"- Category/Severity/Priority: `{ticket.get('category')}` / "
            f"`{ticket.get('severity')}` / `{ticket.get('priority_score')}`"
        )
        steps = ticket.get("implementation_steps", [])
        if isinstance(steps, list) and steps:
            lines.append("- Implementation Steps:")
            for step in steps:
                lines.append(f"  - {step}")
        checks = ticket.get("proof_of_fix_checks", [])
        if isinstance(checks, list) and checks:
            lines.append("- Proof of Fix Checks:")
            for check in checks:
                if isinstance(check, dict):
                    lines.append(
                        f"  - {check.get('name')}: `{check.get('command')}` (expect: {check.get('expected')})"
                    )
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _normalize_priority(decision: dict[str, Any]) -> tuple[int, str]:
    raw = decision.get("priority", "medium")
    if isinstance(raw, (int, float)):
        score = int(raw)
        if score >= 9:
            return score, "critical"
        if score >= 7:
            return score, "high"
        if score >= 4:
            return score, "medium"
        return score, "low"
    label = str(raw).strip().lower()
    label_to_score = {"critical": 10, "high": 8, "medium": 5, "low": 2}
    return label_to_score.get(label, 5), label if label in label_to_score else "medium"


def _decision_signature(decision: dict[str, Any]) -> str:
    identity = {
        "decision": decision.get("decision", ""),
        "category": decision.get("category", "general"),
        "severity": decision.get("severity", "medium"),
        "rationale": decision.get("rationale", ""),
    }
    return json.dumps(identity, sort_keys=True)


def _load_codeowners_rules() -> tuple[list[tuple[str, list[str]]], str]:
    codeowners_path = Path(".github/CODEOWNERS")
    default_owner = "@KiloMusician"
    rules: list[tuple[str, list[str]]] = []

    if not codeowners_path.exists():
        return rules, default_owner

    for raw in codeowners_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        pattern, owners = parts[0], [p for p in parts[1:] if p.startswith("@")]
        if not owners:
            continue
        if pattern == "*":
            default_owner = owners[0]
        rules.append((pattern, owners))
    return rules, default_owner


def _resolve_owner(affected_files: list[str] | None = None) -> str:
    rules, default_owner = _load_codeowners_rules()
    files = affected_files or []

    for target in files:
        normalized = str(target).replace("\\", "/").lstrip("./")
        matched_owner: str | None = None
        for pattern, owners in rules:
            rule = pattern.lstrip("/")
            if rule.endswith("/"):
                rule = f"{rule}*"
            if fnmatch(normalized, rule):
                matched_owner = owners[0]
        if matched_owner:
            return matched_owner
    return default_owner


def _build_proof_of_fix_checks(decision: dict[str, Any]) -> list[dict[str, str]]:
    category = str(decision.get("category", "general")).lower()
    affected_files = decision.get("affected_files", [])
    if not isinstance(affected_files, list):
        affected_files = []
    py_files = [str(path) for path in affected_files if str(path).endswith(".py")]
    scoped_py = " ".join(py_files[:8])

    checks: list[dict[str, str]] = []
    if scoped_py:
        checks.append(
            {
                "name": "Targeted Ruff check",
                "command": f"python -m ruff check {scoped_py}",
                "expected": "No lint violations in targeted files",
            }
        )
        checks.append(
            {
                "name": "Targeted mypy check",
                "command": f"python -m mypy --follow-imports=skip {scoped_py}",
                "expected": "No type errors in targeted files",
            }
        )

    checks.extend(
        [
            {
                "name": "Main CLI latency guard",
                "command": "python src/main.py --help",
                "expected": "Completes in under 2 seconds",
            },
            {
                "name": "OpenClaw integration smoke",
                "command": "python scripts/openclaw_smoke_test.py",
                "expected": "5/5 smoke checks pass",
            },
        ]
    )

    if category in {"correctness", "quality"}:
        checks.append(
            {
                "name": "Filtered test suite",
                "command": 'python -m pytest -q -k "not e2e and not llm_testing"',
                "expected": "No regressions in filtered test suite",
            }
        )
    elif category == "architecture":
        checks.append(
            {
                "name": "Culture Ship dry-run cycle",
                "command": "python scripts/start_nusyq.py culture_ship_cycle --sync --dry-run --json",
                "expected": "Cycle completes with status=ok",
            }
        )
    elif category == "efficiency":
        checks.append(
            {
                "name": "AI status health gate",
                "command": "python scripts/start_nusyq.py ai_status --json",
                "expected": "No critical AI health failures",
            }
        )

    return checks


def _find_existing_quest_by_signature(
    quests: list[dict[str, Any]], signature: str
) -> dict[str, Any] | None:
    for quest in quests:
        metadata = quest.get("metadata", {})
        if isinstance(metadata, dict) and metadata.get("culture_ship_signature") == signature:
            return quest
    return None


def _upsert_quest_metadata(
    quest: dict[str, Any],
    owner: str,
    proof_checks: list[dict[str, str]],
    signature: str,
) -> None:
    metadata = quest.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    metadata["owner"] = owner
    metadata["proof_of_fix_checks"] = proof_checks
    metadata["culture_ship_signature"] = signature
    quest["metadata"] = metadata
    quest["owner"] = owner
    quest["proof_of_fix_checks"] = proof_checks
    quest["updated_at"] = datetime.now().isoformat()


def journal_strategic_decision_as_quest(decision: dict[str, Any]) -> str:
    """Convert Culture Ship strategic decision to quest.

    Args:
        decision: Strategic decision from Culture Ship
            {
                "decision": "Modernize type annotations",
                "rationale": "Improve type safety...",
                "priority": "high",
                "category": "architecture",
                "timestamp": "2026-01-24T..."
            }

    Returns:
        Quest ID
    """
    quest_file = Path("src/Rosetta_Quest_System/quests.json")

    quests = _read_json(quest_file, [])
    if not isinstance(quests, list):
        quests = []

    signature = _decision_signature(decision)
    existing = _find_existing_quest_by_signature(quests, signature)
    owner = _resolve_owner(decision.get("affected_files", []))
    proof_checks = _build_proof_of_fix_checks(decision)
    _, priority_label = _normalize_priority(decision)

    if existing:
        _upsert_quest_metadata(existing, owner, proof_checks, signature)
        _write_json(quest_file, quests)
        quest_id = str(existing.get("id", ""))
        if quest_id:
            return quest_id

    quest = {
        "id": f"quest-cs-{int(datetime.now().timestamp() * 1000)}",
        "title": f"Strategic: {decision['decision']}",
        "description": decision.get("rationale", "Culture Ship strategic decision"),
        "status": "active",
        "tags": ["strategy", "culture-ship", decision.get("category", "general")],
        "priority": priority_label,
        "xp": calculate_strategic_xp(decision),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "source": "culture_ship",
        "owner": owner,
        "proof_of_fix_checks": proof_checks,
        "metadata": {
            "culture_ship_decision": decision,
            "culture_ship_signature": signature,
            "owner": owner,
            "proof_of_fix_checks": proof_checks,
        },
    }

    quests.append(quest)
    _write_json(quest_file, quests)

    logger.info(f"Created quest {quest['id']} from Culture Ship decision")
    return quest["id"]


def _triage_sort_key(decision: dict[str, Any]) -> tuple[int, int]:
    category_rank = {
        "architecture": 0,
        "correctness": 1,
        "efficiency": 2,
        "quality": 3,
    }
    category = str(decision.get("category", "general")).lower()
    priority_score, _ = _normalize_priority(decision)
    return category_rank.get(category, 9), -priority_score


def triage_latest_culture_ship_cycle(cycle_timestamp: str | None = None) -> dict[str, Any]:
    """Convert strategic cycle decisions to concrete implementation tickets.

    Args:
        cycle_timestamp: Optional exact (or prefix) timestamp to triage.
            When omitted, triages the latest cycle.
    """
    history_file = Path("state/culture_ship_healing_history.json")
    quest_file = Path("src/Rosetta_Quest_System/quests.json")
    quest_log = Path("src/Rosetta_Quest_System/quest_log.jsonl")
    report_file = Path("state/reports/culture_ship_tickets_latest.json")
    report_md_file = Path("state/reports/culture_ship_tickets_latest.md")

    history = _read_json(history_file, {"cycles": []})
    if not isinstance(history, dict):
        history = {"cycles": []}
    cycles = history.get("cycles", [])
    if not isinstance(cycles, list) or not cycles:
        payload = {
            "status": "no_cycles",
            "generated_at": datetime.now().isoformat(),
            "tickets": [],
        }
        _write_json(report_file, payload)
        return payload

    quests = _read_json(quest_file, [])
    if not isinstance(quests, list):
        quests = []

    selected_index = len(cycles) - 1
    if cycle_timestamp:
        match_index = next(
            (
                idx
                for idx in range(len(cycles) - 1, -1, -1)
                if str(cycles[idx].get("timestamp", "")).startswith(cycle_timestamp)
            ),
            None,
        )
        if match_index is None:
            payload = {
                "status": "cycle_not_found",
                "generated_at": datetime.now().isoformat(),
                "requested_cycle_timestamp": cycle_timestamp,
                "tickets": [],
            }
            _write_json(report_file, payload)
            return payload
        selected_index = match_index

    cycle = cycles[selected_index]
    decisions = cycle.get("strategic_decisions", [])
    if not isinstance(decisions, list):
        decisions = []

    ordered = sorted(enumerate(decisions), key=lambda item: _triage_sort_key(item[1]))
    cycle_stamp = (
        str(cycle.get("timestamp", datetime.now().isoformat())).replace(":", "").replace("-", "")
    )
    tickets: list[dict[str, Any]] = []

    for position, (original_index, decision) in enumerate(ordered, start=1):
        if not isinstance(decision, dict):
            continue

        signature = _decision_signature(decision)
        owner = str(decision.get("owner") or _resolve_owner(decision.get("affected_files", [])))
        proof_checks = decision.get("proof_of_fix_checks")
        if not isinstance(proof_checks, list):
            proof_checks = _build_proof_of_fix_checks(decision)

        quest_id = str(decision.get("quest_id", "")).strip()
        if not quest_id:
            quest_id = journal_strategic_decision_as_quest(decision)
            decision["quest_id"] = quest_id

        existing_quest = next((q for q in quests if q.get("id") == quest_id), None)
        if existing_quest is None:
            # Fallback to signature lookup if quest file changed out-of-band.
            existing_quest = _find_existing_quest_by_signature(quests, signature)
            if existing_quest is not None:
                quest_id = str(existing_quest.get("id", quest_id))
                decision["quest_id"] = quest_id
        if existing_quest is not None:
            _upsert_quest_metadata(existing_quest, owner, proof_checks, signature)

        ticket_id = str(decision.get("triage_ticket_id", "")).strip()
        is_new_ticket = not ticket_id
        if is_new_ticket:
            ticket_id = f"cs-ticket-{cycle_stamp[:15]}-{position:02d}"

        priority_score, priority_label = _normalize_priority(decision)
        ticket = {
            "ticket_id": ticket_id,
            "order": position,
            "quest_id": quest_id,
            "owner": owner,
            "category": decision.get("category", "general"),
            "severity": decision.get("severity", "medium"),
            "priority_score": priority_score,
            "priority": priority_label,
            "title": decision.get("decision", "Culture Ship strategic task"),
            "implementation_steps": decision.get("action_plan", []),
            "affected_files": decision.get("affected_files", []),
            "proof_of_fix_checks": proof_checks,
            "status": "open",
            "triaged_at": datetime.now().isoformat(),
        }
        tickets.append(ticket)

        decision["owner"] = owner
        decision["proof_of_fix_checks"] = proof_checks
        decision["triage_ticket_id"] = ticket_id
        decision["triage_order"] = position
        decisions[original_index] = decision

        if is_new_ticket:
            _append_jsonl(
                quest_log,
                {
                    "timestamp": datetime.now().isoformat(),
                    "event": "culture_ship_ticket_triaged",
                    "details": ticket,
                },
            )

    cycle["strategic_decisions"] = decisions
    cycle["triage_tickets"] = tickets
    cycles[selected_index] = cycle
    history["cycles"] = cycles
    _write_json(history_file, history)
    _write_json(quest_file, quests)

    payload = {
        "status": "ok",
        "generated_at": datetime.now().isoformat(),
        "requested_cycle_timestamp": cycle_timestamp,
        "source_cycle_timestamp": cycle.get("timestamp"),
        "ticket_count": len(tickets),
        "tickets": tickets,
        "report_path": str(report_file),
    }
    _write_json(report_file, payload)
    _write_ticket_markdown(report_md_file, payload)
    return payload


def sync_culture_ship_history_to_quests() -> list[str]:
    """Sync Culture Ship healing history to quest system.

    Reads Culture Ship's healing history and creates quests for strategic
    decisions that don't yet have associated quests.

    Returns:
        List of created quest IDs
    """
    history_file = Path("state/culture_ship_healing_history.json")

    if not history_file.exists():
        logger.warning("Culture Ship history not found at %s", history_file)
        return []

    try:
        history = json.loads(history_file.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error("Failed to load Culture Ship history: %s", e)
        return []

    quest_ids: list[str] = []

    # Process each healing cycle
    for cycle in history.get("cycles", []):
        for decision in cycle.get("strategic_decisions", []):
            # Only create quests for decisions not already tracked
            if not decision.get("quest_id"):
                try:
                    quest_id = journal_strategic_decision_as_quest(decision)
                    quest_ids.append(quest_id)
                    decision["quest_id"] = quest_id
                except Exception as e:
                    logger.error(f"Failed to create quest for decision: {e}")
                    continue

    # Update history with quest IDs
    if quest_ids:
        try:
            _write_json(history_file, history)
            logger.info(f"✅ Synced {len(quest_ids)} Culture Ship decisions to quests")
        except Exception as e:
            logger.error(f"Failed to update Culture Ship history: {e}")

    try:
        triage = triage_latest_culture_ship_cycle()
        if triage.get("ticket_count", 0):
            logger.info(
                "🧭 Triaged %s strategic tickets (architecture+correctness prioritized)",
                triage["ticket_count"],
            )
    except Exception as e:
        logger.error(f"Failed to triage latest Culture Ship cycle: {e}")

    return quest_ids


if __name__ == "__main__":
    # Test the bridge
    logging.basicConfig(level=logging.INFO)

    logger.info("🚢 Testing Culture Ship → Quest Bridge\n")

    # Sync existing Culture Ship history to quests
    quest_ids = sync_culture_ship_history_to_quests()

    logger.info(f"\n✅ Created {len(quest_ids)} quests from Culture Ship strategic decisions")
    triage = triage_latest_culture_ship_cycle()
    logger.info(f"✅ Triaged {triage.get('ticket_count', 0)} strategic tickets")

    if quest_ids:
        logger.info("\n📋 Quest IDs:")
        for qid in quest_ids[:5]:  # Show first 5
            logger.info(f"   - {qid}")
        if len(quest_ids) > 5:
            logger.info(f"   ... and {len(quest_ids) - 5} more")
