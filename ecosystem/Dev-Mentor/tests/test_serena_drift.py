"""Tests for agents/serena/drift.py — DriftSignal and DriftDetector."""
import time
import textwrap

import pytest

from agents.serena.drift import (
    ARCH_LAYERS,
    OMNI_TAG_RE,
    REQUIRED_YAML_FIELDS,
    DriftDetector,
    DriftSignal,
)


# ── DriftSignal ───────────────────────────────────────────────────────────────

class TestDriftSignal:
    def test_required_fields(self):
        sig = DriftSignal(
            category="DOC_DEBT",
            severity="info",
            path="agents/foo.py:10",
            message="missing docstring",
        )
        assert sig.category == "DOC_DEBT"
        assert sig.severity == "info"
        assert sig.path == "agents/foo.py:10"
        assert sig.message == "missing docstring"

    def test_auto_fix_defaults_false(self):
        sig = DriftSignal(
            category="ARCH_BOUNDARY",
            severity="warn",
            path="cli/app.py:5",
            message="forbidden import",
        )
        assert sig.auto_fix is False

    def test_auto_fix_can_be_true(self):
        sig = DriftSignal(
            category="DOC_DEBT",
            severity="info",
            path="x.py:1",
            message="no docstring",
            auto_fix=True,
        )
        assert sig.auto_fix is True

    def test_tick_is_positive_float(self):
        before = time.time()
        sig = DriftSignal(
            category="STALE_INDEX",
            severity="info",
            path="x.py",
            message="not indexed",
        )
        assert sig.tick >= before

    def test_to_dict_round_trips(self):
        sig = DriftSignal(
            category="ROLE_DRIFT",
            severity="critical",
            path="agents/personalities/foo.yaml",
            message="missing 'name' field",
        )
        d = sig.to_dict()
        assert d["category"] == "ROLE_DRIFT"
        assert d["severity"] == "critical"

    def test_str_contains_category_and_path(self):
        sig = DriftSignal(
            category="ORPHAN_CHUNK",
            severity="warn",
            path="app/old.py",
            message="source gone",
        )
        s = str(sig)
        assert "ORPHAN_CHUNK" in s
        assert "app/old.py" in s

    def test_severity_icons(self):
        for severity, icon in [
            ("info", "◦"), ("warn", "⚠"), ("critical", "✕")
        ]:
            sig = DriftSignal(
                category="X", severity=severity, path="p", message="m"
            )
            assert icon in str(sig)


# ── Constants ─────────────────────────────────────────────────────────────────

class TestConstants:
    def test_arch_layers_has_expected_keys(self):
        assert "agents" in ARCH_LAYERS
        assert "cli" in ARCH_LAYERS

    def test_required_yaml_fields_contains_essentials(self):
        for field in ("id", "name", "role", "system_prompt"):
            assert field in REQUIRED_YAML_FIELDS

    def test_omni_tag_re_matches_valid_tag(self):
        m = OMNI_TAG_RE.search("[Msg\u26db{some-uuid}]")
        assert m is not None
        assert m.group(1) == "Msg"
        assert m.group(2) == "some-uuid"

    def test_omni_tag_re_no_match_on_plain_text(self):
        assert OMNI_TAG_RE.search("no tags here") is None


# ── DriftDetector.detect_doc_debt ─────────────────────────────────────────────

