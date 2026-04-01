"""Knowledge & Reuse helpers (Phase 6).

- Ingest run manifests into a lightweight knowledge index (JSONL)
- Pattern catalog loader and Three-Before-New checker
- Lessons-learned ledger appender
"""

from __future__ import annotations

import json
from pathlib import Path

from src.config.feature_flag_manager import is_feature_enabled

ARTIFACT_ROOT = Path("state") / "artifacts"
KNOWLEDGE_INDEX = Path("state") / "reports" / "knowledge_index.jsonl"
PATTERN_CATALOG = Path("config") / "pattern_catalog.jsonl"
LESSONS_LOG = Path("state") / "reports" / "lessons_learned.jsonl"


def ingest_artifacts() -> int:
    if not is_feature_enabled("knowledge_reuse_enabled"):
        return 0
    entries: list[str] = []
    for manifest_path in ARTIFACT_ROOT.glob("*/run_manifest.json"):
        try:
            data = json.loads(manifest_path.read_text())
            entry = {
                "run_id": manifest_path.parent.name,
                "task": data.get("task"),
                "models": data.get("models") or {"model": data.get("model")},
                "use_ollama": data.get("use_ollama"),
                "plan_steps": len(data.get("plan_bundle", {}).get("high_level", [])),
            }
            entries.append(json.dumps(entry))
        except Exception:
            continue
    if not entries:
        return 0
    KNOWLEDGE_INDEX.parent.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_INDEX.write_text("\n".join(entries) + "\n")
    return len(entries)


def load_patterns() -> list[dict]:
    if not PATTERN_CATALOG.exists():
        return []
    return [json.loads(line) for line in PATTERN_CATALOG.read_text().splitlines() if line.strip()]


def three_before_new(capability: str) -> list[str]:
    """Return up to three pattern ids/descriptions that match capability substring."""
    if not is_feature_enabled("knowledge_reuse_enabled"):
        return []
    patterns = load_patterns()
    matches = [p for p in patterns if capability.lower() in json.dumps(p).lower()]
    return [f"{p.get('id')}: {p.get('description')}" for p in matches[:3]]


def append_lesson(lesson: dict) -> None:
    if not is_feature_enabled("knowledge_reuse_enabled"):
        return
    LESSONS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with LESSONS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(lesson) + "\n")
