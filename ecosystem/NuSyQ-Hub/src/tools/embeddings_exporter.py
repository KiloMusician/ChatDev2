"""Embeddings exporter for lattices.

Supports Ollama-first embedding; in dry-run mode it writes placeholder vectors.
"""

from __future__ import annotations

import http.client
import json
import os
import pathlib
import time
from typing import Any
from urllib.parse import urlparse

try:
    from config.service_config import ServiceConfig
except ImportError:  # pragma: no cover - allow lightweight usage
    ServiceConfig = None


def _ollama_embed(texts: list[str], model: str) -> list[list[float]]:
    """Call a local Ollama embedding endpoint.

    Uses the configured Ollama HTTP endpoint (ServiceConfig/env). Model name is
    the Ollama model id (e.g. 'nomic-embed-text'). Returns list of vectors.
    """
    if ServiceConfig:
        ollama_url = ServiceConfig.get_ollama_url()
    else:
        env_base = os.environ.get("OLLAMA_BASE_URL")
        if env_base:
            ollama_url = env_base
        else:
            host_default = os.environ.get("OLLAMA_HOST", "http://127.0.0.1")
            port_default = os.environ.get("OLLAMA_PORT", "11434")
            ollama_url = f"{host_default}:{port_default}"
    parsed = urlparse(ollama_url if "://" in ollama_url else f"http://{ollama_url}")
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 11434

    conn = http.client.HTTPConnection(host, port, timeout=60)
    payload = json.dumps({"model": model, "input": texts})
    conn.request("POST", "/api/embeddings", payload, {"Content-Type": "application/json"})
    resp = conn.getresponse()
    body = resp.read().decode("utf-8", errors="ignore")
    conn.close()
    if resp.status != 200:
        msg = f"Ollama returned {resp.status}: {body}"
        raise RuntimeError(msg)

    try:
        data = json.loads(body)
    except (json.JSONDecodeError, ValueError, OSError) as parse_error:
        msg = f"Failed to parse Ollama response as JSON: {body!r}"
        raise RuntimeError(msg) from parse_error

    # normalize/validate response formats
    out: list[list[float] | None] = []

    def extract_embedding(candidate) -> list[float] | None:
        # candidate may be a dict {"embedding": [...]}, or a bare list
        if isinstance(candidate, dict):
            emb = candidate.get("embedding") or candidate.get("embeddings")
            # some providers return {"embeddings": [..]} per-item
            if (
                isinstance(emb, list)
                and emb
                and all(
                    isinstance(x, (int, float))
                    for x in (
                        emb
                        if isinstance(emb[0], (int, float))
                        else emb[0] if isinstance(emb[0], list) else []
                    )
                )
            ):
                # emb appears to be a list of numbers (single) or list-of-lists
                if emb and isinstance(emb[0], (int, float)):
                    return list(map(float, emb))
                # if embedding stored as first element in a list-of-lists
                if emb and isinstance(emb[0], list):
                    return list(map(float, emb[0]))
            # fallback: explicit 'embedding' key
            if "embedding" in candidate and isinstance(candidate["embedding"], list):
                if candidate["embedding"]:
                    return [float(x) for x in candidate["embedding"]]
                return None
        elif isinstance(candidate, list):
            # candidate is directly an embedding vector
            if candidate and all(isinstance(x, (int, float)) for x in candidate):
                return [float(x) for x in candidate]
        return None

    if isinstance(data, dict):
        # common shapes: {"embedding": [...] } or {"embeddings": [{...}, ...]}
        if "embeddings" in data and isinstance(data["embeddings"], list):
            for itm in data["embeddings"]:
                out.append(extract_embedding(itm))
        elif "embedding" in data:
            out.append(extract_embedding({"embedding": data.get("embedding")}))
        # sometimes the payload is wrapped in a results list
        elif "results" in data and isinstance(data["results"], list):
            for itm in data["results"]:
                out.append(extract_embedding(itm))
    elif isinstance(data, list):
        for itm in data:
            out.append(extract_embedding(itm))

    # ensure we have clean non-empty vectors
    cleaned: list[list[float]] = []
    for i, v in enumerate(out):
        if v is None or not isinstance(v, list) or len(v) == 0:
            msg = f"Ollama returned empty or invalid embedding for batch index {i}: {data!r}"
            raise RuntimeError(
                msg,
            )
        cleaned.append(v)

    if not cleaned:
        msg = f"Unexpected Ollama embeddings response (no vectors): {data!r}"
        raise RuntimeError(msg)

    return cleaned


def _local_embed(texts: list[str]) -> list[list[float]]:
    """Fallback local embedding using sentence-transformers (all-MiniLM-L6-v2).

    This does a lazy import so the package is only required when the fallback is used.
    Returns list of vectors as lists of floats.
    """
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        msg = "Local fallback requires sentence-transformers. Install with: pip install sentence-transformers"
        raise RuntimeError(msg) from e

    model = SentenceTransformer("all-MiniLM-L6-v2")
    embs = model.encode(texts, show_progress_bar=False)
    # convert numpy arrays to lists
    out: list[Any] = []
    if hasattr(embs, "tolist"):
        # single array or 2D array
        try:
            out = np.asarray(embs).tolist()
        except (AttributeError, ValueError):
            out = [list(map(float, list(x))) for x in embs]
    else:
        out = [list(map(float, list(x))) for x in embs]
    return out


