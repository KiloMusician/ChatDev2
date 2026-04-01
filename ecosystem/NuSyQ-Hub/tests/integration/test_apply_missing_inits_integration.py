from pathlib import Path

from scripts.apply_missing_inits import find_dirs_missing_init


def test_find_dirs_missing_init_and_write_report(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    roots = [repo_root / "src", repo_root / "projects"]
    missing = find_dirs_missing_init(roots, excludes=[".venv", ".git", "node_modules", "reports"])  # type: ignore

    out_dir = repo_root / "reports"
    out_dir.mkdir(exist_ok=True)
    jsonp = out_dir / "missing_init_dirs.json"
    mdp = out_dir / "missing_init_report.md"

    jsonp.write_text("\n".join(str(p) for p in missing), encoding="utf-8")
    mdp.write_text(
        "# Missing __init__.py Report\n\n" + "\n".join(f"- {p}" for p in missing), encoding="utf-8"
    )

    # At minimum, ensure function runs (no exception). Missing may be empty.
    assert jsonp.exists()
    assert mdp.exists()
