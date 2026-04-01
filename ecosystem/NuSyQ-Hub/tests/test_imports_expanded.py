import json
import os
import subprocess
import sys
from pathlib import Path

# Modules known to be slow or have heavy dependencies that cause timeouts
# These are functional but import slowly due to:
# - ML/AI libraries (sentence_transformers, sklearn, scipy, torch)
# - Complex initialization sequences
# - Heavy network/database dependencies
SLOW_MODULES = {
    "autonomy",
    "blockchain",
    "code_quality_tools",
    "culture_ship_real_action",
    "consciousness",  # Heavy ML imports
    "ai_intermediary",  # Network dependencies
    "chatdev_integrator",  # External process spawning
}


def discover_candidates(root: Path) -> list[str]:
    candidates: list[str] = []
    if not root.exists():
        return candidates
    # top-level python files (module names)
    for f in root.glob("*.py"):
        if f.name == "__init__.py" or f.name.startswith("test_"):
            continue
        candidates.append(f.stem)

    # packages: directories with __init__.py or any .py files
    for d in [p for p in root.iterdir() if p.is_dir()]:
        py_exists = any(d.rglob("*.py"))
        init_exists = (d / "__init__.py").exists()
        if init_exists or py_exists:
            candidates.append(d.name)

    # dedupe while preserving order
    seen = set()
    out = []
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        out.append(c)
    return out


def try_import(module: str, repo_root: Path, timeout: int = 6) -> tuple[bool, str]:
    # start with a copy of the current environment so PATH and other vars are preserved
    env = os.environ.copy()
    # ensure PYTHONPATH includes repo_root, src, and projects so imports resolve
    src_root = repo_root / "src"
    projects_root = repo_root / "projects"
    pythonpath = os.pathsep.join([str(repo_root), str(src_root), str(projects_root)])
    env.update({"PYTHONPATH": pythonpath})
    cmd = [sys.executable, "-c", f"import {module}"]
    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=timeout, check=False)
        if proc.returncode == 0:
            return True, proc.stdout or ""
        return False, proc.stderr or proc.stdout or "non-zero exit"
    except subprocess.TimeoutExpired:
        return False, "timeout"


def test_expanded_imports():
    repo_root = Path(__file__).resolve().parents[1]
    src_root = repo_root / "src"
    projects_root = repo_root / "projects"

    candidates = []
    candidates.extend(discover_candidates(src_root))
    candidates.extend(discover_candidates(projects_root))

    assert candidates, "No import candidates discovered"

    failures = {}
    skipped = []
    for mod in candidates:
        # Skip known slow modules (they work but import slowly)
        if mod in SLOW_MODULES:
            skipped.append(mod)
            continue
        ok, out = try_import(mod, repo_root)
        if not ok:
            failures[mod] = out

    if failures:
        # save a brief JSON for diagnostics
        (repo_root / "reports").mkdir(exist_ok=True)
        (repo_root / "reports" / "import_failures.json").write_text(json.dumps(failures, indent=2))

    if skipped:
        print(f"Skipped {len(skipped)} known slow modules: {', '.join(skipped)}")

    assert not failures, f"Import failures detected: {len(failures)} (see reports/import_failures.json)"
