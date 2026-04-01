"""Consolidated health check system for NuSyQ-Hub.
[ROUTE METRICS] 📊

Modes:
    fast    - Environment checks only (~2s)
    full    - Environment + code quality + AI systems (~30s)
    startup - AI health check with gating (--require, --min-score)

Formats:
    json    - Machine-readable JSON
    human   - Human-readable table

Examples:
    python scripts/integration_health_check.py                 # Fast JSON
    python scripts/integration_health_check.py --mode full --format human
    python scripts/integration_health_check.py --mode startup --require ollama chatdev
"""

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

SIMULATEDVERSE_RUNTIME_MODES = {"auto", "always_on", "off"}
SIMULATEDVERSE_MODE_ALIASES = {
    "always-on": "always_on",
    "always": "always_on",
    "on": "always_on",
    "disabled": "off",
    "none": "off",
}

PROBE_BLOCKED_ERROR_MARKERS = (
    "operation not permitted",
    "permission denied",
    "access is denied",
    "sandbox(denied",
    "winerror 5",
    "permissionerror",
)


def _is_probe_blocked_error(detail: object) -> bool:
    """Detect runtime/sandbox permission failures distinct from service-down signals."""
    if detail is None:
        return False
    if isinstance(detail, dict):
        return any(_is_probe_blocked_error(value) for value in detail.values())
    if isinstance(detail, (list, tuple, set)):
        return any(_is_probe_blocked_error(value) for value in detail)
    text = str(detail).strip().lower()
    if not text:
        return False
    if "[errno 1]" in text:
        return True
    return any(marker in text for marker in PROBE_BLOCKED_ERROR_MARKERS)


def _ensure_scheme(url: str) -> str:
    return url if "://" in url else f"http://{url}"


def _normalize_host_and_port(url: str, default_port: str) -> str:
    parsed = urlparse(_ensure_scheme(url))
    if parsed.port:
        return parsed.geturl().rstrip("/")
    netloc = f"{parsed.hostname}:{default_port}" if parsed.hostname else f"127.0.0.1:{default_port}"
    return f"{parsed.scheme}://{netloc}"


def _is_wsl() -> bool:
    """Return True when running inside WSL."""
    if os.getenv("WSL_DISTRO_NAME"):
        return True
    try:
        return "microsoft" in Path("/proc/version").read_text(encoding="utf-8").lower()
    except OSError:
        return False


def _resolve_filesystem_path(raw_path: str) -> Path:
    """Resolve Windows-style env paths to current filesystem semantics.

    On WSL, convert `C:\\foo\\bar` style paths to `/mnt/c/foo/bar` so existence
    checks reflect the real mounted filesystem state.
    """
    text = raw_path.strip().strip('"').strip("'")
    match = re.match(r"^([a-zA-Z]):[\\/](.*)$", text)
    if match and os.name != "nt":
        drive = match.group(1).lower()
        remainder = match.group(2).replace("\\", "/")
        return Path("/mnt") / drive / remainder

    candidate = Path(text)
    if candidate.exists():
        return candidate
    if not _is_wsl():
        return candidate
    if not match:
        return candidate
    drive = match.group(1).lower()
    remainder = match.group(2).replace("\\", "/")
    return Path("/mnt") / drive / remainder


def _read_dotenv_pairs(path: Path) -> dict[str, str]:
    """Parse dotenv file into key/value pairs."""
    pairs: dict[str, str] = {}
    if not path.exists():
        return pairs
    try:
        for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if not key:
                continue
            value = value.strip()
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            pairs[key] = value
    except Exception:
        return {}
    return pairs


def _hydrate_env_from_dotenv_files() -> None:
    """Hydrate env vars from local dotenv files with explicit precedence.

    Precedence: shell > .env.workspace > .env > .env.docker
    """
    root = Path(__file__).resolve().parents[1]
    shell_env_keys = {k for k, v in os.environ.items() if str(v).strip()}

    for key, value in _read_dotenv_pairs(root / ".env").items():
        if key not in os.environ or not str(os.environ.get(key, "")).strip():
            os.environ[key] = value

    for key, value in _read_dotenv_pairs(root / ".env.workspace").items():
        if key in shell_env_keys:
            continue
        os.environ[key] = value

    for key, value in _read_dotenv_pairs(root / ".env.docker").items():
        if key not in os.environ or not str(os.environ.get(key, "")).strip():
            os.environ[key] = value


