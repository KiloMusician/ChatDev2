from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.nusyq_bridge as bridge


def test_candidate_base_urls_include_nusyq_hub_dev_alias():
    candidates = bridge._candidate_base_urls("http://nusyq-hub:8000")

    assert candidates == ["http://nusyq-hub:8000", "http://nusyq-hub-dev:8000"]


def test_candidate_base_urls_leave_unknown_hosts_unchanged():
    candidates = bridge._candidate_base_urls("http://example.internal:9000")

    assert candidates == ["http://example.internal:9000"]
