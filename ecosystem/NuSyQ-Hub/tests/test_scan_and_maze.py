from src.tools import scan_guard
from src.tools.maze_solver import MazeRepoScanner


def test_scans_disabled_with_sentinel(tmp_path):
    repo = tmp_path
    sentinel = repo / ".disable_scans"
    sentinel.write_text("stop")
    disabled, reason = scan_guard.scans_disabled(repo)
    assert disabled is True
    assert "Found sentinel file" in reason


def test_ensure_scan_allowed_force(tmp_path):
    # force should bypass safety heuristics
    allowed, reason = scan_guard.ensure_scan_allowed(tmp_path, force=True, raise_on_block=False)
    assert allowed is True
    assert reason == ""


def test_maze_repo_scanner_finds_todo(tmp_path, monkeypatch):
    # Ensure the scan guard allows scanning in this unit test by monkeypatching
    monkeypatch.setattr(scan_guard, "ensure_scan_allowed", lambda *a, **k: (True, ""))

    # Create a small repo with files
    repo = tmp_path
    (repo / "src").mkdir()
    target = repo / "src" / "example.py"
    target.write_text('# TODO: fix this\nprint("hello")\n')

    scanner = MazeRepoScanner(repo)
    # Scanner uses default excludes and file size limits

    results = scanner.scan(max_depth=3)
    # Findings keys are Path objects; ensure our file is present
    found_paths = [str(p) for p in results.keys()]
    assert any("example.py" in p for p in found_paths)
    # Check that the reported todo line is present
    hits = []
    for v in results.values():
        hits.extend(v)
    assert any("TODO" in t for _, t in hits)
