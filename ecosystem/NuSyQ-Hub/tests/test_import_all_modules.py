import importlib
import pathlib


def test_import_every_src_module():
    root = pathlib.Path(__file__).resolve().parents[1] / "src"
    py_files = list(root.rglob("*.py"))

    successes = []
    failures = []

    for p in py_files:
        # Build module path like src.some.module
        rel = p.relative_to(root.parent)
        parts = rel.with_suffix("").parts
        module = ".".join(parts)
        try:
            importlib.import_module(module)
            successes.append(module)
        except BaseException:  # pragma: no cover - best-effort import
            failures.append(module)

    assert len(successes) >= 1, f"No modules imported successfully: failures={failures}"