def _wsl_default_gateway_ip() -> str | None:
    """Resolve WSL default gateway IP for Windows-host service probing."""
    try:
        result = subprocess.run(
            ["ip", "route"],
            capture_output=True,
            text=True,
            check=False,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    if result.returncode != 0 or not result.stdout:
        return None

    for line in result.stdout.splitlines():
        stripped = line.strip()
        if not stripped.startswith("default "):
            continue
        parts = stripped.split()
        if "via" in parts:
            via_index = parts.index("via")
            if via_index + 1 < len(parts):
                return parts[via_index + 1]
    return None


def _looks_like_localhost_base(url: str) -> bool:
    """Check whether URL points to localhost-style hostnames."""
    parsed = urlparse(_ensure_scheme(url))
    host = (parsed.hostname or "").strip().lower()
    return host in {"127.0.0.1", "localhost"}


def _with_host(url: str, host: str) -> str:
    """Return URL with host replaced while preserving scheme/path/port."""
    parsed = urlparse(_ensure_scheme(url))
    scheme = parsed.scheme or "http"
    port = parsed.port
    host_part = f"{host}:{port}" if port else host
    return f"{scheme}://{host_part}".rstrip("/")


def _host_resolves(host: str | None) -> bool:
    """Return True when a hostname resolves in the current runtime."""
    if not host:
        return False
    try:
        socket.getaddrinfo(host, None)
        return True
    except socket.gaierror:
        return False


def _resolve_ollama_url() -> str:
    candidates = []

    if get_ollama_host:
        try:
            candidates.append(get_ollama_host())
        except (AttributeError, RuntimeError, TypeError):
            candidates.append(None)

    if ServiceConfig:
        try:
            candidates.append(ServiceConfig.get_ollama_url())
        except (AttributeError, RuntimeError, TypeError):
            candidates.append(None)

    candidates.extend(
        [
            os.getenv("OLLAMA_BASE_URL"),
            os.getenv("OLLAMA_HOST"),
        ]
    )

    for cand in candidates:
        if cand:
            normalized = _normalize_host_and_port(cand, os.getenv("OLLAMA_PORT", "11434"))
            parsed = urlparse(_ensure_scheme(normalized))
            host = (parsed.hostname or "").strip().lower()
            if host in {"ollama", "host.docker.internal"} and not _host_resolves(host):
                return _normalize_host_and_port("http://127.0.0.1", os.getenv("OLLAMA_PORT", "11434"))
            if host and not _looks_like_localhost_base(normalized) and not _host_resolves(host):
                return _normalize_host_and_port("http://127.0.0.1", os.getenv("OLLAMA_PORT", "11434"))
            return normalized

    return _normalize_host_and_port("http://127.0.0.1", os.getenv("OLLAMA_PORT", "11434"))


def _resolve_lm_studio_url() -> str:
    base = os.getenv("LM_STUDIO_BASE_URL") or os.getenv("LM_STUDIO_HOST") or "http://127.0.0.1"
    return _normalize_host_and_port(base.strip(), os.getenv("LM_STUDIO_PORT", "1234").strip())


def _resolve_dev_mentor_url() -> str:
    base = os.getenv("DEV_MENTOR_BASE_URL") or os.getenv("TERMINAL_DEPTHS_URL") or "http://127.0.0.1"
    return _normalize_host_and_port(base.strip(), os.getenv("DEV_MENTOR_PORT", "7337").strip())


def _resolve_chatdev_adapter_url() -> str:
    base = os.getenv("CHATDEV_ADAPTER_BASE_URL") or "http://127.0.0.1"
    return _normalize_host_and_port(base.strip(), os.getenv("CHATDEV_ADAPTER_PORT", "4466").strip())


def _resolve_hub_api_url() -> str:
    base = os.getenv("NUSYQ_HUB_BASE_URL") or "http://127.0.0.1"
    return _normalize_host_and_port(base.strip(), os.getenv("NUSYQ_HUB_PORT", "8000").strip())


def _resolve_gitnexus_url() -> str:
    base = os.getenv("GITNEXUS_BASE_URL") or "http://127.0.0.1"
    return _normalize_host_and_port(base.strip(), os.getenv("GITNEXUS_PORT", "9001").strip())


def _probe_url_candidates(
    candidates: list[tuple[str, str]],
    out: dict,
    status_key: str,
    base_key: str,
    probe_blocked_reason: str = "network_probe_blocked",
) -> None:
    errors = []
    non_blocking_error = False
    probe_blocked_count = 0
    for base, path in candidates:
        try:
            r = requests.get(f"{base}{path}", timeout=3)
            if r.status_code < 400:
                out[base_key] = base
                out[status_key] = {"ok": True, "code": r.status_code, "path": path}
                return
            errors.append({f"{base}{path}": f"HTTP {r.status_code}"})
            non_blocking_error = True
        except Exception as e:
            error_text = str(e)
            errors.append({f"{base}{path}": error_text})
            if _is_probe_blocked_error(error_text):
                probe_blocked_count += 1
            else:
                non_blocking_error = True

    status: dict[str, object] = {"ok": False, "error": errors or "unreachable"}
    if probe_blocked_count > 0 and not non_blocking_error:
        status["probe_blocked"] = True
        status["reason"] = probe_blocked_reason
    out[status_key] = status


def _probe_windows_localhost_via_powershell(port: str, path: str) -> dict[str, object]:
    """Probe a Windows-local HTTP endpoint from WSL via PowerShell."""
    target = f"http://127.0.0.1:{port}{path}"
    command = [
        "powershell.exe",
        "-NoLogo",
        "-NoProfile",
        "-Command",
        (
            "$ProgressPreference='SilentlyContinue';"
            f"$r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 '{target}';"
            'Write-Output "{\"ok\":true,\"status\":"$r.StatusCode"}"'
        ),
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "error": str(exc), "target": target}

    if result.returncode != 0:
        return {
            "ok": False,
            "error": (result.stderr or result.stdout or f"powershell exit {result.returncode}").strip(),
            "target": target,
        }

    try:
        payload = json.loads((result.stdout or "").strip() or "{}")
    except json.JSONDecodeError:
        payload = {"ok": True}
    payload["target"] = target
    return payload


def _probe_gitnexus_local_cli() -> dict[str, object]:
    """Fallback probe when the GitNexus HTTP surface is not mounted."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "src.orchestration.gitnexus", "--json"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "error": str(exc)}

    if result.returncode != 0:
        return {
            "ok": False,
            "error": (result.stderr or result.stdout or f"gitnexus exit {result.returncode}").strip(),
        }

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"invalid gitnexus json: {exc}"}

    if isinstance(payload, dict) and "repos" in payload:
        repo_count = len(payload.get("repos") or {})
    elif isinstance(payload, dict) and "matrix" in payload:
        repo_count = len(payload.get("matrix") or {})
    else:
        repo_count = 0

    return {
        "ok": True,
        "probe": "local_cli",
        "repo_count": repo_count,
    }


def _resolve_simulatedverse_url() -> str:
    if ServiceConfig:
        try:
            return ServiceConfig.get_simulatedverse_url().strip().rstrip("/")
        except (AttributeError, RuntimeError, TypeError):
            pass

    base = os.getenv("SIMULATEDVERSE_BASE_URL")
    if base:
        return _normalize_host_and_port(base.strip(), os.getenv("SIMULATEDVERSE_PORT", "5002").strip())

    host = os.getenv("SIMULATEDVERSE_HOST", "http://127.0.0.1")
    return _normalize_host_and_port(host.strip(), os.getenv("SIMULATEDVERSE_PORT", "5002").strip())


def _simulatedverse_base_candidates(base_url: str) -> list[str]:
    """Build an ordered list of SimulatedVerse base URLs to probe."""
    normalized = _normalize_host_and_port(base_url, os.getenv("SIMULATEDVERSE_PORT", "5002"))
    parsed = urlparse(_ensure_scheme(normalized))
    current_port = parsed.port or int(os.getenv("SIMULATEDVERSE_PORT", "5002"))
    scheme = parsed.scheme or "http"
    host = (parsed.hostname or "127.0.0.1").strip()

    candidates = [normalized]
    # Current local minimal runtime uses 5002; older configs may still point at 5001/5000.
    for port in (5002, 5001, 5000):
        if port == current_port:
            continue
        candidates.append(f"{scheme}://{host}:{port}")

    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = candidate.rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(key)
    return deduped


def _resolve_simulatedverse_runtime_mode(
    cli_mode: str | None = None,
) -> tuple[str, str, str | None]:
    """Resolve SimulatedVerse runtime mode from CLI/env with safe defaults."""
    if cli_mode and cli_mode.strip():
        source = "cli"
        candidate = cli_mode
    else:
        source = "env"
        candidate = os.getenv("NUSYQ_SIMULATEDVERSE_MODE") or os.getenv("SIMULATEDVERSE_MODE") or "auto"

    normalized = candidate.strip().lower().replace("-", "_")
    normalized = SIMULATEDVERSE_MODE_ALIASES.get(normalized, normalized)
    if normalized not in SIMULATEDVERSE_RUNTIME_MODES:
        return "auto", source, f"invalid simulatedverse mode '{candidate}', using auto"
    return normalized, source, None


try:
    from src.config.service_config import ServiceConfig
except ImportError:
    ServiceConfig = None

try:
    from src.utils.config_helper import get_ollama_host
except (ImportError, ModuleNotFoundError):
    get_ollama_host = None


def check_environment(simulatedverse_mode: str = "auto") -> dict:
    """Run environment and connectivity checks (fast mode)."""
    out = {}
    keys = [
        "OPENAI_API_KEY",
        "GITHUB_COPILOT_API_KEY",
        "OLLAMA_BASE_URL",
        "OLLAMA_HOST",
        "CHATDEV_PATH",
        "MCP_SERVER_URL",
        "NUSYQ_ROOT_PATH",
        "SIMULATEDVERSE_PATH",
        "CHATDEV_API_KEY",
        "GITHUB_TOKEN",
    ]
    for k in keys:
        out[k] = "SET" if os.getenv(k) else None

    for p in ["CHATDEV_PATH", "SIMULATEDVERSE_PATH", "NUSYQ_ROOT_PATH"]:
        val = os.getenv(p)
        if val:
            resolved = _resolve_filesystem_path(val)
            out[f"FS_{p}"] = {
                "exists": resolved.exists(),
                "path": val,
                "resolved_path": str(resolved),
            }

    # Git remote
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=True,
        )
        if res.stdout.strip() == "true":
            try:
                remote = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                out["git_origin"] = remote.stdout.strip()
            except subprocess.CalledProcessError as e:
                out["git_origin"] = None
                out["git_remote_err"] = (e.stderr or "").strip()
        else:
            out["git_origin"] = None
    except Exception as e:
        out["git_origin"] = None
        out["git_err"] = str(e)

    # Ollama HTTP check
    ollama_url = _resolve_ollama_url()
    out["ollama_base"] = ollama_url
    try:
        r = requests.get(f"{ollama_url}/api/tags", timeout=3)
        out["ollama_status"] = {"ok": r.status_code == 200, "code": r.status_code}
    except Exception as e:
        error_text = str(e)
        ollama_status: dict[str, object] = {"ok": False, "error": error_text}
        if _is_probe_blocked_error(error_text):
            ollama_status["probe_blocked"] = True
            ollama_status["reason"] = "network_probe_blocked"
        out["ollama_status"] = ollama_status

    # SimulatedVerse HTTP check (if configured)
    sim_url = _resolve_simulatedverse_url()
    sim_bases = _simulatedverse_base_candidates(sim_url)
    out["simulatedverse_mode"] = simulatedverse_mode
    out["simulatedverse_base"] = sim_url
    out["simulatedverse_base_candidates"] = sim_bases
    sim_paths = ["/health", "/api/health", "/healthz", "/readyz", "/status"]
    sim_ok = False
    sim_errors = []
    sim_non_blocking_error = False
    sim_probe_blocked_count = 0
    if simulatedverse_mode == "off":
        out["simulatedverse_status"] = {
            "ok": True,
            "skipped": True,
            "reason": "simulatedverse_mode_off",
        }
    else:
        for base in sim_bases:
            for path in sim_paths:
                try:
                    r = requests.get(f"{base}{path}", timeout=3)
                    if r.status_code < 400:
                        out["simulatedverse_base"] = base
                        out["simulatedverse_status"] = {
                            "ok": True,
                            "code": r.status_code,
                            "path": path,
                        }
                        sim_ok = True
                        break
                    sim_errors.append({f"{base}{path}": f"HTTP {r.status_code}"})
                    sim_non_blocking_error = True
                except Exception as e:
                    error_text = str(e)
                    sim_errors.append({f"{base}{path}": error_text})
                    if _is_probe_blocked_error(error_text):
                        sim_probe_blocked_count += 1
                    else:
                        sim_non_blocking_error = True
            if sim_ok:
                break

        # WSL fallback: localhost in WSL may not reach Windows-host service; probe via gateway IP.
        if not sim_ok and _is_wsl():
            gateway_ip = _wsl_default_gateway_ip()
            if gateway_ip:
                for local_base in sim_bases:
                    if not _looks_like_localhost_base(local_base):
                        continue
                    gateway_base = _with_host(local_base, gateway_ip)
                    for path in sim_paths:
                        try:
                            r = requests.get(f"{gateway_base}{path}", timeout=3)
                            if r.status_code < 400:
                                out["simulatedverse_base"] = gateway_base
                                out["simulatedverse_wsl_gateway_base"] = gateway_base
                                out["simulatedverse_local_base"] = local_base
                                out["simulatedverse_status"] = {
                                    "ok": True,
                                    "code": r.status_code,
                                    "path": path,
                                    "probe": "wsl_gateway",
                                    "gateway_ip": gateway_ip,
                                }
                                sim_ok = True
                                break
                        except Exception as gateway_exc:
                            if _is_probe_blocked_error(str(gateway_exc)):
                                sim_probe_blocked_count += 1
                            continue
                    if sim_ok:
                        break

        if not sim_ok and sim_errors:
            sim_status: dict[str, object] = {"ok": False, "error": sim_errors}
            if sim_probe_blocked_count > 0 and not sim_non_blocking_error:
                sim_status["probe_blocked"] = True
                sim_status["reason"] = "network_probe_blocked"
            out["simulatedverse_status"] = sim_status

    lm_studio_url = _resolve_lm_studio_url()
    lm_studio_port = os.getenv("LM_STUDIO_PORT", "1234").strip()
    lm_candidates = [(lm_studio_url, "/v1/models")]
    if _is_wsl() and _looks_like_localhost_base(lm_studio_url):
        gateway_ip = _wsl_default_gateway_ip()
        if gateway_ip:
            lm_candidates.append((_with_host(lm_studio_url, gateway_ip), "/v1/models"))
    out["lm_studio_base"] = lm_studio_url
    _probe_url_candidates(
        lm_candidates,
        out,
        "lm_studio_status",
        "lm_studio_base",
    )
    if not out["lm_studio_status"].get("ok") and _is_wsl():
        powershell_probe = _probe_windows_localhost_via_powershell(lm_studio_port, "/v1/models")
        if powershell_probe.get("ok"):
            out["lm_studio_base"] = f"http://127.0.0.1:{lm_studio_port}"
            out["lm_studio_status"] = {
                "ok": True,
                "probe": "windows_localhost_via_powershell",
                "target": powershell_probe["target"],
            }

    dev_mentor_url = _resolve_dev_mentor_url()
    out["dev_mentor_base"] = dev_mentor_url
    _probe_url_candidates(
        [(dev_mentor_url, "/api/health"), (dev_mentor_url, "/health")],
        out,
        "dev_mentor_status",
        "dev_mentor_base",
    )

    chatdev_adapter_url = _resolve_chatdev_adapter_url()
    out["chatdev_adapter_base"] = chatdev_adapter_url
    _probe_url_candidates(
        [(chatdev_adapter_url, "/chatdev/agents")],
        out,
        "chatdev_adapter_status",
        "chatdev_adapter_base",
    )

    hub_api_url = _resolve_hub_api_url()
    gitnexus_url = _resolve_gitnexus_url()
    out["hub_api_base"] = hub_api_url
    out["gitnexus_base"] = gitnexus_url
    _probe_url_candidates(
        [
            (hub_api_url, "/api/gitnexus/health"),
            (gitnexus_url, "/api/gitnexus/health"),
            (gitnexus_url, "/health"),
            (hub_api_url, "/health"),
        ],
        out,
        "gitnexus_status",
        "gitnexus_base",
    )
    if not out["gitnexus_status"].get("ok"):
        gitnexus_local = _probe_gitnexus_local_cli()
        if gitnexus_local.get("ok"):
            out["gitnexus_status"] = gitnexus_local

    # MCP server check
    mcp = os.getenv("MCP_SERVER_URL")
    out["mcp_server"] = mcp
    if mcp:
        tried = False
        mcp_non_blocking_error = False
        mcp_probe_blocked_count = 0
        for path in ["/status", "/health", "/"]:
            try:
                r = requests.get(mcp.rstrip("/") + path, timeout=3)
                out["mcp_status"] = {"ok": r.status_code < 400, "code": r.status_code, "path": path}
                tried = True
                break
            except Exception as e:
                error_text = str(e)
                out.setdefault("mcp_errors", []).append({path: error_text})
                if _is_probe_blocked_error(error_text):
                    mcp_probe_blocked_count += 1
                else:
                    mcp_non_blocking_error = True
        if not tried:
            out["mcp_status"] = {"ok": False}
            if mcp_probe_blocked_count > 0 and not mcp_non_blocking_error:
                out["mcp_status"]["probe_blocked"] = True
                out["mcp_status"]["reason"] = "network_probe_blocked"
    else:
        out["mcp_status"] = None

    # OpenAI library check
    try:
        import importlib

        importlib.import_module("openai")
        out["openai_installed"] = True
        out["openai_key_sets"] = bool(os.getenv("OPENAI_API_KEY"))
    except Exception as e:
        out["openai_installed"] = False
        out["openai_import_error"] = str(e)

    # Copilot key presence
    out["copilot_key_present"] = bool(os.getenv("GITHUB_COPILOT_API_KEY") or os.getenv("GITHUB_TOKEN"))

    # ChatDev path check
    chatdev = os.getenv("CHATDEV_PATH")
    if chatdev:
        p = _resolve_filesystem_path(chatdev)
        out["chatdev_exists"] = p.exists()
        out["chatdev_is_git"] = p.exists() and (p / ".git").exists()
        if (p / ".git").exists():
            try:
                remote = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    cwd=str(p),
                    capture_output=True,
                    text=True,
                    check=True,
                )
                out["chatdev_remote"] = remote.stdout.strip()
            except Exception as e:
                out["chatdev_remote_err"] = str(e)
    else:
        out["chatdev_exists"] = False

    out["hostname"] = socket.gethostname()
    return out


def check_code_quality() -> dict:
    """Run code quality checks (ruff, black, pytest smoke tests)."""
    results = {}
    ruff_timeout = int(os.getenv("NUSYQ_HEALTH_RUFF_TIMEOUT", "60"))
    black_timeout = int(os.getenv("NUSYQ_HEALTH_BLACK_TIMEOUT", "60"))
    smoke_timeout = int(os.getenv("NUSYQ_HEALTH_SMOKE_TIMEOUT", "300"))
    disabled_pytest_plugins = [
        item.strip()
        for item in os.getenv("NUSYQ_HEALTH_PYTEST_DISABLE_PLUGINS", "benchmark").split(",")
        if item.strip()
    ]
    pytest_plugin_args = [flag for plugin in disabled_pytest_plugins for flag in ("-p", f"no:{plugin}")]

    # Ruff linting
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "src/"],
            capture_output=True,
            text=True,
            timeout=ruff_timeout,
        )
        ruff_ok = result.returncode == 0
        results["ruff"] = {"ok": ruff_ok, "returncode": result.returncode}
    except Exception as e:
        results["ruff"] = {"ok": False, "error": str(e)}

    # Black formatting
    black_fallback_targets = [
        "src/orchestration/healing_cycle_scheduler.py",
        "src/agents/agent_orchestration_hub.py",
        "src/integration/unified_chatdev_bridge.py",
        "src/system/terminal_api.py",
    ]
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "src/", "--check", "--quiet"],
            capture_output=True,
            text=True,
            timeout=black_timeout,
        )
        black_ok = result.returncode == 0
        if black_ok:
            results["black"] = {"ok": True, "returncode": 0}
        else:
            black_stderr = f"{result.stdout}\n{result.stderr}"
            if not black_stderr.strip():
                # In some environments `black --quiet` fails without diagnostics.
                # Probe once without `--quiet` so we can distinguish formatter
                # findings from multiprocessing/runtime issues.
                probe = subprocess.run(
                    [sys.executable, "-m", "black", "src/", "--check"],
                    capture_output=True,
                    text=True,
                    timeout=min(black_timeout, 45),
                )
                black_stderr = f"{probe.stdout}\n{probe.stderr}"

            black_env_failure = any(
                signature in black_stderr
                for signature in (
                    "Operation not supported",
                    "SyncManager-1",
                    "multiprocessing.managers",
                    "Aborted!",
                )
            )

            if black_env_failure:
                fallback_ok = True
                failed_target = None
                for target in black_fallback_targets:
                    check = subprocess.run(
                        [sys.executable, "-m", "black", "--check", "--quiet", target],
                        capture_output=True,
                        text=True,
                        timeout=min(black_timeout, 30),
                    )
                    if check.returncode != 0:
                        fallback_ok = False
                        failed_target = target
                        break

                if fallback_ok:
                    results["black"] = {
                        "ok": True,
                        "returncode": 0,
                        "mode": "fallback_core_targets",
                        "targets_checked": black_fallback_targets,
                    }
                else:
                    results["black"] = {
                        "ok": False,
                        "returncode": 1,
                        "mode": "fallback_core_targets",
                        "failed_target": failed_target,
                    }
            else:
                results["black"] = {"ok": False, "returncode": result.returncode}
    except subprocess.TimeoutExpired:
        fallback_ok = True
        failed_target = None
        for target in black_fallback_targets:
            check = subprocess.run(
                [sys.executable, "-m", "black", "--check", "--quiet", target],
                capture_output=True,
                text=True,
                timeout=min(black_timeout, 30),
            )
            if check.returncode != 0:
                fallback_ok = False
                failed_target = target
                break

        if fallback_ok:
            results["black"] = {
                "ok": True,
                "returncode": 0,
                "mode": "fallback_core_targets_after_timeout",
                "targets_checked": black_fallback_targets,
            }
        else:
            results["black"] = {
                "ok": False,
                "timed_out": True,
                "timeout_seconds": black_timeout,
                "mode": "fallback_core_targets_after_timeout",
                "failed_target": failed_target,
            }
    except Exception as e:
        results["black"] = {"ok": False, "error": str(e)}

    # Pytest contract smoke tests (explicit suite to avoid unrelated long-running markers)
    try:
        smoke_targets = os.getenv(
            "NUSYQ_HEALTH_SMOKE_TARGETS",
            (
                "tests/test_unified_chatdev_bridge_contract.py "
                "tests/integration/test_terminal_api_smoke.py "
                "tests/smoke/test_agent_orchestration_hub_contract_smoke.py "
                "tests/test_unified_orchestration_bridge_contract.py"
            ),
        ).split()
        smoke_with_coverage = os.getenv("NUSYQ_HEALTH_SMOKE_WITH_COVERAGE", "1").strip().lower() not in {
            "0",
            "false",
            "no",
        }
        smoke_cov_targets = (
            os.getenv(
                "NUSYQ_HEALTH_SMOKE_COV_TARGETS",
                (
                    "src.agents.agent_orchestration_hub "
                    "src.integration.unified_chatdev_bridge "
                    "src.system.terminal_api "
                    "src.orchestration.unified_orchestration_bridge"
                ),
            ).split()
            if smoke_with_coverage
            else []
        )
        split_smoke = os.getenv("NUSYQ_HEALTH_SMOKE_SPLIT", "1").strip().lower() not in {
            "0",
            "false",
            "no",
        }
        split_with_coverage = os.getenv("NUSYQ_HEALTH_SMOKE_SPLIT_WITH_COVERAGE", "1").strip().lower() not in {
            "0",
            "false",
            "no",
        }

        if split_smoke:
            per_target_timeout = int(
                os.getenv(
                    "NUSYQ_HEALTH_SMOKE_PER_TARGET_TIMEOUT",
                    str(max(120, smoke_timeout // max(len(smoke_targets), 1) + 30)),
                )
            )
            target_runs: list[dict[str, object]] = []
            for target in smoke_targets:
                target_cmd = [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    target,
                    "--tb=line",
                    *pytest_plugin_args,
                ]
                if smoke_with_coverage and split_with_coverage:
                    target_cmd.extend(
                        [
                            "--cov-config=.coveragerc",
                            "--cov-report=term-missing",
                            "--cov-fail-under=0",
                        ]
                    )
                    for cov_target in smoke_cov_targets:
                        target_cmd.append(f"--cov={cov_target}")
                try:
                    target_result = subprocess.run(
                        target_cmd,
                        capture_output=True,
                        text=True,
                        timeout=per_target_timeout,
                    )
                    target_runs.append(
                        {
                            "target": target,
                            "ok": target_result.returncode == 0,
                            "returncode": target_result.returncode,
                        }
                    )
                except subprocess.TimeoutExpired:
                    target_runs.append(
                        {
                            "target": target,
                            "ok": False,
                            "timed_out": True,
                            "timeout_seconds": per_target_timeout,
                        }
                    )

            pytest_ok = all(bool(run.get("ok")) for run in target_runs)
            results["pytest_smoke"] = {
                "ok": pytest_ok,
                "mode": "per_target",
                "targets": target_runs,
                "coverage_enabled": smoke_with_coverage and split_with_coverage,
            }
        else:
            pytest_cmd = [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                *smoke_targets,
                "--tb=line",
                *pytest_plugin_args,
            ]
            if smoke_with_coverage:
                pytest_cmd.extend(
                    [
                        "--cov-config=.coveragerc",
                        "--cov-report=term-missing",
                        "--cov-fail-under=0",
                    ]
                )
                for cov_target in smoke_cov_targets:
                    pytest_cmd.append(f"--cov={cov_target}")
            result = subprocess.run(
                pytest_cmd,
                capture_output=True,
                text=True,
                timeout=smoke_timeout,
            )
            pytest_ok = result.returncode == 0
            results["pytest_smoke"] = {
                "ok": pytest_ok,
                "mode": "combined",
                "returncode": result.returncode,
                "coverage_enabled": smoke_with_coverage,
            }
    except subprocess.TimeoutExpired:
        results["pytest_smoke"] = {
            "ok": False,
            "timed_out": True,
            "timeout_seconds": smoke_timeout,
        }
    except Exception as e:
        results["pytest_smoke"] = {"ok": False, "error": str(e)}

    return results


def check_ai_systems() -> dict:
    """Run AI systems health probe (requires src.system.ai_health_probe)."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from system.ai_health_probe import run_full_health_check

        report = run_full_health_check(timeout_per_system=5)

        if hasattr(report, "results"):
            # Backward compatibility with older report shape.
            system_statuses = {s: r.status for s, r in report.results.items()}
        else:
            system_statuses = {
                "ollama": ("available" if getattr(report.ollama, "available", False) else "unavailable"),
                "chatdev": ("available" if getattr(report.chatdev, "available", False) else "unavailable"),
                "quantum": ("available" if getattr(report.quantum, "available", False) else "unavailable"),
            }

        return {
            "overall_score": report.overall_score,
            "available_systems": report.get_available_systems(),
            "unavailable_systems": report.get_unavailable_systems(),
            "system_statuses": system_statuses,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def format_human(data: dict, mode: str) -> str:
    """Format health check results in human-readable format."""
    lines = []
    lines.append("=" * 70)
    lines.append(f"🏥 NuSyQ-Hub Health Check ({mode.upper()})")
    lines.append("=" * 70)

    # Environment section
    if "environment" in data:
        lines.append("\n📦 ENVIRONMENT")
        lines.append("-" * 70)
        env = data["environment"]

        for key in ["OPENAI_API_KEY", "GITHUB_COPILOT_API_KEY", "OLLAMA_BASE_URL", "CHATDEV_PATH"]:
            status = "✅ SET" if env.get(key) == "SET" else "❌ NOT SET"
            lines.append(f"  {key:30s} {status}")

        # Ollama connectivity
        ollama = env.get("ollama_status", {})
        ollama_status = "✅ OK" if ollama.get("ok") else f"❌ FAIL ({ollama.get('error', 'unknown')})"
        lines.append(f"  {'Ollama HTTP':30s} {ollama_status}")

        # SimulatedVerse connectivity
        sim = env.get("simulatedverse_status", {})
        sim_status = "✅ OK" if sim.get("ok") else f"❌ FAIL ({sim.get('error', 'unknown')})"
        lines.append(f"  {'SimulatedVerse HTTP':30s} {sim_status}")

        lm_studio = env.get("lm_studio_status", {})
        lm_studio_status = "✅ OK" if lm_studio.get("ok") else f"❌ FAIL ({lm_studio.get('error', 'unknown')})"
        lines.append(f"  {'LM Studio HTTP':30s} {lm_studio_status}")

        dev_mentor = env.get("dev_mentor_status", {})
        dev_mentor_status = "✅ OK" if dev_mentor.get("ok") else f"❌ FAIL ({dev_mentor.get('error', 'unknown')})"
        lines.append(f"  {'Dev-Mentor HTTP':30s} {dev_mentor_status}")

        chatdev = env.get("chatdev_adapter_status", {})
        chatdev_status = "✅ OK" if chatdev.get("ok") else f"❌ FAIL ({chatdev.get('error', 'unknown')})"
        lines.append(f"  {'ChatDev Adapter':30s} {chatdev_status}")

        gitnexus = env.get("gitnexus_status", {})
        gitnexus_status = "✅ OK" if gitnexus.get("ok") else f"❌ FAIL ({gitnexus.get('error', 'unknown')})"
        lines.append(f"  {'GitNexus HTTP':30s} {gitnexus_status}")

    # Code quality section
    if "code_quality" in data:
        lines.append("\n🔍 CODE QUALITY")
        lines.append("-" * 70)
        cq = data["code_quality"]

        ruff_status = "✅ PASS" if cq.get("ruff", {}).get("ok") else "❌ FAIL"
        lines.append(f"  {'Ruff Linting':30s} {ruff_status}")

        black_status = "✅ PASS" if cq.get("black", {}).get("ok") else "❌ FAIL"
        lines.append(f"  {'Black Formatting':30s} {black_status}")

        pytest_status = "✅ PASS" if cq.get("pytest_smoke", {}).get("ok") else "❌ FAIL"
        lines.append(f"  {'Pytest Smoke Tests':30s} {pytest_status}")

    # AI systems section
    if "ai_systems" in data:
        lines.append("\n🤖 AI SYSTEMS")
        lines.append("-" * 70)
        ai = data["ai_systems"]

        if "overall_score" in ai:
            score = ai["overall_score"]
            score_emoji = "✅" if score >= 0.66 else "⚠️" if score >= 0.33 else "❌"
            lines.append(f"  {'Overall Health':30s} {score_emoji} {score:.2f}")

            avail = ai.get("available_systems", [])
            unavail = ai.get("unavailable_systems", [])
            lines.append(f"  {'Available':30s} {', '.join(avail) if avail else 'None'}")
            lines.append(f"  {'Unavailable':30s} {', '.join(unavail) if unavail else 'None'}")
        else:
            lines.append(f"  Error: {ai.get('error', 'Unknown')}")

    # Summary
    if "duration" in data:
        lines.append(f"\n⏱️  Total time: {data['duration']:.1f}s")

    lines.append("=" * 70)
    return "\n".join(lines)


def main():
    _hydrate_env_from_dotenv_files()

    parser = argparse.ArgumentParser(description="NuSyQ-Hub consolidated health check")
    parser.add_argument(
        "--mode",
        choices=["fast", "full", "startup"],
        default="fast",
        help="Health check mode (default: fast)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "human"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--require",
        nargs="+",
        choices=["ollama", "chatdev", "quantum"],
        help="(startup mode) Require specific AI systems",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.66,
        help="(startup mode) Minimum health score to pass (default: 0.66)",
    )
    parser.add_argument(
        "--simulatedverse-mode",
        dest="simulatedverse_mode",
        default=None,
        help="SimulatedVerse runtime policy: auto|always_on|off (default: env or auto)",
    )
    parser.add_argument(
        "--simulatedverse-policy",
        dest="simulatedverse_policy",
        default=None,
        help=argparse.SUPPRESS,
    )

    args = parser.parse_args()
    requested_mode = args.simulatedverse_mode or args.simulatedverse_policy
    simulatedverse_mode, mode_source, mode_warning = _resolve_simulatedverse_runtime_mode(requested_mode)

    start_time = time.time()
    result = {
        "mode": args.mode,
        "simulatedverse_mode": simulatedverse_mode,
        "simulatedverse_mode_source": mode_source,
        "simulatedverse_mode_warning": mode_warning,
    }

    # Always check environment
    result["environment"] = check_environment(simulatedverse_mode=simulatedverse_mode)

    # Add code quality for full mode
    if args.mode in ["full"]:
        result["code_quality"] = check_code_quality()

    # Add AI systems for full/startup modes
    if args.mode in ["full", "startup"]:
        result["ai_systems"] = check_ai_systems()

    result["duration"] = time.time() - start_time

    # Output formatting
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(format_human(result, args.mode))

    # Startup mode gating
    if args.mode == "startup":
        ai = result.get("ai_systems", {})

        if args.require:
            unavail = ai.get("unavailable_systems", [])
            missing = [s for s in args.require if s in unavail]
            if missing:
                print(f"\n❌ Required systems unavailable: {', '.join(missing)}", file=sys.stderr)
                return 1
        else:
            score = ai.get("overall_score", 0.0)
            if score < args.min_score:
                print(
                    f"\n❌ Health score {score:.2f} below threshold {args.min_score}",
                    file=sys.stderr,
                )
                return 1

        print("\n✅ Health check passed. System ready.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
