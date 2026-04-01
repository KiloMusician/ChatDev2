"""Tests for src/dispatch/context_detector.py.

Covers ContextDetector._resolve_root, detect, _detect_mode, enrich_context.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from src.dispatch.context_detector import ContextDetector, ContextMode


# ── TestResolveRoot ───────────────────────────────────────────────────────────


class TestResolveRoot:
    """Tests for _resolve_root static method."""

    def test_env_var_dir_found(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        (tmp_path / "CLAUDE.md").touch()
        monkeypatch.setenv("NUSYQ_HUB_ROOT", str(tmp_path))
        result = ContextDetector._resolve_root("NUSYQ_HUB_ROOT", {"CLAUDE.md"})
        assert result == tmp_path.resolve()

    def test_env_var_not_a_dir_falls_through(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("NUSYQ_HUB_ROOT", "/nonexistent_xyz/path")
        with patch.dict("sys.modules", {"src.utils.repo_path_resolver": None}):
            result = ContextDetector._resolve_root("NUSYQ_HUB_ROOT", {"___no_marker___"})
        assert result is None or isinstance(result, Path)

    def test_import_error_in_resolver_falls_through(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("NUSYQ_HUB_ROOT", raising=False)
        with patch.dict("sys.modules", {"src.utils.repo_path_resolver": None}):
            result = ContextDetector._resolve_root("NUSYQ_HUB_ROOT", {"___no_marker___"})
        assert result is None or isinstance(result, Path)

    def test_marker_scan_finds_parent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        marker = "test_marker_sentinel_xyz.json"
        (tmp_path / marker).touch()
        sub = tmp_path / "sub" / "deep"
        sub.mkdir(parents=True)
        monkeypatch.delenv("NUSYQ_HUB_ROOT", raising=False)
        monkeypatch.chdir(sub)
        with patch.dict("sys.modules", {"src.utils.repo_path_resolver": None}):
            result = ContextDetector._resolve_root("NUSYQ_HUB_ROOT", {marker})
        assert result == tmp_path.resolve()

    def test_no_marker_found_returns_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("NUSYQ_HUB_ROOT", raising=False)
        monkeypatch.chdir(tmp_path)
        with patch.dict("sys.modules", {"src.utils.repo_path_resolver": None}):
            result = ContextDetector._resolve_root("NUSYQ_HUB_ROOT", {"___no_marker___"})
        assert result is None


# ── TestDetect ────────────────────────────────────────────────────────────────


class TestDetect:
    """Tests for detect() including agent_awareness emit side-effect."""

    def test_detect_returns_context_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("NUSYQ_CONTEXT_MODE", "project")
        detector = ContextDetector()
        result = detector.detect()
        assert isinstance(result, ContextMode)

    def test_detect_emits_agent_awareness(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("NUSYQ_CONTEXT_MODE", "project")
        emitted: list = []

        class _FakeMod:
            @staticmethod
            def emit(category: str, msg: str, **kw: object) -> None:
                emitted.append((category, msg))

        with patch.dict("sys.modules", {"src.system.agent_awareness": _FakeMod}):
            detector = ContextDetector()
            detector.detect()
        assert any("ContextDetector" in str(m) for _, m in emitted)

    def test_detect_emit_exception_is_swallowed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("NUSYQ_CONTEXT_MODE", "project")

        class _BrokenMod:
            @staticmethod
            def emit(*a: object, **kw: object) -> None:
                raise RuntimeError("emit failed")

        with patch.dict("sys.modules", {"src.system.agent_awareness": _BrokenMod}):
            detector = ContextDetector()
            result = detector.detect()  # must not raise
        assert isinstance(result, ContextMode)


# ── TestDetectMode ────────────────────────────────────────────────────────────


class TestDetectMode:
    """Tests for _detect_mode logic."""

    def test_ecosystem_mode_when_cwd_under_hub_root(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("NUSYQ_CONTEXT_MODE", raising=False)
        sub = tmp_path / "src" / "tools"
        sub.mkdir(parents=True)
        detector = ContextDetector()
        detector._hub_root = tmp_path.resolve()
        mode = detector._detect_mode(cwd=sub)
        assert mode == ContextMode.ECOSYSTEM

    def test_game_mode_when_cwd_under_simverse_root(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("NUSYQ_CONTEXT_MODE", raising=False)
        game_root = tmp_path / "game"
        game_root.mkdir()
        cwd = game_root / "scenes"
        cwd.mkdir()
        detector = ContextDetector()
        detector._hub_root = None
        detector._simverse_root = game_root.resolve()
        mode = detector._detect_mode(cwd=cwd)
        assert mode == ContextMode.GAME

    def test_project_mode_fallback(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("NUSYQ_CONTEXT_MODE", raising=False)
        hub = tmp_path / "hub"
        hub.mkdir()
        sv = tmp_path / "simverse"
        sv.mkdir()
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        detector = ContextDetector()
        detector._hub_root = hub.resolve()
        detector._simverse_root = sv.resolve()
        mode = detector._detect_mode(cwd=elsewhere)
        assert mode == ContextMode.PROJECT

    def test_hub_root_none_skips_ecosystem_check(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("NUSYQ_CONTEXT_MODE", raising=False)
        detector = ContextDetector()
        detector._hub_root = None
        detector._simverse_root = None
        mode = detector._detect_mode(cwd=tmp_path)
        assert mode == ContextMode.PROJECT

    def test_value_error_when_cwd_not_under_hub_falls_through(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("NUSYQ_CONTEXT_MODE", raising=False)
        hub = tmp_path / "hub"
        hub.mkdir()
        sv = tmp_path / "sv"
        sv.mkdir()
        other = tmp_path / "other"
        other.mkdir()
        detector = ContextDetector()
        detector._hub_root = hub.resolve()
        detector._simverse_root = sv.resolve()
        # other is not under hub or sv → ValueError in relative_to → PROJECT
        mode = detector._detect_mode(cwd=other)
        assert mode == ContextMode.PROJECT


# ── TestEnrichContext ─────────────────────────────────────────────────────────


class TestEnrichContext:
    """Tests for enrich_context()."""

    def test_ecosystem_mode_adds_hub_root(self, tmp_path: Path) -> None:
        detector = ContextDetector()
        detector._hub_root = tmp_path
        ctx = detector.enrich_context(ContextMode.ECOSYSTEM)
        assert ctx["context_mode"] == "ecosystem"
        assert "hub_root" in ctx
        assert "scope_hint" in ctx
        assert "relevant_configs" in ctx

    def test_ecosystem_mode_without_hub_root(self) -> None:
        detector = ContextDetector()
        detector._hub_root = None
        ctx = detector.enrich_context(ContextMode.ECOSYSTEM)
        assert "hub_root" not in ctx
        assert ctx["context_mode"] == "ecosystem"

    def test_game_mode_adds_simverse_root(self, tmp_path: Path) -> None:
        sv_root = tmp_path / "sv"
        sv_root.mkdir()
        detector = ContextDetector()
        detector._simverse_root = sv_root
        ctx = detector.enrich_context(ContextMode.GAME)
        assert ctx["context_mode"] == "game"
        assert "simverse_root" in ctx
        assert "relevant_configs" in ctx

    def test_game_mode_without_simverse_root(self) -> None:
        detector = ContextDetector()
        detector._simverse_root = None
        ctx = detector.enrich_context(ContextMode.GAME)
        assert "simverse_root" not in ctx
        assert ctx["scope_hint"] == "SimulatedVerse game and cultivation system"

    def test_project_mode_adds_cwd(self) -> None:
        detector = ContextDetector()
        ctx = detector.enrich_context(ContextMode.PROJECT)
        assert ctx["context_mode"] == "project"
        assert "project_root" in ctx
        assert "scope_hint" in ctx

    def test_base_context_is_preserved(self, tmp_path: Path) -> None:
        detector = ContextDetector()
        detector._hub_root = tmp_path
        ctx = detector.enrich_context(ContextMode.ECOSYSTEM, base_context={"my_key": "my_val"})
        assert ctx["my_key"] == "my_val"
        assert ctx["context_mode"] == "ecosystem"

    def test_base_context_not_mutated(self, tmp_path: Path) -> None:
        detector = ContextDetector()
        detector._hub_root = tmp_path
        original = {"x": 1}
        detector.enrich_context(ContextMode.ECOSYSTEM, base_context=original)
        assert original == {"x": 1}
