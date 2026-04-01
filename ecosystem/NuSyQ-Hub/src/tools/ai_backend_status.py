"""AI Backend Status Helper.

Checks local Ollama availability and presence of cloud API keys without printing secrets.

Outputs a concise, machine- and human-readable summary to stdout.

Contract:
- Input: none (reads environment and optional config/secrets.json)
- Output: lines of the form KEY=VALUE
  - OLLAMA_BASE_URL
  - OLLAMA_REACHABLE (true/false)
  - OLLAMA_MODELS (integer, -1 if unknown)
  - OPENAI_KEY_PRESENT (true/false)
  - ANTHROPIC_KEY_PRESENT (true/false)
- Exit code: 0 always; intended for diagnostics only
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from src.config.service_config import ServiceConfig
except ImportError:
    ServiceConfig = None

try:
    from src.utils import config_helper
except ImportError:
    config_helper = None

try:
    # Prefer urllib to avoid external deps
    from urllib.error import URLError
    from urllib.request import Request, urlopen
except (ImportError, ModuleNotFoundError):  # pragma: no cover - extremely unlikely
    urlopen = None  # type: ignore
    Request = None  # type: ignore
    URLError = Exception  # type: ignore


def _read_secrets_ollama_host(repo_root: Path) -> str | None:
    secrets_path = repo_root / "config" / "secrets.json"
    try:
        if secrets_path.exists():
            with open(secrets_path, encoding="utf-8") as f:
                data = json.load(f)
            host = data.get("ollama", {}).get("host") if isinstance(data, dict) else None
            if host and isinstance(host, str) and host.strip():
                host_str: str = host.strip()
                return host_str
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        logger.debug("Suppressed FileNotFoundError/OSError/json", exc_info=True)
    return None


def _detect_ollama_base_url(repo_root: Path) -> str:
    # Priority: ServiceConfig > config_helper > env > secrets.json > default
    if ServiceConfig:
        return ServiceConfig.get_ollama_url().rstrip("/")
    if config_helper:
        return config_helper.get_ollama_host().rstrip("/")
    env_val = os.getenv("OLLAMA_BASE_URL")
    if env_val and env_val.strip():
        return env_val.strip().rstrip("/")
    secrets_val = _read_secrets_ollama_host(repo_root)
    if secrets_val:
        return secrets_val.rstrip("/")
    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1")
    port = os.getenv("OLLAMA_PORT", "11434")
    return f"{host.rstrip('/')}:{port}"


def _ping_ollama(base_url: str, timeout: float = 3.0) -> tuple[bool, int]:
    """Return (reachable, model_count). model_count = -1 if unknown.

    We attempt a GET to `${base_url}/api/tags` which lists installed models.
    """
    try:
        if urlopen is None or Request is None:
            return False, -1
        # defensive: ensure scheme present
        if not base_url.startswith("http://") and not base_url.startswith("https://"):
            base_url = f"http://{base_url}"
        req = Request(f"{base_url}/api/tags", headers={"Accept": "application/json"})
        with urlopen(req, timeout=timeout) as resp:  # nosemgrep
            if resp.status != 200:
                return False, -1
            content = resp.read()
            try:
                payload = json.loads(content.decode("utf-8", errors="ignore"))
                # Common shape: { "models": [ {"name": "..."}, ... ] }
                models = payload.get("models")
                if isinstance(models, list):
                    return True, len(models)
                return True, -1
            except json.JSONDecodeError:
                return True, -1
    except (TimeoutError, URLError, ConnectionError, OSError):
        return False, -1


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    base_url = _detect_ollama_base_url(repo_root)

    reachable, model_count = _ping_ollama(base_url)
    openai_key_present = bool(os.getenv("OPENAI_API_KEY"))
    anthropic_key_present = bool(os.getenv("ANTHROPIC_API_KEY"))

    # Print results (machine-friendly) — intentional CLI stdout output
    print(f"OLLAMA_BASE_URL={base_url}")
    print(f"OLLAMA_REACHABLE={'true' if reachable else 'false'}")
    print(f"OLLAMA_MODELS={model_count}")
    print(f"OPENAI_KEY_PRESENT={'true' if openai_key_present else 'false'}")
    print(f"ANTHROPIC_KEY_PRESENT={'true' if anthropic_key_present else 'false'}")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        # Never raise in diagnostics; keep it resilient
        sys.exit(0)
