#!/usr/bin/env python3
"""🚀 KILO-FOOLISH ChatDev Integration Launcher.

Enhanced ChatDev launcher with KILO-FOOLISH secrets integration and structured logging.

OmniTag: {
    "purpose": "ChatDev launcher with API key management",
    "dependencies": ["src.setup.secrets", "ChatDev_CORE"],
    "context": "AI agent orchestration, backup LLM system",
    "evolution_stage": "v4.0_logging_enhanced"
}
MegaTag: {
    "type": "AIIntegration",
    "integration_points": ["chatdev", "secrets_manager", "ollama_fallback"],
    "related_tags": ["AIOrchestration", "SecureConfig", "BackupLLM"]
}
RSHTS: ΞΨΩ∞⟨CHATDEV⟩→ΦΣΣ
"""

import contextlib
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, cast

from src.config.feature_flag_manager import is_feature_enabled
from src.integration.sandbox_runner import get_sandbox_runner
from src.system.policy import enforce_policy
from src.system.run_protocol import (build_claims_evidence,
                                     build_handoff_template,
                                     materialize_run_bundle)

from ..utils.constants import AIModel
from ..utils.helpers import join_path

# File name constants
RUN_PY_FILENAME = "run.py"
RUN_OLLAMA_FILENAME = "run_ollama.py"

# Configure enhanced logging to handle Unicode properly on Windows
if sys.platform == "win32":
    import codecs

    # Reconfigure stdout to handle UTF-8
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "replace")

# Add repository src directory to Python path for KILO-FOOLISH imports
current_dir = Path(__file__).parent.resolve()
repo_root = current_dir.parent.parent
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    from src.setup.secrets import SecureConfig

    KILO_SECRETS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"KILO-FOOLISH secrets not available: {e}")
    KILO_SECRETS_AVAILABLE = False

# Configure enhanced structured logging
_CHATDEV_LOG_FORMAT = "🤖 [%(asctime)s] CHATDEV: %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=_CHATDEV_LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)


