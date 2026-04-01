

from config.flexibility_manager import FlexiblePathManager


def test_get_python_executable_prefers_venv(tmp_path):
    # Create a fake workspace with a .venv Python on Windows path
    workspace = tmp_path / "repo"
    scripts_py = workspace / ".venv" / "Scripts"
    scripts_py.mkdir(parents=True)
    py_exe = scripts_py / "python.exe"
    py_exe.write_text("")

    manager = FlexiblePathManager(str(workspace))
    exe = manager.get_python_executable()

    assert str(py_exe) == exe


def test_resolve_template_path_substitutions(tmp_path, monkeypatch):
    workspace = tmp_path / "repo2"
    workspace.mkdir()
    monkeypatch.chdir(workspace)

    manager = FlexiblePathManager(str(workspace))

    template = "${workspaceFolder}/data/${platform}/${custom}"
    resolved = manager.resolve_template_path(template, custom="x")

    assert str(workspace) in resolved
    assert "/data/" in resolved or "\\data\\" in resolved
    assert "x" in resolved
