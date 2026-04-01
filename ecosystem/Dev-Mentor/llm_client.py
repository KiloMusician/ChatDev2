"""
LLM Client — multi-backend LLM interface for DevMentor / Terminal Depths.

Backend priority (auto mode):
  1. Open Router            (feature-flagged resilient gateway — set USE_ROUTER=1)
  2. Replit AI Integration  (localhost proxy — zero-token, always available)
  3. Ollama                 (local model server, if running)
  4. OpenAI direct          (DISABLED by default — set ALLOW_OPENAI=1 to enable)
  5. Stub                   (deterministic fallback, no network)

Cost-safety rules:
  - Replit AI proxy (localhost:1106) is always preferred — zero token cost.
  - Open Router is opt-in via USE_ROUTER=1 or LLM_BACKEND=router.
  - OpenAI direct is DISABLED unless ALLOW_OPENAI=1 is set.
  - Set LLM_BACKEND=replit to hard-lock to Replit proxy.
  - LLM responses are cached in agent_memory.db (set LLM_CACHE=0 to disable).

Usage:
    from llm_client import LLMClient, get_client, generate
    llm = get_client()
    print(llm.generate("Write a haiku about hacking"))
    print(llm.status())
"""
from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional

import requests


# ── Replit AI Integration backend ─────────────────────────────────────────────

class ReplitAIBackend:
    """
    Uses Replit's built-in OpenAI proxy (AI_INTEGRATIONS_OPENAI_*).
    Zero-token, always available when the integration is installed.
    """

    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(self, model: str | None = None):
        self.model = model or os.environ.get("REPLIT_AI_MODEL", self.DEFAULT_MODEL)
        self._base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL", "")
        self._api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY", "")
        self._client = None

    def _get_client(self):
        if self._client is None and self._base_url and self._api_key:
            from openai import OpenAI
            self._client = OpenAI(base_url=self._base_url, api_key=self._api_key)
        return self._client

    def available(self) -> bool:
        return bool(self._base_url and self._api_key and self._get_client() is not None)

    def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system: str | None = None,
        model: str | None = None,
    ) -> str:
        client = self._get_client()
        if not client:
            raise RuntimeError("Replit AI backend unavailable")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content.strip()

    def chat(
        self,
        messages: list[dict],
        *,
        max_tokens: int = 500,
        temperature: float = 0.7,
        model: str | None = None,
    ) -> str:
        client = self._get_client()
        if not client:
            raise RuntimeError("Replit AI backend unavailable")
        resp = client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content.strip()


# ── Ollama backend ────────────────────────────────────────────────────────────

