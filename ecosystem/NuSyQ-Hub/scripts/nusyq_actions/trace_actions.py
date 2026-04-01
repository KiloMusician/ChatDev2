"""Action module: Tracing service/config utilities and assertions."""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlparse

if TYPE_CHECKING:
    from scripts.start_nusyq import RepoPaths
from scripts.nusyq_actions.shared import (
    collect_audit_intelligence,
    emit_action_receipt,
    format_audit_intelligence_lines,
    load_otel_bridge,
    parse_kv_args,
    write_state_report,
)

# Constants
DEFAULT_OTLP_ENDPOINT = "http://localhost:4318"
SPINE_MODULE = "scripts.start_nusyq"
TRACE_CORRELATION_FILENAME = "trace_correlation.json"
TRACE_SERVICE_SCRIPT_REL = Path("scripts/trace_service.py")
TRACE_SERVICE_PID_FILENAME = "trace_service_stub.pid"
TRACE_SERVICE_READY_TIMEOUT_S = 6.0
TRACE_SERVICE_STOP_GRACE_S = 3.0


def _spine() -> Any:
    import importlib

    return importlib.import_module(SPINE_MODULE)


# Optional OpenTelemetry bridge
otel, _OTEL_SOURCE, _OTEL_IMPORT_ERROR = load_otel_bridge()


def _resolve_otel_bridge() -> tuple[object | None, str, str | None]:
    """Load tracing bridge lazily, preserving import diagnostics."""
    global otel, _OTEL_SOURCE, _OTEL_IMPORT_ERROR
    if otel is None:
        otel, _OTEL_SOURCE, _OTEL_IMPORT_ERROR = load_otel_bridge()
    return otel, _OTEL_SOURCE, _OTEL_IMPORT_ERROR


def _load_and_apply_config(paths: RepoPaths) -> dict:
    """Load tracing config and apply it once per action.

    Imported lazily to avoid circular imports with the spine.
    """
    spine = _spine()
    config = cast(dict, spine.load_trace_config(paths.nusyq_hub))
    spine.apply_trace_config(config)
    return config


def _tracing_enabled(config: dict) -> bool:
    """Respect explicit enabled flag with a safe default to True."""
    return bool(config.get("enabled", True))


def _write_state_report(paths: RepoPaths, filename: str, payload: dict) -> Path:
    """Write a JSON report under state/reports/ and return the path."""
    hub = cast(Path, paths.nusyq_hub)
    return write_state_report(hub, filename, payload)


def _trace_endpoint_check(endpoint: str) -> tuple[bool, str]:
    checker: Any = _spine()._trace_endpoint_check
    return cast(tuple[bool, str], checker(endpoint))


def _is_wsl() -> bool:
    if os.environ.get("WSL_DISTRO_NAME"):
        return True
    try:
        return "microsoft" in os.uname().release.lower()
    except AttributeError:
        return False


def _is_local_endpoint(endpoint: str) -> bool:
    try:
        host = (urlparse(endpoint).hostname or "").lower()
    except ValueError:
        return False
    return host in {"localhost", "127.0.0.1", "::1"}


def _is_policy_blocked_detail(detail: str) -> bool:
    lowered = detail.lower()
    return any(
        token in lowered
        for token in (
            "operation not permitted",
            "permission denied",
            "errno 1",
            "eperm",
            "access is denied",
        )
    )


def _endpoint_probe_candidates(endpoint: str) -> list[str]:
    base = endpoint.rstrip("/")
    if "/v1/traces" in base:
        return [base]
    return [f"{base}/health", f"{base}/v1/traces", base]


