"""Report Aggregator.

Aggregates treasure scanning outputs (action plan, issue stubs, feature docs) and
latest agent session logs into a structured insight model for downstream
orchestration (MultiAIOrchestrator, consciousness bridge, etc.).

Designed to answer the question: "Are we actually reading and using the logs and
reports we create?" by producing a synthesized view combining counts, recency,
and prioritized next actions.

Usage:
    python -m src.tools.report_aggregator
    python src/tools/report_aggregator.py --markdown --json

Outputs (if present):
    docs/Reports/aggregated_insights.md
    docs/Reports/aggregated_insights.json

Safe to run if files missing; missing components are noted.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast

try:
    from datetime import UTC
except ImportError:  # Python <3.11
    from datetime import timezone

    UTC = timezone.utc  # noqa: UP017

DOCS_DIR = Path("docs")
REPORTS_DIR = DOCS_DIR / "Reports"
AGENT_SESSIONS_DIR = DOCS_DIR / "Agent-Sessions"

ACTION_PLAN_FILE = REPORTS_DIR / "treasure_action_plan.md"
ISSUE_STUBS_FILE = REPORTS_DIR / "treasure_issue_stubs.md"
FEATURES_FILE = REPORTS_DIR / "TREASURE_PIPELINE_FEATURES.md"
SUMMARY_JSON_FILE = Path("treasure_scan_summary.json")  # typical output of maze_solver

AGGREGATED_JSON = REPORTS_DIR / "aggregated_insights.json"
AGGREGATED_MD = REPORTS_DIR / "aggregated_insights.md"
AGGREGATED_DELTA_JSON = REPORTS_DIR / "aggregated_insights_delta.json"
AGGREGATED_DELTA_MD = REPORTS_DIR / "aggregated_insights_delta.md"
HISTORY_FILE = REPORTS_DIR / "aggregated_history.jsonl"

SEVERITY_LEVELS = ["critical", "high", "medium", "low", "info"]


@dataclass
class SeverityCounts:
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0

    def to_sorted_items(self) -> list[tuple[str, int]]:
        return [(s, getattr(self, s)) for s in SEVERITY_LEVELS if getattr(self, s)]


@dataclass
class AggregatedInsights:
    generated_at: str
    action_plan_present: bool
    issue_stubs_present: bool
    features_doc_present: bool
    summary_json_present: bool
    latest_session_log: str | None
    latest_session_log_path: str | None
    total_session_logs: int
    action_plan_counts: SeverityCounts
    issue_stub_counts: SeverityCounts
    prioritized_next_actions: list[str]
    missing_components: list[str]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        # Expand dataclass severity counts -> dict
        data["action_plan_counts"] = asdict(self.action_plan_counts)
        data["issue_stub_counts"] = asdict(self.issue_stub_counts)
        return data


def _read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


def _extract_severity_counts(md: str) -> SeverityCounts:
    counts = SeverityCounts()
    # crude pattern: lines starting with '-' and containing severity tokens
    for line in md.splitlines():
        if not line.lstrip().startswith("-"):
            continue
        lowered = line.lower()
        for sev in SEVERITY_LEVELS:
            # ensure whole word match boundaries
            if re.search(rf"\b{sev}\b", lowered):
                current = getattr(counts, sev)
                setattr(counts, sev, current + 1)
                break
    return counts


def _latest_session_log() -> tuple[str | None, str | None, int]:
    if not AGENT_SESSIONS_DIR.exists():
        return None, None, 0
    session_files = sorted(
        AGENT_SESSIONS_DIR.glob("SESSION_*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not session_files:
        return None, None, 0
    latest = session_files[0]
    text = _read_text(latest)
    return text, str(latest), len(session_files)


def _derive_prioritized_actions(
    action_counts: SeverityCounts,
    issue_counts: SeverityCounts,
) -> list[str]:
    prioritized: list[str] = []
    # Highest severity first; simple heuristic: if critical items exist, escalate remediation tasks
    if action_counts.critical or issue_counts.critical:
        prioritized.append(
            "Execute remediation sprint for all critical findings (create real issues, assign owners).",
        )
    if action_counts.high + issue_counts.high > 10:
        prioritized.append(
            "Batch triage high severity items: cluster by module and schedule fixes.",
        )
    if action_counts.medium + issue_counts.medium > 50:
        prioritized.append(
            "Introduce automated suppression or tagging for medium items to avoid overwhelm.",
        )
    if not prioritized:
        prioritized.append("Maintain monitoring cadence; no escalations required.")
    return prioritized


def aggregate_insights() -> AggregatedInsights:
    now = datetime.now(UTC).isoformat()

    action_md = _read_text(ACTION_PLAN_FILE)
    issue_md = _read_text(ISSUE_STUBS_FILE)
    features_md = _read_text(FEATURES_FILE)
    summary_json = _read_text(SUMMARY_JSON_FILE)

    action_counts = _extract_severity_counts(action_md) if action_md else SeverityCounts()
    issue_counts = _extract_severity_counts(issue_md) if issue_md else SeverityCounts()

    latest_session_text, latest_session_path, total_session_logs = _latest_session_log()

    missing: list[str] = []
    for label, present in [
        ("treasure_action_plan.md", action_md is not None),
        ("treasure_issue_stubs.md", issue_md is not None),
        ("TREASURE_PIPELINE_FEATURES.md", features_md is not None),
        ("treasure_scan_summary.json", summary_json is not None),
    ]:
        if not present:
            missing.append(label)

    notes: list[str] = []
    if latest_session_text:
        notes.append("Latest session log ingested for context alignment.")
    if not latest_session_text:
        notes.append("No session log available or readable; context continuity limited.")
    if missing:
        notes.append(
            "Some expected artifacts are missing; run treasure pipeline and maze scanner if stale.",
        )

    prioritized = _derive_prioritized_actions(action_counts, issue_counts)

    return AggregatedInsights(
        generated_at=now,
        action_plan_present=action_md is not None,
        issue_stubs_present=issue_md is not None,
        features_doc_present=features_md is not None,
        summary_json_present=summary_json is not None,
        latest_session_log=(
            latest_session_text[:5000] if latest_session_text else None
        ),  # truncate
        latest_session_log_path=latest_session_path,
        total_session_logs=total_session_logs,
        action_plan_counts=action_counts,
        issue_stub_counts=issue_counts,
        prioritized_next_actions=prioritized,
        missing_components=missing,
        notes=notes,
    )


# ---------------- Delta Computation ---------------- #
def _load_previous_snapshot() -> dict[str, Any] | None:
    """Load previous aggregated snapshot JSON if present."""
    if not AGGREGATED_JSON.exists():
        return None
    try:
        return cast("dict[str, Any]", json.loads(AGGREGATED_JSON.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return None


def _severity_delta(current: SeverityCounts, previous: dict[str, Any] | None) -> dict[str, int]:
    delta: dict[str, int] = {}
    for sev in SEVERITY_LEVELS:
        prev_val = 0
        if previous and isinstance(previous.get("action_plan_counts"), dict):
            prev_val = previous["action_plan_counts"].get(sev, 0)
        delta[sev] = getattr(current, sev) - prev_val
    return delta


def _severity_delta_issue(
    current: SeverityCounts,
    previous: dict[str, Any] | None,
) -> dict[str, int]:
    delta: dict[str, int] = {}
    for sev in SEVERITY_LEVELS:
        prev_val = 0
        if previous and isinstance(previous.get("issue_stub_counts"), dict):
            prev_val = previous["issue_stub_counts"].get(sev, 0)
        delta[sev] = getattr(current, sev) - prev_val
    return delta


def compute_delta(current: AggregatedInsights, previous: dict[str, Any] | None) -> dict[str, Any]:
    first_run = previous is None
    newly_missing, recovered = _artifact_diffs(current, previous)
    action_delta = _severity_delta(current.action_plan_counts, previous)
    issue_delta = _severity_delta_issue(current.issue_stub_counts, previous)
    session_log_delta = _session_delta(current, previous)
    trend_lines = _build_trends(
        first_run,
        action_delta,
        issue_delta,
        newly_missing,
        recovered,
        session_log_delta,
    )
    urgency_score = _compute_urgency(current, newly_missing, recovered, session_log_delta)
    return {
        "generated_at": current.generated_at,
        "baseline_generated_at": previous.get("generated_at") if previous else None,
        "first_run": first_run,
        "action_plan_severity_delta": action_delta,
        "issue_stub_severity_delta": issue_delta,
        "newly_missing_artifacts": newly_missing,
        "recovered_artifacts": recovered,
        "session_logs_delta": session_log_delta,
        "trend_summary": trend_lines,
        "urgency_score": urgency_score,
    }


def _artifact_diffs(
    current: AggregatedInsights,
    previous: dict[str, Any] | None,
) -> tuple[list[str], list[str]]:
    if not previous:
        return [], []
    prev_missing = set(previous.get("missing_components", []))
    curr_missing = set(current.missing_components)
    return sorted(curr_missing - prev_missing), sorted(prev_missing - curr_missing)


def _session_delta(current: AggregatedInsights, previous: dict[str, Any] | None) -> int | None:
    if previous and isinstance(previous.get("total_session_logs"), int):
        return int(current.total_session_logs - previous["total_session_logs"])
    return None


def _build_trends(
    first_run: bool,
    action_delta: dict[str, int],
    issue_delta: dict[str, int],
    newly_missing: list[str],
    recovered: list[str],
    session_log_delta: int | None,
) -> list[str]:
    lines: list[str] = []
    if first_run:
        return ["Initial aggregation baseline created; no previous snapshot for comparison."]

    def _summarize(delta_map: dict[str, int], label: str) -> None:
        non_zero = {k: v for k, v in delta_map.items() if v}
        if not non_zero:
            lines.append(f"{label}: no change")
        else:
            pos = [f"{k}+{v}" for k, v in non_zero.items() if v > 0]
            neg = [f"{k}{v}" for k, v in non_zero.items() if v < 0]
            combined = ", ".join(pos + neg)
            lines.append(f"{label}: {combined}")

    _summarize(action_delta, "Action Plan severities")
    _summarize(issue_delta, "Issue Stub severities")
    if newly_missing:
        lines.append(f"Newly missing artifacts: {', '.join(newly_missing)}")
    if recovered:
        lines.append(f"Recovered artifacts: {', '.join(recovered)}")
    if session_log_delta:
        sign = "+" if session_log_delta > 0 else ""
        lines.append(f"Session logs count delta: {sign}{session_log_delta}")
    if not lines:
        lines.append("No metric changes detected since last snapshot.")
    return lines


def _compute_urgency(
    current: AggregatedInsights,
    newly_missing: list[str],
    recovered: list[str],
    session_log_delta: int | None,
) -> int:
    # Compute components separately to satisfy style rules and improve readability.
    crit_action = current.action_plan_counts.critical * 100
    crit_issue = current.issue_stub_counts.critical * 90
    high_total = (current.action_plan_counts.high + current.issue_stub_counts.high) * 40
    medium_total = (current.action_plan_counts.medium + current.issue_stub_counts.medium) * 10
    base = crit_action + crit_issue + high_total + medium_total
    base += len(newly_missing) * 25
    base += len(recovered) * 5
    if session_log_delta:
        base += session_log_delta * 2
    return base


def _delta_markdown_lines(delta: dict[str, Any]) -> list[str]:
    lines: list[str] = [
        "# Aggregated Insights Delta",
        "",
        f"Generated: {delta['generated_at']}",
    ]
    baseline = delta.get("baseline_generated_at")
    if baseline:
        lines.append(f"Baseline: {baseline}")
    lines.append("")
    if delta.get("first_run"):
        lines.append("Initial run: no previous snapshot for comparison.")

    # Helper to add a severity block
    def _severity_block(title: str, sev_map: dict[str, int]) -> None:
        lines.append(title)
        for sev, val in sev_map.items():
            lines.append(f"- {sev}: {val:+d}")
        lines.append("")

    _severity_block("## Severity Deltas (Action Plan)", delta["action_plan_severity_delta"])
    _severity_block("## Severity Deltas (Issue Stubs)", delta["issue_stub_severity_delta"])

    def _artifact_list(title: str, items: list[str]) -> None:
        if items:
            lines.append(title)
            for art in items:
                lines.append(f"- {art}")
            lines.append("")

    _artifact_list("## Newly Missing Artifacts", delta.get("newly_missing_artifacts", []))
    _artifact_list("## Recovered Artifacts", delta.get("recovered_artifacts", []))
    if delta.get("session_logs_delta") is not None:
        lines.append("## Session Logs Delta")
        lines.append(f"Delta: {delta['session_logs_delta']:+d}")
        lines.append("")
    trend = delta.get("trend_summary", [])
    if trend:
        lines.append("## Trend Summary")
        for t in trend:
            lines.append(f"- {t}")
        lines.append("")
    lines.append(f"**Urgency Score**: {delta.get('urgency_score', 0)}")
    return lines


def write_delta_outputs(delta: dict[str, Any], write_markdown: bool, write_json: bool) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if write_json:
        AGGREGATED_DELTA_JSON.write_text(json.dumps(delta, indent=2), encoding="utf-8")
    if write_markdown:
        AGGREGATED_DELTA_MD.write_text("\n".join(_delta_markdown_lines(delta)), encoding="utf-8")


def append_history(
    insights: AggregatedInsights,
    delta: dict[str, Any],
    retention: int = 30,
) -> None:
    """Append a compact JSONL record of current snapshot + urgency; enforce retention."""
    record = {
        "ts": insights.generated_at,
        "critical_total": insights.action_plan_counts.critical
        + insights.issue_stub_counts.critical,
        "high_total": insights.action_plan_counts.high + insights.issue_stub_counts.high,
        "medium_total": insights.action_plan_counts.medium + insights.issue_stub_counts.medium,
        "missing": insights.missing_components,
        "urgency": delta.get("urgency_score", 0),
    }
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Read existing lines
    lines: list[str] = []
    if HISTORY_FILE.exists():
        try:
            lines = HISTORY_FILE.read_text(encoding="utf-8").splitlines()
        except OSError:
            lines = []
    lines.append(json.dumps(record))
    # Trim if beyond retention
    if len(lines) > retention:
        lines = lines[-retention:]
    HISTORY_FILE.write_text("\n".join(lines), encoding="utf-8")


def _format_artifact_presence(insights: AggregatedInsights) -> list[str]:
    return [
        "## Artifact Presence",
        "| Artifact | Present |",
        "|----------|---------|",
        f"| Action Plan | {'✅' if insights.action_plan_present else '❌'} |",
        f"| Issue Stubs | {'✅' if insights.issue_stubs_present else '❌'} |",
        f"| Features Doc | {'✅' if insights.features_doc_present else '❌'} |",
        f"| Summary JSON | {'✅' if insights.summary_json_present else '❌'} |",
        "",
    ]


def _severity_section(title: str, items: list[tuple[str, int]]) -> list[str]:
    lines: list[str] = [title]
    for sev, count in items:
        lines.append(f"- {sev.title()}: {count}")
    lines.append("")
    return lines


def _latest_session_block(insights: AggregatedInsights) -> list[str]:
    if not insights.latest_session_log_path:
        return []
    block: list[str] = [
        "## Latest Session Log (truncated)",
        f"Source: `{insights.latest_session_log_path}`",
        "",
    ]
    if insights.latest_session_log:
        block.append("```md")
        block.append(insights.latest_session_log)
        block.append("```")
    return block


def _insights_markdown_lines(insights: AggregatedInsights) -> list[str]:
    lines: list[str] = [
        "# Aggregated Insights",
        "",
        f"Generated: {insights.generated_at}",
        "",
    ]
    lines.extend(_format_artifact_presence(insights))
    lines.extend(
        _severity_section(
            "## Severity Counts (Action Plan)",
            insights.action_plan_counts.to_sorted_items(),
        ),
    )
    lines.extend(
        _severity_section(
            "## Severity Counts (Issue Stubs)",
            insights.issue_stub_counts.to_sorted_items(),
        ),
    )
    lines.append("## Prioritized Next Actions")
    for act in insights.prioritized_next_actions:
        lines.append(f"- {act}")
    if insights.missing_components:
        lines.append("")
        lines.append("## Missing Components")
        for m in insights.missing_components:
            lines.append(f"- {m}")
    if insights.notes:
        lines.append("")
        lines.append("## Notes")
        for n in insights.notes:
            lines.append(f"- {n}")
    session_block = _latest_session_block(insights)
    if session_block:
        lines.append("")
        lines.extend(session_block)
    return lines


def write_outputs(insights: AggregatedInsights, write_markdown: bool, write_json: bool) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if write_json:
        AGGREGATED_JSON.write_text(json.dumps(insights.to_dict(), indent=2), encoding="utf-8")
    if write_markdown:
        AGGREGATED_MD.write_text("\n".join(_insights_markdown_lines(insights)), encoding="utf-8")


def get_insights() -> dict[str, Any]:  # orchestrator callable
    return aggregate_insights().to_dict()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Aggregate treasure and session insights")
    parser.add_argument("--markdown", action="store_true", help="Write aggregated markdown report")
    parser.add_argument("--json", action="store_true", help="Write aggregated JSON output")
    parser.add_argument("--print", action="store_true", help="Print summary to stdout")
    args = parser.parse_args(argv)
    previous = _load_previous_snapshot()
    insights = aggregate_insights()
    delta = compute_delta(insights, previous)
    write_outputs(insights, write_markdown=args.markdown, write_json=args.json)
    write_delta_outputs(delta, write_markdown=args.markdown, write_json=args.json)
    append_history(insights, delta)
    if args.print:
        payload = insights.to_dict()
        payload["delta"] = delta
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
