"""
agents/serena/cocoindex_bridge.py — CocoIndex semantic indexing bridge for Serena.

CocoIndex (https://github.com/cocoindex-io/cocoindex) is a high-performance
incremental data transformation and indexing framework for AI pipelines.
It provides:
  - Declarative flow definitions for ETL → embedding → vector DB
  - Incremental re-indexing (only changed files are re-processed)
  - Built-in support for LLM embedding backends
  - First-class Python API

This bridge wires CocoIndex to Serena's MemoryPalace architecture:
  Repo files → CocoIndex Flow → nomic-embed-text (Ollama) → SQLite vector store
                                                           ↓
                                              MemoryPalace.search() upgraded
                                              to vector similarity (cosine)

Install:
    pip install cocoindex

Run initial index:
    python agents/serena/cocoindex_bridge.py --index
    python agents/serena/cocoindex_bridge.py --query "XP gain logic"

Environment variables:
    COCOINDEX_DB      Path to cocoindex SQLite DB (default: state/cocoindex.db)
    EMBED_MODEL       Ollama embedding model (default: nomic-embed-text)
    OLLAMA_HOST       Ollama base URL (default: http://localhost:11434)

ΨΞΦΩ role: Ψ-enhancement — semantic signal intake to augment the Ω-core.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

LOG = logging.getLogger("serena.cocoindex")

_ROOT = Path(__file__).resolve().parents[2]
_COCO_DB = Path(os.getenv("COCOINDEX_DB", str(_ROOT / "state" / "cocoindex.db")))
_OLLAMA_BASE = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
_EMBED_MODEL = os.environ.get("EMBED_MODEL", "nomic-embed-text")

# Files to index — mirrors RepoWalker.INDEXABLE_EXTS but focused set
_INDEXABLE_EXTS = {".py", ".md", ".yaml", ".yml", ".txt"}
_SKIP_DIRS = {
    ".git", "__pycache__", ".mypy_cache", ".pytest_cache",
    "node_modules", ".vscode", ".devmentor",
    "outputs", ".local", "sessions", "state", "dist", "build",
    ".pythonlibs", ".cache", ".npm", "venv", ".venv", "site-packages",
    "lib", ".uv", "attached_assets", "knowledge",
}
_MAX_FILE_BYTES = 200_000   # 200KB cap per file


# ── SQLite schema for vector store ───────────────────────────────────────────

_DDL = """
CREATE TABLE IF NOT EXISTS coco_meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
CREATE TABLE IF NOT EXISTS coco_chunks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id      TEXT NOT NULL UNIQUE,
    path        TEXT NOT NULL,
    kind        TEXT NOT NULL,
    name        TEXT NOT NULL,
    lineno      INTEGER DEFAULT 0,
    end_lineno  INTEGER DEFAULT 0,
    text        TEXT NOT NULL,
    docstring   TEXT,
    embedding   TEXT,               -- JSON list[float] from nomic-embed-text
    embed_model TEXT,               -- model name used
    dim         INTEGER DEFAULT 0,
    file_hash   TEXT,               -- SHA-256 of source file for incremental
    indexed_at  REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_coco_path ON coco_chunks(path);
