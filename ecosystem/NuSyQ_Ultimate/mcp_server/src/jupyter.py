"""
Jupyter Service - Code execution in isolated environment
"""

import logging
import subprocess
from typing import Any, Dict

try:
    from .models import JupyterRequest
except ImportError:
    from models import JupyterRequest

logger = logging.getLogger(__name__)


class JupyterService:
    """Service for executing Python code in Jupyter-style environment"""

    def __init__(self, config_manager=None):
        self.config_manager = config_manager

    def execute_code(self, request: JupyterRequest) -> Dict[str, Any]:
        """
        Execute Python code in subprocess (Jupyter-style)

        WARNING: This is a simplified implementation that executes Python
        code directly via subprocess. Production systems should use proper
        Jupyter kernel communication (jupyter_client library) for:
        - Variable persistence across cells
        - Rich output handling (plots, HTML, etc.)
        - Kernel state management
        - Security sandboxing

        Args:
            request: Validated Jupyter request with code and kernel type

        Returns:
            Dictionary with execution results (stdout, stderr, return code)

        Security Note:
            ⚠️ Executes Python code with basic validation.
            Dangerous patterns are blocked by model validation.
        """
        code = request.code
        kernel = request.kernel

        # Get timeout from config or use default
        # Increased from 60s to 300s - code execution can vary widely
        # Simple print: <1s, Complex computation: minutes
        # Safety limit, not expectation
        timeout = 300
        if self.config_manager:
            timeout = self.config_manager.get("jupyter.timeout", 300)

        try:
            # Execute Python code in isolated subprocess
            #
            # Future Enhancement: jupyter_client Integration
            # -------------------------------------------------
            # For true notebook integration, replace subprocess with:
            #   from jupyter_client import KernelManager
            #   km = KernelManager(kernel_name='python3')
            #   km.start_kernel()
            #   kc = km.client()
            #   kc.execute(code)
            #
            # Benefits:
            #   - Persistent kernel state between executions
            #   - Rich output formatting (HTML, images, LaTeX)
            #   - Interrupt/restart capabilities
            #   - Multiple kernel support (Python, R, Julia)
            #
            # Current approach: subprocess (stateless, safer for MVP)
            result = self._run_subprocess(["python", "-c", code], timeout=timeout)

            return {
                "success": result["returncode"] == 0,
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "return_code": result["returncode"],
                "kernel_used": kernel,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Code execution timed out after {timeout} seconds",
                "stdout": "",
                "stderr": "TimeoutExpired",
                "return_code": -1,
            }
        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
            }

    def _run_subprocess(self, command: list, timeout: int = 60) -> Dict[str, Any]:
        """Run subprocess command synchronously"""
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }

        except subprocess.TimeoutExpired:
            raise
        except Exception as e:
            logger.error(f"Subprocess execution failed: {e}")
            return {"stdout": "", "stderr": str(e), "returncode": 1}

    def validate_code_safety(self, code: str) -> tuple[bool, str]:
        """
        Additional code safety validation beyond model validation

        Returns:
            Tuple of (is_safe, error_message)
        """
        # Check for additional dangerous patterns
        dangerous_imports = [
            "ctypes",
            "winreg",
            "nt",
            "posix",
            "pwd",
            "grp",
            "resource",
            "termios",
            "tty",
            "pty",
        ]

        for pattern in dangerous_imports:
            if f"import {pattern}" in code or f"from {pattern}" in code:
                return False, f"Import of dangerous module not allowed: {pattern}"

        # Check for file system operations
        filesystem_ops = ["open(", "write(", "unlink(", "remove("]
        for op in filesystem_ops:
            if op in code:
                return False, f"File system operation not allowed: {op}"

        return True, ""
