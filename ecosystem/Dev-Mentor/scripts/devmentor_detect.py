import json
import os
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def detect_env():
    env = {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "workspace": str(ROOT),
        "is_replit": bool(
            os.environ.get("REPL_ID")
            or os.environ.get("REPLIT_DB_URL")
            or os.environ.get("REPLIT_CLUSTER")
        ),
        "is_codespaces": bool(
            os.environ.get("CODESPACES")
            or os.environ.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN")
        ),
        "is_vscode": bool(
            os.environ.get("VSCODE_PID") or os.environ.get("TERM_PROGRAM") == "vscode"
        ),
    }
    if env["is_codespaces"]:
        env["environment"] = "codespaces"
    elif env["is_replit"]:
        env["environment"] = "replit"
    elif env["is_vscode"]:
        env["environment"] = "vscode"
    else:
        env["environment"] = "unknown"
    return env


if __name__ == "__main__":
    print(json.dumps(detect_env(), indent=2))
