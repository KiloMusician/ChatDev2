import json
from pathlib import Path

import pytest
from scripts.mirror_spine_snapshot import (
    _mirror_snapshot,
    _read_snapshot,
    get_default_targets,
    main,
)


def test_read_snapshot_missing(tmp_path: Path) -> None:
    missing = tmp_path / "absent.json"
    with pytest.raises(FileNotFoundError):
        _read_snapshot(missing)


def test_mirror_snapshot_writes_file(tmp_path: Path) -> None:
    destination = tmp_path / "nested" / "snapshot.json"
    payload = {"hello": "world"}

    _mirror_snapshot(payload, destination)

    assert destination.exists()
    written = json.loads(destination.read_text())
    assert written == payload


def test_get_default_targets_env_overrides(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    hub_root = tmp_path / "hub"
    root_repo = tmp_path / "NuSyQ"
    sim_repo = tmp_path / "SimulatedVerse" / "SimulatedVerse"
    hub_root.mkdir()
    root_repo.mkdir()
    sim_repo.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("NUSYQ_ROOT_PATH", str(root_repo))
    monkeypatch.setenv("SIMULATEDVERSE_PATH", str(sim_repo))

    targets = get_default_targets(hub_root)

    assert "hub_feed" in targets
    assert targets["hub_feed"].parent.name == "feeds"

    nusyq_root_target = targets["nusyq_root"]
    simulatedverse_target = targets["simulatedverse"]

    assert nusyq_root_target.parent.name == "feeds"
    assert nusyq_root_target.parent.parent.name == "state"

    assert simulatedverse_target.parent.name == "feeds"
    assert simulatedverse_target.parent.parent.name == "state"


def test_main_writes_targets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    hub_root = tmp_path / "hub"
    snapshot_dir = hub_root / "state" / "reports"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = snapshot_dir / "spine_health_snapshot.json"
    snapshot_payload = {"status": "ok", "details": []}
    snapshot_path.write_text(json.dumps(snapshot_payload))

    target_a = tmp_path / "mirror_a.json"
    target_b = tmp_path / "mirror_b.json"

    # Build argv manually
    import sys

    argv_backup = sys.argv[:]
    sys.argv = [
        "mirror_spine_snapshot",
        "--hub-root",
        str(hub_root),
        "--targets",
        str(target_a),
        str(target_b),
        "--quiet",
    ]
    try:
        exit_code = main()
    finally:
        sys.argv = argv_backup

    assert exit_code == 0
    assert target_a.exists()
    assert target_b.exists()
    assert json.loads(target_a.read_text()) == snapshot_payload
    assert json.loads(target_b.read_text()) == snapshot_payload
