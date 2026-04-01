#!/usr/bin/env python3
"""ChatDev Autonomous Multi-Agent Router.

============================================================

Routes autonomous healing tasks to ChatDev's multi-agent team:
- Task decomposition into sub-tasks suitable for multi-agent development
- Agent assignment (CEO, CTO, Programmer, Tester, Product Manager)
- Progress tracking and async execution
- Integration with extended autonomous cycle runner

Enables full autonomous software development with ChatDev!
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Constants
NUSYQ_FACADE_UNAVAILABLE_ERROR = "NuSyQ facade not available"

get_repo_path: Callable[[str], Path] | None = None
try:
    from src.utils.repo_path_resolver import \
        get_repo_path as _resolved_get_repo_path
except ImportError:  # pragma: no cover - fallback for isolated runs
    _resolved_get_repo_path = None
get_repo_path = _resolved_get_repo_path

# Import the unified NuSyQ facade lazily to avoid heavy side effects at module import.
nusyq = None
Result = Ok = Fail = None
NUSYQ_FACADE_AVAILABLE = False
_NUSYQ_FACADE_LOADED = False


def _ensure_nusyq_facade_loaded() -> bool:
    """Load NuSyQ facade on first use to keep router imports lightweight."""
    global nusyq, Result, Ok, Fail, NUSYQ_FACADE_AVAILABLE, _NUSYQ_FACADE_LOADED

    if _NUSYQ_FACADE_LOADED:
        return bool(NUSYQ_FACADE_AVAILABLE and nusyq is not None)

    _NUSYQ_FACADE_LOADED = True
    try:
        from src.core.orchestrate import nusyq as loaded_nusyq
        from src.core.result import Fail as loaded_fail
        from src.core.result import Ok as loaded_ok
        from src.core.result import Result as loaded_result

        nusyq = loaded_nusyq
        Result = loaded_result
        Ok = loaded_ok
        Fail = loaded_fail
        NUSYQ_FACADE_AVAILABLE = True
    except ImportError:  # pragma: no cover - optional in isolated runs
        nusyq = None
        Result = Ok = Fail = None
        NUSYQ_FACADE_AVAILABLE = False

    return bool(NUSYQ_FACADE_AVAILABLE and nusyq is not None)


class AgentRole(Enum):
    """ChatDev agent roles in multi-agent team."""

    CEO = "chief_executive_officer"
    CTO = "chief_technology_officer"
    PROGRAMMER = "programmer"
    TESTER = "code_tester"
    PRODUCT_MANAGER = "product_manager"


class TaskCategory(Enum):
    """Categories of tasks suitable for ChatDev routing."""

    CODE_GENERATION = "code_generation"
    BUG_FIX = "bug_fix"
    TEST_GENERATION = "test_generation"
    CODE_REVIEW = "code_review"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"


@dataclass
class ChatDevTask:
    """Represents a task for ChatDev's multi-agent team."""

    task_id: str
    category: TaskCategory
    title: str
    description: str
    codebase_issues: list[dict[str, Any]] = field(default_factory=list)
    assigned_agents: list[AgentRole] = field(default_factory=list)
    status: str = "pending"  # pending, assigned, in_progress, completed
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    execution_log: str = ""
    results: dict[str, Any] = field(default_factory=dict)


