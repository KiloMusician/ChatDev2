#!/usr/bin/env python3
"""Setup and wire all NuSyQ system integrations.

This script:
1. Detects available AI systems (Ollama, ChatDev, GitHub Copilot)
2. Configures environment variables
3. Tests connectivity
4. Wires up cross-system integrations
5. Generates configuration reports

OmniTag: {
    "purpose": "system_integration_setup",
    "evolution_stage": "v1.0_comprehensive_wiring"
}
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

METACLAW_PRIVATE_KEY_ENV_KEYS = (
    "PRIVATE_KEY",
    "METACLAW_PRIVATE_KEY",
    "WALLET_PRIVATE_KEY",
    "BASE_PRIVATE_KEY",
    "ETH_PRIVATE_KEY",
    "EVM_PRIVATE_KEY",
)
METACLAW_API_KEY_ENV_KEYS = (
    "CLOWNCH_API_KEY",
    "CLAWNCHER_API_KEY",
    "METACLAW_API_KEY",
)
METACLAW_API_BASE_ENV_KEYS = (
    "CLOWNCH_API_BASE_URL",
    "CLAWNCHER_API_BASE_URL",
    "METACLAW_API_BASE_URL",
)
METACLAW_OPTIONAL_ENV_KEYS = (
    "AGENT_NAME",
    "AGENT_DESCRIPTION",
    "RPC_URL",
    "PORT",
    "HOST",
)
PROBE_BLOCKED_ERROR_MARKERS = (
    "operation not permitted",
    "permission denied",
    "access is denied",
    "sandbox(denied",
    "winerror 5",
    "permissionerror",
)


class IntegrationSetup:
    """Setup and configure all system integrations."""

    def __init__(self) -> None:
        self.repo_root = Path.cwd()
        self.config_path = self.repo_root / "config" / "secrets.json"
        self.status: dict[str, Any] = {
            "ollama": {},
            "chatdev": {},
            "simulatedverse": {},
            "nusyq_root": {},
            "hermes_agent": {},
            "metaclaw": {},
            "extensions": {},
            "environment": {},
        }

    @staticmethod
    def _coerce_path(raw_path: str | None) -> Path | None:
        """Convert Windows/WSL path strings into usable local paths."""
        if not raw_path:
            return None
        text = str(raw_path).strip()
        if not text:
            return None
        drive, sep, tail = text[:1], text[1:3], text[3:]
        if sep in {":\\", ":/"}:
            wsl_path = Path("/mnt") / drive.lower() / tail.replace("\\", "/").lstrip("/")
            if wsl_path.exists():
                return wsl_path
        candidate = Path(text).expanduser()
        return candidate if candidate.exists() else None

    @staticmethod
    def _load_jsonc(path: Path) -> dict[str, Any]:
        """Load JSON with line comments."""
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

    @staticmethod
    def _user_repo_candidates(repo_name: str) -> list[Path]:
        """Search common Windows user homes for a repo folder."""
        user_root = Path("/mnt/c/Users")
        if not user_root.exists():
            return []
        return sorted(path for path in user_root.glob(f"*/{repo_name}") if path.exists())

    @staticmethod
    def _first_existing_path(candidates: list[Path | None]) -> Path | None:
        """Return the first existing path from a list of optional candidates."""
        for candidate in candidates:
            if candidate is not None and candidate.exists():
                return candidate
        return None

    @staticmethod
    def _env_file_has_real_values(env_path: Path) -> bool:
        """Check whether an env file contains at least one non-placeholder assignment."""
        try:
            for raw_line in env_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                _key, value = line.split("=", 1)
                normalized = value.strip().strip("\"'")
                if normalized and "your_" not in normalized.lower() and "placeholder" not in normalized.lower():
                    return True
        except OSError:
            return False
        return False

    @staticmethod
    def _read_env_assignments(env_path: Path) -> dict[str, str]:
        """Parse simple KEY=VALUE assignments from an env file."""
        return IntegrationSetup._read_assignment_file(env_path, separators=("=",))

    @staticmethod
    def _read_assignment_file(path: Path, separators: tuple[str, ...] = ("=",)) -> dict[str, str]:
        """Parse simple KEY=VALUE or KEY: VALUE assignment files."""
        values: dict[str, str] = {}
        try:
            for raw_line in path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                separator = next((token for token in separators if token in line), None)
                if separator is None:
                    continue
                key, value = line.split(separator, 1)
                normalized = value.strip().strip("\"'")
                values[key.strip()] = normalized
        except OSError:
            return {}
        return values

    @staticmethod
    def _is_real_env_value(value: str | None) -> bool:
        """Return True when an env value looks configured rather than placeholder text."""
        if not value:
            return False
        normalized = value.strip().strip("\"'")
        if not normalized:
            return False
        lowered = normalized.lower()
        placeholder_tokens = (
            "your_",
            "_here",
            "placeholder",
            "0x...",
            "xxx",
            "changeme",
        )
        return not any(token in lowered for token in placeholder_tokens)

    @staticmethod
    def _load_json_file(path: Path) -> dict[str, Any]:
        """Load a JSON file when present and valid."""
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def _first_real_value(mapping: dict[str, Any], candidate_keys: tuple[str, ...]) -> tuple[str | None, str | None]:
        """Return the first configured value and the key it came from."""
        for key in candidate_keys:
            value = mapping.get(key)
            if IntegrationSetup._is_real_env_value(str(value) if value is not None else None):
                return str(value).strip().strip("\"'"), key
        return None, None

    def _collect_layered_env_assignments(self) -> dict[str, str]:
        """Collect env values using the workspace precedence contract."""
        pairs: dict[str, str] = {}
        for env_path in (
            self.repo_root / ".env.docker",
            self.repo_root / ".env",
            self.repo_root / ".env.workspace",
        ):
            for key, value in self._read_env_assignments(env_path).items():
                if self._is_real_env_value(value):
                    pairs[key] = value
        for key, value in os.environ.items():
            if self._is_real_env_value(value):
                pairs[key] = value
        return pairs

    def _collect_secrets_config(self) -> dict[str, Any]:
        """Collect config/secrets payload if present."""
        return self._load_json_file(self.config_path)

    @staticmethod
    def _merge_optional_env_values(
        env_values: dict[str, str], layered_values: dict[str, str], secret_values: dict[str, Any]
    ) -> dict[str, str]:
        """Resolve optional MetaClaw env values without overriding explicit runtime config."""
        merged: dict[str, str] = {}
        for key in METACLAW_OPTIONAL_ENV_KEYS:
            for source in (env_values, layered_values, secret_values):
                raw_value = source.get(key)
                if raw_value is None:
                    raw_value = source.get(key.lower())
                if IntegrationSetup._is_real_env_value(str(raw_value) if raw_value is not None else None):
                    merged[key] = str(raw_value).strip().strip("\"'")
                    break
        return merged

    @staticmethod
    def _upsert_env_values(path: Path, updates: dict[str, str]) -> list[str]:
        """Upsert dotenv-style values and return keys that changed."""
        if not updates:
            return []
        raw_lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        remaining = dict(updates)
        changed_keys: list[str] = []
        next_lines: list[str] = []
        for line in raw_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in line:
                next_lines.append(line)
                continue
            key, _value = line.split("=", 1)
            normalized_key = key.strip()
            if normalized_key in remaining:
                desired_line = f"{normalized_key}={remaining.pop(normalized_key)}"
                if line.strip() != desired_line:
                    next_lines.append(desired_line)
                    changed_keys.append(normalized_key)
                else:
                    next_lines.append(line)
                continue
            next_lines.append(line)
        for key, value in remaining.items():
            next_lines.append(f"{key}={value}")
            changed_keys.append(key)
        if changed_keys or not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("\n".join(next_lines).rstrip() + "\n", encoding="utf-8")
        return changed_keys

    def _resolve_metaclaw_credentials(
        self, runtime_path: Path
    ) -> tuple[dict[str, str], list[str], dict[str, str], dict[str, Any]]:
        """Resolve MetaClaw credentials from runtime env, layered env, and secrets config."""
        env_path = runtime_path / ".env"
        backup_env_path = runtime_path / ".env.backup"
        runtime_env = self._read_env_assignments(env_path) if env_path.exists() else {}
        backup_env = (
            self._read_assignment_file(backup_env_path, separators=("=", ":")) if backup_env_path.exists() else {}
        )
        layered_env = self._collect_layered_env_assignments()
        secrets_payload = self._collect_secrets_config()
        metaclaw_secrets = secrets_payload.get("metaclaw", {})
        if not isinstance(metaclaw_secrets, dict):
            metaclaw_secrets = {}

        resolved: dict[str, str] = {}
        sources: list[str] = []
        used_aliases: dict[str, str] = {}

        private_key, private_key_name = self._first_real_value(runtime_env, METACLAW_PRIVATE_KEY_ENV_KEYS)
        if private_key:
            resolved["PRIVATE_KEY"] = private_key
            sources.append("metaclaw:.env")
            if private_key_name:
                used_aliases["PRIVATE_KEY"] = private_key_name
        else:
            private_key, private_key_name = self._first_real_value(backup_env, METACLAW_PRIVATE_KEY_ENV_KEYS)
            if private_key:
                resolved["PRIVATE_KEY"] = private_key
                sources.append("metaclaw:.env.backup")
                if private_key_name:
                    used_aliases["PRIVATE_KEY"] = private_key_name
            else:
                private_key, private_key_name = self._first_real_value(layered_env, METACLAW_PRIVATE_KEY_ENV_KEYS)
                if private_key:
                    resolved["PRIVATE_KEY"] = private_key
                    sources.append("workspace:env")
                    if private_key_name:
                        used_aliases["PRIVATE_KEY"] = private_key_name
                else:
                    private_key, private_key_name = self._first_real_value(
                        metaclaw_secrets,
                        (
                            "private_key",
                            "wallet_private_key",
                            "base_private_key",
                            "eth_private_key",
                            "evm_private_key",
                        ),
                    )
                    if private_key:
                        resolved["PRIVATE_KEY"] = private_key
                        sources.append("config:secrets.json:metaclaw")
                        if private_key_name:
                            used_aliases["PRIVATE_KEY"] = private_key_name

        api_key, api_key_name = self._first_real_value(runtime_env, METACLAW_API_KEY_ENV_KEYS)
        if api_key:
            sources.append("metaclaw:.env")
            if api_key_name:
                used_aliases["CLOWNCH_API_KEY"] = api_key_name
        else:
            api_key, api_key_name = self._first_real_value(backup_env, METACLAW_API_KEY_ENV_KEYS)
            if api_key:
                sources.append("metaclaw:.env.backup")
                if api_key_name:
                    used_aliases["CLOWNCH_API_KEY"] = api_key_name
            else:
                api_key, api_key_name = self._first_real_value(layered_env, METACLAW_API_KEY_ENV_KEYS)
                if api_key:
                    sources.append("workspace:env")
                    if api_key_name:
                        used_aliases["CLOWNCH_API_KEY"] = api_key_name
                else:
                    api_key, api_key_name = self._first_real_value(
                        metaclaw_secrets,
                        (
                            "api_key",
                            "clownch_api_key",
                            "clawnch_api_key",
                            "clawncher_api_key",
                            "metaclaw_api_key",
                        ),
                    )
                    if api_key:
                        sources.append("config:secrets.json:metaclaw")
                        if api_key_name:
                            used_aliases["CLOWNCH_API_KEY"] = api_key_name
        if api_key:
            # The upstream repo inconsistently reads both spellings. Writing both avoids drift.
            resolved["CLOWNCH_API_KEY"] = api_key
            resolved["CLAWNCHER_API_KEY"] = api_key

        resolved.update(self._merge_optional_env_values(runtime_env, layered_env, metaclaw_secrets))
        return resolved, sorted(set(sources)), used_aliases, runtime_env

    def _sync_metaclaw_env(
        self, runtime_path: Path, resolved_values: dict[str, str], current_env: dict[str, str]
    ) -> list[str]:
        """Materialize a local MetaClaw .env from resolved values when possible."""
        env_updates: dict[str, str] = {}
        for key in ("PRIVATE_KEY", "CLOWNCH_API_KEY", "CLAWNCHER_API_KEY", *METACLAW_OPTIONAL_ENV_KEYS):
            value = resolved_values.get(key)
            if not self._is_real_env_value(value):
                continue
            current_value = current_env.get(key)
            if self._is_real_env_value(current_value):
                continue
            env_updates[key] = value
        if not env_updates:
            return []
        return self._upsert_env_values(runtime_path / ".env", env_updates)

    @staticmethod
    def _detect_python_311() -> str | None:
        """Return a usable Python 3.11+ interpreter.

        Prefer the current interpreter if it meets the minimum version. Otherwise
        fall back to common python3.11 executables on PATH.
        """
        try:
            return sys.executable
        except Exception:
            pass

        for candidate in ("python3.11", "python311"):
            resolved = shutil.which(candidate)
            if resolved:
                return resolved
        return None

    @staticmethod
    def _looks_like_probe_blocked_error(detail: str | None) -> bool:
        """Detect probe failures caused by the current runtime context."""
        if not detail:
            return False
        lowered = str(detail).strip().lower()
        return any(marker in lowered for marker in PROBE_BLOCKED_ERROR_MARKERS)

    @staticmethod
    def _classify_metaclaw_probe_error(exc: Exception) -> dict[str, Any]:
        """Classify MetaClaw probe failures into actionable states."""
        detail = str(exc).strip() or exc.__class__.__name__
        lowered = detail.lower()
        if isinstance(exc, requests.Timeout):
            return {"ok": False, "status": "timeout", "error": detail}
        if IntegrationSetup._looks_like_probe_blocked_error(detail):
            return {"ok": False, "status": "probe_blocked", "error": detail, "probe_blocked": True}
        if isinstance(exc, requests.ConnectionError):
            if any(
                marker in lowered
                for marker in (
                    "name or service not known",
                    "temporary failure in name resolution",
                    "nodename nor servname provided",
                    "getaddrinfo failed",
                )
            ):
                return {"ok": False, "status": "dns_error", "error": detail}
            return {"ok": False, "status": "connect_error", "error": detail}
        return {"ok": False, "status": "error", "error": detail}

    @staticmethod
    def _probe_metaclaw_status(env_values: dict[str, str], timeout_s: int = 12) -> dict[str, Any]:
        """Probe MetaClaw directly via HTTP so failures classify cleanly."""
        api_key = env_values.get("CLOWNCH_API_KEY") or env_values.get("CLAWNCHER_API_KEY")
        if not IntegrationSetup._is_real_env_value(api_key):
            return {"ok": False, "status": "skipped", "error": "missing_api_key"}

        api_base = (
            env_values.get("CLOWNCH_API_BASE_URL")
            or env_values.get("CLAWNCHER_API_BASE_URL")
            or env_values.get("METACLAW_API_BASE_URL")
            or "https://clawn.ch"
        )
        api_url = f"{str(api_base).rstrip('/')}/api/agents/me"
        headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}

        try:
            response = requests.get(api_url, headers=headers, timeout=timeout_s)
        except requests.RequestException as exc:
            failure = IntegrationSetup._classify_metaclaw_probe_error(exc)
            failure["url"] = api_url
            return failure

        response_body = response.text.strip()
        response_preview = response_body[:240] if response_body else None
        if response.status_code in (401, 403):
            return {
                "ok": False,
                "status": "auth_error",
                "http_status": response.status_code,
                "error": response_preview or f"http_{response.status_code}",
                "url": api_url,
            }
        if response.status_code >= 400:
            return {
                "ok": False,
                "status": "http_error",
                "http_status": response.status_code,
                "error": response_preview or f"http_{response.status_code}",
                "url": api_url,
            }

        try:
            payload = response.json()
        except ValueError:
            return {
                "ok": False,
                "status": "parse_error",
                "http_status": response.status_code,
                "error": response_preview or "invalid_json_response",
                "url": api_url,
            }

        return {"ok": True, "status": "ok", "http_status": response.status_code, "payload": payload, "url": api_url}

    def detect_ollama(self) -> dict[str, Any]:
        """Detect and configure Ollama integration."""
        print("🔍 Detecting Ollama...")
        existing_status = self.status.get("ollama")
        if not isinstance(existing_status, dict):
            existing_status = {}

        # Try common Ollama ports and hosts
        candidates = [
            "http://localhost:11434",
            "http://127.0.0.1:11434",
            "http://localhost:11435",  # Alternative port
        ]
        blocked_details: list[str] = []

        for url in candidates:
            try:
                response = requests.get(f"{url}/api/tags", timeout=5)
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    print(f"  ✅ Ollama found at {url}")
                    print(f"  📦 Models: {len(models)}")
                    for model in models[:5]:  # Show first 5
                        print(f"     - {model.get('name')}")

                    self.status["ollama"] = {
                        "available": True,
                        "url": url,
                        "models": [m.get("name") for m in models],
                        "model_count": len(models),
                    }
                    return self.status["ollama"]
            except Exception as e:
                detail = str(e)
                print(f"  ❌ {url}: {detail[:50]}")
                if self._looks_like_probe_blocked_error(detail):
                    blocked_details.append(detail)

        if blocked_details:
            print("  ⚠️  Ollama probe blocked by current runtime context")
            self.status["ollama"] = {
                "available": bool(existing_status.get("available")),
                "probe_blocked": True,
                "detail": blocked_details[-1],
                "check_mode": "probe_blocked_fallback",
            }
            return self.status["ollama"]

        print("  ⚠️  Ollama not detected. Install from https://ollama.ai")
        self.status["ollama"] = {"available": False}
        return self.status["ollama"]

    def detect_chatdev(self) -> dict[str, Any]:
        """Detect ChatDev installation."""
        print("\n🔍 Detecting ChatDev...")

        env_chatdev = self._coerce_path(os.getenv("CHATDEV_PATH"))
        env_nusyq_root = self._coerce_path(os.getenv("NUSYQ_ROOT_PATH"))
        # Check common ChatDev locations
        candidates = [
            env_chatdev,
            env_nusyq_root / "ChatDev" if env_nusyq_root else None,
            self.repo_root.parent.parent / "NuSyQ" / "ChatDev",
            *[path / "ChatDev" for path in self._user_repo_candidates("NuSyQ")],
            Path.home() / "NuSyQ" / "ChatDev",
        ]

        for path in candidates:
            if path is None:
                continue
            if path.exists():
                print(f"  ✅ ChatDev found at {path}")
                run_py = path / "run.py"
                has_run = run_py.exists()
                print(f"  📝 run.py: {'✅' if has_run else '❌'}")

                self.status["chatdev"] = {
                    "available": True,
                    "path": str(path),
                    "has_run_script": has_run,
                }
                return self.status["chatdev"]

        print("  ⚠️  ChatDev not found. Clone from GitHub into NuSyQ/ChatDev")
        self.status["chatdev"] = {"available": False}
        return self.status["chatdev"]

    def detect_simulatedverse(self) -> dict[str, Any]:
        """Detect SimulatedVerse installation."""
        print("\n🔍 Detecting SimulatedVerse...")

        env_simulatedverse = self._coerce_path(os.getenv("SIMULATEDVERSE_PATH"))
        candidates = [
            env_simulatedverse,
            self.repo_root.parent.parent / "SimulatedVerse" / "SimulatedVerse",
            self.repo_root.parent.parent.parent / "SimulatedVerse" / "SimulatedVerse",
            *self._user_repo_candidates("SimulatedVerse"),
        ]

        for path in candidates:
            if path is None:
                continue
            if path.exists():
                print(f"  ✅ SimulatedVerse found at {path}")
                package_json = path / "package.json"
                has_package = package_json.exists()
                print(f"  📦 package.json: {'✅' if has_package else '❌'}")

                # Probe both the legacy and current minimal-agent endpoints.
                sim_host = os.getenv("SIMULATEDVERSE_HOST", "http://127.0.0.1")
                probe_candidates = [
                    f"{sim_host}:{os.getenv('SIMULATEDVERSE_PORT', '5002')}/health",
                    f"{sim_host}:5002/api/health",
                    f"{sim_host}:5001/api/health",
                    "http://localhost:5001/api/health",
                ]
                running = False
                active_probe = None
                blocked_details: list[str] = []
                for sim_url in probe_candidates:
                    try:
                        response = requests.get(sim_url, timeout=2)
                        if response.status_code < 400:
                            running = True
                            active_probe = sim_url
                            break
                    except Exception as exc:
                        detail = str(exc)
                        if self._looks_like_probe_blocked_error(detail):
                            blocked_details.append(detail)
                        continue

                if blocked_details and not running:
                    print("  🚀 Server running: ⚠️ probe blocked in current runtime context")
                else:
                    print(f"  🚀 Server running: {'✅' if running else '❌'}")
                if active_probe:
                    print(f"  ❤️ Health endpoint: {active_probe}")

                self.status["simulatedverse"] = {
                    "available": True,
                    "path": str(path),
                    "has_package_json": has_package,
                    "server_running": running,
                    "health_url": active_probe,
                    "probe_blocked": bool(blocked_details and not running),
                    "detail": blocked_details[-1] if blocked_details and not running else None,
                    "recommended_start_command": (
                        'cmd.exe /c "cd /d C:\\Users\\keath\\Desktop\\SimulatedVerse\\SimulatedVerse && npm run dev:minimal"'
                    ),
                }
                return self.status["simulatedverse"]

        print("  ⚠️  SimulatedVerse not found")
        self.status["simulatedverse"] = {"available": False}
        return self.status["simulatedverse"]

    def detect_nusyq_root(self) -> dict[str, Any]:
        """Detect NuSyQ root repository."""
        print("\n🔍 Detecting NuSyQ Root...")

        candidates = [
            self._coerce_path(os.getenv("NUSYQ_ROOT_PATH")),
            self.repo_root.parent.parent / "NuSyQ",
            self.repo_root.parent.parent.parent / "NuSyQ",
            *self._user_repo_candidates("NuSyQ"),
            Path.home() / "NuSyQ",
        ]

        for path in candidates:
            if path is None:
                continue
            if path.exists():
                print(f"  ✅ NuSyQ Root found at {path}")
                mcp_server = path / "mcp_server" / "main.py"
                has_mcp = mcp_server.exists()
                print(f"  🔌 MCP Server: {'✅' if has_mcp else '❌'}")

                self.status["nusyq_root"] = {
                    "available": True,
                    "path": str(path),
                    "has_mcp_server": has_mcp,
                }
                return self.status["nusyq_root"]

        print("  ⚠️  NuSyQ Root not found")
        self.status["nusyq_root"] = {"available": False}
        return self.status["nusyq_root"]

    def detect_copilot(self) -> dict[str, Any]:
        """Detect GitHub Copilot CLI availability and token configuration."""
        print("\n🔍 Detecting GitHub Copilot CLI...")

        copilot_bin = shutil.which("copilot")
        env_vars = {
            "GITHUB_COPILOT_API_KEY": os.getenv("GITHUB_COPILOT_API_KEY"),
            "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN"),
            "GH_TOKEN": os.getenv("GH_TOKEN"),
            "COPILOT_GITHUB_TOKEN": os.getenv("COPILOT_GITHUB_TOKEN"),
        }
        config_token = None
        config_path = self.repo_root / "config" / "secrets.json"
        if config_path.exists():
            try:
                config = json.loads(config_path.read_text(encoding="utf-8"))
                config_token = config.get("github", {}).get("token")
            except Exception:
                config_token = None

        tokens_present = {k: bool(v) for k, v in env_vars.items()}
        any_token = any(tokens_present.values()) or bool(config_token)

        copilot_version = None
        copilot_ok = False
        if copilot_bin:
            try:
                result = subprocess.run(
                    [copilot_bin, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                copilot_version = (result.stdout or result.stderr).strip().splitlines()[0]
                copilot_ok = result.returncode == 0
            except Exception:
                copilot_ok = False

        print(f"  📦 Copilot CLI: {'✅' if copilot_bin else '❌'}")
        if copilot_bin:
            print(f"    Path: {copilot_bin}")
        if copilot_version:
            print(f"    Version: {copilot_version}")
        print(f"  🔑 Token configured: {'✅' if any_token else '❌'}")

        self.status["copilot"] = {
            "available": bool(copilot_bin),
            "path": copilot_bin,
            "version": copilot_version,
            "token_present": any_token,
            "token_sources": {**tokens_present, "config": bool(config_token)},
            "config_path": str(config_path) if config_path.exists() else None,
            "copilot_ok": copilot_ok,
        }
        return self.status["copilot"]

    def detect_hermes_agent(self) -> dict[str, Any]:
        """Detect Hermes Agent installation and local runtime readiness."""
        print("\n🔍 Detecting Hermes Agent...")

        candidates = [
            self._coerce_path(os.getenv("HERMES_AGENT_PATH")),
            self.repo_root / "state" / "runtime" / "external" / "hermes-agent",
            self.repo_root.parent / "hermes-agent",
        ]
        path = self._first_existing_path(candidates)
        if path is None:
            print("  ⚠️  Hermes Agent not found")
            self.status["hermes_agent"] = {"available": False}
            return self.status["hermes_agent"]

        python_311 = self._detect_python_311()
        hermes_venv = path / ".venv" / "bin" / "python"
        local_python = str(hermes_venv) if hermes_venv.exists() else python_311
        node_available = shutil.which("node") is not None
        npm_available = shutil.which("npm") is not None
        node_modules_ready = (path / "node_modules").exists()
        pyproject_exists = (path / "pyproject.toml").exists()
        package_exists = (path / "package.json").exists()
        runnable = bool(local_python and node_available and pyproject_exists)

        print(f"  ✅ Hermes Agent found at {path}")
        print(f"  🐍 Python 3.11+: {'✅' if local_python else '❌'}")
        print(f"  📦 Node toolchain: {'✅' if node_available and npm_available else '❌'}")
        print(f"  🌐 Browser deps: {'✅' if node_modules_ready else '❌'}")

        self.status["hermes_agent"] = {
            "available": True,
            "path": str(path),
            "has_pyproject": pyproject_exists,
            "has_package_json": package_exists,
            "python_3_11_available": bool(local_python),
            "python_command": local_python,
            "node_available": node_available,
            "npm_available": npm_available,
            "node_modules_ready": node_modules_ready,
            "runnable": runnable,
            "recommended_bootstrap": ("python3.11 -m venv .venv && .venv/bin/pip install -e . && npm install"),
        }
        return self.status["hermes_agent"]

    def detect_metaclaw(self) -> dict[str, Any]:
        """Detect MetaClaw installation and workspace-local readiness."""
        print("\n🔍 Detecting MetaClaw...")

        candidates = [
            self._coerce_path(os.getenv("METACLAW_PATH")),
            self.repo_root / "state" / "runtime" / "external" / "metaclaw-agent",
            self.repo_root.parent / "metaclaw-agent",
        ]
        path = self._first_existing_path(candidates)
        if path is None:
            print("  ⚠️  MetaClaw not found")
            self.status["metaclaw"] = {"available": False}
            return self.status["metaclaw"]

        node_available = shutil.which("node") is not None
        npm_available = shutil.which("npm") is not None
        node_modules_ready = (path / "node_modules").exists()
        env_path = path / ".env"
        resolved_values, secret_sources, alias_map, env_values = self._resolve_metaclaw_credentials(path)
        env_updates = self._sync_metaclaw_env(path, resolved_values, env_values)
        if env_updates:
            env_values = self._read_env_assignments(env_path)
        private_key_ready = self._is_real_env_value(env_values.get("PRIVATE_KEY"))
        api_key_ready = self._is_real_env_value(env_values.get("CLOWNCH_API_KEY")) or self._is_real_env_value(
            env_values.get("CLAWNCHER_API_KEY")
        )
        missing_required_env: list[str] = []
        if not private_key_ready:
            missing_required_env.append("PRIVATE_KEY")
        if not api_key_ready:
            missing_required_env.append("CLOWNCH_API_KEY or CLAWNCHER_API_KEY")
        env_ready = env_path.exists() and not missing_required_env
        registration_ready = bool(
            node_available and npm_available and node_modules_ready and private_key_ready and not api_key_ready
        )
        has_env_template = (path / ".env.example").exists()
        package_exists = (path / "package.json").exists()
        runnable = bool(node_available and npm_available and node_modules_ready and env_ready)
        status_check = self._probe_metaclaw_status(env_values) if runnable else {"ok": False, "status": "skipped"}
        externally_verified = bool(status_check.get("ok"))
        status_name = str(status_check.get("status") or "")
        registration_recommended = bool(
            status_name == "auth_error" and private_key_ready and node_available and npm_available
        )
        if registration_recommended:
            next_step = "npm run register"
        elif status_name == "auth_error":
            next_step = "Update CLOWNCH_API_KEY/CLAWNCHER_API_KEY"
        elif runnable:
            next_step = "npm run status"
        elif registration_ready:
            next_step = "npm run register"
        else:
            next_step = "Provide PRIVATE_KEY and CLOWNCH_API_KEY/CLAWNCHER_API_KEY"

        print(f"  ✅ MetaClaw found at {path}")
        print(f"  📦 Node toolchain: {'✅' if node_available and npm_available else '❌'}")
        print(f"  📚 Dependencies: {'✅' if node_modules_ready else '❌'}")
        print(f"  🔐 Environment configured: {'✅' if env_ready else '❌'}")
        print(f"  🌐 Status probe: {'✅' if externally_verified else '⚠️'}")
        if registration_ready:
            print("  📝 Registration ready: ✅ (private key present, API key still needed)")
        if env_updates:
            print(f"  🔁 Synced .env keys: {', '.join(env_updates)}")

        self.status["metaclaw"] = {
            "available": True,
            "path": str(path),
            "has_package_json": package_exists,
            "has_env_template": has_env_template,
            "env_file_present": env_path.exists(),
            "env_configured": env_ready,
            "private_key_configured": private_key_ready,
            "api_key_configured": api_key_ready,
            "registration_ready": registration_ready,
            "missing_required_env": missing_required_env,
            "api_key_aliases_checked": ["CLOWNCH_API_KEY", "CLAWNCHER_API_KEY"],
            "private_key_aliases_checked": list(METACLAW_PRIVATE_KEY_ENV_KEYS),
            "resolved_secret_sources": secret_sources,
            "resolved_secret_aliases": alias_map,
            "env_sync_applied": bool(env_updates),
            "env_sync_keys": env_updates,
            "node_available": node_available,
            "npm_available": npm_available,
            "node_modules_ready": node_modules_ready,
            "runnable": runnable,
            "registration_recommended": registration_recommended,
            "externally_verified": externally_verified,
            "status_check": status_check,
            "recommended_bootstrap": (
                "npm install && npm run register"
                if registration_ready
                else "npm install && cp .env.example .env && npm run status"
            ),
            "next_step": next_step,
            "constraints": [
                "Requires wallet/private key configuration",
                "Requires Clawncher/MetaClaw credentials for real on-chain workflows",
            ],
        }
        return self.status["metaclaw"]

    def check_extensions(self) -> dict[str, Any]:
        """Check VS Code extensions (read-only)."""
        print("\n🔍 Checking VS Code Extensions...")

        # Extensions are managed by VS Code, we can only report recommendations
        extensions_file = self.repo_root / ".vscode" / "extensions.json"
        if extensions_file.exists():
            data = self._load_jsonc(extensions_file)
            recommended = list(dict.fromkeys(data.get("recommendations", [])))
            optional = list(dict.fromkeys(data.get("optionalRecommendations", [])))
            local = list(dict.fromkeys(data.get("localRecommendations", []) or data.get("localExtensions", [])))
            print(f"  📋 Recommended: {len(recommended)} extensions")
            for ext in recommended[:5]:
                print(f"     - {ext}")
            if optional:
                print(f"  🧰 Optional: {len(optional)} extensions")
                for ext in optional[:5]:
                    print(f"     - {ext}")
            if local:
                print(f"  🏠 Local: {len(local)} extensions")
                for ext in local[:5]:
                    print(f"     - {ext}")

            optional_workflows = {
                "fuzionix.devtool-plus": [
                    "Use DevTool+ for JSON/Base64/UUID/hash transforms in receipts and bridge payloads",
                    "Pin JSON Editor, Base64 Encoder / Decoder, and UUID Generator in the focused coding profile",
                ],
                "hbenl.vscode-test-explorer": [
                    "Run focused pytest regressions from the Testing view before broad sweeps",
                ],
                "hediet.vscode-drawio": [
                    "Maintain architecture diagrams in-editor for routing and subsystem maps",
                ],
                "ms-vsliveshare.vsliveshare": [
                    "Use Live Share for paired debugging on editor-only or profile-specific issues",
                ],
            }
            active_optional_workflows = {ext: optional_workflows[ext] for ext in optional if ext in optional_workflows}

            devtool_probe: dict[str, Any] | None = None
            try:
                from src.integrations.devtool_bridge import probe_devtool

                probe_status, probe_detail, probe_meta = probe_devtool()
                devtool_probe = {
                    "status": probe_status.lower(),
                    "detail": probe_detail,
                    "metadata": probe_meta,
                }
                print(f"  🌐 DevTool+: {probe_status} - {probe_detail}")
            except Exception as exc:
                devtool_probe = {"status": "unknown", "error": str(exc)}
                print(f"  🌐 DevTool+: ⚠️ probe failed ({exc})")

            self.status["extensions"] = {
                "file_exists": True,
                "recommended_count": len(recommended),
                "recommendations": recommended,
                "optional_count": len(optional),
                "optional_recommendations": optional,
                "local_count": len(local),
                "local_recommendations": local,
                "optional_workflows": active_optional_workflows,
                "devtool_probe": devtool_probe,
            }
        else:
            print("  ❌ extensions.json not found")
            self.status["extensions"] = {"file_exists": False}

        return self.status["extensions"]

    def generate_env_config(self) -> dict[str, str]:
        """Generate environment variable configuration."""
        print("\n🔧 Generating environment configuration...")

        env_vars: dict[str, str] = {}

        if self.status["ollama"]["available"]:
            env_vars["OLLAMA_BASE_URL"] = self.status["ollama"]["url"]
            print(f"  OLLAMA_BASE_URL={self.status['ollama']['url']}")

        if self.status["chatdev"]["available"]:
            env_vars["CHATDEV_PATH"] = self.status["chatdev"]["path"]
            print(f"  CHATDEV_PATH={self.status['chatdev']['path']}")

        if self.status["simulatedverse"]["available"]:
            env_vars["SIMULATEDVERSE_PATH"] = self.status["simulatedverse"]["path"]
            print(f"  SIMULATEDVERSE_PATH={self.status['simulatedverse']['path']}")

        if self.status["nusyq_root"]["available"]:
            env_vars["NUSYQ_ROOT_PATH"] = self.status["nusyq_root"]["path"]
            print(f"  NUSYQ_ROOT_PATH={self.status['nusyq_root']['path']}")

        if self.status["hermes_agent"]["available"]:
            env_vars["HERMES_AGENT_PATH"] = self.status["hermes_agent"]["path"]
            print(f"  HERMES_AGENT_PATH={self.status['hermes_agent']['path']}")

        if self.status["metaclaw"]["available"]:
            env_vars["METACLAW_PATH"] = self.status["metaclaw"]["path"]
            print(f"  METACLAW_PATH={self.status['metaclaw']['path']}")

        self.status["environment"] = env_vars
        return env_vars

    def save_env_script(self) -> None:
        """Save PowerShell script to set environment variables."""
        env_vars = self.status.get("environment", {})
        if not env_vars:
            return

        script_path = self.repo_root / "scripts" / "set_env.ps1"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write("# Auto-generated environment configuration\n")
            f.write("# Source this script: . .\\scripts\\set_env.ps1\n\n")
            for key, value in env_vars.items():
                f.write(f'$env:{key} = "{value}"\n')
            f.write("\nWrite-Host '✅ Environment variables configured' -ForegroundColor Green\n")

        print(f"\n💾 Saved environment script: {script_path}")
        print("   To use: . .\\scripts\\set_env.ps1")

    def save_report(self) -> None:
        """Save integration status report."""
        report_path = self.repo_root / "state" / "reports" / "integration_status.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.status, f, indent=2)

        print(f"\n📊 Saved integration report: {report_path}")

    def run_full_setup(self) -> dict[str, Any]:
        """Run complete integration setup."""
        print("🚀 NuSyQ Integration Setup")
        print("=" * 60)

        self.detect_ollama()
        self.detect_chatdev()
        self.detect_simulatedverse()
        self.detect_nusyq_root()
        self.detect_copilot()
        self.detect_hermes_agent()
        self.detect_metaclaw()
        self.check_extensions()
        self.generate_env_config()

        self.save_env_script()
        self.save_report()

        print("\n" + "=" * 60)
        print("🎯 Integration Setup Complete!")

        # Summary
        integration_keys = [
            "ollama",
            "chatdev",
            "simulatedverse",
            "nusyq_root",
            "copilot",
            "hermes_agent",
            "metaclaw",
        ]

        available_count = sum(1 for key in integration_keys if self.status.get(key, {}).get("available", False))
        constrained_count = sum(1 for key in integration_keys if self.status.get(key, {}).get("probe_blocked", False))
        effective_count = sum(
            1
            for key in integration_keys
            if self.status.get(key, {}).get("available", False) or self.status.get(key, {}).get("probe_blocked", False)
        )
        if constrained_count:
            print(f"\n✅ Available/constrained systems: {effective_count}/6")
            print(f"⚠️  Probe-constrained systems: {constrained_count}")
        else:
            print(f"\n✅ Available systems: {available_count}/{len(integration_keys)}")
        print(f"🔧 Environment variables: {len(self.status['environment'])}")

        return self.status


def main() -> int:
    """Main entry point."""
    try:
        setup = IntegrationSetup()
        setup.run_full_setup()
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
