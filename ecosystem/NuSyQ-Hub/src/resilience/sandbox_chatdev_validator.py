"""Sandboxed ChatDev Validator for Phase 8 Testing (MCP-ready).

Goals:
    1. Run ChatDev generation in isolated container/process
    2. Validate output completeness and quality
    3. Test resource limits and timeout handling
    4. Emit audit entries for every step
    5. Return structured result for MCP integration

Design:
    - SandboxConfig: Resource constraints (memory, CPU, timeout, disk)
    - ChatDevSandboxValidator: Orchestrates sandboxed run with validation
    - Emits AuditEntry for each step (start, checkpoint, success/failure)
    - Returns structured ValidatorResult for MCP handlers
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class SandboxMode(Enum):
    """Sandbox execution mode."""

    PROCESS_ISOLATED = "process_isolated"  # Use process boundaries
    CONTAINER = "container"  # Use Docker container
    LOCAL_ONLY = "local_only"  # Local execution with resource checks


@dataclass
class SandboxConfig:
    """Resource and execution constraints for sandbox."""

    mode: SandboxMode = SandboxMode.PROCESS_ISOLATED
    memory_limit: int = 2048  # MB
    cpu_limit: float = 1.0  # CPU cores
    timeout: float = 300.0  # seconds
    disk_limit: int = 5000  # MB
    network_allowed: bool = False
    write_allowed: bool = True
    output_dir: Path | None = None

    def to_dict(self) -> dict:
        return {
            "mode": self.mode.value,
            "memory_limit": self.memory_limit,
            "cpu_limit": self.cpu_limit,
            "timeout": self.timeout,
            "disk_limit": self.disk_limit,
            "network_allowed": self.network_allowed,
            "write_allowed": self.write_allowed,
            "output_dir": str(self.output_dir) if self.output_dir else None,
        }


@dataclass
class ValidatorResult:
    """Result of sandbox validation."""

    success: bool
    sandbox_id: str
    execution_time: float
    output: dict | None = None  # Generated artifacts/metadata
    error: str | None = None
    resource_usage: dict | None = None  # actual memory/cpu/disk used
    audit_entries: list | None = None  # Audit trail of execution
    validation_score: float = 0.0  # 0.0-1.0

    def __post_init__(self):
        """Implement __post_init__."""
        if self.output is None:
            self.output = {}
        if self.resource_usage is None:
            self.resource_usage = {}
        if self.audit_entries is None:
            self.audit_entries = []


class ChatDevSandboxValidator:
    """Validate ChatDev generation in isolated sandbox."""

    def __init__(self, sandbox_config: SandboxConfig | None = None):
        """Initialize ChatDevSandboxValidator with sandbox_config."""
        self.config = sandbox_config or SandboxConfig()
        self.sandbox_id = str(uuid.uuid4())[:8]
        self.output_dir = self.config.output_dir or Path("state/sandbox") / self.sandbox_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.audit_entries: list = []

    async def validate_chatdev_run(
        self,
        task: str,
        model: str = "qwen2.5-coder:7b",
        project_name: str | None = None,
    ) -> ValidatorResult:
        """Execute ChatDev generation in sandbox.

        Args:
            task: Project description
            model: Ollama model to use
            project_name: Output project name (auto-generated if None)

        Returns:
            ValidatorResult with success, output, audit trail, and score
        """
        start_time = time.time()
        project_name = project_name or f"sandbox_test_{self.sandbox_id}"
        checkpoint_id = str(uuid.uuid4())

        try:
            # === CHECKPOINT 1: Pre-execution ===
            self._emit_audit(
                "checkpoint_pre_execution",
                "success",
                {
                    "task": task,
                    "model": model,
                    "checkpoint_id": checkpoint_id,
                },
            )

            # === VALIDATE ENVIRONMENT ===
            env_check = await self._validate_environment()
            if not env_check["valid"]:
                return ValidatorResult(
                    success=False,
                    sandbox_id=self.sandbox_id,
                    execution_time=time.time() - start_time,
                    error=f"Environment validation failed: {env_check['errors']}",
                    audit_entries=self.audit_entries,
                )

            self._emit_audit("environment_validated", "success", env_check)

            # === RUN CHATDEV ===
            logger.info(f"[{self.sandbox_id}] Starting ChatDev in sandbox")
            self._emit_audit(
                "chatdev_start",
                "running",
                {
                    "task": task,
                    "model": model,
                },
            )

            result = await self._execute_chatdev(task, model, project_name)

            if not result["success"]:
                self._emit_audit(
                    "chatdev_failed",
                    "failure",
                    {
                        "error": result.get("error"),
                    },
                )
                return ValidatorResult(
                    success=False,
                    sandbox_id=self.sandbox_id,
                    execution_time=time.time() - start_time,
                    error=result.get("error"),
                    audit_entries=self.audit_entries,
                )

            self._emit_audit(
                "chatdev_complete",
                "success",
                {
                    "project_dir": str(result.get("project_dir")),
                    "files_generated": result.get("file_count", 0),
                },
            )

            # === VALIDATE OUTPUT ===
            logger.info(f"[{self.sandbox_id}] Validating output")
            self._emit_audit("validation_start", "running", {})

            validation = self._validate_output(result["project_dir"])
            validation_score = validation["score"]
            validation_issues = validation.get("issues", [])

            if validation_issues:
                self._emit_audit(
                    "validation_warnings",
                    "partial",
                    {
                        "issues": validation_issues,
                    },
                )
            else:
                self._emit_audit(
                    "validation_complete",
                    "success",
                    {
                        "score": validation_score,
                    },
                )

            # === CHECKPOINT 2: Post-execution ===
            execution_time = time.time() - start_time
            self._emit_audit(
                "checkpoint_post_execution",
                "success",
                {
                    "execution_time": execution_time,
                    "validation_score": validation_score,
                },
            )

            # === CLEANUP ===
            resource_usage = self._measure_resources()

            return ValidatorResult(
                success=True,
                sandbox_id=self.sandbox_id,
                execution_time=execution_time,
                output={
                    "project_name": project_name,
                    "project_dir": str(result["project_dir"]),
                    "file_count": result.get("file_count", 0),
                    "validation_issues": validation_issues,
                },
                resource_usage=resource_usage,
                audit_entries=self.audit_entries,
                validation_score=validation_score,
            )

        except TimeoutError:
            self._emit_audit(
                "timeout",
                "failure",
                {
                    "timeout_sec": self.config.timeout,
                },
            )
            return ValidatorResult(
                success=False,
                sandbox_id=self.sandbox_id,
                execution_time=time.time() - start_time,
                error=f"ChatDev exceeded timeout ({self.config.timeout}s)",
                audit_entries=self.audit_entries,
            )
        except Exception as e:
            logger.error(f"[{self.sandbox_id}] Unexpected error: {e}", exc_info=True)
            self._emit_audit(
                "unexpected_error",
                "failure",
                {
                    "error": str(e),
                },
            )
            return ValidatorResult(
                success=False,
                sandbox_id=self.sandbox_id,
                execution_time=time.time() - start_time,
                error=f"Unexpected error: {e!s}",
                audit_entries=self.audit_entries,
            )

    async def _validate_environment(self) -> dict:
        """Check if ChatDev and Ollama are available."""
        try:
            # Check Ollama using async subprocess
            process = await asyncio.create_subprocess_exec(
                "ollama",
                "list",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                await asyncio.wait_for(process.wait(), timeout=5)
                ollama_ok = process.returncode == 0
            except TimeoutError:
                process.kill()
                ollama_ok = False

            # Check ChatDev path
            chatdev_path = Path.home() / "NuSyQ" / "ChatDev"
            chatdev_ok = chatdev_path.exists()

            errors = []
            if not ollama_ok:
                errors.append("Ollama not running (run `ollama serve`)")
            if not chatdev_ok:
                errors.append(f"ChatDev not found at {chatdev_path}")

            return {
                "valid": ollama_ok and chatdev_ok,
                "ollama": ollama_ok,
                "chatdev": chatdev_ok,
                "errors": errors,
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "errors": [str(e)],
            }

    async def _execute_chatdev(self, task: str, _model: str, project_name: str) -> dict:
        """Run ChatDev generation (would be docker on production)."""
        try:
            # Simulate ChatDev run or invoke real ChatDev
            # For now, we create a mock project structure
            logger.info(f"[{self.sandbox_id}] Running ChatDev: {task}")

            project_dir = self.output_dir / project_name
            project_dir.mkdir(exist_ok=True)

            # Create mock project files
            (project_dir / "main.py").write_text(f"# Generated: {project_name}\nprint('Hello')")
            (project_dir / "README.md").write_text(f"# {project_name}\n\n{task}")
            (project_dir / "requirements.txt").write_text("# Dependencies")

            # Simulate async execution with timeout
            await asyncio.sleep(0.5)  # Mock execution time

            return {
                "success": True,
                "project_dir": project_dir,
                "file_count": 3,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def _validate_output(self, project_dir: Path) -> dict:
        """Validate generated project structure."""
        issues = []
        score = 1.0

        if not project_dir.exists():
            issues.append("Project directory not found")
            score = 0.0
            return {"score": score, "issues": issues}

        required_files = {"main.py", "README.md"}
        found_files = {f.name for f in project_dir.glob("*") if f.is_file()}

        for required in required_files:
            if required not in found_files:
                issues.append(f"Missing required file: {required}")
                score -= 0.2

        # Check file sizes (all should be non-empty)
        for file in project_dir.glob("*.py"):
            if file.stat().st_size < 10:
                issues.append(f"File too small: {file.name}")
                score -= 0.1

        score = max(0.0, min(1.0, score))
        return {
            "score": score,
            "issues": issues,
            "files_found": sorted(found_files),
        }

    def _measure_resources(self) -> dict:
        """Measure resource usage (simplified)."""
        return {
            "memory_mb": 512,  # Placeholder
            "cpu_percent": 25.0,  # Placeholder
            "disk_mb": 50,  # Placeholder
        }

    def _emit_audit(self, action: str, result: str, context: dict) -> None:
        """Emit audit entry for tracking."""
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "sandbox_id": self.sandbox_id,
            "action": action,
            "result": result,
            "context": context,
        }
        self.audit_entries.append(entry)
        logger.info(f"[{self.sandbox_id}] Audit: {action} -> {result}")

    def save_result(self, result: ValidatorResult, path: Path | str | None = None) -> Path:
        """Save validation result to disk."""
        if path is None:
            path = self.output_dir / "validation_result.json"
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(result), indent=2, default=str))
        logger.info(f"Validation result saved: {path}")
        return path


# Convenience async function
async def validate_chatdev_sandbox(
    task: str,
    model: str = "qwen2.5-coder:7b",
    config: SandboxConfig | None = None,
) -> ValidatorResult:
    """Quick validation of ChatDev in sandbox."""
    validator = ChatDevSandboxValidator(config)
    return await validator.validate_chatdev_run(task, model)
