"""Run Protocol helpers for artifact-ledger, manifest, and replay bundles.

This module implements Phase 1 (Trust & Artifacts):
- per-run artifact ledger under state/artifacts/<run_id>/
- deterministic run manifest
- replay recipe
- handoff summary (claims -> evidence)

All functions are side-effect free except filesystem writes into state/artifacts/.
"""

from __future__ import annotations

import json
import shutil
import time
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.config.feature_flag_manager import is_feature_enabled
from src.system.attestation import attest_manifest
from src.system.knowledge import append_lesson
from src.system.planning import build_dual_plan, planbundle_to_dict
from src.system.telemetry import log_span

ARTIFACT_ROOT = Path("state") / "artifacts"


def generate_run_id(prefix: str | None = None) -> str:
    ts = time.strftime("%Y%m%d_%H%M%S")
    return f"{prefix + '_' if prefix else ''}{ts}_{uuid.uuid4().hex[:8]}"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


@dataclass
class RunPaths:
    run_id: str
    base: Path
    manifest: Path
    handoff: Path
    claims: Path
    replay_sh: Path
    replay_json: Path


def init_run_paths(run_id: str | None = None) -> RunPaths:
    rid = run_id or generate_run_id()
    base = ARTIFACT_ROOT / rid
    ensure_dir(base)
    return RunPaths(
        run_id=rid,
        base=base,
        manifest=base / "run_manifest.json",
        handoff=base / "handoff.md",
        claims=base / "claims_evidence.json",
        replay_sh=base / "replay.sh",
        replay_json=base / "replay.json",
    )


def write_manifest(paths: RunPaths, manifest: dict[str, Any]) -> None:
    ensure_dir(paths.base)
    with paths.manifest.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def write_handoff(paths: RunPaths, summary: str) -> None:
    ensure_dir(paths.base)
    with paths.handoff.open("w", encoding="utf-8") as f:
        f.write(summary.strip() + "\n")


def write_claims(paths: RunPaths, claims: dict[str, Any]) -> None:
    ensure_dir(paths.base)
    with paths.claims.open("w", encoding="utf-8") as f:
        json.dump(claims, f, indent=2)


def write_replay(paths: RunPaths, command: list[str], env: dict[str, str] | None = None) -> None:
    ensure_dir(paths.base)
    env = env or {}
    # replay.json for programmatic consumption
    with paths.replay_json.open("w", encoding="utf-8") as f:
        json.dump({"cmd": command, "env": env}, f, indent=2)
    # replay.sh for humans
    with paths.replay_sh.open("w", encoding="utf-8") as f:
        f.write("#!/usr/bin/env bash\nset -euo pipefail\n")
        for k, v in env.items():
            f.write(f'export {k}="{v}"\n')
        f.write(" ".join(command) + "\n")
    paths.replay_sh.chmod(0o755)


def save_artifact(paths: RunPaths, name: str, content: str | bytes) -> Path:
    ensure_dir(paths.base)
    target = paths.base / name
    mode = "wb" if isinstance(content, (bytes, bytearray)) else "w"
    with target.open(mode, encoding=None if "b" in mode else "utf-8") as f:
        f.write(content)
    return target


def copy_artifact(paths: RunPaths, source: Path, target_name: str | None = None) -> Path:
    ensure_dir(paths.base)
    target = paths.base / (target_name or source.name)
    shutil.copy2(source, target)
    return target


def build_handoff_template(
    changes: Iterable[str],
    next_actions: Iterable[str],
    do_not_touch: Iterable[str] | None = None,
    impact: Iterable[str] | None = None,
    suggested_agent: str | None = None,
) -> str:
    lines = []
    lines.append("# Handoff")
    lines.append("## What changed")
    lines.extend(f"- {c}" for c in changes)
    lines.append("## Next actions")
    lines.extend(f"- {a}" for a in next_actions)
    if do_not_touch:
        lines.append("## Do NOT touch")
        lines.extend(f"- {d}" for d in do_not_touch)
    if impact:
        lines.append("## Impact / blast radius")
        lines.extend(f"- {i}" for i in impact)
    if suggested_agent:
        lines.append(f"## Suggested next agent: {suggested_agent}")
    return "\n".join(lines)


def build_claims_evidence(entries: list[dict[str, str]]) -> dict[str, Any]:
    """entries: list of {claim, evidence, pointer}."""
    return {"claims": entries, "count": len(entries)}


# Convenience one-shot writer
def materialize_run_bundle(
    manifest: dict[str, Any],
    replay_cmd: list[str],
    replay_env: dict[str, str] | None,
    handoff: str,
    claims: dict[str, Any],
    run_id: str | None = None,
) -> RunPaths:
    paths = init_run_paths(run_id)
    # Attach planning scaffolding if enabled
    if is_feature_enabled("planning_discipline_enabled"):
        plan_bundle = planbundle_to_dict(build_dual_plan(manifest.get("task", "task")))
        manifest = {**manifest, "plan_bundle": plan_bundle}
    manifest.setdefault("timestamps", {})["created"] = time.time()
    manifest = attest_manifest(manifest)
    write_manifest(paths, manifest)
    write_replay(paths, replay_cmd, replay_env or {})
    write_handoff(paths, handoff)
    write_claims(paths, claims)
    if is_feature_enabled("mission_control_enabled"):
        log_span(
            "run_bundle_created",
            {
                "run_id": paths.run_id,
                "task": manifest.get("task", "task"),
                "artifact_path": str(paths.base),
            },
        )
    if is_feature_enabled("knowledge_reuse_enabled"):
        append_lesson(
            {
                "run_id": paths.run_id,
                "task": manifest.get("task", "task"),
                "summary": "bundle_created",
            }
        )
    return paths
