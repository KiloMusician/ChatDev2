from pathlib import Path

import src.automation.autonomous_loop as autonomous_loop_module
from src.automation.autonomous_loop import AutonomousLoop


def test_count_issues_in_output_parses_mypy_and_ruff() -> None:
    loop = AutonomousLoop.__new__(AutonomousLoop)

    mypy_output = (
        "src/a.py:1: error: Name 'x' is not defined\nsrc/b.py:2: error: Incompatible types"
    )
    ruff_output = (
        "src/a.py:1:1: F401 `os` imported but unused\n"
        "src/b.py:2:5: E722 Do not use bare `except`"
    )

    assert loop._count_issues_in_output("mypy", mypy_output) == 2
    assert loop._count_issues_in_output("ruff", ruff_output) == 2


def test_score_feedback_loop_produces_high_band() -> None:
    loop = AutonomousLoop.__new__(AutonomousLoop)

    score = loop._score_feedback_loop(
        execution_results={"success_rate": 1.0},
        apply_results={"applied_file_count": 6, "preview": {"applicable_results": 2}},
        validation_results={"checks_run": 2, "checks_passed": 2, "issue_count": 0},
        audit_results={"findings": 8},
    )

    assert score["band"] == "high"
    assert score["score"] >= 0.75


def test_apply_task_results_skips_when_result_applier_unavailable(monkeypatch) -> None:
    loop = AutonomousLoop.__new__(AutonomousLoop)
    loop.result_apply_mode = "preview"
    loop.result_apply_limit = 5

    monkeypatch.setattr(autonomous_loop_module, "RESULT_APPLIER_AVAILABLE", False)
    monkeypatch.setattr(autonomous_loop_module, "ResultApplier", None)

    result = loop._apply_task_results()

    assert result["status"] == "skipped"
    assert result["reason"] == "result_applier_unavailable"


def test_run_feedback_validation_uses_python_targets(
    monkeypatch,
    tmp_path: Path,
) -> None:
    loop = AutonomousLoop.__new__(AutonomousLoop)
    loop.root = tmp_path
    loop.result_apply_mode = "stage"
    loop.validation_timeout_seconds = 60

    staged_file = tmp_path / "state" / "review_gate" / "result_applier" / "sample.py"
    staged_file.parent.mkdir(parents=True, exist_ok=True)
    staged_file.write_text("print('ok')\n", encoding="utf-8")

    commands: list[tuple[str, list[str]]] = []

    def fake_resolve_tool_command(_tool_name: str) -> list[str]:
        return ["tool"]

    def fake_run_validation_check(name: str, command: list[str]) -> dict[str, object]:
        commands.append((name, command))
        return {
            "name": name,
            "status": "completed",
            "passed": True,
            "returncode": 0,
            "issue_count": 0,
            "duration_s": 0.1,
            "command": command,
        }

    monkeypatch.setattr(loop, "_resolve_tool_command", fake_resolve_tool_command)
    monkeypatch.setattr(loop, "_run_validation_check", fake_run_validation_check)

    result = loop._run_feedback_validation(
        {
            "test_paths": [],
            "staged_paths": [str(staged_file)],
        }
    )

    assert result["checks_run"] == 2
    assert len(result["python_targets"]) == 1
    assert any(name == "ruff" for name, _ in commands)
    assert any(name == "mypy" for name, _ in commands)
