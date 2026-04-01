#!/usr/bin/env python3
"""Demo: materialize a run bundle for the Run Protocol (Phase 1)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from src.system.run_protocol import (  # type: ignore
    build_claims_evidence,
    build_handoff_template,
    materialize_run_bundle,
)


def main() -> None:
    manifest = {
        "task": "demo",
        "models": {"primary": "gpt-4o-mini"},
        "environment": {"BASE_URL": os.getenv("BASE_URL", ""), "OPENAI_API_KEY": "redacted"},
        "feature_flags": {"trust_artifacts_enabled": True},
        "cost_estimate": {"tokens": 0, "usd": 0},
    }
    replay_cmd = ["echo", "demo run"]
    replay_env = {}

    handoff = build_handoff_template(
        changes=["Initialized Run Protocol demo bundle"],
        next_actions=["Replace demo with real task", "Attach real diffs/tests/screenshots"],
        do_not_touch=["None in demo"],
        impact=["None - demo only"],
        suggested_agent="Codex",
    )
    claims = build_claims_evidence(
        [
            {
                "claim": "Bundle created",
                "evidence": "state/artifacts/<run_id>/",
                "pointer": "manifest + replay",
            }
        ]
    )
    paths = materialize_run_bundle(manifest, replay_cmd, replay_env, handoff, claims)
    print(f"Run bundle created at {paths.base}")


if __name__ == "__main__":
    main()
