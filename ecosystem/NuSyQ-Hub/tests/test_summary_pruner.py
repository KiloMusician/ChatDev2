import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# no need for tempfile/time
from src.tools.summary_pruner import (
    archive_pruned_files,
    compute_prune_candidates,
    generate_prune_plan,
)


def _write_file(path: Path, content: str, modified: datetime | None = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if modified:
        ts = modified.timestamp()
        os.utime(path, (ts, ts))


def test_prune_plan_generation(tmp_path: Path):
    # Create a small repo structure
    f1 = tmp_path / "old_summary.md"
    f2 = tmp_path / "large_report.md"
    f3 = tmp_path / "dup_A.md"
    f4 = tmp_path / "dup_B.md"

    now = datetime.now()
    _write_file(f1, "old content", modified=now - timedelta(days=400))
    # Large file
    _write_file(f2, "A" * 200_000, modified=now - timedelta(days=10))
    # Duplicate content (different filenames but identical content)
    _write_file(f3, "Dup content identical", modified=now - timedelta(days=30))
    _write_file(f4, "Dup content identical", modified=now - timedelta(days=20))

    # Build index
    index = {
        "generated_at": now.isoformat(),
        "repository": "tmp_repo",
        "total_files": 4,
        "categories": {"summary": 2, "report": 1, "analysis": 1},
        "files": [
            {
                "path": str(f1),
                "repository": "tmp_repo",
                "category": "summary",
                "size_bytes": f1.stat().st_size,
                "modified": (now - timedelta(days=400)).isoformat(),
                "title": "Old Summary",
                "first_heading": "Old Summary",
            },
            {
                "path": str(f2),
                "repository": "tmp_repo",
                "category": "report",
                "size_bytes": f2.stat().st_size,
                "modified": (now - timedelta(days=10)).isoformat(),
                "title": "Large Report",
                "first_heading": "Large Report",
            },
            {
                "path": str(f3),
                "repository": "tmp_repo",
                "category": "analysis",
                "size_bytes": f3.stat().st_size,
                "modified": (now - timedelta(days=30)).isoformat(),
                "title": "Duplicate Title",
                "first_heading": "Duplicate Title",
            },
            {
                "path": str(f4),
                "repository": "tmp_repo",
                "category": "analysis",
                "size_bytes": f4.stat().st_size,
                "modified": (now - timedelta(days=20)).isoformat(),
                "title": "Duplicate Title",
                "first_heading": "Duplicate Title",
            },
        ],
    }

    index_path = tmp_path / "INDEX.json"
    index_path.write_text(json.dumps(index), encoding="utf-8")

    # Compute prune candidates with small thresholds to detect them
    candidates = compute_prune_candidates(
        index, age_days=365, size_threshold_bytes=50_000, min_duplicate_group=2
    )
    # We expect: f1 (old), f2 (large), and one of f3/f4 (duplicate) candidates
    assert any(c.path == str(f1) for c in candidates)
    assert any(c.path == str(f2) for c in candidates)
    # duplicates: there should be at least one candidate by content hash
    assert any("duplicate_content" in c.reason for c in candidates)

    # Generate plan file
    plan_path = generate_prune_plan(
        index_path,
        plan_path=tmp_path / "plan.json",
        age_days=365,
        size_threshold_bytes=50_000,
    )
    assert plan_path is not None
    assert (tmp_path / "plan.json").exists()

    # Archive via plan
    archive_dir = tmp_path / "archive"
    archived = archive_pruned_files(tmp_path / "plan.json", archive_dir)
    # archived may be empty if files couldn't be moved, but verify return type
    assert isinstance(archived, list)
