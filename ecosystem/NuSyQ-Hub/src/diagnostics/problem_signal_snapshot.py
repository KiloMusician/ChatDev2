#!/usr/bin/env python3
"""Problem Signal Snapshot - align VS Code problem counts with tool diagnostics.

This snapshot captures multiple "views" of problems:
- Human/VS Code reported totals (manual or file-based)
- Tool exports (ruff/mypy/pylint export file, if present)
- Optional ruff scan (explicit flag)

Outputs: JSON + Markdown reports under docs/Reports/diagnostics/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_SUBDIR = Path("docs") / "Reports" / "diagnostics"
DEFAULT_VSCODE_COUNTS_FILE = DEFAULT_OUTPUT_SUBDIR / "vscode_problem_counts.json"

try:
    from src.utils.repo_path_resolver import get_repo_path
except Exception:
    get_repo_path = None


@dataclass(frozen=True)
class RepoInfo:
    name: str
    path: Path | None


def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _safe_read_json(path: Path) -> dict[str, Any] | None:
    try:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return data
    except Exception:
        return None


def _safe_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _load_vscode_counts(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    data = _safe_read_json(path)
    if not isinstance(data, dict):
        return None
    return data


def _write_vscode_counts(path: Path, counts: dict[str, Any]) -> None:
    payload = {
        "source": counts.get("source", "manual"),
        "timestamp": datetime.now().isoformat(),
        "counts": counts.get("counts", {}),
        "note": counts.get("note", ""),
    }
    _safe_write_json(path, payload)


def _extract_diagnostics_counts(counts_path: Path) -> dict[str, Any] | None:
    data = _safe_read_json(counts_path)
    if not isinstance(data, dict):
        return None

    if isinstance(data.get("counts"), dict):
        counts_obj = data["counts"]
        counts = {
            "errors": int(counts_obj.get("errors", 0)),
            "warnings": int(counts_obj.get("warnings", 0)),
            "infos": int(counts_obj.get("infos", 0)),
            "total": int(counts_obj.get("total", 0)),
        }
        return {
            "source": str(data.get("source", "diagnostics_counts")),
            "path": str(counts_path),
            "counts": counts,
        }

    by_category = data.get("by_category", {})
    if isinstance(by_category, dict):
        counts = {
            "errors": int(by_category.get("errors", 0)),
            "warnings": int(by_category.get("warnings", 0)),
            "infos": int(by_category.get("info", 0)),
            "total": int(data.get("total_issues", 0)),
        }
        return {
            "source": "diagnostics_export",
            "path": str(counts_path),
            "counts": counts,
        }
    return None


def _find_counts_file(repo_root: Path) -> Path | None:
    candidates = [
        repo_root / "docs" / "Reports" / "diagnostics" / "vscode_problem_counts_tooling.json",
        repo_root / "docs" / "Reports" / "diagnostics" / "vscode_problem_counts.json",
        repo_root / "docs" / "Reports" / "diagnostics" / "vscode_diagnostics_export.json",
        repo_root / "data" / "diagnostics" / "vscode_diagnostics_export.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _run_ruff_counts(repo_root: Path) -> dict[str, Any] | None:
    targets = []
    for name in ("src", "tests", "scripts"):
        candidate = repo_root / name
        if candidate.exists():
            targets.append(str(candidate))
    if not targets:
        return None

    try:
        result = subprocess.run(
            ["ruff", "check", "--output-format=json", *targets],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {
            "source": "ruff",
            "error": "ruff_unavailable_or_timeout",
            "counts": None,
        }

    if not result.stdout:
        return {
            "source": "ruff",
            "counts": {"errors": 0, "warnings": 0, "infos": 0, "total": 0},
        }

    try:
        issues = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "source": "ruff",
            "error": "ruff_invalid_json",
            "counts": None,
        }

    total = len(issues)
    counts = {"errors": 0, "warnings": total, "infos": 0, "total": total}
    return {
        "source": "ruff",
        "counts": counts,
        "targets": targets,
    }


def _aggregate_counts(entries: list[dict[str, Any]]) -> dict[str, int]:
    totals = {"errors": 0, "warnings": 0, "infos": 0, "total": 0}
    for entry in entries:
        counts = entry.get("counts")
        if not isinstance(counts, dict):
            continue
        for key in totals:
            totals[key] += int(counts.get(key, 0))
    return totals


def _snapshot_fingerprint(snapshot: dict[str, Any]) -> str:
    vscode_counts_obj = snapshot.get("vscode_counts")
    vscode_counts = (
        vscode_counts_obj.get("counts", {}) if isinstance(vscode_counts_obj, dict) else {}
    )
    repo_view = []
    for repo in snapshot.get("repos", []):
        if not isinstance(repo, dict):
            continue
        repo_view.append(
            {
                "name": str(repo.get("name", "")),
                "present": bool(repo.get("present", False)),
                "summary_counts": repo.get("summary_counts", {}),
            }
        )
    payload = {
        "vscode_counts": vscode_counts,
        "aggregate": snapshot.get("aggregate", {}),
        "repos": sorted(repo_view, key=lambda item: item.get("name", "")),
        "notes": snapshot.get("notes", []),
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _prune_snapshot_history(output_dir: Path, keep_count: int) -> None:
    if keep_count <= 0:
        return
    history = sorted(
        [
            path
            for path in output_dir.glob("problem_signal_snapshot_*.json")
            if path.name != "problem_signal_snapshot_latest.json"
        ],
        key=lambda p: p.stat().st_mtime if p.exists() else 0.0,
        reverse=True,
    )
    for stale_json in history[keep_count:]:
        stale_md = stale_json.with_suffix(".md")
        try:
            stale_json.unlink()
        except OSError:
            continue
        try:
            if stale_md.exists():
                stale_md.unlink()
        except OSError:
            continue


def _build_repo_view(
    repo: RepoInfo,
    include_exports: bool,
    run_ruff: bool,
) -> dict[str, Any]:
    view: dict[str, Any] = {
        "name": repo.name,
        "path": str(repo.path) if repo.path else None,
        "present": bool(repo.path and repo.path.exists()),
        "sources": [],
    }
    if not repo.path or not repo.path.exists():
        return view

    if include_exports:
        counts_path = _find_counts_file(repo.path)
        if counts_path:
            counts_view = _extract_diagnostics_counts(counts_path)
            if counts_view:
                view["sources"].append(counts_view)
        else:
            view["sources"].append(
                {
                    "source": "diagnostics_export",
                    "missing": True,
                }
            )

    if run_ruff:
        view["sources"].append(
            _run_ruff_counts(repo.path)
            or {
                "source": "ruff",
                "missing": True,
            }
        )

    view["summary_counts"] = _aggregate_counts(view["sources"])
    return view


def _render_markdown(snapshot: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Problem Signal Snapshot\n\n")
    lines.append(f"- Timestamp: {snapshot.get('timestamp')}\n")
    lines.append(f"- Run ID: {snapshot.get('run_id')}\n")
    lines.append("\n## VS Code (Human) Counts\n")
    vscode = snapshot.get("vscode_counts")
    if vscode and vscode.get("counts"):
        counts = vscode["counts"]
        lines.append(
            f"- Errors: {counts.get('errors')}, "
            f"Warnings: {counts.get('warnings')}, "
            f"Infos: {counts.get('infos')}, "
            f"Total: {counts.get('total')}\n"
        )
        if vscode.get("source"):
            lines.append(f"- Source: {vscode.get('source')}\n")
        if vscode.get("note"):
            lines.append(f"- Note: {vscode.get('note')}\n")
    else:
        lines.append("- No VS Code counts provided.\n")

    lines.append("\n## Repo Views\n")
    for repo in snapshot.get("repos", []):
        lines.append(f"### {repo.get('name')}\n")
        lines.append(f"- Path: {repo.get('path')}\n")
        lines.append(f"- Present: {repo.get('present')}\n")
        summary = repo.get("summary_counts", {})
        lines.append(
            f"- Summary: errors={summary.get('errors', 0)}, "
            f"warnings={summary.get('warnings', 0)}, "
            f"infos={summary.get('infos', 0)}, "
            f"total={summary.get('total', 0)}\n"
        )
        sources = repo.get("sources", [])
        for source in sources:
            source_name = source.get("source", "unknown")
            if source.get("missing"):
                lines.append(f"  - {source_name}: missing\n")
                continue
            counts = source.get("counts")
            if isinstance(counts, dict):
                lines.append(
                    f"  - {source_name}: errors={counts.get('errors', 0)}, "
                    f"warnings={counts.get('warnings', 0)}, "
                    f"infos={counts.get('infos', 0)}, "
                    f"total={counts.get('total', 0)}\n"
                )
            if source.get("path"):
                lines.append(f"    - Path: {source.get('path')}\n")

    lines.append("\n## Aggregate (Tool View)\n")
    aggregate = snapshot.get("aggregate", {})
    lines.append(
        f"- Errors: {aggregate.get('errors', 0)}, "
        f"Warnings: {aggregate.get('warnings', 0)}, "
        f"Infos: {aggregate.get('infos', 0)}, "
        f"Total: {aggregate.get('total', 0)}\n"
    )

    notes = snapshot.get("notes", [])
    if notes:
        lines.append("\n## Notes\n")
        for note in notes:
            lines.append(f"- {note}\n")

    return "".join(lines)


def run_snapshot(
    repos: list[RepoInfo],
    run_id: str,
    vscode_counts_path: Path,
    vscode_counts_override: dict[str, Any] | None,
    include_exports: bool,
    run_ruff: bool,
    output_dir: Path,
    write_latest: bool,
) -> dict[str, Any]:
    notes: list[str] = []
    if vscode_counts_override:
        _write_vscode_counts(vscode_counts_path, vscode_counts_override)

    vscode_counts = _load_vscode_counts(vscode_counts_path)
    if not vscode_counts:
        notes.append("No VS Code counts file found or provided.")

    repo_views = []
    for repo in repos:
        repo_views.append(_build_repo_view(repo, include_exports, run_ruff))

    aggregate = _aggregate_counts(
        [source for repo in repo_views for source in repo.get("sources", [])]
    )

    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "run_id": run_id,
        "vscode_counts": vscode_counts,
        "repos": repo_views,
        "aggregate": aggregate,
        "notes": notes,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = _now_stamp()
    json_path = output_dir / f"problem_signal_snapshot_{stamp}.json"
    md_path = output_dir / f"problem_signal_snapshot_{stamp}.md"
    latest_json = output_dir / "problem_signal_snapshot_latest.json"
    latest_md = output_dir / "problem_signal_snapshot_latest.md"
    rendered_markdown = _render_markdown(snapshot)

    try:
        keep_history = int(os.getenv("NUSYQ_PROBLEM_SNAPSHOT_HISTORY_KEEP", "14"))
    except ValueError:
        keep_history = 14
    write_history = str(os.getenv("NUSYQ_PROBLEM_SNAPSHOT_WRITE_HISTORY", "1")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    skip_unchanged_history = str(
        os.getenv("NUSYQ_PROBLEM_SNAPSHOT_SKIP_UNCHANGED_HISTORY", "1")
    ).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    refresh_latest = str(
        os.getenv("NUSYQ_PROBLEM_SNAPSHOT_REFRESH_LATEST", "1")
    ).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    latest_snapshot = _safe_read_json(latest_json) if latest_json.exists() else None
    unchanged = isinstance(latest_snapshot, dict) and (
        _snapshot_fingerprint(latest_snapshot) == _snapshot_fingerprint(snapshot)
    )

    write_timestamped = write_history and (
        not skip_unchanged_history or not unchanged or not latest_json.exists()
    )
    if write_timestamped:
        _safe_write_json(json_path, snapshot)
        md_path.write_text(rendered_markdown, encoding="utf-8")
    elif latest_json.exists() and latest_md.exists():
        json_path = latest_json
        md_path = latest_md
    else:
        _safe_write_json(json_path, snapshot)
        md_path.write_text(rendered_markdown, encoding="utf-8")

    outputs = {
        "status": "success",
        "json_report": str(json_path),
        "md_report": str(md_path),
        "vscode_counts_path": (str(vscode_counts_path) if vscode_counts_path.exists() else None),
        "snapshot": snapshot,
    }

    if write_latest and (
        refresh_latest or not skip_unchanged_history or not unchanged or not latest_json.exists()
    ):
        _safe_write_json(latest_json, snapshot)
        latest_md.write_text(rendered_markdown, encoding="utf-8")
    if write_latest and latest_json.exists() and latest_md.exists():
        outputs["latest_json"] = str(latest_json)
        outputs["latest_md"] = str(latest_md)

    if write_history:
        _prune_snapshot_history(output_dir, keep_count=max(1, keep_history))

    return outputs


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate problem signal snapshot")
    parser.add_argument("--run-ruff", action="store_true", help="Run ruff scan for counts")
    parser.add_argument("--no-exports", action="store_true", help="Skip diagnostics exports")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_SUBDIR), help="Output directory")
    parser.add_argument("--no-latest", action="store_true", help="Do not write latest files")
    parser.add_argument("--vscode-counts-path", default=str(DEFAULT_VSCODE_COUNTS_FILE))
    parser.add_argument("--vscode-errors", type=int)
    parser.add_argument("--vscode-warnings", type=int)
    parser.add_argument("--vscode-infos", type=int)
    parser.add_argument("--vscode-total", type=int)
    parser.add_argument("--vscode-source", default="manual")
    parser.add_argument("--vscode-note", default="")
    return parser.parse_args(args)


def build_vscode_override(parsed: argparse.Namespace) -> dict[str, Any] | None:
    if (
        parsed.vscode_errors is None
        and parsed.vscode_warnings is None
        and parsed.vscode_infos is None
        and parsed.vscode_total is None
    ):
        return None
    counts = {
        "errors": parsed.vscode_errors or 0,
        "warnings": parsed.vscode_warnings or 0,
        "infos": parsed.vscode_infos or 0,
        "total": parsed.vscode_total or 0,
    }
    return {
        "source": parsed.vscode_source,
        "counts": counts,
        "note": parsed.vscode_note,
    }


def main(args: list[str] | None = None) -> int:
    parsed = parse_args(args)
    output_dir = Path(parsed.output_dir)
    vscode_counts_path = Path(parsed.vscode_counts_path)
    vscode_override = build_vscode_override(parsed)
    repos = []
    if get_repo_path:
        for name, key in (
            ("NuSyQ-Hub", "NUSYQ_HUB_ROOT"),
            ("SimulatedVerse", "SIMULATEDVERSE_ROOT"),
            ("NuSyQ", "NUSYQ_ROOT"),
        ):
            try:
                repos.append(RepoInfo(name, get_repo_path(key)))
            except Exception:
                repos.append(RepoInfo(name, None))
    else:
        repos = [RepoInfo("NuSyQ-Hub", Path.cwd())]

    result = run_snapshot(
        repos=repos,
        run_id="run_cli",
        vscode_counts_path=vscode_counts_path,
        vscode_counts_override=vscode_override,
        include_exports=not parsed.no_exports,
        run_ruff=parsed.run_ruff,
        output_dir=output_dir,
        write_latest=not parsed.no_latest,
    )

    logger.info(result["md_report"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
