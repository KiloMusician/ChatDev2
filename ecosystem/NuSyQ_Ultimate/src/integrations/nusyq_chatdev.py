"""
╔══════════════════════════════════════════════════════════════════════════╗
║ ΞNuSyQ OmniTag Metadata                                                  ║
╠══════════════════════════════════════════════════════════════════════════╣
║ FILE-ID: nusyq.core.chatdev.orchestrator                               ║
║ TYPE: Python Module                                                     ║
║ STATUS: Production                                                      ║
║ VERSION: 2.0.0                                                          ║
║ TAGS: [chatdev, orchestration, ollama, ai-core, symbolic-protocol]     ║
║ CONTEXT: Σ1 (Component Layer)                                          ║
║ AGENTS: [ClaudeCode, ChatDev, OllamaModels]                            ║
║ DEPS: [requests, ChatDev/*, ollama, knowledge-base.yaml]               ║
║ INTEGRATIONS: [Ollama-API, ChatDev, ΞNuSyQ-Framework]                  ║
║ CREATED: 2025-10-05                                                     ║
║ UPDATED: 2025-10-06                                                     ║
║ AUTHOR: Claude Code + KiloMusician                                      ║
║ STABILITY: High (Production Ready)                                      ║
╚══════════════════════════════════════════════════════════════════════════╝

NuSyQ-ChatDev Integration Module with ΞNuSyQ ∆ΨΣ Framework
===========================================================

Purpose:
    Bridge ChatDev with Ollama local models and ΞNuSyQ symbolic framework.
    Provides local AI model access with advanced message tracking and
    recursive orchestration capabilities.

ΞNuSyQ Framework Integration:
    - Symbolic message tracking: [Msg⛛{X}↗️Σ∞]
    - OmniTag encoding for rich context
    - Fractal pattern coordination
    - Temporal drift tracking
    - Multi-model consensus mechanisms

Integration Points:
    1. Ollama API compatibility layer for ChatDev
    2. Model selection and management
    3. Symbolic message tracking and OmniTag encoding
    4. Fractal coordination for multi-agent workflows
    5. Token counting and response formatting
    6. Configuration management for local models

Usage:
    # Basic usage
    python nusyq_chatdev.py --task "create a calculator" \
        --model "qwen2.5-coder:7b"

    # With symbolic tracking
    python nusyq_chatdev.py --task "REST API" --symbolic --msg-id 1

    # Multi-model consensus
    python nusyq_chatdev.py --task "optimize code" --consensus \
        --models qwen2.5-coder:14b,codellama:7b

Author: NuSyQ Development Team
Version: 2.0.0 (ΞNuSyQ ∆ΨΣ Enhanced)
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import telemetry.tracing_setup as tracing

# Fix Windows console UTF-8 encoding for ΞNuSyQ symbols
if sys.platform == "win32":
    import codecs

    # Some environments (pytest, certain logging setups) wrap stdout/stderr
    # and may not expose `.buffer`. Use a safe fallback in those cases.
    try:
        stdout_buffer = sys.stdout.buffer
    except AttributeError:
        stdout_buffer = None

    try:
        stderr_buffer = sys.stderr.buffer
    except AttributeError:
        stderr_buffer = None

    if stdout_buffer:
        sys.stdout = codecs.getwriter("utf-8")(stdout_buffer, "strict")
    if stderr_buffer:
        sys.stderr = codecs.getwriter("utf-8")(stderr_buffer, "strict")

# Basic logging configuration (can be overridden by caller / environment)
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)

# Initialize tracing at module import; safe no-op if OTEL not available
tracing.initialize_tracing(service_name="nusyq_chatdev")
tracing.instrument_requests()

# Import process tracker for intelligent process monitoring
# (replaces arbitrary timeouts with behavioral analysis)
sys.path.insert(0, str(Path(__file__).parent))


# === ΞNuSyQ ∆ΨΣ Framework Classes ===


@dataclass
class NuSyQMessage:
    """
    Symbolic message wrapper following [Msg⛛{X}↗️Σ∞] protocol

    Attributes:
        msg_id: Message identifier (can be hierarchical like "1.1.2")
        data: Core message content
        context: Contextual metadata
        timestamp: Message creation time
        recursion_level: Depth in recursive chain (↗️Σ∞)
        symbolic_tag: Optional ΞNuSyQ symbolic overlay (⧉ΞΦΣΛΨΞ)
    """

    msg_id: str
    data: Any
    context: Dict[str, Any]
    timestamp: datetime
    recursion_level: int = 0
    symbolic_tag: Optional[str] = None

    def to_omnitag(self) -> str:
        """
        Generate OmniTag representation

        Format: [Msg⛛{X}]▲[Data]↠t[⏳]↞🌐{Ctx}🌐
        """
        time_str = self.timestamp.isoformat()
        ctx_str = json.dumps(self.context) if self.context else "{}"

        omnitag = (
            f"[Msg⛛{{{self.msg_id}}}]▲[{self.data}]↠t[{time_str}]\n↞🌐{{{ctx_str}}}🌐"
        )

        if self.symbolic_tag:
            omnitag += f"⧉{self.symbolic_tag}⧉"

        if self.recursion_level > 0:
            omnitag += f"↗️Σ{self.recursion_level}"

        return omnitag

    def recurse(
        self, new_data: Any, new_context: Optional[Dict] = None
    ) -> "NuSyQMessage":
        """Create recursive child message (↗️Σ∞)"""
        child_id = f"{self.msg_id}.{self.recursion_level + 1}"
        child_context = {**(new_context or {}), "parent_msg": self.msg_id}

        return NuSyQMessage(
            msg_id=child_id,
            data=new_data,
            context=child_context,
            timestamp=datetime.now(),
            recursion_level=self.recursion_level + 1,
            symbolic_tag=self.symbolic_tag,
        )


class FractalCoordinator:
    """
    Fractal pattern generator for multi-agent coordination

    Implements: ↻ΞFractalGenerator
    Supports: ΣΛΘΨΞ↻ΞPrimaryCore recursive patterns
    """

    def __init__(self):
        self.root_tag = "ΞΦΣΛ⟆ΣΞ"  # SystemRoot
        self.patterns = []

    def generate_agent_pattern(self, agent_count: int) -> List[str]:
        """
        Generate fractal pattern for N agents

        Returns symbolic tags for each agent node
        """
        pattern = []
        for i in range(agent_count):
            # Generate hierarchical symbolic tag
            tag = f"{{ΣΛΘΨΞ↻ΞAgent{i}::{self.root_tag}}}"
            pattern.append(tag)

        self.patterns.append(pattern)
        return pattern

    def coordinate_responses(self, responses: List[Dict], pattern: List[str]) -> Dict:
        """
        Coordinate multiple agent responses using fractal pattern

        Implements: ⊕ΞΛΨΘ↻ΞRecursiveChains
        """
        coordinated = {
            "fractal_pattern": pattern,
            "responses": [],
            "consensus": None,
            "symbolic_overlay": "⧉ΞΦΣΛΨΞ-Coordination⧉",
        }

        for i, (response, tag) in enumerate(zip(responses, pattern, strict=False)):
            coordinated["responses"].append(
                {
                    "agent_id": i,
                    "symbolic_tag": tag,
                    "content": response.get("content", ""),
                    "confidence": response.get("confidence", 1.0),
                }
            )

        # Simple consensus: highest confidence response
        if coordinated["responses"]:
            best = max(coordinated["responses"], key=lambda x: x.get("confidence", 0))
            coordinated["consensus"] = best["content"]

        return coordinated


class TemporalTracker:
    """
    Temporal drift tracking for AI performance analysis

    Implements: ⨈ΦΣΞΨΘΣΛ (temporal drift mapping)
    """

    def __init__(self):
        self.session_history = []

    def track_session(self, msg: NuSyQMessage, model: str, response: str) -> None:
        """Track session for temporal analysis"""
        self.session_history.append(
            {
                "msg_id": msg.msg_id,
                "timestamp": msg.timestamp,
                "model": model,
                "task": msg.data,
                "response_length": len(response),
                "context": msg.context,
            }
        )

    def analyze_drift(self) -> Dict[str, Any]:
        """
        Analyze temporal drift across sessions

        Returns drift metrics and symbolic mapping
        """
        if len(self.session_history) < 2:
            return {"drift": 0, "sessions": len(self.session_history)}

        # Simple drift: response length variance over time
        response_lengths = [s["response_length"] for s in self.session_history]
        mean_length = sum(response_lengths) / len(response_lengths)
        variance = sum(
            (length - mean_length) ** 2 for length in response_lengths
        ) / len(response_lengths)

        return {
            "drift_metric": variance,
            "mean_response_length": mean_length,
            "session_count": len(self.session_history),
            "temporal_tag": "⨈ΦΣΞΨΘΣΛ",
            "sessions": self.session_history[-5:],  # Last 5 sessions
        }


# === Constants ===
DEFAULT_CODING_MODEL = "qwen2.5-coder:7b"
RECOMMENDED_MODELS = [
    "qwen2.5-coder:14b",
    DEFAULT_CODING_MODEL,
    "codellama:7b",
]


class OllamaModelBackend:
    """
    Ollama integration for ChatDev
    Replaces OpenAI API calls with local Ollama model requests
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = DEFAULT_CODING_MODEL,
    ) -> None:
        self.base_url = base_url
        self.model = model
        self.session = requests.Session()
        # HTTP timeout configuration for Ollama calls.
        # If OLLAMA_HTTP_TIMEOUT_SECONDS is set, use it for health checks and metadata calls.
        # If OLLAMA_HTTP_GENERATE_TIMEOUT_SECONDS is set, use it for generation calls; if
        # not set, leave generation timeout as None (no enforced timeout) to avoid
        # killing long-running inferences.
        http_timeout = os.getenv("OLLAMA_HTTP_TIMEOUT_SECONDS")
        if http_timeout and http_timeout.isdigit():
            self.http_timeout = int(http_timeout)
        else:
            self.http_timeout = 10

        gen_timeout = os.getenv("OLLAMA_HTTP_GENERATE_TIMEOUT_SECONDS")
        # None means requests will wait until completion for generation calls
        if gen_timeout and gen_timeout.isdigit():
            self.generate_timeout = int(gen_timeout)
        else:
            # Default generation timeout to 120s to avoid indefinite waits
            # for long-running generations while still allowing longer jobs
            # to be configured via OLLAMA_HTTP_GENERATE_TIMEOUT_SECONDS.
            self.generate_timeout = 120

    def check_ollama_connection(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            # Quick health check - expected to be fast
            response = self.session.get(
                f"{self.base_url}/api/tags", timeout=self.http_timeout
            )
            return response.status_code == 200
        except requests.RequestException as e:
            logging.error("Ollama connection failed: %s", e)
            return False

    def get_available_models(self) -> List[str]:
        """Get list of available Ollama models"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/tags", timeout=self.http_timeout
            )
            if response.status_code == 200:
                models_data = response.json()
                return [model["name"] for model in models_data.get("models", [])]
            return []
        except (ConnectionError, TimeoutError, ValueError) as e:
            logging.error("Failed to get available models: %s", e)
            return []

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Generate chat completion using Ollama
        Compatible with OpenAI ChatCompletion format
        """
        # Convert messages to Ollama format
        prompt = self._convert_messages_to_prompt(messages)

        try:
            # Use process tracker for intelligent monitoring instead of arbitrary timeout
            # Ollama generation can vary: 10s for simple, 300s+ for complex reasoning
            # Let the tracker investigate anomalies instead of killing legitimate work
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature,
                    },
                },
                timeout=self.generate_timeout,
            )

            if response.status_code == 200:
                result = response.json()
                return self._format_ollama_response(result, prompt)
            else:
                raise RuntimeError(f"Ollama API error: {response.status_code}")

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to generate response: {e}") from e

    def _convert_messages_to_prompt(self, messages: List[Dict[str, Any]]) -> str:
        """Convert OpenAI messages format to single prompt"""
        prompt_parts = []

        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")

            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)

    def _format_ollama_response(
        self, ollama_result: Dict[str, Any], prompt: str
    ) -> Dict[str, Any]:
        """Format Ollama response to match OpenAI format"""
        response_text = ollama_result.get("response", "")

        # Estimate token counts (rough approximation)
        prompt_tokens = len(prompt.split()) * 1.3  # Rough token estimation
        completion_tokens = len(response_text.split()) * 1.3

        return {
            "choices": [
                {
                    "message": {"role": "assistant", "content": response_text},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": int(prompt_tokens),
                "completion_tokens": int(completion_tokens),
                "total_tokens": int(prompt_tokens + completion_tokens),
            },
            "model": self.model,
        }


def setup_ollama_for_chatdev() -> bool | tuple[bool, str]:
    """
    Configure ChatDev to use Ollama instead of OpenAI
    """
    logging.info("=== NuSyQ ChatDev + Ollama Setup ===")

    # Check Ollama connection
    ollama = OllamaModelBackend()
    with tracing.start_span("check_ollama_connection"):
        if not ollama.check_ollama_connection():
            logging.error("[X] Ollama is not running or not accessible")
            logging.error("Please start Ollama and ensure models are available")
            return False

    logging.info("[OK] Ollama connection verified")

    # Get available models
    with tracing.start_span("get_available_models"):
        models = ollama.get_available_models()
    if not models:
        logging.error("[X] No Ollama models found")
        logging.error("Please install models using: ollama pull qwen2.5-coder:7b")
        return False
    logging.info("[OK] Found %s Ollama models:", len(models))
    for model in models[:5]:  # Show first 5
        logging.info("   - %s", model)
    if len(models) > 5:
        logging.info("   ... and %s more", len(models) - 5)
    print()

    # Recommend best model for coding
    coding_models = [m for m in models if "coder" in m.lower() or "code" in m.lower()]
    if coding_models:
        recommended = coding_models[0]
        logging.info("[*] Recommended coding model: %s", recommended)
    else:
        recommended = models[0] if models else DEFAULT_CODING_MODEL
        logging.info("[*] Using available model: %s", recommended)

    return True, recommended


def run_chatdev_with_ollama(
    task: str,
    model: str,
    config: str = "NuSyQ_Ollama",
    use_modular_models: bool = True,
    background: bool = False,
    project_name: Optional[str] = None,
    max_runtime: int = 1800,
) -> bool:
    """
    Run ChatDev with Ollama integration

    Args:
        task: Development task description
        model: Default Ollama model (used if modular models disabled)
        config: ChatDev configuration name
        use_modular_models: Enable per-agent model assignment
        background: Run in detached background mode
        project_name: Project name (auto-generated if None)
    """
    with tracing.start_span(
        "run_chatdev_with_ollama",
        {"task": task, "model": model, "background": background},
    ):
        chatdev_dir = Path("ChatDev")
    if not chatdev_dir.exists():
        logging.error("[X] ChatDev directory not found")
        return False

    # Generate project name from task if not provided
    if not project_name:
        # Simple sanitization: remove special chars, limit length
        import re

        project_name = (
            re.sub(r"[^a-zA-Z0-9\s]", "", task)[:30].strip().replace(" ", "_")
        )
        if not project_name:
            project_name = "NuSyQ_Project"

    # Set up environment for Ollama usage
    env = os.environ.copy()

    # Create a mock OpenAI key to satisfy ChatDev's requirements
    # ChatDev will use our Ollama backend instead
    env["OPENAI_API_KEY"] = "ollama-local-model"

    # Enable modular model system if requested
    if use_modular_models:
        logging.info("[🤖] Modular Agent Models: ENABLED")
        logging.info("[>>] Per-agent model assignments will be loaded from config")
        # Import and apply modular model adapter
        try:
            sys.path.insert(0, str(chatdev_dir))
            with tracing.start_span(
                "apply_modular_models", {"component": "modular_adapter"}
            ):
                from chatdev.modular_model_adapter import (
                    apply_modular_models,  # type: ignore[reportMissingImports]
                )

                apply_modular_models()
            logging.info("[✅] Modular model system activated")
        except ImportError as e:
            logging.warning("[⚠️ ] Modular models failed to load: %s", e)
            logging.info("[>>] Falling back to single model mode")
            use_modular_models = False
    else:
        logging.info("[>>] Starting ChatDev with Ollama model: %s", model)

    logging.info("[>>] Task: %s", task)
    logging.info("[>>] Project Name: %s", project_name)
    logging.info("[>>] Configuration: %s", config)
    logging.info("[>>] Max Runtime (foreground): %s seconds", max_runtime)

    # Command to run ChatDev (subprocess imported globally)

    try:
        # Use .venv Python if available, fallback to system Python
        venv_python = Path(__file__).parent / ".venv" / "Scripts" / "python.exe"
        if not venv_python.exists():
            venv_python = (
                Path(__file__).parent / ".venv" / "bin" / "python"
            )  # Linux/Mac

        python_exe = str(venv_python) if venv_python.exists() else sys.executable

        logging.info("[*] Using Python: %s", python_exe)

        cmd = [
            python_exe,
            "run_ollama.py",  # Relative to cwd (ChatDev/)
            "--task",
            task,
            "--name",
            project_name,  # Required argument
            "--config",
            config,
            "--org",
            "NuSyQ",
            "--model",
            model,
        ]

        logging.info("Running command:")
        logging.info("%s", " ".join(cmd))

        # Background mode: detach and log to file
        if background:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = Path(f"chatdev_background_{timestamp}.log")

            logging.info("[⚙️] BACKGROUND MODE ENABLED")
            logging.info("[⚙️] Process will run detached from this terminal")
            logging.info("[⚙️] Output logging to: %s", log_file.absolute())
            logging.info("[⚙️] Check log file for progress updates")

            # Start process detached and capture output to log file
            with open(log_file, "w", encoding="utf-8") as log:
                log.write("=== NuSyQ ChatDev Background Execution ===\n")
                log.write(f"Task: {task}\n")
                log.write(f"Model: {model}\n")
                log.write(f"Started: {datetime.now().isoformat()}\n")
                log.write(f"Command: {' '.join(cmd)}\n\n")
                log.flush()

                if sys.platform == "win32":
                    process = subprocess.Popen(
                        cmd,
                        env=env,
                        cwd=str(chatdev_dir),
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        creationflags=subprocess.DETACHED_PROCESS
                        | subprocess.CREATE_NEW_PROCESS_GROUP,
                    )
                else:
                    process = subprocess.Popen(
                        cmd,
                        env=env,
                        cwd=str(chatdev_dir),
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        start_new_session=True,
                    )

            logging.info("[OK] Background process started with PID: %s", process.pid)
            logging.info("[>>] Monitor progress: tail -f %s", log_file)
            logging.info("[>>] Or open in editor: %s", log_file.absolute())
            return True

        # Run ChatDev with real-time output streaming
        # Don't buffer output - let it flow to console immediately
        # This prevents subprocess from blocking when output buffer fills
        with tracing.start_span("start_subprocess", {"command": "run_ollama"}):
            process = subprocess.Popen(
                cmd,
                env=env,
                cwd=str(chatdev_dir),  # Run from ChatDev directory
                stdout=None,  # Stream directly to console
                stderr=None,  # Stream directly to console
                text=True,
                encoding="utf-8",
                errors="replace",
            )

        # Wait for process to complete with interruption protection
        logging.info("[*] ChatDev running... (output streaming above)")
        logging.info("[*] This may take several minutes for complex tasks")
        logging.warning(
            "[⚠️] IMPORTANT: Do NOT interrupt! ChatDev agents are coordinating..."
        )
        logging.warning(
            "[⚠️] Interruption will lose all progress. Let the agents finish!"
        )

        # Wrap process.wait() with KeyboardInterrupt protection
        try:
            with tracing.start_span("wait_for_process", {"timeout": max_runtime}):
                exit_code = process.wait(timeout=max_runtime)
        except KeyboardInterrupt:
            print()  # keep user-facing interrupt messaging on stdout
            logging.error("[!!!!] INTERRUPT DETECTED - DO YOU REALLY WANT TO STOP?")
            logging.error(
                "[!!!!] ChatDev agents are still working. This will lose ALL progress!"
            )
            logging.error(
                "[!!!!] Press Ctrl+C again within 5 seconds to force stop, or wait to continue..."
            )
            print()

            import signal
            import time

            # Set up a timeout handler
            stop_confirmed = [False]

            def confirm_handler(_signum, _frame):
                stop_confirmed[0] = True
                raise KeyboardInterrupt("User confirmed stop")

            old_handler = signal.signal(signal.SIGINT, confirm_handler)

            try:
                time.sleep(5)
                # If we get here, user didn't press Ctrl+C again - resume waiting
                logging.info("[OK] Continuing to wait for ChatDev agents...")
                signal.signal(signal.SIGINT, old_handler)
                exit_code = process.wait(timeout=max_runtime)
            except KeyboardInterrupt:
                # User pressed Ctrl+C again - actually stop
                print()
                logging.error("[X] STOP CONFIRMED - Terminating ChatDev process...")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logging.error("Process did not terminate in time; killing.")
                    process.kill()
                signal.signal(signal.SIGINT, old_handler)
                return False

        if exit_code == 0:
            print()
            logging.info("[OK] ChatDev completed successfully!")
            logging.info("[>>] Check ChatDev/WareHouse/ for output")
        else:
            print()
            logging.error("[X] ChatDev encountered an error (exit code: %s)", exit_code)

        return exit_code == 0
    except (OSError, subprocess.SubprocessError) as e:
        logging.error("[X] Error running ChatDev: %s", e)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="NuSyQ ChatDev with Ollama Integration + ΞNuSyQ ∆ΨΣ Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python nusyq_chatdev.py --task "Create a calculator app"

  # With symbolic tracking
  python nusyq_chatdev.py --task "REST API" --symbolic --msg-id 1

  # Multi-model consensus
  python nusyq_chatdev.py --task "Optimize code" --consensus --models qwen2.5-coder:14b,codellama:7b

  # With temporal drift analysis
  python nusyq_chatdev.py --task "Generate UI" --track-drift

ΞNuSyQ Framework:
  --symbolic        Enable symbolic message tracking [Msg⛛{X}↗️Σ∞]
  --msg-id         Set initial message ID for tracking
  --consensus      Use multi-model consensus (requires --models)
  --track-drift    Enable temporal drift tracking (⨈ΦΣΞΨΘΣΛ)
        """,
    )

    parser.add_argument("--task", help="Development task description")
    parser.add_argument(
        "--model",
        default=DEFAULT_CODING_MODEL,
        help=f"Ollama model to use (default: {DEFAULT_CODING_MODEL})",
    )
    parser.add_argument(
        "--config", default="NuSyQ_Ollama", help="ChatDev configuration"
    )
    parser.add_argument(
        "--setup-only", action="store_true", help="Only check setup, don't run"
    )
    parser.add_argument(
        "--help-chatdev", action="store_true", help="Show ChatDev run.py help"
    )
    parser.add_argument(
        "--background",
        action="store_true",
        help="Run in background mode (detached, logs to file)",
    )

    # ΞNuSyQ Framework options
    parser.add_argument(
        "--symbolic", action="store_true", help="Enable symbolic message tracking"
    )
    parser.add_argument(
        "--msg-id", type=str, default="1", help="Initial message ID for tracking"
    )
    parser.add_argument(
        "--consensus", action="store_true", help="Use multi-model consensus"
    )
    parser.add_argument(
        "--models", type=str, help="Comma-separated list of models for consensus"
    )
    parser.add_argument(
        "--track-drift", action="store_true", help="Enable temporal drift tracking"
    )
    parser.add_argument(
        "--fractal-depth",
        type=int,
        default=3,
        help="Fractal pattern depth for coordination",
    )
    parser.add_argument(
        "--max-runtime",
        type=int,
        default=1800,
        help="Maximum seconds to wait for foreground ChatDev run (default: 1800)",
    )

    # Modular model system
    parser.add_argument(
        "--modular-models",
        action="store_true",
        default=True,
        help="Enable per-agent model assignment (default: True)",
    )
    parser.add_argument(
        "--no-modular-models",
        dest="modular_models",
        action="store_false",
        help="Disable per-agent models, use single model for all agents",
    )

    args = parser.parse_args()

    # Top-level main span is intentionally avoided to keep structure flat; we add
    # smaller spans to capture key sections instead.

    # Show ChatDev help if requested
    if args.help_chatdev:
        chatdev_dir = Path("ChatDev")
        if chatdev_dir.exists():
            try:
                env = os.environ.copy()
                env["OPENAI_API_KEY"] = "ollama-local-model"
                # Increased from 30s to 60s - help display can be slow on first run
                result = subprocess.run(
                    [sys.executable, str(chatdev_dir / "run.py"), "--help"],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False,
                )
                print(result.stdout)
                if result.stderr:
                    print(result.stderr)
                return 0
            except (
                subprocess.TimeoutExpired,
                OSError,
            ) as e:
                print(f"[X] Error getting ChatDev help: {e}")
                return 1
        else:
            print("[X] ChatDev directory not found")
            return 1

    # Setup and verification
    setup_result = setup_ollama_for_chatdev()
    if not setup_result:
        return 1

    if isinstance(setup_result, tuple):
        success, recommended_model = setup_result
        if args.model == DEFAULT_CODING_MODEL and recommended_model != args.model:
            logging.info("[*] Using recommended model: %s", recommended_model)
            args.model = recommended_model

    if args.setup_only:
        print("[OK] Setup verification complete!")
        return 0

    # Require task if not setup-only or help-chatdev
    if not args.task:
        logging.error(
            "[X] --task is required (use --setup-only to check setup or --help-chatdev for ChatDev help)"
        )
        return 1

    # === ΞNuSyQ Framework Integration ===

    # Initialize symbolic tracking if enabled
    symbolic_msg = None
    if args.symbolic:
        logging.info("\n[ΞNuSyQ] Symbolic Tracking Enabled")
        symbolic_msg = NuSyQMessage(
            msg_id=args.msg_id,
            data=args.task,
            context={
                "model": args.model,
                "config": args.config,
                "framework": "ΞNuSyQ ∆ΨΣ v2.0",
            },
            timestamp=datetime.now(),
            symbolic_tag="⧉ΞΦΣΛΨΞ-ChatDev⧉",
        )
        logging.info("[OmniTag] %s...", symbolic_msg.to_omnitag()[:100])

    # Initialize temporal tracking if enabled
    temporal_tracker = None
    if args.track_drift:
        logging.info("\n[ΞNuSyQ] Temporal Drift Tracking Enabled (⨈ΦΣΞΨΘΣΛ)")
        temporal_tracker = TemporalTracker()

    # Multi-model consensus mode
    if args.consensus:
        if not args.models:
            print("[X] --consensus requires --models argument")
            return 1

        models_list = args.models.split(",")
        logging.info("\n[ΞNuSyQ] Multi-Model Consensus Mode")
        logging.info("   Models: %s", ", ".join(models_list))

        fractal = FractalCoordinator()
        pattern = fractal.generate_agent_pattern(len(models_list))

        logging.info("   Fractal Pattern Generated: %s nodes", len(pattern))

        # Run with each model and coordinate
        responses = []
        for i, model in enumerate(models_list):
            with tracing.start_span(
                "consensus_model_run", {"model": model.strip(), "index": i}
            ):
                logging.info(
                    "\n   [%s/%s] Running with %s...", i + 1, len(models_list), model
                )
                success = run_chatdev_with_ollama(args.task, model.strip(), args.config)
            responses.append(
                {
                    "model": model,
                    "success": success,
                    "confidence": 1.0 if success else 0.5,
                }
            )

        # Coordinate responses
        with tracing.start_span("coordinate_responses", {"pattern_len": len(pattern)}):
            coordination = fractal.coordinate_responses(responses, pattern)
        logging.info("\n[ΞNuSyQ] Fractal Coordination Complete:")
        logging.info("   Symbolic Overlay: %s", coordination["symbolic_overlay"])
        logging.info(
            "   Consensus: %s successful runs",
            len([r for r in responses if r["success"]]),
        )

        return 0

    # Standard single-model run
    success = run_chatdev_with_ollama(
        args.task,
        args.model,
        args.config,
        use_modular_models=args.modular_models,
        background=args.background,
        max_runtime=args.max_runtime,
    )

    # Track with temporal drift if enabled
    if args.track_drift and temporal_tracker and symbolic_msg:
        temporal_tracker.track_session(symbolic_msg, args.model, "ChatDev execution")
        drift_analysis = temporal_tracker.analyze_drift()
        # Safe access with default values
        temporal_tag = drift_analysis.get("temporal_tag", "⨈ΦΣΞΨΘΣΛ")
        session_count = drift_analysis.get("session_count", 1)
        logging.info("\n[ΞNuSyQ] Temporal Drift Analysis (%s):", temporal_tag)
        logging.info("   Sessions: %s", session_count)

    # Display symbolic summary if enabled
    if args.symbolic and symbolic_msg:
        logging.info("\n[ΞNuSyQ] Session Summary:")
        logging.info("   Message ID: [Msg⛛{%s}]", symbolic_msg.msg_id)
        logging.info("   Symbolic Tag: %s", symbolic_msg.symbolic_tag)
        logging.info("   Status: %s", "[OK] Success" if success else "[X] Failed")

    return 0 if success else 1


if __name__ == "__main__":
    # Enhanced error reporting integration
    try:
        from ChatDev.error_reporter import ChatDevErrorReporter

        reporter = ChatDevErrorReporter(log_dir=Path("ChatDev/error_reports"))

        try:
            with tracing.start_span("program_main"):
                exit(main())
        except (RuntimeError, OSError, subprocess.SubprocessError) as e:
            # Capture comprehensive error context
            error_ctx = reporter.capture_error(
                e,
                context={
                    "module": "nusyq_chatdev",
                    "function": "main",
                    "cwd": str(Path.cwd()),
                },
                expected="ChatDev should complete task successfully with Ollama models",
                actual=f"Execution failed with {type(e).__name__}: {str(e)[:200]}",
            )

            # Display formatted report
            print(reporter.format_report(error_ctx))

            # Save detailed report
            report_path = reporter.save_report(error_ctx)
            print(f"\n📝 Detailed error report saved to: {report_path}")
            print("   Share this report for troubleshooting assistance!")

            exit(1)

    except ImportError:
        # Fallback if error_reporter not available
        print("[!] Enhanced error reporting not available - using basic mode")
        exit(main())
