"""
╔══════════════════════════════════════════════════════════════════════════╗
║ ΞNuSyQ Multi-Model Consensus Orchestrator                               ║
╠══════════════════════════════════════════════════════════════════════════╣
║ FILE-ID: nusyq.consensus.orchestrator                                   ║
║ TYPE: Python Module                                                     ║
║ STATUS: Experimental                                                    ║
║ VERSION: 1.0.0                                                          ║
║ TAGS: [consensus, multi-model, orchestration, ai-ensemble]             ║
║ CONTEXT: Σ2 (System Layer)                                             ║
║ AGENTS: [Multiple Ollama Models]                                        ║
║ DEPS: [ollama, nusyq_chatdev, asyncio]                                  ║
║ CREATED: 2025-10-11                                                     ║
║ AUTHOR: GitHub Copilot + KiloMusician                                   ║
╚══════════════════════════════════════════════════════════════════════════╝

Multi-Model Consensus Orchestration System
===========================================

Coordinates multiple AI models to achieve consensus on code generation,
architectural decisions, and problem-solving tasks.

Features:
    - Parallel model execution with asyncio
    - Voting mechanisms (simple majority, weighted, ranked)
    - Solution quality analysis
    - Consensus reporting
    - ΞNuSyQ symbolic tracking integration

Usage:
    # Basic consensus
    orchestrator = ConsensusOrchestrator([
        "qwen2.5-coder:14b", "codellama:7b", "starcoder2:15b"
    ])
    result = orchestrator.run_consensus("Create a calculator function")

    # With voting strategy
    result = orchestrator.run_consensus(
        "Optimize bubble sort", voting="weighted"
    )
"""

import asyncio
import concurrent.futures
import hashlib
import json
import logging
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)

try:
    from config.adaptive_timeout_manager import (
        AgentType as TimeoutAgentType,
    )
    from config.adaptive_timeout_manager import (
        TaskComplexity as TimeoutTaskComplexity,
    )
    from config.adaptive_timeout_manager import (
        get_timeout_manager,
    )

    ADAPTIVE_TIMEOUT_AVAILABLE = True
except ImportError:
    ADAPTIVE_TIMEOUT_AVAILABLE = False


@dataclass
class ModelResponse:
    """Response from a single model"""

    model: str
    response: str
    timestamp: datetime
    duration_sec: float
    success: bool
    error: Optional[str] = None
    confidence: float = 1.0
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self):
        """Convert the response to a serializable dictionary."""
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d


@dataclass
class ConsensusResult:
    """Result of multi-model consensus"""

    task: str
    models: List[str]
    responses: List[ModelResponse]
    consensus_response: str
    agreement_rate: float
    voting_method: str
    total_duration_sec: float
    timestamp: datetime
    analysis: Dict[str, Any]

    def to_dict(self):
        """Convert the consensus result to a serializable dictionary."""
        d = {
            "task": self.task,
            "models": self.models,
            "responses": [r.to_dict() for r in self.responses],
            "consensus_response": self.consensus_response,
            "agreement_rate": self.agreement_rate,
            "voting_method": self.voting_method,
            "total_duration_sec": self.total_duration_sec,
            "timestamp": self.timestamp.isoformat(),
            "analysis": self.analysis,
        }
        return d