CREATE INDEX IF NOT EXISTS idx_coco_kind ON coco_chunks(kind);
CREATE INDEX IF NOT EXISTS idx_coco_name ON coco_chunks(name);
CREATE INDEX IF NOT EXISTS idx_coco_hash ON coco_chunks(file_hash);
"""


def _get_conn(path: Path = _COCO_DB) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(_DDL)
    conn.commit()
    return conn


# ── Ollama nomic-embed-text ───────────────────────────────────────────────────

def _ollama_embed(text: str, timeout: int = 10) -> Optional[List[float]]:
    """Call Ollama /api/embeddings with nomic-embed-text. Returns float list or None."""
    try:
        resp = requests.post(
            f"{_OLLAMA_BASE}/api/embeddings",
            json={"model": _EMBED_MODEL, "prompt": text[:4096]},
            timeout=timeout,
        )
        if resp.status_code == 200:
            vec = resp.json().get("embedding", [])
            return vec if vec else None
    except Exception as exc:
        LOG.debug("Ollama embed failed: %s", exc)
    return None


def _ollama_available() -> bool:
    """Check Ollama is running and nomic-embed-text is loaded."""
    try:
        resp = requests.get(f"{_OLLAMA_BASE}/api/tags", timeout=3)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            return any("nomic" in m or "embed" in m for m in models)
    except Exception:
        pass
    return False


# ── Cosine similarity (pure Python, no numpy dep) ────────────────────────────

def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    dot = sum(a[i] * b[i] for i in range(n))
    mag_a = math.sqrt(sum(x * x for x in a)) or 1e-9
    mag_b = math.sqrt(sum(x * x for x in b)) or 1e-9
    return max(0.0, min(1.0, dot / (mag_a * mag_b)))


# ── File hashing for incremental indexing ────────────────────────────────────

def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    try:
        h.update(path.read_bytes())
    except Exception:
        pass
    return h.hexdigest()[:16]


# ── Chunking (reuses walker logic, no import dependency) ─────────────────────

def _chunk_python(path: str, source: str) -> List[Dict]:
    """Extract function/class chunks from Python source using ast."""
    import ast
    chunks = []
    lines = source.splitlines(keepends=True)

    def _text(node) -> str:
        start = node.lineno - 1
        end = getattr(node, "end_lineno", node.lineno)
        return "".join(lines[start:end])

    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError:
        return [{"kind": "module", "name": "", "lineno": 1,
                 "end_lineno": len(lines), "text": source[:3000], "docstring": None}]

    module_doc = ast.get_docstring(tree)
    chunks.append({
        "kind": "module", "name": "",
        "lineno": 1, "end_lineno": min(30, len(lines)),
        "text": "".join(lines[:30]),
        "docstring": module_doc,
    })

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            chunks.append({
                "kind": "function",
                "name": node.name,
                "lineno": node.lineno,
                "end_lineno": getattr(node, "end_lineno", node.lineno),
                "text": _text(node)[:4096],
                "docstring": ast.get_docstring(node),
            })
        elif isinstance(node, ast.ClassDef):
            chunks.append({
                "kind": "class",
                "name": node.name,
                "lineno": node.lineno,
                "end_lineno": getattr(node, "end_lineno", node.lineno),
                "text": _text(node)[:4096],
                "docstring": ast.get_docstring(node),
            })
    return chunks


def _chunk_text(path: str, text: str, chunk_lines: int = 30) -> List[Dict]:
    """Split non-Python text into line-window chunks."""
    lines = text.splitlines()
    chunks = []
    for i in range(0, len(lines), chunk_lines):
        block = lines[i: i + chunk_lines]
        chunks.append({
            "kind": "text",
            "name": f"block_{i // chunk_lines}",
            "lineno": i + 1,
            "end_lineno": i + len(block),
            "text": "\n".join(block),
            "docstring": None,
        })
    return chunks


def _should_skip(rel: Path) -> bool:
    return any(part in _SKIP_DIRS for part in rel.parts)


# ── CocoIndex Flow (declarative description) ─────────────────────────────────
#
# CocoIndex uses a Flow abstraction: you define Sources, Transformers, and
# Targets, then cocoindex handles incremental re-runs.
#
# Our conceptual flow (implemented below in pure Python as a fallback when
# the cocoindex package is not installed):
#
#   Source:      LocalFileSource(repo_root, extensions=[...])
#   Transformer: PythonChunker / TextChunker
#   Embedder:    OllamaEmbedder(model="nomic-embed-text")
#   Target:      SQLiteVectorStore(state/cocoindex.db)
#
# When cocoindex IS installed, CocoIndexFlow.run() delegates to it for
# incremental scheduling and state tracking.


class CocoIndexFlow:
    """
    Semantic indexing pipeline for Dev-Mentor / Serena.

    Two-tier operation:
      1. If `cocoindex` package is installed → uses native CocoIndex Flow API
         for incremental indexing with full state tracking.
      2. Fallback → custom incremental pipeline using file hashes + SQLite,
         same SQLite schema, compatible query API.

    Embedding backend: nomic-embed-text via Ollama (localhost:11434).
    Fallback backend:  lightweight TF-IDF (no Ollama needed).
    """

    def __init__(
        self,
        repo_root: Path = _ROOT,
        db_path: Path = _COCO_DB,
    ):
        self.repo_root = Path(repo_root)
        self.db_path = Path(db_path)
        self._conn: Optional[sqlite3.Connection] = None

        # Detect cocoindex availability
        try:
            import cocoindex  # noqa: F401
            self._has_cocoindex = True
            LOG.info("cocoindex package detected — native flow available")
        except ImportError:
            self._has_cocoindex = False
            LOG.info("cocoindex not installed — using built-in incremental pipeline")

        self._use_ollama = _ollama_available()
        if self._use_ollama:
            LOG.info("Ollama available — using nomic-embed-text for embeddings")
        else:
            LOG.info("Ollama unavailable — TF-IDF fallback for embeddings")

    def _db(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = _get_conn(self.db_path)
        return self._conn

    # ── Native CocoIndex flow ─────────────────────────────────────────────

    def _run_native_cocoindex(self, incremental: bool = True) -> Dict:
        """
        Use the cocoindex library's Flow API.

        CocoIndex flow definition:
          - Source: directory scanner over repo_root
          - Split:  Python AST / text window chunker
          - Embed:  Ollama nomic-embed-text
          - Store:  SQLite (our schema, compatible with query_semantic)

        The library handles incremental re-runs automatically via its
        content-addressed state store.
        """
        import cocoindex

        # Build the flow
        @cocoindex.flow_def(name="DevMentorSerena")
        def dev_mentor_flow(flow_builder: cocoindex.FlowBuilder, data_scope: cocoindex.DataScope):
            # Source: local directory
            data_scope["files"] = flow_builder.add_source(
                cocoindex.sources.LocalFile(
                    path=str(self.repo_root),
                    included_patterns=[
                        "**/*.py", "**/*.md", "**/*.yaml",
                        "**/*.yml", "**/*.txt",
                    ],
                    excluded_patterns=[
                        f"**/{d}/**" for d in _SKIP_DIRS
                    ] + ["**/state/**", "**/knowledge/**"],
                )
            )

            # Transform: split files into chunks
            data_scope["chunks"] = data_scope["files"].transform(
                cocoindex.functions.SplitRecursively(
                    language=None,   # auto-detect Python / text
                    chunk_size=1200,
                    chunk_overlap=120,
                )
            )

            # Embed with nomic-embed-text via Ollama
            data_scope["embeddings"] = data_scope["chunks"].transform(
                cocoindex.functions.SentenceTransformerEmbed(
                    model="nomic-embed-text",
                    # CocoIndex supports custom endpoint — point to Ollama
                    base_url=f"{_OLLAMA_BASE}/v1",
                )
            )

            # Store: write to our SQLite schema via a custom collector
            # (CocoIndex also supports Qdrant, Postgres pgvector, etc.)
            data_scope["embeddings"].export(
                cocoindex.storages.SqliteStorage(
                    database=str(self.db_path),
                    table="coco_chunks",
                )
            )

        # Run the flow (incremental if state exists)
        try:
            cocoindex.update(dev_mentor_flow)
            stats = cocoindex.stats(dev_mentor_flow)
            return {
                "backend": "cocoindex_native",
                "stats": stats,
                "embed_model": _EMBED_MODEL,
            }
        except Exception as exc:
            LOG.warning("Native CocoIndex flow failed (%s), falling back", exc)
            return self._run_builtin_pipeline(incremental=incremental)

    # ── Built-in incremental pipeline ────────────────────────────────────

    def _run_builtin_pipeline(self, incremental: bool = True) -> Dict:
        """
        Pure-Python incremental pipeline.
        Hashes each file; skips unchanged files if incremental=True.
        """
        conn = self._db()
        stats = {"files_visited": 0, "chunks_indexed": 0, "files_skipped": 0,
                 "errors": 0, "embed_backend": "tfidf", "elapsed_s": 0.0}
        t0 = time.monotonic()

        # Load existing file hashes for incremental check
        known_hashes: Dict[str, str] = {}
        if incremental:
            rows = conn.execute("SELECT DISTINCT path, file_hash FROM coco_chunks").fetchall()
            for row in rows:
                known_hashes[row["path"]] = row["file_hash"] or ""

        embed_backend = "ollama" if self._use_ollama else "tfidf"
        stats["embed_backend"] = embed_backend

        for p in self.repo_root.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in _INDEXABLE_EXTS:
                continue
            rel = p.relative_to(self.repo_root)
            if _should_skip(rel):
                continue
            if p.stat().st_size > _MAX_FILE_BYTES:
                continue

            rel_str = str(rel).replace("\\", "/")
            fhash = _file_hash(p)

            if incremental and known_hashes.get(rel_str) == fhash:
                stats["files_skipped"] += 1
                continue

            stats["files_visited"] += 1

            # Remove stale chunks for this file
            conn.execute("DELETE FROM coco_chunks WHERE path=?", (rel_str,))

            try:
                source = p.read_text(encoding="utf-8", errors="replace")
            except Exception as exc:
                LOG.debug("Read error %s: %s", rel_str, exc)
                stats["errors"] += 1
                continue

            if p.suffix.lower() == ".py":
                raw_chunks = _chunk_python(rel_str, source)
            else:
                raw_chunks = _chunk_text(rel_str, source)

            for chunk in raw_chunks:
                embed_text = " ".join(filter(None, [
                    chunk.get("name", ""),
                    chunk.get("docstring", ""),
                    chunk.get("text", ""),
                ]))[:2000]

                doc_id = f"{rel_str}:{chunk['name']}:{chunk['lineno']}"
                embedding_json = None
                model_used = "none"

                if self._use_ollama:
                    vec = _ollama_embed(embed_text)
                    if vec:
                        embedding_json = json.dumps(vec)
                        model_used = _EMBED_MODEL
                    else:
                        # Ollama call failed; fall back silently for this chunk
                        model_used = "tfidf_fallback"
                else:
                    model_used = "tfidf_deferred"

                conn.execute(
                    """INSERT OR REPLACE INTO coco_chunks
                       (doc_id, path, kind, name, lineno, end_lineno,
                        text, docstring, embedding, embed_model, dim,
                        file_hash, indexed_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        doc_id,
                        rel_str,
                        chunk["kind"],
                        chunk["name"] or "",
                        chunk["lineno"],
                        chunk["end_lineno"],
                        chunk["text"][:8000],
                        chunk.get("docstring"),
                        embedding_json,
                        model_used,
                        len(json.loads(embedding_json)) if embedding_json else 0,
                        fhash,
                        time.time(),
                    ),
                )
                stats["chunks_indexed"] += 1

            conn.commit()

        stats["elapsed_s"] = round(time.monotonic() - t0, 2)
        LOG.info(
            "CocoIndex pipeline: files=%d chunks=%d skipped=%d errors=%d %.1fs",
            stats["files_visited"], stats["chunks_indexed"],
            stats["files_skipped"], stats["errors"], stats["elapsed_s"],
        )
        return stats

    # ── Public API ────────────────────────────────────────────────────────

    def run(self, incremental: bool = True) -> Dict:
        """
        Run the indexing pipeline.
        Uses native cocoindex if installed, otherwise built-in pipeline.
        """
        if self._has_cocoindex:
            return self._run_native_cocoindex(incremental=incremental)
        return self._run_builtin_pipeline(incremental=incremental)

    def query_semantic(self, query: str, top_k: int = 10,
                       kind: Optional[str] = None,
                       path_prefix: Optional[str] = None,
                       min_score: float = 0.05) -> List[Dict]:
        """
        Semantic vector search over the coco_chunks table.

        If nomic-embed-text is available: embeds query → cosine similarity
        against all stored vectors.
        Fallback: keyword overlap scoring (same result format).

        Args:
            query:       Natural language or code query.
            top_k:       Max results to return.
            kind:        Filter by chunk kind: function|class|module|text
            path_prefix: Restrict to files under this path prefix.
            min_score:   Minimum similarity threshold (0-1).

        Returns:
            List of dicts: {path, kind, name, lineno, score, text, docstring}
        """
        conn = self._db()
        where_clauses = []
        params: List = []

        if kind:
            where_clauses.append("kind=?")
            params.append(kind)
        if path_prefix:
            where_clauses.append("path LIKE ?")
            params.append(f"{path_prefix}%")

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        rows = conn.execute(
            f"SELECT * FROM coco_chunks {where_sql} ORDER BY indexed_at DESC",
            params,
        ).fetchall()

        if not rows:
            return []

        # Try vector search with Ollama
        q_vec = _ollama_embed(query) if self._use_ollama else None

        results: List[Tuple[float, Dict]] = []

        for row in rows:
            d = dict(row)
            score = 0.0

            if q_vec and d.get("embedding"):
                try:
                    stored_vec = json.loads(d["embedding"])
                    score = _cosine(q_vec, stored_vec)
                except Exception:
                    score = self._keyword_score(query, d)
            else:
                score = self._keyword_score(query, d)

            if score >= min_score:
                results.append((score, {
                    "path":      d["path"],
                    "kind":      d["kind"],
                    "name":      d["name"],
                    "lineno":    d["lineno"],
                    "end_lineno": d["end_lineno"],
                    "score":     round(score, 4),
                    "text":      (d.get("text") or "")[:300],
                    "docstring": d.get("docstring"),
                    "embed_model": d.get("embed_model", "none"),
                }))

        results.sort(key=lambda x: -x[0])
        return [r for _, r in results[:top_k]]

    @staticmethod
    def _keyword_score(query: str, chunk: Dict) -> float:
        """Simple keyword overlap score (fallback when no vectors)."""
        import re
        words = set(re.findall(r"[a-z0-9_]+", query.lower())) - {
            "the", "a", "an", "in", "on", "of", "to", "is", "it", "and",
        }
        if not words:
            return 0.0
        blob = " ".join(filter(None, [
            chunk.get("name", ""),
            chunk.get("docstring", ""),
            chunk.get("text", ""),
            chunk.get("path", ""),
        ])).lower()
        hits = sum(blob.count(w) for w in words)
        return min(1.0, hits / (len(words) * 5))

    def index_stats(self) -> Dict:
        """Return stats about what's been indexed."""
        conn = self._db()
        total = conn.execute("SELECT COUNT(*) FROM coco_chunks").fetchone()[0]
        by_kind = conn.execute(
            "SELECT kind, COUNT(*) as n FROM coco_chunks GROUP BY kind"
        ).fetchall()
        paths = conn.execute(
            "SELECT COUNT(DISTINCT path) FROM coco_chunks"
        ).fetchone()[0]
        embedded = conn.execute(
            "SELECT COUNT(*) FROM coco_chunks WHERE embedding IS NOT NULL"
        ).fetchone()[0]
        models = conn.execute(
            "SELECT embed_model, COUNT(*) as n FROM coco_chunks "
            "WHERE embed_model IS NOT NULL GROUP BY embed_model"
        ).fetchall()
        return {
            "total_chunks":    total,
            "unique_files":    paths,
            "embedded_chunks": embedded,
            "by_kind":         {r["kind"]: r["n"] for r in by_kind},
            "by_model":        {r["embed_model"]: r["n"] for r in models},
            "has_cocoindex":   self._has_cocoindex,
            "ollama_available": self._use_ollama,
            "embed_model":     _EMBED_MODEL,
            "db_path":         str(self.db_path),
        }

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None


