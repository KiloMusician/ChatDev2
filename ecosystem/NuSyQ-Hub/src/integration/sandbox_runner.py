"""Sandbox Runner (Phase 3) - per-task containerized execution.

Lightweight runner that spins an ephemeral container using the existing
ChatDev CI image, mounts a temp workspace, and enforces resource caps.
"""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from src.config.feature_flag_manager import is_feature_enabled
from src.system.telemetry import log_span


@dataclass
class SandboxResult:
    success: bool
    returncode: int
    stdout: str
    stderr: str
    workdir: Path


class SandboxRunner:
    def __init__(
        self,
        image: str = "sheepgreen/chatdev:latest",
        cpu: str = "1",
        mem: str = "1g",
        timeout: int = 600,
        network: str = "none",
    ) -> None:
        """Initialize SandboxRunner with image, cpu, mem, ...."""
        self.image = image
        self.cpu = cpu
        self.mem = mem
        self.timeout = timeout
        self.network = network

    def run(
        self,
        command: list[str],
        env: dict[str, str] | None = None,
        readonly_mount: Path | None = None,
    ) -> SandboxResult:
        if not is_feature_enabled("sandbox_runner_enabled"):
            return SandboxResult(False, -1, "", "sandbox_runner_disabled", Path("."))

        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            warehouse = workdir / "WareHouse"
            warehouse.mkdir(parents=True, exist_ok=True)

            docker_cmd = [
                "docker",
                "run",
                "--rm",
                "--cpus",
                self.cpu,
                "--memory",
                self.mem,
                "--network",
                self.network,
                "-v",
                f"{workdir}:/workspace",
                "-w",
                "/workspace",
            ]
            if readonly_mount:
                docker_cmd += ["-v", f"{readonly_mount}:/workspace/input:ro"]
            if env:
                for k, v in env.items():
                    docker_cmd += ["-e", f"{k}={v}"]

            docker_cmd += [self.image, *command]

            try:
                proc = subprocess.run(
                    docker_cmd,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
                return SandboxResult(
                    success=proc.returncode == 0,
                    returncode=proc.returncode,
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                    workdir=workdir,
                )
            except subprocess.TimeoutExpired as e:
                log_span("sandbox_run", {"status": "timeout", "command": command})
                return SandboxResult(False, -1, e.stdout or "", "timeout", workdir)
            except Exception as e:  # pragma: no cover - best-effort wrapper
                log_span("sandbox_run", {"status": "error", "error": str(e)})
                return SandboxResult(False, -1, "", str(e), workdir)


def get_sandbox_runner() -> SandboxRunner:
    return SandboxRunner()