class ConsensusOrchestrator:
    """Orchestrate multiple models for consensus decision-making"""

    def __init__(
        self,
        models: List[str],
        ollama_url: str = "http://localhost:11434",
    ) -> None:
        """
        Initialize consensus orchestrator

        Args:
            models: List of Ollama model names
            ollama_url: Ollama API base URL
        """
        self.models = models
        self.ollama_url = ollama_url
        self.results_dir = Path("Reports/consensus")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        # Timeout configuration
        # By default do NOT enforce subprocess timeouts for Ollama runs unless
        # explicitly configured. This prevents killing long-running model
        # inferences arbitrarily on local agents.
        max_timeout = os.getenv("OLLAMA_MAX_TIMEOUT_SECONDS")
        # If set and numeric, use as maximum timeout cap (seconds);
        # if not set, None means no enforced timeout. Annotate attribute for
        # type checkers and default to None.
        self.max_timeout_seconds: Optional[int] = None
        if max_timeout and max_timeout.isdigit():
            self.max_timeout_seconds = int(max_timeout)

        adaptive_env = os.getenv("OLLAMA_ADAPTIVE_TIMEOUT")
        if adaptive_env is None:
            self.use_adaptive_timeouts = ADAPTIVE_TIMEOUT_AVAILABLE
        else:
            self.use_adaptive_timeouts = adaptive_env.lower() in ("1", "true", "yes")

        # File to store simple per-model timing history for adaptive timeouts
        cache_dir = Path(".cache")
        cache_dir.mkdir(exist_ok=True)
        self.timeout_history_file = cache_dir / "ollama_timeouts.json"
        self._timeout_history = self._load_timeout_history()
        self._current_task_complexity: Optional[TimeoutTaskComplexity] = None

    def run_consensus(
        self,
        task: str,
        voting: str = "simple",
        max_tokens: Optional[int] = None,
    ) -> ConsensusResult:
        """
        Run task on all models and achieve consensus

        Synchronous wrapper that handles event loop properly.
        Works in both sync and async contexts.

        Args:
            task: Task/question for models
            voting: Voting method ('simple', 'weighted', 'ranked')
            max_tokens: Max tokens per response

        Returns:
            ConsensusResult with consensus response and analysis
        """
        # Check if we're already in an event loop
        try:
            asyncio.get_running_loop()
            # We're in an async context - use run_until_complete won't work
            # Instead, we'll run in a thread pool
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    self._run_consensus_sync, task, voting, max_tokens
                )
                return future.result()
        except RuntimeError:
            # No event loop running - create one
            return asyncio.run(self._run_consensus_async(task, voting, max_tokens))

    async def run_consensus_async(
        self,
        task: str,
        voting: str = "simple",
        max_tokens: Optional[int] = None,
    ) -> ConsensusResult:
        """Public async entrypoint to run consensus across models."""
        return await self._run_consensus_async(task, voting, max_tokens)

    def _run_consensus_sync(
        self,
        task: str,
        voting: str,
        max_tokens: Optional[int],
    ) -> ConsensusResult:
        """Internal sync version that creates its own event loop"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._run_consensus_async(task, voting, max_tokens)
            )
        finally:
            loop.close()

    async def _run_consensus_async(
        self,
        task: str,
        voting: str,
        max_tokens: Optional[int],
    ) -> ConsensusResult:
        """
        Internal async implementation of consensus orchestration

        Args:
            task: Task/question for models
            voting: Voting method
            max_tokens: Max tokens per response

        Returns:
            ConsensusResult with consensus and analysis
        """
        print("\n" + "=" * 60)
        print("🤖 Multi-Model Consensus Orchestration")
        print("=" * 60)

        print("\n📋 Task:", task)
        print("🔧 Models:", ", ".join(self.models))
        print("🗳️  Voting:", voting)
        print("\n" + "=" * 60 + "\n")
        complexity = self._infer_task_complexity(task)
        if complexity in (TimeoutTaskComplexity.TRIVIAL, TimeoutTaskComplexity.SIMPLE):
            complexity = TimeoutTaskComplexity.MODERATE
        self._current_task_complexity = complexity

        # Respect optional max_tokens parameter if provided (log for now)
        if max_tokens is not None:
            print("Note: max_tokens provided:", max_tokens)

        start_time = time.time()

        # Execute on all models in parallel
        print(
            "⚡ Executing task on",
            len(self.models),
            "models in parallel...\n",
        )
        responses = await self._execute_parallel(task)

        # Analyze responses
        print("\n📊 Analyzing consensus...\n")
        consensus_response, agreement_rate, analysis = self._analyze_consensus(
            responses, voting
        )

        total_duration = time.time() - start_time

        # Create result
        result = ConsensusResult(
            task=task,
            models=self.models,
            responses=responses,
            consensus_response=consensus_response,
            agreement_rate=agreement_rate,
            voting_method=voting,
            total_duration_sec=total_duration,
            timestamp=datetime.now(),
            analysis=analysis,
        )

        # Save result
        self._save_result(result)

        # Print summary
        self._print_summary(result)

        return result

    async def _execute_parallel(self, task: str) -> List[ModelResponse]:
        """Execute task on all models in parallel using asyncio"""
        tasks = [self._execute_with_model(model, task) for model in self.models]
        return await asyncio.gather(*tasks)

    async def _execute_with_model(
        self,
        model: str,
        task: str,
    ) -> ModelResponse:
        """Execute task with a single model"""
        start_time = time.time()
        # Use a synchronous subprocess inside a thread to avoid asyncio
        # subprocess transport finalizer warnings when the event loop closes on
        # Windows.
        try:
            print(f"  [{model}] Starting...")

            # Determine timeout (None means no timeout / wait until completion)
            timeout = self._get_model_timeout(model)

            stdout, stderr, returncode, duration = await asyncio.to_thread(
                self._run_model_sync, model, task, timeout
            )

            if returncode == 0:
                response = (stdout or "").strip()
                if not response:
                    print(f"  [{model}] ❌ Failed: Empty response")
                    return ModelResponse(
                        model=model,
                        response="",
                        timestamp=datetime.now(),
                        duration_sec=duration,
                        success=False,
                        error="Empty response",
                        confidence=0.0,
                    )
                print(f"  [{model}] ✅ Completed in {duration:.1f}s")
                return ModelResponse(
                    model=model,
                    response=response,
                    timestamp=datetime.now(),
                    duration_sec=duration,
                    success=True,
                    confidence=1.0,
                    metadata={
                        "tokens": len(response.split()),
                    },
                )
            elif returncode is None:
                # timeout
                print(f"  [{model}] ⏱️  Timeout after {duration:.1f}s")
                return ModelResponse(
                    model=model,
                    response="",
                    timestamp=datetime.now(),
                    duration_sec=duration,
                    success=False,
                    error="Timeout",
                    confidence=0.0,
                )
            else:
                err = (stderr or "").strip()
                print(f"  [{model}] ❌ Failed: {err[:100]}")
                return ModelResponse(
                    model=model,
                    response="",
                    timestamp=datetime.now(),
                    duration_sec=duration,
                    success=False,
                    error=err,
                    confidence=0.0,
                )

        except (RuntimeError, OSError, ValueError) as e:
            # Expected runtime-level errors from subprocess or parsing
            duration = time.time() - start_time
            logger = logging.getLogger(__name__)
            logger.error("Model %s execution failed: %s", model, e)
            print(f"  [{model}] ❌ Error: {str(e)[:100]}")
            return ModelResponse(
                model=model,
                response="",
                timestamp=datetime.now(),
                duration_sec=duration,
                success=False,
                error=str(e),
                confidence=0.0,
            )
        except Exception as e:
            # Unexpected error: log full traceback and re-raise so callers
            # can decide whether to continue or abort. This avoids silently
            # swallowing programming errors.
            logging.getLogger(__name__).exception(
                "Unexpected error executing model %s: %s", model, e
            )
            raise

    def _get_model_timeout(self, model: str) -> Optional[int]:
        """
        Determine an appropriate timeout (seconds) for a model run.

        Behavior:
                - If `OLLAMA_ADAPTIVE_TIMEOUT` is enabled and we have
                    historical data for the model, use an adaptive estimate
                    (recent_duration * 1.5).
        - If `OLLAMA_MAX_TIMEOUT_SECONDS` is set, use it as a cap.
        - If neither is set, return None to indicate no enforced timeout.
        """
        if self.use_adaptive_timeouts and ADAPTIVE_TIMEOUT_AVAILABLE:
            manager = get_timeout_manager()
            agent_type = self._infer_agent_type(model)
            complexity = self._current_task_complexity or TimeoutTaskComplexity.MODERATE
            rec = manager.get_timeout(agent_type, complexity)
            timeout = int(rec.timeout_seconds)
            if self.max_timeout_seconds:
                return min(timeout, self.max_timeout_seconds)
            return timeout

        # Adaptive: prefer historical data if enabled
        if self.use_adaptive_timeouts:
            hist = self._timeout_history.get(model)
            if hist:
                try:
                    est = float(hist.get("ema", hist.get("last", 0)))
                    timeout = int(max(1, est * 1.5))
                    if self.max_timeout_seconds:
                        return min(timeout, self.max_timeout_seconds)
                    return timeout
                except (ValueError, TypeError) as e:
                    # Non-fatal parsing/typing issues for historical data
                    # Leave adaptive timeout disabled for this model on error
                    # and log for diagnostics.
                    LOGGER.debug(
                        "Adaptive timeout parse failed for model %s: %s",
                        model,
                        e,
                    )

        # If an explicit max timeout is set via environment, use it as a cap.
        if self.max_timeout_seconds:
            return int(self.max_timeout_seconds)

        # Default: no enforced timeout (None)
        return None

    def _infer_agent_type(self, model: str) -> TimeoutAgentType:
        """Map model name to adaptive timeout agent type."""
        name = model.lower()
        if any(key in name for key in ("phi3.5", "qwen2.5-coder:7b", "codellama")):
            return TimeoutAgentType.LOCAL_FAST
        return TimeoutAgentType.LOCAL_QUALITY

    def _infer_task_complexity(self, task: str) -> TimeoutTaskComplexity:
        """Estimate task complexity from prompt length."""
        length = len(task or "")
        if length < 50:
            return TimeoutTaskComplexity.TRIVIAL
        if length < 150:
            return TimeoutTaskComplexity.SIMPLE
        if length < 500:
            return TimeoutTaskComplexity.MODERATE
        if length < 1500:
            return TimeoutTaskComplexity.COMPLEX
        return TimeoutTaskComplexity.CRITICAL

    def _load_timeout_history(self) -> Dict[str, Any]:
        try:
            if self.timeout_history_file.exists():
                with open(
                    self.timeout_history_file,
                    "r",
                    encoding="utf-8",
                ) as f:
                    return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            # Best-effort: if we can't read or parse the history file,
            # return empty
            LOGGER.debug("Could not load timeout history: %s", e)
            return {}
        return {}

    def _save_timeout_history(self):
        try:
            with open(self.timeout_history_file, "w", encoding="utf-8") as f:
                json.dump(self._timeout_history, f, indent=2)
        except (OSError, TypeError) as e:
            LOGGER.warning("Failed to save timeout history: %s", e)

    def _record_model_duration(self, model: str, duration: float):
        """Record last duration and a simple EMA for the model."""
        entry = self._timeout_history.get(model, {})
        last = float(entry.get("last", 0))
        if last <= 0:
            ema = duration
        else:
            # exponential moving average with alpha=0.3
            alpha = 0.3
            ema = alpha * duration + (1 - alpha) * last

        self._timeout_history[model] = {"last": duration, "ema": ema}
        self._save_timeout_history()

    def _run_model_sync(self, model: str, task: str, timeout: Optional[int]):
        """Run `ollama run model task` synchronously.

        Returns (stdout, stderr, returncode, duration).
        If timeout is None the call will wait until completion. If the process
        expires, returncode will be None and stderr will contain the exception.
        """
        start = time.time()
        args = ["ollama", "run", model, task]
        try:
            env = os.environ.copy()
            env.setdefault("OLLAMA_NO_SPINNER", "1")
            if timeout is None:
                proc = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=False,
                    env=env,
                )
            else:
                proc = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout,
                    check=False,
                    env=env,
                )

            duration = time.time() - start

            # Record duration for adaptive timeout history (best-effort)
            try:
                self._record_model_duration(model, duration)
            except (OSError, TypeError, ValueError) as e:
                # Non-fatal: recording history failed (IO or parse issue)
                logging.getLogger(__name__).debug(
                    "Failed to record model duration for %s: %s", model, e
                )

            stdout = (proc.stdout or "").strip()
            if proc.returncode == 0 and stdout:
                return proc.stdout, proc.stderr, proc.returncode, duration

            api_response = self._run_model_api(model, task, timeout)
            if api_response["success"]:
                return api_response["response"], "", 0, duration

            return proc.stdout, proc.stderr, proc.returncode, duration

        except subprocess.TimeoutExpired as e:
            duration = time.time() - start
            return "", str(e), None, duration
        except OSError as e:
            duration = time.time() - start
            return "", str(e), -1, duration
        except (ValueError, RuntimeError) as e:
            # Likely an argument/logic error or runtime failure - return error
            duration = time.time() - start
            logging.getLogger(__name__).error("Model run failed for %s: %s", model, e)
            return "", str(e), -1, duration
        except Exception as e:
            # Unexpected error while running subprocess - log full traceback
            logging.getLogger(__name__).exception(
                "Unexpected error while running model %s: %s", model, e
            )
            duration = time.time() - start
            raise

    def _run_model_api(
        self, model: str, task: str, timeout: Optional[int]
    ) -> Dict[str, Any]:
        """Fallback to Ollama HTTP API for model execution."""
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        url = f"{base_url.rstrip('/')}/api/generate"
        payload = json.dumps({"model": model, "prompt": task, "stream": False}).encode(
            "utf-8"
        )

        request = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}
        )

        try:
            # Security: Only allow http(s) URLs
            from urllib.parse import urlparse

            parsed_url = urlparse(url)
            if parsed_url.scheme not in ("http", "https"):
                return {
                    "success": False,
                    "error": f"Disallowed URL scheme: {parsed_url.scheme}",
                }
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                body = resp.read().decode("utf-8")
                data = json.loads(body)
                response = data.get("response", "")
                if response:
                    return {"success": True, "response": response}
                return {"success": False, "error": data.get("error", "Empty response")}
        except (urllib.error.URLError, ValueError) as e:
            return {"success": False, "error": str(e)}

    def _analyze_consensus(
        self,
        responses: List[ModelResponse],
        voting: str,
    ) -> tuple:
        """
        Analyze responses and determine consensus

        Returns:
            (consensus_response, agreement_rate, analysis)
        """
        successful_responses = [r for r in responses if r.success]

        if not successful_responses:
            return (
                "",
                0.0,
                {
                    "error": "No successful responses",
                    "total_models": len(responses),
                    "successful_models": 0,
                    "failed_models": len(responses),
                    "avg_duration_sec": 0.0,
                    "response_lengths": [],
                    "unique_responses": 0,
                },
            )

        analysis = {
            "total_models": len(responses),
            "successful_models": len(successful_responses),
            "failed_models": len(responses) - len(successful_responses),
            "avg_duration_sec": (
                sum(r.duration_sec for r in successful_responses)
                / len(successful_responses)
            ),
            "response_lengths": [len(r.response) for r in successful_responses],
            "unique_responses": len(
                {self._normalize(r.response) for r in successful_responses}
            ),
        }

        # Simple voting: choose most common response (normalized)
        if voting == "simple":
            normalized_responses = [
                self._normalize(r.response) for r in successful_responses
            ]
            response_counts = Counter(normalized_responses)
            most_common = response_counts.most_common(1)[0]
            consensus_normalized = most_common[0]
            consensus_count = most_common[1]

            # Find original (non-normalized) version
            for r in successful_responses:
                if self._normalize(r.response) == consensus_normalized:
                    consensus_response = r.response
                    break

            agreement_rate = consensus_count / len(successful_responses)

            analysis["voting_details"] = {
                "method": "simple_majority",
                "consensus_count": consensus_count,
                "response_distribution": dict(response_counts),
            }

        # Weighted voting: weight by model confidence
        elif voting == "weighted":
            # For now, use simple voting (can enhance with model-specific
            # weights later)
            consensus_response, agreement_rate, _ = self._analyze_consensus(
                responses, "simple"
            )
            analysis["voting_details"] = {
                "method": "weighted (using simple for now)",
                "note": "Future: weight by model performance history",
            }

        # Ranked voting: rank by quality metrics
        elif voting == "ranked":
            # Rank by response length + success (simple heuristic for now)
            ranked = sorted(
                successful_responses,
                key=lambda r: len(r.response),
                reverse=True,
            )
            consensus_response = ranked[0].response
            agreement_rate = 1.0 / len(successful_responses)
            # Lower for ranked

            analysis["voting_details"] = {
                "method": "ranked_by_length",
                "rankings": [(r.model, len(r.response)) for r in ranked],
            }

        else:
            # Default to simple
            return self._analyze_consensus(responses, "simple")

        return consensus_response, agreement_rate, analysis

    def _normalize(self, text: str) -> str:
        """Normalize text for comparison"""
        # Remove extra whitespace, lowercase, remove punctuation
        text = text.lower().strip()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^\w\s]", "", text)
        return text

    def _save_result(self, result: ConsensusResult):
        """Save consensus result to JSON file"""
        timestamp_str = result.timestamp.strftime("%Y%m%d_%H%M%S")
        task_hash = hashlib.md5(result.task.encode()).hexdigest()[:8]
        filename = f"consensus_{timestamp_str}_{task_hash}.json"
        filepath = self.results_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

        print(f"\n💾 Result saved: {filepath}")

    def _print_summary(self, result: ConsensusResult):
        """Print consensus summary"""
        print("\n" + "=" * 60)
        print("📊 CONSENSUS SUMMARY")
        print("" + "=" * 60 + "\n")

        analysis = result.analysis or {}
        successful_models = analysis.get("successful_models", 0)
        total_models = analysis.get("total_models", 0)
        print("✅ Successful:", f"{successful_models}/{total_models}", "models")
        print("🤝 Agreement Rate:", f"{result.agreement_rate * 100:.1f}%")
        print("⏱️  Total Duration:", f"{result.total_duration_sec:.1f}s")
        avg_duration = analysis.get("avg_duration_sec", 0.0)
        print(
            "📈 Avg Response Time:",
            f"{avg_duration:.1f}s per model",
        )
        print("🎯 Unique Responses:", analysis.get("unique_responses", 0))

        print("\n" + "=" * 60)
        print("🏆 CONSENSUS RESPONSE")
        print("" + "=" * 60 + "\n")
        consensus_text = result.consensus_response or ""
        print(consensus_text[:500])
        if len(consensus_text) > 500:
            print("\n... (truncated, see full result in JSON)")

        print("\n" + "=" * 60)
        print("📋 INDIVIDUAL RESPONSES")
        print("" + "=" * 60 + "\n")

        for r in result.responses:
            if r.success:
                print(f"[{r.model}] ({r.duration_sec:.1f}s)")
                print(f"  {r.response[:200]}")
                if len(r.response) > 200:
                    print("  ... (truncated)")
            else:
                print(f"[{r.model}] ❌ FAILED: {(r.error or '')[:100]}")
            print()

        print(f"{'=' * 60}\n")


def main():
    """Example usage"""
    print("ΞNuSyQ Multi-Model Consensus Orchestrator")
    print("=========================================\n")

    # Example 1: Simple code generation consensus
    models = ["qwen2.5-coder:7b", "codellama:7b"]  # Start with 2 for testing
    task = "Write a Python function to calculate fibonacci numbers"

    orchestrator = ConsensusOrchestrator(models)
    result = orchestrator.run_consensus(task, voting="simple")

    agreement_pct = result.agreement_rate * 100
    print(f"\n✅ Consensus achieved with {agreement_pct:.1f}% agreement!")


if __name__ == "__main__":
    main()
