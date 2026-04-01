"""Sync state/registry.json into the model_registry table (postgres-core).

Usage:
  python scripts/postgres/sync_registry.py --registry state/registry.json

Env (defaults):
  PG_HOST=127.0.0.1
  PG_PORT=5433
  PG_DB=nusyq_core
  PG_USER=nusyq
  PG_PASS=nusyq
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

try:
    import psycopg2
    from psycopg2.extras import Json
except Exception as exc:  # pragma: no cover - optional dependency
    raise SystemExit(f"psycopg2 required: {exc}") from exc


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)


def connect():
    return psycopg2.connect(
        host=_env("PG_HOST", "127.0.0.1"),
        port=int(_env("PG_PORT", "5433")),
        dbname=_env("PG_DB", "nusyq_core"),
        user=_env("PG_USER", "nusyq"),
        password=_env("PG_PASS", "nusyq"),
        connect_timeout=5,
    )


def load_registry(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        # normalize dict to list of values
        return list(data.values())
    if not isinstance(data, list):
        raise ValueError("registry must be a list or dict")
    return data


def sync(registry_path: Path, truncate: bool = False) -> dict[str, Any]:
    rows = load_registry(registry_path)
    conn = connect()
    inserted = 0
    try:
        with conn, conn.cursor() as cur:
            if truncate:
                cur.execute("TRUNCATE TABLE model_registry")
            for item in rows:
                name = item.get("name") or item.get("model") or "unknown"
                provider = item.get("provider") or item.get("source")
                version = item.get("version") or item.get("format")
                location = item.get("path") or item.get("dest") or item.get("location")
                size_bytes = item.get("size_bytes") or 0
                size_mb = float(size_bytes) / 1_000_000 if size_bytes else None
                cur.execute(
                    """
                    INSERT INTO model_registry (name, provider, version, location, size_mb, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (name, provider, version, location, size_mb, Json(item)),
                )
                inserted += 1
    finally:
        conn.close()
    return {"inserted": inserted}


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync registry.json into model_registry table.")
    parser.add_argument("--registry", type=Path, default=Path("state/registry.json"))
    parser.add_argument("--truncate", action="store_true", help="Truncate table before insert")
    args = parser.parse_args()

    if not args.registry.exists():
        raise SystemExit(f"Missing registry file: {args.registry}")

    summary = sync(args.registry, truncate=args.truncate)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
