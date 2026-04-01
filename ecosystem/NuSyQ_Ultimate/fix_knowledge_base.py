#!/usr/bin/env python3
"""Recover knowledge-base.yaml to a minimal valid YAML document."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import shutil

import yaml


ROOT = Path(__file__).resolve().parent
KB_PATH = ROOT / "knowledge-base.yaml"
BACKUP_DIR = ROOT / "state" / "receipts" / "knowledge_base_repairs"


def build_recovered_document() -> dict:
    now = datetime.now(timezone.utc)
    return {
        "meta": {
            "name": "NuSyQ Knowledge Base",
            "version": "1.4.0",
            "last_updated": now.date().isoformat(),
            "format": "YAML",
            "repaired_at": now.isoformat().replace("+00:00", "Z"),
            "repair_reason": (
                "Recovered from invalid YAML and appended markdown so runtime "
                "config loaders can start reliably."
            ),
        },
        "sessions": [],
        "completions": [],
    }


def main() -> int:
    if not KB_PATH.exists():
        raise FileNotFoundError(f"Missing knowledge base: {KB_PATH}")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = BACKUP_DIR / f"knowledge-base.corrupt.{timestamp}.yaml"
    shutil.copy2(KB_PATH, backup_path)

    recovered = build_recovered_document()
    with KB_PATH.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(
            recovered,
            handle,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    with KB_PATH.open("r", encoding="utf-8") as handle:
        yaml.safe_load(handle)

    print(f"Backup written: {backup_path}")
    print(f"Recovered knowledge base: {KB_PATH}")
    print("YAML validation: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