class OllamaBackend:
    """REST client for a locally running Ollama server.

    Recommended models (vision + tool use — see docs/temple/models/):
      qwen3-vl:8b       — best daily driver (vision+tools, 256K ctx, ~5GB VRAM)
      qwen2.5vl:7b      — proven alternative (same family as qwen2.5-coder:14b)
      qwen3-vl:32b      — highest quality (20GB VRAM)
      minicpm-v         — OCR/document specialist (no strict tool schema)
    Set OLLAMA_MODEL env var or pass model= to constructor to override.
    """

    BASE_URL = "http://localhost:11434"
    # qwen3-vl:8b: vision + tool calling confirmed, 256K context, ~5GB VRAM
    # Fallback to smollm2:360m if neither is pulled (zero-VRAM stub)
    DEFAULT_MODEL = "qwen3-vl:8b"

    def __init__(self, model: str | None = None):
        self.model = model or os.environ.get("OLLAMA_MODEL", self.DEFAULT_MODEL)
        self.base_url = os.environ.get("OLLAMA_HOST", os.environ.get("OLLAMA_ENDPOINT", self.BASE_URL)).rstrip("/")

    def _ping(self) -> bool:
        try:
            return requests.get(f"{self.base_url}/api/tags", timeout=2).status_code == 200
        except Exception:
            return False

    def available(self) -> bool:
        return self._ping()

    def models(self) -> list[str]:
        try:
            return [m["name"] for m in requests.get(f"{self.base_url}/api/tags", timeout=3).json().get("models", [])]
        except Exception:
            return []

    def ensure_model(self, model: str | None = None) -> bool:
        target = model or self.model
        if target in self.models():
            return True
        try:
            result = subprocess.run(["ollama", "pull", target], capture_output=True, timeout=300)
            return result.returncode == 0
        except Exception:
            return False

    def generate(self, prompt: str, *, max_tokens: int = 500, temperature: float = 0.7,
                 system: str | None = None, model: str | None = None) -> str:
        payload: dict = {
            "model": model or self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": temperature},
        }
        if system:
            payload["system"] = system
        r = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=120)
        r.raise_for_status()
        return r.json()["response"].strip()

    def chat(self, messages: list[dict], *, max_tokens: int = 500, temperature: float = 0.7,
             model: str | None = None) -> str:
        r = requests.post(
            f"{self.base_url}/api/chat",
            json={"model": model or self.model, "messages": messages, "stream": False,
                  "options": {"num_predict": max_tokens, "temperature": temperature}},
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["message"]["content"].strip()


# ── LM Studio backend (OpenAI-compatible local API) ───────────────────────────

class LMStudioBackend:
    """
    LM Studio local server — OpenAI-compatible API, no auth required.
    Default endpoint: http://localhost:1234/v1
    Override with LMSTUDIO_HOST env var (include scheme, no /v1 suffix).
    """

    DEFAULT_MODEL = "openai/gpt-oss-20b"

    def __init__(self, model: str | None = None):
        self.model = model or os.environ.get("LMSTUDIO_MODEL", self.DEFAULT_MODEL)
        self._base = os.environ.get("LMSTUDIO_HOST", "http://localhost:1234").rstrip("/")
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(base_url=f"{self._base}/v1", api_key="lm-studio")
            except Exception:
                pass
        return self._client

    def available(self) -> bool:
        import urllib.request
        try:
            with urllib.request.urlopen(f"{self._base}/v1/models", timeout=1) as r:
                return r.status == 200
        except Exception:
            return False

    def generate(self, prompt: str, *, max_tokens: int = 500, temperature: float = 0.7,
                 system: str | None = None, model: str | None = None) -> str:
        msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        resp = self._get_client().chat.completions.create(
            model=model or self.model, messages=msgs, max_tokens=max_tokens, temperature=temperature)
        return resp.choices[0].message.content.strip()

    def chat(self, messages: list[dict], *, max_tokens: int = 500, temperature: float = 0.7,
             model: str | None = None) -> str:
        resp = self._get_client().chat.completions.create(
            model=model or self.model, messages=messages, max_tokens=max_tokens, temperature=temperature)
        return resp.choices[0].message.content.strip()


# ── OpenAI direct backend ─────────────────────────────────────────────────────

class OpenAIBackend:
    """
    Direct OpenAI API using OPENAI_API_KEY env var.
    DISABLED by default — set ALLOW_OPENAI=1 to re-enable.
    Prefer the Replit AI proxy (ReplitAIBackend) which is free.
    """

    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(self, model: str | None = None):
        self.model = model or self.DEFAULT_MODEL
        self._client = None

    def _get_client(self):
        if self._client is None and os.environ.get("OPENAI_API_KEY"):
            from openai import OpenAI
            self._client = OpenAI()
        return self._client

    def available(self) -> bool:
        # Hard-disabled unless explicitly opted in — avoid surprise costs
        if not os.environ.get("ALLOW_OPENAI"):
            return False
        return bool(os.environ.get("OPENAI_API_KEY")) and self._get_client() is not None

    def generate(self, prompt: str, *, max_tokens: int = 500, temperature: float = 0.7,
                 system: str | None = None, model: str | None = None) -> str:
        messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        resp = self._get_client().chat.completions.create(
            model=model or self.model, messages=messages, max_tokens=max_tokens, temperature=temperature)
        return resp.choices[0].message.content.strip()


class RouterBackend:
    """
    Feature-flagged gateway backend that routes LLM calls through the local
    Open Router service for retries, fallbacks, rate limiting, and metrics.
    """

    DEFAULT_URL = "http://localhost:9001"

    def __init__(self, model: str | None = None):
        self.model = model
        self.base_url = os.environ.get(
            "MODEL_ROUTER_URL",
            os.environ.get("GORDON_MODEL_ROUTER", self.DEFAULT_URL),
        ).rstrip("/")

    @staticmethod
    def _enabled() -> bool:
        if os.environ.get("LLM_BACKEND", "").lower() == "router":
            return True
        return os.environ.get("USE_ROUTER", "0").lower() in {"1", "true", "yes", "on"}

    def available(self) -> bool:
        if not self._enabled():
            return False
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def _request(self, payload: dict) -> str:
        response = requests.post(
            f"{self.base_url}/route/llm",
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        body = response.json()
        return str(body.get("output", "")).strip()

    def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system: str | None = None,
        model: str | None = None,
    ) -> str:
        return self._request(
            {
                "action": "generate",
                "prompt": prompt,
                "system": system,
                "model": model or self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
        )

    def chat(
        self,
        messages: list[dict],
        *,
        max_tokens: int = 500,
        temperature: float = 0.7,
        model: str | None = None,
    ) -> str:
        return self._request(
            {
                "action": "chat",
                "messages": messages,
                "model": model or self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
        )

    def chat(self, messages: list[dict], *, max_tokens: int = 500, temperature: float = 0.7,
             model: str | None = None) -> str:
        resp = self._get_client().chat.completions.create(
            model=model or self.model, messages=messages, max_tokens=max_tokens, temperature=temperature)
        return resp.choices[0].message.content.strip()


# ── Stub backend ──────────────────────────────────────────────────────────────

class StubBackend:
    """
    Deterministic no-network fallback — zero cost, zero latency.
    Loads pre-written content from stubs/*.json when available.
    """

    _challenges: list | None = None
    _lore: list | None = None
    _npc: dict | None = None

    def _load_stubs(self) -> None:
        stub_dir = Path(__file__).parent / "stubs"
        if self._challenges is None:
            try:
                self._challenges = json.loads((stub_dir / "challenges.json").read_text())
            except Exception:
                self._challenges = []
        if self._lore is None:
            try:
                self._lore = json.loads((stub_dir / "lore.json").read_text())
            except Exception:
                self._lore = []
        if self._npc is None:
            try:
                self._npc = json.loads((stub_dir / "npc.json").read_text())
            except Exception:
                self._npc = {}

    def available(self) -> bool:
        return True

    def generate(self, prompt: str, **kwargs) -> str:
        self._load_stubs()
        import random
        p = prompt.lower()
        if "challenge" in p and self._challenges:
            return json.dumps(random.choice(self._challenges))
        if ("lore" in p or "story" in p or "log" in p or "email" in p) and self._lore:
            return random.choice(self._lore)["content"]
        if any(name in p for name in ("nova", "ada", "watcher")) and self._npc:
            for name, lines in self._npc.items():
                if name in p:
                    return random.choice(lines)
        if "test" in p:
            return "def test_stub():\n    assert True"
        if "fix" in p or "debug" in p:
            return "Check imports and variable names first."
        if "doc" in p or "document" in p:
            return "## Module\nThis module provides core functionality. See source for details."
        return f"[stub] {prompt[:80]}"

    def chat(self, messages: list[dict], **kwargs) -> str:
        return self.generate(messages[-1].get("content", "") if messages else "")


# ── Main LLMClient ────────────────────────────────────────────────────────────

# ── Cost log & circuit breaker ────────────────────────────────────────────────

import csv
from datetime import date

_COST_LOG_PATH = Path("cost_log.csv")
_CIRCUIT_BREAKER_DAILY_LIMIT = int(os.environ.get("LLM_DAILY_LIMIT", "2000"))
_cost_today: dict = {"date": "", "count": 0}
_cost_lock = threading.Lock()


def _cost_log(backend: str, prompt_len: int, response_len: int) -> bool:
    """
    Record one LLM call. Increments daily counter, writes CSV row.
    Returns True if still under limit, False if circuit breaker tripped.
    """
    global _cost_today
    today = str(date.today())
    with _cost_lock:
        if _cost_today["date"] != today:
            _cost_today = {"date": today, "count": 0}
        _cost_today["count"] += 1
        count = _cost_today["count"]
        write_header = not _COST_LOG_PATH.exists()
        try:
            with open(_COST_LOG_PATH, "a", newline="") as f:
                w = csv.writer(f)
                if write_header:
                    w.writerow(["timestamp", "backend", "prompt_chars", "response_chars", "daily_count"])
                w.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), backend, prompt_len, response_len, count])
        except Exception:
            pass
        return count <= _CIRCUIT_BREAKER_DAILY_LIMIT


