"""
Inference Server — unified async wrapper over llm_client.py.

Adds:
  - Per-call Msg⛛ logging: [ML⛛{inference}]
  - Latency tracking → model_registry.inference_log
  - Fallback chain: Ollama → Replit AI → stub
  - Streaming support (generator)

Msg⛛ protocol: [ML⛛{inference}], [ML⛛{embed}], [ML⛛{score}]

API:
  generate(prompt, task_type, model_id)  → str
  embed_text(text)                       → (list[float], str)
  score(text, labels)                    → dict[str, float]
  status()                               → dict
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Lazy imports — keep this module importable even if llm_client is absent
_llm_client = None
_registry = None
_embedder = None


def _get_llm():
    global _llm_client
    if _llm_client is None:
        try:
            import llm_client as _lc
            _llm_client = _lc.get_client()
        except Exception:
            pass
    return _llm_client


def chat(messages: list[dict], **kwargs) -> str:
    """Thin chat wrapper that keeps the game engine off llm_client."""
    llm = _get_llm()
    if not llm:
        raise RuntimeError("llm backend unavailable")
    return llm.chat(messages, **kwargs)


def _get_registry():
    global _registry
    if _registry is None:
        try:
            from services import model_registry as _mr
            _registry = _mr
        except Exception:
            pass
    return _registry


def _get_embedder():
    global _embedder
    if _embedder is None:
        try:
            from services import embedder as _em
            _embedder = _em
        except Exception:
            pass
    return _embedder


# ── Generate ──────────────────────────────────────────────────────────────────

def generate(
    prompt: str,
    task_type: str = "general",
    model_id: Optional[str] = None,
    max_tokens: int = 512,
    system: Optional[str] = None,
) -> str:
    """
    Generate text using the best available backend.
    Logs the call with [ML⛛{inference}] tag.
    """
    llm = _get_llm()
    t0 = time.time()
    result = "[ML⛛{inference}] No LLM backend available."
    backend = "stub"

    if llm:
        try:
            full_prompt = f"{system}\n\n{prompt}" if system else prompt
            result = llm.generate(full_prompt, max_tokens=max_tokens)
            backend = getattr(llm, "_backend_name", "llm_client")
        except Exception as e:
            result = f"[ML⛛{{inference}}] Error: {e}"

    latency_ms = (time.time() - t0) * 1000
    reg = _get_registry()
    if reg:
        used_model = model_id or "auto"
        reg.log_inference(
            model_id=used_model,
            task_type=task_type,
            prompt_len=len(prompt),
            response_len=len(result),
            latency_ms=latency_ms,
            backend=backend,
        )

    return result


# ── Embed ─────────────────────────────────────────────────────────────────────

def embed_text(text: str, doc_id: Optional[str] = None) -> Tuple[List[float], str]:
    em = _get_embedder()
    if em:
        return em.embed(text, doc_id=doc_id)
    return [], "unavailable"


# ── Score / classify ──────────────────────────────────────────────────────────

def score(text: str, labels: List[str]) -> Dict[str, float]:
    """
    Zero-shot classification using TF-IDF overlap with label names.
    No ML library needed.
    """
    from services.embedder import search
    results = search(text, labels, top_k=len(labels))
    total = sum(s for s, _ in results) or 1.0
    return {lbl: round(s / total, 4) for s, lbl in results}


# ── Status ────────────────────────────────────────────────────────────────────

def status() -> Dict:
    llm = _get_llm()
    em = _get_embedder()
    reg = _get_registry()

    llm_status = {}
    if llm:
        try:
            llm_status = llm.status()
        except Exception:
            llm_status = {"available": False}

    embed_status = {}
    if em:
        try:
            embed_status = em.embedding_stats()
        except Exception:
            pass

    reg_stats = {}
    if reg:
        try:
            reg_stats = reg.registry_stats()
        except Exception:
            pass

    return {
        "llm": llm_status,
        "embedder": embed_status,
        "registry": reg_stats,
        "msg_tag": "[ML⛛{status}]",
    }


def initialise() -> Dict:
    return status()