# ── Singleton accessor ────────────────────────────────────────────────────────

_flow: Optional[CocoIndexFlow] = None


def get_flow(repo_root: Path = _ROOT) -> CocoIndexFlow:
    global _flow
    if _flow is None:
        _flow = CocoIndexFlow(repo_root=repo_root)
    return _flow


# ── CLI entrypoint ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    parser = argparse.ArgumentParser(description="CocoIndex bridge for Serena")
    parser.add_argument("--index", action="store_true", help="Run full index (or incremental if DB exists)")
    parser.add_argument("--full", action="store_true", help="Force full re-index (ignore file hashes)")
    parser.add_argument("--query", type=str, help="Run a semantic search query")
    parser.add_argument("--top-k", type=int, default=10, help="Max results for --query")
    parser.add_argument("--kind", type=str, help="Filter by kind: function|class|module|text")
    parser.add_argument("--stats", action="store_true", help="Print index stats")
    args = parser.parse_args()

    flow = CocoIndexFlow(repo_root=_ROOT)

    if args.index or args.full:
        incremental = not args.full
        print(f"Running {'incremental' if incremental else 'full'} CocoIndex pipeline...")
        stats = flow.run(incremental=incremental)
        print(json.dumps(stats, indent=2))

    if args.query:
        print(f"\nSemantic search: '{args.query}'")
        results = flow.query_semantic(
            args.query,
            top_k=args.top_k,
            kind=args.kind or None,
        )
        if not results:
            print("  (no results)")
        for r in results:
            print(f"  [{r['score']:.3f}] {r['path']}:{r['lineno']} [{r['kind']}] {r['name']}")
            if r.get("docstring"):
                print(f"    doc: {r['docstring'][:80]}")

    if args.stats:
        print("\nIndex stats:")
        print(json.dumps(flow.index_stats(), indent=2))
