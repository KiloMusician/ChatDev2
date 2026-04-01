from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.workspace_scm_truth as scm_truth


def test_load_workspace_folders(tmp_path):
    workspace = tmp_path / "sample.code-workspace"
    workspace.write_text(
        json.dumps(
            {
                "folders": [
                    {"name": "Alpha", "path": str(tmp_path / "alpha")},
                    {"path": str(tmp_path / "beta")},
                ]
            }
        ),
        encoding="utf-8",
    )

    folders = scm_truth.load_workspace_folders(workspace)

    assert folders == [
        ("Alpha", (tmp_path / "alpha").resolve()),
        ("beta", (tmp_path / "beta").resolve()),
    ]


def test_discover_workspace_repos_includes_nested_repo(tmp_path):
    root = tmp_path / "NuSyQ"
    root.mkdir()
    (root / ".git").mkdir()
    chatdev = root / "ChatDev"
    chatdev.mkdir()
    (chatdev / ".git").mkdir()

    workspace = tmp_path / "sample.code-workspace"
    workspace.write_text(json.dumps({"folders": [{"name": "NuSyQ", "path": str(root)}]}), encoding="utf-8")

    repos = scm_truth.discover_workspace_repos(workspace)

    assert ("NuSyQ", root.resolve(), False) in repos
    assert ("NuSyQ:ChatDev", chatdev.resolve(), True) in repos


def test_discover_workspace_repos_skips_temp_nested_repos(tmp_path):
    root = tmp_path / "Hub"
    root.mkdir()
    (root / ".git").mkdir()
    temp_repo = root / "temp_sns_core"
    temp_repo.mkdir()
    (temp_repo / ".git").mkdir()
    hidden_repo = root / "_vibe"
    hidden_repo.mkdir()
    (hidden_repo / ".git").mkdir()

    workspace = tmp_path / "sample.code-workspace"
    workspace.write_text(json.dumps({"folders": [{"name": "Hub", "path": str(root)}]}), encoding="utf-8")

    repos = scm_truth.discover_workspace_repos(workspace)

    assert ("Hub", root.resolve(), False) in repos
    assert all(path != temp_repo.resolve() for _label, path, _nested in repos)
    assert all(path != hidden_repo.resolve() for _label, path, _nested in repos)


def test_choose_git_command_prefers_windows_git_for_mnt_paths(monkeypatch):
    import sys
    if sys.platform == "win32":
        pytest.skip("Path resolution under Windows turns /mnt/... into C:\\mnt\\...; test is Linux/WSL only")

    fake_git = Path("/mnt/c/Program Files/Git/cmd/git.exe")
    monkeypatch.setattr(scm_truth, "WINDOWS_GIT", fake_git)
    monkeypatch.setattr(type(fake_git), "exists", lambda self: True)

    cmd = scm_truth.choose_git_command(Path("/mnt/c/Users/example/repo"))

    assert cmd[:2] == [str(scm_truth.WINDOWS_GIT), "-C"]
    assert cmd[2].startswith("C:")


def test_parse_porcelain_counts_tracked_and_untracked():
    tracked, untracked, files = scm_truth.parse_porcelain(
        " M foo.txt\nA  bar.txt\n?? baz.txt\nR  old.txt -> new.txt\n"
    )

    assert tracked == 3
    assert untracked == 1
    assert files == ["foo.txt", "bar.txt", "baz.txt", "old.txt -> new.txt"]
