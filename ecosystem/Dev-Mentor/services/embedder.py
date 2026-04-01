"""
Embedding Worker — text embedding and similarity search for the ΔΨΣ ecosystem.

Two backends (in priority order):
  1. Ollama /api/embeddings  — dense vector embeddings (requires a running Ollama
     with an embedding model like nomic-embed-text or mxbai-embed-large)
  2. TF-IDF bag-of-words     — pure stdlib fallback, always available offline

Embeddings are cached in SQLite so repeated calls are instant.
Source text is stored alongside vectors so query_index can return readable results.
Cosine similarity search is implemented in pure Python (no numpy).

Msg⛛ protocol: [ML⛛{embed}]

API:
  embed(text)                     → list[float]
  similarity(a, b)                → float  (0-1)
  search(query, corpus)           → list[(score, text)]
  index_text(doc_id, text)        → stores embedding + source text in DB
  query_index(query_text, top_k)  → top-k similar docs with text snippets
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

_ROOT = Path(__file__).resolve().parent.parent
_DB_PATH = _ROOT / "state" / "embeddings.db"
_OLLAMA_BASE = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
_EMBED_MODEL = os.environ.get("EMBED_MODEL", "nomic-embed-text")

_DDL = """
CREATE TABLE IF NOT EXISTS embedding_cache (
    doc_id      TEXT NOT NULL,
    text_hash   TEXT NOT NULL,
    backend     TEXT,
    vector      TEXT,           -- JSON list[float]
    dim         INTEGER,
    source_text TEXT,           -- original text for re-embedding at query time
    ts          REAL,
    PRIMARY KEY (doc_id)
);
CREATE INDEX IF NOT EXISTS idx_ec_hash ON embedding_cache(text_hash);
"""

# Run DB init at import time so the migration always applies (idempotent)
def _ensure_db() -> None:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with sqlite3.connect(str(_DB_PATH)) as c:
            c.executescript(_DDL)
            try:
                c.execute("ALTER TABLE embedding_cache ADD COLUMN source_text TEXT")
                c.commit()
            except Exception:
                pass
    except Exception:
        pass

_ensure_db()


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def _init_db() -> None:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _conn() as c:
        c.executescript(_DDL)
        # Migrate: add source_text column if missing (idempotent)
        try:
            c.execute("ALTER TABLE embedding_cache ADD COLUMN source_text TEXT")
            c.commit()
        except Exception:
            pass


# ── Tokeniser (stdlib) ────────────────────────────────────────────────────────

_STOP = {
    "the", "a", "an", "in", "on", "of", "to", "is", "it", "and",
    "or", "for", "with", "this", "that", "are", "be", "at", "as",
    "by", "from", "not", "but", "was", "has", "have", "do", "did",
    "i", "you", "we", "he", "she", "they", "my", "your", "our",
}


def _tokenise(text: str) -> List[str]:
    tokens = re.findall(r"[a-z0-9_]+", text.lower())
    return [t for t in tokens if t not in _STOP and len(t) > 1]


# ── TF-IDF vocabulary (shared across corpus) ─────────────────────────────────

def _tfidf_embed(text: str, vocab: Optional[List[str]] = None) -> List[float]:
    """
    Simple TF-IDF vector. Vocab defaults to the text's own terms (256-dim).
    For index search, pass a shared vocab built from query + corpus.
    """
    tokens = _tokenise(text)
    counts = Counter(tokens)
    total = sum(counts.values()) or 1

    if vocab is None:
        vocab = sorted(set(tokens))[:256]

    vec = []
    for term in vocab:
        tf = counts.get(term, 0) / total
        vec.append(tf)
    return vec


# ── Ollama embeddings ─────────────────────────────────────────────────────────

def _ollama_embed(text: str, timeout: int = 5) -> Optional[List[float]]:
    try:
        resp = requests.post(
            f"{_OLLAMA_BASE}/api/embeddings",
            json={"model": _EMBED_MODEL, "prompt": text},
            timeout=timeout,
        )
        if resp.status_code == 200:
            return resp.json().get("embedding", [])
    except Exception:
        pass
    return None


def _ollama_available() -> bool:
    try:
        resp = requests.get(f"{_OLLAMA_BASE}/api/tags", timeout=2)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            return any("embed" in m or "nomic" in m or "mxbai" in m for m in models)
    except Exception:
        pass
    return False


# ── Public embed API ──────────────────────────────────────────────────────────

def embed(text: str, doc_id: Optional[str] = None,
          use_cache: bool = True) -> Tuple[List[float], str]:
    """
    Returns (vector, backend_used).
    backend_used is 'ollama' or 'tfidf'.
    """
    if not text.strip():
        return ([], "empty")

    text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
    _did = doc_id or text_hash

    if use_cache:
        with _conn() as c:
            row = c.execute(
                "SELECT vector, backend FROM embedding_cache WHERE doc_id=?", (_did,)
            ).fetchone()
            if row:
                return json.loads(row["vector"]), row["backend"]

    backend = "tfidf"
    vector: List[float] = []

    if _ollama_available():
        v = _ollama_embed(text)
        if v:
            vector = v
            backend = "ollama"

    if not vector:
        tokens = _tokenise(text)
        vocab = sorted(set(tokens))[:256]
        vector = _tfidf_embed(text, vocab)
        backend = "tfidf"

    if use_cache and vector:
        snippet = text[:1000]
        with _conn() as c:
            c.execute(
                """INSERT INTO embedding_cache
                   (doc_id, text_hash, backend, vector, dim, source_text, ts)
                   VALUES (?,?,?,?,?,?,?)
                   ON CONFLICT(doc_id) DO UPDATE SET
                       vector=excluded.vector, source_text=excluded.source_text,
                       ts=excluded.ts""",
                (_did, text_hash, backend, json.dumps(vector), len(vector),
                 snippet, time.time()),
            )
            c.commit()

    return vector, backend


# ── Cosine similarity (pure Python) ──────────────────────────────────────────

def _dot(a: List[float], b: List[float]) -> float:
    n = min(len(a), len(b))
    return sum(a[i] * b[i] for i in range(n))


def _mag(v: List[float]) -> float:
    return math.sqrt(sum(x * x for x in v)) or 1e-9


def similarity(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two vectors."""
    if not a or not b:
        return 0.0
    return max(0.0, min(1.0, _dot(a, b) / (_mag(a) * _mag(b))))


