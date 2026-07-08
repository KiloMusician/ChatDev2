"""Return the most recent bounded smoke receipt from the sandbox receipt directory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _find_latest_receipt(receipt_dir: Path) -> Path | None:
    if not receipt_dir.exists():
        return None
    latest_pointer = receipt_dir / "latest.json"
    if latest_pointer.exists() and latest_pointer.is_file():
        return latest_pointer
    candidates = [path for path in receipt_dir.glob("*.json") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _load_receipt(receipt_path: Path) -> dict[str, Any]:
    return json.loads(receipt_path.read_text(encoding="utf-8"))


def _runtime_proof_summary(payload: dict[str, Any]) -> dict[str, Any]:
    validations = payload.get("artifact_runtime_validation") or []
    if not validations:
        return {
            "artifact_runtime_outcome": None,
            "runtime_proof_depth": "missing",
            "runtime_launch_proven": False,
            "runtime_completion_proven": False,
        }

    outcomes = [item.get("outcome") for item in validations if item.get("outcome")]
    all_valid = all(item.get("valid") is True for item in validations)
    launch_outcomes = {"completed", "timed_out_after_launch"}
    launch_proven = all_valid and bool(outcomes) and all(outcome in launch_outcomes for outcome in outcomes)
    completion_proven = all_valid and bool(outcomes) and all(outcome == "completed" for outcome in outcomes)
    if completion_proven:
        proof_depth = "completed"
    elif launch_proven:
        proof_depth = "launch_only"
    else:
        proof_depth = "failed"

    return {
        "artifact_runtime_outcome": outcomes[0] if outcomes else None,
        "runtime_proof_depth": proof_depth,
        "runtime_launch_proven": launch_proven,
        "runtime_completion_proven": completion_proven,
    }


def _resolve_artifact_path(payload: dict[str, Any]) -> str | None:
    repo_root = payload.get("repo_root")
    relative_path = payload.get("first_artifact_path")
    if not repo_root or not relative_path:
        return None
    return str((Path(repo_root) / relative_path).resolve())


def _provider_model_summary(payload: dict[str, Any]) -> dict[str, Any]:
    token_usage = payload.get("token_usage", {}) or {}
    model_usages = token_usage.get("model_usages", {}) or {}
    call_history = token_usage.get("call_history", []) or []
    proven_smoke_model = next(iter(model_usages), None)
    attempted_model = payload.get("override_model")
    if attempted_model is None and call_history:
        attempted_model = call_history[-1].get("model_name")
    if attempted_model is None:
        attempted_model = proven_smoke_model
    return {
        "provider": call_history[-1].get("provider") if call_history else None,
        "model": proven_smoke_model,
        "proven_smoke_model": proven_smoke_model,
        "attempted_model": attempted_model,
    }


def _build_latest_summary_payload(payload: dict[str, Any], *, receipt_path: Path) -> dict[str, Any]:
    runtime_summary = _runtime_proof_summary(payload)
    provider_model = _provider_model_summary(payload)
    return {
        "receipt_path": str(receipt_path),
        "result_json": str(receipt_path),
        "session_name": payload.get("session_name"),
        "status": payload.get("status"),
        "bounded_stop_reason": payload.get("bounded_stop_reason"),
        "workflow_used": payload.get("yaml_file"),
        "first_artifact_path": payload.get("first_artifact_path"),
        "output_path": _resolve_artifact_path(payload),
        "runtime_python": payload.get("runtime_python"),
        "elapsed_seconds": payload.get("elapsed_seconds"),
        "env_defaults": payload.get("env_defaults") or {},
        **provider_model,
        **runtime_summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Return the latest bounded smoke receipt.")
    parser.add_argument(
        "--receipt-dir",
        default=r"C:\dev\_sandboxes\chatdev-factory-prototype-smoke\WareHouse\_smoke_receipts",
        help="Directory containing smoke receipt JSON files",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Emit only a compact summary instead of the full receipt payload",
    )
    args = parser.parse_args()

    receipt_dir = Path(args.receipt_dir).expanduser().resolve()
    latest = _find_latest_receipt(receipt_dir)
    if latest is None:
        print(
            json.dumps(
                {
                    "status": "missing",
                    "receipt_dir": str(receipt_dir),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 1

    payload = _load_receipt(latest)
    if args.summary:
        payload = _build_latest_summary_payload(payload, receipt_path=latest)
    else:
        payload = {
            "receipt_path": str(latest),
            **payload,
        }

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
