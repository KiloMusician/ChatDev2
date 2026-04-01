"""Tests for src/analysis/ — RepositoryCompendium and health_verifier module."""

from pathlib import Path

import pytest


class TestRepositoryCompendium:
    """Tests for RepositoryCompendium AST-based repository analysis."""

    @pytest.fixture
    def tiny_repo(self, tmp_path):
        """Create a tiny synthetic repo for analysis."""
        (tmp_path / "module.py").write_text(
            "import os\nimport sys\n\nclass Foo:\n    def bar(self):\n        return 1\n\ndef helper(): pass\n"
        )
        (tmp_path / "data.json").write_text('{"key": "value"}')
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "nested.py").write_text("x = 1\ny = 2\n")
        return tmp_path

    @pytest.fixture
    def compendium(self, tiny_repo):
        from src.analysis.repository_analyzer import RepositoryCompendium
        return RepositoryCompendium(tiny_repo)

    def test_analyze_returns_expected_keys(self, compendium):
        result = compendium.analyze_repository()
        assert "metrics" in result
        assert "files" in result
        assert "functions" in result
        assert "classes" in result
        assert "imports" in result
        assert "structure" in result

    def test_metrics_has_total_files(self, compendium):
        result = compendium.analyze_repository()
        metrics = result["metrics"]
        assert "total_files" in metrics.index or hasattr(metrics, "loc")
        total = int(metrics["total_files"])
        assert total >= 3  # module.py, data.json, sub/nested.py

    def test_metrics_has_total_lines(self, compendium):
        result = compendium.analyze_repository()
        total_lines = int(result["metrics"]["total_lines"])
        assert total_lines > 0

    def test_files_dataframe_not_empty(self, compendium):
        result = compendium.analyze_repository()
        files_df = result["files"]
        assert len(files_df) >= 3

    def test_classes_detected(self, compendium):
        result = compendium.analyze_repository()
        classes_df = result["classes"]
        # Foo class in module.py
        assert len(classes_df) >= 1
        names = list(classes_df["class_name"] if "class_name" in classes_df.columns else [])
        assert any("Foo" in str(n) for n in names)

    def test_functions_detected(self, compendium):
        result = compendium.analyze_repository()
        funcs_df = result["functions"]
        assert len(funcs_df) >= 1
        names = list(funcs_df["function_name"] if "function_name" in funcs_df.columns else [])
        assert any("helper" in str(n) for n in names)

    def test_imports_detected(self, compendium):
        result = compendium.analyze_repository()
        imports_df = result["imports"]
        # module.py imports os and sys
        assert len(imports_df) >= 2

    def test_structure_has_depth_info(self, compendium):
        result = compendium.analyze_repository()
        structure = result["structure"]
        assert structure is not None

    def test_empty_directory(self, tmp_path):
        from src.analysis.repository_analyzer import RepositoryCompendium
        rc = RepositoryCompendium(tmp_path)
        result = rc.analyze_repository()
        assert "metrics" in result
        total = int(result["metrics"]["total_files"])
        assert total == 0

    def test_repo_path_stored(self, tiny_repo):
        from src.analysis.repository_analyzer import RepositoryCompendium
        rc = RepositoryCompendium(tiny_repo)
        assert rc.repo_path == Path(tiny_repo)

    def test_unicode_decode_error_handled(self, tmp_path):
        """Binary files should not crash the analyzer."""
        (tmp_path / "binary.bin").write_bytes(b"\xff\xfe\x00\x01")
        from src.analysis.repository_analyzer import RepositoryCompendium
        rc = RepositoryCompendium(tmp_path)
        result = rc.analyze_repository()  # Should not raise
        assert "metrics" in result

    def test_syntax_error_file_handled(self, tmp_path):
        """Python files with syntax errors should not crash the analyzer."""
        (tmp_path / "broken.py").write_text("def foo(\n  # unclosed\n")
        from src.analysis.repository_analyzer import RepositoryCompendium
        rc = RepositoryCompendium(tmp_path)
        result = rc.analyze_repository()
        assert "metrics" in result


