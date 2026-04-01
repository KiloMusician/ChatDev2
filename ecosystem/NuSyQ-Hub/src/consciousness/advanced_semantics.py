"""Helper utilities for optional advanced semantic cognition."""

from __future__ import annotations

import importlib
from collections.abc import Sequence
from types import ModuleType
from typing import Any, cast

from .house_models import MemoryEngram

FaissIndex = Any
SentenceTransformerClass = Any
TiktokenEncoding = Any


def _import_optional_module(name: str) -> ModuleType | None:
    try:
        return importlib.import_module(name)  # nosemgrep
    except ImportError:
        return None


_faiss_module: ModuleType | None = _import_optional_module("faiss")
_np_module: ModuleType | None = _import_optional_module("numpy")
_sentence_transformers_module: ModuleType | None = _import_optional_module("sentence_transformers")
_tiktoken_module: ModuleType | None = _import_optional_module("tiktoken")


def _get_sentence_transformer() -> type[Any] | None:
    if _sentence_transformers_module is None:
        return None
    return getattr(_sentence_transformers_module, "SentenceTransformer", None)


def _create_faiss_index(dim: int) -> Any | None:
    if _faiss_module is None:
        return None
    index_cls = getattr(_faiss_module, "IndexFlatIP", None)
    if index_cls is None:
        return None
    return index_cls(dim)


class AdvancedCognitionToolkit:
    """Encapsulate optional semantic cognition tooling."""

    def __init__(self) -> None:
        """Initialize AdvancedCognitionToolkit."""
        transformer_cls = _get_sentence_transformer()
        self.semantic_encoder: SentenceTransformerClass | None = (
            transformer_cls("all-MiniLM-L6-v2") if transformer_cls else None
        )
        self.tokenizer: TiktokenEncoding | None = (
            _tiktoken_module.get_encoding("cl100k_base") if _tiktoken_module else None
        )
        self.vector_index: FaissIndex | None = _create_faiss_index(384)

    def encode(self, text: str) -> list[float] | None:
        if self.semantic_encoder:
            return cast(list[float], self.semantic_encoder.encode(text))
        return None

    def add_vector(self, vector: Sequence[float]) -> None:
        if self.vector_index and _np_module is not None:
            self.vector_index.add(_np_module.array([vector]))

    def cluster_semantic_vectors(
        self,
        engrams_with_vectors: list[MemoryEngram],
        similarity_threshold: float = 0.7,
    ) -> list[list[MemoryEngram]]:
        """Cluster engrams by cosine similarity if numpy is available."""
        if not _np_module or not engrams_with_vectors:
            return []

        vectors = [
            _np_module.array(engram.semantic_vector or []) for engram in engrams_with_vectors
        ]
        if not vectors:
            return []

        clusters: list[list[MemoryEngram]] = []
        used: set[int] = set()

        for i, engram_i in enumerate(engrams_with_vectors):
            if i in used:
                continue
            cluster = [engram_i]
            used.add(i)

            for j, engram_j in enumerate(engrams_with_vectors[i + 1 :], i + 1):
                if j in used:
                    continue

                vec_i = vectors[i]
                vec_j = vectors[j]
                if vec_i.size == 0 or vec_j.size == 0:
                    continue

                norm_product = float(_np_module.linalg.norm(vec_i) * _np_module.linalg.norm(vec_j))
                similarity = _np_module.dot(vec_i, vec_j) / max(norm_product, 1e-9)

                if similarity > similarity_threshold:
                    cluster.append(engram_j)
                    used.add(j)

            if len(cluster) >= 2:
                clusters.append(cluster)

        return clusters