def _check_limit() -> bool:
    """Check if we're under the daily limit WITHOUT incrementing the counter."""
    today = str(date.today())
    with _cost_lock:
        if _cost_today.get("date") != today:
            return True
        return _cost_today["count"] < _CIRCUIT_BREAKER_DAILY_LIMIT


def get_daily_llm_count() -> int:
    today = str(date.today())
    if _cost_today.get("date") == today:
        return _cost_today["count"]
    return 0


BACKEND_PRIORITY = ["router", "replit", "ollama", "lmstudio", "openai", "stub"]


class LLMClient:
    """
    Unified LLM interface — picks the best available backend automatically.

    Force a backend with LLM_BACKEND env var:
        router | replit | ollama | lmstudio | openai | stub
    """

    def __init__(self, model: str | None = None, backend: str = "auto"):
        self._backends: dict = {
            "router": RouterBackend(model),
            "replit": ReplitAIBackend(model),
            "ollama": OllamaBackend(model),
            "lmstudio": LMStudioBackend(model),
            "openai": OpenAIBackend(model),
            "stub": StubBackend(),
        }
        forced = os.environ.get("LLM_BACKEND", backend).lower()
        if forced != "auto" and forced in self._backends:
            self._active = forced
        else:
            self._active = next(
                (name for name in BACKEND_PRIORITY if self._backends[name].available()),
                "stub",
            )

    @property
    def backend_name(self) -> str:
        return self._active

    @property
    def _backend(self):
        return self._backends[self._active]

    def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system: str | None = None,
        model: str | None = None,
        cache: bool | None = None,
    ) -> str:
        """Generate a completion. Checks LLM cache first; falls back to stub on error."""
        use_cache = (os.environ.get("LLM_CACHE", "1") != "0") if cache is None else cache
        cache_prefix = system or ""

        # ── Cache lookup ──────────────────────────────────────────────────────
        if use_cache and temperature <= 0.5:
            try:
                from memory import get_memory
                mem = get_memory()
                cached = mem.cache_get(prompt, prefix=cache_prefix)
                if cached:
                    return cached
            except Exception:
                pass

        # ── Circuit breaker — trip to stub if daily limit exceeded ────────────
        if not _check_limit():
            return (
                f"[circuit-breaker] Daily LLM limit ({_CIRCUIT_BREAKER_DAILY_LIMIT}) reached. "
                "Reset at midnight or raise LLM_DAILY_LIMIT env var."
            )

        # ── Generation ────────────────────────────────────────────────────────
        try:
            response = self._backend.generate(
                prompt, max_tokens=max_tokens, temperature=temperature,
                system=system, model=model,
            )
        except Exception:
            response = self._backends["stub"].generate(prompt)

        # Log the call (increments counter + writes CSV)
        _cost_log(self._active, len(prompt), len(response))

        # ── Cache store (only deterministic / low-temp calls) ─────────────────
        if use_cache and temperature <= 0.5 and response:
            try:
                from memory import get_memory
                get_memory().cache_put(prompt, response, backend=self._active, prefix=cache_prefix)
            except Exception:
                pass

        return response

    def chat(self, messages: list[dict], *, max_tokens: int = 500, temperature: float = 0.7,
             model: str | None = None, system: str | None = None) -> str:
        """Chat-completion interface. system= prepends a system message if provided."""
        if system:
            has_sys = any(m.get("role") == "system" for m in messages)
            if not has_sys:
                messages = [{"role": "system", "content": system}] + list(messages)
        try:
            return self._backend.chat(messages, max_tokens=max_tokens,
                                      temperature=temperature, model=model)
        except Exception:
            return self._backends["stub"].chat(messages)

    def status(self) -> dict:
        router_b: RouterBackend = self._backends["router"]
        replit_b: ReplitAIBackend = self._backends["replit"]
        ollama_b: OllamaBackend = self._backends["ollama"]
        daily = get_daily_llm_count()
        return {
            "active_backend": self._active,
            "router": router_b.available(),
            "model_router_url": router_b.base_url,
            "replit_ai": replit_b.available(),
            "ollama": ollama_b.available(),
            "ollama_models": ollama_b.models() if ollama_b.available() else [],
            "openai_direct": self._backends["openai"].available(),
            "daily_calls": daily,
            "daily_limit": _CIRCUIT_BREAKER_DAILY_LIMIT,
            "circuit_breaker_ok": daily < _CIRCUIT_BREAKER_DAILY_LIMIT,
        }


