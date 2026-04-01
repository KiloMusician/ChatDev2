"""Action module: brief workspace summary."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from scripts.nusyq_actions.shared import emit_action_receipt

try:
    from datetime import UTC  # type: ignore[attr-defined]
except ImportError:
    UTC = timezone.utc  # noqa: UP017

DEFAULT_QUEST_LOG_FILENAME = "quest_log.jsonl"
CURRENT_STATE_LINT_PATTERN = re.compile(r"- Lint errors: `(\d+)`")


def _read_json(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _as_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _extract_counts(payload: dict | None) -> dict[str, int]:
    if not isinstance(payload, dict):
        return {"errors": 0, "warnings": 0, "infos": 0, "total": 0}
    errors = _as_int(payload.get("errors"))
    warnings = _as_int(payload.get("warnings"))
    infos = _as_int(payload.get("infos", payload.get("infos_hints", 0)))
    total = _as_int(payload.get("total", errors + warnings + infos))
    return {
        "errors": errors,
        "warnings": warnings,
        "infos": infos,
        "total": total,
    }


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = str(value).strip().replace("Z", "+00:00")
    if not normalized:
        return None
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def _report_timestamp(payload: dict, fallback_path: Path) -> datetime | None:
    ground_truth = payload.get("ground_truth")
    ground_truth_obj = ground_truth if isinstance(ground_truth, dict) else {}
    for key in ("timestamp",):
        value = payload.get(key) or ground_truth_obj.get(key)
        if value:
            parsed = _parse_iso(str(value))
            if parsed:
                return parsed
    try:
        return datetime.fromtimestamp(fallback_path.stat().st_mtime, tz=UTC)
    except OSError:
        return None


def _collect_ground_truth_candidates(diagnostics_dir: Path) -> list[Path]:
    latest = diagnostics_dir / "unified_error_report_latest.json"
    timestamped = sorted(
        diagnostics_dir.glob("unified_error_report_*.json"),
        key=lambda p: p.stat().st_mtime if p.exists() else 0.0,
        reverse=True,
    )
    ordered: list[Path] = []
    if latest.exists():
        ordered.append(latest)
    for path in timestamped:
        if path.name.endswith("_latest.json"):
            continue
        ordered.append(path)
        if len(ordered) >= 25:
            break
    return ordered


def _ground_truth_quality_score(payload: dict, timestamp: datetime | None) -> tuple[int, float]:
    ground_truth = payload.get("ground_truth")
    gt = ground_truth if isinstance(ground_truth, dict) else {}
    scope = gt.get("scope")
    scope_obj = scope if isinstance(scope, dict) else {}
    targets_raw = scope_obj.get("targets", payload.get("targets", []))
    targets = targets_raw if isinstance(targets_raw, list) else []
    target_count = len(targets)

    scan_mode = str(scope_obj.get("scan_mode", payload.get("scan_mode", ""))).lower()
    partial_scan = bool(scope_obj.get("partial_scan", payload.get("partial_scan", False)))
    confidence = str(gt.get("confidence", "unknown")).lower()

    quality = target_count * 100
    quality += 40 if scan_mode == "full" else 10 if scan_mode == "quick" else 0
    quality += 20 if not partial_scan else -10
    quality += 15 if confidence == "high" else 8 if confidence == "medium" else 3 if confidence == "low" else 0

    age_penalty = 0.0
    if timestamp is not None:
        age_hours = max((datetime.now(UTC) - timestamp).total_seconds() / 3600.0, 0.0)
        # Prefer comprehensive scans, but decay stale reports.
        age_penalty = age_hours * 2.0
    return quality, age_penalty


def _select_ground_truth_report(diagnostics_dir: Path) -> tuple[Path, dict] | None:
    now = datetime.now(UTC)
    fresh_window_minutes = _as_int(os.getenv("NUSYQ_BRIEF_GROUND_TRUTH_FRESH_MINUTES"), default=1440)
    fresh_candidates: list[tuple[datetime, Path, dict]] = []
    best: tuple[float, datetime, Path, dict] | None = None
    for path in _collect_ground_truth_candidates(diagnostics_dir):
        payload = _read_json(path)
        if not payload:
            continue
        timestamp = _report_timestamp(payload, path)
        if timestamp is None:
            continue
        age_minutes = max(int((now - timestamp).total_seconds() // 60), 0)
        if age_minutes <= fresh_window_minutes:
            fresh_candidates.append((timestamp, path, payload))
        quality, age_penalty = _ground_truth_quality_score(payload, timestamp)
        total_score = float(quality) - age_penalty
        if best is None or total_score > best[0] or (total_score == best[0] and timestamp > best[1]):
            best = (total_score, timestamp, path, payload)
    if fresh_candidates:
        fresh_candidates.sort(key=lambda item: item[0], reverse=True)
        _, fresh_path, fresh_payload = fresh_candidates[0]
        return fresh_path, fresh_payload
    if best is None:
        return None
    return best[2], best[3]


def _load_ground_truth(diagnostics_dir: Path) -> dict | None:
    selected = _select_ground_truth_report(diagnostics_dir)
    if not selected:
        return None
    report_path, data = selected

    ground_truth_obj = data.get("ground_truth")
    ground_truth = ground_truth_obj if isinstance(ground_truth_obj, dict) else {}
    by_severity_obj = data.get("by_severity")
    by_severity = by_severity_obj if isinstance(by_severity_obj, dict) else {}

    counts = _extract_counts(ground_truth)
    if counts["total"] == 0 and any(by_severity.get(k) for k in ("errors", "warnings", "infos_hints")):
        counts = _extract_counts(
            {
                "errors": by_severity.get("errors", 0),
                "warnings": by_severity.get("warnings", 0),
                "infos": by_severity.get("infos_hints", 0),
                "total": data.get("total_diagnostics", 0),
            }
        )

    scope_obj = ground_truth.get("scope", {})
    scope = scope_obj if isinstance(scope_obj, dict) else {}
    targets_raw = scope.get("targets", data.get("targets", []))
    targets = [str(t) for t in targets_raw] if isinstance(targets_raw, list) else []
    timestamp_raw = ground_truth.get("timestamp") or data.get("timestamp")
    parsed_ts = _parse_iso(str(timestamp_raw)) if timestamp_raw else None
    age_minutes = None
    if parsed_ts:
        age_minutes = max(int((datetime.now(UTC) - parsed_ts).total_seconds() // 60), 0)

    return {
        "path": report_path,
        "counts": counts,
        "source": str(ground_truth.get("source", "unified_error_report")),
        "confidence": str(ground_truth.get("confidence", "unknown")),
        "scan_mode": str(scope.get("scan_mode", data.get("scan_mode", "unknown"))),
        "partial_scan": bool(scope.get("partial_scan", data.get("partial_scan", False))),
        "targets": targets,
        "timestamp": str(timestamp_raw) if timestamp_raw else "",
        "age_minutes": age_minutes,
    }


def _collect_problem_snapshot_candidates(diagnostics_dir: Path) -> list[Path]:
    latest = diagnostics_dir / "problem_signal_snapshot_latest.json"
    timestamped = sorted(
        diagnostics_dir.glob("problem_signal_snapshot_*.json"),
        key=lambda p: p.stat().st_mtime if p.exists() else 0.0,
        reverse=True,
    )
    ordered: list[Path] = []
    if latest.exists():
        ordered.append(latest)
    for path in timestamped:
        if path.name.endswith("_latest.json"):
            continue
        ordered.append(path)
        if len(ordered) >= 25:
            break
    return ordered


def _load_problem_snapshot(diagnostics_dir: Path) -> dict | None:
    latest_path = diagnostics_dir / "problem_signal_snapshot_latest.json"
    if latest_path.exists():
        payload = _read_json(latest_path)
        if payload:
            aggregate_obj = payload.get("aggregate", {})
            aggregate = aggregate_obj if isinstance(aggregate_obj, dict) else {}
            counts = _extract_counts(aggregate)
            timestamp = _parse_iso(str(payload.get("timestamp") or "")) or _report_timestamp(payload, latest_path)
            if timestamp is not None:
                return {
                    "path": latest_path,
                    "counts": counts,
                    "timestamp": timestamp.isoformat(),
                    "age_minutes": max(int((datetime.now(UTC) - timestamp).total_seconds() // 60), 0),
                }

    best: tuple[float, datetime, dict] | None = None
    for path in _collect_problem_snapshot_candidates(diagnostics_dir):
        payload = _read_json(path)
        if not payload:
            continue
        aggregate_obj = payload.get("aggregate", {})
        aggregate = aggregate_obj if isinstance(aggregate_obj, dict) else {}
        counts = _extract_counts(aggregate)
        timestamp = _parse_iso(str(payload.get("timestamp") or "")) or _report_timestamp(payload, path)
        if timestamp is None:
            continue
        age_hours = max((datetime.now(UTC) - timestamp).total_seconds() / 3600.0, 0.0)
        # Recency-first fallback scoring when latest is unavailable/unreadable.
        quality = counts["total"] - (age_hours * 10.0)
        candidate = {
            "path": path,
            "counts": counts,
            "timestamp": timestamp.isoformat(),
            "age_minutes": max(int((datetime.now(UTC) - timestamp).total_seconds() // 60), 0),
        }
        if best is None or quality > best[0] or (quality == best[0] and timestamp > best[1]):
            best = (quality, timestamp, candidate)
    if best is None:
        return None
    return best[2]


def _load_current_state_lint_errors(hub_path: Path) -> int | None:
    snapshot_path = hub_path / "state" / "reports" / "current_state.md"
    if not snapshot_path.exists():
        return None
    try:
        content = snapshot_path.read_text(encoding="utf-8")
    except OSError:
        return None
    match = CURRENT_STATE_LINT_PATTERN.search(content)
    if not match:
        return None
    return _as_int(match.group(1), default=0)


def handle_brief(
    paths,
    check_spine_hygiene: Callable,
    quest_log_filename: str = DEFAULT_QUEST_LOG_FILENAME,
) -> int:
    """Render a concise workspace brief."""
    deep_checks = os.getenv("NUSYQ_BRIEF_DEEP_CHECKS", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    if deep_checks:
        # Optional deep runtime probe for operators who explicitly request it.
        try:
            from src.services.ollama_service_manager import OllamaServiceManager

            mgr = OllamaServiceManager()
            if not mgr.is_healthy():
                print("🦙 Ensuring Ollama is running...")
                if mgr.ensure_running():
                    print("   ✅ Ollama started")
                else:
                    print("   ⚠️  Could not start Ollama (continuing anyway)")
        except ImportError:
            pass  # OllamaServiceManager not available

    print("📊 NuSyQ Workspace Brief")
    print("=" * 50)
    if not deep_checks:
        print("⚡ Lightweight mode active (set NUSYQ_BRIEF_DEEP_CHECKS=1 for full runtime probes)")

    print("\n## Repository Status")
    hygiene = check_spine_hygiene(paths.nusyq_hub)
    for h in hygiene:
        print(f"  {h}")

    print("\n## Active Quest")
    quest_file = paths.nusyq_hub / "src" / "Rosetta_Quest_System" / quest_log_filename
    if quest_file.exists():
        try:
            with open(quest_file, encoding="utf-8") as f:
                quest_rows = [json.loads(line) for line in f if line.strip()]
            if quest_rows:
                actionable_statuses = {"active", "open", "pending", "in_progress", "todo"}
                selected: dict | None = None
                fallback: dict | None = None
                for row in reversed(quest_rows):
                    if not isinstance(row, dict):
                        continue
                    details = row.get("details", {})
                    details_obj = details if isinstance(details, dict) else {}
                    status = str(row.get("status") or details_obj.get("status") or "").lower()
                    title = str(
                        row.get("title") or row.get("quest") or row.get("task_type") or details_obj.get("title") or ""
                    ).strip()
                    description = str(row.get("description") or details_obj.get("description") or "").strip()
                    if not fallback and (title or description):
                        fallback = {
                            "status": status,
                            "title": title,
                            "description": description,
                        }
                    if status in actionable_statuses and (title or description):
                        selected = {
                            "status": status,
                            "title": title,
                            "description": description,
                        }
                        break
                chosen = selected or fallback
                if chosen:
                    display_status = chosen.get("status", "unknown")
                    display_title = chosen.get("title", "unknown")
                    display_desc = str(chosen.get("description") or "").strip()
                    status_emoji = {
                        "completed": "✅",
                        "failed": "❌",
                        "in_progress": "🔄",
                        "active": "🔄",
                        "pending": "🟡",
                        "open": "🔵",
                        "todo": "📝",
                    }.get(display_status, "🔵")
                    if display_desc:
                        print(f"  {status_emoji} {display_title}: {display_desc[:60]}")
                    else:
                        print(f"  {status_emoji} {display_title}")
                else:
                    print("  📭 No quest entries with actionable metadata")
            else:
                print("  📭 No quests logged")
        except (OSError, json.JSONDecodeError) as exc:
            print(f"  ⚠️ Error reading quest log: {exc}")

    print("\n## Problem Signals")
    diagnostics_dir = paths.nusyq_hub / "docs" / "Reports" / "diagnostics"
    stale_days = 14
    now_utc = datetime.now(UTC)
    history_reports = [
        path for path in diagnostics_dir.glob("unified_error_report_*.json") if not path.name.endswith("_latest.json")
    ]
    stale_history = []
    for candidate in history_reports:
        try:
            age_days = (now_utc - datetime.fromtimestamp(candidate.stat().st_mtime, tz=UTC)).days
        except OSError:
            continue
        if age_days >= stale_days:
            stale_history.append(candidate)
    snapshot_history = [
        path
        for path in diagnostics_dir.glob("problem_signal_snapshot_*.json")
        if not path.name.endswith("_latest.json")
    ]
    print(
        f"  Report Inventory: {len(history_reports)} error reports "
        f"({len(stale_history)} stale>{stale_days}d), "
        f"{len(snapshot_history)} problem snapshots"
    )

    ground_truth = _load_ground_truth(diagnostics_dir)
    vscode_count_candidates = [
        diagnostics_dir / "vscode_problem_counts_tooling.json",
        diagnostics_dir / "vscode_problem_counts.json",
    ]
    snapshot_latest = diagnostics_dir / "problem_signal_snapshot_latest.json"
    vscode_counts_path = next((p for p in vscode_count_candidates if p.exists()), None)
    vscode_counts: dict[str, int] | None = None
    if vscode_counts_path:
        try:
            data = json.loads(vscode_counts_path.read_text(encoding="utf-8"))
            counts = data.get("counts", data)
            counts_obj = counts if isinstance(counts, dict) else {}
            vscode_counts = _extract_counts(counts_obj)
            source = str(data.get("source", "unknown"))
            print(
                f"  VS Code: {vscode_counts.get('errors', 0)} errors, "
                f"{vscode_counts.get('warnings', 0)} warnings, "
                f"{vscode_counts.get('infos', 0)} infos, "
                f"{vscode_counts.get('total', 0)} total"
            )
            print(f"  VS Code Source: {source}")
        except (OSError, json.JSONDecodeError):
            print("  ⚠️ VS Code counts present but unreadable")
    else:
        print("  Info: No VS Code counts recorded yet")

    snapshot_counts: dict[str, int] | None = None
    snapshot = _load_problem_snapshot(diagnostics_dir)
    if snapshot:
        snapshot_counts = snapshot["counts"]
        print(
            f"  Tool Aggregate: {snapshot_counts.get('errors', 0)} errors, "
            f"{snapshot_counts.get('warnings', 0)} warnings, "
            f"{snapshot_counts.get('infos', 0)} infos, "
            f"{snapshot_counts.get('total', 0)} total"
        )
    elif snapshot_latest.exists():
        print("  ⚠️ Problem snapshot present but unreadable")

    drift_max_age_minutes = _as_int(os.getenv("NUSYQ_BRIEF_DRIFT_MAX_AGE_MINUTES"), default=360)
    ground_truth_age_minutes: int | None = None
    ground_truth_confidence: str = "unknown"
    if ground_truth:
        gt_counts = ground_truth["counts"]
        print(
            f"  Ground Truth: {gt_counts.get('errors', 0)} errors, "
            f"{gt_counts.get('warnings', 0)} warnings, "
            f"{gt_counts.get('infos', 0)} infos, "
            f"{gt_counts.get('total', 0)} total"
        )
        gt_targets = ", ".join(ground_truth.get("targets", [])) or "unknown"
        gt_scan = ground_truth.get("scan_mode", "unknown")
        gt_confidence = ground_truth.get("confidence", "unknown")
        ground_truth_confidence = str(gt_confidence).strip().lower() or "unknown"
        partial_scan = "partial" if ground_truth.get("partial_scan") else "full"
        print(f"  Ground Truth Scope: {gt_scan} / {partial_scan} / targets={gt_targets} / confidence={gt_confidence}")
        age_minutes = ground_truth.get("age_minutes")
        if isinstance(age_minutes, int):
            ground_truth_age_minutes = age_minutes
        if isinstance(age_minutes, int):
            if age_minutes >= 60:
                print(f"  Ground Truth Age: ~{age_minutes // 60}h {age_minutes % 60}m")
            else:
                print(f"  Ground Truth Age: ~{age_minutes}m")
            if age_minutes > 24 * 60:
                print("  ⚠️ Ground truth is older than 24h; rerun error_report for fresh diagnostics")
    else:
        print("  ⚠️ Ground truth unavailable; run: python scripts/start_nusyq.py error_report --sync")

    gt_stale_for_drift = isinstance(ground_truth_age_minutes, int) and (
        ground_truth_age_minutes > drift_max_age_minutes
    )
    gt_low_confidence = ground_truth_confidence in {"low", "unknown"}
    drift_comparison_ready = bool(ground_truth and snapshot_counts and not gt_stale_for_drift and not gt_low_confidence)

    if ground_truth and snapshot_counts and not drift_comparison_ready:
        reason = []
        if gt_stale_for_drift:
            reason.append(f"age>{drift_max_age_minutes}m")
        if gt_low_confidence:
            reason.append(f"confidence={ground_truth_confidence}")
        print(f"  Info: Drift comparison deferred ({', '.join(reason) if reason else 'insufficient confidence'})")

    if drift_comparison_ready and ground_truth["counts"]["total"] != snapshot_counts["total"]:
        print(
            "  ⚠️ Signal drift: Tool Aggregate and Ground Truth totals differ "
            f"({snapshot_counts['total']} vs {ground_truth['counts']['total']})"
        )

    current_state_lint = _load_current_state_lint_errors(paths.nusyq_hub)
    if drift_comparison_ready and current_state_lint is not None:
        gt_errors = ground_truth["counts"]["errors"]
        if current_state_lint != gt_errors:
            print(
                "  ⚠️ Snapshot drift: current_state lint errors differ from ground truth errors "
                f"({current_state_lint} vs {gt_errors})"
            )

    if ground_truth and vscode_counts and ground_truth["counts"]["total"] != vscode_counts["total"]:
        print(
            "  Info: VS Code and ground-truth totals differ "
            f"({vscode_counts['total']} vs {ground_truth['counts']['total']}); "
            "filtered editor diagnostics can be lower."
        )

    # --- Consciousness State ---
    print("\n## Consciousness State")
    if deep_checks:
        try:
            from src.orchestration.consciousness_loop import ConsciousnessLoop

            cl = ConsciousnessLoop()
            cl.initialize()
            state = cl.get_brief_state()
            if state["available"]:
                factor = state["breathing_factor"]
                factor_label = "accelerating" if factor < 0.95 else "braking" if factor > 1.05 else "steady"
                print(f"  🧠 Level {state['level']:.1f} | Stage: {state['stage']}")
                print(f"  🫁 Breathing: {factor:.2f}x  ({factor_label})")
                directives = state.get("directives", [])
                if directives:
                    print(f"  ⚓ Ship: {len(directives)} active directive(s)")
                else:
                    print("  ⚓ Ship: no active directives")
                print("  🔗 SimulatedVerse: online")
            else:
                print("  ⚫ SimulatedVerse offline — consciousness loop inactive")
        except Exception as exc:
            print(f"  ⚠️ Consciousness state unavailable: {exc}")
    else:
        print("  ⚡ Deep consciousness probe skipped in lightweight mode")

    # Pulse the metrics terminal with an awareness snapshot (best-effort)
    try:
        from src.system.agent_awareness import broadcast_awareness_snapshot

        broadcast_awareness_snapshot()
    except Exception:
        pass

    emit_action_receipt("brief", exit_code=0, metadata={"systems_checked": 3})
    return 0
