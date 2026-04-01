"""Attestation helper (Phase 7) - lightweight manifest signer."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from src.config.feature_flag_manager import is_feature_enabled


def attest_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if not is_feature_enabled("attestation_enabled"):
        return manifest
    serialized = json.dumps(manifest, sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(serialized).hexdigest()
    manifest["attestation"] = {"sha256": digest}
    return manifest
