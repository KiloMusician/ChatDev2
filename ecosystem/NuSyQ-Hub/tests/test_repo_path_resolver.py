from pathlib import Path

import pytest
from src.utils.repo_path_resolver import RepositoryPathResolver, get_repo_path


def test_env_override_paths(monkeypatch, tmp_path):
    root = tmp_path / "NuSyQ"
    hub = tmp_path / "Hub"
    sim = tmp_path / "SimVerse"
    root.mkdir()
    hub.mkdir()
    sim.mkdir()

    monkeypatch.setenv("NUSYQ_ROOT", str(root))
    monkeypatch.setenv("NUSYQ_HUB_ROOT", str(hub))
    monkeypatch.setenv("SIMULATEDVERSE_ROOT", str(sim))

    RepositoryPathResolver.reset_instance()
    resolver = RepositoryPathResolver.get_instance()

    assert resolver.get_path("NUSYQ_ROOT") == root.resolve()
    assert resolver.get_path("NUSYQ_HUB_ROOT") == hub.resolve()
    assert resolver.get_path("SIMULATEDVERSE_ROOT") == sim.resolve()
    assert get_repo_path("NUSYQ_ROOT") == root.resolve()


def test_unknown_repo_key_raises():
    RepositoryPathResolver.reset_instance()
    resolver = RepositoryPathResolver.get_instance()

    with pytest.raises(KeyError):
        resolver.get_path("UNKNOWN_REPO")


def test_normalize_userprofile_windows_path_does_not_raise_bad_escape(monkeypatch):
    """Ensure USERPROFILE replacement handles backslashes safely on Windows-style paths."""
    resolver = RepositoryPathResolver.__new__(RepositoryPathResolver)
    monkeypatch.delenv("USERPROFILE", raising=False)

    monkeypatch.setattr(
        RepositoryPathResolver,
        "_infer_userprofile_path",
        staticmethod(lambda: Path(r"C:\Users\UnitTester")),
    )

    resolved = resolver._normalize_path_value(r"$env:USERPROFILE\NuSyQ")
    assert resolved is not None
    # Path format depends on platform: WSL produces /mnt/c/... Windows produces C:\...
    posix_str = str(resolved).replace("\\", "/")
    assert "UnitTester" in posix_str and "NuSyQ" in posix_str
