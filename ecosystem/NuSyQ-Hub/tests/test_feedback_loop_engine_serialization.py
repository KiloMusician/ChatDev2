from __future__ import annotations

import json
from datetime import datetime

from src.orchestration.feedback_loop_engine import (
    ErrorReport,
    FeedbackLoopEngine,
    FeedbackLoopState,
)


def test_persists_error_queue_with_datetime_fields(tmp_path) -> None:
    engine = FeedbackLoopEngine(loop_dir=tmp_path / "loops")
    engine.ingest_error(
        ErrorReport(
            error_id="ruff_dt",
            error_type="ruff",
            file_path="src/example.py",
            line_number=1,
            detected_at=datetime(2026, 1, 3, 9, 42, 9),
        )
    )

    raw = engine.error_queue_file.read_text(encoding="utf-8").strip()
    payload = json.loads(raw.splitlines()[0])
    assert isinstance(payload["detected_at"], str)
    assert payload["detected_at"].startswith("2026-01-03T09:42:09")


def test_persists_loop_state_with_datetime_fields(tmp_path) -> None:
    engine = FeedbackLoopEngine(loop_dir=tmp_path / "loops")
    error = ErrorReport(
        error_id="mypy_dt",
        error_type="mypy",
        file_path="src/example.py",
        line_number=2,
        detected_at=datetime(2026, 1, 3, 9, 42, 10),
    )
    loop = FeedbackLoopState(
        error_id=error.error_id,
        error_report=error,
        created_at=datetime(2026, 1, 3, 9, 42, 11),
        updated_at=datetime(2026, 1, 3, 9, 42, 12),
    )
    engine._save_loop(loop)

    raw = engine.loops_file.read_text(encoding="utf-8").strip()
    payload = json.loads(raw.splitlines()[0])
    assert isinstance(payload["created_at"], str)
    assert payload["created_at"].startswith("2026-01-03T09:42:11")
    assert isinstance(payload["updated_at"], str)
    assert payload["error_report"]["detected_at"].startswith("2026-01-03T09:42:10")
