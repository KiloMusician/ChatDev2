import json
from pathlib import Path

from scripts.nusyq_actions.brief import handle_brief


class _Paths:
    def __init__(self, hub: Path) -> None:
        self.nusyq_hub = hub


def _seed_quest_log(hub: Path) -> None:
    quest_file = hub / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
    quest_file.parent.mkdir(parents=True, exist_ok=True)
    quest_file.write_text(
        json.dumps(
            {
                "status": "active",
                "title": "Signal consistency hardening",
                "description": "Align diagnostics outputs",
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_brief_prefers_ground_truth_and_flags_drift(tmp_path, capsys, monkeypatch):
    hub = tmp_path
    _seed_quest_log(hub)
    # Allow old ground truth for drift comparison (default 360m, test timestamp ~17d old)
    monkeypatch.setenv("NUSYQ_BRIEF_DRIFT_MAX_AGE_MINUTES", "99999")

    diagnostics_dir = hub / "docs" / "Reports" / "diagnostics"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)

    (diagnostics_dir / "unified_error_report_latest.json").write_text(
        json.dumps(
            {
                "timestamp": "2026-02-20T12:00:00+00:00",
                "scan_mode": "full",
                "ground_truth": {
                    "errors": 1228,
                    "warnings": 0,
                    "infos": 0,
                    "total": 1228,
                    "source": "tool_scan",
                    "confidence": "high",
                    "scope": {
                        "targets": ["nusyq-hub", "simulated-verse", "nusyq"],
                        "scan_mode": "full",
                        "partial_scan": False,
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    (diagnostics_dir / "vscode_problem_counts_tooling.json").write_text(
        json.dumps(
            {
                "source": "vscode_diagnostics_bridge",
                "counts": {"errors": 209, "warnings": 0, "infos": 0, "total": 209},
            }
        ),
        encoding="utf-8",
    )
    (diagnostics_dir / "problem_signal_snapshot_latest.json").write_text(
        json.dumps({"aggregate": {"errors": 0, "warnings": 0, "infos": 0, "total": 0}}),
        encoding="utf-8",
    )

    current_state = hub / "state" / "reports" / "current_state.md"
    current_state.parent.mkdir(parents=True, exist_ok=True)
    current_state.write_text("- Lint errors: `29`\n", encoding="utf-8")

    rc = handle_brief(_Paths(hub), lambda _hub: ["✅ Spine hygiene: CLEAN"])
    assert rc == 0

    out = capsys.readouterr().out
    assert "Ground Truth: 1228 errors" in out
    assert "⚠️ Signal drift: Tool Aggregate and Ground Truth totals differ" in out
    assert "⚠️ Snapshot drift: current_state lint errors differ from ground truth errors" in out
    assert "VS Code and ground-truth totals differ (209 vs 1228)" in out


def test_brief_warns_when_ground_truth_unavailable(tmp_path, capsys):
    hub = tmp_path
    _seed_quest_log(hub)

    diagnostics_dir = hub / "docs" / "Reports" / "diagnostics"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    (diagnostics_dir / "vscode_problem_counts_tooling.json").write_text(
        json.dumps(
            {"source": "vscode", "counts": {"errors": 1, "warnings": 0, "infos": 0, "total": 1}}
        ),
        encoding="utf-8",
    )

    rc = handle_brief(_Paths(hub), lambda _hub: ["✅ Spine hygiene: CLEAN"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Ground truth unavailable" in out
