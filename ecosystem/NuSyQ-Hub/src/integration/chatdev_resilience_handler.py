"""Wire Phase 8 Resilience into ChatDev/MCP Handlers (Integration Layer).

Goals:
    1. Wrap ChatDev MCP handlers with checkpoint/retry/degraded-mode
    2. Emit audit entries for every handler step
    3. Create attestations linking artifacts to audit trail
    4. Enable sandbox validation when Docker is available
    5. Return enriched responses with attestation hashes and policy status

Design:
    - ResilientChatDevHandler: Wraps MCP tool handlers
    - Emit checkpoint before + after
    - Catch failures, retry with backoff, fallback to degraded
    - Emit audit entries throughout lifecycle
    - Attach attestation hashes to MCP response
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from collections.abc import Callable
from typing import Any

from src.resilience.checkpoint_retry_degraded import (DegradedModeConfig,
                                                      ExecutionContext,
                                                      RetryPolicy)
from src.resilience.mission_control_attestation import (AttestationManager,
                                                        AuditEntry, AuditLog,
                                                        PolicyStatus)
from src.resilience.sandbox_chatdev_validator import (SandboxConfig,
                                                      SandboxMode,
                                                      validate_chatdev_sandbox)

logger = logging.getLogger(__name__)

# Module-level constants
DEFAULT_MODEL_NAME = "qwen2.5-coder:7b"


class ResilientChatDevHandler:
    """Wraps ChatDev MCP handlers with resilience pattern (checkpoint/retry/degraded).

    Usage:
        handler = ResilientChatDevHandler()
        result = await handler.execute_generate_project(
            task="Build a CLI app",
            model=DEFAULT_MODEL_NAME,
            agent="copilot",
        )
        # result includes: success, output, execution_mode, attestation_hash, audit_entries
    """

    def __init__(
        self,
        retry_policy: RetryPolicy | None = None,
        degraded_config: DegradedModeConfig | None = None,
        sandbox_config: SandboxConfig | None = None,
        primary_runner: Callable[..., Any] | None = None,
        degraded_runner: Callable[..., Any] | None = None,
        audit_log: AuditLog | None = None,
        attestation_mgr: AttestationManager | None = None,
    ):
        """Initialize ResilientChatDevHandler with retry_policy, degraded_config, sandbox_config, ...."""
        self.retry_policy = retry_policy or RetryPolicy()
        self.degraded_config = degraded_config or DegradedModeConfig()
        self.sandbox_config = sandbox_config or SandboxConfig(mode=SandboxMode.LOCAL_ONLY)
        self.primary_runner = primary_runner
        self.degraded_runner = degraded_runner
        self.audit_log = audit_log or AuditLog()
        self.attestation_mgr = attestation_mgr or AttestationManager()

    async def execute_generate_project(
        self,
        task: str,
        model: str = DEFAULT_MODEL_NAME,
        agent: str = "unknown",
        use_sandbox: bool = False,
        project_name: str | None = None,
        operation: str = "chatdev_generate_project",
    ) -> dict:
        """Execute ChatDev project generation with resilience.

        Args:
            task: Project description
            model: Ollama model
            agent: Calling agent (copilot, ollama, etc)
            use_sandbox: If True, run in sandbox (requires Docker)
            project_name: Optional name for the generated project.
            operation: Operation label for audit logging.

        Returns:
            {
                "success": bool,
                "output": <generated project>,
                "execution_mode": "primary|degraded|offline",
                "attestation_hash": <hash>,
                "audit_entries": [<entries>],
                "error": <error if failed>
            }
        """
        operation_name = operation or "chatdev_generate_project"
        context = ExecutionContext(
            operation=operation_name,
            retry_policy=self.retry_policy,
            degraded_config=self.degraded_config,
        )

        # === AUDIT: Start ===
        self._emit_audit(
            action="generate_project_start",
            result="running",
            agent=agent,
            context={"task": task[:100], "model": model, "use_sandbox": use_sandbox},
        )

        try:
            # === PRIMARY: ChatDev generation ===
            primary_callable = self.primary_runner or self._primary_generate_project
            # Select degraded runner - prefer explicit runner, fallback to method if enabled
            if self.degraded_runner is not None:
                degraded_callable = self.degraded_runner
            elif self.degraded_config.enabled:
                degraded_callable = self._degraded_generate_project
            else:
                degraded_callable = None

            primary_result = await context.execute(
                primary_fn=primary_callable,
                primary_args={
                    "task": task,
                    "model": model,
                    "name": project_name,
                },
                degraded_fn=degraded_callable,
                degraded_args={"task": task, "model": model, "name": project_name},
                context={"task": task, "model": model, "project_name": project_name},
            )

            if not primary_result.success:
                self._emit_audit(
                    action="generate_project_failed",
                    result="failure",
                    agent=agent,
                    context={"error": primary_result.error, "attempts": primary_result.attempt},
                )
                return {
                    "success": False,
                    "error": primary_result.error,
                    "execution_mode": primary_result.mode.value,
                    "audit_entries": self._get_recent_audits(5),
                }

            # === OPTIONAL: Sandbox validation ===
            if use_sandbox and primary_result.output:
                logger.info(f"[{agent}] Running sandbox validation...")
                self._emit_audit(
                    action="sandbox_validation_start",
                    result="running",
                    agent=agent,
                )
                sandbox_result = await validate_chatdev_sandbox(
                    task=task,
                    model=model,
                    config=self.sandbox_config,
                )
                if sandbox_result.success:
                    self._emit_audit(
                        action="sandbox_validation_success",
                        result="success",
                        agent=agent,
                        context={
                            "sandbox_id": sandbox_result.sandbox_id,
                            "validation_score": sandbox_result.validation_score,
                        },
                    )
                else:
                    self._emit_audit(
                        action="sandbox_validation_failed",
                        result="failure",
                        agent=agent,
                        context={"error": sandbox_result.error},
                    )

            # === ATTESTATION: Create artifact attestation ===
            output_str = json.dumps(primary_result.output, default=str)
            recent_audits = self._get_recent_audits(10)
            attestation = self.attestation_mgr.attest_artifact(
                artifact_id=f"{operation_name}_{context.execution_id}",
                artifact_content=output_str,
                audit_entries=self._audits_to_entries(recent_audits),
                policy_status=PolicyStatus(
                    sandboxing_enabled=use_sandbox,
                    isolation_level="container" if use_sandbox else "none",
                    attestation_required=True,
                ),
                run_id=context.execution_id,
            )

            # === AUDIT: Complete ===
            self._emit_audit(
                action="generate_project_success",
                result="success",
                agent=agent,
                context={
                    "execution_mode": primary_result.mode.value,
                    "execution_time": primary_result.execution_time,
                    "attestation_hash": attestation.attestation_hash,
                },
            )

            try:
                from src.system.agent_awareness import emit as _emit

                _emit(
                    "tasks",
                    f"ChatDev resilient: mode={primary_result.mode.value}"
                    f" fallback={primary_result.fallback_applied} agent={agent}",
                    level="INFO",
                    source="chatdev_resilience_handler",
                )
            except Exception:
                pass

            return {
                "success": True,
                "output": primary_result.output,
                "execution_mode": primary_result.mode.value,
                "execution_time": primary_result.execution_time,
                "fallback_applied": primary_result.fallback_applied,
                "attestation_hash": attestation.attestation_hash,
                "policy_hash": attestation.policy_status.get("policy_hash"),
                "audit_entries": recent_audits,
            }

        except Exception as e:
            logger.error(f"[{operation_name}] Unexpected error: {e}", exc_info=True)
            self._emit_audit(
                action="generate_project_error",
                result="failure",
                agent=agent,
                context={"error": str(e)},
            )
            return {
                "success": False,
                "error": f"Unexpected error: {e!s}",
                "execution_mode": "offline",
                "audit_entries": self._get_recent_audits(5),
            }

    async def _primary_generate_project(
        self, task: str, _model: str, name: str | None = None
    ) -> dict:
        """Primary ChatDev generation (would call actual ChatDev API)."""
        logger.info(f"Executing primary ChatDev generation: {task[:50]}...")
        # This would call the actual ChatDev MCP tool
        # For now, return mock result
        await asyncio.sleep(0.1)  # Simulate async work
        return {
            "project_name": name or "generated_project",
            "files": ["main.py", "README.md"],
            "status": "complete",
        }

    async def _degraded_generate_project(
        self, task: str, _model: str = DEFAULT_MODEL_NAME, name: str | None = None
    ) -> dict:
        """Degraded mode: Smaller, faster generation (local model)."""
        logger.info(f"Executing degraded ChatDev generation: {task[:50]}...")
        await asyncio.sleep(0.05)  # Faster (smaller model)
        return {
            "project_name": name or "degraded_project",
            "files": ["main.py"],
            "status": "degraded",
            "note": "Generated with smaller local model (reduced scope)",
        }

    def _emit_audit(
        self,
        action: str,
        result: str,
        agent: str = "unknown",
        context: dict | None = None,
    ) -> None:
        """Emit audit entry."""
        entry = AuditEntry(
            audit_id=self._gen_id(),
            timestamp=self._timestamp(),
            action=action,
            agent=agent,
            result=result,
            context=context or {},
        )
        self.audit_log.append(entry)

    def _get_recent_audits(self, count: int = 10) -> list[dict]:
        """Get last N audit entries."""
        all_entries = self.audit_log.read_all()
        return [e.to_dict() for e in all_entries[-count:]]

    def _audits_to_entries(self, audit_dicts: list[dict]) -> list[AuditEntry]:
        """Convert audit dicts back to AuditEntry objects."""
        entries = []
        for d in audit_dicts:
            with contextlib.suppress(Exception):
                entries.append(AuditEntry(**d))
        return entries

    @staticmethod
    def _gen_id() -> str:
        """Generate unique ID."""
        import uuid

        return str(uuid.uuid4())[:8]

    @staticmethod
    def _timestamp() -> str:
        """Get ISO 8601 timestamp."""
        import time

        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# Convenience factory
async def execute_chatdev_resilient(
    task: str,
    model: str = DEFAULT_MODEL_NAME,
    agent: str = "copilot",
    use_sandbox: bool = False,
) -> dict:
    """Quick wrapper for resilient ChatDev execution."""
    handler = ResilientChatDevHandler()
    return await handler.execute_generate_project(
        task=task,
        model=model,
        agent=agent,
        use_sandbox=use_sandbox,
    )


def load_resilience_config() -> dict:
    """Load ChatDev resilience config from config/chatdev_resilience_config.json."""
    from pathlib import Path

    config_path = Path(__file__).parent.parent.parent / "config" / "chatdev_resilience_config.json"
    if not config_path.exists():
        logger.warning(f"Resilience config not found at {config_path}, using defaults")
        return {}
    try:
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError, OSError) as e:
        logger.error(f"Failed to load resilience config: {e}")
        return {}


def create_ollama_runner(model: str = DEFAULT_MODEL_NAME, config: dict | None = None):
    """Create an Ollama-based ChatDev runner for fallback.

    This runs ChatDev via run_ollama.py, bypassing OpenAI entirely.
    Used as degraded_runner when OpenAI quota/rate limits hit.
    """
    import sys
    from pathlib import Path

    cfg = config or load_resilience_config()
    ollama_cfg = cfg.get("ollama_config", {})
    run_ollama_path = ollama_cfg.get(
        "run_ollama_path",
        "C:/Users/keath/NuSyQ/ChatDev/run_ollama.py",
    )

    async def run_chatdev_ollama(
        task: str, model: str = model, name: str | None = None, **kwargs
    ) -> dict:
        """Execute ChatDev with Ollama backend using async subprocess."""
        chatdev_root = Path(run_ollama_path).parent
        project_name = (
            name or f"OllamaFallback_{ResilientChatDevHandler._timestamp().replace(':', '-')}"
        )

        cmd = [
            sys.executable,
            str(run_ollama_path),
            "--task",
            task,
            "--name",
            project_name,
            "--model",
            model,
        ]

        logger.info(f"[OLLAMA FALLBACK] Running ChatDev: {' '.join(cmd[:6])}...")

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(chatdev_root),
            )

            timeout_sec = ollama_cfg.get("timeout_seconds", 600)
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout_sec
            )
            stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
            stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""

            if proc.returncode == 0:
                # Find generated project in WareHouse
                warehouse = chatdev_root / "WareHouse"
                projects = sorted(
                    warehouse.glob(f"{project_name}*"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )

                if projects:
                    project_path = projects[0]
                    files = {
                        f.name: f.read_text(errors="replace") for f in project_path.glob("*.py")
                    }
                    return {
                        "success": True,
                        "project_path": str(project_path),
                        "files": files,
                        "stdout": stdout[-2000:],
                        "model_used": model,
                        "fallback": True,
                    }

            return {
                "success": False,
                "error": stderr or "ChatDev Ollama run failed",
                "stdout": stdout[-1000:],
                "returncode": proc.returncode,
            }

        except TimeoutError:
            return {
                "success": False,
                "error": f"Ollama fallback timed out after {ollama_cfg.get('timeout_seconds', 600)}s",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    return run_chatdev_ollama


def create_resilient_handler_with_ollama_fallback() -> ResilientChatDevHandler:
    """Factory: Create handler with Ollama as automatic fallback.

    When OpenAI fails (429, timeout, quota), automatically switches to local Ollama.
    """
    config = load_resilience_config()
    retry_cfg = config.get("retry_policy", {})
    degraded_cfg = config.get("degraded_mode", {})

    # Map config fields to RetryPolicy fields
    backoff_factor = 2.0 if retry_cfg.get("exponential_backoff", True) else 1.0
    retry_policy = RetryPolicy(
        max_attempts=retry_cfg.get("max_attempts", 3),
        initial_delay=retry_cfg.get("initial_delay_seconds", 1.0),
        max_delay=retry_cfg.get("max_delay_seconds", 30.0),
        backoff_factor=backoff_factor,
        jitter=retry_cfg.get("jitter", True),
    )

    degraded_config = DegradedModeConfig(
        enabled=degraded_cfg.get("enabled", True),
        reduce_scope=degraded_cfg.get("scope_reduction", 0.5) < 1.0,  # Convert ratio to bool
    )

    # Use Ollama as the degraded runner
    ollama_runner = create_ollama_runner(config=config)

    return ResilientChatDevHandler(
        retry_policy=retry_policy,
        degraded_config=degraded_config,
        degraded_runner=ollama_runner,
    )
