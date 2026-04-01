from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

from src.search.smart_search import (
    OutputFormat,
    SmartSearch,
    _run_find,
    render_results,
)


def _build_search_with_indexes() -> SmartSearch:
    search = SmartSearch(repo_root=Path("."))
    # Inject lightweight indexes to avoid disk I/O
    search._file_metadata = {  # type: ignore[attr-defined]
        "a.py": {"file_type": "python"},
        "b.py": {"file_type": "python"},
    }
    search._keyword_index = {  # type: ignore[attr-defined]
        "foo": ["a.py", "b.py"],
    }
    return search


def test_agent_output_records_are_kv_lines() -> None:
    search = _build_search_with_indexes()
    results = search.search_keyword("foo", limit=5)

    out = StringIO()
    render_results(results, OutputFormat.AGENT, out)
    lines = [line.strip() for line in out.getvalue().splitlines() if line.strip()]

    assert lines[0].startswith("record=result")
    assert all("\t" in line for line in lines)
    for line in lines:
        for token in line.split("\t"):
            assert "=" in token


def test_jsonl_output_is_valid_and_has_required_fields() -> None:
    search = _build_search_with_indexes()
    # Simulate find command results
    args = type("Args", (), {"pattern": "*.py", "limit": 2})
    results = _run_find(search, args)

    out = StringIO()
    render_results(results, OutputFormat.JSONL, out)
    payloads = [json.loads(line) for line in out.getvalue().splitlines() if line.strip()]

    assert payloads
    assert payloads[0]["record"] == "result"
    assert "file" in payloads[0]
