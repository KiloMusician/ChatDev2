"""Treasure Remediation Pipeline.

Consumes latest classified maze summary JSON and produces a prioritized
remediation action plan markdown file.

Usage:
    python src/tools/treasure_pipeline.py --plan

Outputs:
    docs/reports/treasure_action_plan.md

The pipeline groups findings:
- Critical defects (severity=critical)
- High remediation items (severity=high)
- Top maintenance hotspots (directories with most moderate items)

Future extensions:
- MultiAI orchestrator task submission
- Heuristic false-positive pruning
- Age tracking (via git blame integration)
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast

# NOTE: Historical path used lowercase 'reports'; aggregators expect 'Reports'.
# We write to both for backward compatibility.
LEGACY_REPORTS_DIR = Path("docs/reports")
REPORTS_DIR = Path("docs/Reports")
ACTION_PLAN_FILENAME = "treasure_action_plan.md"
ISSUE_STUBS_FILENAME = "treasure_issue_stubs.md"
PLAN_PATH = REPORTS_DIR / ACTION_PLAN_FILENAME
ISSUE_STUBS_PATH = REPORTS_DIR / ISSUE_STUBS_FILENAME
LOG_DIR = Path("logs")


def load_latest_summary() -> dict[str, Any]:
    if not LOG_DIR.exists():
        msg = "logs directory missing; run maze_solver first"
        raise FileNotFoundError(msg)
    summaries = sorted(LOG_DIR.glob("maze_summary_*.json"), key=lambda p: p.stat().st_mtime)
    if not summaries:
        msg = "No maze summary JSON files found"
        raise FileNotFoundError(msg)
    latest = summaries[-1]
    data = cast("dict[str, Any]", json.loads(latest.read_text(encoding="utf-8")))
    if not data.get("classified"):
        msg = "Latest summary not classified; re-run maze_solver with --classify"
        raise ValueError(msg)
    return data


SEVERITY_ORDER: tuple[str, ...] = ("info", "low", "moderate", "high", "critical")


def prioritize_items(
    items: list[dict[str, Any]],
    *,
    min_severity: str = "low",
) -> dict[str, list[dict[str, Any]]]:
    """Group and sort items by severity, applying a minimum severity filter.

    Args:
        items: Classified items from maze summary.
        min_severity: Minimum severity to include (info|low|moderate|high|critical).

    """
    try:
        min_idx = SEVERITY_ORDER.index(min_severity)
    except ValueError:
        min_idx = 1  # default to 'low'
    # Only include groups that meet the minimum severity threshold

    def include(sev: str) -> bool:
        try:
            return SEVERITY_ORDER.index(sev) >= min_idx
        except ValueError:
            return False

    critical = [i for i in items if i.get("severity") == "critical"] if include("critical") else []
    high = [i for i in items if i.get("severity") == "high"] if include("high") else []
    moderate = [i for i in items if i.get("severity") == "moderate"] if include("moderate") else []
    # Sort by path then line number for determinism
    critical.sort(key=lambda x: (x.get("path"), x.get("line_no", 0)))
    high.sort(key=lambda x: (x.get("path"), x.get("line_no", 0)))
    moderate.sort(key=lambda x: (x.get("path"), x.get("line_no", 0)))
    return {
        "critical": critical,
        "high": high,
        "moderate": moderate,
    }


def build_plan(data: dict[str, Any], *, min_severity: str = "low", limit: int = 25) -> str:
    items = data.get("items", [])
    hotspots = data.get("hotspots_by_dir", {})
    counts_by_pattern = data.get("counts_by_pattern", {})
    counts_by_severity = data.get("counts_by_severity", {})
    tiers = prioritize_items(items, min_severity=min_severity)
    timestamp = datetime.now().isoformat()

    def fmt_item(it: dict[str, Any]) -> str:
        snippet = it.get("line", "")[:140].replace("\n", " ")
        sev = (it.get("severity") or "").upper()
        path_str = it.get("path") or ""
        root = data.get("root") or ""
        try:
            p = Path(path_str)
            abs_path = p if p.is_absolute() else Path(root) / p
            link_path = str(abs_path).replace("\\", "/")
        except (OSError, ValueError):
            link_path = path_str.replace("\\", "/")
        line_no = it.get("line_no")
        return f"- {path_str}:{line_no} [{sev} {it.get('pattern')}] {snippet} [Open](vscode://file/{link_path}:{line_no})"

    plan = [
        "# NuSyQ-Hub Treasure Remediation Action Plan",
        f"Generated: {timestamp}",
        "",
        "## Summary",
        f"Total Findings: {data.get('total')}",
        f"Patterns: {', '.join(f'{k}={v}' for k, v in counts_by_pattern.items())}",
        f"Severity Distribution: {', '.join(f'{k}={v}' for k, v in counts_by_severity.items())}",
        "",
        f"## 1. Critical Defects (top {limit})",
    ]
    for it in tiers["critical"][:limit]:
        plan.append(fmt_item(it))
    if not tiers["critical"]:
        plan.append("(none detected)")

    plan.extend(
        [
            "",
            f"## 2. High Severity Remediation (top {limit})",
        ],
    )
    for it in tiers["high"][:limit]:
        plan.append(fmt_item(it))
    if not tiers["high"]:
        plan.append("(none detected)")

    plan.extend(
        [
            "",
            "## 3. Directory Hotspots (top 10)",
        ],
    )
    for d, count in sorted(hotspots.items(), key=lambda kv: kv[1], reverse=True):
        plan.append(f"- {d} : {count} findings")
    if not hotspots:
        plan.append("(none)")

    plan.extend(
        [
            "",
            f"## 4. Maintenance Queue (sample {min(limit, 50)} moderate)",
        ],
    )
    for it in tiers["moderate"][: min(limit, 50)]:
        plan.append(fmt_item(it))
    if not tiers["moderate"]:
        plan.append("(none)")

    plan.extend(
        [
            "",
            "## 5. Recommended Next Steps",
            "1. Address critical defects (defect category) first; validate with targeted tests.",
            "2. Batch high severity FIXMEs into focused refactor PRs.",
            "3. Convert lingering TODO clusters in hotspot dirs into tracked GitHub issues.",
            "4. Integrate MultiAI orchestrator to parallelize remediation suggestions.",
            "5. Add or update classification tests to lock behavior.",
            "",
            "---",
            "Generated automatically by treasure_pipeline.py",
        ],
    )
    return "\n".join(plan)


def write_plan(plan: str) -> Path:
    # primary
    PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLAN_PATH.write_text(plan, encoding="utf-8")
    # legacy mirror
    LEGACY_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (LEGACY_REPORTS_DIR / "treasure_action_plan.md").write_text(plan, encoding="utf-8")
    return PLAN_PATH


def write_issue_stubs(data: dict[str, Any], *, min_severity: str = "high") -> Path:
    """Generate GitHub issue stub markdown for critical/high items.

    Args:
        data: Classified summary JSON
        min_severity: Minimum severity to include in issues (default: high)

    """
    items = data.get("items", [])
    sev_order = list(SEVERITY_ORDER)
    try:
        min_idx = sev_order.index(min_severity)
    except ValueError:
        min_idx = sev_order.index("high")

    def include(it: dict[str, Any]) -> bool:
        sev = it.get("severity", "")
        try:
            return sev_order.index(sev) >= min_idx
        except ValueError:
            return False

    selected = [it for it in items if include(it)]
    stub_lines = [
        "# Treasure Issue Stubs",
        f"Generated: {datetime.now().isoformat()}",
        "This file lists suggested GitHub issues for high-impact findings (auto-generated).",
        "",
    ]
    for it in selected:
        path = it.get("path")
        ln = it.get("line_no")
        sev = it.get("severity")
        pat = it.get("pattern")
        line = (it.get("line") or "").strip()
        title = f"[{sev.upper()}][{pat}] {path}:{ln}"
        stub_lines.extend(
            [
                f"## {title}",
                "**Summary**:",
                f"- File: `{path}` line {ln}",
                f"- Pattern: `{pat}`",
                f"- Severity: `{sev}`",
                f"- Snippet: `{line[:160]}`",
                "**Suggested Next Step**: Provide concrete fix description and convert to tracked issue.",
                "",
            ],
        )
    ISSUE_STUBS_PATH.parent.mkdir(parents=True, exist_ok=True)
    ISSUE_STUBS_PATH.write_text("\n".join(stub_lines), encoding="utf-8")
    # legacy mirror
    legacy_issue_path = LEGACY_REPORTS_DIR / "treasure_issue_stubs.md"
    legacy_issue_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_issue_path.write_text("\n".join(stub_lines), encoding="utf-8")
    return ISSUE_STUBS_PATH


# ---------------- Multi-Repo Seeding ---------------- #
PLACEHOLDER_FEATURES = "TREASURE_PIPELINE_FEATURES.md"
SCAN_SUMMARY_NAME = "treasure_scan_summary.json"


def _write_if_absent(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def seed_repo_artifacts(repo_root: Path) -> dict[str, Any]:
    """Seed missing treasure artifacts in a target repository without overwriting existing files.

    This enables multi-repo aggregation to compare baselines even where the pipeline
    hasn't been run yet. Generates minimal placeholder severity bullets.
    """
    reports_dir = repo_root / "docs" / "Reports"
    created: dict[str, bool] = {}
    timestamp = datetime.now().isoformat()
    # Action plan placeholder
    action_placeholder = [
        "# Placeholder Action Plan",
        f"Generated seed: {timestamp}",
        "",
        "- CRITICAL sample critical item",
        "- HIGH sample high item",
        "- MEDIUM sample moderate item",
        "- LOW sample low item",
        "- INFO sample info item",
        "",
        "(Seeded placeholder; run maze_solver + treasure_pipeline for real data)",
    ]
    created[ACTION_PLAN_FILENAME] = _write_if_absent(
        reports_dir / ACTION_PLAN_FILENAME,
        "\n".join(action_placeholder),
    )
    # Issue stubs placeholder
    issue_placeholder = [
        "# Placeholder Issue Stubs",
        f"Generated seed: {timestamp}",
        "",
        "## [CRITICAL][sample] path/to/file.py:10",
        "- File: path/to/file.py line 10",
        "- Pattern: sample",
        "- Severity: critical",
        "- Snippet: sample snippet",
        "",
    ]
    created[ISSUE_STUBS_FILENAME] = _write_if_absent(
        reports_dir / ISSUE_STUBS_FILENAME,
        "\n".join(issue_placeholder),
    )
    # Features doc placeholder
    features_placeholder = [
        "# Treasure Pipeline Features (Placeholder)",
        f"Generated seed: {timestamp}",
        "Run pipeline locally to populate real feature inventory.",
    ]
    created[PLACEHOLDER_FEATURES] = _write_if_absent(
        reports_dir / PLACEHOLDER_FEATURES,
        "\n".join(features_placeholder),
    )
    # Scan summary placeholder at repo root
    summary_path = repo_root / SCAN_SUMMARY_NAME
    if not summary_path.exists():
        summary_path.write_text(
            json.dumps(
                {
                    "seed": True,
                    "generated_at": timestamp,
                    "classified": True,
                    "items": [],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        created[SCAN_SUMMARY_NAME] = True
    else:
        created[SCAN_SUMMARY_NAME] = False
    return {"repo": str(repo_root), "created": created}


def seed_multi_repo(targets: list[Path]) -> list[dict[str, Any]]:
    results: list[Any] = []
    for root in targets:
        try:
            results.append(seed_repo_artifacts(root))
        except OSError as e:
            results.append({"repo": str(root), "error": str(e)})
    return results


def run(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate treasure remediation artifacts")
    parser.add_argument("--plan", action="store_true", help="Generate action plan")
    parser.add_argument(
        "--issues",
        action="store_true",
        help="Generate issue stub markdown for high-impact findings",
    )
    parser.add_argument(
        "--seed-multi-repo",
        action="store_true",
        help="Seed placeholder treasure artifacts in sibling repositories",
    )
    parser.add_argument(
        "--seed-targets",
        nargs="*",
        help="Explicit repository roots to seed (defaults to SimulatedVerse & NuSyQ root)",
    )
    parser.add_argument(
        "--min-severity",
        choices=list(SEVERITY_ORDER),
        default="low",
        help="Minimum severity to include in plan",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Max items per section (critical/high) and sample size for moderate",
    )
    parser.add_argument(
        "--issue-min-severity",
        choices=list(SEVERITY_ORDER),
        default="high",
        help="Minimum severity for issue stubs",
    )
    args = parser.parse_args(argv)
    if not (args.plan or args.issues or args.seed_multi_repo):
        return 1
    try:
        data = load_latest_summary()
    except (FileNotFoundError, ValueError):
        return 2
    if args.plan:
        plan = build_plan(data, min_severity=args.min_severity, limit=args.limit)
        write_plan(plan)
    if args.issues:
        write_issue_stubs(data, min_severity=args.issue_min_severity)
    if args.seed_multi_repo:
        if args.seed_targets:
            targets = [Path(p) for p in args.seed_targets]
        else:
            targets = [
                Path(r"..\..\SimulatedVerse\SimulatedVerse"),
                Path(r"..\..\..\NuSyQ"),
            ]
        seed_multi_repo(targets)
    return 0


if __name__ == "__main__":  # pragma: no cover
    run()
