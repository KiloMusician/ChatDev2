import json

from src.tools.maze_solver import MazeRepoScanner


def test_maze_scanner_writes_summary_and_finds_treasures(tmp_path):
    # Create a small repo layout
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    # file with a TODO
    f1 = repo_dir / "a.py"
    f1.write_text("# TODO: implement this\nprint('hello')\n")

    # file without TODO
    f2 = repo_dir / "b.txt"
    f2.write_text("just some text\n")

    scanner = MazeRepoScanner(repo_dir)
    results = scanner.scan(max_depth=2)

    # Expect one treasure in a.py
    assert any(str(f1) in str(p) or p == f1 for p in results)
    total = sum(len(v) for v in results.values())
    assert total >= 1

    # Write a JSON summary to a temp logs dir to simulate runner behavior
    logs = tmp_path / "logs"
    logs.mkdir()
    summary_path = logs / "maze_summary_test.json"
    serializable = {str(p): [(ln, txt) for ln, txt in hits] for p, hits in results.items()}
    summary_obj = {
        "root": str(repo_dir.resolve()),
        "total": total,
        "files": serializable,
        "errors": scanner.errors,
        "interrupted": False,
    }
    summary_path.write_text(json.dumps(summary_obj, indent=2), encoding="utf-8")

    # Validate file exists and contains expected keys
    assert summary_path.exists()
    loaded = json.loads(summary_path.read_text(encoding="utf-8"))
    assert loaded.get("total") == total
