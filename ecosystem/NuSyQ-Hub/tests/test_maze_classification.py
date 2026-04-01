import json

from src.tools.maze_solver import main as maze_main


def test_classification_aggregation_and_docs_downgrade(tmp_path, monkeypatch):
    # Arrange: create a small repo structure
    code = tmp_path / "pkg"
    docs = tmp_path / "docs"
    code.mkdir()
    docs.mkdir()

    # Code file with explicit tokens
    (code / "code.py").write_text(
        """
# TODO: implement feature
# FIXME: address edge case
# BUG: critical crash path
""".strip(),
        encoding="utf-8",
    )

    # Docs with non-matching 'BugHerd' and a real BUG marker
    (docs / "readme.md").write_text(
        """
This integrates BugHerd for feedback.
Known BUG - tracked for awareness only.
TODO: Update screenshots.
""".strip(),
        encoding="utf-8",
    )

    # Act: run scanner CLI with classification enabled in the temp repo
    monkeypatch.chdir(tmp_path)
    rc = maze_main([".", "--max-depth", "4", "--classify", "--force"])
    assert rc == 0

    # Find the latest summary file in logs/
    log_dir = tmp_path / "logs"
    summaries = sorted(log_dir.glob("maze_summary_*.json"))
    assert summaries, "No summary JSON produced"
    summary_path = summaries[-1]
    data = json.loads(summary_path.read_text(encoding="utf-8"))

    # Assert: classification flags and structures present
    assert data.get("classified") is True
    items = data.get("items", [])
    assert isinstance(items, list) and items, "Expected classified items"

    counts_by_pattern = data.get("counts_by_pattern", {})
    counts_by_severity = data.get("counts_by_severity", {})
    hotspots_by_dir = data.get("hotspots_by_dir", {})

    # Pattern counts: we added 1 TODO in code and 1 TODO in docs, 1 FIXME, 2 BUG (1 code, 1 docs)
    assert counts_by_pattern.get("TODO", 0) >= 2
    assert counts_by_pattern.get("FIXME", 0) >= 1
    assert counts_by_pattern.get("BUG", 0) >= 2

    # Severity counts: code BUG remains critical; docs BUG should be downgraded to low
    assert counts_by_severity.get("critical", 0) >= 1
    assert counts_by_severity.get("low", 0) >= 1

    # Hotspot for docs directory should be present
    assert any("/docs" in k.replace("\\", "/") for k in hotspots_by_dir.keys())

    # Items sanity: required fields present
    for it in items:
        assert {"path", "line_no", "pattern", "category", "severity", "line"} <= set(it.keys())
