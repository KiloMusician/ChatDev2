"""Tests for the distributed Rosetta bundle builder."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_rosetta_bootstrap as builder  # noqa: E402


def test_build_bundle_has_required_generated_artifacts():
    bundle = builder.build_bundle()

    for key in ("registry", "deprecations", "snapshot", "bootstrap", "boot_text"):
        assert key in bundle

    registry = bundle["registry"]
    snapshot = bundle["snapshot"]
    bootstrap = bundle["bootstrap"]

    for payload in (registry, snapshot, bootstrap):
        assert "generated_at" in payload
        assert "generator_version" in payload
        assert "stale_after_seconds" in payload
        assert "source_paths" in payload
        assert "source_hashes" in payload

    assert registry["workflows"]["culture_ship_dual_authority"]["runtime_owner"] == "simulatedverse"
    assert registry["workflows"]["culture_ship_dual_authority"]["control_owner"] == "nusyq_hub"
    assert (
        bootstrap["session_contract"]["read_precedence"][0] == "State/boot/rosetta_bootstrap.json"
    )


def test_boot_text_stays_compact():
    boot_text = builder.build_bundle()["boot_text"]
    assert len(boot_text.splitlines()) <= 120
    assert len(boot_text.encode("utf-8")) < 12_000


def test_control_plane_contract_inputs_exist():
    assert builder.DOC_PATH.exists()
    assert builder.MANIFEST_PATH.exists()
    assert builder.STATE_DIR == Path(builder.ROOT / "State")


def test_maintenance_surfaces_are_exposed():
    bundle = builder.build_bundle()
    registry = bundle["registry"]

    assert "quest_log_rotation" in registry["commands"]
    assert "archive_index" in registry["commands"]
    assert "quest_log_rotation_status" in registry["artifacts"]
    assert "archive_index" in registry["artifacts"]