def _trace_endpoint_check_windows(endpoint: str) -> tuple[bool, str]:
    if not (_is_wsl() and _is_local_endpoint(endpoint)):
        return False, "windows_probe skipped (not wsl-local)"

    powershell = shutil.which("powershell.exe")
    if not powershell:
        return False, "windows_probe unavailable (powershell.exe not found)"

    last_detail = "windows_probe did not run"
    for candidate in _endpoint_probe_candidates(endpoint):
        ps_script = (
            "$u=$args[0]; "
            "$ProgressPreference='SilentlyContinue'; "
            "try { "
            "$r=Invoke-WebRequest -UseBasicParsing -Method GET -Uri $u -TimeoutSec 2; "
            "if ($r.StatusCode -lt 500) { "
            "Write-Output ('HTTP ' + $r.StatusCode); exit 0 "
            "} else { "
            "Write-Output ('HTTP ' + $r.StatusCode); exit 1 "
            "} "
            "} catch { "
            "Write-Output ($_.Exception.Message); exit 1 "
            "}"
        )
        try:
            proc = subprocess.run(
                [powershell, "-NoProfile", "-Command", ps_script, candidate],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            last_detail = f"windows_probe error: {exc}"
            continue

        output = (proc.stdout or proc.stderr or "").strip()
        if proc.returncode == 0:
            return True, f"{candidate} -> {output or 'OK'}"
        last_detail = f"{candidate} -> {output or f'rc={proc.returncode}'}"

    return False, last_detail


def _collector_health(endpoint: str, managed_running: bool = False) -> dict[str, Any]:
    reachable, detail = _trace_endpoint_check(endpoint)
    result = {
        "reachable": reachable,
        "detail": detail,
        "probe_method": "python",
        "policy_blocked": _is_policy_blocked_detail(detail),
        "windows_probe_attempted": False,
        "windows_probe_detail": "",
        "inferred_from_managed_pid": False,
    }
    if reachable:
        return result

    if _is_wsl() and _is_local_endpoint(endpoint):
        result["windows_probe_attempted"] = True
        win_ok, win_detail = _trace_endpoint_check_windows(endpoint)
        result["windows_probe_detail"] = win_detail
        if win_ok:
            result["reachable"] = True
            result["probe_method"] = "windows-powershell"
            result["detail"] = f"{detail}; windows_probe={win_detail}"
            return result
        result["detail"] = f"{detail}; windows_probe={win_detail}"

    if managed_running and result["policy_blocked"] and _is_wsl() and _is_local_endpoint(endpoint):
        result["reachable"] = True
        result["probe_method"] = "inferred-managed-pid"
        result["inferred_from_managed_pid"] = True
        result["detail"] = f"{result['detail']}; inferred_reachable_from_managed_pid"
    return result


def _receipt_dir(hub: Path) -> Path:
    dir_getter: Any = _spine()._receipt_dir
    return cast(Path, dir_getter(hub))


def _runtime_dir(hub: Path) -> Path:
    runtime = hub / "state" / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    return runtime


def _trace_service_pid_path(hub: Path) -> Path:
    return _runtime_dir(hub) / TRACE_SERVICE_PID_FILENAME


def _read_pid_record(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        import json

        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _write_pid_record(path: Path, payload: dict) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _stop_pid(pid: int, grace_seconds: float = TRACE_SERVICE_STOP_GRACE_S) -> bool:
    if pid <= 0:
        return False
    if not _pid_alive(pid):
        return True

    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError:
            return False
        return not _pid_alive(pid)

    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return not _pid_alive(pid)

    deadline = time.time() + max(grace_seconds, 0.2)
    while time.time() < deadline:
        if not _pid_alive(pid):
            return True
        time.sleep(0.1)

    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        return not _pid_alive(pid)

    time.sleep(0.1)
    return not _pid_alive(pid)


def _wait_for_endpoint(endpoint: str, timeout_s: float = TRACE_SERVICE_READY_TIMEOUT_S) -> tuple[bool, str]:
    deadline = time.time() + max(timeout_s, 0.1)
    last_detail = "endpoint check not attempted"
    while time.time() < deadline:
        health = _collector_health(endpoint, managed_running=True)
        if bool(health["reachable"]):
            return True, str(health["detail"])
        last_detail = str(health["detail"])
        time.sleep(0.2)
    return False, last_detail


# Import trace helpers from spine (centralized config + reporting utils)
# (spine helpers imported lazily in functions to avoid circular import)


# --- Service controls -------------------------------------------------------


def handle_trace_service_status(paths: RepoPaths) -> int:
    print("🔎 Trace Service Status")
    print("=" * 50)

    hub = cast(Path, paths.nusyq_hub)
    config = _load_and_apply_config(paths)
    endpoint = config.get("endpoint", DEFAULT_OTLP_ENDPOINT)
    endpoint_str = str(endpoint)

    pid_path = _trace_service_pid_path(hub)
    pid_record = _read_pid_record(pid_path) or {}
    pid = int(pid_record.get("pid", 0) or 0)
    managed_running = _pid_alive(pid)
    stale_pid_file = bool(pid and not managed_running and pid_path.exists())
    if stale_pid_file:
        try:
            pid_path.unlink(missing_ok=True)
        except OSError:
            pass

    health: dict[str, Any] = {
        "reachable": False,
        "detail": "tracing disabled in config",
        "probe_method": "disabled",
        "policy_blocked": False,
        "windows_probe_attempted": False,
        "windows_probe_detail": "",
        "inferred_from_managed_pid": False,
    }
    if _tracing_enabled(config) or managed_running:
        health = _collector_health(endpoint_str, managed_running=managed_running)
        reachable = bool(health["reachable"])
        detail = str(health["detail"])
    else:
        reachable, detail = False, "tracing disabled in config"

    spine = _spine()
    report = {
        "enabled": _tracing_enabled(config),
        "endpoint": endpoint,
        "reachable": reachable,
        "detail": detail,
        "managed_pid": pid or None,
        "managed_running": managed_running,
        "probe_method": health.get("probe_method"),
        "policy_blocked": bool(health.get("policy_blocked", False)),
        "windows_probe_attempted": bool(health.get("windows_probe_attempted", False)),
        "windows_probe_detail": health.get("windows_probe_detail") or None,
        "inferred_from_managed_pid": bool(health.get("inferred_from_managed_pid", False)),
        "pid_file": str(pid_path),
        "stale_pid_file": stale_pid_file,
        "run_id": spine.ensure_run_id(),
        "audit_intelligence": collect_audit_intelligence(hub, include_sessions=False),
    }
    report_path = _write_state_report(paths, "trace_service_status.json", report)

    if reachable:
        print("TRACE_SERVICE_STATUS_OK")
    else:
        print("TRACE_SERVICE_STATUS_WARN")
    print(f"Report: {report_path}")
    print("\n📚 Audit Intelligence")
    for line in format_audit_intelligence_lines(report["audit_intelligence"], max_lines=3):
        print(f"  - {line}")
    rc = 0 if reachable else 1
    emit_action_receipt(
        "trace_service_status",
        exit_code=rc,
        metadata={
            "reachable": reachable,
            "endpoint": endpoint_str,
            "probe_method": health.get("probe_method"),
            "inferred_from_managed_pid": bool(health.get("inferred_from_managed_pid", False)),
        },
    )
    return rc


def handle_trace_service_start(paths: RepoPaths) -> int:
    print("▶️ Trace Service Start")
    print("=" * 50)

    spine = _spine()
    hub = cast(Path, paths.nusyq_hub)
    config = _load_and_apply_config(paths)
    if not _tracing_enabled(config):
        config["enabled"] = True
        spine.save_trace_config(paths.nusyq_hub, config)
        spine.apply_trace_config(config)

    endpoint = str(config.get("endpoint", DEFAULT_OTLP_ENDPOINT))
    pid_path = _trace_service_pid_path(hub)
    pid_record = _read_pid_record(pid_path) or {}
    existing_pid = int(pid_record.get("pid", 0) or 0)
    existing_alive = _pid_alive(existing_pid)

    if existing_alive:
        health = _collector_health(endpoint, managed_running=True)
        reachable = bool(health["reachable"])
        detail = str(health["detail"])
        if reachable:
            report = {
                "status": "already_running",
                "endpoint": endpoint,
                "reachable": reachable,
                "detail": detail,
                "probe_method": health.get("probe_method"),
                "managed_pid": existing_pid,
                "pid_file": str(pid_path),
                "run_id": spine.ensure_run_id(),
            }
            _write_state_report(paths, "trace_service_start.json", report)
            print("TRACE_SERVICE_START_OK")
            emit_action_receipt(
                "trace_service_start",
                exit_code=0,
                metadata={"status": "already_running", "endpoint": endpoint},
            )
            return 0
        _stop_pid(existing_pid)

    script_path = hub / TRACE_SERVICE_SCRIPT_REL
    if not script_path.exists():
        print(f"TRACE_SERVICE_START_ERROR (missing script: {script_path})")
        emit_action_receipt(
            "trace_service_start",
            exit_code=1,
            metadata={"error": "missing_script", "path": str(script_path)},
        )
        return 1

    launcher_log = _runtime_dir(hub) / "trace_service_launcher.log"
    try:
        with launcher_log.open("a", encoding="utf-8") as log_fh:
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(hub),
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
    except OSError as exc:
        print(f"TRACE_SERVICE_START_ERROR ({exc})")
        emit_action_receipt(
            "trace_service_start",
            exit_code=1,
            metadata={"error": str(exc)},
        )
        return 1

    _write_pid_record(
        pid_path,
        {
            "pid": process.pid,
            "started_at": spine.now_stamp(),
            "command": [sys.executable, str(script_path)],
        },
    )

    reachable, detail = _wait_for_endpoint(endpoint)
    report = {
        "status": "started" if reachable else "started_unreachable",
        "endpoint": endpoint,
        "reachable": reachable,
        "detail": detail,
        "managed_pid": process.pid,
        "pid_file": str(pid_path),
        "launcher_log": str(launcher_log),
        "run_id": spine.ensure_run_id(),
    }
    _write_state_report(paths, "trace_service_start.json", report)

    if reachable:
        print("TRACE_SERVICE_START_OK")
        emit_action_receipt(
            "trace_service_start",
            exit_code=0,
            metadata={"status": report.get("status"), "endpoint": endpoint},
        )
        return 0
    print("TRACE_SERVICE_START_WARN")
    emit_action_receipt(
        "trace_service_start",
        exit_code=1,
        metadata={"status": report.get("status"), "endpoint": endpoint},
    )
    return 1


def handle_trace_service_stop(paths: RepoPaths) -> int:
    print("⏹️ Trace Service Stop")
    print("=" * 50)

    spine = _spine()
    hub = cast(Path, paths.nusyq_hub)
    config = _load_and_apply_config(paths)
    if _tracing_enabled(config):
        config["enabled"] = False
        spine.save_trace_config(paths.nusyq_hub, config)
        spine.apply_trace_config(config)

    pid_path = _trace_service_pid_path(hub)
    pid_record = _read_pid_record(pid_path) or {}
    pid = int(pid_record.get("pid", 0) or 0)
    managed_stopped = True
    if pid:
        managed_stopped = _stop_pid(pid)
    if managed_stopped and pid_path.exists():
        try:
            pid_path.unlink(missing_ok=True)
        except OSError:
            pass

    endpoint = str(config.get("endpoint", DEFAULT_OTLP_ENDPOINT))
    reachable_after_stop, detail_after_stop = _trace_endpoint_check(endpoint)

    try:
        if otel:
            cast(Any, otel).shutdown_tracing()
    except (AttributeError, RuntimeError):
        pass

    report = {
        "endpoint": endpoint,
        "managed_pid": pid or None,
        "managed_stopped": managed_stopped,
        "reachable_after_stop": reachable_after_stop,
        "detail_after_stop": detail_after_stop,
        "pid_file": str(pid_path),
        "run_id": spine.ensure_run_id(),
    }
    _write_state_report(paths, "trace_service_stop.json", report)

    if managed_stopped and not reachable_after_stop:
        print("TRACE_SERVICE_STOP_OK")
        emit_action_receipt(
            "trace_service_stop",
            exit_code=0,
            metadata={"reachable_after_stop": reachable_after_stop},
        )
        return 0

    print("TRACE_SERVICE_STOP_WARN")
    emit_action_receipt(
        "trace_service_stop",
        exit_code=1,
        metadata={"reachable_after_stop": reachable_after_stop},
    )
    return 1


def handle_trace_service_healthcheck(paths: RepoPaths) -> int:
    print("🧪 Trace Service Healthcheck")
    print("=" * 50)

    # Force OTLP HTTP env for healthcheck
    os.environ.pop("OTEL_EXPORTER_OTLP_ENDPOINT", None)
    os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = "http://127.0.0.1:4318/v1/traces"
    os.environ["OTEL_EXPORTER_OTLP_PROTOCOL"] = "http/protobuf"
    os.environ["OTEL_EXPORTER_OTLP_TRACES_PROTOCOL"] = "http/protobuf"

    config = _load_and_apply_config(paths)
    endpoint = config.get("endpoint", DEFAULT_OTLP_ENDPOINT)
    enabled_flag = _tracing_enabled(config)
    if enabled_flag:
        health = _collector_health(str(endpoint), managed_running=False)
        reachable = bool(health["reachable"])
        detail = str(health["detail"])
    else:
        reachable, detail = False, "disabled"
    tracer_available = bool(otel)
    tracer_enabled = bool(
        enabled_flag and otel and cast(Any, otel).init_tracing(config.get("service_name", "nusyq-hub"))
    )

    spine = _spine()
    report = {
        "enabled": tracer_enabled,
        "tracer_available": tracer_available,
        "endpoint": endpoint,
        "reachable": reachable,
        "detail": detail,
        "probe_method": health.get("probe_method") if enabled_flag else "disabled",
        "run_id": spine.ensure_run_id(),
    }
    _write_state_report(paths, "trace_service_healthcheck.json", report)

    # Healthcheck should primarily validate transport reachability.
    # In environments where the tracer backend is optional/unavailable,
    # reachable OTLP endpoint is sufficient for an OK status.
    if reachable and (tracer_enabled or not tracer_available):
        print("TRACE_HEALTHCHECK_OK")
        emit_action_receipt(
            "trace_service_healthcheck",
            exit_code=0,
            metadata={"reachable": reachable, "tracer_enabled": tracer_enabled},
        )
        return 0
    print("TRACE_HEALTHCHECK_WARN")
    emit_action_receipt(
        "trace_service_healthcheck",
        exit_code=1,
        metadata={"reachable": reachable, "tracer_enabled": tracer_enabled},
    )
    return 1


# --- Config ops ------------------------------------------------------------


def handle_trace_config_show(paths: RepoPaths) -> int:
    print("📄 Trace Config Show")
    print("=" * 50)

    spine = _spine()
    config = spine.load_trace_config(paths.nusyq_hub)
    report_path = _write_state_report(paths, "trace_config.json", config)
    print(f"Report: {report_path}")
    emit_action_receipt(
        "trace_config_show",
        exit_code=0,
        metadata={"report_path": str(report_path)},
    )
    return 0


def _parse_value(value: str) -> object:
    vlow = value.lower()
    if vlow in {"true", "false"}:
        return vlow == "true"
    try:
        return float(value) if "." in value else int(value)
    except ValueError:
        return value


def _parse_kv_args(args: list[str]) -> dict[str, object]:
    updates: dict[str, object] = {}
    for arg in args:
        if arg.startswith("--") and "=" in arg:
            key, value = arg[2:].split("=", 1)
            key_norm = key.replace("-", "_")
            updates[key_norm] = _parse_value(value)
    return updates


def handle_trace_config_set(args: list[str], paths: RepoPaths) -> int:
    print("✍️ Trace Config Set")
    print("=" * 50)

    spine = _spine()
    config = spine.load_trace_config(paths.nusyq_hub)
    updates = parse_kv_args(args[1:])
    config.update(updates)
    spine.save_trace_config(paths.nusyq_hub, config)
    spine.apply_trace_config(config)
    print("TRACE_CONFIG_SET_OK")
    emit_action_receipt(
        "trace_config_set",
        exit_code=0,
        metadata={"updated_keys": list(updates.keys())},
    )
    return 0


def handle_trace_config_validate(paths: RepoPaths) -> int:
    print("✅ Trace Config Validate")
    print("=" * 50)

    spine = _spine()
    config = spine.load_trace_config(paths.nusyq_hub)
    endpoint = config.get("endpoint")
    exporter = config.get("exporter")
    errors = []

    if not endpoint:
        errors.append("missing endpoint")
    if exporter not in {"otlp", "otlp_http", "console", "none"}:
        errors.append("unknown exporter")

    report = {
        "valid": len(errors) == 0,
        "errors": errors,
        "config": config,
        "run_id": spine.ensure_run_id(),
    }
    _write_state_report(paths, "trace_config_validation.json", report)
    if report["valid"]:
        print("TRACE_CONFIG_VALID")
        emit_action_receipt(
            "trace_config_validate",
            exit_code=0,
            metadata={"valid": True},
        )
        return 0
    print("TRACE_CONFIG_INVALID")
    emit_action_receipt(
        "trace_config_validate",
        exit_code=1,
        metadata={"valid": False, "errors": errors},
    )
    return 1


# --- Smoke & assert --------------------------------------------------------


def handle_trace_smoke(paths: RepoPaths) -> int:
    print("🔥 Trace Smoke")
    print("=" * 50)

    config = _load_and_apply_config(paths)
    config_enabled = _tracing_enabled(config)
    endpoint = str(config.get("endpoint", DEFAULT_OTLP_ENDPOINT))

    otel_bridge, otel_source, otel_import_error = _resolve_otel_bridge()
    init_error = ""
    runtime_enabled = False
    if config_enabled and otel_bridge:
        try:
            runtime_enabled = bool(cast(Any, otel_bridge).init_tracing(config.get("service_name", "nusyq-hub")))
        except (AttributeError, RuntimeError) as exc:
            init_error = str(exc)
            runtime_enabled = False

    collector_probe_method = "disabled"
    if config_enabled:
        collector_health = _collector_health(endpoint, managed_running=False)
        collector_reachable = bool(collector_health["reachable"])
        collector_detail = str(collector_health["detail"])
        collector_probe_method = str(collector_health.get("probe_method") or "python")
    else:
        collector_reachable, collector_detail = False, "tracing disabled in config"

    trace_id, span_id = ("n/a", "n/a")
    if otel_bridge and runtime_enabled:
        with cast(Any, otel_bridge).start_action_span("nusyq.trace.smoke", {"action.id": "trace_smoke"}):
            trace_id, span_id = cast(Any, otel_bridge).current_trace_ids()

    if not config_enabled:
        failure_reason = "config_disabled"
    elif not otel_bridge:
        failure_reason = "otel_module_unavailable"
    elif init_error:
        failure_reason = "otel_init_error"
    elif not runtime_enabled:
        failure_reason = "otel_runtime_disabled"
    elif trace_id == "n/a":
        failure_reason = "no_active_trace_context"
    elif not collector_reachable:
        failure_reason = "collector_unreachable"
    else:
        failure_reason = "none"

    spine = _spine()
    report = {
        "enabled": runtime_enabled,
        "config_enabled": config_enabled,
        "module_available": bool(otel_bridge),
        "module_source": otel_source,
        "module_import_error": otel_import_error,
        "runtime_enabled": runtime_enabled,
        "init_error": init_error or None,
        "endpoint": endpoint,
        "collector_reachable": collector_reachable,
        "collector_detail": collector_detail,
        "collector_probe_method": collector_probe_method,
        "failure_reason": failure_reason,
        "trace_id": trace_id,
        "span_id": span_id,
        "run_id": spine.ensure_run_id(),
    }
    _write_state_report(paths, "trace_smoke.json", report)

    if trace_id != "n/a":
        print("TRACE_SMOKE_OK")
        emit_action_receipt(
            "trace_smoke",
            exit_code=0,
            metadata={"trace_id": trace_id, "failure_reason": failure_reason},
        )
        return 0
    print("TRACE_SMOKE_WARN")
    emit_action_receipt(
        "trace_smoke",
        exit_code=1,
        metadata={"trace_id": trace_id, "failure_reason": failure_reason},
    )
    return 1


def handle_trace_assert(args: list[str], paths: RepoPaths) -> int:
    print("🔍 Trace Assert")
    print("=" * 50)

    action_id = None
    for arg in args[1:]:
        if arg.startswith("--action="):
            action_id = arg.split("=", 1)[1]
    if not action_id and len(args) > 1:
        action_id = args[1]
    if not action_id:
        print("TRACE_ASSERT_ERROR (missing action id)")
        emit_action_receipt(
            "trace_assert",
            exit_code=1,
            metadata={"error": "missing_action_id"},
        )
        return 1

    spine = _spine()
    hub = cast(Path, paths.nusyq_hub)
    receipts_dir = _receipt_dir(hub)
    receipts = sorted(receipts_dir.glob(f"{action_id}_*.txt"), reverse=True)
    trace_id = "n/a"
    receipt_path: Path | None = None
    if receipts:
        receipt_path = receipts[0]
        assert receipt_path is not None
        content = receipt_path.read_text(encoding="utf-8", errors="replace")
        for line in content.splitlines():
            if line.startswith("trace_id:"):
                trace_id = line.split(":", 1)[1].strip()
                break

    report = {
        "action_id": action_id,
        "trace_id": trace_id,
        "receipt_path": str(receipt_path) if receipt_path else None,
        "run_id": spine.ensure_run_id(),
    }
    _write_state_report(paths, f"trace_assert_{action_id}.json", report)

    if trace_id != "n/a":
        print("TRACE_ASSERT_OK")
        emit_action_receipt(
            "trace_assert",
            exit_code=0,
            metadata={"action_id": action_id, "trace_id": trace_id},
        )
        return 0
    print("TRACE_ASSERT_WARN")
    emit_action_receipt(
        "trace_assert",
        exit_code=1,
        metadata={"action_id": action_id, "trace_id": trace_id},
    )
    return 1


# --- Correlation flags -----------------------------------------------------


def handle_trace_correlation_on(paths: RepoPaths) -> int:
    print("🔗 Trace Correlation On")
    print("=" * 50)

    spine = _spine()
    run_id = spine.ensure_run_id()
    payload = {
        "enabled": True,
        "run_id": run_id,
        "timestamp": spine.now_stamp(),
    }
    _write_state_report(paths, TRACE_CORRELATION_FILENAME, payload)
    print("TRACE_CORRELATION_ON")
    emit_action_receipt("trace_correlation_on", exit_code=0)
    return 0


def handle_trace_correlation_off(paths: RepoPaths) -> int:
    print("🔌 Trace Correlation Off")
    print("=" * 50)

    spine = _spine()
    payload = {
        "enabled": False,
        "run_id": spine.ensure_run_id(),
        "timestamp": spine.now_stamp(),
    }
    _write_state_report(paths, TRACE_CORRELATION_FILENAME, payload)
    print("TRACE_CORRELATION_OFF")
    emit_action_receipt("trace_correlation_off", exit_code=0)
    return 0


# --- Doctor ----------------------------------------------------------------


def handle_trace_doctor(paths: RepoPaths) -> int:
    """Validate tracing env + collector reachability + emit a test span, write report."""
    print("🩻 Trace Doctor")
    print("=" * 50)

    config = _load_and_apply_config(paths)
    enabled_flag = _tracing_enabled(config)

    hub = cast(Path, paths.nusyq_hub)
    reports_dir = hub / "docs" / "tracing"
    reports_dir.mkdir(parents=True, exist_ok=True)

    otel_bridge, otel_source, otel_import_error = _resolve_otel_bridge()
    init_error = ""
    runtime_enabled = False
    try:
        runtime_enabled = bool(enabled_flag and otel_bridge and cast(Any, otel_bridge).init_tracing("nusyq-hub"))
    except (AttributeError, RuntimeError) as exc:
        runtime_enabled = False
        init_error = str(exc)

    endpoint = str(config.get("endpoint") or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", DEFAULT_OTLP_ENDPOINT))
    collector_probe_method = "disabled"
    if enabled_flag:
        collector_health = _collector_health(endpoint, managed_running=False)
        reachable = bool(collector_health["reachable"])
        detail = str(collector_health["detail"])
        collector_probe_method = str(collector_health.get("probe_method") or "python")
    else:
        reachable, detail = False, "tracing disabled in config"

    # Emit a test span
    trace_id, span_id = "n/a", "n/a"
    try:
        if otel_bridge and runtime_enabled:
            with cast(Any, otel_bridge).start_action_span("nusyq.trace.doctor", {"nusyq.repo": str(paths.nusyq_hub)}):
                trace_id, span_id = cast(Any, otel_bridge).current_trace_ids()
    except (AttributeError, RuntimeError):
        pass

    if not enabled_flag:
        diagnosis = "config_disabled"
    elif not otel_bridge:
        diagnosis = "otel_module_unavailable"
    elif init_error:
        diagnosis = "otel_init_error"
    elif not runtime_enabled:
        diagnosis = "otel_runtime_disabled"
    elif trace_id == "n/a":
        diagnosis = "no_active_trace_context"
    elif not reachable:
        diagnosis = "collector_unreachable"
    else:
        diagnosis = "healthy"

    # Build report
    report = []
    report.append("# Trace Doctor Report\n\n")
    report.append(f"- Config Enabled: {enabled_flag}\n")
    report.append(f"- Runtime Enabled: {runtime_enabled}\n")
    report.append(f"- OTel Module Available: {bool(otel_bridge)}\n")
    report.append(f"- OTel Module Source: {otel_source}\n")
    if otel_import_error:
        report.append(f"- OTel Import Error: {otel_import_error}\n")
    if init_error:
        report.append(f"- Init Error: {init_error}\n")
    report.append(f"- Endpoint: {endpoint}\n")
    report.append(f"- Reachable: {reachable} ({detail})\n")
    report.append(f"- Probe Method: {collector_probe_method}\n")
    report.append(f"- trace_id: {trace_id}\n")
    report.append(f"- span_id: {span_id}\n")
    report.append(f"- Diagnosis: {diagnosis}\n")

    report_path = reports_dir / "TRACE_DOCTOR_REPORT.md"
    report_path.write_text("".join(report), encoding="utf-8")
    _write_state_report(
        paths,
        "trace_doctor.json",
        {
            "config_enabled": enabled_flag,
            "runtime_enabled": runtime_enabled,
            "module_available": bool(otel_bridge),
            "module_source": otel_source,
            "module_import_error": otel_import_error,
            "init_error": init_error or None,
            "endpoint": endpoint,
            "reachable": reachable,
            "detail": detail,
            "probe_method": collector_probe_method,
            "trace_id": trace_id,
            "span_id": span_id,
            "diagnosis": diagnosis,
            "run_id": _spine().ensure_run_id(),
        },
    )
    print(f"\n📄 Report saved: {report_path}")
    emit_action_receipt(
        "trace_doctor",
        exit_code=0,
        metadata={
            "report_path": str(report_path),
            "reachable": reachable,
            "diagnosis": diagnosis,
            "runtime_enabled": runtime_enabled,
        },
    )
    return 0
