"""Run a bounded workflow smoke against a ChatDev2 checkout.

This helper is designed for local-first smoke passes where we want stronger proof
than YAML validation, but do not want an unbounded multi-agent run burning local
tokens after the first useful artifact appears.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
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


def _configure_import_roots(repo_root: Path, source_root: Path | None) -> Path:
    effective_source_root = (source_root or repo_root).expanduser().resolve()
    if not effective_source_root.exists():
        raise SystemExit(f"Source root not found: {effective_source_root}")

    # Keep the code import root first so sandbox output paths can differ from the
    # authoritative checkout we want to execute.
    sys.path.insert(0, str(effective_source_root))
    if effective_source_root != repo_root:
        sys.path.insert(1, str(repo_root))
    return effective_source_root


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


def _write_result_json(result: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_latest_result_json(result: dict[str, Any], output_path: Path) -> Path:
    latest_path = output_path.with_name("latest.json")
    _write_result_json(result, latest_path)
    return latest_path


def _validate_python_artifacts(output_dir: Path, artifacts: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    validations: list[dict[str, Any]] = []
    for artifact in artifacts:
        relative_path = artifact.get("relative_path")
        if not isinstance(relative_path, str) or not relative_path.endswith(".py"):
            continue

        artifact_path = output_dir / Path(relative_path)
        source = _read_text(artifact_path)
        if source is None:
            validations.append(
                {
                    "relative_path": relative_path,
                    "valid": False,
                    "error": "unreadable",
                }
            )
            continue

        try:
            ast.parse(source, filename=str(artifact_path))
            validations.append(
                {
                    "relative_path": relative_path,
                    "valid": True,
                }
            )
        except SyntaxError as exc:
            validations.append(
                {
                    "relative_path": relative_path,
                    "valid": False,
                    "error": exc.msg,
                    "line": exc.lineno,
                    "offset": exc.offset,
                }
            )
    return validations


def _runtime_validate_python_artifacts(
    output_dir: Path,
    artifacts: Sequence[dict[str, Any]],
    *,
    runtime_python: str,
    timeout_seconds: float,
) -> list[dict[str, Any]]:
    validations: list[dict[str, Any]] = []
    for artifact in artifacts:
        relative_path = artifact.get("relative_path")
        if not isinstance(relative_path, str) or not relative_path.endswith(".py"):
            continue

        artifact_path = output_dir / Path(relative_path)
        env = os.environ.copy()
        env.setdefault("SDL_VIDEODRIVER", "dummy")
        env.setdefault("SDL_AUDIODRIVER", "dummy")
        env.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

        try:
            completed = subprocess.run(
                [runtime_python, artifact_path.name],
                cwd=str(artifact_path.parent),
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
            )
            valid = completed.returncode == 0
            outcome = "exited_0" if valid else "exited_nonzero"
            validations.append(
                {
                    "relative_path": relative_path,
                    "valid": valid,
                    "outcome": outcome,
                    "returncode": completed.returncode,
                    "stdout_tail": completed.stdout[-500:],
                    "stderr_tail": completed.stderr[-500:],
                }
            )
        except subprocess.TimeoutExpired as exc:
            validations.append(
                {
                    "relative_path": relative_path,
                    "valid": True,
                    "outcome": "timed_out_after_launch",
                    "timeout_seconds": timeout_seconds,
                    "stdout_tail": (exc.stdout or "")[-500:],
                    "stderr_tail": (exc.stderr or "")[-500:],
                }
            )
        except Exception as exc:
            validations.append(
                {
                    "relative_path": relative_path,
                    "valid": False,
                    "outcome": "spawn_error",
                    "error": str(exc),
                }
            )
    return validations


def _summarize_token_progress(token_usage: dict[str, Any] | None, current_node_id: str | None) -> dict[str, Any]:
    call_history = token_usage.get("call_history", []) if token_usage else []
    last_completed_node = call_history[-1]["node_id"] if call_history else None
    return {
        "last_completed_node": last_completed_node,
        "last_active_node": current_node_id,
    }


def _node_progress_reached(
    token_progress: dict[str, Any],
    *,
    stop_on_active_node: str | None,
    stop_on_completed_node: str | None,
) -> bool:
    if stop_on_active_node and token_progress.get("last_active_node") == stop_on_active_node:
        return True
    if stop_on_completed_node and token_progress.get("last_completed_node") == stop_on_completed_node:
        return True
    return False


def _resolve_final_status(
    *,
    state_status: str,
    artifacts: list[dict[str, Any]],
    artifact_stop_requested: bool,
    node_progress_stop_requested: bool,
    cancel_requested: bool,
    exception_type: str | None,
) -> str:
    if artifact_stop_requested and artifacts:
        return "artifact_emitted"
    if node_progress_stop_requested:
        return "node_progress_reached"
    if (
        state_status == "error"
        and cancel_requested
        and artifacts
        and exception_type == "WorkflowCancelledError"
    ):
        return "artifact_emitted"
    if state_status == "running":
        return "timeout_no_artifact" if not artifacts else "artifact_emitted_timeout"
    return state_status


def _resolve_bounded_stop_reason(
    *,
    artifact_stop_requested: bool,
    node_progress_stop_requested: bool,
    cancel_requested: bool,
    exception_type: str | None,
    status: str,
) -> str | None:
    if artifact_stop_requested and status == "artifact_emitted":
        return "artifact_threshold_reached"
    if node_progress_stop_requested and status == "node_progress_reached":
        return "node_progress_threshold_reached"
    if cancel_requested and exception_type == "WorkflowCancelledError" and status == "artifact_emitted_timeout":
        return "timeout_after_artifact_emission"
    return None


def _normalize_expected_bounded_cancellation(
    *,
    status: str,
    cancel_requested: bool,
    exception_type: str | None,
    exception: str | None,
    final_message: str | None,
    bounded_stop_reason: str | None,
) -> tuple[str | None, str | None, str | None]:
    if not cancel_requested or exception_type != "WorkflowCancelledError":
        return exception_type, exception, final_message
    if bounded_stop_reason is None:
        return exception_type, exception, final_message
    if status not in {"artifact_emitted", "artifact_emitted_timeout", "node_progress_reached"}:
        return exception_type, exception, final_message

    normalized_message = final_message
    if final_message in {None, "", "Workflow execution cancelled"}:
        normalized_message = bounded_stop_reason.replace("_", " ")
    return None, None, normalized_message


def _override_openai_node_models(graph_definition: dict[str, Any], model_name: str) -> int:
    if hasattr(graph_definition, "nodes"):
        nodes = getattr(graph_definition, "nodes", [])
    elif isinstance(graph_definition, dict):
        nodes = graph_definition.get("nodes", [])
    else:
        nodes = []

    updated = 0
    for node in nodes:
        if hasattr(node, "config"):
            config = getattr(node, "config")
            provider = getattr(config, "provider", None)
            if provider != "openai":
                continue
            setattr(config, "name", model_name)
        elif isinstance(node, dict):
            config = node.get("config")
            if not isinstance(config, dict):
                continue
            if config.get("provider") != "openai":
                continue
            config["name"] = model_name
        else:
            continue
        updated += 1
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a bounded ChatDev2 workflow smoke.")
    parser.add_argument("--repo-root", required=True, help="Target ChatDev2 checkout root")
    parser.add_argument(
        "--source-root",
        help="Optional checkout root to import workflow/runtime code from; defaults to --repo-root",
    )
    parser.add_argument("--yaml-file", required=True, help="Workflow YAML path or name")
    parser.add_argument("--task-prompt", required=True, help="Prompt to feed into the workflow")
    parser.add_argument("--session-name", required=True, help="Deterministic session name for the run")
    parser.add_argument("--timeout-seconds", type=float, default=300.0, help="Overall smoke timeout")
    parser.add_argument("--poll-interval", type=float, default=2.0, help="Artifact polling interval")
    parser.add_argument("--grace-seconds", type=float, default=20.0, help="Cancel grace period after artifact")
    parser.add_argument("--stop-on-first-artifact", action="store_true", help="Cancel once the first artifact is written")
    parser.add_argument("--stop-on-active-node", help="Cancel once the named node becomes the current active node")
    parser.add_argument("--stop-on-completed-node", help="Cancel once the named node completes a model call")
    parser.add_argument("--override-model", help="Override all openai-provider node model aliases for this run")
    parser.add_argument(
        "--validate-python-artifacts",
        action="store_true",
        help="Compile emitted Python artifacts with ast.parse and fail if any are invalid",
    )
    parser.add_argument(
        "--run-python-artifacts",
        action="store_true",
        help="Launch emitted Python artifacts with a short timeout and fail on immediate runtime errors",
    )
    parser.add_argument(
        "--python-run-timeout-seconds",
        type=float,
        default=5.0,
        help="Per-artifact timeout for --run-python-artifacts runtime validation",
    )
    parser.add_argument(
        "--runtime-python",
        help="Interpreter to use for --run-python-artifacts; defaults to the current Python executable",
    )
    parser.add_argument("--attachment", action="append", default=[], help="Optional attachment path")
    parser.add_argument("--result-json", help="Optional path to write the final smoke JSON receipt")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        raise SystemExit(f"Repo root not found: {repo_root}")

    os.chdir(repo_root)
    source_root = _configure_import_roots(repo_root, Path(args.source_root) if args.source_root else None)

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
    overridden_node_count = 0
    if args.override_model:
        overridden_node_count = _override_openai_node_models(design.graph, args.override_model)
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
    node_progress_stop_requested = False
    last_artifacts: list[dict[str, Any]] = []
    token_progress = _summarize_token_progress(None, None)

    while thread.is_alive() and time.time() < deadline:
        last_artifacts = _list_workspace_artifacts(graph_context.directory)
        token_usage = executor.token_tracker.get_token_usage() if executor.token_tracker else None
        token_progress = _summarize_token_progress(
            token_usage,
            getattr(executor.token_tracker, "current_node_id", None) if executor.token_tracker else None,
        )
        if last_artifacts and args.stop_on_first_artifact and not artifact_stop_requested:
            artifact_stop_requested = True
            state["cancel_requested"] = True
            state["artifacts"] = last_artifacts
            executor.request_cancel("Smoke threshold met: artifact emitted")
            thread.join(timeout=args.grace_seconds)
            break
        if (
            not node_progress_stop_requested
            and _node_progress_reached(
                token_progress,
                stop_on_active_node=args.stop_on_active_node,
                stop_on_completed_node=args.stop_on_completed_node,
            )
        ):
            node_progress_stop_requested = True
            state["cancel_requested"] = True
            executor.request_cancel("Smoke threshold met: node progress reached")
            thread.join(timeout=args.grace_seconds)
            break
        time.sleep(args.poll_interval)

    if thread.is_alive() and not artifact_stop_requested and not node_progress_stop_requested:
        state["cancel_requested"] = True
        executor.request_cancel("Smoke timeout reached")
        thread.join(timeout=args.grace_seconds)

    final_artifacts = _list_workspace_artifacts(graph_context.directory)
    state["artifacts"] = final_artifacts or last_artifacts

    status = _resolve_final_status(
        state_status=state["status"],
        artifacts=state["artifacts"],
        artifact_stop_requested=artifact_stop_requested,
        node_progress_stop_requested=node_progress_stop_requested,
        cancel_requested=state["cancel_requested"],
        exception_type=state["exception_type"],
    )

    final_message = None
    token_usage = executor.token_tracker.get_token_usage() if executor.token_tracker else None
    token_progress = _summarize_token_progress(
        token_usage,
        getattr(executor.token_tracker, "current_node_id", None) if executor.token_tracker else None,
    )
    if status in {"completed", "artifact_emitted", "artifact_emitted_timeout"}:
        message = executor.get_final_output_message()
        if message is not None:
            final_message = message.text_content()

    bounded_stop_reason = _resolve_bounded_stop_reason(
        artifact_stop_requested=artifact_stop_requested,
        node_progress_stop_requested=node_progress_stop_requested,
        cancel_requested=state["cancel_requested"],
        exception_type=state["exception_type"],
        status=status,
    )
    exception_type, exception, final_message = _normalize_expected_bounded_cancellation(
        status=status,
        cancel_requested=state["cancel_requested"],
        exception_type=state["exception_type"],
        exception=state["exception"],
        final_message=final_message,
        bounded_stop_reason=bounded_stop_reason,
    )

    first_artifact_text = None
    first_artifact_path = None
    if state["artifacts"]:
        first_artifact_path = graph_context.directory / Path(state["artifacts"][0]["relative_path"])
        first_artifact_text = _read_text(first_artifact_path)

    artifact_validation = None
    if args.validate_python_artifacts:
        artifact_validation = _validate_python_artifacts(graph_context.directory, state["artifacts"])
        if artifact_validation and not all(item["valid"] for item in artifact_validation):
            status = "artifact_validation_failed"

    artifact_runtime_validation = None
    runtime_python = None
    if args.run_python_artifacts:
        runtime_python = args.runtime_python or sys.executable
        artifact_runtime_validation = _runtime_validate_python_artifacts(
            graph_context.directory,
            state["artifacts"],
            runtime_python=runtime_python,
            timeout_seconds=args.python_run_timeout_seconds,
        )
        if artifact_runtime_validation and not all(item["valid"] for item in artifact_runtime_validation):
            status = "artifact_runtime_failed"

    result = {
        "status": status,
        "repo_root": str(repo_root),
        "source_root": str(source_root),
        "yaml_file": str(yaml_path),
        "override_model": args.override_model,
        "overridden_node_count": overridden_node_count,
        "session_name": args.session_name,
        "output_dir": str(graph_context.directory),
        "artifacts": state["artifacts"],
        "first_artifact_path": str(first_artifact_path) if first_artifact_path else None,
        "first_artifact_text": first_artifact_text,
        "stop_on_active_node": args.stop_on_active_node,
        "stop_on_completed_node": args.stop_on_completed_node,
        "bounded_stop_reason": bounded_stop_reason,
        "cancel_requested": state["cancel_requested"],
        "exception_type": exception_type,
        "exception": exception,
        "final_message": final_message,
        "artifact_validation": artifact_validation,
        "runtime_python": runtime_python,
        "artifact_runtime_validation": artifact_runtime_validation,
        "token_usage": token_usage,
        "token_progress": token_progress,
        "elapsed_seconds": round((state["ended_at"] or time.time()) - state["started_at"], 2),
    }
    if args.result_json:
        result_output_path = Path(args.result_json).expanduser()
        _write_result_json(result, result_output_path)
        latest_result_path = _write_latest_result_json(result, result_output_path)
        result["result_json"] = str(result_output_path)
        result["latest_result_json"] = str(latest_result_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if status in {"completed", "artifact_emitted", "artifact_emitted_timeout", "node_progress_reached"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
