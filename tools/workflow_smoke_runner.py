"""Run a bounded workflow smoke against a ChatDev2 checkout.

This helper is designed for local-first smoke passes where we want stronger proof
than YAML validation, but do not want an unbounded multi-agent run burning local
tokens after the first useful artifact appears.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Sequence


def _resolve_yaml_path(repo_root: Path, yaml_file: str) -> Path:
    candidate = Path(yaml_file)
    if candidate.is_absolute():
        return candidate
    direct = repo_root / candidate
    if direct.exists():
        return direct
    return repo_root / "yaml_instance" / candidate


def _build_task_input(graph_context: Any, prompt: str, attachments: Sequence[str]) -> Any:
    if not attachments:
        return prompt

    from utils.attachments import AttachmentStore
    from utils.task_input import TaskInputBuilder

    attachments_dir = graph_context.directory / "code_workspace" / "attachments"
    attachments_dir.mkdir(parents=True, exist_ok=True)
    store = AttachmentStore(attachments_dir)
    builder = TaskInputBuilder(store)
    normalized_paths = [str(Path(path).expanduser()) for path in attachments]
    return builder.build_from_file_paths(prompt, normalized_paths)


def _list_workspace_artifacts(output_dir: Path) -> list[dict[str, Any]]:
    code_workspace = output_dir / "code_workspace"
    if not code_workspace.exists():
        return []

    ignored_files = {"pyproject.toml", "uv.lock", "attachments_manifest.json"}
    artifacts: list[dict[str, Any]] = []
    for path in sorted(code_workspace.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(output_dir)
        if any(part.startswith(".") for part in rel.parts):
            continue
        if "attachments" in rel.parts:
            continue
        if path.name in ignored_files:
            continue
        artifacts.append(
            {
                "relative_path": str(rel).replace("\\", "/"),
                "size": path.stat().st_size,
                "modified_at": path.stat().st_mtime,
            }
        )
    return artifacts


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8-sig")
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a bounded ChatDev2 workflow smoke.")
    parser.add_argument("--repo-root", required=True, help="Target ChatDev2 checkout root")
    parser.add_argument("--yaml-file", required=True, help="Workflow YAML path or name")
    parser.add_argument("--task-prompt", required=True, help="Prompt to feed into the workflow")
    parser.add_argument("--session-name", required=True, help="Deterministic session name for the run")
    parser.add_argument("--timeout-seconds", type=float, default=300.0, help="Overall smoke timeout")
    parser.add_argument("--poll-interval", type=float, default=2.0, help="Artifact polling interval")
    parser.add_argument("--grace-seconds", type=float, default=20.0, help="Cancel grace period after artifact")
    parser.add_argument("--stop-on-first-artifact", action="store_true", help="Cancel once the first artifact is written")
    parser.add_argument("--attachment", action="append", default=[], help="Optional attachment path")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        raise SystemExit(f"Repo root not found: {repo_root}")

    os.chdir(repo_root)
    sys.path.insert(0, str(repo_root))

    from check.check import load_config
    from entity.graph_config import GraphConfig
    from runtime.bootstrap.schema import ensure_schema_registry_populated
    from workflow.graph import GraphExecutor
    from workflow.graph_context import GraphContext

    ensure_schema_registry_populated()

    yaml_path = _resolve_yaml_path(repo_root, args.yaml_file).resolve()
    if not yaml_path.exists():
        raise SystemExit(f"Workflow YAML not found: {yaml_path}")

    design = load_config(yaml_path)
    graph_config = GraphConfig.from_definition(
        design.graph,
        name=args.session_name,
        output_root=Path("WareHouse"),
        source_path=str(yaml_path),
        vars=design.vars,
    )
    graph_context = GraphContext(config=graph_config)
    task_input = _build_task_input(graph_context, args.task_prompt, args.attachment)

    cancel_event = threading.Event()
    executor = GraphExecutor(graph_context, cancel_event=cancel_event)

    state: dict[str, Any] = {
        "status": "running",
        "exception_type": None,
        "exception": None,
        "artifacts": [],
        "cancel_requested": False,
        "started_at": time.time(),
        "ended_at": None,
    }

    def _runner() -> None:
        try:
            executor._execute(task_input)
            state["status"] = "completed"
        except Exception as exc:  # pragma: no cover - smoke helper
            state["status"] = "error"
            state["exception_type"] = type(exc).__name__
            state["exception"] = str(exc)
        finally:
            state["ended_at"] = time.time()

    thread = threading.Thread(target=_runner, name="workflow-smoke-runner", daemon=True)
    thread.start()

    deadline = time.time() + args.timeout_seconds
    artifact_stop_requested = False
    last_artifacts: list[dict[str, Any]] = []

    while thread.is_alive() and time.time() < deadline:
        last_artifacts = _list_workspace_artifacts(graph_context.directory)
        if last_artifacts and args.stop_on_first_artifact and not artifact_stop_requested:
            artifact_stop_requested = True
            state["cancel_requested"] = True
            state["artifacts"] = last_artifacts
            executor.request_cancel("Smoke threshold met: artifact emitted")
            thread.join(timeout=args.grace_seconds)
            break
        time.sleep(args.poll_interval)

    if thread.is_alive() and not artifact_stop_requested:
        state["cancel_requested"] = True
        executor.request_cancel("Smoke timeout reached")
        thread.join(timeout=args.grace_seconds)

    final_artifacts = _list_workspace_artifacts(graph_context.directory)
    state["artifacts"] = final_artifacts or last_artifacts

    status = state["status"]
    if status == "running":
        if artifact_stop_requested and state["artifacts"]:
            status = "artifact_emitted"
        else:
            status = "timeout_no_artifact" if not state["artifacts"] else "artifact_emitted_timeout"

    final_message = None
    if status in {"completed", "artifact_emitted", "artifact_emitted_timeout"}:
        message = executor.get_final_output_message()
        if message is not None:
            final_message = message.text_content()

    first_artifact_text = None
    first_artifact_path = None
    if state["artifacts"]:
        first_artifact_path = graph_context.directory / Path(state["artifacts"][0]["relative_path"])
        first_artifact_text = _read_text(first_artifact_path)

    result = {
        "status": status,
        "repo_root": str(repo_root),
        "yaml_file": str(yaml_path),
        "session_name": args.session_name,
        "output_dir": str(graph_context.directory),
        "artifacts": state["artifacts"],
        "first_artifact_path": str(first_artifact_path) if first_artifact_path else None,
        "first_artifact_text": first_artifact_text,
        "cancel_requested": state["cancel_requested"],
        "exception_type": state["exception_type"],
        "exception": state["exception"],
        "final_message": final_message,
        "token_usage": executor.token_tracker.get_token_usage() if executor.token_tracker else None,
        "elapsed_seconds": round((state["ended_at"] or time.time()) - state["started_at"], 2),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if status in {"completed", "artifact_emitted", "artifact_emitted_timeout"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
