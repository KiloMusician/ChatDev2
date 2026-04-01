import os
from pathlib import Path

import pytest


@pytest.mark.skipif(
    not os.getenv("USE_EMBEDDINGS"),
    reason="Embeddings not enabled in environment",
)
def test_summary_retrieval_with_embeddings():
    import importlib

    if importlib.util.find_spec("sentence_transformers") is None:
        pytest.skip("sentence_transformers not installed")

    os.environ["USE_EMBEDDINGS"] = "1"
    from src.tools.summary_retrieval import build_engine

    engine = build_engine(Path.cwd())
    if not engine:
        pytest.skip("Retrieval engine not built")

    results = engine.retrieve("consciousness memory palace", top_k=3)
    assert isinstance(results, list)
    # If no matches, it's allowed; just ensure we don't error
    assert all(hasattr(r, "path") for r in results)
