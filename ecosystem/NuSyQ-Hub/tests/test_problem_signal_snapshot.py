from __future__ import annotations

import json
from pathlib import Path

from src.diagnostics.problem_signal_snapshot import RepoInfo, run_snapshot


def test_problem_signal_snapshot_writes_reports(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    export_dir = repo_root / "data" / "diagnostics"
    export_dir.mkdir(parents=True)
    export_file = export_dir / "vscode_diagnostics_export.json"
    export_file.write_text(
        json.dumps(
            {
                "total_issues": 3,
                "by_category": {"errors": 1, "warnings": 1, "info": 1},
            }
        ),
        encoding="utf-8",
    )

    output_dir = tmp_path / "out"
    vscode_counts_path = output_dir / "vscode_problem_counts.json"

    result = run_snapshot(
        repos=[RepoInfo("NuSyQ-Hub", repo_root)],
        run_id="run_test",
        vscode_counts_path=vscode_counts_path,
        vscode_counts_override={
            "source": "manual",
            "counts": {"errors": 2, "warnings": 3, "infos": 4, "total": 9},
            "note": "test",
        },
        include_exports=True,
        run_ruff=False,
        output_dir=output_dir,
        write_latest=True,
    )

    assert Path(result["json_report"]).exists()
    assert Path(result["md_report"]).exists()
    assert Path(result["latest_json"]).exists()
    assert Path(result["latest_md"]).exists()

    snapshot = result["snapshot"]
    assert snapshot["aggregate"]["total"] == 3
    assert snapshot["vscode_counts"]["counts"]["total"] == 9
