"""Combine current doctor truth with the latest bounded smoke receipt."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.chatdev_colony_doctor import build_report
from tools.latest_smoke_receipt import _build_latest_summary_payload, _find_latest_receipt, _load_receipt, _runtime_proof_summary


def _operator_commands() -> dict[str, str]:
    return {
        "latest_summary": r"powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 latest",
        "latest_full": r"powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 latest-full",
        "local_start": r"powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 local-start",
        "local_status": r"powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 local-status",
        "local_stop": r"powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 local-stop",
        "local_proof": r"powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 local-proof -Json",
        "status_compact": r"powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 status-compact",
        "status_full": r"powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 status-full",
        "smoke_status_compact": r"powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 status-compact",
        "smoke_status": r"powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 status -Json",
        "smoke_run": r"powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_gamedev_lane.ps1 smoke -Json",
    }


def _yaml_validation_payload(*, timeout: float) -> dict[str, Any]:
    command = ["uv", "run", "python", "tools/validate_all_yamls.py"]
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=max(timeout, 30.0),
            check=False,
        )
    except Exception as exc:
        return {
            "status": "error",
            "ok": False,
            "command": command,
            "error": f"{type(exc).__name__}: {exc}",
        }

    stdout = completed.stdout or ""
    total_match = re.search(r"Total Files:\s+(\d+)", stdout)
    passed_match = re.search(r"Passed:\s+(\d+)", stdout)
    failed_match = re.search(r"Failed:\s+(\d+)", stdout)
    total_files = int(total_match.group(1)) if total_match else None
    passed = int(passed_match.group(1)) if passed_match else None
    failed = int(failed_match.group(1)) if failed_match else None
    ok = completed.returncode == 0

    return {
        "status": "passed" if ok else "failed",
        "ok": ok,
        "command": command,
        "returncode": completed.returncode,
        "total_files": total_files,
        "passed": passed,
        "failed": failed,
        "stdout_tail": stdout[-4000:],
        "stderr_tail": (completed.stderr or "")[-2000:],
    }


def _latest_receipt_payload(receipt_dir: Path, *, full: bool) -> dict[str, Any]:
    latest = _find_latest_receipt(receipt_dir)
    if latest is None:
        return {
            "receipt_path": None,
            "status": "missing",
            "receipt_dir": str(receipt_dir),
        }

    payload = _load_receipt(latest)
    if full:
        return {
            "receipt_path": str(latest),
            **_runtime_proof_summary(payload),
            **payload,
        }
    return _build_latest_summary_payload(payload, receipt_path=latest)


def _build_assessment(doctor: dict[str, Any], latest: dict[str, Any], yaml_validation: dict[str, Any]) -> dict[str, Any]:
    summary = doctor.get("summary", {})
    probes = doctor.get("probes", {})
    litellm_ok = (
        probes.get("litellm", {})
        .get("paths", {})
        .get("/v1/models", {})
        .get("ok")
        is True
    )
    colony_ok = summary.get("chatdev_colony_health") is True
    runtime_labels = summary.get("gamedev_python_with_pygame") or []
    repo_runtime_ok = "repo_gamedev_venv" in runtime_labels
    latest_status = latest.get("status")
    bounded_smoke_ok = latest_status in {"artifact_emitted", "completed", "node_progress_reached"}
    yaml_validation_ok = yaml_validation.get("ok") is True
    live_surface_id = summary.get("live_surface_id")
    live_surface_mode = "worker_only" if live_surface_id == "devmentor-chatdev-worker" else (live_surface_id or "unknown")
    live_worker_status = (
        probes.get("chatdev_colony", {})
        .get("paths", {})
        .get("/status", {})
        .get("json", {})
    )
    live_preferred_model = live_worker_status.get("model")
    smoke_model_usages = latest.get("token_usage", {}).get("model_usages", {})
    proven_smoke_model = next(iter(smoke_model_usages), None)
    alignment = _preferred_model_alignment(
        preferred_live_model=live_preferred_model,
        proven_smoke_model=proven_smoke_model,
        smoke_proven=bounded_smoke_ok,
    )

    gaps: list[str] = []
    if summary.get("chatdev_local_health") is not True:
        gaps.append("chatdev_local_offline")
    if live_surface_mode == "worker_only":
        gaps.append("live_surface_is_queue_worker_not_devall_app")
    if not bounded_smoke_ok:
        gaps.append("bounded_smoke_not_proven")
    if not litellm_ok:
        gaps.append("litellm_unhealthy")
    if not repo_runtime_ok:
        gaps.append("repo_gamedev_runtime_missing")
    if not yaml_validation_ok:
        gaps.append("yaml_validation_not_proven")

    overall_status = "ready" if not gaps else (
        "ready_with_gaps"
        if bounded_smoke_ok and litellm_ok and repo_runtime_ok and yaml_validation_ok
        else "degraded"
    )

    next_action = "none"
    recommendation = "No immediate action required."
    notes: list[str] = []
    if not yaml_validation_ok:
        next_action = "run_validate_yamls"
        recommendation = "Run the YAML validation gate and fix any reported workflow errors before relying on this lane."
    elif not bounded_smoke_ok:
        next_action = "run_bounded_smoke"
        recommendation = "Run the bounded GameDev mechanic smoke to refresh execution proof and receipts."
    elif not litellm_ok:
        next_action = "repair_litellm"
        recommendation = "Restore LiteLLM /v1/models health before using the local ChatDev workflow lane."
    elif not repo_runtime_ok:
        next_action = "bootstrap_repo_gamedev_env"
        recommendation = "Bootstrap the repo-local .venv-gamedev313 runtime before trusting pygame workflow execution."
    elif summary.get("chatdev_local_health") is not True:
        next_action = "start_local_devall_app"
        recommendation = "Run the managed local-start command if you need the full local DevAll app on :6400 instead of the worker-only colony surface."
    elif live_surface_mode == "worker_only":
        next_action = "decide_worker_vs_app_surface"
        recommendation = "Decide whether worker-only :7338 is sufficient or whether the full ChatDev2 DevAll app should be brought online with the managed local-start command."

    if (
        alignment["preferred_live_model"]
        and alignment["proven_smoke_model"]
        and not alignment["preferred_live_model_matches_smoke"]
    ):
        notes.append(
            f"Preferred live worker model '{alignment['preferred_live_model']}' differs from the current proven bounded smoke model '{alignment['proven_smoke_model']}'."
        )
        notes.append(
            "Treat the preferred live route as available but not yet runtime-proven for the bounded smoke lane unless a fresh receipt shows the same model."
        )

    return {
        "overall_status": overall_status,
        "bounded_smoke_ok": bounded_smoke_ok,
        "yaml_validation_ok": yaml_validation_ok,
        "litellm_ok": litellm_ok,
        "chatdev_colony_ok": colony_ok,
        "repo_gamedev_runtime_ok": repo_runtime_ok,
        "live_surface_mode": live_surface_mode,
        "preferred_live_model": alignment["preferred_live_model"],
        "proven_smoke_model": alignment["proven_smoke_model"],
        "preferred_live_model_matches_smoke": alignment["preferred_live_model_matches_smoke"],
        "preferred_live_model_proven_for_smoke": alignment["preferred_live_model_proven_for_smoke"],
        "recommended_runtime_label": "repo_gamedev_venv" if repo_runtime_ok else (runtime_labels[0] if runtime_labels else None),
        "next_action": next_action,
        "recommendation": recommendation,
        "advisories": alignment["advisories"],
        "notes": notes,
        "operator_commands": _operator_commands(),
        "gaps": gaps,
    }


def _resolve_artifact_path(latest: dict[str, Any]) -> str | None:
    repo_root = latest.get("repo_root")
    relative_path = latest.get("first_artifact_path")
    if not repo_root or not relative_path:
        return None
    return str((Path(repo_root) / relative_path).resolve())


def _build_proof_freshness(latest: dict[str, Any], *, stale_after_seconds: float = 24 * 60 * 60) -> dict[str, Any]:
    receipt_ref = latest.get("result_json") or latest.get("receipt_path")
    if not receipt_ref:
        return {
            "proof_generated_at": None,
            "proof_age_seconds": None,
            "proof_freshness": "missing",
            "proof_stale_after_seconds": stale_after_seconds,
        }

    receipt_path = Path(receipt_ref)
    if not receipt_path.exists():
        return {
            "proof_generated_at": None,
            "proof_age_seconds": None,
            "proof_freshness": "missing",
            "proof_stale_after_seconds": stale_after_seconds,
        }

    modified_at = datetime.fromtimestamp(receipt_path.stat().st_mtime, tz=timezone.utc)
    age_seconds = max(0.0, (datetime.now(timezone.utc) - modified_at).total_seconds())
    freshness = "fresh" if age_seconds <= stale_after_seconds else "stale"
    return {
        "proof_generated_at": modified_at.isoformat().replace("+00:00", "Z"),
        "proof_age_seconds": round(age_seconds, 1),
        "proof_freshness": freshness,
        "proof_stale_after_seconds": stale_after_seconds,
    }


def _preferred_model_alignment(
    *,
    preferred_live_model: str | None,
    proven_smoke_model: str | None,
    smoke_proven: bool,
) -> dict[str, Any]:
    matches = bool(preferred_live_model) and bool(proven_smoke_model) and preferred_live_model == proven_smoke_model
    proven_for_smoke = matches and smoke_proven
    advisories: list[str] = []
    if preferred_live_model and proven_smoke_model and preferred_live_model != proven_smoke_model:
        advisories.append("preferred_live_model_differs_from_proven_smoke_model")
    if preferred_live_model and not proven_for_smoke:
        advisories.append("preferred_live_model_not_proven_for_bounded_smoke")
    return {
        "preferred_live_model": preferred_live_model,
        "proven_smoke_model": proven_smoke_model,
        "preferred_live_model_matches_smoke": matches,
        "preferred_live_model_proven_for_smoke": proven_for_smoke,
        "advisories": advisories,
    }


def _build_automation_summary(
    doctor: dict[str, Any],
    latest: dict[str, Any],
    yaml_validation: dict[str, Any],
    assessment: dict[str, Any],
) -> dict[str, Any]:
    summary = doctor.get("summary", {})
    probes = doctor.get("probes", {})
    latest_status = latest.get("status")
    smoke_ok = assessment.get("bounded_smoke_ok") is True
    local_devall_ready = summary.get("chatdev_local_health") is True
    local_devall_bootable = summary.get("local_app_bootable") is True
    local_core_routes_ready = summary.get("local_app_core_routes_ready") is True
    local_extended_routes_ready = summary.get("local_app_extended_routes_ready") is True
    worker_only = assessment.get("live_surface_mode") == "worker_only"
    workflow_execution = "passed" if smoke_ok else ("missing" if latest_status == "missing" else "failed")
    model_usages = latest.get("token_usage", {}).get("model_usages", {})
    call_history = latest.get("token_usage", {}).get("call_history", [])
    smoke_model = next(iter(model_usages), None)
    smoke_provider = call_history[-1].get("provider") if call_history else None
    attempted_model = latest.get("attempted_model")
    if attempted_model is None:
        attempted_model = latest.get("override_model")
    if attempted_model is None and call_history:
        attempted_model = call_history[-1].get("model_name")
    if attempted_model is None:
        attempted_model = smoke_model
    ollama_ok = probes.get("ollama", {}).get("paths", {}).get("/api/tags", {}).get("ok") is True
    live_worker_status = (
        probes.get("chatdev_colony", {})
        .get("paths", {})
        .get("/status", {})
        .get("json", {})
    )
    preferred_live_model = live_worker_status.get("model")
    preferred_live_backend = live_worker_status.get("backend")
    local_startup_probe = doctor.get("local_startup_probe", {})
    proof_freshness = _build_proof_freshness(latest)
    runtime_summary = _runtime_proof_summary(latest)
    runtime_proof_depth = latest.get("runtime_proof_depth") or runtime_summary.get("runtime_proof_depth")
    runtime_launch_proven = (
        latest.get("runtime_launch_proven")
        if "runtime_launch_proven" in latest
        else runtime_summary.get("runtime_launch_proven")
    ) is True
    runtime_completion_proven = (
        latest.get("runtime_completion_proven")
        if "runtime_completion_proven" in latest
        else runtime_summary.get("runtime_completion_proven")
    ) is True
    current_proof_blockers: list[str] = []
    if smoke_ok is not True:
        current_proof_blockers.append("bounded_smoke_not_proven")
    if assessment.get("litellm_ok") is not True:
        current_proof_blockers.append("litellm_unhealthy")
    if assessment.get("repo_gamedev_runtime_ok") is not True:
        current_proof_blockers.append("repo_gamedev_runtime_missing")
    if proof_freshness.get("proof_freshness") != "fresh":
        current_proof_blockers.append(f"proof_{proof_freshness.get('proof_freshness')}")
    alignment = _preferred_model_alignment(
        preferred_live_model=preferred_live_model,
        proven_smoke_model=smoke_model,
        smoke_proven=(
            smoke_ok
            and assessment.get("litellm_ok") is True
            and assessment.get("repo_gamedev_runtime_ok") is True
            and proof_freshness.get("proof_freshness") == "fresh"
        ),
    )
    runtime_launch_gate_blockers = list(current_proof_blockers)
    if runtime_launch_proven is not True:
        runtime_launch_gate_blockers.append("runtime_launch_not_proven")
    runtime_completion_gate_blockers = list(current_proof_blockers)
    if runtime_completion_proven is not True:
        runtime_completion_gate_blockers.append("runtime_completion_not_proven")
    workflow_gate_blockers = list(current_proof_blockers)
    if yaml_validation.get("ok") is not True:
        workflow_gate_blockers.append("yaml_validation_not_proven")

    errors: list[str] = []
    if assessment.get("litellm_ok") is not True:
        errors.append("litellm_unhealthy")
    if yaml_validation.get("ok") is not True:
        errors.append("yaml_validation_not_proven")
    if smoke_ok is not True:
        errors.append("bounded_smoke_not_proven")
    if summary.get("chatdev_local_health") is not True:
        errors.append("chatdev_local_offline")
    if assessment.get("live_surface_mode") == "worker_only":
        errors.append("live_surface_is_queue_worker_not_devall_app")

    operator_commands = _operator_commands()
    local_devall_blockers: list[str] = []
    if local_devall_ready is not True:
        local_devall_blockers.append("local_devall_not_running_on_6400")
    if summary.get("local_app_loaded") is not True:
        local_devall_blockers.append("local_app_not_loaded_from_checkout")
    if local_startup_probe.get("ok") is not True:
        startup_error = local_startup_probe.get("error") or local_startup_probe.get("reason") or "startup_probe_not_proven"
        local_devall_blockers.append(f"local_startup_probe_{startup_error}")
    if local_core_routes_ready is not True:
        local_devall_blockers.append("local_devall_core_routes_not_ready")
    if local_extended_routes_ready is not True:
        local_devall_blockers.append("local_devall_extended_routes_not_ready")

    return {
        "contract_version": 1,
        "proof_scope": "bounded_sandbox_smoke",
        "callable": smoke_ok and assessment.get("litellm_ok") is True and assessment.get("repo_gamedev_runtime_ok") is True,
        "callable_via": "worker_only_lane" if worker_only else ("local_devall_app" if local_devall_ready else "unknown"),
        "full_devall_ready": local_devall_ready,
        "local_app_bootable": local_devall_bootable,
        "local_app_core_routes_ready": local_core_routes_ready,
        "local_app_extended_routes_ready": local_extended_routes_ready,
        "workflow_execution": workflow_execution,
        "workflow_used": latest.get("yaml_file"),
        "smoke_status": latest_status,
        "provider": smoke_provider,
        "model": smoke_model,
        "proven_smoke_model": alignment["proven_smoke_model"],
        "attempted_model": attempted_model,
        "preferred_live_model": alignment["preferred_live_model"],
        "preferred_live_backend": preferred_live_backend,
        "preferred_live_model_matches_smoke": alignment["preferred_live_model_matches_smoke"],
        "preferred_live_model_proven_for_smoke": alignment["preferred_live_model_proven_for_smoke"],
        "output_path": _resolve_artifact_path(latest),
        "result_json": latest.get("result_json") or latest.get("receipt_path"),
        "runtime_python": latest.get("runtime_python"),
        "env_defaults": latest.get("env_defaults") or {},
        "artifact_runtime_outcome": latest.get("artifact_runtime_outcome") or runtime_summary.get("artifact_runtime_outcome"),
        "runtime_proof_depth": runtime_proof_depth,
        "runtime_launch_proven": runtime_launch_proven,
        "runtime_completion_proven": runtime_completion_proven,
        "smoke_attempted_without_model_call": (
            latest_status != "missing" and attempted_model is not None and smoke_model is None
        ),
        **proof_freshness,
        "current_proof": (
            smoke_ok
            and assessment.get("litellm_ok") is True
            and assessment.get("repo_gamedev_runtime_ok") is True
            and proof_freshness.get("proof_freshness") == "fresh"
        ),
        "current_proof_blockers": current_proof_blockers,
        "runtime_launch_gate_ok": not runtime_launch_gate_blockers,
        "runtime_launch_gate_blockers": runtime_launch_gate_blockers,
        "runtime_completion_gate_ok": not runtime_completion_gate_blockers,
        "runtime_completion_gate_blockers": runtime_completion_gate_blockers,
        "workflow_gate_ok": not workflow_gate_blockers,
        "workflow_gate_blockers": workflow_gate_blockers,
        "proxy_health": {
            "litellm": assessment.get("litellm_ok") is True,
            "ollama": ollama_ok,
            "colony_worker": summary.get("chatdev_colony_health") is True,
            "local_devall_app": summary.get("chatdev_local_health") is True,
            "local_devall_core_routes": local_core_routes_ready,
            "local_devall_extended_routes": local_extended_routes_ready,
        },
        "backend_requirements": {
            "primary_provider": "litellm",
            "primary_provider_required": True,
            "primary_provider_healthy": assessment.get("litellm_ok") is True,
            "ollama_required_for_current_lane": False,
            "ollama_healthy": ollama_ok,
            "ollama_optional_reason": "bounded_gamedev_smoke_is_currently_proven_via_litellm",
        },
        "surface": {
            "live_surface_id": summary.get("live_surface_id"),
            "live_surface_kind": summary.get("live_surface_kind"),
            "mode": assessment.get("live_surface_mode"),
        },
        "local_devall_proof": {
            "currently_live_on_6400": local_devall_ready,
            "loaded_from_checkout": summary.get("local_app_loaded") is True,
            "startup_probe_ok": local_startup_probe.get("ok") is True,
            "startup_probe_error": local_startup_probe.get("error") or local_startup_probe.get("reason"),
            "startup_probe_port": local_startup_probe.get("port"),
            "startup_probe_health_url": local_startup_probe.get("health_url"),
            "startup_probe_log": local_startup_probe.get("log_path"),
            "core_routes_ready": local_core_routes_ready,
            "extended_routes_ready": local_extended_routes_ready,
            "blockers": local_devall_blockers,
            "operator_command": operator_commands["local_status"] if local_devall_ready else operator_commands["local_start"],
            "proof_command": operator_commands["local_proof"],
        },
        "operator_commands": operator_commands,
        "yaml_validation_ok": yaml_validation.get("ok") is True,
        "next_action": assessment.get("next_action"),
        "advisories": alignment["advisories"],
        "errors": errors,
    }


def build_status(*, timeout: float, receipt_dir: Path, full: bool) -> dict[str, Any]:
    doctor = build_report(timeout=timeout)
    latest = _latest_receipt_payload(receipt_dir, full=full)
    yaml_validation = _yaml_validation_payload(timeout=timeout)
    assessment = _build_assessment(doctor, latest, yaml_validation)
    automation_summary = _build_automation_summary(doctor, latest, yaml_validation, assessment)
    return {
        "generated_at": doctor.get("generated_at"),
        "root": doctor.get("root"),
        "doctor_summary": doctor.get("summary"),
        "latest_smoke": latest,
        "yaml_validation": yaml_validation,
        "assessment": assessment,
        "automation_summary": automation_summary,
        "notes": [
            "doctor_summary reflects current live/local service truth",
            "latest_smoke reflects the freshest bounded smoke receipt under the selected receipt root",
            "yaml_validation reflects the current uv-managed workflow gate across yaml_instance",
            "assessment turns those facts into an operator-facing readiness verdict",
            "automation_summary lifts the smoke/provider/output facts into a compact automation-friendly contract",
        ],
        **({"doctor_report": doctor} if full else {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Return combined ChatDev GameDev lane status.")
    parser.add_argument("--timeout", type=float, default=2.0, help="Doctor probe timeout in seconds")
    parser.add_argument(
        "--receipt-dir",
        default=r"C:\dev\_sandboxes\chatdev-factory-prototype-smoke\WareHouse\_smoke_receipts",
        help="Directory containing smoke receipt JSON files",
    )
    parser.add_argument("--json", action="store_true", help="Emit the full combined report")
    parser.add_argument(
        "--automation-summary-only",
        action="store_true",
        help="Emit only the compact automation_summary payload",
    )
    args = parser.parse_args()

    status = build_status(
        timeout=args.timeout,
        receipt_dir=Path(args.receipt_dir).expanduser().resolve(),
        full=(args.json or args.automation_summary_only),
    )
    payload = status["automation_summary"] if args.automation_summary_only else status
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
