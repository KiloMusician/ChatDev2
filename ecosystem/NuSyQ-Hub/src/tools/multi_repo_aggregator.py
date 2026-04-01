"""Multi-Repository Aggregator.

Aggregates treasure / report artifacts across multiple sibling repositories:
- NuSyQ-Hub (this repo)
- SimulatedVerse
- NuSyQ root

It reuses parsing heuristics from single-repo report_aggregator while adding a
per-repo breakdown and cross-repo prioritization.

Run:
    python src/tools/multi_repo_aggregator.py --markdown --json --print

Outputs:
    docs/Reports/multi_repo_aggregated_insights.json
    docs/Reports/multi_repo_aggregated_insights.md

If artifacts are missing in a repo, it records them rather than failing.
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

SEVERITY_LEVELS = ["critical", "high", "medium", "low", "info"]

DEFAULT_REPOS = [
    ("NuSyQ-Hub", Path()),
    ("SimulatedVerse", Path(r"..\..\SimulatedVerse\SimulatedVerse")),
    ("NuSyQ", Path(r"..\..\..\NuSyQ")),
]


ARTIFACT_FILENAMES = {
    "action_plan": "treasure_action_plan.md",
    "issue_stubs": "treasure_issue_stubs.md",
    "features": "TREASURE_PIPELINE_FEATURES.md",
    "scan_summary": "treasure_scan_summary.json",
}

HISTORY_FILE = Path("docs/Reports/multi_repo_aggregated_history.jsonl")


@dataclass
class SeverityCounts:
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0

    def add_line(self, line: str) -> None:
        lowered = line.lower()
        for sev in SEVERITY_LEVELS:
            if re.search(rf"\b{sev}\b", lowered):
                setattr(self, sev, getattr(self, sev) + 1)
                break

    def to_dict(self) -> dict[str, int]:
        return {s: getattr(self, s) for s in SEVERITY_LEVELS}


@dataclass
class RepoInsights:
    name: str
    path: str
    action_plan_present: bool
    issue_stubs_present: bool
    features_doc_present: bool
    scan_summary_present: bool
    action_plan_counts: SeverityCounts
    issue_stub_counts: SeverityCounts
    missing: list[str]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["action_plan_counts"] = self.action_plan_counts.to_dict()
        d["issue_stub_counts"] = self.issue_stub_counts.to_dict()
        return d


@dataclass
class MultiRepoAggregated:
    generated_at: str
    repos: list[RepoInsights]
    cross_repo: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "repos": [r.to_dict() for r in self.repos],
            "cross_repo": self.cross_repo,
        }


def _read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


def _extract_counts(md: str | None) -> SeverityCounts:
    counts = SeverityCounts()
    if not md:
        return counts
    for line in md.splitlines():
        if line.lstrip().startswith("-"):
            counts.add_line(line)
    return counts


def _gather_repo(repo_name: str, root: Path) -> RepoInsights:
    docs_reports = root / "docs" / "Reports"
    action_path = docs_reports / ARTIFACT_FILENAMES["action_plan"]
    issue_path = docs_reports / ARTIFACT_FILENAMES["issue_stubs"]
    feat_path = docs_reports / ARTIFACT_FILENAMES["features"]
    summary_path = root / ARTIFACT_FILENAMES["scan_summary"]  # may reside at root

    action_md = _read_text(action_path)
    issue_md = _read_text(issue_path)
    feat_md = _read_text(feat_path)
    summary_json = _read_text(summary_path)

    missing: list[str] = []
    for label, content in [
        (ARTIFACT_FILENAMES["action_plan"], action_md),
        (ARTIFACT_FILENAMES["issue_stubs"], issue_md),
        (ARTIFACT_FILENAMES["features"], feat_md),
        (ARTIFACT_FILENAMES["scan_summary"], summary_json),
    ]:
        if content is None:
            missing.append(label)

    return RepoInsights(
        name=repo_name,
        path=str(root.resolve()),
        action_plan_present=action_md is not None,
        issue_stubs_present=issue_md is not None,
        features_doc_present=feat_md is not None,
        scan_summary_present=summary_json is not None,
        action_plan_counts=_extract_counts(action_md),
        issue_stub_counts=_extract_counts(issue_md),
        missing=missing,
    )


def aggregate_multi_repo(
    repos: list[tuple[str, Path]] | None = None,
) -> MultiRepoAggregated:
    repos = repos or DEFAULT_REPOS
    collected: list[RepoInsights] = []
    for name, path in repos:
        collected.append(_gather_repo(name, path))

    # Cross-repo totals
    total_action = SeverityCounts()
    total_issue = SeverityCounts()
    for r in collected:
        for sev in SEVERITY_LEVELS:
            setattr(
                total_action,
                sev,
                getattr(total_action, sev) + getattr(r.action_plan_counts, sev),
            )
            setattr(
                total_issue,
                sev,
                getattr(total_issue, sev) + getattr(r.issue_stub_counts, sev),
            )

    prioritized: list[str] = []
    if total_action.critical + total_issue.critical > 0:
        prioritized.append("Cross-repo critical remediation sprint (assign owners per repository).")
    if total_action.high + total_issue.high > 20:
        prioritized.append("Establish cross-repo high severity triage board.")
    if (total_action.medium + total_issue.medium) > 200:
        prioritized.append(
            "Introduce tagging/deferral policy for medium items to prevent backlog fatigue.",
        )
    if not prioritized:
        prioritized.append("No cross-repo escalation required; maintain monitoring cadence.")

    cross_repo = {
        "total_action_plan_counts": total_action.to_dict(),
        "total_issue_stub_counts": total_issue.to_dict(),
        "prioritized_next_actions": prioritized,
        "repos_missing_artifacts": {r.name: r.missing for r in collected if r.missing},
    }

    return MultiRepoAggregated(
        generated_at=datetime.now(UTC).isoformat(),
        repos=collected,
        cross_repo=cross_repo,
    )


def _compute_cross_repo_urgency(
    data: MultiRepoAggregated,
    newly_missing_repos: list[str],
    recovered_repos: list[str],
) -> int:
    """Compute urgency score for multi-repo aggregation.

    Weights cross-repo totals and penalizes repos with missing artifacts.
    """
    totals_action = data.cross_repo["total_action_plan_counts"]
    totals_issue = data.cross_repo["total_issue_stub_counts"]
    # Compute components separately for style compliance
    crit_action = totals_action["critical"] * 100
    crit_issue = totals_issue["critical"] * 90
    high_total = (totals_action["high"] + totals_issue["high"]) * 40
    medium_total = (totals_action["medium"] + totals_issue["medium"]) * 10
    base = crit_action + crit_issue + high_total + medium_total
    # Penalize missing repos more heavily (cross-repo gaps are more critical)
    base += len(newly_missing_repos) * 50
    base += len(recovered_repos) * 10
    # Count total repos with missing artifacts
    repos_with_missing = len(data.cross_repo.get("repos_missing_artifacts", {}))
    base += repos_with_missing * 20
    return int(base)


def _append_multi_history(data: MultiRepoAggregated, urgency: int, retention: int = 30) -> None:
    """Append JSONL record of current multi-repo snapshot with urgency; enforce retention."""
    totals_action = data.cross_repo["total_action_plan_counts"]
    totals_issue = data.cross_repo["total_issue_stub_counts"]
    record = {
        "ts": data.generated_at,
        "critical_total": totals_action["critical"] + totals_issue["critical"],
        "high_total": totals_action["high"] + totals_issue["high"],
        "medium_total": totals_action["medium"] + totals_issue["medium"],
        "repos_with_missing": len(data.cross_repo.get("repos_missing_artifacts", {})),
        "urgency": urgency,
    }
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    if HISTORY_FILE.exists():
        try:
            lines = HISTORY_FILE.read_text(encoding="utf-8").splitlines()
        except OSError:
            lines = []
    lines.append(json.dumps(record))
    if len(lines) > retention:
        lines = lines[-retention:]
    HISTORY_FILE.write_text("\n".join(lines), encoding="utf-8")


def _format_repo_summary(repo: RepoInsights) -> list[str]:
    """Format a single repo summary block."""
    lines: list[str] = [f"### {repo.name}", f"Path: `{repo.path}`"]
    lines.append(
        f"Artifacts: ActionPlan={'✅' if repo.action_plan_present else '❌'}, "
        f"IssueStubs={'✅' if repo.issue_stubs_present else '❌'}, "
        f"Features={'✅' if repo.features_doc_present else '❌'}, "
        f"ScanSummary={'✅' if repo.scan_summary_present else '❌'}",
    )
    lines.append(
        "- Action Plan Counts: "
        + ", ".join(f"{k}:{v}" for k, v in repo.action_plan_counts.to_dict().items() if v),
    )
    lines.append(
        "- Issue Stub Counts: "
        + ", ".join(f"{k}:{v}" for k, v in repo.issue_stub_counts.to_dict().items() if v),
    )
    if repo.missing:
        lines.append("- Missing: " + ", ".join(repo.missing))
    lines.append("")
    return lines


def _build_main_markdown(data: MultiRepoAggregated) -> list[str]:
    """Build main multi-repo markdown report lines."""
    lines: list[str] = [
        "# Multi-Repository Aggregated Insights",
        "",
        f"Generated: {data.generated_at}",
        "",
    ]
    lines.append("## Cross-Repo Prioritized Actions")
    for act in data.cross_repo["prioritized_next_actions"]:
        lines.append(f"- {act}")
    lines.append("")
    lines.append("## Per-Repository Summary")
    for repo in data.repos:
        lines.extend(_format_repo_summary(repo))
    lines.append("## Cross-Repo Totals")
    for sev, cnt in data.cross_repo["total_action_plan_counts"].items():
        lines.append(f"- Action {sev}: {cnt}")
    for sev, cnt in data.cross_repo["total_issue_stub_counts"].items():
        lines.append(f"- Issue {sev}: {cnt}")
    if data.cross_repo.get("repos_missing_artifacts"):
        lines.append("")
        lines.append("## Missing Artifacts By Repo")
        for rn, miss in data.cross_repo["repos_missing_artifacts"].items():
            lines.append(f"- {rn}: {', '.join(miss)}")
    return lines


def _compute_delta_data(
    data: MultiRepoAggregated,
    previous: dict[str, Any] | None,
) -> tuple[dict[str, int], dict[str, int], list[str], list[str], int]:
    """Compute delta metrics for multi-repo aggregation."""

    def _delta_map(
        current: dict[str, int],
        prev: dict[str, Any] | None,
        key: str,
    ) -> dict[str, int]:
        result: dict[str, int] = {}
        prev_counts: dict[str, int] = {}
        if prev and isinstance(prev.get("cross_repo"), dict):
            prev_counts = prev["cross_repo"].get(key, {}) or {}
        for sev, val in current.items():
            prev_val = prev_counts.get(sev, 0)
            result[sev] = val - prev_val
        return result

    action_delta = _delta_map(
        data.cross_repo["total_action_plan_counts"],
        previous,
        "total_action_plan_counts",
    )
    issue_delta = _delta_map(
        data.cross_repo["total_issue_stub_counts"],
        previous,
        "total_issue_stub_counts",
    )
    prev_missing_repos = set()
    if previous and isinstance(previous.get("cross_repo"), dict):
        prev_missing_repos = set(previous["cross_repo"].get("repos_missing_artifacts", {}).keys())
    curr_missing_repos = set(data.cross_repo.get("repos_missing_artifacts", {}).keys())
    newly_missing_repos = sorted(curr_missing_repos - prev_missing_repos)
    recovered_repos = sorted(prev_missing_repos - curr_missing_repos)
    urgency_score = _compute_cross_repo_urgency(data, newly_missing_repos, recovered_repos)
    return (
        action_delta,
        issue_delta,
        newly_missing_repos,
        recovered_repos,
        urgency_score,
    )


def _build_delta_markdown(delta_struct: dict[str, Any]) -> list[str]:
    """Build delta markdown report lines."""
    d_lines: list[str] = [
        "# Multi-Repo Aggregated Insights Delta",
        "",
        f"Generated: {delta_struct['generated_at']}",
    ]
    baseline = delta_struct.get("baseline_generated_at")
    if baseline:
        d_lines.append(f"Baseline: {baseline}")
    d_lines.append("")
    if delta_struct.get("first_run"):
        d_lines.append("Initial run: no previous multi-repo snapshot.")
    d_lines.append("## Severity Deltas (Action Plan Totals)")
    for sev, val in delta_struct["action_plan_severity_delta"].items():
        d_lines.append(f"- {sev}: {val:+d}")
    d_lines.append("")
    d_lines.append("## Severity Deltas (Issue Stub Totals)")
    for sev, val in delta_struct["issue_stub_severity_delta"].items():
        d_lines.append(f"- {sev}: {val:+d}")
    newly_missing = delta_struct.get("newly_missing_repos", [])
    if newly_missing:
        d_lines.append("")
        d_lines.append("## Newly Missing Repos (Artifacts)")
        for r in newly_missing:
            d_lines.append(f"- {r}")
    recovered = delta_struct.get("recovered_repos", [])
    if recovered:
        d_lines.append("")
        d_lines.append("## Recovered Repos (Artifacts now present)")
        for r in recovered:
            d_lines.append(f"- {r}")
    d_lines.append("")
    d_lines.append(f"**Urgency Score**: {delta_struct.get('urgency_score', 0)}")
    return d_lines


def write_outputs(data: MultiRepoAggregated, write_markdown: bool, write_json: bool) -> None:
    reports_dir = Path("docs/Reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / "multi_repo_aggregated_insights.json"
    md_path = reports_dir / "multi_repo_aggregated_insights.md"
    delta_json_path = reports_dir / "multi_repo_aggregated_insights_delta.json"
    delta_md_path = reports_dir / "multi_repo_aggregated_insights_delta.md"

    # Load previous snapshot for delta
    previous: dict[str, Any] | None = None
    if json_path.exists():
        try:
            previous = cast("dict[str, Any]", json.loads(json_path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            previous = None

    if write_json:
        json_path.write_text(json.dumps(data.to_dict(), indent=2), encoding="utf-8")
    if write_markdown:
        md_path.write_text("\n".join(_build_main_markdown(data)), encoding="utf-8")

    # Compute delta
    action_delta, issue_delta, newly_missing_repos, recovered_repos, urgency_score = (
        _compute_delta_data(data, previous)
    )
    delta_struct: dict[str, Any] = {
        "generated_at": data.generated_at,
        "baseline_generated_at": previous.get("generated_at") if previous else None,
        "first_run": previous is None,
        "action_plan_severity_delta": action_delta,
        "issue_stub_severity_delta": issue_delta,
        "newly_missing_repos": newly_missing_repos,
        "recovered_repos": recovered_repos,
        "urgency_score": urgency_score,
    }

    if write_json:
        delta_json_path.write_text(json.dumps(delta_struct, indent=2), encoding="utf-8")
    if write_markdown:
        delta_md_path.write_text("\n".join(_build_delta_markdown(delta_struct)), encoding="utf-8")

    # Append history
    _append_multi_history(data, urgency_score)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Aggregate multi-repo insights")
    parser.add_argument("--markdown", action="store_true", help="Write markdown output")
    parser.add_argument("--json", action="store_true", help="Write JSON output")
    parser.add_argument("--print", action="store_true", help="Print JSON to stdout")
    args = parser.parse_args(argv)

    data = aggregate_multi_repo()
    write_outputs(data, write_markdown=args.markdown, write_json=args.json)
    if args.print:
        pass
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
