from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.diagnostics.unified_error_reporter import RepoName, UnifiedErrorReporter
from src.utils.repo_path_resolver import RepositoryPathResolver


def test_unified_error_reporter_quick_mode_reads_vscode_counts(tmp_path: Path, monkeypatch) -> None:
    simverse_root = tmp_path / "simulatedverse_missing"
    nusyq_root = tmp_path / "nusyq_missing"
    monkeypatch.setenv("SIMULATEDVERSE_ROOT", str(simverse_root))
    monkeypatch.setenv("NUSYQ_ROOT", str(nusyq_root))
    RepositoryPathResolver.reset_instance()

    hub_root = tmp_path / "hub"
    diagnostics_dir = hub_root / "docs" / "Reports" / "diagnostics"
    diagnostics_dir.mkdir(parents=True)
    counts_path = diagnostics_dir / "vscode_problem_counts.json"
    counts_path.write_text(
        json.dumps(
            {
                "source": "manual",
                "counts": {"errors": 3, "warnings": 5, "infos": 7, "total": 15},
            }
        ),
        encoding="utf-8",
    )

    reporter = UnifiedErrorReporter(hub_path=hub_root)
    report = reporter.scan_all_repos(quick=True)

    assert report["scan_mode"] == "quick"
    assert report["total_diagnostics"] == 0
    assert report["vscode_counts"]["counts"]["total"] == 15
    assert report["ground_truth"]["total"] == 0
    assert report["ground_truth"]["scope"]["targets"] == ["nusyq-hub"]
    assert report["ground_truth"]["confidence"] == "medium"
    assert "targeted repos: nusyq-hub" in report["ground_truth"]["note"]

    outputs = reporter.write_report(diagnostics_dir)
    assert Path(outputs["json"]).exists()
    assert Path(outputs["md"]).exists()


def _seed_hub_with_e501_debt_file(tmp_path: Path, monkeypatch) -> Path:
    simverse_root = tmp_path / "simulatedverse_missing"
    nusyq_root = tmp_path / "nusyq_missing"
    monkeypatch.setenv("SIMULATEDVERSE_ROOT", str(simverse_root))
    monkeypatch.setenv("NUSYQ_ROOT", str(nusyq_root))
    RepositoryPathResolver.reset_instance()

    hub_root = tmp_path / "hub"
    (hub_root / "docs" / "Reports" / "diagnostics").mkdir(parents=True, exist_ok=True)
    (hub_root / "src").mkdir(parents=True, exist_ok=True)
    (hub_root / "pyproject.toml").write_text(
        '[tool.ruff]\nline-length = 100\nignore = ["E501"]\n',
        encoding="utf-8",
    )
    (hub_root / "src" / "sample.py").write_text(
        'LONG_VALUE = "' + ("x" * 130) + '"\n',
        encoding="utf-8",
    )
    return hub_root