class TestDetectDocDebt:
    def test_finds_undocumented_public_function(self, tmp_path):
        src = textwrap.dedent("""\
            def no_doc():
                pass
        """)
        (tmp_path / "sample.py").write_text(src, encoding="utf-8")
        det = DriftDetector(repo_root=tmp_path)
        signals = det.detect_doc_debt()
        assert any(
            s.category == "DOC_DEBT" and "no_doc" in s.message
            for s in signals
        )

    def test_ignores_private_functions(self, tmp_path):
        src = textwrap.dedent("""\
            def _private():
                pass
        """)
        (tmp_path / "sample.py").write_text(src, encoding="utf-8")
        det = DriftDetector(repo_root=tmp_path)
        signals = det.detect_doc_debt()
        assert not any("_private" in s.message for s in signals)

    def test_no_signal_for_documented_function(self, tmp_path):
        src = textwrap.dedent('''\
            def documented():
                """Has a docstring."""
                pass
        ''')
        (tmp_path / "sample.py").write_text(src, encoding="utf-8")
        det = DriftDetector(repo_root=tmp_path)
        signals = det.detect_doc_debt()
        assert not any("documented" in s.message for s in signals)

    def test_skips_syntax_errors_gracefully(self, tmp_path):
        (tmp_path / "broken.py").write_text(
            "def (\nbroken", encoding="utf-8"
        )
        det = DriftDetector(repo_root=tmp_path)
        signals = det.detect_doc_debt()
        assert isinstance(signals, list)

    def test_auto_fix_is_true(self, tmp_path):
        (tmp_path / "x.py").write_text(
            "def foo(): pass\n", encoding="utf-8"
        )
        det = DriftDetector(repo_root=tmp_path)
        signals = det.detect_doc_debt()
        assert all(s.auto_fix is True for s in signals)

    def test_scope_restricts_search(self, tmp_path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        (sub / "in_scope.py").write_text(
            "def in_scope(): pass\n", encoding="utf-8"
        )
        (tmp_path / "out_scope.py").write_text(
            "def out_scope(): pass\n", encoding="utf-8"
        )
        det = DriftDetector(repo_root=tmp_path)
        signals = det.detect_doc_debt(scope="subdir")
        names = [s.message for s in signals]
        assert any("in_scope" in n for n in names)
        assert not any("out_scope" in n for n in names)


# ── DriftDetector.detect_role_drift ──────────────────────────────────────────

class TestDetectRoleDrift:
    def _make_detector(self, tmp_path):
        personalities = tmp_path / "agents" / "personalities"
        personalities.mkdir(parents=True)
        return DriftDetector(repo_root=tmp_path), personalities

    def test_no_signals_for_complete_yaml(self, tmp_path):
        det, personalities = self._make_detector(tmp_path)
        yaml_content = "\n".join(
            f"{f}: value" for f in REQUIRED_YAML_FIELDS
        )
        (personalities / "complete.yaml").write_text(
            yaml_content, encoding="utf-8"
        )
        try:
            signals = det.detect_role_drift()
            assert not any(
                "complete.yaml" in s.path
                and s.category == "ROLE_DRIFT"
                and "missing" in s.message
                for s in signals
            )
        except ImportError:
            pytest.skip("pyyaml not installed")

    def test_missing_field_generates_signal(self, tmp_path):
        det, personalities = self._make_detector(tmp_path)
        fields = [f for f in REQUIRED_YAML_FIELDS if f != "system_prompt"]
        yaml_content = "\n".join(f"{f}: value" for f in fields)
        (personalities / "incomplete.yaml").write_text(
            yaml_content, encoding="utf-8"
        )
        try:
            signals = det.detect_role_drift()
            assert any("system_prompt" in s.message for s in signals)
        except ImportError:
            pytest.skip("pyyaml not installed")

    def test_no_personalities_dir_returns_empty(self, tmp_path):
        det = DriftDetector(repo_root=tmp_path)
        assert not det.detect_role_drift()


# ── DriftDetector: DB-dependent methods gracefully skip ──────────────────────

class TestDBDependentMethods:
    def test_orphan_chunks_returns_empty_without_db(self, tmp_path):
        det = DriftDetector(repo_root=tmp_path, db_path=None)
        assert not det.detect_orphan_chunks()

    def test_stale_index_returns_empty_without_db(self, tmp_path):
        det = DriftDetector(repo_root=tmp_path, db_path=None)
        assert not det.detect_stale_index()

    def test_protocol_drift_returns_empty_without_db(self, tmp_path):
        det = DriftDetector(repo_root=tmp_path, db_path=None)
        assert not det.detect_protocol_drift()


# ── DriftDetector.detect_all ──────────────────────────────────────────────────

class TestDetectAll:
    def test_returns_list_on_empty_dir(self, tmp_path):
        det = DriftDetector(repo_root=tmp_path)
        signals = det.detect_all()
        assert isinstance(signals, list)

    def test_combines_doc_debt(self, tmp_path):
        (tmp_path / "x.py").write_text(
            "def undocumented(): pass\n", encoding="utf-8"
        )
        det = DriftDetector(repo_root=tmp_path)
        # fast=False includes the AST-based doc-debt scan
        signals = det.detect_all(fast=False)
        assert any(s.category == "DOC_DEBT" for s in signals)
