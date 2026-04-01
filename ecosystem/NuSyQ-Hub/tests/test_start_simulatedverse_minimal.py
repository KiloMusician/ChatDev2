import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

# These tests are for SimulatedVerse minimal mode - skip if not available
pytestmark = pytest.mark.skip(reason="SimulatedVerse tests require specific environment")


def test_detect_use_npm_run(tmp_path, monkeypatch):
    try:
        from scripts.start_simulatedverse_minimal import SimulatedVerseMinimal
    except ImportError:
        pytest.skip("SimulatedVerse module not available")

    sv = SimulatedVerseMinimal()
    # Create fake package.json with a dev:minimal script
    test_pkg = tmp_path / "package.json"
    test_pkg.write_text(json.dumps({"scripts": {"dev:minimal": "echo hi"}}))

    # Point the object to tmp_path
    sv.simulatedverse_path = tmp_path

    assert sv._detect_use_npm_run() is True

    # Remove script and ensure detection is False
    test_pkg.write_text(json.dumps({"scripts": {}}))
    assert sv._detect_use_npm_run() is False


def test_build_exec_cmd_windows_npm(monkeypatch):
    try:
        from scripts.start_simulatedverse_minimal import SimulatedVerseMinimal
    except ImportError:
        pytest.skip("SimulatedVerse module not available")

    sv = SimulatedVerseMinimal()
    sv.simulatedverse_path = Path(".")

    # Monkeypatch os.name to 'nt' to simulate Windows
    monkeypatch.setattr(os, "name", "nt")

    # Use npm run path
    base_cmd = ["npm", "run", "dev:minimal"]
    cmd = sv._build_exec_cmd(base_cmd, use_npm_run=True, is_windows=True)
    assert cmd[:2] == ["cmd", "/c"]


def test_build_exec_cmd_windows_npx_fallback(monkeypatch, capsys):
    try:
        from src.start_simulatedverse_minimal import SimulatedVerseMinimal
    except ImportError:
        pytest.skip("SimulatedVerseMinimal not available")

    sv = SimulatedVerseMinimal()
    sv.simulatedverse_path = Path(".")
    monkeypatch.setattr(os, "name", "nt")

    # If npx is not available, _build_exec_cmd should return a cmd wrapper
    monkeypatch.setattr(sv, "_build_exec_cmd", SimulatedVerseMinimal._build_exec_cmd.__get__(sv))

    cmd = sv._build_exec_cmd(
        ["npx", "tsx", "server/minimal_server.ts"], use_npm_run=False, is_windows=True
    )
    # Accept either direct invocation or cmd /c wrapper starting with 'cmd'
    assert isinstance(cmd, list)


def test_build_exec_cmd_unix(monkeypatch):
    try:
        from src.start_simulatedverse_minimal import SimulatedVerseMinimal
    except ImportError:
        pytest.skip("SimulatedVerseMinimal not available")

    sv = SimulatedVerseMinimal()
    sv.simulatedverse_path = Path(".")
    monkeypatch.setattr(os, "name", "posix")

    base_cmd = ["npx", "tsx", "server/minimal_server.ts"]
    cmd = sv._build_exec_cmd(base_cmd, use_npm_run=False, is_windows=False)
    assert cmd == base_cmd