def test_unified_error_reporter_quick_mode_excludes_e501_debt_by_default(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv("NUSYQ_ERROR_SCAN_INCLUDE_QUICK_E501_DEBT", raising=False)
    hub_root = _seed_hub_with_e501_debt_file(tmp_path, monkeypatch)

    reporter = UnifiedErrorReporter(hub_path=hub_root)
    report = reporter.scan_all_repos(quick=True)

    assert report["scan_mode"] == "quick"
    assert report["ground_truth"]["total"] == 0
    assert "excludes quick E501 debt scan" in report["ground_truth"]["note"]


def test_unified_error_reporter_quick_mode_can_include_e501_debt(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("NUSYQ_ERROR_SCAN_INCLUDE_QUICK_E501_DEBT", "1")
    hub_root = _seed_hub_with_e501_debt_file(tmp_path, monkeypatch)

    reporter = UnifiedErrorReporter(hub_path=hub_root)
    report = reporter.scan_all_repos(quick=True)

    assert report["scan_mode"] == "quick"
    assert report["ground_truth"]["total"] >= 1
    assert "includes quick E501 debt scan" in report["ground_truth"]["note"]
    assert any(detail.get("error_id") == "ruff-E501" for detail in report["diagnostic_details"])


def test_unified_error_reporter_mypy_retry_avoids_timeout_warning(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SIMULATEDVERSE_ROOT", str(tmp_path / "simulatedverse_missing"))
    monkeypatch.setenv("NUSYQ_ROOT", str(tmp_path / "nusyq_missing"))
    RepositoryPathResolver.reset_instance()

    hub_root = tmp_path / "hub"
    src_dir = hub_root / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    for idx in range(6):
        (src_dir / f"sample_{idx}.py").write_text("value: int = 'oops'\n", encoding="utf-8")

    reporter = UnifiedErrorReporter(hub_path=hub_root, include_repos=[RepoName.NUSYQ_HUB])
    monkeypatch.setattr("src.diagnostics.unified_error_reporter.MAX_MYPY_FILES", 6)
    monkeypatch.setattr("src.diagnostics.unified_error_reporter.MYPY_RETRY_MAX_FILES", 2)

    call_count = {"count": 0}

    def fake_run_with_heartbeat(cmd: list[str], label: str, timeout: int):
        _ = cmd, label, timeout
        call_count["count"] += 1
        if call_count["count"] == 1:
            raise subprocess.TimeoutExpired(cmd=["python", "-m", "mypy"], timeout=300)
        return subprocess.CompletedProcess(
            args=["python", "-m", "mypy"],
            returncode=1,
            stdout="src/sample.py:1: error: Incompatible types in assignment\n",
            stderr="",
        )

    monkeypatch.setattr(reporter, "_run_with_heartbeat", fake_run_with_heartbeat)
    diagnostics = reporter._scan_with_mypy(RepoName.NUSYQ_HUB, hub_root)

    # 1 initial timeout + ceil(6 files / 2 files-per-chunk) = 1 + 3 = 4 calls
    assert call_count["count"] == 4
    assert len(diagnostics) >= 1
    assert diagnostics[0].source == "mypy"
    assert reporter.scan_warnings == []


def test_unified_error_reporter_pylint_targets_python_files_only(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SIMULATEDVERSE_ROOT", str(tmp_path / "simulatedverse_missing"))
    monkeypatch.setenv("NUSYQ_ROOT", str(tmp_path / "nusyq_missing"))
    RepositoryPathResolver.reset_instance()

    hub_root = tmp_path / "hub"
    src_dir = hub_root / "src" / "nested"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "example.py").write_text("value = 1\n", encoding="utf-8")

    reporter = UnifiedErrorReporter(hub_path=hub_root, include_repos=[RepoName.NUSYQ_HUB])
    monkeypatch.setattr("src.diagnostics.unified_error_reporter.MAX_PYLINT_FILES", 10)
    monkeypatch.setattr("src.diagnostics.unified_error_reporter.shutil.which", lambda name: None)

    captured_cmd: dict[str, list[str]] = {}

    def fake_run_with_heartbeat(cmd: list[str], label: str, timeout: int):
        _ = label, timeout
        captured_cmd["cmd"] = cmd
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="[]", stderr="")

    monkeypatch.setattr(reporter, "_run_with_heartbeat", fake_run_with_heartbeat)
    diagnostics = reporter._scan_with_pylint(RepoName.NUSYQ_HUB, hub_root)

    assert diagnostics == []
    cmd = captured_cmd["cmd"]
    assert cmd[:5] == [sys.executable, "-m", "pylint", "--exit-zero", "-f"]
    assert cmd[5] == "json"
    assert cmd[-1].endswith("example.py")
    assert all(item.endswith(".py") for item in cmd[6:])


def test_unified_error_reporter_collect_python_files_prefers_rg(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SIMULATEDVERSE_ROOT", str(tmp_path / "simulatedverse_missing"))
    monkeypatch.setenv("NUSYQ_ROOT", str(tmp_path / "nusyq_missing"))
    RepositoryPathResolver.reset_instance()

    hub_root = tmp_path / "hub"
    src_dir = hub_root / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    reporter = UnifiedErrorReporter(hub_path=hub_root, include_repos=[RepoName.NUSYQ_HUB])

    monkeypatch.setattr("src.diagnostics.unified_error_reporter.shutil.which", lambda name: "/usr/bin/rg")

    def fake_run_with_heartbeat(cmd: list[str], label: str, timeout: int):
        _ = label, timeout
        assert cmd[:3] == ["/usr/bin/rg", "--files", str(src_dir)]
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=0,
            stdout="src/example_b.py\nsrc/example_a.py\n",
            stderr="",
        )

    monkeypatch.setattr(reporter, "_run_with_heartbeat", fake_run_with_heartbeat)
    files = reporter._collect_python_files([src_dir], limit=1)

    assert len(files) == 1
    assert files[0].name == "example_b.py"


def test_unified_error_reporter_count_python_files_falls_back_when_rg_unavailable(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SIMULATEDVERSE_ROOT", str(tmp_path / "simulatedverse_missing"))
    monkeypatch.setenv("NUSYQ_ROOT", str(tmp_path / "nusyq_missing"))
    RepositoryPathResolver.reset_instance()

    hub_root = tmp_path / "hub"
    src_dir = hub_root / "src" / "nested"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "one.py").write_text("value = 1\n", encoding="utf-8")
    (src_dir / "two.py").write_text("value = 2\n", encoding="utf-8")

    reporter = UnifiedErrorReporter(hub_path=hub_root, include_repos=[RepoName.NUSYQ_HUB])
    monkeypatch.setattr("src.diagnostics.unified_error_reporter.shutil.which", lambda name: None)

    assert reporter._count_python_files([hub_root / "src"]) == 2


def test_unified_error_reporter_quick_scan_skips_full_file_count(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SIMULATEDVERSE_ROOT", str(tmp_path / "simulatedverse_missing"))
    monkeypatch.setenv("NUSYQ_ROOT", str(tmp_path / "nusyq_missing"))
    RepositoryPathResolver.reset_instance()

    hub_root = tmp_path / "hub"
    src_dir = hub_root / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "example.py").write_text("value = 1\n", encoding="utf-8")

    reporter = UnifiedErrorReporter(hub_path=hub_root, include_repos=[RepoName.NUSYQ_HUB])

    def fail_count(targets):
        raise AssertionError(f"_count_python_files should not run in quick mode: {targets}")

    monkeypatch.setattr(reporter, "_count_python_files", fail_count)
    monkeypatch.setattr(
        reporter,
        "_scan_with_ruff",
        lambda repo_name, repo_path, quick=False: [],
    )

    scan = reporter._scan_repo(RepoName.NUSYQ_HUB, hub_root, quick=True)

    assert scan.diagnostics == []
