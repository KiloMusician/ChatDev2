#!/usr/bin/env python3
"""Utility to validate the tripartite workspace (NuSyQ-Hub, SimulatedVerse, NuSyQ)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env.workspace"
WORKSPACE_LOADER = ROOT / ".vscode" / "workspace_loader.ps1"
COMMAND_NAMES = [
    "cdhub",
    "cdroot",
    "cdverse",
    "cdanchor",
    "cdsrc",
    "cdscripts",
    "start-system",
    "show-state",
    "error-report",
]

# External reference folders that should not live in the active tripartite IDE window.
FOREIGN_WORKSPACE_MARKERS = (
    "steamapps\\common",
    "steamapps/common",
)
STALE_LOG_THRESHOLD_SECONDS = 60 * 60
WORKSPACE_EXTENSIONS_JSON = ROOT / ".vscode" / "extensions.json"
CANONICAL_LIVE_REPORTS = (
    ROOT / "state" / "reports" / "current_state.md",
    ROOT / "state" / "reports" / "integration_status.json",
    ROOT / "state" / "reports" / "doctor_dashboard_latest.json",
    ROOT / "state" / "reports" / "unified_error_report_latest.json",
    ROOT / "state" / "reports" / "token_metrics_summary.json",
)
SETTINGS_ALIGNMENT_EXPECTATIONS: dict[str, object] = {
    "editor.codeActions.triggerOnFocusChange": False,
    "semgrep.useExperimentalLS": True,
    "semgrep.doHover": False,
    "ruff.nativeServer": "on",
}


def _read_env_file(path: Path) -> Mapping[str, str]:
    if not path.exists():
        return {}
    env: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def _load_jsonc(path: Path) -> dict:
    """Load JSON/JSONC with inline comments and trailing commas."""
    raw = path.read_text(encoding="utf-8")
    cleaned_lines = []
    for raw_line in raw.splitlines():
        line = raw_line
        in_string = False
        escaped = False
        comment_index = None
        for index, char in enumerate(line):
            if char == "\\" and not escaped:
                escaped = True
                continue
            if char == '"' and not escaped:
                in_string = not in_string
            elif not in_string and char == "/" and index + 1 < len(line) and line[index + 1] == "/":
                comment_index = index
                break
            escaped = False
        if comment_index is not None:
            line = line[:comment_index]
        if line.strip():
            cleaned_lines.append(line)
    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r",(\s*[}\]])", r"\1", cleaned)
    return json.loads(cleaned)


def _expand_value(value: str, env: Mapping[str, str]) -> str:
    pattern = re.compile(r"\$\{?([A-Z0-9_]+)\}?")
    prev = ""
    current = value
    while prev != current:
        prev = current
        for match in pattern.findall(current):
            replacement = env.get(match, os.environ.get(match, ""))
            current = current.replace(f"${{{match}}}", replacement)
            current = current.replace(f"${match}", replacement)
    return current


def _resolve_platform_path(value: str) -> Path:
    if os.name == "nt":
        return Path(value)
    win_match = re.match(r"^([A-Za-z]):[\\/](.*)", value)
    if win_match:
        drive = win_match.group(1).lower()
        rest = win_match.group(2).replace("\\", "/")
        return Path(f"/mnt/{drive}/{rest}")
    return Path(value)


def _print_status(label: str, raw_value: str) -> bool:
    path = _resolve_platform_path(raw_value)
    exists = path.exists()
    status = "✅" if exists else "❌"
    print(f"{status} {label}: {raw_value} → {path}")
    return exists


def _check_aliases(loader_path: Path, aliases: Iterable[str]) -> None:
    if not loader_path.exists():
        print(f"⚠ Workspace loader missing at {loader_path}; run workspace_loader.ps1 installer.")
        return
    content = loader_path.read_text(encoding="utf-8").lower()
    missing = []
    for alias in aliases:
        alias_token = f"-name {alias.lower()}"
        function_token = f"function {alias.lower()}"
        if alias_token not in content and function_token not in content:
            missing.append(alias)
    if missing:
        print(f"⚠ Missing aliases in workspace loader: {', '.join(missing)}")
    else:
        print("✅ All quick-command aliases/functions are defined.")


def _profile_candidates() -> Iterable[Path]:
    home = Path.home()
    yield home / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
    yield home / "Documents" / "PowerShell" / "profile.ps1"
    yield home / ".config" / "powershell" / "profile.ps1"
    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        win_home = _resolve_platform_path(userprofile)
        yield win_home / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
        yield win_home / "Documents" / "PowerShell" / "profile.ps1"
        yield win_home / "Documents" / "WindowsPowerShell" / "profile.ps1"


def _check_docker() -> None:
    """Check Docker daemon accessibility and WSL integration."""
    import subprocess

    print("\n🐋 Docker Diagnostic Check:")

    # Check docker command availability
    try:
        result = subprocess.run(
            ["docker", "version", "--format", "{{.Server.Version}}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        docker_stderr = (result.stderr or "").strip().lower()
        docker_sock = Path("/var/run/docker.sock")
        if result.returncode != 0 and "permission denied" in docker_stderr and docker_sock.exists():
            print("⚠ Docker socket is present but inaccessible from this runtime context")
            print(f"   → Socket: {docker_sock}")
            print("   → This is often a sandbox/permission boundary, not a Docker daemon failure")
            print("   → Verify with `docker ps` from PowerShell or an unsandboxed shell if needed")
            return
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Docker daemon accessible (version {version})")

            # Check running containers
            ps_result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if ps_result.returncode == 0:
                containers = [c for c in ps_result.stdout.strip().split("\n") if c]
                if containers:
                    nusyq_containers = [c for c in containers if "nusyq" in c.lower()]
                    print(f"✅ Docker running {len(containers)} containers ({len(nusyq_containers)} NuSyQ-related)")
                else:
                    print("⚠ Docker daemon running but no containers active")

            # Check compose availability
            compose_result = subprocess.run(
                ["docker", "compose", "version", "--short"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if compose_result.returncode == 0:
                compose_version = compose_result.stdout.strip()
                print(f"✅ Docker Compose available (v{compose_version})")
            else:
                print("⚠ Docker Compose not available - install Docker Desktop or docker-compose-plugin")

        else:
            print("❌ Docker daemon not accessible")
            print("   → Check Docker Desktop is running")
            print("   → Verify WSL integration enabled in Docker Desktop → Settings → Resources → WSL Integration")
            print("   → On Windows, use PowerShell; on WSL, ensure socket access")

    except FileNotFoundError:
        print("❌ Docker command not found")
        print("   → Install Docker Desktop: https://www.docker.com/products/docker-desktop")
    except subprocess.TimeoutExpired:
        print("⚠ Docker check timed out (daemon may be starting)")
    except Exception as e:
        print(f"⚠ Docker check failed: {e}")


def _vscode_logs_root_candidates() -> list[Path]:
    """Return likely VS Code logs roots across Windows + WSL."""
    candidates: list[Path] = []
    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        candidates.append(_resolve_platform_path(userprofile) / "AppData" / "Roaming" / "Code" / "logs")

    local_home = Path.home()
    candidates.append(local_home / "AppData" / "Roaming" / "Code" / "logs")
    candidates.append(local_home / ".config" / "Code" / "logs")

    seen: set[str] = set()
    deduped: list[Path] = []
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _vscode_settings_path_candidates() -> list[Path]:
    """Return likely VS Code settings.json paths across Windows + WSL."""
    candidates: list[Path] = []
    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        base = _resolve_platform_path(userprofile)
        candidates.append(base / "AppData" / "Roaming" / "Code" / "User" / "settings.json")

    local_home = Path.home()
    candidates.append(local_home / "AppData" / "Roaming" / "Code" / "User" / "settings.json")
    candidates.append(local_home / ".config" / "Code" / "User" / "settings.json")
    candidates.append(ROOT / ".vscode" / "settings.json")

    seen: set[str] = set()
    deduped: list[Path] = []
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _find_primary_user_settings_path() -> Path | None:
    """Return the first existing machine/user settings path."""
    for candidate in _vscode_settings_path_candidates():
        if candidate == ROOT / ".vscode" / "settings.json":
            continue
        if candidate.exists():
            return candidate
    return None


def _load_settings_jsonc(path: Path | None) -> dict:
    if path is None or not path.exists():
        return {}
    try:
        return _load_jsonc(path)
    except Exception:
        return {}


def _collect_settings_alignment_findings(
    workspace_settings: Mapping[str, object], user_settings: Mapping[str, object]
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    for key, expected in SETTINGS_ALIGNMENT_EXPECTATIONS.items():
        workspace_value = workspace_settings.get(key)
        user_has_value = key in user_settings
        user_value = user_settings.get(key)

        if workspace_value != expected:
            findings.append(
                {
                    "severity": "error",
                    "message": f"Workspace setting `{key}` should be `{expected!r}` but is `{workspace_value!r}`.",
                }
            )
            continue

        if user_has_value and user_value != expected:
            findings.append(
                {
                    "severity": "warning",
                    "message": (
                        f"User setting `{key}` is `{user_value!r}` while workspace forces `{expected!r}`. "
                        "This drift can still make other workspaces noisier or slower."
                    ),
                }
            )

    return findings


def _check_vscode_settings_alignment() -> None:
    """Surface workspace vs user settings drift for high-impact extension knobs."""
    print("\n⚙ VS Code Settings Alignment:")
    workspace_settings = _load_settings_jsonc(ROOT / ".vscode" / "settings.json")
    user_settings_path = _find_primary_user_settings_path()
    user_settings = _load_settings_jsonc(user_settings_path)

    findings = _collect_settings_alignment_findings(workspace_settings, user_settings)
    if not findings:
        print("✅ Workspace/user settings alignment is clean for high-impact Python/Semgrep knobs.")
        return

    for finding in findings:
        prefix = "❌" if finding["severity"] == "error" else "⚠"
        print(f"{prefix} {finding['message']}")

    if user_settings_path is not None:
        print(f"ℹ User settings path inspected: {user_settings_path}")
    print(
        "ℹ Recommendation: keep Semgrep on the experimental LS, disable focus-triggered code actions, "
        "and keep hover AST inspection off in this large workspace."
    )


def _vscode_exthost_roots() -> list[Path]:
    """Locate candidate exthost roots ordered by recency."""
    candidates: list[Path] = []
    for logs_root in _vscode_logs_root_candidates():
        if not logs_root.exists():
            continue
        sessions = sorted(
            [item for item in logs_root.iterdir() if item.is_dir()],
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        for session in sessions:
            windows = sorted(
                [item for item in session.glob("window*/exthost") if item.is_dir()],
                key=lambda item: item.stat().st_mtime,
                reverse=True,
            )
            candidates.extend(windows)

    seen: set[str] = set()
    deduped: list[Path] = []
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _find_recent_extension_logs() -> tuple[Path | None, Path | None, Path | None, Path | None]:
    """Return the freshest exthost root with relevant extension logs."""
    for exthost_root in _vscode_exthost_roots():
        output_logs = sorted(
            [item for item in exthost_root.glob("output_logging_*") if item.is_dir()],
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        latest_output = output_logs[0] if output_logs else None

        ruff_log: Path | None = None
        semgrep_log: Path | None = None
        if latest_output:
            ruff_candidates = sorted(latest_output.glob("*Ruff Language Server.log"))
            semgrep_candidates = sorted(latest_output.glob("*Semgrep (Server).log"))
            if ruff_candidates:
                ruff_log = ruff_candidates[-1]
            if semgrep_candidates:
                semgrep_log = semgrep_candidates[-1]

        isort_log = exthost_root / "ms-python.isort" / "isort.log"
        if any(path and path.exists() for path in (ruff_log, semgrep_log)) or isort_log.exists():
            return exthost_root, ruff_log, semgrep_log, isort_log

    return None, None, None, None


def _load_workspace_unwanted_extensions() -> set[str]:
    """Load unwanted extension IDs from workspace JSONC."""
    if not WORKSPACE_EXTENSIONS_JSON.exists():
        return set()
    try:
        data = _load_jsonc(WORKSPACE_EXTENSIONS_JSON)
        unwanted = data.get("unwantedRecommendations", [])
        return {str(item).strip().lower() for item in unwanted if str(item).strip()}
    except Exception:
        return set()


def _resolve_workspace_interpreter(settings_path: Path, workspace_root: Path = ROOT) -> tuple[str | None, Path | None]:
    """Resolve the configured workspace interpreter to an absolute path."""
    if not settings_path.exists():
        return None, None
    try:
        data = _load_jsonc(settings_path)
    except Exception:
        return None, None
    raw = data.get("python.defaultInterpreterPath")
    if not isinstance(raw, str) or not raw.strip():
        return None, None
    resolved_text = raw.replace("${workspaceFolder}", str(workspace_root))
    resolved_text = re.sub(
        r"\$\{env:([^}]+)\}",
        lambda match: os.environ.get(match.group(1), ""),
        resolved_text,
    )
    resolved_path = Path(resolved_text).expanduser()
    return raw, resolved_path


def _check_python_workspace_environment() -> bool:
    """Validate that VS Code points to a concrete workspace interpreter."""
    print("\n🐍 Python Workspace Environment:")
    settings_path = ROOT / ".vscode" / "settings.json"
    raw_value, resolved_path = _resolve_workspace_interpreter(settings_path, workspace_root=ROOT)
    if not raw_value or resolved_path is None:
        print("❌ python.defaultInterpreterPath missing or unreadable in .vscode/settings.json")
        return False

    if resolved_path.exists() and resolved_path.is_file():
        print(f"✅ Workspace interpreter configured: {raw_value} → {resolved_path}")
        try:
            result = subprocess.run(
                [str(resolved_path), "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            version = (result.stdout or result.stderr).strip()
            if result.returncode == 0 and version:
                print(f"✅ Interpreter executable responds: {version}")
                version_match = re.search(r"Python\s+(\d+)\.(\d+)\.(\d+)", version)
                if version_match:
                    major = int(version_match.group(1))
                    minor = int(version_match.group(2))
                    if major == 3 and minor < 11:
                        print(f"❌ Workspace interpreter is below the repo minimum: {version} (require Python 3.11+)")
                        return False
                return True
            else:
                print("⚠ Configured interpreter exists but did not respond cleanly to --version")
        except Exception as exc:
            print(f"⚠ Interpreter exists but could not be executed: {exc}")
        return False

    if resolved_path.exists() and resolved_path.is_dir():
        print(f"❌ Workspace interpreter points to a directory, not a Python executable: {resolved_path}")
        return False

    print(f"❌ Workspace interpreter does not exist: {raw_value} → {resolved_path}")
    return False


def _count_doc_report_like_files() -> int:
    """Count report/audit/session-like docs without traversing the entire docs vault."""
    report_dirs = (
        ROOT / "docs" / "Reports",
        ROOT / "docs" / "Analysis",
        ROOT / "docs" / "Agent-Sessions",
    )
    count = 0
    for report_dir in report_dirs:
        if not report_dir.exists():
            continue
        for _root, _dirs, files in os.walk(report_dir):
            count += len(files)
    return count


def _check_report_governance() -> None:
    """Surface live report contract vs archive/report sprawl."""
    print("\n🧾 Report Governance:")
    state_reports_dir = ROOT / "state" / "reports"
    live_count = len([item for item in state_reports_dir.glob("*") if item.is_file()])
    doc_report_count = _count_doc_report_like_files()
    print(f"ℹ state/reports top-level files: {live_count}")
    print(f"ℹ docs report/audit/session-like files: {doc_report_count}")

    missing = [path for path in CANONICAL_LIVE_REPORTS if not path.exists()]
    if missing:
        print("⚠ Canonical live report set is incomplete:")
        for path in missing:
            print(f"   - {path.relative_to(ROOT)}")
    else:
        print("✅ Canonical live reports present:")
        for path in CANONICAL_LIVE_REPORTS:
            print(f"   - {path.relative_to(ROOT)}")

    if live_count > 250:
        print("⚠ state/reports is crowded; prefer consuming *_latest/canonical artifacts over raw history.")


def _check_active_extension_processes() -> None:
    """Report unwanted extension processes that are actually running."""
    unwanted = _load_workspace_unwanted_extensions()
    if not unwanted:
        return

    try:
        result = subprocess.run(
            ["code", "--status"],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return

    combined = "\n".join(part for part in (result.stdout, result.stderr) if part)
    matches = re.findall(
        r"[\\/]\.vscode[\\/]+extensions[\\/]+([a-z0-9.-]+)-\d",
        combined,
        flags=re.IGNORECASE,
    )
    active_unwanted = sorted({match.lower() for match in matches if match.lower() in unwanted})
    if active_unwanted:
        print("⚠ Redundant/unwanted extension processes are still active in VS Code:")
        for extension_id in active_unwanted:
            print(f"   - {extension_id}")
        print("ℹ Recommendation: apply the Codex-Isolation disable set or reload into the focused profile.")
    else:
        print("✅ No unwanted extension processes detected in live VS Code status.")


def _read_text(path: Path, max_lines: int = 3000) -> str:
    """Read bounded text from log file."""
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return ""
    if len(lines) > max_lines:
        lines = lines[-max_lines:]
    return "\n".join(lines)


def _scan_workspace_registrations(text: str) -> list[str]:
    return re.findall(r"Registering workspace:\s*(.+)", text)


def _contains_foreign_workspace(entries: Iterable[str]) -> list[str]:
    hits: list[str] = []
    for entry in entries:
        lowered = entry.lower()
        if any(marker in lowered for marker in FOREIGN_WORKSPACE_MARKERS):
            hits.append(entry)
    return hits


def _check_vscode_extension_host_health() -> None:
    """Diagnose common VS Code extension-host contention signals."""
    print("\n🧩 VS Code Extension Host Check:")
    exthost_root, ruff_log, semgrep_log, isort_log = _find_recent_extension_logs()
    if not exthost_root:
        print("⚠ No VS Code exthost logs found (open VS Code once, then rerun).")
        _check_active_extension_processes()
        return

    if not any(path and path.exists() for path in (ruff_log, semgrep_log)) and not isort_log.exists():
        print(f"⚠ No Ruff/isort/Semgrep logs found under {exthost_root}")
        _check_active_extension_processes()
        return

    latest_log_mtime: float | None = None
    for log_path in (ruff_log, semgrep_log, isort_log if isort_log.exists() else None):
        if log_path is None or not log_path.exists():
            continue
        try:
            log_mtime = log_path.stat().st_mtime
        except OSError:
            continue
        latest_log_mtime = max(latest_log_mtime or log_mtime, log_mtime)

    if latest_log_mtime is not None:
        latest_settings_mtime: float | None = None
        for settings_path in _vscode_settings_path_candidates():
            if not settings_path.exists():
                continue
            try:
                settings_mtime = settings_path.stat().st_mtime
            except OSError:
                continue
            latest_settings_mtime = max(latest_settings_mtime or settings_mtime, settings_mtime)

        if latest_settings_mtime is not None and latest_log_mtime < latest_settings_mtime:
            log_dt = datetime.fromtimestamp(latest_log_mtime, tz=UTC).isoformat()
            settings_dt = datetime.fromtimestamp(latest_settings_mtime, tz=UTC).isoformat()
            print("ℹ VS Code extension logs are older than latest settings update; skipping stale warnings.")
            print(f"   latest_log={log_dt}, latest_settings={settings_dt}")
            print("   → Reload the VS Code window to apply the newest Semgrep/Ruff extension settings.")
            return

        age_seconds = max(0.0, datetime.now(UTC).timestamp() - latest_log_mtime)
        if age_seconds > STALE_LOG_THRESHOLD_SECONDS:
            age_minutes = int(age_seconds // 60)
            print(
                f"ℹ Latest extension-host logs are stale ({age_minutes}m old); skipping historical contention warnings."
            )
            return

    foreign_hits: list[str] = []
    if ruff_log and ruff_log.exists():
        ruff_text = _read_text(ruff_log)
        registered = _scan_workspace_registrations(ruff_text)
        foreign_hits.extend(_contains_foreign_workspace(registered))
        if "Cannot call write after a stream was destroyed" in ruff_text:
            print("❌ Ruff stream-destroyed errors detected (extension-host instability).")
        if "Stopping server timed out" in ruff_text:
            print("❌ Ruff server stop timeout detected.")

    if isort_log.exists():
        isort_text = _read_text(isort_log)
        foreign_hits.extend(
            _contains_foreign_workspace(re.findall(r"workspace\s+(.+)$", isort_text, flags=re.MULTILINE))
        )
        if "Stopping server timed out" in isort_text:
            print("❌ isort server stop timeout detected.")
        if "Client isort: connection to server is erroring" in isort_text:
            print("❌ isort client/server transport errors detected.")

    if semgrep_log and semgrep_log.exists():
        semgrep_text = _read_text(semgrep_log)
        if "positionEncoding" in semgrep_text:
            print("❌ Semgrep legacy language-server init crash detected (positionEncoding).")
        if "No such file or directory open" in semgrep_text and ".mypy_cache" in semgrep_text:
            print("❌ Semgrep attempted to open missing `.mypy_cache` artifacts during init.")
            print("ℹ Recommendation: exclude `.mypy_cache` from `semgrep.scan.exclude` and reload the VS Code window.")
        if "No such file or directory open" in semgrep_text and ".coverage" in semgrep_text:
            print("❌ Semgrep attempted to open missing '.coverage' file during init.")

    if foreign_hits:
        deduped = sorted(set(foreign_hits))
        print("❌ Foreign heavy folders detected in active IDE workspace:")
        for entry in deduped:
            print(f"   - {entry}")
        print("⚠ Recommendation: keep Steam/example folders out of the active tripartite coding window.")
    else:
        print("✅ No foreign Steam workspace registrations detected in latest extension logs.")
    _check_active_extension_processes()

    print("ℹ Stability profile:")
    print("   - Use one coding window for tripartite repos only.")
    print("   - Keep example/reference game folders in a separate read-only window.")
    print("   - Set machine-scope `isort.serverEnabled=false` in VS Code user settings.")
    print("   - Set `semgrep.useExperimentalLS=true` to avoid legacy LS crash loops.")


def main() -> int:
    print(f"Tripartite workspace verifier (root={ROOT})\n")
    overall_ok = True
    env = _read_env_file(ENV_FILE)
    if not env:
        print(f"⚠ Failed to read {ENV_FILE}; ensure the file exists with the three repo paths.")
    targets = (
        ("NuSyQ-Hub", env.get("NUSYQ_HUB", str(ROOT))),
        ("NuSyQ Root", env.get("NUSYQ_ROOT", os.environ.get("NUSYQ_ROOT", ""))),
        ("SimulatedVerse", env.get("SIMULATEDVERSE", os.environ.get("SIMULATEDVERSE", ""))),
    )
    for label, value in targets:
        if not value:
            print(f"❌ {label} path missing; set the variable in {ENV_FILE} or the environment.")
            continue
        resolved = _expand_value(value, env)
        _print_status(label, resolved)
    print()
    _print_status("Workspace loader", str(WORKSPACE_LOADER))
    _check_aliases(WORKSPACE_LOADER, COMMAND_NAMES)
    profiles = [p for p in _profile_candidates() if p.exists()]
    if not profiles:
        print("⚠ No PowerShell profile found; create one and source workspace_loader.ps1 to enable the quick commands.")
    else:
        for profile in profiles:
            print(f"✅ PowerShell profile found: {profile}")
        loader_profiles: list[Path] = []
        for profile in profiles:
            try:
                if "workspace_loader.ps1" in profile.read_text(encoding="utf-8"):
                    loader_profiles.append(profile)
            except OSError:
                continue
        if loader_profiles:
            joined = ", ".join(str(p) for p in loader_profiles)
            print(f"✅ workspace_loader.ps1 already sourced in: {joined}")
        else:
            preferred = profiles[0]
            print(f"⚠ Add '& \"{WORKSPACE_LOADER}\"' to {preferred} to auto-load the tripartite loader.")

    # Docker diagnostics
    overall_ok = _check_python_workspace_environment() and overall_ok
    _check_vscode_settings_alignment()
    _check_docker()
    _check_vscode_extension_host_health()
    _check_report_governance()

    print("\nStep-by-step sanity tips:")
    print(" 1. From a fresh shell, run one of the aliases (cdhub/cdroot/cdverse) to confirm navigation.")
    print(" 2. Run `python scripts/start_all_critical_services.py start` after cdhub.")
    print(
        " 3. Use `python scripts/start_nusyq.py` and `python scripts/start_nusyq.py error_report` from NuSyQ-Hub root."
    )
    print(
        " 4. For full auto-setup (profile wiring + env regen), run `python scripts/validate_and_setup_workspace.py --setup`."
    )
    print(" 5. For Docker issues, see docs/AGENT_TUTORIAL.md section 4 (Docker & Stack Boots).")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