def parse_model_spec(spec: str) -> tuple[str | None, str]:
    """Parse a model spec string into (provider, model_name).

    Examples:
      - "ollama:nomic-embed-text"
      - "ollama:nomic-embed-text:latest"
      - "sentence-transformers:all-MiniLM-L6-v2"
      - "nomic-embed-text:latest" (no provider -> treated as ollama provider)

    Returns (provider, rest) where provider is normalized (e.g. "ollama", "sentence-transformers")
    or None when no explicit provider was given. The rest preserves any additional colons.

    """
    if ":" not in spec:
        return None, spec
    scheme, rest = spec.split(":", 1)
    aliases = {
        "ollama": "ollama",
        "st": "sentence-transformers",
        "sentence-transformers": "sentence-transformers",
        "hf": "huggingface",
        "local": "local",
    }
    provider = aliases.get(scheme.lower(), scheme.lower())
    return provider, rest


def _validate_vectors(vecs: list[list[float]], metas: list[dict]) -> None:
    """Ensure vectors are non-empty lists of numbers. Raise RuntimeError on bad items."""
    if not isinstance(vecs, list) or not vecs:
        msg = "Embedding provider returned no vectors for the batch"
        raise RuntimeError(msg)
    for i, v in enumerate(vecs):
        meta = metas[i] if i < len(metas) else {}
        item_id = meta.get("id") or meta.get("file") or f"idx:{i}"
        if not isinstance(v, list) or len(v) == 0:
            msg = f"Embedding provider returned empty vector for item {item_id}"
            raise RuntimeError(msg)
        # basic element type check
        ok = all(isinstance(x, (int, float)) for x in v)
        if not ok:
            msg = f"Embedding provider returned non-numeric vector elements for item {item_id}"
            raise RuntimeError(
                msg,
            )


def embed_lattice(
    lattice: str,
    out: str,
    *,
    dry_run: bool = False,
    model: str = "nomic-embed-text",
    rate_limit: float = 8.0,
) -> None:
    p = pathlib.Path(lattice)
    if not p.exists():
        msg = f"Lattice not found: {p}"
        raise FileNotFoundError(msg)

    L = json.loads(p.read_text(encoding="utf-8"))
    nodes = L.get("nodes") if isinstance(L, dict) else L
    if nodes is None:
        msg = "Could not find nodes in lattice"
        raise RuntimeError(msg)

    outp = pathlib.Path(out)
    outp.parent.mkdir(parents=True, exist_ok=True)

    batch_size = 8
    dim = None
    provider, model_name = parse_model_spec(model)
    # treat no explicit provider as Ollama for backward compatibility
    if provider is None:
        provider = "ollama"

    with outp.open("w", encoding="utf-8") as fh:
        batch_texts: list[Any] = []
        batch_meta: list[Any] = []
        for n in nodes:
            title = n.get("title") or n.get("id")
            desc = n.get("desc") or n.get("summary") or ""
            file = n.get("file") or n.get("path") or ""
            text = " | ".join([x for x in (title, desc, file) if x])
            # truncate to a safe size for embedding models
            text = text[:4096]
            batch_texts.append(text)
            batch_meta.append({"id": n.get("id"), "file": file})

            if len(batch_texts) >= batch_size:
                if dry_run:
                    # placeholder zero vectors; choose 384 as a reasonable default
                    vecs = [[0.0] * 384 for _ in batch_texts]
                # choose embedding provider
                elif provider == "ollama":
                    try:
                        vecs = _ollama_embed(batch_texts, model_name)
                        # validate results
                        _validate_vectors(vecs, batch_meta)
                    except (ConnectionError, TimeoutError, OSError, ValueError):
                        vecs = _local_embed(batch_texts)
                elif provider in ("sentence-transformers", "st", "local"):
                    vecs = _local_embed(batch_texts)
                else:
                    # unknown provider: try Ollama then fallback
                    try:
                        vecs = _ollama_embed(batch_texts, model_name)
                    except (ConnectionError, TimeoutError, OSError, ValueError):
                        vecs = _local_embed(batch_texts)
                # validate and infer dim
                _validate_vectors(vecs, batch_meta)
                if vecs:
                    dim = len(vecs[0])
                for meta, vec in zip(batch_meta, vecs, strict=False):
                    fh.write(json.dumps({"meta": meta, "embedding": vec}) + "\n")
                batch_texts: list[Any] = []
                batch_meta: list[Any] = []
                time.sleep(max(0.0, 1.0 / rate_limit))

        # flush remaining
        if batch_texts:
            if dry_run:
                vecs = [[0.0] * (dim or 384) for _ in batch_texts]
            elif provider == "ollama":
                try:
                    vecs = _ollama_embed(batch_texts, model_name)
                    _validate_vectors(vecs, batch_meta)
                except (ConnectionError, TimeoutError, OSError, ValueError):
                    vecs = _local_embed(batch_texts)
            elif provider in ("sentence-transformers", "st", "local"):
                vecs = _local_embed(batch_texts)
            else:
                try:
                    vecs = _ollama_embed(batch_texts, model_name)
                except (ConnectionError, TimeoutError, OSError, ValueError):
                    vecs = _local_embed(batch_texts)
            for meta, vec in zip(batch_meta, vecs, strict=False):
                fh.write(json.dumps({"meta": meta, "embedding": vec}) + "\n")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser("embeddings_exporter")
    ap.add_argument("--lattice", default="lattices/vibe.json")
    ap.add_argument("--out", default="lattices/vibe.embeddings.jsonl")
    ap.add_argument("--model", default="ollama:nomic-embed-text")
    ap.add_argument("--rate-limit", type=float, default=8.0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    embed_lattice(
        lattice=args.lattice,
        out=args.out,
        dry_run=args.dry_run,
        model=args.model,
        rate_limit=args.rate_limit,
    )