# ── Prompts library ───────────────────────────────────────────────────────────

class Prompts:
    """Reusable prompt templates for DevMentor / Terminal Depths tasks."""

    SYSTEM_GAME = (
        "You are the AI Game Master of Terminal Depths — a cyberpunk terminal RPG. "
        "Respond as the game world: dramatic, terse, hacker-aesthetic. "
        "Keep responses under 150 words unless generating code or JSON."
    )
    SYSTEM_DEV = (
        "You are DevMentor's code generation assistant. "
        "Output only valid Python code or JSON unless asked for explanation. "
        "Follow the existing codebase style: type hints, List[dict] returns, _line/_sys/_err helpers."
    )

    @staticmethod
    def npc_response(npc_name: str, personality: str, player_input: str) -> str:
        return (
            f"NPC '{npc_name}' ({personality}) responds to: '{player_input}'\n"
            f"Reply in character, 1-3 sentences, cyberpunk tone."
        )

    @staticmethod
    def generate_challenge(category: str, difficulty: str) -> str:
        return (
            f"Generate a cybersecurity challenge for a hacking terminal game.\n"
            f"Category: {category}\nDifficulty: {difficulty}\n"
            f"Return ONLY valid JSON with keys: title, description, solution, hint, xp (integer)."
        )

    @staticmethod
    def generate_lore(node_name: str, context: str = "") -> str:
        return (
            f"Write a short lore fragment (log file, email, or note) for node '{node_name}' "
            f"in a cyberpunk world where corporations run surveillance on citizens. "
            f"Context: {context or 'NexusCorp Node-7, CHIMERA surveillance system'}. "
            f"50-100 words."
        )

    @staticmethod
    def debug_error(traceback: str, code: str) -> str:
        return f"Error:\n{traceback}\n\nCode:\n{code}\n\nBrief diagnosis and fix (1-2 sentences):"

    @staticmethod
    def generate_command_handler(command_name: str, flags: str, description: str) -> str:
        return (
            f"Write a Python method `_cmd_{command_name}(self, args: List[str]) -> List[dict]` "
            f"for a virtual Linux terminal in a hacking game.\n"
            f"Description: {description}\nFlags: {flags}\n"
            f"Use these helpers: _line(text, color=None), _sys(text), _err(text), _ok(text), _dim(text).\n"
            f"Return realistic output. Handle missing args gracefully."
        )

    @staticmethod
    def devlog_priorities(devlog: str) -> str:
        return (
            f"Based on this development log, list the top 3 highest-priority next tasks.\n"
            f"Be specific and actionable. Format as numbered list.\n\n{devlog[-3000:]}"
        )


# ── Module-level singleton ────────────────────────────────────────────────────

_default: LLMClient | None = None
_lock = threading.Lock()


def get_client(model: str | None = None, backend: str = "auto") -> LLMClient:
    """Return the process-level singleton LLMClient."""
    global _default
    with _lock:
        if _default is None:
            _default = LLMClient(model=model, backend=backend)
    return _default


def generate(prompt: str, **kwargs) -> str:
    return get_client().generate(prompt, **kwargs)


def chat(messages: list[dict], **kwargs) -> str:
    return get_client().chat(messages, **kwargs)


def status() -> dict:
    return get_client().status()


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Hello from Terminal Depths. Who are you?"
    llm = LLMClient()
    st = llm.status()
    print(f"[LLM] backend={st['active_backend']} replit={st['replit_ai']} ollama={st['ollama']}")
    print()
    print(llm.generate(prompt, system=Prompts.SYSTEM_GAME))
