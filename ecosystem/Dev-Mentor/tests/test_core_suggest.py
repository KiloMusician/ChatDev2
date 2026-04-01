from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.suggest import Suggester


def test_suggester_uses_services_inference_wrapper_when_llm_enabled() -> None:
    suggester = Suggester(use_llm=True)
    assert callable(suggester._llm_fn)
    assert suggester._llm_fn.__module__ == "services.inference"