class ChatDevLauncher:
    """Enhanced ChatDev launcher with KILO-FOOLISH integration.

    Manages API keys, environment setup, and fallback systems.
    """

    def __repr__(self) -> str:
        """Return debug representation."""
        return f"ChatDevLauncher(config_loaded={self.config is not None}, api_configured={self.api_key_configured})"

    def __init__(self) -> None:
        """Initialize ChatDevLauncher."""
        import json

        self.api_key_configured = False
        self.openai_key_source: str | None = None
        self.config = None
        self.last_stdout_log: Path | None = None
        self.last_stderr_log: Path | None = None

        # Load settings.json
        settings_path = Path(__file__).parent / "settings.json"
        if settings_path.exists():
            with open(settings_path) as f:
                try:
                    self.settings = json.load(f)
                except (json.JSONDecodeError, ValueError, OSError) as e:
                    logger.warning(f"⚠️ Failed to load settings.json: {e}")
                    self.settings = {}
        else:
            self.settings = {}

        self.use_ollama = bool(self.settings.get("use_ollama", False)) or bool(
            os.getenv("CHATDEV_USE_OLLAMA")
        )
        self.ollama_base_url = str(
            self.settings.get("ollama_base_url")
            or os.getenv("BASE_URL")
            or "http://localhost:11434/v1"
        )

        # Initialize KILO-FOOLISH configuration
        if KILO_SECRETS_AVAILABLE:
            try:
                self.config = SecureConfig()
                logger.info("✅ KILO-FOOLISH secrets configuration loaded")
            except Exception as e:
                logger.warning(f"⚠️  Failed to load KILO-FOOLISH config: {e}")

        # Resolve ChatDev installation path from environment or config
        self.chatdev_path = self._resolve_chatdev_path()

        # Use settings.json for debug and log_level
        debug = self.settings.get("debug", False)
        log_level = self.settings.get("log_level", "INFO")
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        if debug:
            logger.info("Debug mode enabled from settings.json")

        # Validate ChatDev installation and choose runner
        self.runner = self._validate_chatdev_installation()
        self._ensure_writable_runtime_path()
        self.runner = self._validate_chatdev_installation()

    @staticmethod
    def _normalize_path(path_value: str | Path) -> Path:
        """Normalize Windows-style paths when running under WSL/Linux."""
        raw = str(path_value).strip().strip('"').strip("'")
        if os.name != "nt":
            match = re.match(r"^([A-Za-z]):[\\/](.*)$", raw)
            if match:
                drive = match.group(1).lower()
                remainder = match.group(2).replace("\\", "/")
                raw = f"/mnt/{drive}/{remainder}"
        return Path(raw).expanduser()

    def _resolve_chatdev_path(self) -> Path:
        """Determine ChatDev installation path from env var or config."""
        env_path = os.getenv("CHATDEV_PATH")
        if env_path:
            return self._normalize_path(env_path)

        if self.config and self.config.has_secret("chatdev", "path"):
            try:
                return self._normalize_path(self.config.get_secret("chatdev", "path"))
            except Exception as e:
                logger.warning(f"⚠️  Invalid ChatDev path in config: {e}")

        # Fallback to settings.json for chatdev_path
        chatdev_path_str = self.settings.get("chatdev_path")
        if chatdev_path_str:
            return self._normalize_path(chatdev_path_str)

        # Auto-discovery fallbacks for known local installs used in NuSyQ tripartite setup.
        candidate_paths = [
            Path("C:/Users/keath/NuSyQ/ChatDev"),
            Path("C:/Users/keath/Desktop/Legacy/ChatDev_CORE/ChatDev-main"),
            Path("/mnt/c/Users/keath/NuSyQ/ChatDev"),
            Path.home() / "NuSyQ" / "ChatDev",
        ]
        for candidate in candidate_paths:
            if (candidate / RUN_PY_FILENAME).exists():
                logger.info(f"🔎 Auto-discovered ChatDev path: {candidate}")
                return candidate

        msg = "ChatDev path not configured. Set CHATDEV_PATH environment variable or add 'chatdev_path' to settings.json"
        raise FileNotFoundError(
            msg,
        )

    def _validate_chatdev_installation(self) -> Path:
        """Validate that ChatDev is properly installed and return runner path."""
        if not self.chatdev_path.exists():
            msg = f"ChatDev not found at {self.chatdev_path}"
            raise FileNotFoundError(msg)

        run_py = self.chatdev_path / RUN_PY_FILENAME
        run_ollama = self.chatdev_path / RUN_OLLAMA_FILENAME
        if self.use_ollama and run_ollama.exists():
            runner = run_ollama
        elif run_py.exists():
            runner = run_py
        elif run_ollama.exists():
            runner = run_ollama
        else:
            msg = f"ChatDev entrypoint not found (expected run.py or run_ollama.py under {self.chatdev_path})"
            raise FileNotFoundError(msg)

        logger.info(
            f"✅ ChatDev installation validated at {self.chatdev_path} (runner={runner.name})"
        )
        return runner

    def _probe_warehouse_writable(self, root: Path) -> tuple[bool, str]:
        """Check whether ChatDev WareHouse under `root` is writable."""
        warehouse = root / "WareHouse"
        try:
            warehouse.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            return False, f"warehouse_create_failed: {exc}"

        probe = warehouse / f"nq_probe_{os.getpid()}_{int(time.time() * 1000)}.tmp"
        try:
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return True, "ok"
        except Exception as exc:
            with contextlib.suppress(Exception):
                probe.unlink(missing_ok=True)
            return False, str(exc)

    def _ensure_writable_runtime_path(self) -> None:
        """Auto-heal read-only ChatDev installs by using a writable shadow runtime path."""
        writable, reason = self._probe_warehouse_writable(self.chatdev_path)
        if writable:
            return

        shadow_root = repo_root / "state" / "runtime" / "chatdev_shadow"
        shadow_root.parent.mkdir(parents=True, exist_ok=True)

        logger.warning(
            "⚠️ ChatDev WareHouse not writable at %s (%s). Activating writable shadow runtime at %s",
            self.chatdev_path,
            reason,
            shadow_root,
        )

        if not (shadow_root / RUN_PY_FILENAME).exists():
            shutil.copytree(
                self.chatdev_path,
                shadow_root,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns(
                    "__pycache__",
                    "*.pyc",
                    "*.pyo",
                    "WareHouse",
                    ".git",
                ),
            )

        (shadow_root / "WareHouse").mkdir(parents=True, exist_ok=True)
        shadow_writable, shadow_reason = self._probe_warehouse_writable(shadow_root)
        if not shadow_writable:
            msg = f"ChatDev WareHouse is not writable at original path ({reason}) or shadow path ({shadow_reason})."
            raise RuntimeError(msg)

        self.chatdev_path = shadow_root
        logger.info("✅ ChatDev runtime switched to writable shadow path: %s", self.chatdev_path)

    @staticmethod
    def _looks_like_placeholder_api_key(candidate: str) -> bool:
        lowered = candidate.lower()
        placeholder_markers = (
            "your-",
            "replace-",
            "enter-",
            "todo",
            "example",
            "placeholder",
            "redacted",
            "config",
            "api_key",
            "sk-your",
        )
        return any(
            marker in lowered for marker in placeholder_markers
        ) or candidate.strip().startswith("${")

    @classmethod
    def _is_probably_valid_openai_key(cls, candidate: Any) -> bool:
        if not isinstance(candidate, str):
            return False
        key = candidate.strip()
        if len(key) < 20:
            return False
        if any(ch.isspace() for ch in key):
            return False
        if cls._looks_like_placeholder_api_key(key):
            return False
        if key.startswith(("sk-", "sess-")) and len(key) >= 24:
            return True
        return bool(re.fullmatch(r"[A-Za-z0-9._\-]{32,}", key))

    def _collect_api_key_candidates(self) -> list[tuple[str, str]]:
        candidates: list[tuple[str, str]] = []

        env_key = os.getenv("OPENAI_API_KEY")
        if env_key:
            candidates.append(("environment", env_key))

        if self.config and self.config.has_secret("openai", "api_key"):
            try:
                secret_key = self.config.get_secret("openai", "api_key")
                if isinstance(secret_key, str) and secret_key:
                    candidates.append(("kilo_secrets", secret_key))
            except Exception as e:
                logger.warning(f"⚠️  Failed to retrieve API key from KILO config: {e}")

        settings_key = self.settings.get("openai_api_key", "")
        if isinstance(settings_key, str) and settings_key:
            candidates.append(("settings", settings_key))

        return candidates

    def _try_enable_ollama_mode(self, reason: str, key_for_compat: str = "ollama") -> bool:
        run_ollama = self.chatdev_path / RUN_OLLAMA_FILENAME
        if not run_ollama.exists():
            logger.warning(
                "⚠️ Ollama fallback requested but %s is missing; reason=%s",
                run_ollama,
                reason,
            )
            return False

        self.use_ollama = True
        os.environ["OPENAI_API_KEY"] = key_for_compat or "ollama"
        os.environ["BASE_URL"] = self.ollama_base_url
        self.openai_key_source = "ollama_fallback"
        self.api_key_configured = True
        logger.warning(
            "🦙 ChatDev switched to Ollama mode (BASE_URL=%s, reason=%s)",
            self.ollama_base_url,
            reason,
        )
        return True

    def _resolve_runtime_model(self, model: str) -> str:
        """Resolve model name for the active runtime (OpenAI or Ollama)."""
        requested = str(model or "").strip()
        if not self.use_ollama:
            return requested or AIModel.GPT_3_5_TURBO.value

        default_ollama_model = str(
            os.getenv("NUSYQ_CHATDEV_OLLAMA_MODEL")
            or self.settings.get("ollama_model")
            or "qwen2.5-coder:7b"
        ).strip()
        aliases = {
            "GPT_3_5_TURBO": default_ollama_model,
            "GPT_4": default_ollama_model,
            "GPT_4_TURBO": default_ollama_model,
            "GPT_4O": default_ollama_model,
            "GPT_4O_MINI": default_ollama_model,
            "CLAUDE_3_SONNET": default_ollama_model,
        }
        upper_requested = requested.upper()
        if not requested:
            return default_ollama_model
        if upper_requested in aliases:
            mapped = aliases[upper_requested]
            logger.warning(
                "🦙 Remapping ChatDev model for Ollama: %s -> %s",
                requested,
                mapped,
            )
            return mapped
        if requested.lower().startswith("gpt-"):
            logger.warning(
                "🦙 Replacing OpenAI model %s with Ollama default %s",
                requested,
                default_ollama_model,
            )
            return default_ollama_model
        return requested

    def setup_api_key(self) -> bool:
        """Configure OpenAI API key for ChatDev.

        Returns True if successfully configured.
        """
        api_key: str | None = None
        api_key_source: str | None = None
        suspicious_sources: list[str] = []

        for source, candidate in self._collect_api_key_candidates():
            if self._is_probably_valid_openai_key(candidate):
                api_key = candidate.strip()
                api_key_source = source
                logger.info("🔑 Selected OpenAI API key from %s", source)
                break
            suspicious_sources.append(source)
            logger.warning("⚠️ Skipping suspicious OpenAI API key from %s", source)

        # Ollama mode: ChatDev only needs OpenAI-compatible base URL and a non-empty key.
        if self.use_ollama:
            os.environ.setdefault("OPENAI_API_KEY", api_key or "ollama")
            os.environ["BASE_URL"] = self.ollama_base_url
            self.openai_key_source = api_key_source or "ollama"
            self.api_key_configured = True
            logger.info(f"🦙 ChatDev Ollama mode enabled (BASE_URL={self.ollama_base_url})")
            return True

        # Validate API key
        if not api_key:
            auto_ollama_fallback = str(
                os.getenv("NUSYQ_CHATDEV_AUTO_OLLAMA_FALLBACK", "1")
            ).strip().lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
            if auto_ollama_fallback:
                reason = (
                    "no_valid_openai_key"
                    if not suspicious_sources
                    else f"no_valid_openai_key (suspicious_sources={','.join(suspicious_sources)})"
                )
                if self._try_enable_ollama_mode(reason=reason):
                    return True

            logger.error("❌ No valid OpenAI API key found!")
            logger.info("💡 To configure API key:")
            logger.info("   1. Set OPENAI_API_KEY environment variable, OR")
            logger.info("   2. Add to your KILO-FOOLISH secrets configuration")
            logger.info("   3. Or add to settings.json in integration/")
            return False
        if not isinstance(api_key, str) or len(api_key.strip()) < 20:
            logger.error("❌ Invalid API key format")
            return False
        # Check for placeholder values
        if self._looks_like_placeholder_api_key(api_key):
            logger.error("❌ API key appears to be a placeholder!")
            logger.info("💡 Please replace with your actual OpenAI API key")
            return False
        # set environment variable for ChatDev
        os.environ["OPENAI_API_KEY"] = api_key
        self.openai_key_source = api_key_source or "unknown"
        self.api_key_configured = True
        logger.info("✅ OpenAI API key configured for ChatDev")
        return True

    def setup_environment(self) -> None:
        """Setup additional environment variables for ChatDev."""
        # set Python path for ChatDev
        chatdev_path_str = str(self.chatdev_path)
        if chatdev_path_str not in sys.path:
            sys.path.insert(0, chatdev_path_str)

        # set working directory environment
        os.environ["CHATDEV_ROOT"] = chatdev_path_str

        # Ensure Ollama-compatible env defaults
        if self.use_ollama:
            os.environ.setdefault("BASE_URL", self.ollama_base_url)
            # ChatDev expects OPENAI-style variables even when pointed at Ollama
            os.environ.setdefault("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", "ollama"))

        # Optional: Configure additional settings from KILO config
        if self.config and self.config.has_secret("system", "debug"):
            # set debug mode if configured
            debug_mode = self.config.get_secret("system", "debug", False)
            if debug_mode:
                os.environ["CHATDEV_DEBUG"] = "true"

        logger.info("🌐 ChatDev environment configured")

    def launch_chatdev(
        self,
        task: str = "Create a simple calculator app",
        name: str = "Calculator",
        model: str = "GPT_3_5_TURBO",
        organization: str = "KiloFoolish",
        config: str = "Default",
        git_mode: bool = False,
        git_branch: str | None = None,
        sandbox: bool = False,
        degraded_mode: bool = False,
    ) -> subprocess.Popen[str] | subprocess.CompletedProcess[str]:
        """Launch ChatDev with specified parameters.

        Args:
            task: Description of the software to develop
            name: Name of the software project
            model: GPT model to use
            organization: Organization name
            config: Configuration to use
            git_mode: Enable git-mode mirroring (tracks changes in git).
            git_branch: Branch name to use when git_mode is enabled.
            sandbox: Run in isolated Docker sandbox (requires Docker).
            degraded_mode: Run in degraded (offline/local) mode.

        Returns:
            subprocess.Popen object for the ChatDev process

        """
        if not self.api_key_configured and not self.setup_api_key():
            msg = "Cannot launch ChatDev without API key"
            raise RuntimeError(msg)

        self.setup_environment()
        if degraded_mode:
            os.environ["NUSYQ_DEGRADED_MODE"] = "1"

        # Optional git-mode (mirrors OpenBMB git_mode support)
        if git_mode:
            os.environ["CHATDEV_GIT_MODE"] = "true"
            if git_branch:
                os.environ["CHATDEV_GIT_BRANCH"] = git_branch

        # Prepare ChatDev command
        runner = (
            self.chatdev_path / RUN_OLLAMA_FILENAME
            if self.use_ollama and (self.chatdev_path / RUN_OLLAMA_FILENAME).exists()
            else self.chatdev_path / RUN_PY_FILENAME
        )
        # fall back to validated runner if nothing else
        if not runner.exists():
            runner = self.runner

        runtime_model = self._resolve_runtime_model(model)

        cmd = [
            sys.executable,
            str(runner),
            "--task",
            task,
            "--name",
            name,
            "--model",
            runtime_model,
            "--org",
            organization,
            "--config",
            config,
        ]

        logger.info(f"🚀 Launching ChatDev with task: {task}")
        logger.info(f"📝 Project: {name} | Model: {runtime_model} | Org: {organization}")

        # Change to ChatDev directory
        original_cwd = os.getcwd()
        os.chdir(self.chatdev_path)

        try:
            # Setup logging for subprocess output
            log_dir = repo_root / "logs" / "chatdev"
            log_dir.mkdir(parents=True, exist_ok=True)

            import time

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            stdout_log = log_dir / f"chatdev_stdout_{timestamp}.log"
            stderr_log = log_dir / f"chatdev_stderr_{timestamp}.log"
            self.last_stdout_log = stdout_log
            self.last_stderr_log = stderr_log

            # Optional policy check (PII/keys)
            policy = enforce_policy(task)
            if policy.get("policy") == "blocked":
                raise RuntimeError(f"Policy blocked task: {policy}")

            # Optional sandbox execution
            if sandbox and is_feature_enabled("sandbox_runner_enabled"):
                runner_env = {
                    "CHATDEV_PATH": str(self.chatdev_path),
                    "CHATDEV_USE_OLLAMA": "1" if self.use_ollama else "0",
                    "BASE_URL": os.getenv("BASE_URL", ""),
                    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
                    "NUSYQ_DEGRADED_MODE": "1" if degraded_mode else "",
                }
                sb = get_sandbox_runner()
                sb_res = sb.run(cmd, env=runner_env, readonly_mount=self.chatdev_path)
                if not sb_res.success:
                    raise RuntimeError(f"Sandbox run failed: {sb_res.stderr or sb_res.stdout}")
                # In sandbox mode, no live PID; emulate process object with None PID
                process: subprocess.Popen[str] | subprocess.CompletedProcess[str] = (
                    subprocess.CompletedProcess(cmd, sb_res.returncode)
                )
                logger.info("✅ ChatDev sandbox run completed")
            else:
                # Launch ChatDev process with logging to files
                stdout_handle = open(stdout_log, "w", encoding="utf-8")
                stderr_handle = open(stderr_log, "w", encoding="utf-8")
                process = subprocess.Popen(
                    cmd,
                    stdout=stdout_handle,
                    stderr=stderr_handle,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                )
                # Child owns duplicated descriptors; parent can close its handles.
                stdout_handle.close()
                stderr_handle.close()

                # Guardrail: if process exits during warmup, report truthful failure details.
                warmup_seconds = int(os.getenv("CHATDEV_LAUNCH_GUARD_SECONDS", "15"))
                early_exit_code: int | None = None
                try:
                    early_exit_code = process.wait(timeout=warmup_seconds)
                except subprocess.TimeoutExpired:
                    early_exit_code = None
                if early_exit_code is not None:
                    stderr_tail = ""
                    stdout_tail = ""
                    warehouse_tail = ""
                    with contextlib.suppress(Exception):
                        stderr_tail = stderr_log.read_text(encoding="utf-8", errors="replace")[
                            -1200:
                        ]
                    with contextlib.suppress(Exception):
                        stdout_tail = stdout_log.read_text(encoding="utf-8", errors="replace")[
                            -1200:
                        ]
                    try:
                        warehouse_log = (
                            self.chatdev_path
                            / "WareHouse"
                            / f"{name}_{organization}_{timestamp}.log"
                        )
                        if warehouse_log.exists():
                            warehouse_tail = warehouse_log.read_text(
                                encoding="utf-8", errors="replace"
                            )[-1800:]
                    except Exception:
                        logger.debug("Suppressed Exception", exc_info=True)
                    msg = (
                        "ChatDev process exited immediately "
                        f"(pid={process.pid}, code={early_exit_code}). "
                        f"stderr_tail={stderr_tail!r} stdout_tail={stdout_tail!r} "
                        f"warehouse_tail={warehouse_tail!r}"
                    )
                    logger.error(f"❌ {msg}")
                    raise RuntimeError(msg)

                logger.info(f"✅ ChatDev launched with PID: {process.pid}")
                logger.info(f"📝 Logs: {stdout_log} | {stderr_log}")

            # Run Protocol: materialize artifact bundle (Phase 1)
            if is_feature_enabled("trust_artifacts_enabled"):
                try:
                    manifest = {
                        "task": task,
                        "name": name,
                        "model": model,
                        "requested_model": model,
                        "organization": organization,
                        "config": config,
                        "git_mode": git_mode,
                        "git_branch": git_branch,
                        "use_ollama": self.use_ollama,
                        "runner": str(runner),
                        "sandbox": sandbox,
                        "logs": {"stdout": str(stdout_log), "stderr": str(stderr_log)},
                        "env": {
                            "CHATDEV_PATH": str(self.chatdev_path),
                            "BASE_URL": os.getenv("BASE_URL", ""),
                        },
                    }
                    claims = build_claims_evidence(
                        [
                            {
                                "claim": "ChatDev run initiated",
                                "evidence": "process.pid",
                                "pointer": str(cast(subprocess.Popen[str], process).pid),
                            }
                        ]
                    )
                    handoff = build_handoff_template(
                        changes=[
                            f"Started ChatDev task '{task}' (PID {cast(subprocess.Popen[str], process).pid})"
                        ],
                        next_actions=["Monitor run output", "Ingest artifacts when finished"],
                        do_not_touch=["Do not kill process unless failing"],
                        impact=[f"Workspace: {self.chatdev_path}"],
                        suggested_agent="Copilot",
                    )
                    paths = materialize_run_bundle(
                        manifest=manifest,
                        replay_cmd=cmd,
                        replay_env={
                            "CHATDEV_PATH": str(self.chatdev_path),
                            "CHATDEV_USE_OLLAMA": "1" if self.use_ollama else "0",
                            "BASE_URL": os.getenv("BASE_URL", ""),
                        },
                        handoff=handoff,
                        claims=claims,
                    )
                    logger.info(f"🗂️  Run protocol bundle: {paths.base}")
                except Exception as rp_err:
                    logger.warning(f"Run protocol bundle skipped: {rp_err}")

            logger.debug(
                "ChatDev launcher returning process handle (pid=%s)", getattr(process, "pid", None)
            )

            try:
                from src.system.agent_awareness import emit as _emit

                _pid = getattr(process, "pid", "sandbox")
                _emit(
                    "tasks",
                    f"ChatDev launch: task={task[:60]} name={name} pid={_pid} model={runtime_model}",
                    level="INFO",
                    source="chatdev_launcher",
                )
            except Exception:
                pass

            return process

        except Exception as e:
            logger.exception(f"❌ Failed to launch ChatDev: {e}")
            try:
                from src.system.agent_awareness import emit as _emit

                _emit(
                    "tasks",
                    f"ChatDev launch FAILED: {str(e)[:100]}",
                    level="ERROR",
                    source="chatdev_launcher",
                )
            except Exception:
                pass
            raise
        finally:
            # Restore original working directory
            os.chdir(original_cwd)
            logger.debug("Restored working directory to %s", original_cwd)

    def launch_interactive(self) -> subprocess.Popen | None:
        """Launch ChatDev with interactive prompts."""
        logger.info("Starting KILO-FOOLISH ChatDev Interactive Launcher")
        logger.info("=" * 50)

        # Setup API key
        if not self.setup_api_key():
            logger.error("Cannot proceed without API key configuration")
            return None

        # Check for special modes
        logger.info("Select ChatDev Mode:")
        logger.info("1. 🧪 Testing Chamber (Ollama Integration Development)")
        logger.info("2. 🚀 Standard Interactive Mode")
        logger.info("3. 📋 Predefined Task Templates")

        mode_choice = input("Select mode (1-3): ").strip()

        if mode_choice == "1":
            return self.launch_testing_chamber_mode()
        if mode_choice == "3":
            return self.launch_template_mode()
        # Continue with standard mode for choice "2" or default

        # Get user input
        task = input("📝 Enter the software task description: ").strip()
        if not task:
            task = "Create a simple calculator app"

        name = input("🏷️  Enter project name (or press Enter for 'Calculator'): ").strip()
        if not name:
            name = "Calculator"

        model_options = AIModel.get_openai_models()
        logger.info(f"Available models: {', '.join(model_options)}")
        model = input("🧠 Select model (or press Enter for GPT_3_5_TURBO): ").strip()
        if not model or model not in model_options:
            model = AIModel.GPT_3_5_TURBO.value

        # Launch ChatDev
        try:
            process = cast(
                subprocess.Popen[str], self.launch_chatdev(task=task, name=name, model=model)
            )

            logger.info("ChatDev launched successfully!")
            logger.info(f"Process ID: {process.pid}")
            logger.info(f"Output will be in: {self.chatdev_path}/WareHouse/{name}_KiloFoolish_*")
            logger.info("Monitoring ChatDev output... (Ctrl+C to stop monitoring)")

            # Monitor output
            try:
                if process.stdout is None:
                    logger.warning("ChatDev stdout is not available for monitoring.")
                    return process
                while True:
                    output = process.stdout.readline()
                    if output == "" and process.poll() is not None:
                        break
                    if output:
                        logger.info(f"ChatDev: {output.strip()}")

            except KeyboardInterrupt:
                logger.info("Stopped monitoring. ChatDev continues running in background.")
                logger.info(f"Process ID: {process.pid}")

            return process

        except Exception as e:
            logger.exception(f"Failed to launch ChatDev: {e}")
            return None

    def check_status(self) -> dict[str, Any]:
        """Check ChatDev integration status."""
        status = {
            "chatdev_installed": self.chatdev_path.exists(),
            "chatdev_installation": self.chatdev_path.exists(),  # legacy key
            "chatdev_path": str(self.chatdev_path),
            "kilo_secrets_available": KILO_SECRETS_AVAILABLE,
            "api_key_configured": self.api_key_configured,
            "openai_key_source": self.openai_key_source,
            "config_loaded": self.config is not None,
            "runner": ((r := getattr(self, "runner", None)) and r.name) or None,
            "use_ollama": self.use_ollama,
        }

        # Check for recent projects
        warehouse_path = self.chatdev_path / "WareHouse"
        if warehouse_path.exists():
            projects = list(warehouse_path.glob("*"))
            status["recent_projects"] = len(projects)
            status["latest_project"] = (
                max(projects, key=lambda p: p.stat().st_ctime).name if projects else None
            )

        return status

    def launch_testing_chamber_mode(self) -> subprocess.Popen | None:
        """Launch ChatDev in testing chamber mode leveraging existing Ollama integration."""
        logger.info("🧪 TESTING CHAMBER MODE - Leveraging Existing Infrastructure")
        logger.info("Using your existing ChatDev-Ollama integration systems")
        logger.info("-" * 60)

        # Check for existing infrastructure
        src_path = join_path(Path(__file__).parent, "src")
        integration_files = [
            "integration/Update-ChatDev-to-use-Ollama.py",
            "integration/chatdev_llm_adapter.py",
            "integration/chatdev_environment_patcher.py",
            "ai/ai_coordinator.py",
        ]

        available_integrations: list[Any] = []
        for file_path in integration_files:
            full_path = src_path / file_path
            if full_path.exists():
                available_integrations.append(file_path)

        logger.info(f"Found {len(available_integrations)} existing integration components:")
        for integration in available_integrations:
            logger.info(f"   • {integration}")

        # Enhanced task leveraging existing infrastructure
        enhanced_task = f"""
        Enhance and extend the existing KILO-FOOLISH ChatDev-Ollama integration:

        EXISTING INFRASTRUCTURE TO LEVERAGE:
        {chr(10).join(f"        {integration}" for integration in available_integrations)}

        ENHANCEMENT OBJECTIVES:
        1. Advanced Copilot Integration Bridge
           Context sharing between Copilot and Ollama/ChatDev
           Intelligent suggestion enhancement
           Workspace-aware development assistance

        2. Recursive Improvement Engine
           Self-analyzing code quality
           Automatic pattern recognition and suggestion
           Context-aware architectural guidance

        3. Multi-AI Orchestration Hub
           Intelligent routing between Ollama, ChatDev, and OpenAI
           Load balancing and fallback mechanisms
           Performance optimization and monitoring

        4. Enhanced Testing Chamber
           Automated integration testing
           Performance benchmarking
           Context validation and improvement

        5. VS Code Integration Enhancements
           Custom commands and shortcuts
           Workspace settings optimization
           Extension bridge for enhanced development

        TECHNICAL REQUIREMENTS:
        Build upon existing ChatDevOllamaAdapter class
        Integrate with existing AI coordinator patterns
        Maintain KILO-FOOLISH OmniTag/MegaTag/RSHTS conventions
        Implement comprehensive error handling and logging
        Create modular, extensible architecture
        Include comprehensive test suite

        The system should be production-ready and seamlessly integrate with
        the existing KILO-FOOLISH ecosystem while providing significant enhancements
        to the development workflow.
        """

        logger.info("Enhanced Task: Multi-AI Development Environment")
        logger.info(f"Leveraging: {len(available_integrations)} existing components")

        return cast(
            subprocess.Popen[str],
            self.launch_chatdev(
                task=enhanced_task,
                name="KILOAdvancedMultiAIHub",
                model=AIModel.GPT_4.value,  # Use more powerful model for complex integration
                organization="KiloFoolishAdvanced",
            ),
        )

    def launch_template_mode(self) -> subprocess.Popen | None:
        """Launch ChatDev with predefined task templates."""
        logger.info("📋 PREDEFINED TASK TEMPLATES")
        logger.info("=" * 30)

        templates = {
            "1": {
                "name": "AI Integration System",
                "task": "Create a multi-AI integration system that can orchestrate between different AI providers (Ollama, OpenAI, Anthropic) with intelligent routing and fallback mechanisms.",
            },
            "2": {
                "name": "Testing Framework",
                "task": "Develop a comprehensive testing framework for AI integrations with automated testing, monitoring, and reporting capabilities.",
            },
            "3": {
                "name": "Configuration Manager",
                "task": "Build a secure configuration management system for AI applications with secrets handling, environment management, and validation.",
            },
            "4": {
                "name": "Logging System",
                "task": "Create an advanced logging and monitoring system for AI applications with structured logging, metrics, and alerting.",
            },
        }

        for key, template in templates.items():
            logger.info(f"{key}. {template['name']}")

        choice = input("\nSelect template (1-4): ").strip()

        if choice in templates:
            template = templates[choice]
            project_name = template["name"].replace(" ", "")

            return cast(
                subprocess.Popen[str],
                self.launch_chatdev(
                    task=template["task"],
                    name=project_name,
                    model=AIModel.GPT_3_5_TURBO.value,
                    organization="KiloFoolishTemplates",
                ),
            )
        logger.error("Invalid template selection")
        return None


def main() -> None:
    """Main entry point for ChatDev launcher."""
    try:
        launcher = ChatDevLauncher()

        # Check if command line arguments are provided
        if len(sys.argv) > 1:
            if sys.argv[1] == "status":
                status = launcher.check_status()
                logger.info("ChatDev Integration Status")
                logger.info("=" * 40)
                for key, value in status.items():
                    logger.info(f"{key}: {value}")
                return
            if sys.argv[1] == "setup":
                success = launcher.setup_api_key()
                if success:
                    logger.info("API key configured successfully!")
                else:
                    logger.error("Failed to configure API key")
                return

        # Launch interactive mode
        launcher.launch_interactive()

    except Exception as e:
        logger.exception(f"ChatDev launcher failed: {e}")


if __name__ == "__main__":
    main()
