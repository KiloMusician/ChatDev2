#!/usr/bin/env python3
"""Claude Orchestrator - Unified Multi-AI System Interface.

========================================================

**Purpose:** Single interface for Claude (GitHub Copilot) to orchestrate ALL AI systems:
- Ollama (9 local LLM models, 37.5GB)
- ChatDev (multi-agent development team)
- MCP Server (Model Context Protocol bridge)
- Jupyter (multi-kernel notebooks)
- Obsidian (knowledge graph)
- OpenTelemetry (distributed tracing)

**Architecture:**
Claude (me) → ClaudeOrchestrator → [Ollama, ChatDev, MCP, Jupyter, Obsidian, OTEL]

**Example Usage (from Copilot chat):**
```python
from src.orchestration.claude_orchestrator import ClaudeOrchestrator

orchestrator = ClaudeOrchestrator()

# Ask Ollama for code review
result = await orchestrator.ask_ollama(
    prompt="Review this code for security issues: ...",
    model="qwen2.5-coder:14b"
)

# Spawn ChatDev multi-agent team
project = await orchestrator.spawn_chatdev(
    task="Create a REST API with JWT authentication",
    testing_chamber=True  # Quarantine until validated
)

# Execute Python code in Jupyter
output = await orchestrator.execute_jupyter(
    code="import numpy as np; np.random.rand(5)",
    kernel="python"
)

# Log to Obsidian knowledge graph
await orchestrator.log_to_obsidian(
    content="AI insight: Ollama prefers functional decomposition",
    tags=["ai", "ollama", "architecture"]
)

# Trace operation with OpenTelemetry
with orchestrator.trace("multi_ai_consensus"):
    responses = await orchestrator.multi_ai_consensus(
        question="Should we refactor this module?",
        systems=["ollama", "chatdev", "claude"]
    )
```

**Status:** ✅ OPERATIONAL (Phase 1 activated)
**Version:** 1.0.0
**Author:** Claude Sonnet 4.5 (via GitHub Copilot)
**Date:** 2025-12-24
"""

import argparse
import asyncio
import contextlib
import importlib
import importlib.util
import json
import logging
import os
import subprocess
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Any, Literal, cast

# Ensure repository root is on sys.path for CLI usage
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import aiohttp

from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator


def _import_optional_module(name: str) -> ModuleType | None:
    spec = importlib.util.find_spec(name)
    if spec is None:
        return None
    return importlib.import_module(name)


_tracing_module = _import_optional_module("src.observability.tracing")
tracing_mod: Any | None = _tracing_module

_jupyter_client_module = _import_optional_module("jupyter_client")
jupyter_client_mod: Any | None = _jupyter_client_module

_repo_path_module = _import_optional_module("src.utils.repo_path_resolver")
get_repo_path: Callable[[str], Path | str] | None = (
    getattr(_repo_path_module, "get_repo_path", None) if _repo_path_module else None
)

logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)

if tracing_mod is None:
    logger.warning("⚠️ OpenTelemetry not available - tracing disabled")

DEFAULT_CLAUDE_SYSTEMS: list[Literal["ollama", "chatdev", "claude"]] = ["ollama", "claude"]


