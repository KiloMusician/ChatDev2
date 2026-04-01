"""Tests for the distributed Rosetta bootstrap builder."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_rosetta_bootstrap import (  # noqa: E402
    BOOT_JSON_MAX_BYTES,
    BOOT_TXT_MAX_LINES,
    BOOTSTRAP_JSON_PATH,
    BOOTSTRAP_TXT_PATH,
    DEPRECATION_PATH,
    REGISTRY_PATH,
    main,
)


def test_build_rosetta_bootstrap_generates_artifacts():
    """Builder should emit the canonical registry and compact boot capsule."""
    result = main()
    assert result == 0

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    deprecations = json.loads(DEPRECATION_PATH.read_text(encoding="utf-8"))
    bootstrap = json.loads(BOOTSTRAP_JSON_PATH.read_text(encoding="utf-8"))
    boot_txt = BOOTSTRAP_TXT_PATH.read_text(encoding="utf-8")

    for payload in (registry, deprecations, bootstrap):
        assert "generated_at" in payload
        assert "source_hashes" in payload
        assert "source_paths" in payload
        assert "stale_after_seconds" in payload
        assert "generator_version" in payload

    assert registry["workflows"]["read_precedence"][0] == "state/boot/rosetta_bootstrap.json"
    assert registry["control_plane"]["runtime_owner"] == "simulatedverse"
    assert registry["control_plane"]["control_owner"] == "nusyq_hub"
    assert "extensions" in deprecations["deprecated"]
    assert len(json.dumps(bootstrap, separators=(",", ":")).encode("utf-8")) <= BOOT_JSON_MAX_BYTES
    assert len(boot_txt.splitlines()) <= BOOT_TXT_MAX_LINES
