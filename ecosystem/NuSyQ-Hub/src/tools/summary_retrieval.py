#!/usr/bin/env python3
"""🔎 Summary / Report / Analysis Retrieval Engine (Lightweight RAG).

====================================================================

OmniTag: {
  "purpose": "Provide retrieval-augmented context from indexed summary/report/analysis docs",
  "dependencies": ["summary_indexer"],
  "context": "Enrich orchestration tasks with historically relevant documentation artifacts",
  "evolution_stage": "rag-v1"
}

This module implements a minimal retrieval layer over the generated
`docs/Auto/SUMMARY_INDEX.json` artifact. It deliberately avoids heavy
ML dependencies (vector DBs, transformers) to remain portable and fast.

Retrieval Strategy:
1. Load metadata from summary index.
2. Read each file's first N characters (default 4000) for lightweight content snapshot.
3. Tokenize into lowercase alphanumeric terms; build TF and document frequencies.
4. Compute TF-IDF (log-scaled idf) vectors lazily.
5. For a query: tokenize, compute query TF-IDF, cosine similarity to each doc.
6. Return top-k scored documents with essential metadata.

Extensibility hooks:
- Replace internal `_tokenize` with stemming/lemmatization if needed.
- Swap TF-IDF for embeddings (e.g. sentence-transformers) guarded by optional dependency.
- Add semantic category boosting (e.g. emphasize `analysis` for reasoning tasks).

Failsafe behavior: Any exception yields an empty list; no task failure.
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+")


@dataclass
class RetrievedDoc:
    path: str
    title: str | None
    category: str
    score: float
    size_bytes: int
    modified: str


class SummaryRetrievalEngine:
    """Lightweight TF-IDF retrieval over summary/report/analysis documents."""

    def __init__(
        self,
        root: Path,
        index_path: Path | None = None,
        snapshot_chars: int = 4000,
    ) -> None:
        """Initialize SummaryRetrievalEngine with root, index_path, snapshot_chars."""
        self.root = root
        self.index_path = index_path or root / "docs" / "Auto" / "SUMMARY_INDEX.json"
        self.snapshot_chars = snapshot_chars
        self._raw_index: dict[str, Any] | None = None
        self._docs: list[dict[str, Any]] = []
        self._doc_tokens: list[dict[str, int]] = []
        self._df: dict[str, int] = {}
        self._tfidf_cache: list[dict[str, float]] = []
        self._embeddings: list[Any] = []
        self._use_embeddings = os.getenv("USE_EMBEDDINGS", "false").lower() in (
            "1",
            "true",
            "yes",
        )
        self._embed_model: Any | None = None
        self._loaded = False
        self._load_index()

    def _load_index(self) -> None:
        if not self.index_path.exists():
            return
        try:
            self._raw_index = json.loads(self.index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._raw_index = None
            return
        raw_index = self._raw_index
        if not isinstance(raw_index, dict):
            return
        files = raw_index.get("files", [])
        for meta in files:
            path = Path(meta.get("path", ""))
            if not path.exists():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")[: self.snapshot_chars]
            except OSError:
                text = ""
            tokens = self._tokenize(text)
            tf: dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            # update df
            for t in set(tokens):
                self._df[t] = self._df.get(t, 0) + 1
            self._docs.append(meta)
            self._doc_tokens.append(tf)
            # if embeddings are enabled, collect snapshot text for embedding later
            self._docs[-1]["_snapshot_text"] = text
        self._loaded = True
        self._build_tfidf_cache()
        if self._use_embeddings:
            self._initialize_embeddings()

    def _tokenize(self, text: str) -> list[str]:
        return [m.group(0).lower() for m in TOKEN_PATTERN.finditer(text)]

    def _build_tfidf_cache(self) -> None:
        # Precompute TF-IDF vectors
        N = max(len(self._docs), 1)
        self._tfidf_cache = []
        for tf in self._doc_tokens:
            vec: dict[str, float] = {}
            total_terms = sum(tf.values()) or 1
            for term, count in tf.items():
                tf_weight = count / total_terms
                idf = math.log((N + 1) / (1 + self._df.get(term, 0))) + 1.0
                vec[term] = tf_weight * idf
            self._tfidf_cache.append(vec)

    def _initialize_embeddings(self) -> None:
        """Set up embedding model and compute document embeddings.

        This is an optional path: if `sentence_transformers` is not installed,
        we fallback to TF-IDF.
        """
        try:
            from sentence_transformers import SentenceTransformer

            model_name = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
            self._embed_model = SentenceTransformer(model_name)
            texts = [m.get("_snapshot_text", "") for m in self._docs]
            if texts:
                # Compute embeddings using the model
                embs = self._embed_model.encode(texts, convert_to_numpy=True)
                self._embeddings = list(embs)
        except (ImportError, OSError, RuntimeError):
            # Embeddings unavailable; fallback to TF-IDF only
            self._embeddings = []
            self._use_embeddings = False

    def _compute_query_vec(self, tokens: list[str]) -> dict[str, float]:
        tf: dict[str, int] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        N = max(len(self._docs), 1)
        total = sum(tf.values()) or 1
        vec: dict[str, float] = {}
        for term, count in tf.items():
            tf_weight = count / total
            idf = math.log((N + 1) / (1 + self._df.get(term, 0))) + 1.0
            vec[term] = tf_weight * idf
        return vec

    @staticmethod
    def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
        common = set(a.keys()) & set(b.keys())
        num = sum(a[t] * b[t] for t in common)
        denom_a = math.sqrt(sum(v * v for v in a.values())) or 1.0
        denom_b = math.sqrt(sum(v * v for v in b.values())) or 1.0
        return num / (denom_a * denom_b)

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedDoc]:
        if not self._loaded or not self._docs:
            return []
        try:
            scores: list[tuple[int, float]] = []
            # Embedding-based similarity if model available
            if self._use_embeddings and self._embeddings:
                try:
                    import numpy as np
                    from numpy.linalg import norm

                    model_name = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
                    # compute query embedding
                    if self._embed_model is None:
                        from sentence_transformers import SentenceTransformer

                        self._embed_model = SentenceTransformer(model_name)
                    q_emb = self._embed_model.encode([query], convert_to_numpy=True)[0]
                    for idx, d_emb in enumerate(self._embeddings):
                        denom = (norm(q_emb) * norm(d_emb)) or 1.0
                        score = float(np.dot(q_emb, d_emb) / denom)
                        if score > 0:
                            scores.append((idx, score))
                except (ImportError, AttributeError, ValueError):
                    # fallback to TF-IDF
                    logger.debug("Suppressed AttributeError/ImportError/ValueError", exc_info=True)

            if not scores:
                tokens = self._tokenize(query)
                q_vec = self._compute_query_vec(tokens)
                for idx, d_vec in enumerate(self._tfidf_cache):
                    score = self._cosine(q_vec, d_vec)
                    if score > 0:
                        scores.append((idx, score))
            scores.sort(key=lambda x: x[1], reverse=True)
            results: list[RetrievedDoc] = []
            for idx, score in scores[:top_k]:
                meta = self._docs[idx]
                results.append(
                    RetrievedDoc(
                        path=meta.get("path", ""),
                        title=meta.get("title"),
                        category=meta.get("category", "unknown"),
                        score=round(score, 6),
                        size_bytes=meta.get("size_bytes", 0),
                        modified=meta.get("modified", ""),
                    ),
                )
            return results
        except (AttributeError, KeyError, IndexError):
            return []


def build_engine(root: Path) -> SummaryRetrievalEngine | None:
    try:
        return SummaryRetrievalEngine(root)
    except (FileNotFoundError, ImportError, OSError):
        return None


if __name__ == "__main__":  # pragma: no cover
    repo_root = Path(__file__).resolve().parents[2]
    engine = build_engine(repo_root)
    if not engine:
        pass
    else:
        sample_query = "quantum consciousness integration pipeline"
        for _r in engine.retrieve(sample_query, top_k=5):
            pass
