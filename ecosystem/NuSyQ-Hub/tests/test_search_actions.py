"""Unit tests for search action rendering and contracts."""

from __future__ import annotations

from scripts.nusyq_actions import search_actions


def test_search_index_health_derives_missing_counts(monkeypatch) -> None:
    class FakeSearch:
        def __init__(self) -> None:
            self.file_metadata = {
                "a.py": {"functions": ["fa", "fb"], "classes": ["A"]},
                "b.py": {"functions": ["fc"], "classes": ["B", "C"]},
            }
            self.keyword_index = {"alpha": {}, "beta": {}, "gamma": {}}

        def get_index_health(self) -> dict[str, object]:
            return {"status": "healthy"}

        def get_index_stats(self) -> dict[str, object]:
            # Deliberately omit functions/classes/keywords keys.
            return {"total_files": 2, "total_keywords": 3}

    from src.search import smart_search as smart_search_module

    monkeypatch.setattr(smart_search_module, "SmartSearch", FakeSearch)
    monkeypatch.setattr(search_actions, "emit_action_receipt", lambda *args, **kwargs: None)

    result = search_actions.handle_search_index_health()
    output = result["output"]

    assert result["status"] == "success"
    assert "Functions found: 3" in output
    assert "Classes found: 3" in output
    assert "Keywords tracked: 3" in output
