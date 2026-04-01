#!/usr/bin/env python3
"""🛡️ Safe Subprocess Execution with Zen Engine Validation.

Wraps subprocess calls with automated command validation using Zen Engine.
Provides security layer for all system command execution.

OmniTag: {
    "purpose": "Safe subprocess execution with command validation",
    "dependencies": ["zen_engine_wrapper", "subprocess"],
    "context": "Security layer for command execution",
    "evolution_stage": "v1.0-production"
}
MegaTag: SAFE_SUBPROCESS⨳ZEN_VALIDATION⦾SECURITY→∞
"""

import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SafeSubprocessExecutor:
    """Execute subprocess commands with Zen Engine validation.

    Provides automated safety checking and optional auto-fix for all
    subprocess command execution.
    """

    def __init__(self, auto_fix: bool = True, strict_mode: bool = False) -> None:
        """Initialize safe subprocess executor.

        Args:
            auto_fix: Automatically apply Zen Engine fixes
            strict_mode: Block execution if validation fails
        """
        self.auto_fix = auto_fix
        self.strict_mode = strict_mode
        self.validation_enabled = True
        self.zen: Any = None
        self.zen_available = False

        # Try to import Zen wrapper
        try:
            from src.integration.zen_engine_wrapper import zen_wrapper

            self.zen = zen_wrapper
            self.zen_available = zen_wrapper.available
        except (ImportError, AttributeError) as e:
            logger.warning(f"Zen Engine not available: {e}")
            self.zen = None
            self.zen_available = False
            self.validation_enabled = False

    def run(
        self,
        command: list[str] | str,
        *,
        shell: bool = False,
        check: bool = False,
        timeout: int | None = None,
        capture_output: bool = False,
        text: bool = False,
        cwd: str | Path | None = None,
        env: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> subprocess.CompletedProcess:
        """Safely execute command with Zen validation.

        Args:
            command: Command to execute (list or string)
            shell: Execute through shell
            check: Raise on non-zero exit
            timeout: Timeout in seconds
            capture_output: Capture stdout/stderr
            text: Text mode for output
            cwd: Working directory
            env: Environment variables
            **kwargs: Additional subprocess.run() arguments

        Returns:
            CompletedProcess result

        Raises:
            subprocess.CalledProcessError: If check=True and command fails
            subprocess.TimeoutExpired: If timeout exceeded
            SecurityError: If strict_mode=True and validation blocks command
        """
        # Convert command to string for validation
        cmd_str = command if isinstance(command, str) else " ".join(command)

        # Validate with Zen if available
        if self.validation_enabled and self.zen_available:
            try:
                validation = self.zen.validate_command(
                    cmd_str,
                    shell=shell,
                    auto_fix=self.auto_fix,
                )

                # Log validation results
                if validation.warnings:
                    logger.warning(f"⚠️  Command warnings: {validation.warnings}")

                if validation.blocked:
                    error_msg = f"🚫 Command blocked by Zen validation: {cmd_str}"
                    logger.error(error_msg)
                    if self.strict_mode:
                        raise SecurityError(error_msg)
                    # In non-strict mode, proceed with warning
                    logger.warning("⚠️  Proceeding anyway (strict_mode=False)")

                # Use modified command if auto-fix applied
                if self.auto_fix and validation.modified_command:
                    original_cmd = cmd_str
                    cmd_str = validation.modified_command
                    logger.info(f"🔧 Auto-fix applied: {original_cmd} → {cmd_str}")

                    # Reconstruct command in original format
                    command = cmd_str.split() if isinstance(command, list) else cmd_str

            except (ValueError, TypeError, AttributeError) as e:
                logger.warning(f"Zen validation failed, proceeding anyway: {e}")

        # Execute command
        try:
            result = subprocess.run(
                command,
                shell=shell,
                check=check,
                timeout=timeout,
                capture_output=capture_output,
                text=text,
                cwd=cwd,
                env=env,
                **kwargs,
            )

            logger.debug(f"✅ Command executed successfully: {cmd_str[:50]}...")
            return result

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Command failed (exit {e.returncode}): {cmd_str}")
            raise

        except subprocess.TimeoutExpired:
            logger.error(f"⏱️  Command timeout ({timeout}s): {cmd_str}")
            raise

    def Popen(
        self,
        command: list[str] | str,
        *,
        shell: bool = False,
        cwd: str | Path | None = None,
        env: dict[str, str] | None = None,
        stdout=None,
        stderr=None,
        stdin=None,
        **kwargs: Any,
    ) -> subprocess.Popen:
        """Safely create subprocess with Zen validation.

        Args:
            command: Command to execute
            shell: Execute through shell
            cwd: Working directory
            env: Environment variables
            stdout: Stdout redirection
            stderr: Stderr redirection
            stdin: Stdin redirection
            **kwargs: Additional Popen arguments

        Returns:
            Popen process object
        """
        # Convert and validate command
        cmd_str = command if isinstance(command, str) else " ".join(command)

        if self.validation_enabled and self.zen_available:
            try:
                validation = self.zen.validate_command(
                    cmd_str,
                    shell=shell,
                    auto_fix=self.auto_fix,
                )

                if validation.blocked and self.strict_mode:
                    raise SecurityError(f"Command blocked by Zen: {cmd_str}")

                if self.auto_fix and validation.modified_command:
                    cmd_str = validation.modified_command
                    command = cmd_str.split() if isinstance(command, list) else cmd_str

            except (ValueError, TypeError, AttributeError) as e:
                logger.warning(f"Zen validation failed for Popen: {e}")

        # Create process
        return subprocess.Popen(
            command,
            shell=shell,
            cwd=cwd,
            env=env,
            stdout=stdout,
            stderr=stderr,
            stdin=stdin,
            **kwargs,
        )

    def check_output(
        self,
        command: list[str] | str,
        *,
        shell: bool = False,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> bytes:
        """Safely execute command and return output with Zen validation.

        Args:
            command: Command to execute
            shell: Execute through shell
            timeout: Timeout in seconds
            **kwargs: Additional check_output arguments

        Returns:
            Command output as bytes
        """
        # Enforce binary output; callers cannot request text=True here
        if "text" in kwargs:
            kwargs.pop("text")

        result = self.run(
            command,
            shell=shell,
            timeout=timeout,
            capture_output=True,
            check=True,
            text=False,
            **kwargs,
        )
        # stdout is bytes when text=False; cast for type checkers
        from typing import cast

        return cast(bytes, result.stdout)


class SecurityError(Exception):
    """Raised when command is blocked by security validation."""


# Global singleton instance
safe_subprocess = SafeSubprocessExecutor(auto_fix=True, strict_mode=False)


# Convenience functions mimicking subprocess API
def run(*args, **kwargs) -> subprocess.CompletedProcess:
    """Safe subprocess.run() with Zen validation."""
    return safe_subprocess.run(*args, **kwargs)


def Popen(*args, **kwargs) -> subprocess.Popen:
    """Safe subprocess.Popen() with Zen validation."""
    return safe_subprocess.Popen(*args, **kwargs)


def check_output(*args, **kwargs) -> bytes:
    """Safe subprocess.check_output() with Zen validation."""
    # Ensure binary output
    if "text" in kwargs:
        kwargs.pop("text")
    return safe_subprocess.check_output(*args, **kwargs)


def demo_safe_subprocess() -> None:
    """Demo safe subprocess execution."""
    logger.info("🛡️ Safe Subprocess Execution Demo")
    logger.info("=" * 60)

    executor = SafeSubprocessExecutor(auto_fix=True, strict_mode=False)

    # Test safe command
    logger.info("\n✅ Testing safe command...")
    result = executor.run(["echo", "Hello, safe world!"], capture_output=True, text=True)
    logger.info(f"   Output: {result.stdout.strip()}")

    # Test command with validation
    logger.info("\n🔍 Testing command validation...")
    result = executor.run("ls -la", shell=True, capture_output=True, text=True)
    logger.info("   Validated and executed successfully")

    # Test potentially dangerous command (should warn)
    logger.warning("\n⚠️  Testing dangerous command (should warn)...")
    try:
        # This would be blocked in strict mode
        result = executor.run(
            "echo 'test' > /tmp/test.txt", shell=True, capture_output=True, text=True
        )
        logger.warning("   Executed with warnings (strict_mode=False)")
    except SecurityError as e:
        logger.info(f"   🚫 Blocked: {e}")

    logger.info("\n" + "=" * 60)
    logger.info("✅ Safe subprocess demo complete")


if __name__ == "__main__":
    demo_safe_subprocess()
