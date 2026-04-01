import json
from pathlib import Path

from src.system import run_protocol as rp


def test_run_bundle_creation(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(rp, "ARTIFACT_ROOT", tmp_path)
    manifest = {"task": "unit-test"}
    claims = rp.build_claims_evidence([{"claim": "ok", "evidence": "log", "pointer": "log.txt"}])
    handoff = rp.build_handoff_template(["c1"], ["n1"])
    paths = rp.materialize_run_bundle(
        manifest, ["echo", "test"], {}, handoff, claims, run_id="test-id"
    )

    assert paths.base.exists()
    assert json.loads(paths.manifest.read_text())["task"] == "unit-test"
    assert paths.replay_json.exists()
    assert "Handoff" in paths.handoff.read_text()
    loaded_claims = json.loads(paths.claims.read_text())
    assert loaded_claims["count"] == 1