class ChatDevAutonomousRouter:
    """Routes autonomous healing tasks to ChatDev multi-agent system."""

    def __init__(self) -> None:
        """Initialize ChatDev router with environment configuration."""
        self.chatdev_path = self._get_chatdev_path()
        self.chatdev_available = self._validate_chatdev_installation()
        self._supported_chatdev_flags: set[str] | None = None
        self._resolved_router_settings: dict[str, str] | None = None
        self.tasks: dict[str, ChatDevTask] = {}
        logger.info("🤖 ChatDev Autonomous Router initialized")
        logger.info(f"   ChatDev Path: {self.chatdev_path}")
        logger.info(f"   Available: {self.chatdev_available}")

    @staticmethod
    def _run_subprocess(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        """Isolated subprocess wrapper for predictable monkeypatching in tests."""
        return subprocess.run(*args, **kwargs)

    async def _run_subprocess_async(
        self,
        command: list[str],
        cwd: Path,
        timeout_s: int,
        wait_timeout_s: int,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        """Execute subprocess in thread only for the default runner.

        When tests monkeypatch `_run_subprocess`, execute inline to avoid
        cross-thread monkeypatch side effects during pytest teardown.
        """
        kwargs = {
            "capture_output": True,
            "text": True,
            "cwd": cwd,
            "timeout": timeout_s,
            "env": env,
        }
        if self._run_subprocess is ChatDevAutonomousRouter._run_subprocess:
            return await asyncio.wait_for(
                asyncio.to_thread(self._run_subprocess, command, **kwargs),
                timeout=wait_timeout_s,
            )
        return self._run_subprocess(command, **kwargs)

    def _get_supported_chatdev_flags(self) -> set[str]:
        """Discover supported CLI flags from ChatDev run.py --help output."""
        if self._supported_chatdev_flags is not None:
            return self._supported_chatdev_flags

        # `--task` is required in every known ChatDev invocation.
        supported_flags: set[str] = {"--task"}
        if not self.chatdev_path:
            self._supported_chatdev_flags = supported_flags
            return supported_flags

        try:
            help_result = self._run_subprocess(
                [sys.executable, str(self.chatdev_path / "run.py"), "--help"],
                capture_output=True,
                text=True,
                cwd=self.chatdev_path,
                timeout=15,
            )
            help_text = f"{help_result.stdout}\n{help_result.stderr}"
            discovered = set(re.findall(r"--[a-zA-Z][a-zA-Z0-9-]*", help_text))
            if discovered:
                supported_flags.update(discovered)
        except Exception as exc:
            logger.debug(f"Could not probe ChatDev CLI flags: {exc}")

        self._supported_chatdev_flags = supported_flags
        return supported_flags

    def _build_chatdev_command(self, task: ChatDevTask) -> list[str]:
        """Build a ChatDev command using only supported CLI flags."""
        if self.chatdev_path is None:
            msg = "ChatDev path is not configured"
            raise ValueError(msg)

        supported_flags = self._get_supported_chatdev_flags()
        chatdev_cmd = [
            sys.executable,
            str(self.chatdev_path / "run.py"),
            "--task",
            task.description,
        ]

        if "--name" in supported_flags:
            chatdev_cmd.extend(["--name", task.title])
        if "--description" in supported_flags:
            chatdev_cmd.extend(["--description", task.description])
        if "--model" in supported_flags:
            # Allow operator override while preserving backward-compatible default.
            runpy_model = os.getenv("CHATDEV_RUNPY_MODEL", "ollama")
            chatdev_cmd.extend(["--model", runpy_model])
        if "--auto-mode" in supported_flags:
            chatdev_cmd.append("--auto-mode")

        return chatdev_cmd

    @staticmethod
    def _read_json_file(path: Path) -> dict[str, Any] | None:
        """Load JSON file safely, returning None on missing/invalid content."""
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            return payload if isinstance(payload, dict) else None
        except (json.JSONDecodeError, ValueError, OSError):
            return None

    def _resolve_router_settings(self) -> dict[str, str]:
        """Resolve ChatDev/Ollama settings from env + project configs."""
        if self._resolved_router_settings is not None:
            return self._resolved_router_settings

        settings: dict[str, str] = {}

        # 1) Environment has highest priority
        env_url = (
            os.getenv("CHATDEV_OLLAMA_URL") or os.getenv("OLLAMA_BASE_URL") or os.getenv("BASE_URL")
        )
        env_model = os.getenv("CHATDEV_OLLAMA_MODEL")
        env_org = os.getenv("CHATDEV_ORG")
        if env_url:
            settings["ollama_base_url"] = env_url
        if env_model:
            settings["ollama_model"] = env_model
        if env_org:
            settings["organization"] = env_org

        # 2) Shared config helper (existing ecosystem source of truth)
        if "ollama_base_url" not in settings:
            try:
                from src.utils.config_helper import get_ollama_host

                helper_url = get_ollama_host()
                if helper_url:
                    settings["ollama_base_url"] = helper_url
            except Exception:
                logger.debug("Suppressed Exception", exc_info=True)

        # 3) Repository configs
        root_settings = self._read_json_file(REPO_ROOT / "config" / "settings.json") or {}
        chatdev_models = (
            self._read_json_file(REPO_ROOT / "config" / "chatdev_ollama_models.json") or {}
        )
        integration_settings = (
            self._read_json_file(REPO_ROOT / "src" / "integration" / "settings.json") or {}
        )

        if "ollama_base_url" not in settings:
            root_ollama = root_settings.get("ollama", {})
            if isinstance(root_ollama, dict):
                host = root_ollama.get("host")
                if isinstance(host, str) and host.strip():
                    settings["ollama_base_url"] = host

        if "ollama_base_url" not in settings:
            endpoint = chatdev_models.get("ollama_endpoint")
            if isinstance(endpoint, str) and endpoint.strip():
                settings["ollama_base_url"] = endpoint

        if "ollama_base_url" not in settings:
            int_ollama_url = integration_settings.get("ollama_base_url")
            if isinstance(int_ollama_url, str) and int_ollama_url.strip():
                settings["ollama_base_url"] = int_ollama_url

        if "ollama_model" not in settings:
            model_group = chatdev_models.get("models", {})
            if isinstance(model_group, dict):
                primary = model_group.get("primary_coder")
                if isinstance(primary, dict):
                    model_name = primary.get("name")
                    if isinstance(model_name, str) and model_name.strip():
                        settings["ollama_model"] = model_name
            if "ollama_model" not in settings:
                assignment_group = chatdev_models.get("agent_assignments", {})
                if isinstance(assignment_group, dict):
                    programmer_model = assignment_group.get("Programmer")
                    if isinstance(programmer_model, str) and programmer_model.strip():
                        settings["ollama_model"] = programmer_model

        if "organization" not in settings:
            int_org = integration_settings.get("organization")
            if isinstance(int_org, str) and int_org.strip():
                settings["organization"] = int_org
            else:
                settings["organization"] = "NuSyQ"

        self._resolved_router_settings = settings
        return settings

    @staticmethod
    def _ensure_openai_compatible_ollama_url(base_url: str) -> str:
        """Normalize Ollama URL to OpenAI-compatible `/v1` form."""
        normalized = base_url.strip().rstrip("/")
        if not normalized:
            return "http://localhost:11434/v1"
        if not re.match(r"^https?://", normalized):
            normalized = f"http://{normalized}"
        if not normalized.endswith("/v1"):
            normalized = f"{normalized}/v1"
        return normalized

    def _build_chatdev_env(self, prefer_ollama: bool = False) -> dict[str, str]:
        """Build subprocess environment from auto-resolved settings."""
        env = os.environ.copy()
        resolved = self._resolve_router_settings()

        base_url = resolved.get("ollama_base_url")
        if base_url:
            openai_compatible_url = self._ensure_openai_compatible_ollama_url(base_url)
            env.setdefault("OLLAMA_BASE_URL", openai_compatible_url)
            env.setdefault("BASE_URL", openai_compatible_url)
            env.setdefault("OPENAI_BASE_URL", openai_compatible_url)

        preferred_model = resolved.get("ollama_model")
        if preferred_model:
            env.setdefault("CHATDEV_MODEL", preferred_model)

        if prefer_ollama:
            env.setdefault("CHATDEV_USE_OLLAMA", "1")
            env.setdefault("OPENAI_API_KEY", env.get("OPENAI_API_KEY", "ollama-local"))

        return env

    @staticmethod
    def _to_ollama_root_url(openai_compatible_url: str) -> str:
        """Convert OpenAI-compatible URL ending in /v1 to Ollama root URL."""
        normalized = openai_compatible_url.rstrip("/")
        if normalized.endswith("/v1"):
            return normalized[:-3]
        return normalized

    @staticmethod
    def _sanitize_project_name(raw: str) -> str:
        """Create a filesystem-safe project name for ChatDev runners."""
        cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", raw).strip("_")
        return cleaned or "NuSyQ_Task"

    def _build_chatdev_ollama_shim_command(self, task: ChatDevTask) -> list[str] | None:
        """Build fallback command for legacy ChatDev installs via run_ollama.py."""
        if self.chatdev_path is None:
            return None

        run_ollama = self.chatdev_path / "run_ollama.py"
        if not run_ollama.exists():
            return None

        project_name = self._sanitize_project_name(task.title)
        resolved = self._resolve_router_settings()
        org_name = resolved.get("organization", "NuSyQ")

        cmd = [
            sys.executable,
            str(run_ollama),
            "--task",
            task.description,
            "--name",
            project_name,
            "--org",
            org_name,
        ]

        explicit_model = resolved.get("ollama_model")
        if explicit_model:
            cmd.extend(["--model", explicit_model])

        ollama_url = resolved.get("ollama_base_url", "http://localhost:11434/v1")
        cmd.extend(["--ollama-url", self._to_ollama_root_url(ollama_url)])
        return cmd

    @staticmethod
    def _chatdev_timeout_seconds() -> int:
        """Resolve ChatDev subprocess timeout from environment with sane bounds."""
        raw = os.getenv("CHATDEV_TASK_TIMEOUT_SECONDS", "300").strip()
        try:
            timeout_s = int(raw)
        except ValueError:
            timeout_s = 300
        return max(30, min(timeout_s, 3600))

    def _should_try_legacy_ollama_shim(self, stderr: str, returncode: int) -> bool:
        """Decide whether to retry through legacy run_ollama.py shim."""
        if returncode == 0 or self.chatdev_path is None:
            return False
        if not (self.chatdev_path / "run_ollama.py").exists():
            return False

        err = (stderr or "").lower()
        indicators = (
            "openai api key not found",
            "keyerror: 'ollama'",
            "invalid choice",
            "unrecognized arguments",
        )
        return any(indicator in err for indicator in indicators)

    @staticmethod
    def _strip_model_flag(command: list[str]) -> list[str]:
        """Return command with `--model <value>` removed."""
        stripped: list[str] = []
        skip_next = False
        for token in command:
            if skip_next:
                skip_next = False
                continue
            if token == "--model":
                skip_next = True
                continue
            stripped.append(token)
        return stripped

    @staticmethod
    def _summarize_chatdev_error(stderr: str, returncode: int) -> str:
        """Normalize common ChatDev failures into actionable messages."""
        stderr = (stderr or "").strip()
        if "OpenAI API key not found" in stderr:
            return (
                "ChatDev runtime is missing credentials (OpenAI API key not found). "
                "Set OPENAI_API_KEY or configure ChatDev to use a local provider/model."
            )
        return stderr[:500] if stderr else f"ChatDev exited with code {returncode}"

    def _get_chatdev_path(self) -> Path | None:
        """Get ChatDev installation path from environment or defaults."""
        # Check environment variable
        env_path = os.getenv("CHATDEV_PATH")
        if env_path and Path(env_path).exists():
            return Path(env_path)

        # Check common installation paths
        resolved_root = None
        if get_repo_path is not None:
            try:
                resolved_root = get_repo_path("NUSYQ_ROOT")
            except Exception:
                resolved_root = None

        common_paths = [
            (resolved_root / "ChatDev") if resolved_root else None,
            Path.home() / "NuSyQ" / "ChatDev",
            Path.home() / "Desktop" / "NuSyQ" / "ChatDev",
            Path("./ChatDev"),
            REPO_ROOT.parent / "ChatDev",
        ]

        for path in common_paths:
            if path and path.exists():
                os.environ["CHATDEV_PATH"] = str(path)
                logger.info(f"✅ Found ChatDev at: {path}")
                return path

        logger.warning("⚠️ ChatDev installation not found")
        return None

    def _validate_chatdev_installation(self) -> bool:
        """Verify ChatDev is properly installed."""
        if not self.chatdev_path:
            return False

        required_files = ["run.py", "camel", "chatdev"]

        for file in required_files:
            if not (self.chatdev_path / file).exists():
                logger.warning(f"⚠️ Missing ChatDev component: {file}")
                return False

        logger.info("✅ ChatDev installation validated")
        return True

    def decompose_issue_into_task(self, issue: dict[str, Any], issue_type: str) -> ChatDevTask:
        """Decompose a detected issue into a ChatDev-compatible task."""
        task_id = f"chatdev_task_{issue.get('issue_id', 'unknown')}"

        # Map issue types to task categories and recommended agents
        category_mapping = {
            "missing_type_hint": (
                TaskCategory.REFACTORING,
                [AgentRole.PROGRAMMER, AgentRole.TESTER],
            ),
            "unused_import": (TaskCategory.REFACTORING, [AgentRole.PROGRAMMER]),
            "style_violation": (TaskCategory.CODE_REVIEW, [AgentRole.PROGRAMMER]),
            "undefined_reference": (
                TaskCategory.BUG_FIX,
                [AgentRole.PROGRAMMER, AgentRole.TESTER],
            ),
            "import_error": (
                TaskCategory.BUG_FIX,
                [AgentRole.CTO, AgentRole.PROGRAMMER],
            ),
            "documentation_gap": (
                TaskCategory.DOCUMENTATION,
                [AgentRole.PRODUCT_MANAGER],
            ),
        }

        category, agents = category_mapping.get(
            issue_type, (TaskCategory.CODE_REVIEW, [AgentRole.PROGRAMMER])
        )

        task = ChatDevTask(
            task_id=task_id,
            category=category,
            title=f"Fix: {issue.get('message', 'Unknown issue')}",
            description=self._generate_task_description(issue, issue_type),
            codebase_issues=[issue],
            assigned_agents=agents,
        )

        self.tasks[task_id] = task
        logger.info(f"📋 Decomposed issue into ChatDev task: {task_id}")
        return task

    def _generate_task_description(self, issue: dict[str, Any], issue_type: str) -> str:
        """Generate detailed task description for ChatDev team."""
        file_path = issue.get("file_path", "unknown")
        line_number = issue.get("line_number", "?")
        message = issue.get("message", "No details")

        desc = f"""
Multi-Agent Code Improvement Task
==================================
Type: {issue_type}
File: {file_path}
Line: {line_number}
Description: {message}

Task for Team:
1. CEO: Review scope and dependencies
2. CTO: Suggest technical solution
3. Programmer: Implement the fix
4. Tester: Validate the changes
5. Product Manager: Ensure code quality standards

Expected Deliverables:
- Fixed code in target file
- Updated tests (if applicable)
- Code review comments
- Documentation updates (if needed)
"""
        return desc

    async def route_task_to_chatdev(self, task: ChatDevTask) -> dict[str, Any]:
        """Route a task to ChatDev for multi-agent execution."""
        if not self.chatdev_available:
            logger.warning("⚠️ ChatDev not available - skipping task routing")
            task.status = "failed"
            return {"success": False, "status": "chatdev_unavailable"}

        task.status = "assigned"
        task.updated_at = datetime.now(UTC)

        logger.info(f"🚀 Routing task to ChatDev: {task.task_id}")
        logger.info(f"   Category: {task.category.value}")
        logger.info(f"   Agents: {[a.value for a in task.assigned_agents]}")

        try:
            # Execute ChatDev task in subprocess
            result = await self._execute_chatdev_task(task)
            task.status = "completed" if result.get("success", False) else "failed"
            task.results = result
            if task.status == "completed":
                logger.info(f"✅ ChatDev task completed: {task.task_id}")
            else:
                logger.warning(f"⚠️ ChatDev task failed: {task.task_id}")
            return result
        except Exception as e:
            logger.error(f"❌ ChatDev task failed: {e}")
            task.status = "failed"
            task.execution_log = str(e)
            return {"success": False, "status": "error", "error": str(e)}

    def route_task(
        self,
        task_description: str,
        codebase_issues: list[dict[str, Any]] | None = None,
        priority: str | int | None = None,
    ) -> dict[str, Any]:
        """Route a simple description into ChatDev for synchronous callers."""
        issue = {
            "issue_id": f"external_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
            "message": task_description,
            "priority": priority,
        }
        task = self.decompose_issue_into_task(issue, "external_task")
        if codebase_issues:
            task.codebase_issues.extend(codebase_issues)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.route_task_to_chatdev(task))
        _dispatch = loop.create_task(self.route_task_to_chatdev(task))
        _dispatch.add_done_callback(lambda t: None)  # keep ref; suppress dangling-task warning
        return {"success": True, "status": "scheduled", "task_id": task.task_id}

    async def _execute_chatdev_task(self, task: ChatDevTask) -> dict[str, Any]:
        """Execute task using ChatDev's multi-agent system."""
        logger.info(f"⚙️ Executing ChatDev task: {task.task_id}")
        timeout_s = self._chatdev_timeout_seconds()
        wait_timeout_s = timeout_s + 10

        if self.chatdev_path is None:
            return {"success": False, "status": "error", "error": "ChatDev path is not configured"}

        # Build ChatDev command with CLI compatibility discovery.
        chatdev_cmd = self._build_chatdev_command(task)

        logger.info(f"   Command: {' '.join(chatdev_cmd).replace(chr(10), ' ')}")

        try:
            # Run ChatDev with timeout
            result = await self._run_subprocess_async(
                command=chatdev_cmd,
                cwd=self.chatdev_path,
                timeout_s=timeout_s,
                wait_timeout_s=wait_timeout_s,
                env=self._build_chatdev_env(prefer_ollama=False),
            )

            # Some ChatDev installs expose --model but reject specific values (e.g. "ollama").
            # Retry once without model override so the local ChatDev default can execute.
            stderr_text = (result.stderr or "").lower()
            if (
                result.returncode != 0
                and "--model" in chatdev_cmd
                and ("keyerror: 'ollama'" in stderr_text or "invalid choice" in stderr_text)
            ):
                fallback_cmd = self._strip_model_flag(chatdev_cmd)
                logger.warning("ChatDev rejected model override; retrying without --model")
                logger.info(f"   Fallback Command: {' '.join(fallback_cmd).replace(chr(10), ' ')}")
                result = await self._run_subprocess_async(
                    command=fallback_cmd,
                    cwd=self.chatdev_path,
                    timeout_s=timeout_s,
                    wait_timeout_s=wait_timeout_s,
                    env=self._build_chatdev_env(prefer_ollama=False),
                )

            # Legacy shim: if classic run.py fails for integration reasons and run_ollama.py
            # is present, retry through the existing local-LLM ChatDev entrypoint.
            if self._should_try_legacy_ollama_shim(result.stderr, result.returncode):
                shim_cmd = self._build_chatdev_ollama_shim_command(task)
                if shim_cmd is not None:
                    logger.warning("ChatDev legacy compatibility shim engaged (run_ollama.py)")
                    logger.info(f"   Shim Command: {' '.join(shim_cmd).replace(chr(10), ' ')}")
                    result = await self._run_subprocess_async(
                        command=shim_cmd,
                        cwd=self.chatdev_path,
                        timeout_s=timeout_s,
                        wait_timeout_s=wait_timeout_s,
                        env=self._build_chatdev_env(prefer_ollama=True),
                    )

            task.execution_log = result.stdout

            was_success = result.returncode == 0
            return {
                "success": was_success,
                "status": "success" if was_success else "failed",
                "task_id": task.task_id,
                "stdout": result.stdout[:1000],  # First 1000 chars
                "stderr": result.stderr[:1000] if result.stderr else "",
                "returncode": result.returncode,
                "error": (
                    self._summarize_chatdev_error(result.stderr, result.returncode)
                    if not was_success
                    else None
                ),
            }

        except TimeoutError:
            logger.warning(f"⏱️ ChatDev task timeout: {task.task_id}")
            return {"success": False, "status": "timeout", "task_id": task.task_id}
        except subprocess.TimeoutExpired as e:
            logger.warning(f"⏱️ ChatDev subprocess timeout: {task.task_id}")
            return {
                "success": False,
                "status": "timeout",
                "task_id": task.task_id,
                "error": f"ChatDev command timed out after {int(e.timeout)} seconds",
            }
        except Exception as e:
            logger.error(f"💥 ChatDev execution error: {e}")
            return {"success": False, "status": "error", "error": str(e)}

    async def route_autonomous_cycle_issues(
        self, issues: list[dict[str, Any]], issue_types: list[str], max_tasks: int = 5
    ) -> list[dict[str, Any]]:
        """Route top issues from autonomous cycle to ChatDev."""
        if not self.chatdev_available:
            logger.warning("⚠️ ChatDev unavailable - cannot route issues")
            return []

        logger.info(f"🔄 Routing {min(len(issues), max_tasks)} issues to ChatDev")

        # Create tasks from top issues
        tasks = []
        for issue, issue_type in zip(issues[:max_tasks], issue_types[:max_tasks], strict=False):
            task = self.decompose_issue_into_task(issue, issue_type)
            tasks.append(task)

        # Execute tasks concurrently
        results = await asyncio.gather(
            *[self.route_task_to_chatdev(task) for task in tasks],
            return_exceptions=True,
        )

        return [
            {
                "task_id": task.task_id,
                "status": task.status,
                "result": (result if isinstance(result, dict) else {"error": str(result)}),
            }
            for task, result in zip(tasks, results, strict=False)
        ]

    def get_task_status(self, task_id: str) -> dict[str, Any] | None:
        """Get status of a routed task."""
        if task_id not in self.tasks:
            return None

        task = self.tasks[task_id]
        return {
            "task_id": task.task_id,
            "status": task.status,
            "category": task.category.value,
            "agents": [a.value for a in task.assigned_agents],
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "results": task.results,
        }

    def get_all_tasks(self) -> dict[str, dict[str, Any]]:
        """Get status of all routed tasks."""
        statuses: dict[str, dict[str, Any]] = {}
        for task_id in self.tasks:
            status = self.get_task_status(task_id)
            if status is not None:
                statuses[task_id] = status
        return statuses

    # ========== AI Council Integration ==========

    def propose_task_to_council(
        self,
        task_description: str,
        task_category: str = "CODE_GENERATION",
        proposer: str = "chatdev_router",
    ) -> dict[str, Any]:
        """Propose a ChatDev task to the AI Council for approval before execution.

        This enables multi-agent consensus before committing to expensive
        ChatDev multi-agent development cycles.

        Args:
            task_description: Description of the task to propose
            task_category: Category (CODE_GENERATION, BUG_FIX, REFACTORING, etc.)
            proposer: Who is proposing this task

        Returns:
            Dict with decision_id and status
        """
        try:
            import uuid

            from src.orchestration.ai_council_voting import AICouncilVoting

            council = AICouncilVoting()
            decision_id = f"chatdev-{task_category.lower()}-{uuid.uuid4().hex[:8]}"

            decision = council.create_decision(
                decision_id=decision_id,
                topic=f"ChatDev Task: {task_category}",
                description=f"""
ChatDev Multi-Agent Development Task
====================================

Category: {task_category}
Description: {task_description}

This task will be routed to ChatDev's multi-agent team for execution:
- CEO: Project oversight and coordination
- CTO: Technical decision making
- Programmer: Implementation
- Tester: Validation and testing
- Product Manager: Quality assurance

Vote APPROVE to execute this task with ChatDev.
Vote REJECT if the task should not be run.
""",
                proposed_by=proposer,
            )

            logger.info(f"📋 ChatDev task proposed to AI Council: {decision_id}")

            return {
                "success": True,
                "decision_id": decision.decision_id,
                "topic": f"ChatDev Task: {task_category}",
                "status": decision.status,
                "message": "Task proposed to AI Council. Awaiting votes.",
            }

        except ImportError as e:
            logger.warning(f"AICouncilVoting not available: {e}")
            return {"success": False, "error": "AICouncilVoting not available"}
        except Exception as e:
            logger.exception(f"Failed to propose to council: {e}")
            return {"success": False, "error": str(e)}

    async def execute_approved_council_task(
        self,
        decision_id: str,
    ) -> dict[str, Any]:
        """Execute a ChatDev task that was approved by the AI Council.

        Args:
            decision_id: ID of the approved decision

        Returns:
            Dict with execution status and task results
        """
        try:
            from src.orchestration.ai_council_voting import AICouncilVoting

            council = AICouncilVoting()
            decision = council.get_decision(decision_id)

            if not decision:
                return {"success": False, "error": f"Decision {decision_id} not found"}

            if decision.status != "approved":
                return {
                    "success": False,
                    "error": f"Decision {decision_id} is not approved (status: {decision.status})",
                }

            # Extract task details from decision description
            task_description = decision.description
            task_category = decision.topic.replace("ChatDev Task: ", "")

            # Create and route the task
            issue = {
                "issue_id": f"council_{decision_id}",
                "message": task_description,
                "council_decision_id": decision_id,
            }

            category_map = {
                "CODE_GENERATION": TaskCategory.CODE_GENERATION,
                "BUG_FIX": TaskCategory.BUG_FIX,
                "REFACTORING": TaskCategory.REFACTORING,
                "TEST_GENERATION": TaskCategory.TEST_GENERATION,
                "CODE_REVIEW": TaskCategory.CODE_REVIEW,
                "DOCUMENTATION": TaskCategory.DOCUMENTATION,
            }

            task = self.decompose_issue_into_task(
                issue,
                category_map.get(task_category, TaskCategory.CODE_GENERATION).value,
            )

            # Route to ChatDev
            result = await self.route_task_to_chatdev(task)

            # Update council decision with results
            if result.get("status") == "success":
                council.complete_decision(
                    decision_id,
                    artifacts=[f"ChatDev task completed: {task.task_id}"],
                )
            else:
                # Mark decision as failed
                decision.status = "failed"
                decision.execution_plan = (
                    f"ChatDev execution failed: {result.get('error', 'Unknown error')}"
                )

            return {
                "success": result.get("status") == "success",
                "decision_id": decision_id,
                "task_id": task.task_id,
                "chatdev_result": result,
            }

        except ImportError as e:
            logger.warning(f"AICouncilVoting not available: {e}")
            return {"success": False, "error": "AICouncilVoting not available"}
        except Exception as e:
            logger.exception(f"Failed to execute council task: {e}")
            return {"success": False, "error": str(e)}

    def route_with_council_approval(
        self,
        task_description: str,
        task_category: str = "CODE_GENERATION",
        auto_approve: bool = False,
        auto_approve_agents: list[tuple[str, str, float, float]] | None = None,
    ) -> dict[str, Any]:
        """Route a task with optional AI Council approval flow.

        For synchronous callers. If auto_approve is True, automatically
        casts votes from the provided agents and executes if approved.

        Args:
            task_description: Description of the task
            task_category: Category of the task
            auto_approve: If True, auto-cast votes and execute
            auto_approve_agents: List of (agent_id, agent_name, confidence, expertise)
                               to auto-vote with. Defaults to claude + copilot.

        Returns:
            Dict with proposal status or execution result
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(
                self._route_with_council_impl(
                    task_description, task_category, auto_approve, auto_approve_agents
                )
            )

        _council = loop.create_task(
            self._route_with_council_impl(
                task_description, task_category, auto_approve, auto_approve_agents
            )
        )
        _council.add_done_callback(lambda t: None)  # keep ref; suppress dangling-task warning
        return {
            "success": True,
            "status": "scheduled",
            "message": "Task scheduling with council approval",
        }

    async def _route_with_council_impl(
        self,
        task_description: str,
        task_category: str,
        auto_approve: bool,
        auto_approve_agents: list[tuple[str, str, float, float]] | None,
    ) -> dict[str, Any]:
        """Implementation of route_with_council_approval."""
        # Propose to council
        proposal = self.propose_task_to_council(task_description, task_category, "chatdev_router")

        if not proposal.get("success"):
            return proposal

        decision_id = proposal["decision_id"]

        if auto_approve:
            from src.orchestration.ai_council_voting import (AICouncilVoting,
                                                             VoteChoice)

            council = AICouncilVoting()

            # Default agents if not provided
            if not auto_approve_agents:
                auto_approve_agents = [
                    ("claude", "Claude", 0.85, 0.8),
                    ("copilot", "GitHub Copilot", 0.8, 0.75),
                ]

            # Cast votes
            for agent_id, agent_name, confidence, expertise in auto_approve_agents:
                council.cast_vote(
                    decision_id=decision_id,
                    agent_id=agent_id,
                    agent_name=agent_name,
                    vote=VoteChoice.APPROVE,
                    confidence=confidence,
                    expertise_level=expertise,
                    reasoning=f"{agent_name} auto-approved ChatDev task",
                )

            # Check if approved and execute
            decision = council.get_decision(decision_id)
            if decision and decision.status == "approved":
                return await self.execute_approved_council_task(decision_id)
            else:
                return {
                    "success": False,
                    "decision_id": decision_id,
                    "status": decision.status if decision else "unknown",
                    "message": "Task not approved after voting",
                }

        return proposal

    # ========== NuSyQ Facade Integration ==========

    def dispatch_via_nusyq(
        self,
        prompt: str,
        task_type: str = "code_generation",
        priority: str = "normal",
    ) -> dict[str, Any]:
        """Dispatch a task using the unified NuSyQ facade.

        Uses the nusyq.background facade for consistent task dispatching
        across all NuSyQ components.

        Args:
            prompt: Task description/prompt
            task_type: Type of task (code_generation, code_analysis, etc.)
            priority: Task priority (low, normal, high, critical)

        Returns:
            Dict with task result or error info
        """
        if not _ensure_nusyq_facade_loaded() or nusyq is None:
            logger.warning(f"{NUSYQ_FACADE_UNAVAILABLE_ERROR}, falling back to direct routing")
            return self.route_task(prompt, priority=priority)

        try:
            result = nusyq.background.dispatch(
                prompt=prompt,
                task_type=task_type,
                priority=priority,
            )

            if result.ok:
                logger.info(f"Task dispatched via NuSyQ facade: {result.value}")
                return {
                    "success": True,
                    "task_id": result.value,
                    "method": "nusyq_facade",
                    "message": result.message,
                }
            else:
                logger.warning(f"NuSyQ dispatch failed: {result.error}")
                return {"success": False, "error": result.error}

        except Exception as e:
            logger.exception(f"NuSyQ facade dispatch failed: {e}")
            return {"success": False, "error": str(e)}

    def search_codebase(self, query: str, limit: int = 10) -> dict[str, Any]:
        """Search codebase using the NuSyQ SmartSearch facade.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            Dict with search results or error info
        """
        if not _ensure_nusyq_facade_loaded() or nusyq is None:
            return {"success": False, "error": NUSYQ_FACADE_UNAVAILABLE_ERROR}

        try:
            result = nusyq.search.find(query, limit=limit)
            if result.ok:
                return {
                    "success": True,
                    "results": result.value,
                    "count": len(result.value) if result.value else 0,
                }
            else:
                return {"success": False, "error": result.error}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_quest_from_task(
        self,
        task: "ChatDevTask",
        questline: str = "ChatDev Tasks",
    ) -> dict[str, Any]:
        """Create a quest entry for a ChatDev task using the NuSyQ facade.

        Args:
            task: The ChatDevTask to create a quest for
            questline: Questline to assign the quest to

        Returns:
            Dict with quest creation result
        """
        if not _ensure_nusyq_facade_loaded() or nusyq is None:
            return {"success": False, "error": NUSYQ_FACADE_UNAVAILABLE_ERROR}

        try:
            result = nusyq.quest.add(
                title=f"[ChatDev] {task.title}",
                description=task.description,
                questline=questline,
                priority="high" if task.category == TaskCategory.BUG_FIX else "normal",
            )
            if result.ok:
                logger.info(f"Quest created for task {task.task_id}: {result.value}")
                return {"success": True, "quest_id": result.value}
            else:
                return {"success": False, "error": result.error}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_nusyq_status(self) -> dict[str, Any]:
        """Get overall NuSyQ system status via the facade.

        Returns:
            Dict with system status from all NuSyQ subsystems
        """
        if not _ensure_nusyq_facade_loaded() or nusyq is None:
            return {"available": False, "error": NUSYQ_FACADE_UNAVAILABLE_ERROR}

        try:
            result = nusyq.status()
            if result.ok:
                return {"available": True, **result.value}
            else:
                return {"available": False, "error": result.error}
        except Exception as e:
            return {"available": False, "error": str(e)}


def test_chatdev_router():
    """Test ChatDev router with sample issues."""
    logger.info("🧪 Testing ChatDev Autonomous Router")

    router = ChatDevAutonomousRouter()

    # Sample issue for testing
    sample_issue = {
        "issue_id": "test_001",
        "message": "Missing type hints in function parameters",
        "file_path": "src/test/sample.py",
        "line_number": 42,
        "suggested_fix": "Add type hints using Python typing module",
    }

    # Decompose and route
    task = router.decompose_issue_into_task(sample_issue, "missing_type_hint")
    logger.info(f"✅ Created task: {task.task_id}")
    logger.info(f"   Status: {task.status}")
    logger.info(f"   Category: {task.category.value}")

    # Show task status
    status = router.get_task_status(task.task_id)
    logger.info(f"📊 Task status: {json.dumps(status, indent=2)}")


if __name__ == "__main__":
    test_chatdev_router()