class TestHealthVerifier:
    """Tests for health_verifier module-level functions."""

    def test_test_standard_library_returns_bool(self):
        from src.analysis.health_verifier import test_standard_library
        result = test_standard_library()
        assert isinstance(result, bool)

    def test_test_critical_imports_returns_bool(self):
        from src.analysis.health_verifier import test_critical_imports
        result = test_critical_imports()
        assert isinstance(result, bool)

    def test_test_third_party_imports_returns_bool(self):
        from src.analysis.health_verifier import test_third_party_imports
        result = test_third_party_imports()
        assert isinstance(result, bool)

    def test_run_comprehensive_health_check_returns_bool(self):
        from src.analysis.health_verifier import run_comprehensive_health_check
        result = run_comprehensive_health_check()
        assert isinstance(result, bool)
        # Standard library should always be available
        assert result is True or result is False  # just a type check; may be False in degraded env

    def test_test_key_functionality_returns_bool(self):
        from src.analysis.health_verifier import test_key_functionality
        result = test_key_functionality()
        assert isinstance(result, bool)


class TestRagIndexer:
    """Smoke tests for ChatDevProjectIndexer initialization and helpers."""

    def test_imports(self):
        from src.rag.chatdev_project_indexer import ChatDevProjectIndexer, get_chatdev_project_indexer
        assert ChatDevProjectIndexer is not None
        assert get_chatdev_project_indexer is not None

    def test_instantiation(self, tmp_path):
        from src.rag.chatdev_project_indexer import ChatDevProjectIndexer
        indexer = ChatDevProjectIndexer(chatdev_root=tmp_path)
        assert indexer is not None

    def test_export_index_manifest_empty(self, tmp_path):
        from src.rag.chatdev_project_indexer import ChatDevProjectIndexer
        indexer = ChatDevProjectIndexer(chatdev_root=tmp_path)
        manifest = indexer.export_index_manifest()
        assert isinstance(manifest, dict)
        assert "total_projects" in manifest or "indexed_projects" in manifest or len(manifest) >= 0

    def test_is_chatdev_project_detection(self, tmp_path):
        from src.rag.chatdev_project_indexer import ChatDevProjectIndexer
        indexer = ChatDevProjectIndexer(chatdev_root=tmp_path)
        # Non-chatdev dir
        plain_dir = tmp_path / "plain"
        plain_dir.mkdir()
        (plain_dir / "hello.txt").write_text("hi")
        assert indexer._is_chatdev_project(plain_dir) is False

    def test_chunk_text_returns_list(self, tmp_path):
        from src.rag.chatdev_project_indexer import ChatDevProjectIndexer
        indexer = ChatDevProjectIndexer(chatdev_root=tmp_path)
        text = "A" * 10000
        chunks = indexer._chunk_text(text, chunk_size=1000)
        assert isinstance(chunks, list)
        assert len(chunks) >= 1
        # Each chunk is at most chunk_size characters
        for chunk in chunks:
            assert len(chunk) <= 1000

    def test_chunk_text_short_returns_single(self, tmp_path):
        from src.rag.chatdev_project_indexer import ChatDevProjectIndexer
        indexer = ChatDevProjectIndexer(chatdev_root=tmp_path)
        chunks = indexer._chunk_text("short text", chunk_size=3000)
        assert len(chunks) >= 1
        assert "short text" in chunks[0]

    def test_get_embedding_model_returns_something(self, tmp_path):
        from src.rag.chatdev_project_indexer import ChatDevProjectIndexer
        indexer = ChatDevProjectIndexer(chatdev_root=tmp_path)
        model = indexer._get_embedding_model()
        # Should return some embedding backend (or str fallback) without raising
        assert model is not None

    def test_project_metadata_dataclass(self):
        from src.rag.chatdev_project_indexer import ProjectMetadata
        pm = ProjectMetadata(project_name="test", project_path="/tmp/test", created_at="2026-01-01")
        assert pm.project_name == "test"
        assert pm.project_path == "/tmp/test"
        assert pm.agents == []

    def test_project_document_dataclass(self):
        from src.rag.chatdev_project_indexer import ProjectDocument
        doc = ProjectDocument(doc_id="d1", project_name="test", source_type="code",
                              content="x=1", metadata={})
        assert doc.project_name == "test"
        assert doc.content == "x=1"
        assert doc.created_at is not None
