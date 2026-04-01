"""MJOLNIR Protocol Engine — Unified Agent Dispatch.

Core coordination layer wrapping AgentTaskRouter, GuildBoard, and SNS-Core.
ALL routing goes through AgentTaskRouter.route_task() — MJOLNIR adds:
  1. Context-aware mode detection (ecosystem/project/game)
  2. Multi-agent patterns (council, parallel, chain, delegate)
  3. Structured JSON response envelope
  4. Per-request SNS-Core toggle
  5. Best-effort Guild Board quest tracking

Usage:
    protocol = MjolnirProtocol()
    result = await protocol.ask("ollama", "Analyze this function", context_file="src/main.py")
    result = await protocol.council("Best approach?", agents=["ollama", "lmstudio"])
    result = await protocol.status(probes=True)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, ClassVar

from src.dispatch.agent_registry import AGENT_PROBES, AgentAvailabilityRegistry
from src.dispatch.context_detector import ContextDetector, ContextMode
from src.dispatch.response_envelope import ResponseEnvelope

logger = logging.getLogger(__name__)

# ── Agent alias mapping ──────────────────────────────────────────────────────
# User-friendly names → canonical names used by AgentTaskRouter

AGENT_ALIASES: dict[str, str] = {
    # Passthroughs
    "ollama": "ollama",
    "lmstudio": "lmstudio",
    "chatdev": "chatdev",
    "copilot": "copilot",
    "codex": "codex",
    "claude_cli": "claude_cli",
    "consciousness": "consciousness",
    "quantum_resolver": "quantum_resolver",
    "factory": "factory",
    "intermediary": "intermediary",
    "openclaw": "openclaw",
    "skyclaw": "skyclaw",
    # Shortcuts
    "lms": "lmstudio",
    "claude": "claude_cli",
    "sv": "consciousness",
    "quantum": "quantum_resolver",
    "qr": "quantum_resolver",
    "ai": "intermediary",  # short alias: --agent=ai routes to AIIntermediary
    "bridge": "intermediary",  # semantic alias for cognitive bridging
    "claw": "openclaw",  # short alias for OpenClaw gateway (TypeScript)
    "oc": "openclaw",  # even shorter
    "sky": "skyclaw",  # short alias for SkyClaw sidecar (Rust)
    "sc": "skyclaw",  # even shorter
    # Neural ML
    "neural_ml": "neural_ml",
    "ml": "neural_ml",  # short alias for ML system
    "neural": "neural_ml",  # semantic alias for neural network dispatch
    "nn": "neural_ml",  # even shorter
    # Continuous Optimizer
    "optimizer": "optimizer",
    "opt": "optimizer",  # short alias
    "continuous_optimizer": "optimizer",  # full name alias
    # Hermes-Agent (OpenRouter autonomous CLI)
    "hermes": "hermes",
    "hermes_agent": "hermes",
    "hermes_cli": "hermes",
    "openrouter": "hermes",  # provider-alias for OpenRouter-backed agent
    # MetaClaw observability + trace agent
    "metaclaw": "metaclaw",
    "trace_agent": "metaclaw",
    "observability": "metaclaw",
    # Auto
    "auto": "auto",
}

# Task-type inference from prompt keywords
_TASK_TYPE_KEYWORDS: list[tuple[str, list[str]]] = [
    ("review", ["review", "code review", "critique", "inspect"]),
    ("debug", ["debug", "fix", "error", "bug", "issue", "problem"]),
    ("analyze", ["analyze", "analysis", "examine", "assess", "evaluate", "audit"]),
    ("generate", ["generate", "create", "write", "build", "implement", "scaffold"]),
    ("plan", ["plan", "design", "architect", "strategy", "roadmap"]),
    ("test", ["test", "verify", "validate", "check"]),
    ("document", ["document", "docs", "explain", "describe"]),
    ("refactor", ["refactor", "restructure", "reorganize", "clean up"]),
    ("optimize", ["optimize", "performance", "speed up", "improve"]),
]


def _infer_task_type(prompt: str) -> str:
    """Infer task type from prompt keywords. Defaults to 'analyze'."""
    lower = prompt.lower()
    for task_type, keywords in _TASK_TYPE_KEYWORDS:
        if any(kw in lower for kw in keywords):
            return task_type
    return "analyze"


class MjolnirProtocol:
    """Unified agent dispatch protocol.

    Wraps AgentTaskRouter with context detection, multi-agent patterns,
    structured responses, and guild board coordination.
    """

    def __init__(self, repo_root: Path | None = None) -> None:
        """Initialize MjolnirProtocol with repo_root."""
        self._repo_root = repo_root
        self._context = ContextDetector()
        self._registry = AgentAvailabilityRegistry()
        self._profile_config_cache: dict[str, Any] | None = None
        self._profile_config_cache_key: str | None = None

        # Lazy-initialized heavy dependencies
        self._router = None
        self._guild = None
        self._sns_helper_loaded = False
        self._sns_convert = None
        self._intermediary = None
        self._intermediary_loaded = False
        self._memory: Any | None = None  # MemoryPalace — lazy-init on first ask()

    def _get_router(self):
        """Lazy-init AgentTaskRouter (avoids import-time overhead)."""
        if self._router is None:
            try:
                from src.tools.agent_task_router import AgentTaskRouter

                self._router = AgentTaskRouter(repo_root=self._repo_root)
            except ImportError as exc:
                logger.error("Failed to import AgentTaskRouter: %s", exc)
                raise RuntimeError(
                    "AgentTaskRouter not available. Ensure src/tools/agent_task_router.py exists."
                ) from exc
        return self._router

    def _get_guild(self):
        """Lazy-init GuildBoard (best-effort — returns None if unavailable)."""
        if self._guild is None:
            try:
                from src.guild.guild_board import GuildBoard

                self._guild = GuildBoard()
            except (ImportError, Exception) as exc:
                logger.debug("GuildBoard not available (optional): %s", exc)
                self._guild = False  # Sentinel: tried and failed
        return self._guild if self._guild is not False else None

    def _get_intermediary(self):
        """Lazy-init AIIntermediary (best-effort — returns None if unavailable)."""
        if not self._intermediary_loaded:
            self._intermediary_loaded = True
            try:
                from src.ai.ai_intermediary import AIIntermediary
                from src.ai.ollama_hub import OllamaHub

                hub = OllamaHub()
                self._intermediary = AIIntermediary(hub)
            except (ImportError, Exception) as exc:
                logger.debug("AIIntermediary not available (optional): %s", exc)
        return self._intermediary

    def _get_memory(self) -> Any:
        """Lazy-init MemoryPalace (best-effort — returns None if unavailable)."""
        if self._memory is None:
            try:
                from src.memory import MemoryPalace

                self._memory = MemoryPalace()
            except (ImportError, Exception) as exc:
                logger.debug("MemoryPalace not available (optional): %s", exc)
                self._memory = False  # Sentinel: tried and failed
        return self._memory if self._memory is not False else None

    def _store_interaction(
        self,
        agent: str,
        prompt: str,
        task_type: str,
        envelope: Any,
        start_time: float,
    ) -> None:
        """Store a completed ask() interaction in MemoryPalace (best-effort)."""
        mem = self._get_memory()
        if mem is None:
            return
        try:
            import time as _time

            node_id = f"{agent}:{task_type}:{int(_time.time() * 1000)}"
            mem.add_memory_node(
                node_id,
                {
                    "prompt": prompt[:300],
                    "agent": agent,
                    "task_type": task_type,
                    "success": envelope.success,
                    "timing_ms": envelope.timing_ms,
                },
                tags=[agent, task_type, "ask", "success" if envelope.success else "failed"],
            )
        except Exception as exc:
            logger.debug("MemoryPalace store failed (non-fatal): %s", exc)

    def recall(self, tag: str, limit: int = 10) -> list[dict[str, Any]]:
        """Query MemoryPalace + file chronicle for past interactions by tag.

        Merges in-session MemoryPalace nodes with persistent entries written to
        ``state/memory_chronicle.jsonl`` (e.g. culture_ship_cycle results).

        Args:
            tag: Tag to search (e.g., "ollama", "analyze", "culture_ship", "failed")
            limit: Maximum number of results to return

        Returns:
            List of memory node content dicts, most-recent first (up to limit).
        """
        results: list[dict[str, Any]] = []

        # 1) In-session MemoryPalace (fast, current process only)
        mem = self._get_memory()
        if mem is not None:
            try:
                node_ids = mem.search_by_tag(tag)
                for nid in reversed(node_ids[-limit:]):
                    node = mem.retrieve_memory_node(nid)
                    if node:
                        results.append({"node_id": nid, "source": "session", **node})
            except Exception as exc:
                logger.debug("MemoryPalace recall failed (non-fatal): %s", exc)

        # 2) Persistent chronicle (cross-process, file-backed)
        try:
            chronicle_path = (
                Path(__file__).resolve().parents[2] / "state" / "memory_chronicle.jsonl"
            )
            if chronicle_path.exists():
                chronicle_hits: list[dict[str, Any]] = []
                with open(chronicle_path, encoding="utf-8") as _f:
                    for line in _f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        entry_tags = entry.get("tags", [])
                        if isinstance(entry_tags, list) and tag in entry_tags:
                            chronicle_hits.append({"source": "chronicle", **entry})
                # Most recent first (file is append-order, so reverse)
                for hit in reversed(chronicle_hits[-limit:]):
                    if not any(r.get("node_id") == hit.get("node_id") for r in results):
                        results.append(hit)
        except Exception as exc:
            logger.debug("Chronicle recall failed (non-fatal): %s", exc)

        return results[:limit]

    async def _ask_intermediary(
        self,
        prompt: str,
        ctx: dict[str, Any],
        task_type: str,
    ) -> dict[str, Any]:
        """Route a prompt through AIIntermediary (cognitive bridge layer).

        Falls back to a descriptive error dict if the intermediary is unavailable.
        """
        intermediary = self._get_intermediary()
        if intermediary is None:
            return {
                "status": "failed",
                "system": "intermediary",
                "error": "AIIntermediary unavailable — import failed or OllamaHub missing",
                "suggestion": "Route to ollama or lmstudio instead",
            }
        try:
            from src.ai.ai_intermediary import CognitiveParadigm

            # Map task_type → paradigm
            _PARADIGM_MAP: dict[str, CognitiveParadigm] = {
                "analyze": CognitiveParadigm.CODE_ANALYSIS,
                "debug": CognitiveParadigm.CODE_ANALYSIS,
                "generate": CognitiveParadigm.CODE_ANALYSIS,
                "plan": CognitiveParadigm.SYMBOLIC_LOGIC,
                "review": CognitiveParadigm.CODE_ANALYSIS,
                "document": CognitiveParadigm.NATURAL_LANGUAGE,
                "optimize": CognitiveParadigm.MATHEMATICAL,
                "refactor": CognitiveParadigm.CODE_ANALYSIS,
            }
            paradigm = _PARADIGM_MAP.get(task_type, CognitiveParadigm.NATURAL_LANGUAGE)

            event = await intermediary.handle(
                input_data=prompt,
                context=ctx,
                source="mjolnir",
                paradigm=paradigm,
                use_ollama=True,
            )
            payload = event.payload if hasattr(event, "payload") else str(event)
            return {
                "status": "success",
                "system": "intermediary",
                "response": str(payload) if not isinstance(payload, str) else payload,
                "paradigm": paradigm.value,
                "event_id": getattr(event, "event_id", None),
            }
        except Exception as exc:
            logger.warning("AIIntermediary dispatch failed: %s", exc)
            return {
                "status": "failed",
                "system": "intermediary",
                "error": str(exc),
            }

    async def _ask_openclaw(
        self,
        prompt: str,
        ctx: dict[str, Any],
        timeout: float | None = None,
        wait_for_completion: bool = True,
    ) -> dict[str, Any]:
        """Route a prompt through OpenClaw CLI (uses local Ollama via gateway).

        OpenClaw provides a rich agent interface with tool support, memory,
        and workspace awareness. This method calls `openclaw agent --local`.
        """
        import json as _json
        import shutil
        import subprocess

        def _coerce_bool(value: Any, default: bool) -> bool:
            if value is None:
                return default
            if isinstance(value, bool):
                return value
            return str(value).strip().lower() in {"1", "true", "yes", "on"}

        # Resolve timeout + retry posture (adaptive for local/offline LLM latencies).
        timeout_raw = timeout if timeout is not None else ctx.get("timeout")
        if timeout_raw is None:
            timeout_raw = ctx.get(
                "openclaw_timeout_seconds",
                os.getenv("NUSYQ_OPENCLAW_DEFAULT_TIMEOUT_S", "900"),
            )
        try:
            min_timeout = float(os.getenv("NUSYQ_OPENCLAW_MIN_TIMEOUT_S", "30"))
        except (TypeError, ValueError):
            min_timeout = 30.0
        min_timeout = max(5.0, min_timeout)
        try:
            timeout_base = max(min_timeout, float(timeout_raw))
        except (TypeError, ValueError):
            timeout_base = 900.0
        try:
            retry_attempts = int(
                ctx.get(
                    "openclaw_retry_attempts",
                    os.getenv("NUSYQ_OPENCLAW_RETRY_ATTEMPTS", "3"),
                )
            )
        except (TypeError, ValueError):
            retry_attempts = 3
        retry_attempts = max(1, min(retry_attempts, 5))
        try:
            retry_backoff = float(
                ctx.get(
                    "openclaw_retry_backoff",
                    os.getenv("NUSYQ_OPENCLAW_TIMEOUT_BACKOFF", "1.0"),
                )
            )
        except (TypeError, ValueError):
            retry_backoff = 1.0
        retry_backoff = max(0.0, retry_backoff)
        timeout_growth = max(1.0, 1.0 + retry_backoff)

        openclaw_agent = str(
            ctx.get("openclaw_agent_id") or os.getenv("NUSYQ_OPENCLAW_AGENT_ID", "")
        ).strip()
        if not openclaw_agent:
            preferred_agent = Path.home() / ".openclaw" / "agents" / "nusyq" / "agent"
            openclaw_agent = "nusyq" if preferred_agent.exists() else "main"
        if not openclaw_agent:
            openclaw_agent = "main"

        requested_model = str(
            ctx.get("openclaw_model")
            or ctx.get("ollama_model")
            or os.getenv("NUSYQ_OPENCLAW_MODEL", "")
        ).strip()
        if requested_model and "/" not in requested_model:
            requested_model = f"ollama/{requested_model}"

        subprocess_env = os.environ.copy()
        ollama_api_key = str(
            ctx.get("openclaw_ollama_api_key")
            or os.getenv("NUSYQ_OPENCLAW_OLLAMA_API_KEY", "ollama-local")
        ).strip()
        if ollama_api_key:
            subprocess_env.setdefault("OLLAMA_API_KEY", ollama_api_key)

        wait_for_completion = _coerce_bool(
            ctx.get("openclaw_wait_for_completion"),
            wait_for_completion,
        )
        if "openclaw_non_blocking" in ctx:
            wait_for_completion = not _coerce_bool(ctx.get("openclaw_non_blocking"), False)
        elif self._env_flag("NUSYQ_OPENCLAW_NON_BLOCKING", "0"):
            wait_for_completion = False

        auto_non_blocking_on_timeout = _coerce_bool(
            ctx.get("openclaw_auto_non_blocking_on_timeout"),
            self._env_flag("NUSYQ_OPENCLAW_AUTO_NON_BLOCKING_ON_TIMEOUT", "1"),
        )
        hub_root = Path(str(ctx.get("hub_root") or self._repo_root or Path.cwd()))

        # Find openclaw command - check PATH first, then npm directory
        openclaw_cmd = shutil.which("openclaw")
        if not openclaw_cmd:
            # Try npm global directory
            npm_global = os.path.join(os.environ.get("APPDATA", ""), "npm")
            for candidate in ["openclaw.cmd", "openclaw"]:
                candidate_path = os.path.join(npm_global, candidate)
                if os.path.exists(candidate_path):
                    openclaw_cmd = candidate_path
                    break

        if not openclaw_cmd:
            return {
                "status": "failed",
                "system": "openclaw",
                "error": "openclaw command not found in PATH or npm global directory",
            }

        cmd_base = [
            openclaw_cmd,
            "agent",
            "--local",
            "--agent",
            openclaw_agent,
            "--message",
            prompt,
            "--json",
        ]

        model_override_applied = False
        model_override_error: str | None = None
        if requested_model:
            model_set_cmd = [
                openclaw_cmd,
                "models",
                "--agent",
                openclaw_agent,
                "set",
                requested_model,
            ]
            try:
                model_set_result = subprocess.run(
                    model_set_cmd,
                    capture_output=True,
                    text=True,
                    timeout=max(min_timeout, min(120.0, timeout_base / 2.0)),
                    check=False,
                    cwd=str(hub_root),
                    env=subprocess_env,
                )
                if model_set_result.returncode == 0:
                    model_override_applied = True
                else:
                    err_text = (model_set_result.stderr or model_set_result.stdout or "").strip()
                    model_override_error = (
                        err_text[:300] if err_text else "Failed to set OpenClaw model override"
                    )
            except Exception as exc:
                model_override_error = str(exc)[:300]

        def _command_for_timeout(seconds: float) -> list[str]:
            return [*cmd_base, "--timeout", str(int(max(min_timeout, seconds)))]

        def _spawn_non_blocking(reason: str, launch_timeout: float) -> dict[str, Any]:
            log_dir = hub_root / "logs" / "openclaw"
            log_dir.mkdir(parents=True, exist_ok=True)
            stamp = time.strftime("%Y%m%d_%H%M%S")
            stdout_log = log_dir / f"openclaw_agent_stdout_{stamp}.log"
            stderr_log = log_dir / f"openclaw_agent_stderr_{stamp}.log"
            launch_cmd = _command_for_timeout(launch_timeout)
            with (
                stdout_log.open("w", encoding="utf-8") as out,
                stderr_log.open("w", encoding="utf-8") as err,
            ):
                proc = subprocess.Popen(
                    launch_cmd,
                    cwd=str(hub_root),
                    stdout=out,
                    stderr=err,
                    text=True,
                    env=subprocess_env,
                )
            return {
                "status": "success",
                "system": "openclaw",
                "result_status": "submitted",
                "note": "OpenClaw process launched in non-blocking mode",
                "non_blocking": True,
                "reason": reason,
                "pid": proc.pid,
                "agent_id": openclaw_agent,
                "requested_model": requested_model or None,
                "stdout_log": str(stdout_log),
                "stderr_log": str(stderr_log),
                "timeout_seconds": launch_timeout,
                "retry_attempts": retry_attempts,
                "model_override_applied": model_override_applied,
                "model_override_error": model_override_error,
            }

        if not wait_for_completion:
            return _spawn_non_blocking("non_blocking_requested", timeout_base)

        timeout_history: list[float] = []

        for attempt in range(1, retry_attempts + 1):
            attempt_timeout = max(min_timeout, timeout_base * (timeout_growth ** (attempt - 1)))
            timeout_history.append(round(attempt_timeout, 2))
            attempt_cmd = _command_for_timeout(attempt_timeout)
            try:
                result = subprocess.run(
                    attempt_cmd,
                    capture_output=True,
                    text=True,
                    timeout=attempt_timeout,
                    check=False,
                    env=subprocess_env,
                )
            except subprocess.TimeoutExpired:
                if attempt < retry_attempts:
                    continue
                if auto_non_blocking_on_timeout:
                    launch_timeout = max(attempt_timeout * timeout_growth, timeout_base)
                    submitted = _spawn_non_blocking(
                        "auto_non_blocking_after_timeout",
                        launch_timeout,
                    )
                    submitted["timeout_history_seconds"] = timeout_history
                    submitted["adaptive_timeout_next_seconds"] = round(launch_timeout, 2)
                    return submitted
                return {
                    "status": "failed",
                    "system": "openclaw",
                    "error": (
                        f"OpenClaw agent timed out after {attempt_timeout:.1f}s (attempt {attempt}/{retry_attempts})"
                    ),
                    "timeout_history_seconds": timeout_history,
                    "next_timeout_seconds": round(attempt_timeout * timeout_growth, 2),
                    "suggestion": (
                        "Retry with --non-blocking, increase --timeout, or set "
                        "NUSYQ_OPENCLAW_DEFAULT_TIMEOUT_S for heavier local models."
                    ),
                    "agent_id": openclaw_agent,
                    "requested_model": requested_model or None,
                    "model_override_applied": model_override_applied,
                    "model_override_error": model_override_error,
                }
            except FileNotFoundError:
                return {
                    "status": "failed",
                    "system": "openclaw",
                    "error": "openclaw command not found in PATH",
                    "agent_id": openclaw_agent,
                    "requested_model": requested_model or None,
                    "model_override_applied": model_override_applied,
                    "model_override_error": model_override_error,
                }
            except Exception as exc:
                logger.warning("OpenClaw dispatch failed: %s", exc)
                return {
                    "status": "failed",
                    "system": "openclaw",
                    "error": str(exc),
                    "agent_id": openclaw_agent,
                    "requested_model": requested_model or None,
                    "model_override_applied": model_override_applied,
                    "model_override_error": model_override_error,
                }

            if result.returncode != 0:
                stderr_text = result.stderr[:500] if result.stderr else "Non-zero exit"
                if attempt < retry_attempts and "timeout" in stderr_text.lower():
                    continue
                return {
                    "status": "failed",
                    "system": "openclaw",
                    "error": stderr_text,
                    "exit_code": result.returncode,
                    "attempt": attempt,
                    "retry_attempts": retry_attempts,
                    "agent_id": openclaw_agent,
                    "requested_model": requested_model or None,
                    "model_override_applied": model_override_applied,
                    "model_override_error": model_override_error,
                }

            # Parse JSON output
            try:
                data = _json.loads(result.stdout)
                # Extract text response from payloads
                payloads = data.get("payloads", [])
                text_responses = [
                    p.get("text", "") for p in payloads if isinstance(p, dict) and p.get("text")
                ]
                response_text = (
                    "\n".join(text_responses) if text_responses else "(no text response)"
                )
                meta = data.get("meta", {})
                agent_meta = meta.get("agentMeta", {})

                return {
                    "status": "success",
                    "system": "openclaw",
                    "response": response_text,
                    "model": agent_meta.get("model"),
                    "provider": agent_meta.get("provider"),
                    "usage": agent_meta.get("usage"),
                    "session_id": agent_meta.get("sessionId"),
                    "duration_ms": meta.get("durationMs"),
                    "agent_id": openclaw_agent,
                    "requested_model": requested_model or None,
                    "model_override_applied": model_override_applied,
                    "model_override_error": model_override_error,
                    "attempt": attempt,
                    "retry_attempts": retry_attempts,
                    "timeout_history_seconds": timeout_history,
                }
            except _json.JSONDecodeError:
                # Non-JSON output (maybe direct text)
                return {
                    "status": "success",
                    "system": "openclaw",
                    "response": result.stdout[:2000],
                    "agent_id": openclaw_agent,
                    "requested_model": requested_model or None,
                    "model_override_applied": model_override_applied,
                    "model_override_error": model_override_error,
                    "attempt": attempt,
                    "retry_attempts": retry_attempts,
                    "timeout_history_seconds": timeout_history,
                }

        return {
            "status": "failed",
            "system": "openclaw",
            "error": "OpenClaw execution ended without a successful response",
            "agent_id": openclaw_agent,
            "requested_model": requested_model or None,
            "model_override_applied": model_override_applied,
            "model_override_error": model_override_error,
            "retry_attempts": retry_attempts,
            "timeout_history_seconds": timeout_history,
        }

    def _get_sns_convert(self):
        """Lazy-load SNS-Core conversion function."""
        if not self._sns_helper_loaded:
            self._sns_helper_loaded = True
            try:
                from src.utils.sns_core_helper import convert_to_sns

                self._sns_convert = convert_to_sns
            except (ImportError, Exception) as exc:
                logger.debug("SNS-Core not available (optional): %s", exc)
        return self._sns_convert

    def _resolve_agent(self, agent: str) -> str:
        """Resolve agent alias to canonical target system name."""
        normalized = agent.strip().lower()
        return AGENT_ALIASES.get(normalized, normalized)

    def _apply_sns(self, prompt: str) -> tuple[str, dict[str, Any]]:
        """Apply SNS-Core compression if available.

        Returns (compressed_prompt, sns_metadata).
        """
        convert = self._get_sns_convert()
        if convert is None:
            return prompt, {"sns_available": False}
        try:
            compressed, metadata = convert(prompt, aggressive=False)
            return compressed, metadata
        except Exception as exc:
            logger.warning("SNS-Core compression failed: %s", exc)
            return prompt, {"sns_error": str(exc)}

    @staticmethod
    def _env_flag(name: str, default: str = "0") -> bool:
        return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _coerce_bool(value: Any, default: bool = False) -> bool:
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _normalize_operating_mode(value: Any) -> str:
        mode = str(value or "").strip().lower()
        if mode in {"strict", "balanced", "fast"}:
            return mode
        return "balanced"

    @staticmethod
    def _normalize_risk_level(value: Any, priority: str = "NORMAL") -> str:
        risk = str(value or "").strip().lower()
        if risk in {"low", "medium", "high"}:
            return risk
        normalized_priority = str(priority or "NORMAL").strip().upper()
        if normalized_priority in {"CRITICAL", "HIGH"}:
            return "high"
        if normalized_priority in {"LOW", "BACKGROUND"}:
            return "low"
        return "medium"

    @staticmethod
    def _merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        merged = dict(base)
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = MjolnirProtocol._merge_dict(
                    dict(merged[key]),
                    value,
                )
            else:
                merged[key] = value
        return merged

    def _profile_repo_root(self) -> Path:
        if self._repo_root is not None:
            return Path(self._repo_root)
        return Path(__file__).resolve().parents[2]

    def _load_dispatch_profile_config(self) -> dict[str, Any]:
        """Load dispatch profile config from team defaults + local file + env."""
        local_file = os.getenv("NUSYQ_DISPATCH_PROFILE_LOCAL_FILE", "").strip()
        if not local_file:
            local_file = str(self._profile_repo_root() / "config" / "dispatch_profiles.local.json")

        cache_key = f"{local_file}|{os.getenv('NUSYQ_NON_BLOCKING_TARGETS', '')}|{os.getenv('NUSYQ_OPERATING_MODE', '')}|{os.getenv('NUSYQ_PROFILE_DEFAULT_RISK_LEVEL', '')}|{os.getenv('NUSYQ_PROFILE_DEFAULT_SIGNAL_BUDGET', '')}"
        if self._profile_config_cache is not None and self._profile_config_cache_key == cache_key:
            return dict(self._profile_config_cache)

        config: dict[str, Any] = {
            "defaults": {
                "operating_mode": "balanced",
                "risk_level": "medium",
                "signal_budget": "normal",
            },
            "non_blocking_targets": [
                "openclaw",
                "chatdev",
                "ollama",
                "lmstudio",
                "copilot",
            ],
            "target_overrides": {},
        }

        try:
            from src.config.orchestration_config_loader import get_config_value

            team_profiles = get_config_value("dispatch_profiles", {})
            if isinstance(team_profiles, dict):
                config = self._merge_dict(config, team_profiles)
        except Exception as exc:
            logger.debug("Dispatch profile team defaults unavailable: %s", exc)

        local_path = Path(local_file).expanduser()
        if local_path.exists():
            try:
                payload = json.loads(local_path.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    config = self._merge_dict(config, payload)
            except (json.JSONDecodeError, ValueError, OSError) as exc:
                logger.warning(
                    "Ignoring invalid dispatch profile local override %s: %s", local_path, exc
                )

        env_non_blocking_targets = os.getenv("NUSYQ_NON_BLOCKING_TARGETS", "").strip()
        if env_non_blocking_targets:
            config["non_blocking_targets"] = [
                item.strip().lower() for item in env_non_blocking_targets.split(",") if item.strip()
            ]

        if os.getenv("NUSYQ_OPERATING_MODE"):
            config.setdefault("defaults", {})["operating_mode"] = os.getenv(
                "NUSYQ_OPERATING_MODE",
                "balanced",
            )
        if os.getenv("NUSYQ_PROFILE_DEFAULT_RISK_LEVEL"):
            config.setdefault("defaults", {})["risk_level"] = os.getenv(
                "NUSYQ_PROFILE_DEFAULT_RISK_LEVEL",
                "medium",
            )
        if os.getenv("NUSYQ_PROFILE_DEFAULT_SIGNAL_BUDGET"):
            config.setdefault("defaults", {})["signal_budget"] = os.getenv(
                "NUSYQ_PROFILE_DEFAULT_SIGNAL_BUDGET",
                "normal",
            )

        self._profile_config_cache = dict(config)
        self._profile_config_cache_key = cache_key
        return config

    @staticmethod
    def _set_non_blocking_mode(ctx: dict[str, Any], target_system: str) -> None:
        ctx.setdefault("non_blocking", True)
        ctx.setdefault("wait_for_completion", False)
        if target_system == "openclaw":
            ctx.setdefault("openclaw_non_blocking", True)
        if target_system == "chatdev":
            ctx.setdefault("chatdev_wait_for_completion", False)

    @staticmethod
    def _set_blocking_mode(ctx: dict[str, Any], target_system: str) -> None:
        # Respect explicit non_blocking=True from caller (e.g., extra_context)
        if ctx.get("non_blocking") is True:
            return
        ctx.setdefault("wait_for_completion", True)
        if target_system == "openclaw":
            ctx.setdefault("openclaw_wait_for_completion", True)
        if target_system == "chatdev":
            ctx.setdefault("chatdev_wait_for_completion", True)

    def _is_non_blocking_requested(self, ctx: dict[str, Any], target_system: str) -> bool:
        if self._coerce_bool(ctx.get("wait_for_completion"), False):
            return False
        if target_system == "openclaw" and self._coerce_bool(
            ctx.get("openclaw_wait_for_completion"),
            False,
        ):
            return False
        if target_system == "chatdev" and "chatdev_wait_for_completion" in ctx:
            return not self._coerce_bool(ctx.get("chatdev_wait_for_completion"), True)
        if self._coerce_bool(ctx.get("non_blocking"), False):
            return True
        if target_system == "openclaw":
            return self._coerce_bool(ctx.get("openclaw_non_blocking"), False)
        return False

    def _apply_operating_profile(
        self,
        ctx: dict[str, Any],
        *,
        target_system: str,
        priority: str,
    ) -> dict[str, Any]:
        """Apply strict/balanced/fast operating profile to routing context."""
        profile_config = self._load_dispatch_profile_config()
        defaults = profile_config.get("defaults", {})
        defaults = defaults if isinstance(defaults, dict) else {}
        target_overrides = profile_config.get("target_overrides", {})
        target_overrides = target_overrides if isinstance(target_overrides, dict) else {}
        target_defaults = target_overrides.get(target_system, {})
        target_defaults = target_defaults if isinstance(target_defaults, dict) else {}

        default_mode = target_defaults.get("operating_mode") or defaults.get("operating_mode")
        mode = self._normalize_operating_mode(
            ctx.get("operating_mode")
            or default_mode
            or os.getenv("NUSYQ_OPERATING_MODE", "balanced")
        )
        default_risk = target_defaults.get("risk_level") or defaults.get("risk_level")
        # Strong priority signals (LOW, HIGH, CRITICAL) override config defaults
        # when no explicit risk_level is provided in context
        explicit_risk = ctx.get("risk_level")
        priority_upper = priority.upper() if priority else "MEDIUM"
        if explicit_risk:
            risk = self._normalize_risk_level(explicit_risk, priority=priority)
        elif priority_upper in {"LOW", "HIGH", "CRITICAL"}:
            risk = self._normalize_risk_level(None, priority=priority)
        else:
            risk = self._normalize_risk_level(default_risk, priority=priority)
        signal_budget = (
            str(
                ctx.get("signal_budget")
                or target_defaults.get("signal_budget")
                or defaults.get("signal_budget")
                or ""
            )
            .strip()
            .lower()
        )
        if signal_budget not in {"minimal", "normal", "full"}:
            signal_budget = {"strict": "full", "fast": "minimal"}.get(mode, "normal")

        non_blocking_targets = profile_config.get("non_blocking_targets", [])
        non_blocking_targets = (
            [str(item).strip().lower() for item in non_blocking_targets]
            if isinstance(non_blocking_targets, list)
            else []
        )
        target_allow_non_blocking = self._coerce_bool(
            target_defaults.get("allow_non_blocking"),
            True,
        )
        non_blocking_eligible = target_allow_non_blocking and target_system in set(
            non_blocking_targets
        )

        profile: dict[str, Any] = {
            "mode": mode,
            "risk_level": risk,
            "signal_budget": signal_budget,
            "target_system": target_system,
            "priority": priority,
            "non_blocking_eligible": non_blocking_eligible,
        }

        if mode == "strict":
            ctx.setdefault("strict_timeouts", True)
            self._set_blocking_mode(ctx, target_system)
            if target_system == "openclaw":
                ctx.setdefault("openclaw_auto_non_blocking_on_timeout", False)
                ctx.setdefault("openclaw_retry_attempts", 2)
                ctx.setdefault("openclaw_retry_backoff", 0.5)
            profile["execution_policy"] = "blocking_verified"
            profile["diagnostics_policy"] = "full"
        elif mode == "fast":
            ctx.setdefault("strict_timeouts", False)
            if non_blocking_eligible:
                self._set_non_blocking_mode(ctx, target_system)
            if target_system == "openclaw":
                ctx.setdefault("openclaw_auto_non_blocking_on_timeout", True)
                ctx.setdefault("openclaw_retry_attempts", 1)
                ctx.setdefault("openclaw_retry_backoff", 0.25)
            profile["execution_policy"] = "non_blocking_preferred"
            profile["diagnostics_policy"] = "minimal"
        else:
            ctx.setdefault("strict_timeouts", False)
            if non_blocking_eligible and risk == "low":
                self._set_non_blocking_mode(ctx, target_system)
            else:
                self._set_blocking_mode(ctx, target_system)
            if target_system == "openclaw":
                ctx.setdefault("openclaw_auto_non_blocking_on_timeout", True)
                ctx.setdefault("openclaw_retry_attempts", 3 if risk != "high" else 2)
                ctx.setdefault("openclaw_retry_backoff", 1.0)
            profile["execution_policy"] = (
                "blocking_high_risk_non_blocking_low_risk"
                if non_blocking_eligible
                else "blocking_default"
            )
            profile["diagnostics_policy"] = "targeted"

        ctx["operating_mode"] = mode
        ctx["risk_level"] = risk
        ctx["signal_budget"] = signal_budget
        ctx["operating_profile"] = profile
        return profile

    def _effective_dispatch_timeout(
        self,
        target_system: str,
        requested_timeout: float | None,
        probe_status: str | None = None,
        strict_override: bool | None = None,
    ) -> float:
        """Compute adaptive timeout with grace for local/offline models."""
        strict = (
            bool(strict_override)
            if strict_override is not None
            else self._env_flag("NUSYQ_STRICT_TIMEOUTS", "0")
        )
        try:
            openclaw_default_timeout = float(os.getenv("NUSYQ_OPENCLAW_DEFAULT_TIMEOUT_S", "900"))
        except ValueError:
            openclaw_default_timeout = 900.0
        default_timeouts: dict[str, float] = {
            "ollama": 180.0,
            "lmstudio": 180.0,
            "openclaw": max(30.0, openclaw_default_timeout),
            "chatdev": 900.0,
        }
        default_timeout = default_timeouts.get(target_system, 120.0)
        try:
            max_timeout = float(os.getenv("NUSYQ_MAX_TIMEOUT_S", "3600"))
        except ValueError:
            max_timeout = 3600.0
        max_timeout = max(60.0, max_timeout)

        if requested_timeout is None:
            effective = default_timeout
        else:
            try:
                requested = max(1.0, float(requested_timeout))
            except (TypeError, ValueError):
                requested = default_timeout
            if strict:
                effective = requested
            else:
                grace_multiplier = 1.0
                if target_system in {"ollama", "lmstudio", "openclaw", "chatdev"}:
                    try:
                        grace_multiplier = float(
                            os.getenv("NUSYQ_LOCAL_LLM_TIMEOUT_GRACE_MULTIPLIER", "2.5")
                        )
                    except ValueError:
                        grace_multiplier = 2.5
                floor = default_timeout / 3.0
                effective = max(floor, requested * max(1.0, grace_multiplier))

        if not strict and probe_status in {"offline", "degraded"}:
            try:
                offline_multiplier = float(
                    os.getenv("NUSYQ_OFFLINE_TIMEOUT_GRACE_MULTIPLIER", "1.5")
                )
            except ValueError:
                offline_multiplier = 1.5
            effective *= max(1.0, offline_multiplier)

        return min(max(1.0, effective), max_timeout)

    async def _queue_background_non_blocking(
        self,
        *,
        target_system: str,
        prompt: str,
        task_type: str,
        priority: str,
        ctx: dict[str, Any],
    ) -> dict[str, Any]:
        """Submit eligible targets to the persisted background queue."""
        try:
            from src.orchestration.background_task_orchestrator import \
                TaskPriority as BGTaskPriority
            from src.orchestration.background_task_orchestrator import (
                TaskTarget, get_orchestrator)
        except ImportError as exc:
            return {
                "status": "failed",
                "system": target_system,
                "error": f"background_queue_unavailable: {exc}",
                "non_blocking": True,
            }

        target_map = {
            "ollama": TaskTarget.OLLAMA,
            "lmstudio": TaskTarget.LM_STUDIO,
            "chatdev": TaskTarget.CHATDEV,
            "copilot": TaskTarget.COPILOT,
        }
        mapped_target = target_map.get(target_system, TaskTarget.AUTO)

        try:
            mapped_priority = BGTaskPriority[str(priority).strip().upper()]
        except KeyError:
            mapped_priority = BGTaskPriority.NORMAL

        model = None
        if target_system == "ollama":
            model = str(ctx.get("ollama_model") or ctx.get("model") or "").strip() or None
        elif target_system == "lmstudio":
            model = str(ctx.get("lmstudio_model") or ctx.get("model") or "").strip() or None

        metadata = {
            "non_blocking": True,
            "source": "mjolnir.ask",
            "requested_target": target_system,
            "operating_profile": ctx.get("operating_profile"),
            "risk_level": ctx.get("risk_level"),
            "signal_budget": ctx.get("signal_budget"),
        }

        def _submit() -> Any:
            orchestrator = get_orchestrator()
            return orchestrator.submit_task(
                prompt=prompt,
                target=mapped_target,
                model=model,
                priority=mapped_priority,
                requesting_agent="mjolnir",
                task_type=task_type,
                metadata=metadata,
            )

        try:
            task = await asyncio.to_thread(_submit)
        except Exception as exc:
            return {
                "status": "failed",
                "system": target_system,
                "error": f"background_queue_submit_failed: {exc}",
                "non_blocking": True,
            }

        return {
            "status": "submitted",
            "system": target_system,
            "task_id": getattr(task, "task_id", None),
            "queue_target": getattr(
                getattr(task, "target", None), "value", str(mapped_target.value)
            ),
            "model": getattr(task, "model", model),
            "non_blocking": True,
            "note": "Task queued for asynchronous execution via BackgroundTaskOrchestrator",
            "metadata": metadata,
        }

    def _record_dispatch_profile_signal(
        self,
        *,
        target_system: str,
        ctx: dict[str, Any],
        task_type: str,
        status: str,
        non_blocking: bool,
        error: str | None = None,
    ) -> None:
        """Record profile-aware dispatch metrics into existing metrics pipeline."""
        try:
            from src.system.ai_metrics_tracker import AIMetricsTracker

            tracker = AIMetricsTracker(self._profile_repo_root())
            profile = (
                ctx.get("operating_profile")
                if isinstance(ctx.get("operating_profile"), dict)
                else {}
            )
            tracker.record_dispatch_profile(
                system_name=target_system,
                mode=str(profile.get("mode") or ctx.get("operating_mode") or "balanced"),
                risk_level=str(profile.get("risk_level") or ctx.get("risk_level") or "medium"),
                signal_budget=str(
                    profile.get("signal_budget") or ctx.get("signal_budget") or "normal"
                ),
                status=status,
                non_blocking=non_blocking,
                metadata={
                    "task_type": task_type,
                    "priority": str(profile.get("priority") or ""),
                    "execution_policy": str(profile.get("execution_policy") or ""),
                    "error": error or "",
                },
            )
        except Exception as exc:
            logger.debug("Dispatch profile metric recording skipped: %s", exc)

    # Priority string → guild board int mapping
    _PRIORITY_MAP: ClassVar[dict[str, int]] = {
        "CRITICAL": 1,
        "HIGH": 2,
        "NORMAL": 3,
        "LOW": 4,
        "BACKGROUND": 5,
    }

    async def _guild_announce(
        self, agent: str, prompt: str, priority: str = "NORMAL"
    ) -> str | None:
        """Announce a dispatch to the guild board as a quest. Best-effort."""
        guild = self._get_guild()
        if guild is None:
            return None
        try:
            title = f"MJOLNIR→{agent}: {prompt[:60]}"
            guild_priority = self._PRIORITY_MAP.get(priority.upper(), 3)
            ok, quest_id = await guild.add_quest(
                quest_id=None,
                title=title,
                description=prompt[:200],
                priority=guild_priority,
                safety_tier="safe",
                tags=["mjolnir", agent],
            )
            return quest_id if ok else None
        except Exception as exc:
            logger.debug("Guild announce failed (non-fatal): %s", exc)
            return None

    async def _guild_complete(self, quest_id: str | None, _result: Any) -> None:
        """Mark a guild quest as complete. Best-effort."""
        if quest_id is None:
            return
        guild = self._get_guild()
        if guild is None:
            return
        try:
            await guild.complete_quest(quest_id, agent_id="mjolnir")
        except Exception as exc:
            logger.debug("Guild complete failed (non-fatal): %s", exc)

    # ── Core dispatch methods ────────────────────────────────────────────────

    async def ask(
        self,
        agent: str,
        prompt: str,
        *,
        context: str | ContextMode | None = None,
        sns: bool = False,
        task_type: str | None = None,
        model: str | None = None,
        context_file: str | None = None,
        timeout: float | None = None,
        no_guild: bool = False,
        priority: str = "NORMAL",
        extra_context: dict[str, Any] | None = None,
    ) -> ResponseEnvelope:
        """Route a prompt to a single agent.

        This is the core method — all other patterns call ask() internally.

        Args:
            agent: Agent name or alias (e.g., "ollama", "claude", "lms")
            prompt: Natural language prompt
            context: Context mode override (ecosystem/project/game/auto)
            sns: Apply SNS-Core compression to the prompt
            task_type: Override task type inference (analyze/generate/review/etc.)
            model: Specific model to request (e.g., "qwen2.5-coder:14b")
            context_file: File path to include as context
            timeout: Override default timeout
            no_guild: Skip guild board tracking
            priority: Task priority (CRITICAL/HIGH/NORMAL/LOW/BACKGROUND)
            extra_context: Additional context dict to merge

        Returns:
            ResponseEnvelope with structured result
        """
        start_time = time.monotonic()

        # 1. Resolve agent alias
        target_system = self._resolve_agent(agent)

        # 2. Detect or use explicit context mode
        if isinstance(context, ContextMode):
            mode = context
        elif isinstance(context, str) and context != "auto":
            try:
                mode = ContextMode(context)
            except ValueError:
                mode = self._context.detect()
        else:
            mode = self._context.detect()

        # 3. Apply SNS-Core if requested
        sns_applied = False
        sns_metadata: dict[str, Any] = {}
        effective_prompt = prompt
        if sns:
            effective_prompt, sns_metadata = self._apply_sns(prompt)
            sns_applied = bool(sns_metadata.get("replacements"))

        # 4. Build enriched context
        ctx = self._context.enrich_context(mode)
        if context_file:
            ctx["file"] = context_file
        if model:
            ctx["ollama_model"] = model
            ctx["openclaw_model"] = model
        if timeout:
            ctx["timeout"] = timeout
        if extra_context:
            ctx.update(extra_context)
        if sns_metadata:
            ctx["sns_metadata"] = sns_metadata
            # Wire token savings to the metrics dashboard so Culture Ship can track them
            if sns_applied and sns_metadata.get("original_tokens_est"):
                try:
                    from src.tools.token_metrics_dashboard import \
                        TokenMetricsDashboard

                    TokenMetricsDashboard().record_conversion(
                        original_tokens=sns_metadata["original_tokens_est"],
                        sns_tokens=sns_metadata["sns_tokens_est"],
                        operation=f"dispatch_{mode}",
                        mode=sns_metadata.get("mode", "normal"),
                    )
                except Exception:
                    pass  # Metrics recording is best-effort, never block dispatch

        profile_info = self._apply_operating_profile(
            ctx,
            target_system=target_system,
            priority=priority,
        )

        # 5. Infer task type
        effective_task_type = task_type or _infer_task_type(prompt)
        non_blocking_requested = self._is_non_blocking_requested(ctx, target_system)

        probe_status_for_timeout: str | None = None

        # 6. Pre-flight: ensure recoverable agents (Ollama) are running before routing.
        #    This is the key fix for the "notices offline but moves on" failure mode.
        if target_system in self._registry.RECOVERABLE_AGENTS:
            probe = await self._registry.probe_with_recovery(target_system, auto_recover=True)
            probe_status_for_timeout = str(probe.status)
            if probe.status != "online":
                self._record_dispatch_profile_signal(
                    target_system=target_system,
                    ctx=ctx,
                    task_type=effective_task_type,
                    status="failed",
                    non_blocking=non_blocking_requested,
                    error=f"{target_system} unavailable: {probe.detail}",
                )
                return ResponseEnvelope.from_error(
                    f"{target_system} is unavailable and auto-recovery failed: {probe.detail}",
                    agent=target_system,
                    context_mode=str(mode),
                    pattern="ask",
                    start_time=start_time,
                )

        # 7. Adaptive timeout policy (local/offline systems get grace by default).
        timeout_hint = ctx.get("timeout")
        apply_adaptive_timeout = timeout_hint is not None or target_system in {
            "ollama",
            "lmstudio",
            "openclaw",
            "chatdev",
        }
        effective_timeout: float | None = None
        if apply_adaptive_timeout:
            effective_timeout = self._effective_dispatch_timeout(
                target_system,
                timeout_hint if isinstance(timeout_hint, (int, float, str)) else None,
                probe_status=probe_status_for_timeout,
                strict_override=(
                    bool(ctx.get("strict_timeouts")) if "strict_timeouts" in ctx else None
                ),
            )
            ctx["timeout"] = effective_timeout
            if timeout_hint is not None:
                ctx["requested_timeout_seconds"] = timeout_hint
            ctx["adaptive_timeout_enabled"] = True

        # 8. Guild board announce (best-effort)
        quest_id = None
        if not no_guild:
            quest_id = await self._guild_announce(target_system, prompt, priority)

        if non_blocking_requested and target_system in {"ollama", "lmstudio", "copilot"}:
            result = await self._queue_background_non_blocking(
                target_system=target_system,
                prompt=effective_prompt,
                task_type=effective_task_type,
                priority=priority,
                ctx=ctx,
            )
            if "operating_profile" not in result:
                result["operating_profile"] = profile_info
            if not no_guild:
                await self._guild_complete(quest_id, result)
            self._record_dispatch_profile_signal(
                target_system=target_system,
                ctx=ctx,
                task_type=effective_task_type,
                status=str(result.get("status", "submitted")),
                non_blocking=True,
                error=str(result.get("error", "")) or None,
            )
            return ResponseEnvelope.wrap(
                result,
                agent=target_system,
                context_mode=str(mode),
                pattern="ask",
                sns_applied=sns_applied,
                guild_quest_id=quest_id,
                start_time=start_time,
            )

        # 9. Route through AgentTaskRouter (or special handlers for intermediary/openclaw)
        try:
            if target_system == "intermediary":
                result = await self._ask_intermediary(effective_prompt, ctx, effective_task_type)
            elif target_system == "openclaw":
                result = await self._ask_openclaw(effective_prompt, ctx, timeout=ctx.get("timeout"))
            else:
                router = self._get_router()
                result = await router.route_task(
                    task_type=effective_task_type,
                    description=effective_prompt,
                    context=ctx,
                    target_system=target_system,
                    priority=priority,
                )

            if isinstance(result, dict):
                if effective_timeout is not None and "timeout_seconds" not in result:
                    result["timeout_seconds"] = effective_timeout
                if timeout_hint is not None and "requested_timeout_seconds" not in result:
                    result["requested_timeout_seconds"] = timeout_hint
                if "operating_profile" not in result:
                    result["operating_profile"] = profile_info

            # 10. Guild complete (best-effort)
            if not no_guild:
                await self._guild_complete(quest_id, result)
            status_value = (
                str(result.get("status", "success")) if isinstance(result, dict) else "success"
            )
            self._record_dispatch_profile_signal(
                target_system=target_system,
                ctx=ctx,
                task_type=effective_task_type,
                status=status_value,
                non_blocking=non_blocking_requested,
                error=(
                    str(result.get("error"))
                    if isinstance(result, dict) and result.get("error")
                    else None
                ),
            )

            envelope = ResponseEnvelope.wrap(
                result,
                agent=target_system,
                context_mode=str(mode),
                pattern="ask",
                sns_applied=sns_applied,
                guild_quest_id=quest_id,
                start_time=start_time,
            )
            # Store interaction in MemoryPalace for cross-session recall
            self._store_interaction(
                target_system, prompt, effective_task_type, envelope, start_time
            )

            try:
                from src.system.agent_awareness import emit as _emit

                _ok = envelope.success
                _lvl = "INFO" if _ok else "WARNING"
                _emit(
                    "agents",
                    f"MJOLNIR ask: agent={target_system} sns={sns_applied} ok={_ok} timing={envelope.timing_ms}ms",
                    level=_lvl,
                    source="mjolnir_ask",
                )
            except Exception:
                pass
            return envelope

        except Exception as exc:
            logger.error("MJOLNIR ask(%s) failed: %s", target_system, exc)
            self._record_dispatch_profile_signal(
                target_system=target_system,
                ctx=ctx,
                task_type=effective_task_type,
                status="failed",
                non_blocking=non_blocking_requested,
                error=str(exc),
            )
            return ResponseEnvelope.from_error(
                str(exc),
                agent=target_system,
                context_mode=str(mode),
                pattern="ask",
                start_time=start_time,
            )

    async def _fan_out(
        self,
        prompt: str,
        *,
        agents: list[str] | None = None,
        sns: bool = False,
        task_type: str | None = None,
        pattern: str = "parallel",
        no_guild: bool = False,
        **kwargs: Any,
    ) -> ResponseEnvelope:
        """Fan out a prompt to multiple agents simultaneously.

        Internal method used by both council() and parallel(). Queries all
        agents in parallel via asyncio.gather and collects responses.

        Args:
            prompt: The question or task for all agents
            agents: List of agents to consult (defaults to ["ollama", "lmstudio"])
            sns: Apply SNS-Core compression
            task_type: Override task type inference
            pattern: Pattern label for the envelope (council/parallel)
            no_guild: Skip guild board tracking
            **kwargs: Additional keyword arguments forwarded to ask().
        """
        start_time = time.monotonic()
        targets = agents or ["ollama", "lmstudio"]
        mode = self._context.detect()

        # Query all agents in parallel
        tasks = [
            self.ask(
                agent,
                prompt,
                sns=sns,
                task_type=task_type,
                no_guild=True,  # Track at fan-out level, not per-ask
                **kwargs,
            )
            for agent in targets
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect responses
        agent_responses: dict[str, Any] = {}
        agents_used: list[str] = []
        for agent, result in zip(targets, results, strict=False):
            canonical = self._resolve_agent(agent)
            agents_used.append(canonical)
            if isinstance(result, Exception):
                agent_responses[canonical] = {"error": str(result)}
            elif isinstance(result, ResponseEnvelope):
                agent_responses[canonical] = {
                    "status": result.status,
                    "output": result.output,
                    "timing_ms": result.timing_ms,
                }
            else:
                agent_responses[canonical] = result

        # Guild tracking for the fan-out as a whole
        quest_id = None
        if not no_guild:
            quest_id = await self._guild_announce(
                pattern, f"{pattern}({','.join(agents_used)}): {prompt[:60]}"
            )
            await self._guild_complete(quest_id, agent_responses)

        return ResponseEnvelope(
            status="ok",
            success=True,
            agent=pattern,
            context_mode=str(mode),
            pattern=pattern,
            sns_applied=sns,
            output=agent_responses,
            guild_quest_id=quest_id,
            agents_used=agents_used,
            timing_ms=round((time.monotonic() - start_time) * 1000, 1),
        )

    async def council(
        self,
        prompt: str,
        *,
        agents: list[str] | None = None,
        sns: bool = False,
        task_type: str | None = None,
        no_guild: bool = False,
        **kwargs: Any,
    ) -> ResponseEnvelope:
        """Query multiple agents and synthesize results (consensus pattern).

        All agents receive the same prompt. Results are collected, then
        analyzed by CouncilSynthesizer to produce consensus metrics.
        Output contains both raw responses and synthesis.

        Args:
            prompt: The question or task for all agents
            agents: List of agents to consult (defaults to ["ollama", "lmstudio"])
            sns: Apply SNS-Core compression
            task_type: Override task type inference
            no_guild: Skip guild board tracking
            **kwargs: Additional keyword arguments forwarded to _fan_out().
        """
        envelope = await self._fan_out(
            prompt,
            agents=agents,
            sns=sns,
            task_type=task_type,
            pattern="council",
            no_guild=no_guild,
            **kwargs,
        )

        # Add consensus synthesis
        synthesis: dict[str, Any] | None = None
        try:
            from src.dispatch.council_synthesizer import CouncilSynthesizer

            synthesis = CouncilSynthesizer().synthesize(envelope.output)
            envelope.output = {"responses": envelope.output, "synthesis": synthesis}
        except ImportError:
            logger.debug("CouncilSynthesizer not available — returning raw responses")
        except Exception as exc:
            logger.warning("Council synthesis failed (non-fatal): %s", exc)

        # Store council decision in MemoryPalace for cross-session recall
        # Tags: "council", each agent name, "consensus"/"split" from synthesis
        try:
            import time as _time

            mem = self._get_memory()
            if mem is not None:
                agents_str = ", ".join(agents or ["ollama", "lmstudio"])
                consensus = synthesis.get("consensus_level", "unknown") if synthesis else "unknown"
                confidence = synthesis.get("confidence", 0.0) if synthesis else 0.0
                node_id = f"council:{int(_time.time() * 1000)}"
                tags = ["council", "ask", str(consensus)] + (agents or ["ollama", "lmstudio"])
                mem.add_memory_node(
                    node_id,
                    {
                        "prompt": prompt[:300],
                        "agents": agents or ["ollama", "lmstudio"],
                        "consensus": consensus,
                        "confidence": confidence,
                        "synthesis": synthesis,
                        "success": envelope.success,
                        "timing_ms": envelope.timing_ms,
                    },
                    tags=tags,
                )
        except Exception as exc:
            logger.debug("MemoryPalace council store failed (non-fatal): %s", exc)

        # Broadcast council result to ai_council terminal (best-effort)
        try:
            from src.system.agent_awareness import emit

            consensus = synthesis.get("consensus_level", "?") if synthesis else "?"
            confidence = synthesis.get("confidence", 0.0) if synthesis else 0.0
            agents_str = ", ".join(agents or ["ollama", "lmstudio"])
            emit(
                "ai_council",
                f"Council vote complete — {agents_str} | consensus={consensus} "
                f"confidence={confidence:.0%} | prompt: {prompt[:80]}",
                level="INFO",
                source="mjolnir_council",
            )
        except Exception:
            pass

        return envelope

    async def parallel(
        self,
        prompt: str,
        *,
        agents: list[str] | None = None,
        sns: bool = False,
        task_type: str | None = None,
        **kwargs: Any,
    ) -> ResponseEnvelope:
        """Execute the same prompt on multiple agents simultaneously.

        Unlike council, parallel returns raw results without synthesis.
        Useful for comparing raw outputs side-by-side.
        """
        return await self._fan_out(
            prompt,
            agents=agents,
            sns=sns,
            task_type=task_type,
            pattern="parallel",
            **kwargs,
        )

    async def chain(
        self,
        prompt: str,
        *,
        agents: list[str],
        steps: list[str] | None = None,
        sns: bool = False,
        **kwargs: Any,
    ) -> ResponseEnvelope:
        """Execute a sequential pipeline: output of agent A feeds agent B.

        Args:
            prompt: Initial prompt for the first agent
            agents: Ordered list of agents in the chain
            steps: Optional step labels (e.g., ["analyze", "generate"])
            sns: Apply SNS-Core to initial prompt
            **kwargs: Additional keyword arguments forwarded to each ask().
        """
        start_time = time.monotonic()
        mode = self._context.detect()
        agents_used: list[str] = []
        chain_results: list[dict[str, Any]] = []

        current_input = prompt
        for i, agent in enumerate(agents):
            step_label = steps[i] if steps and i < len(steps) else None

            result = await self.ask(
                agent,
                current_input,
                sns=sns if i == 0 else False,  # SNS only on first step
                task_type=step_label,
                no_guild=True,
                **kwargs,
            )

            canonical = self._resolve_agent(agent)
            agents_used.append(canonical)
            chain_results.append(
                {
                    "step": i + 1,
                    "agent": canonical,
                    "label": step_label,
                    "status": result.status,
                    "output": result.output,
                    "timing_ms": result.timing_ms,
                }
            )

            # Feed output to next agent
            if result.success and result.output:
                if isinstance(result.output, dict):
                    current_input = json.dumps(result.output, ensure_ascii=False, default=str)
                else:
                    current_input = str(result.output)
            else:
                # Chain broken — return partial results
                return ResponseEnvelope(
                    status="partial",
                    success=False,
                    agent="chain",
                    context_mode=str(mode),
                    pattern="chain",
                    sns_applied=sns,
                    output=chain_results,
                    error=f"Chain broken at step {i + 1} ({canonical}): {result.error}",
                    agents_used=agents_used,
                    timing_ms=round((time.monotonic() - start_time) * 1000, 1),
                )

        envelope = ResponseEnvelope(
            status="ok",
            success=True,
            agent="chain",
            context_mode=str(mode),
            pattern="chain",
            sns_applied=sns,
            output=chain_results,
            agents_used=agents_used,
            timing_ms=round((time.monotonic() - start_time) * 1000, 1),
        )
        try:
            from src.system.agent_awareness import emit as _emit

            chain_str = " → ".join(agents_used)
            _emit(
                "tasks",
                f"Chain complete — {chain_str} | steps={len(chain_results)} timing={envelope.timing_ms}ms | prompt: {prompt[:60]}",
                level="INFO",
                source="mjolnir_chain",
            )
        except Exception:
            pass
        return envelope

    async def delegate(
        self,
        prompt: str,
        *,
        agent: str = "auto",
        priority: int = 3,
        sns: bool = False,
        **_kwargs: Any,
    ) -> ResponseEnvelope:
        """Fire-and-forget delegation to guild board.

        Posts the task as a quest without waiting for completion.
        """
        start_time = time.monotonic()
        mode = self._context.detect()
        target = self._resolve_agent(agent)

        # Apply SNS if requested
        effective_prompt = prompt
        if sns:
            effective_prompt, _ = self._apply_sns(prompt)

        guild = self._get_guild()
        if guild is None:
            return ResponseEnvelope.from_error(
                "Guild board not available for delegation",
                agent=target,
                context_mode=str(mode),
                pattern="delegate",
                start_time=start_time,
            )

        try:
            ok, quest_id = await guild.add_quest(
                quest_id=None,
                title=f"MJOLNIR delegate→{target}: {prompt[:60]}",
                description=effective_prompt[:500],
                priority=priority,
                safety_tier="safe",
                tags=["mjolnir", "delegate", target],
            )

            return ResponseEnvelope(
                status="ok" if ok else "error",
                success=ok,
                agent=target,
                context_mode=str(mode),
                pattern="delegate",
                sns_applied=sns,
                output={"delegated": True, "quest_id": quest_id},
                guild_quest_id=quest_id,
                agents_used=[target],
                timing_ms=round((time.monotonic() - start_time) * 1000, 1),
            )
        except Exception as exc:
            return ResponseEnvelope.from_error(
                f"Delegation failed: {exc}",
                agent=target,
                context_mode=str(mode),
                pattern="delegate",
                start_time=start_time,
            )

    async def status(
        self,
        agent: str | None = None,
        *,
        probes: bool = False,
        auto_recover: bool = True,
    ) -> ResponseEnvelope:
        """Report agent availability.

        Args:
            agent: Check a specific agent (or None for all)
            probes: Actually probe agents (HTTP/CLI checks) vs. just list them
            auto_recover: When probing, attempt to start recoverable agents
                          (e.g. Ollama) if found offline.  Default True.
        """
        start_time = time.monotonic()
        mode = self._context.detect()

        if probes:
            if agent:
                # Use probe_with_recovery for recoverable agents (e.g. Ollama) so
                # a single-agent status check also attempts to start it if offline.
                if auto_recover and agent in self._registry.RECOVERABLE_AGENTS:
                    result = await self._registry.probe_with_recovery(agent, auto_recover=True)
                else:
                    result = await self._registry.probe_one(agent)
                output = result.to_dict()
            else:
                # auto_recover: Ollama (and future recoverable agents) are started
                # automatically if found offline during the probe sweep.
                results = await self._registry.probe_all(auto_recover=auto_recover)
                output = {name: r.to_dict() for name, r in results.items()}
        else:
            # Just list known agents without probing
            output = {
                name: {
                    "agent": name,
                    "display_name": self._registry.get_display_name(name),
                    "status": "unknown",
                    "probe_types": [p[0].__name__ for p in probes_list],
                }
                for name, probes_list in AGENT_PROBES.items()
                if agent is None or name == agent
            }

        return ResponseEnvelope(
            status="ok",
            success=True,
            agent=agent or "all",
            context_mode=str(mode),
            pattern="status",
            output=output,
            agents_used=list(AGENT_PROBES.keys()) if not agent else [agent],
            timing_ms=round((time.monotonic() - start_time) * 1000, 1),
        )

    async def queue(
        self,
        prompt: str,
        *,
        agent: str = "auto",
        task_type: str | None = None,
        priority: str = "NORMAL",
        sns: bool = False,
        _context_file: str | None = None,
    ) -> ResponseEnvelope:
        """Queue a task to BackgroundTaskOrchestrator for persistent async execution.

        Unlike ask() which waits for a result, queue() returns immediately
        with a task_id. The task survives process restarts (SQLite-backed).

        Args:
            prompt: Task description
            agent: Target agent (default "auto")
            task_type: Override task type (default: inferred)
            priority: CRITICAL/HIGH/NORMAL/LOW/BACKGROUND
            sns: Apply SNS-Core compression
            context_file: File path to include as context
        """
        start_time = time.monotonic()
        mode = self._context.detect()
        target = self._resolve_agent(agent)

        effective_prompt = prompt
        if sns:
            effective_prompt, _ = self._apply_sns(prompt)

        effective_type = task_type or _infer_task_type(prompt)

        try:
            from src.orchestration.background_task_orchestrator import \
                dispatch_task_cli

            result = await dispatch_task_cli(
                prompt=effective_prompt,
                target=target,
                task_type=effective_type,
                priority=priority.lower(),
            )

            envelope = ResponseEnvelope.wrap(
                result,
                agent=target,
                context_mode=str(mode),
                pattern="queue",
                sns_applied=sns,
                start_time=start_time,
            )
            try:
                from src.system.agent_awareness import emit as _emit

                task_id = result.get("task_id", "?") if isinstance(result, dict) else "?"
                _emit(
                    "tasks",
                    f"Queued task → {target} | id={task_id} priority={priority} type={effective_type} | {prompt[:60]}",
                    level="INFO",
                    source="mjolnir_queue",
                )
            except Exception:
                pass
            return envelope
        except ImportError:
            return ResponseEnvelope.from_error(
                "BackgroundTaskOrchestrator not available",
                agent=target,
                context_mode=str(mode),
                pattern="queue",
                start_time=start_time,
            )
        except Exception as exc:
            return ResponseEnvelope.from_error(
                f"Queue failed: {exc}",
                agent=target,
                context_mode=str(mode),
                pattern="queue",
                start_time=start_time,
            )

    # ── Task / quest polling ─────────────────────────────────────────────────

    def poll_queue(self, task_id: str) -> dict[str, Any]:
        """Check the status of a queued background task (from queue()).

        Args:
            task_id: The task_id returned in the queue() response envelope output.

        Returns:
            Task status dict (status, result, error, etc.) or {"error": "not found"}.
        """
        try:
            from src.orchestration.background_task_orchestrator import \
                task_status_cli

            return task_status_cli(task_id)
        except Exception as exc:
            return {"error": f"poll_queue failed: {exc}", "task_id": task_id}

    async def poll_delegate(self, quest_id: str) -> dict[str, Any]:
        """Check the status of a delegated guild quest (from delegate()).

        Args:
            quest_id: The quest_id returned in the delegate() response envelope output.

        Returns:
            Quest status dict or {"error": "not found"}.
        """
        guild = self._get_guild()
        if guild is None:
            return {"error": "GuildBoard unavailable", "quest_id": quest_id}
        try:
            quest = await guild.get_quest(quest_id)
            if quest is None:
                return {"error": "Quest not found", "quest_id": quest_id}
            if hasattr(quest, "to_dict"):
                return quest.to_dict()
            return (
                dict(quest)
                if hasattr(quest, "__iter__")
                else {"quest_id": quest_id, "raw": str(quest)}
            )
        except Exception as exc:
            return {"error": f"poll_delegate failed: {exc}", "quest_id": quest_id}

    # ── SkyClaw gateway lifecycle ────────────────────────────────────────────

    async def skyclaw_status(self) -> ResponseEnvelope:
        """Return SkyClaw gateway status (binary + HTTP health).

        Probes the SkyClaw binary on disk and queries the gateway HTTP API
        to determine whether the daemon is running.

        Returns:
            ResponseEnvelope wrapping a dict with keys:
            binary, gateway_url, running, health, status.
        """
        start_time = time.monotonic()
        mode = self._context.detect()

        try:
            from src.integrations.skyclaw_gateway_client import \
                get_skyclaw_gateway_client
        except ImportError as exc:
            return ResponseEnvelope(
                status="unavailable",
                success=False,
                agent="skyclaw",
                context_mode=str(mode),
                pattern="skyclaw_status",
                error=f"skyclaw_gateway_client import failed: {exc}",
                timing_ms=round((time.monotonic() - start_time) * 1000, 1),
            )

        try:
            client = get_skyclaw_gateway_client()
            summary = await client.summary()
            running = bool(summary.get("running"))
            return ResponseEnvelope(
                status="ok" if running else "offline",
                success=True,
                agent="skyclaw",
                context_mode=str(mode),
                pattern="skyclaw_status",
                output=summary,
                timing_ms=round((time.monotonic() - start_time) * 1000, 1),
            )
        except Exception as exc:
            logger.warning("skyclaw_status failed: %s", exc)
            return ResponseEnvelope(
                status="error",
                success=False,
                agent="skyclaw",
                context_mode=str(mode),
                pattern="skyclaw_status",
                error=str(exc),
                timing_ms=round((time.monotonic() - start_time) * 1000, 1),
            )

    async def skyclaw_start(self) -> ResponseEnvelope:
        """Start the SkyClaw gateway daemon.

        Spawns ``skyclaw start`` and waits up to 15 seconds for the gateway
        to become ready.

        Returns:
            ResponseEnvelope with status "ok" on success or "failed"/"error"
            on failure.  Output dict includes binary info and gateway_url.
        """
        start_time = time.monotonic()
        mode = self._context.detect()

        try:
            from src.integrations.skyclaw_gateway_client import \
                get_skyclaw_gateway_client
        except ImportError as exc:
            return ResponseEnvelope(
                status="unavailable",
                success=False,
                agent="skyclaw",
                context_mode=str(mode),
                pattern="skyclaw_start",
                error=f"skyclaw_gateway_client import failed: {exc}",
                timing_ms=round((time.monotonic() - start_time) * 1000, 1),
            )

        try:
            client = get_skyclaw_gateway_client()
            binary = client.binary_info()
            if not binary.get("found"):
                return ResponseEnvelope(
                    status="error",
                    success=False,
                    agent="skyclaw",
                    context_mode=str(mode),
                    pattern="skyclaw_start",
                    error="SkyClaw binary not found — cannot start gateway",
                    output=binary,
                    timing_ms=round((time.monotonic() - start_time) * 1000, 1),
                )

            ok = await client.start_gateway(wait=True)
            return ResponseEnvelope(
                status="ok" if ok else "failed",
                success=ok,
                agent="skyclaw",
                context_mode=str(mode),
                pattern="skyclaw_start",
                output={"gateway_url": client.gateway_url, **binary},
                timing_ms=round((time.monotonic() - start_time) * 1000, 1),
            )
        except Exception as exc:
            logger.warning("skyclaw_start failed: %s", exc)
            return ResponseEnvelope(
                status="error",
                success=False,
                agent="skyclaw",
                context_mode=str(mode),
                pattern="skyclaw_start",
                error=str(exc),
                timing_ms=round((time.monotonic() - start_time) * 1000, 1),
            )

    async def skyclaw_stop(self) -> ResponseEnvelope:
        """Stop the SkyClaw gateway daemon (session-managed).

        Only terminates the process started by skyclaw_start() in the same
        session.  To stop an externally-started gateway, use the OS or the
        SkyClaw CLI directly.

        Returns:
            ResponseEnvelope with status "ok" on success or "error" on failure.
        """
        start_time = time.monotonic()
        mode = self._context.detect()

        try:
            from src.integrations.skyclaw_gateway_client import \
                get_skyclaw_gateway_client
        except ImportError as exc:
            return ResponseEnvelope(
                status="unavailable",
                success=False,
                agent="skyclaw",
                context_mode=str(mode),
                pattern="skyclaw_stop",
                error=f"skyclaw_gateway_client import failed: {exc}",
                timing_ms=round((time.monotonic() - start_time) * 1000, 1),
            )

        try:
            client = get_skyclaw_gateway_client()
            await client.stop_gateway()
            return ResponseEnvelope(
                status="ok",
                success=True,
                agent="skyclaw",
                context_mode=str(mode),
                pattern="skyclaw_stop",
                output={"gateway_url": client.gateway_url},
                timing_ms=round((time.monotonic() - start_time) * 1000, 1),
            )
        except Exception as exc:
            logger.warning("skyclaw_stop failed: %s", exc)
            return ResponseEnvelope(
                status="error",
                success=False,
                agent="skyclaw",
                context_mode=str(mode),
                pattern="skyclaw_stop",
                error=str(exc),
                timing_ms=round((time.monotonic() - start_time) * 1000, 1),
            )

    async def drain(self, limit: int = 5) -> ResponseEnvelope:
        """Drain pending guild quests by executing them through MJOLNIR.

        Pulls OPEN quests from GuildBoard, claims them atomically,
        routes each through ask(), and marks complete/failed.

        Args:
            limit: Maximum number of quests to process in this cycle.

        Returns:
            ResponseEnvelope with list of per-quest results.
        """
        start_time = time.monotonic()
        mode = self._context.detect()

        try:
            from src.dispatch.quest_executor_bridge import QuestExecutorBridge

            bridge = QuestExecutorBridge(protocol=self)
            results = await bridge.drain(limit=limit)

            return ResponseEnvelope(
                status="ok",
                success=True,
                agent="drain",
                context_mode=str(mode),
                pattern="drain",
                output=results,
                agents_used=list({r.get("agent", "unknown") for r in results}),
                timing_ms=round((time.monotonic() - start_time) * 1000, 1),
            )
        except ImportError:
            return ResponseEnvelope.from_error(
                "QuestExecutorBridge not available",
                agent="drain",
                context_mode=str(mode),
                pattern="drain",
                start_time=start_time,
            )
        except Exception as exc:
            return ResponseEnvelope.from_error(
                f"Drain failed: {exc}",
                agent="drain",
                context_mode=str(mode),
                pattern="drain",
                start_time=start_time,
            )
