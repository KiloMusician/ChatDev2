from __future__ import annotations

import json
from io import StringIO

from src.codemap_style_output import OutputFormat, RecordType, analyze_trace, render


def test_agent_output_is_kv_lines() -> None:
    out = StringIO()
    render(analyze_trace("fetchData"), OutputFormat.AGENT, out)
    lines = [line.strip() for line in out.getvalue().splitlines() if line.strip()]

    assert lines[0].startswith("record=meta")
    assert lines[-1].startswith("record=end")
    for line in lines:
        for token in line.split("\t"):
            assert "=" in token  # every token is key=value


def test_jsonl_output_is_valid_json() -> None:
    out = StringIO()
    render(analyze_trace("fetchData"), OutputFormat.JSONL, out)
    payloads = [json.loads(line) for line in out.getvalue().splitlines() if line.strip()]

    assert payloads[0]["record"] == RecordType.META.value
    assert payloads[-1]["record"] == RecordType.END.value
    # ensure optional fields are stripped when absent
    assert "line" not in payloads[0]
