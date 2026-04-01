#!/usr/bin/env python3
"""Small helper to print a redacted version of config/secrets.json for safe logging.

Usage: python scripts/redact_secrets.py

This script does NOT modify files; it only reads and prints a sanitized view.
"""

import json
from pathlib import Path
from typing import Any


def mask_value(v: Any) -> Any:
    if v is None:
        return None
    if not isinstance(v, str):
        return v
    s = v.strip()
    if len(s) <= 6:
        return "REDACTED"
    return f"{s[:4]}...{s[-4:]}"


def redact(secrets: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for svc, cfg in secrets.items():
        if isinstance(cfg, dict):
            out[svc] = {}
            for k, v in cfg.items():
                if any(tok in k.lower() for tok in ("api", "key", "token", "secret")):
                    out[svc][k] = mask_value(v)
                elif isinstance(v, str) and len(v.strip()) > 8:
                    out[svc][k] = mask_value(v)
                else:
                    out[svc][k] = v
        else:
            out[svc] = str(cfg)
    return out


def main() -> None:
    config_path = Path(__file__).resolve().parents[1] / "config" / "secrets.json"
    if not config_path.exists():
        print(f"No secrets.json found at {config_path}")
        return

    try:
        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to read secrets.json: {e}")
        return

    redacted = redact(data if isinstance(data, dict) else {})
    print(json.dumps(redacted, indent=2))


if __name__ == "__main__":
    main()