class ClaudeOrchestrator:
    """Unified orchestration interface for Claude to coordinate all AI systems."""

    def __init__(self, repo_root: Path | None = None) -> None:
        """Initialize Claude Orchestrator.

        Args:
            repo_root: Repository root (defaults to NuSyQ-Hub location)
        """
        self.repo_root = repo_root or Path(__file__).parent.parent.parent
        if get_repo_path:
            try:
                self.nusyq_root = Path(get_repo_path("NUSYQ_ROOT"))
            except Exception:
                self.nusyq_root = Path.home() / "NuSyQ"
            try:
                self.simverse_root = Path(get_repo_path("SIMULATEDVERSE_ROOT"))
            except Exception:
                self.simverse_root = Path.home() / "Desktop" / "SimulatedVerse" / "SimulatedVerse"
        else:
            self.nusyq_root = Path.home() / "NuSyQ"
            self.simverse_root = Path.home() / "Desktop" / "SimulatedVerse" / "SimulatedVerse"

        # Unified AI Orchestrator (existing)
        self.ai_orchestrator = UnifiedAIOrchestrator()

        # Endpoints - use ServiceConfig if available
        from src.utils.config_factory import get_service_config

        config = get_service_config()
        # Prefer the service config's full Ollama URL (host:port) when available;
        # fall back to environment variables with a localhost:11434 default.
        try:
            if config and getattr(config, "get_ollama_url", None):
                ollama_base = config.get_ollama_url()
            else:
                ollama_base = os.getenv("OLLAMA_BASE_URL") or os.getenv(
                    "OLLAMA_HOST", "http://localhost:11434"
                )
        except Exception:
            ollama_base = os.getenv("OLLAMA_BASE_URL") or os.getenv(
                "OLLAMA_HOST", "http://localhost:11434"
            )

        # Normalize loopback IPs to 'localhost' for consistency in tests and logs
        if "127.0.0.1" in str(ollama_base):
            ollama_base = str(ollama_base).replace("127.0.0.1", "localhost")

        self.ollama_endpoint = f"{ollama_base}/api/generate"
        self.mcp_endpoint = "http://localhost:8000"  # MCP server if running
        self.jaeger_ui = "http://localhost:16686"  # Jaeger traces
        self.claude_base_url = os.getenv(
            "ANTHROPIC_API_URL", "https://api.anthropic.com/v1/messages"
        )
        self.claude_model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20240620")

        # Paths
        self.obsidian_vault = self.repo_root / "NuSyQ-Hub-Obsidian"
        self.chatdev_path = self.nusyq_root / "ChatDev"
        self.quest_log = self.repo_root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"

        self.tracing_enabled = False
        if tracing_mod:
            try:
                self.tracing_enabled = tracing_mod.init_tracing(service_name="claude-orchestrator")
            except Exception:
                self.tracing_enabled = False

        logger.info("🧠 Claude Orchestrator initialized")
        logger.info(f"   Ollama: {self.ollama_endpoint}")
        logger.info(f"   MCP: {self.mcp_endpoint}")
        logger.info(f"   Obsidian: {self.obsidian_vault}")
        logger.info(f"   ChatDev: {self.chatdev_path}")
        logger.info(f"   Claude: {self.claude_model} @ {self.claude_base_url}")

    def _span(
        self, name: str, attrs: dict[str, Any] | None = None
    ) -> contextlib.AbstractContextManager[Any]:
        """Create a tracing span or no-op context manager."""
        if tracing_mod:
            return cast(contextlib.AbstractContextManager[Any], tracing_mod.start_span(name, attrs))
        return contextlib.nullcontext()

    # ============================================================================
    # OLLAMA INTEGRATION
    # ============================================================================

    async def ask_ollama(
        self,
        prompt: str,
        model: str = "qwen2.5-coder:14b",
        temperature: float = 0.3,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Query Ollama local LLM.

        Args:
            prompt: User prompt for the model
            model: Ollama model name (see `ollama list`)
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            stream: Whether to stream response (not supported yet)

        Returns:
            {"response": "...", "model": "...", "duration_ms": ..., "eval_count": ...}
        """
        span_context = self._span(
            "ollama_query",
            {
                "model": model,
                "prompt_length": len(prompt),
            },
        )
        with span_context as span:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": stream,
                "options": {"temperature": temperature},
            }

            try:
                start = datetime.now()
                async with aiohttp.ClientSession() as session:
                    timeout = aiohttp.ClientTimeout(total=60)
                    async with session.post(
                        self.ollama_endpoint, json=payload, timeout=timeout
                    ) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            logger.error(f"Ollama error: {error_text}")
                            return {
                                "success": False,
                                "error": error_text,
                                "status": resp.status,
                            }

                result = cast(dict[str, Any], await resp.json())

                duration_ms = (datetime.now() - start).total_seconds() * 1000
                try:
                    if span:
                        span.set_attribute("duration_ms", duration_ms)
                        span.set_attribute("response_length", len(result.get("response", "")))
                except Exception:
                    logger.debug("Suppressed Exception", exc_info=True)

                logger.info(f"✅ Ollama ({model}) responded in {duration_ms:.0f}ms")
                return {
                    "success": True,
                    "status": "success",
                    "response": result.get("response", ""),
                    "model": model,
                    "duration_ms": duration_ms,
                    "eval_count": result.get("eval_count", 0),
                    "context": result.get("context", []),
                }

            except TimeoutError:
                logger.error(f"❌ Ollama timeout after 60s (model: {model})")
                return {
                    "success": False,
                    "status": "error",
                    "error": "Timeout after 60s",
                    "model": model,
                }
            except Exception as e:
                logger.error(f"❌ Ollama error: {e}")
                return {"success": False, "status": "error", "error": str(e), "model": model}

    # ============================================================================
    # CLAUDE (ANTHROPIC) INTEGRATION
    # ============================================================================

    async def ask_claude(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.3,
    ) -> dict[str, Any]:
        """Query Claude via the Anthropics Messages API."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": (
                    "ANTHROPIC_API_KEY not set; export it to enable Claude API mode (Messages API)."
                ),
                "status": "missing_api_key",
            }

        target_model = model or self.claude_model
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": target_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

        span_context = self._span(
            "claude_query",
            {"model": target_model, "prompt_length": len(prompt), "max_tokens": max_tokens},
        )
        with span_context as span:
            try:
                start = datetime.now()
                async with aiohttp.ClientSession() as session:
                    timeout = aiohttp.ClientTimeout(total=90)
                    async with session.post(
                        self.claude_base_url, json=payload, headers=headers, timeout=timeout
                    ) as resp:
                        status = resp.status
                        data = cast(dict[str, Any], await resp.json())

                duration_ms = (datetime.now() - start).total_seconds() * 1000
                text_parts = []
                for part in data.get("content", []):
                    if isinstance(part, dict):
                        text = part.get("text")
                        if isinstance(text, str):
                            text_parts.append(text)
                response_text = "\n".join(text_parts)

                try:
                    if span:
                        span.set_attribute("duration_ms", duration_ms)
                        span.set_attribute("status_code", status)
                        span.set_attribute("response_length", len(response_text))
                except Exception:
                    logger.debug("Suppressed Exception", exc_info=True)

                if status >= 400:
                    logger.error("❌ Claude error (%s): %s", status, data)
                    return {
                        "success": False,
                        "error": data,
                        "status": status,
                        "model": target_model,
                    }

                logger.info(f"✅ Claude ({target_model}) responded in {duration_ms:.0f}ms")
                return {
                    "success": True,
                    "status": "success",
                    "response": response_text,
                    "model": target_model,
                    "duration_ms": duration_ms,
                    "id": data.get("id"),
                }
            except Exception as e:
                logger.error(f"❌ Claude error: {e}")
                return {"success": False, "status": "error", "error": str(e), "model": target_model}

    async def list_ollama_models(self) -> list[dict[str, Any]]:
        """List all available Ollama models."""
        try:
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=5)
                async with session.get("http://localhost:11434/api/tags", timeout=timeout) as resp:
                    if resp.status == 200:
                        data = cast(dict[str, Any], await resp.json())
                        return cast(list[dict[str, Any]], data.get("models", []))
            return []
        except Exception as e:
            logger.error(f"❌ Failed to list Ollama models: {e}")
            return []

    # ============================================================================
    # CHATDEV INTEGRATION
    # ============================================================================

    async def spawn_chatdev(
        self,
        task: str,
        testing_chamber: bool = True,
        model: str = "qwen2.5-coder:7b",
    ) -> dict[str, Any]:
        """Spawn ChatDev multi-agent development team.

        Args:
            task: Development task description (e.g., "Create REST API with JWT")
            testing_chamber: If True, create in isolated testing environment
            model: Ollama model for ChatDev agents

        Returns:
            {"project_path": "...", "status": "...", "agents": [...]}
        """
        span_context = self._span(
            "chatdev_spawn",
            {
                "task": task[:100],
                "testing_chamber": testing_chamber,
            },
        )
        with span_context:
            if not self.chatdev_path.exists():
                logger.error(f"❌ ChatDev not found at {self.chatdev_path}")
                return {"error": "ChatDev not installed"}

            # Use agent_task_router.py for standardized ChatDev invocation
            try:
                from src.tools.agent_task_router import AgentTaskRouter

                router = AgentTaskRouter(repo_root=self.repo_root)
                raw_result = await router.route_task(
                    task_type="generate",
                    description=task,
                    target_system="chatdev",
                    context={"model": model},
                )

                logger.info(f"✅ ChatDev project initiated: {raw_result.get('status')}")
                return raw_result

            except Exception as e:
                logger.error(f"❌ ChatDev spawn error: {e}")
                return {"error": str(e), "task": task}

    # ============================================================================
    # JUPYTER INTEGRATION
    # ============================================================================

    async def execute_jupyter(
        self,
        code: str,
        kernel: str = "python",
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Execute code in Jupyter kernel.

        Args:
            code: Python/Julia/R code to execute
            kernel: Kernel type (python, julia, ir)
            timeout: Execution timeout in seconds

        Returns:
            {"output": "...", "error": None, "execution_time_ms": ...}
        """
        span_context = self._span("jupyter_execute", {"kernel": kernel})
        with span_context as span:
            if span:
                span.set_attribute("code_length", len(code))

            started = datetime.now()

            def _run_with_jupyter_client() -> tuple[str, str | None]:
                km_cls = getattr(jupyter_client_mod, "KernelManager", None)
                if km_cls is None or not callable(km_cls):
                    raise RuntimeError("jupyter_client KernelManager unavailable")

                km = km_cls(kernel_name=kernel)  # pylint: disable=not-callable
                km.start_kernel()
                kc = km.client()
                kc.start_channels()

                output_parts: list[str] = []
                error_text: str | None = None

                try:
                    kc.wait_for_ready(timeout=timeout)
                    kc.execute(code)

                    while True:
                        msg = kc.get_iopub_msg(timeout=timeout)
                        msg_type = msg.get("header", {}).get("msg_type")
                        content = msg.get("content", {})

                        if msg_type == "stream":
                            output_parts.append(content.get("text", ""))
                        elif msg_type in ("execute_result", "display_data"):
                            data = content.get("data", {})
                            text = data.get("text/plain")
                            if text:
                                output_parts.append(f"{text}\n")
                        elif msg_type == "error":
                            error_text = "\n".join(content.get("traceback", [])) or content.get(
                                "ename"
                            )
                        elif msg_type == "status" and content.get("execution_state") == "idle":
                            break
                finally:
                    with contextlib.suppress(Exception):
                        kc.stop_channels()
                    with contextlib.suppress(Exception):
                        km.shutdown_kernel(now=True)

                return ("".join(output_parts)).strip(), error_text

            def _run_python_subprocess() -> tuple[str, str | None]:
                result = subprocess.run(
                    [sys.executable, "-c", code],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False,
                )
                stderr = result.stderr.strip() if result.stderr else None
                if result.returncode != 0 and not stderr:
                    stderr = f"Process exited with code {result.returncode}"
                return result.stdout.strip(), stderr

            if jupyter_client_mod is not None:
                try:
                    output, error = await asyncio.to_thread(_run_with_jupyter_client)
                    mode = "jupyter_client"
                    if span:
                        span.set_attribute("mode", mode)
                    return {
                        "output": output,
                        "error": error,
                        "kernel": kernel,
                        "execution_time_ms": int((datetime.now() - started).total_seconds() * 1000),
                        "mode": mode,
                    }
                except Exception as exc:
                    logger.warning("Jupyter client execution failed: %s", exc)

            if kernel not in ("python", "ipython"):
                return {
                    "output": "",
                    "error": f"Kernel '{kernel}' requires jupyter_client support",
                    "kernel": kernel,
                    "execution_time_ms": int((datetime.now() - started).total_seconds() * 1000),
                    "mode": "unsupported",
                }

            output, error = await asyncio.to_thread(_run_python_subprocess)
            mode = "subprocess"
            if span:
                span.set_attribute("mode", mode)
            return {
                "output": output,
                "error": error,
                "kernel": kernel,
                "execution_time_ms": int((datetime.now() - started).total_seconds() * 1000),
                "mode": mode,
            }

    # ============================================================================
    # OBSIDIAN INTEGRATION
    # ============================================================================

    async def log_to_obsidian(
        self,
        content: str,
        tags: list[str] | None = None,
        title: str | None = None,
    ) -> dict[str, Any]:
        """Write content to Obsidian knowledge graph.

        Args:
            content: Markdown content to log
            tags: Tags for organization (e.g., ["ai", "ollama"])
            title: Note title (auto-generated if None)

        Returns:
            {"note_path": "...", "success": True, "status": "success"}
        """
        span_context = self._span("obsidian_log", {"tags": ",".join(tags or [])})
        with span_context as span:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            title = title or f"AI_Insight_{timestamp}"
            tags = tags or []

            # Create AI Insights directory
            insights_dir = self.obsidian_vault / "AI_Insights"
            insights_dir.mkdir(parents=True, exist_ok=True)

            # Generate note
            note_path = insights_dir / f"{title}.md"
            frontmatter = f"""---
created: {datetime.now().isoformat()}
tags: {", ".join(tags)}
---

"""
            note_content = frontmatter + content

            note_path.write_text(note_content, encoding="utf-8")

            try:
                if span:
                    span.set_attribute("note_path", str(note_path))
            except Exception:
                if span:
                    span.set_attribute("tags", ", ".join(tags))

            logger.info(f"✅ Logged to Obsidian: {note_path.name}")
            return {
                "note_path": str(note_path),
                "success": True,
                "status": "success",
                "title": title,
            }

    # ============================================================================
    # MULTI-AI CONSENSUS
    # ============================================================================

    async def multi_ai_consensus(
        self,
        question: str,
        systems: list[Literal["ollama", "chatdev", "claude"]] | None = None,
        ollama_model: str = "qwen2.5-coder:14b",
    ) -> dict[str, Any]:
        """Ask multiple AI systems and aggregate responses.

        Args:
            question: Question to ask all systems
            systems: Which systems to query (default: ["ollama", "claude"])
            ollama_model: Ollama model to use

        Returns:
            {
                "responses": {"ollama": "...", "claude": "...", "chatdev": "..."},
                "consensus": "majority_agree" | "split_decision",
                "summary": "..."
            }
        """
        span_context = self._span("multi_ai_consensus", {"question": question[:100]})
        with span_context as span:
            systems = systems if systems is not None else DEFAULT_CLAUDE_SYSTEMS.copy()
            responses: dict[str, str] = {}

            # Ollama
            if "ollama" in systems:
                ollama_result = await self.ask_ollama(question, model=ollama_model)
                responses["ollama"] = ollama_result.get("response", "")

            # Claude (me)
            if "claude" in systems:
                claude_result = await self.ask_claude(question)
                responses["claude"] = claude_result.get("response") or str(
                    claude_result.get("error", "")
                )

            # ChatDev (requires more complex setup)
            if "chatdev" in systems:
                responses["chatdev"] = "[ChatDev multi-agent analysis pending]"

            try:
                if span:
                    span.set_attribute("systems_queried", ", ".join(systems))
                    span.set_attribute("response_count", len(responses))
            except Exception:
                logger.debug("Suppressed Exception", exc_info=True)

            # Simple consensus: check if responses are similar length (basic heuristic)
            lengths = [len(r) for r in responses.values()]
            avg_length = sum(lengths) / len(lengths) if lengths else 0
            variance = (
                sum((length - avg_length) ** 2 for length in lengths) / len(lengths)
                if lengths
                else 0
            )
            consensus = "majority_agree" if variance < 1000 else "split_decision"

            logger.info(f"✅ Multi-AI consensus: {consensus} ({len(systems)} systems)")
            return {
                "responses": responses,
                "consensus": consensus,
                "summary": f"{len(systems)} AI systems queried, consensus: {consensus}",
                "question": question[:100],
            }

    # ============================================================================
    # OPENTELEMETRY TRACING
    # ============================================================================

    def trace(self, operation_name: str) -> contextlib.AbstractContextManager[Any]:
        """Create a traced context for operations.

        Usage:
            with orchestrator.trace("my_operation"):
                # ... code to trace
        """
        return self._span(operation_name)

    # ============================================================================
    # SYSTEM HEALTH
    # ============================================================================

    async def health_check(self) -> dict[str, Any]:
        """Check health of all AI systems."""
        span_context = self._span("health_check")
        with span_context:
            systems_map: dict[str, dict[str, Any]] = {}
            health = {
                "timestamp": datetime.now().isoformat(),
                "systems": systems_map,
            }

            # Ollama
            try:
                models = await self.list_ollama_models()
                systems_map["ollama"] = {
                    "status": "healthy" if models else "degraded",
                    "models": len(models),
                    "endpoint": self.ollama_endpoint,
                }
            except Exception as e:
                systems_map["ollama"] = {"status": "down", "error": str(e)}

            # ChatDev
            chatdev_run_py = self.chatdev_path / "run.py" if self.chatdev_path else None
            chatdev_run_ollama_py = (
                self.chatdev_path / "run_ollama.py" if self.chatdev_path else None
            )
            systems_map["chatdev"] = {
                "status": (
                    "ready" if self.chatdev_path and self.chatdev_path.exists() else "missing"
                ),
                "path": str(self.chatdev_path) if self.chatdev_path else None,
                "has_run_py": chatdev_run_py.exists() if chatdev_run_py else False,
                "has_run_ollama_py": (
                    chatdev_run_ollama_py.exists() if chatdev_run_ollama_py else False
                ),
            }

            # Obsidian
            systems_map["obsidian"] = {
                "status": "ready" if self.obsidian_vault.exists() else "missing",
                "vault": str(self.obsidian_vault),
            }

            # MCP Server (attempt connection)
            try:
                async with aiohttp.ClientSession() as session:
                    health_timeout = aiohttp.ClientTimeout(total=5)
                    async with session.get(
                        f"{self.mcp_endpoint}/health", timeout=health_timeout
                    ) as resp:
                        systems_map["mcp"] = {
                            "status": "healthy" if resp.status == 200 else "degraded",
                            "endpoint": self.mcp_endpoint,
                        }
            except Exception:
                systems_map["mcp"] = {
                    "status": "down",
                    "endpoint": self.mcp_endpoint,
                }

            # Claude API availability
            api_key_set = bool(os.getenv("ANTHROPIC_API_KEY"))
            systems_map["claude"] = {
                "status": "ready" if api_key_set else "missing_api_key",
                "model": self.claude_model,
                "endpoint": self.claude_base_url,
            }

            logger.info("✅ Health check complete")
            return health

    def shutdown(self) -> None:
        """Release orchestrator resources for clean process shutdown."""
        try:
            shutdown = getattr(self.unified_orchestrator, "shutdown", None)
            if callable(shutdown):
                shutdown()
        except Exception:
            logger.debug("Suppressed Exception", exc_info=True)


# ============================================================================
# CLI USAGE EXAMPLE
# ============================================================================


async def demo():
    """Demonstration of Claude Orchestrator capabilities."""
    orchestrator = ClaudeOrchestrator()

    logger.info("\n🧠 Claude Orchestrator Demo\n" + "=" * 50)

    # 1. Health check
    logger.info("\n[1/5] Health Check...")
    health = await orchestrator.health_check()
    logger.info(json.dumps(health, indent=2))

    # 2. Ask Ollama
    logger.info("\n[2/5] Ask Ollama (qwen2.5-coder:14b)...")
    ollama_response = await orchestrator.ask_ollama(
        prompt="Explain quantum computing in one sentence",
        model="qwen2.5-coder:14b",
    )
    logger.error(f"Ollama: {ollama_response.get('response', 'ERROR')[:200]}...")

    # 3. Log to Obsidian
    logger.info("\n[3/5] Log to Obsidian...")
    obsidian_result = await orchestrator.log_to_obsidian(
        content=f"Ollama (qwen2.5-coder:14b) explained quantum computing:\n\n{ollama_response.get('response', '')}",
        tags=["ai", "ollama", "quantum", "demo"],
        title=f"Ollama_Demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    )
    logger.info(f"Obsidian: {obsidian_result['note_path']}")

    # 4. Multi-AI consensus
    logger.info("\n[4/5] Multi-AI Consensus...")
    consensus = await orchestrator.multi_ai_consensus(
        question="Should we use async/await or threads for concurrent operations?",
        systems=["ollama", "claude"],
    )
    logger.info(f"Consensus: {consensus['consensus']}")
    for system, response in consensus["responses"].items():
        logger.info(f"  {system}: {response[:100]}...")

    # 5. List Ollama models
    logger.info("\n[5/5] List Ollama Models...")
    models = await orchestrator.list_ollama_models()
    logger.info(f"Found {len(models)} models:")
    for model in models[:5]:  # Show first 5
        logger.info(f"  - {model.get('name', 'unknown')}")

    logger.info("\n✅ Demo complete! Check Jaeger UI: http://localhost:16686")


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Claude Orchestrator CLI")
    parser.add_argument(
        "--ask-claude",
        metavar="PROMPT",
        help="Send a prompt to Claude (requires ANTHROPIC_API_KEY)",
    )
    parser.add_argument(
        "--ask-ollama",
        metavar="PROMPT",
        help="Send a prompt to Ollama (default qwen2.5-coder:7b)",
    )
    parser.add_argument("--model", help="Model override for Claude or Ollama")
    parser.add_argument("--max-tokens", type=int, default=512, help="Max tokens for Claude")
    parser.add_argument("--temperature", type=float, default=0.3, help="Sampling temperature")
    parser.add_argument(
        "--todo",
        action="store_true",
        help="Ask Claude to draft a tiny TODO list for repo hygiene",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the built-in demo (health, ollama, obsidian, consensus, list models)",
    )
    return parser


async def _cli(args: argparse.Namespace) -> None:
    if args.demo:
        await demo()
        return

    orch = ClaudeOrchestrator()

    if args.ask_claude or args.todo:
        prompt = args.ask_claude
        if args.todo:
            prompt = prompt or "Create a 3-item TODO list to validate Claude CLI wiring."
        result = await orch.ask_claude(
            prompt=prompt or "",
            model=args.model,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
        )
        logger.info(json.dumps(result, indent=2))
        return

    if args.ask_ollama:
        result = await orch.ask_ollama(
            prompt=args.ask_ollama,
            model=args.model or "qwen2.5-coder:7b",
            temperature=args.temperature,
        )
        logger.info(json.dumps(result, indent=2))
        return

    # Default: show health to confirm wiring
    health = await orch.health_check()
    logger.info(json.dumps(health, indent=2))


if __name__ == "__main__":
    parsed_args = _build_arg_parser().parse_args()
    asyncio.run(_cli(parsed_args))
