"""Combine current doctor truth with the latest bounded smoke receipt."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.chatdev_colony_doctor import build_report
from tools.latest_smoke_receipt import _find_latest_receipt, _load_receipt


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
            **payload,
        }
    return {
        "receipt_path": str(latest),
        "session_name": payload.get("session_name"),
        "status": payload.get("status"),
        "bounded_stop_reason": payload.get("bounded_stop_reason"),
        "first_artifact_path": payload.get("first_artifact_path"),
        "runtime_python": payload.get("runtime_python"),
        "elapsed_seconds": payload.get("elapsed_seconds"),
    }


def _build_assessment(doctor: dict[str, Any], latest: dict[str, Any]) -> dict[str, Any]:
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
    live_surface_id = summary.get("live_surface_id")
    live_surface_mode = "worker_only" if live_surface_id == "devmentor-chatdev-worker" else (live_surface_id or "unknown")

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

    overall_status = "ready" if not gaps else ("ready_with_gaps" if bounded_smoke_ok and litellm_ok and repo_runtime_ok else "degraded")

    return {
        "overall_status": overall_status,
        "bounded_smoke_ok": bounded_smoke_ok,
        "litellm_ok": litellm_ok,
        "chatdev_colony_ok": colony_ok,
        "repo_gamedev_runtime_ok": repo_runtime_ok,
        "live_surface_mode": live_surface_mode,
        "recommended_runtime_label": "repo_gamedev_venv" if repo_runtime_ok else (runtime_labels[0] if runtime_labels else None),
        "gaps": gaps,
    }


def build_status(*, timeout: float, receipt_dir: Path, full: bool) -> dict[str, Any]:
    doctor = build_report(timeout=timeout)
    latest = _latest_receipt_payload(receipt_dir, full=full)
    assessment = _build_assessment(doctor, latest)
    return {
        "generated_at": doctor.get("generated_at"),
        "root": doctor.get("root"),
        "doctor_summary": doctor.get("summary"),
        "latest_smoke": latest,
        "assessment": assessment,
        "notes": [
            "doctor_summary reflects current live/local service truth",
            "latest_smoke reflects the freshest bounded smoke receipt under the selected receipt root",
            "assessment turns those facts into an operator-facing readiness verdict",
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
    args = parser.parse_args()

    status = build_status(timeout=args.timeout, receipt_dir=Path(args.receipt_dir).expanduser().resolve(), full=args.json)
    print(json.dumps(status, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