def search(query: str, corpus: List[str], top_k: int = 5) -> List[Tuple[float, str]]:
    """
    Embed query + all corpus items (TF-IDF with shared vocab), return ranked results.
    """
    all_texts = [query] + corpus
    all_tokens = []
    for t in all_texts:
        all_tokens.extend(_tokenise(t))
    vocab = sorted(set(all_tokens))[:256]

    q_vec = _tfidf_embed(query, vocab)
    results = []
    for text in corpus:
        c_vec = _tfidf_embed(text, vocab)
        score = similarity(q_vec, c_vec)
        results.append((score, text))
    results.sort(key=lambda x: -x[0])
    return results[:top_k]


# ── Doc index (for serena / agent queries) ────────────────────────────────────

def index_text(doc_id: str, text: str) -> str:
    """Index a document: embed it and store with its source text for retrieval.
    Always updates source_text even when the vector is already cached.
    """
    _, backend = embed(text, doc_id=doc_id, use_cache=True)
    # Always persist source_text — embed() may return early on cache hit
    # without updating source_text for docs indexed before this column existed.
    snippet = text[:1000]
    try:
        with _conn() as c:
            c.execute(
                "UPDATE embedding_cache SET source_text=? WHERE doc_id=? AND (source_text IS NULL OR source_text='')",
                (snippet, doc_id),
            )
            c.commit()
    except Exception:
        pass
    return backend


def query_index(query_text: str, top_k: int = 5) -> List[Dict]:
    """
    Search all indexed docs for query_text.
    Returns results with doc_id, score, text snippet, and path metadata.
    Uses a shared TF-IDF vocab built from query + stored source texts so
    all vectors are comparable in the same space.
    """
    with _conn() as c:
        rows = c.execute(
            "SELECT doc_id, backend, source_text FROM embedding_cache"
        ).fetchall()

    if not rows:
        return []

    # Build shared vocab from query + all stored source texts.
    # Use frequency-based vocabulary selection so we capture the most
    # informative tokens (not alphabetical truncation which cuts off later letters).
    # Query terms are always included to guarantee recall.
    from collections import Counter as _Counter

    query_tokens = set(_tokenise(query_text))
    token_freq: _Counter = _Counter()
    for r in rows:
        src = r["source_text"] or r["doc_id"]
        for tok in _tokenise(src[:500]):
            token_freq[tok] += 1

    # Always include query tokens; fill rest with most-frequent corpus tokens.
    # Cap total vocab at 1024 to keep vectors comparable.
    _max_vocab = 1024
    top_corpus = [tok for tok, _ in token_freq.most_common(_max_vocab)]
    extra_slots = max(0, _max_vocab - len(query_tokens))
    vocab_set = query_tokens | set(top_corpus[:extra_slots])
    vocab = sorted(vocab_set)

    q_vec = _tfidf_embed(query_text, vocab)

    results = []
    for row in rows:
        src_text = row["source_text"] or row["doc_id"]
        if row["backend"] == "ollama":
            # For ollama docs: re-embed query with ollama and use stored vector
            try:
                with _conn() as c2:
                    stored_row = c2.execute(
                        "SELECT vector FROM embedding_cache WHERE doc_id=?",
                        (row["doc_id"],)
                    ).fetchone()
                stored = json.loads(stored_row["vector"] or "[]") if stored_row else []
                doc_q_vec, _ = embed(query_text, use_cache=False)
                score = similarity(doc_q_vec, stored)
            except Exception:
                score = 0.0
        else:
            # TF-IDF: embed source text with the shared vocab
            cand_vec = _tfidf_embed(src_text[:500], vocab)
            score = similarity(q_vec, cand_vec)

        if score > 0.001:
            # Parse doc_id to extract path/name metadata (format: path:name:lineno)
            parts = row["doc_id"].split(":")
            result = {
                "doc_id": row["doc_id"],
                "score": round(score, 4),
                "backend": row["backend"],
                "text": src_text[:200],
            }
            if len(parts) >= 2:
                result["path"] = parts[0]
                result["name"] = parts[1] if len(parts) > 1 else ""
                result["lineno"] = parts[2] if len(parts) > 2 else ""
            results.append(result)

    results.sort(key=lambda x: -x["score"])
    return results[:top_k]


def embedding_stats() -> Dict:
    with _conn() as c:
        total = c.execute("SELECT COUNT(*) FROM embedding_cache").fetchone()[0]
        by_backend = c.execute(
            "SELECT backend, COUNT(*) as n FROM embedding_cache GROUP BY backend"
        ).fetchall()
        has_text = c.execute(
            "SELECT COUNT(*) FROM embedding_cache WHERE source_text IS NOT NULL AND source_text != ''"
        ).fetchone()[0]
    return {
        "indexed_docs": total,
        "docs_with_text": has_text,
        "by_backend": {r["backend"]: r["n"] for r in by_backend},
        "ollama_embed_available": _ollama_available(),
        "embed_model": _EMBED_MODEL,
    }


def initialise() -> Dict:
    _init_db()
    return {"status": "ready", **embedding_stats()}
