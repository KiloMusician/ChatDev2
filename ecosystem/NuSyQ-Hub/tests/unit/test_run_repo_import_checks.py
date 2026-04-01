from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

spec = spec_from_file_location(
    "run_repo_import_checks",
    Path(__file__).resolve().parents[2] / "scripts" / "run_repo_import_checks.py",
)
import_mod = module_from_spec(spec)
spec.loader.exec_module(import_mod)
run_import_checks = import_mod.run_import_checks


def test_run_import_checks_runs():
    repo_root = Path(__file__).resolve().parents[1]
    failures = run_import_checks(repo_root)
    # function should return a dict; failures may be non-empty
    assert isinstance(failures, dict)
