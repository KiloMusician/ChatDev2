"""Tests for the ``repo_scan`` ChatDev command."""

import sys
from pathlib import Path

from src.tools.repo_scan import repo_scan

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def create_structure(base: Path) -> None:
    """Create a small directory tree for testing."""
    (base / "pkg").mkdir()
    (base / "pkg" / "module.py").write_text("print('hi')\n")
    # large file
    (base / "pkg" / "big.bin").write_bytes(b"0" * 2048)
    # file without extension
    (base / "weird").write_text("data")


def test_repo_scan_detects_anomalies(tmp_path: Path) -> None:
    create_structure(tmp_path)
    result = repo_scan(path=str(tmp_path), max_file_size=1024)

    assert result["total_dirs"] == 1
    assert result["files_by_extension"][".py"] == 1
    # Normalize path separators for cross-platform compatibility
    assert any("big.bin" in f for f in result["anomalies"]["large_files"])
    assert "pkg" in result["anomalies"]["missing_init"]
    assert "weird" in result["anomalies"]["suspicious_files"]


def test_repo_scan_respects_depth(tmp_path: Path) -> None:
    create_structure(tmp_path)
    nested = tmp_path / "pkg" / "sub"
    nested.mkdir()
    (nested / "deep.py").write_text("x=1\n")

    result = repo_scan(path=str(tmp_path), depth=0, max_file_size=1024)
    assert "pkg" not in result["anomalies"]["missing_init"]
    assert "pkg/big.bin" not in result["anomalies"]["large_files"]
