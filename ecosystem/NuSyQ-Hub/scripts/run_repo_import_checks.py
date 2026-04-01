"""Programmatic import checker that imports candidate modules in-process.

This is a less strict but immediate check when subprocess-based tests can't be run.
"""

import logging
from importlib import import_module
from pathlib import Path

# Best-effort initialize terminal logging so results of import checks are visible
try:
    from src.system.init_terminal import init_terminal_logging

    try:
        init_terminal_logging(channel="ImportCheck", level=logging.INFO)
    except Exception:
        pass
except Exception:
    pass


def discover_candidates(root: Path) -> list[str]:
    candidates: list[str] = []
    if not root.exists():
        return candidates
    for f in root.glob("*.py"):
        if f.name == "__init__.py" or f.name.startswith("test_"):
            continue
        candidates.append(f.stem)
    for d in [p for p in root.iterdir() if p.is_dir()]:
        py_exists = any(d.rglob("*.py"))
        init_exists = (d / "__init__.py").exists()
        if init_exists or py_exists:
            candidates.append(d.name)
    seen = set()
    out = []
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        out.append(c)
    return out


def run_import_checks(repo_root: Path, exclude_prefixes: list[str] | None = None) -> dict[str, str]:
    """Run import checks but skip modules with heavy optional deps by prefix."""
    failures: dict[str, str] = {}
    src_root = repo_root / "src"
    projects_root = repo_root / "projects"

    exclude_prefixes = exclude_prefixes or [
        "consciousness",
        "ml",
        "analysis",
        "simulatedverse",
        "NuSyQ",
        "Transcendent_Spine",
        "main",
    ]

    candidates = discover_candidates(src_root) + discover_candidates(projects_root)
    for mod in candidates:
        if any(mod.startswith(prefix) for prefix in exclude_prefixes):
            failures[mod] = "skipped_heavy_imports"
            continue
        try:
            import_module(mod)
        except Exception as e:
            failures[mod] = repr(e)
    return failures


if __name__ == "__main__":
    import json
    import sys

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    failures = run_import_checks(root.resolve())
    (root / "reports").mkdir(exist_ok=True)
    (root / "reports" / "import_failures_programmatic.json").write_text(
        json.dumps(failures, indent=2), encoding="utf-8"
    )
    print(f"Checked imports; failures: {len(failures)}")
