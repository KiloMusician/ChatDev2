#!/usr/bin/env python3
"""Demo of planning discipline scaffolding + run bundle."""

from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from src.system.planning import build_dual_plan, planbundle_to_dict  # type: ignore
from src.system.run_protocol import (  # type: ignore
    build_claims_evidence,
    build_handoff_template,
    materialize_run_bundle,
)


def main() -> None:
    plan = build_dual_plan("planning demo task")
    plan_dict = planbundle_to_dict(plan)
    handoff = build_handoff_template(
        changes=["Planning demo bundle created"],
        next_actions=["Inspect plan_bundle in manifest"],
    )
    claims = build_claims_evidence([{"claim": "plan_generated", "evidence": "plan_bundle", "pointer": "manifest"}])
    manifest = {"task": "planning demo", "models": {"primary": "gpt-4o-mini"}}
    bundle = materialize_run_bundle(manifest, ["echo", "demo"], {}, handoff, claims)
    print("Plan bundle stored at:", bundle.base)
    print("Plan detail:", plan_dict)


if __name__ == "__main__":
    main()
