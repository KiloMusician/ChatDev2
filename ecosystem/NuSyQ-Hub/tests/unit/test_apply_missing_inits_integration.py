from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

spec = spec_from_file_location(
    "apply_missing_inits",
    Path(__file__).resolve().parents[2] / "scripts" / "apply_missing_inits.py",
)
apply_mod = module_from_spec(spec)
spec.loader.exec_module(apply_mod)
find_dirs_missing_init = apply_mod.find_dirs_missing_init


def test_find_dirs_missing_init_runs():
    repo_root = Path(__file__).resolve().parents[1]
    roots = [repo_root / "src"]
    missing = find_dirs_missing_init(roots, excludes=[".venv", ".git", "node_modules", "reports"])  # type: ignore
    assert isinstance(missing, list)
