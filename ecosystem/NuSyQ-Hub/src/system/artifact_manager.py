"""Artifact Manager (Phase 1A).

Single place to emit the required run bundle:
- state/artifacts/<run_id>/...
- run_manifest.json (already handled by run_protocol)
- replay.sh/json
- handoff.md
- claims_evidence.json

This wraps run_protocol and applies attestation/lessons automatically.
"""

from __future__ import annotations

from typing import Any

from src.system.run_protocol import (build_claims_evidence,
                                     build_handoff_template,
                                     materialize_run_bundle)


def emit_bundle(
    manifest: dict[str, Any],
    replay_cmd: list[str],
    replay_env: dict[str, str] | None,
    changes: list[str],
    next_actions: list[str],
    do_not_touch: list[str] | None = None,
    impact: list[str] | None = None,
    suggested_agent: str | None = None,
    claims: list[dict[str, str]] | None = None,
    run_id: str | None = None,
) -> str:
    handoff = build_handoff_template(
        changes=changes,
        next_actions=next_actions,
        do_not_touch=do_not_touch,
        impact=impact,
        suggested_agent=suggested_agent,
    )
    claims_payload = build_claims_evidence(claims or [])
    bundle = materialize_run_bundle(
        manifest=manifest,
        replay_cmd=replay_cmd,
        replay_env=replay_env or {},
        handoff=handoff,
        claims=claims_payload,
        run_id=run_id,
    )
    return str(bundle.base)
