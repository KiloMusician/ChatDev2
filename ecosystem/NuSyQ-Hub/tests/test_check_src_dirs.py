from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    root = Path(__file__).resolve().parents[1]
    module_path = root / "scripts" / "check_src_dirs.py"
    spec = importlib.util.spec_from_file_location("check_src_dirs", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load check_src_dirs module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[call-arg]
    return module


def test_scan_root_respects_allowlist(tmp_path):
    module = _load_module()
    allowed = {Path("src")}

    (tmp_path / "src").mkdir(parents=True)
    result = module.scan_root(tmp_path, allowed)

    assert "src" in result["found"]
    assert result["unexpected"] == []


def test_scan_root_flags_unexpected(tmp_path):
    module = _load_module()
    allowed = {Path("src")}

    (tmp_path / "src").mkdir(parents=True)
    (tmp_path / "backup" / "src").mkdir(parents=True)
    result = module.scan_root(tmp_path, allowed)

    unexpected = {Path(p).as_posix() for p in result["unexpected"]}

    assert "backup/src" in unexpected


def test_iter_src_skips_excluded(tmp_path):
    module = _load_module()

    # Create a src inside an excluded directory (.venv) and a valid one
    (tmp_path / ".venv" / "src").mkdir(parents=True)
    (tmp_path / "real" / "src").mkdir(parents=True)

    found = module._iter_src_dirs(tmp_path, module.EXCLUDE_PARTS)
    rels = {p.relative_to(tmp_path).as_posix() for p in found}

    assert "real/src" in rels
    assert ".venv/src" not in rels
