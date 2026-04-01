"""Simple environment validator for NuSyQ-Hub.
Run this from the repo root (python -m scripts.check_env or python scripts/check_env.py)
Exits with code 0 when all required env vars are present, non-zero otherwise.
"""

import json
import os
import sys
from pathlib import Path

REQUIRED = [
    "GITHUB_COPILOT_API_KEY",
    "CHATDEV_PATH",
    "OLLAMA_BASE_URL",
    "MCP_SERVER_URL",
]

missing = [k for k in REQUIRED if not os.environ.get(k)]

print("NuSyQ-Hub environment validation")
print("===============================\n")
for k in REQUIRED:
    val = os.environ.get(k)
    status = "SET" if val else "MISSING"
    print(f"{k}: {status}")

# Validate required paths when provided
chatdev_path = os.environ.get("CHATDEV_PATH")
if chatdev_path and not Path(chatdev_path).exists():
    print(f"\nCHATDEV_PATH points to missing path: {chatdev_path}")
    if "CHATDEV_PATH" not in missing:
        missing.append("CHATDEV_PATH")

repo_root = Path(__file__).parent.parent


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _resolve_simulatedverse_default() -> Path:
    # Prefer config/service_config.json if present
    service_config = _read_json(repo_root / "config" / "service_config.json")
    if service_config:
        sim_path = service_config.get("paths", {}).get("simulatedverse") if isinstance(service_config, dict) else None
        if sim_path:
            return Path(sim_path)

    # Best-effort parse of config/workspace_mapping.yaml
    mapping_path = repo_root / "config" / "workspace_mapping.yaml"
    if mapping_path.exists():
        try:
            lines = mapping_path.read_text(encoding="utf-8").splitlines()
            for idx, line in enumerate(lines):
                if "SimulatedVerse" in line:
                    for back in range(1, 4):
                        if idx - back < 0:
                            break
                        prev = lines[idx - back].strip()
                        if prev.startswith("path:"):
                            return Path(prev.split(":", 1)[1].strip())
        except Exception:
            pass

    # Fallbacks
    desktop_path = Path.home() / "Desktop" / "SimulatedVerse" / "SimulatedVerse"
    if desktop_path.exists():
        return desktop_path

    sibling_path = repo_root.parent.parent / "SimulatedVerse" / "SimulatedVerse"
    return sibling_path


optional_path_vars = {
    "NUSYQ_HUB_PATH": repo_root,
    "NUSYQ_ROOT_PATH": Path.home() / "NuSyQ",
    "SIMULATEDVERSE_PATH": _resolve_simulatedverse_default(),
}
print("\nOptional repo paths")
print("-------------------")
for key, default in optional_path_vars.items():
    val = os.environ.get(key)
    effective = Path(val) if val else default
    status = "SET" if val else "DEFAULT"
    exists = "OK" if effective.exists() else "MISSING"
    print(f"{key}: {status} ({effective}) [{exists}]")

if missing:
    # Try loading from a local .env file (non-invasive) before exiting
    env_path = Path(".env")
    if env_path.exists():
        print("\nFound .env file in repo root; attempting to load values for missing keys...")
        try:
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k in missing and v:
                        os.environ[k] = v
                        print(f"Loaded {k} from .env")
        except Exception as e:
            print(f"Failed to load .env: {e}")

    # Re-evaluate missing after .env load attempt
    missing = [k for k in REQUIRED if not os.environ.get(k)]

    if missing:
        print("\nMissing required variables:\n - " + "\n - ".join(missing))
        print("\nQuick PowerShell (temporary) example:")
        print("$env:GITHUB_COPILOT_API_KEY = 'your-token-here'")
        print("$env:CHATDEV_PATH = 'C:\\Users\\<you>\\NuSyQ\\ChatDev'")
        print("$env:OLLAMA_BASE_URL = 'http://127.0.0.1:11434'  # or custom host")
        print("$env:MCP_SERVER_URL = 'http://127.0.0.1:8081'  # or custom host")
        print("$env:NUSYQ_ROOT_PATH = 'C:\\Users\\<you>\\NuSyQ'")
        print("$env:SIMULATEDVERSE_PATH = 'C:\\Users\\<you>\\Desktop\\SimulatedVerse\\SimulatedVerse'")
        sys.exit(2)
    else:
        print("\nAll required environment variables are present (from environment or .env).")
        sys.exit(0)
