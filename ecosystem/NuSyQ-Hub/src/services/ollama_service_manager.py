"""Ollama Service Manager — Handles WSL/native Ollama lifecycle.

Addresses the persistent "Ollama offline" issue by:
1. Detecting whether Ollama runs in WSL or native Windows
2. Properly starting/restarting Ollama considering WSL relay complications
3. Providing auto-recovery hooks for the agent registry and healing system

Key insight from CLAUDE.md gotcha:
- On Windows, Ollama often runs inside WSL (Ubuntu)
- WSL relay (wslrelay.exe) forwards port 11434 to host
- The relay can exist but be stale (WinError 10053/10054)
- Fix: `wsl --shutdown` then `wsl -e ollama serve`

Usage:
    from src.services.ollama_service_manager import OllamaServiceManager

    mgr = OllamaServiceManager()
    if not mgr.is_healthy():
        mgr.ensure_running()  # Auto-detects WSL vs native and starts appropriately

OmniTag: {
    "purpose": "Ollama lifecycle management with WSL awareness",
    "dependencies": ["subprocess", "requests"],
    "context": "Service management for local LLM backend",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

import logging
import os
import shlex
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class OllamaEnvironment(str, Enum):
    """Where Ollama is installed/running."""

    NATIVE_WINDOWS = "native_windows"  # Ollama.exe in Windows PATH
    WSL = "wsl"  # Ollama inside WSL, relayed to host
    DOCKER = "docker"  # Ollama in Docker container
    UNAVAILABLE = "unavailable"  # Not detected


@dataclass
class OllamaStatus:
    """Health status of Ollama service."""

    healthy: bool
    environment: OllamaEnvironment
    port: int = 11434
    models_available: int = 0
    latency_ms: float | None = None
    error: str | None = None
    wsl_relay_stale: bool = False
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "healthy": self.healthy,
            "environment": self.environment.value,
            "port": self.port,
            "models_available": self.models_available,
            "latency_ms": round(self.latency_ms, 1) if self.latency_ms else None,
            "error": self.error,
            "wsl_relay_stale": self.wsl_relay_stale,
            "detail": self.detail,
        }


class OllamaServiceManager:
    """Manages Ollama service lifecycle with WSL awareness.

    Core responsibilities:
    1. Detect Ollama environment (native Windows, WSL, Docker, unavailable)
    2. Health check with WSL relay stale detection
    3. Start/restart with appropriate method for environment
    4. Auto-recovery when detected as unhealthy
    """

    OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "127.0.0.1")
    OLLAMA_PORT = int(os.environ.get("OLLAMA_PORT", "11434"))
    PROBE_TIMEOUT = 3.0  # seconds
    START_WAIT_TIMEOUT = 30  # seconds to wait for Ollama to start

    def __init__(self, auto_start: bool = False) -> None:
        """Initialize manager.

        Args:
            auto_start: If True, automatically start Ollama if offline at init
        """
        self._environment: OllamaEnvironment | None = None
        self._last_status: OllamaStatus | None = None

        if auto_start:
            self.ensure_running()

    @staticmethod
    def _is_wsl_runtime() -> bool:
        """Return True when the current Python process is running inside WSL."""
        if os.getenv("WSL_DISTRO_NAME"):
            return True
        try:
            return "microsoft" in Path("/proc/version").read_text(encoding="utf-8").lower()
        except OSError:
            return False

    @staticmethod
    def _managed_ollama_home() -> str:
        """Return a writable NuSyQ-managed home for Ollama runtime state."""
        runtime_home = Path(__file__).resolve().parents[2] / "state" / "runtime" / "ollama" / "home"
        runtime_home.mkdir(parents=True, exist_ok=True)
        return str(runtime_home)

    @property
    def base_url(self) -> str:
        return f"http://{self.OLLAMA_HOST}:{self.OLLAMA_PORT}"

    def detect_environment(self) -> OllamaEnvironment:
        """Detect where Ollama is installed/running.

        Priority:
        1. Native Windows (ollama.exe in PATH or AppData)
        2. WSL (wsl -e which ollama succeeds)
        3. Docker (docker ps shows ollama container)
        4. Unavailable
        """
        if self._environment:
            return self._environment

        ollama_exe = shutil.which("ollama")
        if self._is_wsl_runtime() and ollama_exe:
            self._environment = OllamaEnvironment.WSL
            logger.info(f"Detected Ollama in WSL PATH: {ollama_exe}")
            return self._environment

        # Check native Windows first
        if ollama_exe:
            self._environment = OllamaEnvironment.NATIVE_WINDOWS
            logger.info(f"Detected native Windows Ollama at: {ollama_exe}")
            return self._environment

        # Check AppData location
        appdata_ollama = (
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"
        )
        if appdata_ollama.exists():
            self._environment = OllamaEnvironment.NATIVE_WINDOWS
            logger.info(f"Detected native Windows Ollama in AppData: {appdata_ollama}")
            return self._environment

        # Check WSL
        if sys.platform == "win32":
            try:
                result = subprocess.run(
                    ["wsl", "-e", "which", "ollama"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if result.returncode == 0 and result.stdout.strip():
                    self._environment = OllamaEnvironment.WSL
                    logger.info(f"Detected Ollama in WSL: {result.stdout.strip()}")
                    return self._environment
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                logger.debug("Suppressed FileNotFoundError/OSError/subprocess", exc_info=True)

        # Check Docker
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=ollama", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0 and "ollama" in result.stdout.lower():
                self._environment = OllamaEnvironment.DOCKER
                logger.info("Detected Ollama in Docker container")
                return self._environment
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            logger.debug("Suppressed FileNotFoundError/OSError/subprocess", exc_info=True)

        self._environment = OllamaEnvironment.UNAVAILABLE
        logger.warning("Ollama not detected in any environment")
        return self._environment

    def _check_wsl_relay_stale(self) -> bool:
        """Check if WSL relay is listening but connection is broken.

        Returns True if port 11434 is owned by wslrelay.exe but HTTP fails.
        """
        if sys.platform != "win32":
            return False

        try:
            # Check what process owns port 11434
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            # Find line with 11434 LISTENING
            for line in result.stdout.splitlines():
                if f":{self.OLLAMA_PORT}" in line and "LISTENING" in line:
                    parts = line.split()
                    if parts:
                        try:
                            pid = int(parts[-1])
                            proc_result = subprocess.run(
                                ["powershell", "-Command", f"(Get-Process -Id {pid}).ProcessName"],
                                capture_output=True,
                                text=True,
                                timeout=5,
                                check=False,
                            )
                            if "wslrelay" in proc_result.stdout.lower():
                                # Port is owned by wslrelay — if HTTP fails, relay is stale
                                return True
                        except (ValueError, subprocess.TimeoutExpired):
                            logger.debug("Suppressed ValueError/subprocess", exc_info=True)
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            logger.debug("Suppressed FileNotFoundError/OSError/subprocess", exc_info=True)

        return False

    def check_health(
        self, force_probe: bool = False, _force_probe: bool | None = None
    ) -> OllamaStatus:
        """Check Ollama health via HTTP probe.

        Args:
            force_probe: If True, always probe even if recently checked

        Returns:
            OllamaStatus with health details
        """
        _ = force_probe
        if _force_probe is not None:
            force_probe = _force_probe

        import time

        url = f"{self.base_url}/api/tags"
        start = time.monotonic()

        try:
            import json as _json
            import urllib.request

            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=self.PROBE_TIMEOUT) as resp:
                latency = (time.monotonic() - start) * 1000
                body = resp.read().decode("utf-8", errors="replace")
                data = _json.loads(body)
                models = data.get("models", [])

                self._last_status = OllamaStatus(
                    healthy=True,
                    environment=self.detect_environment(),
                    models_available=len(models),
                    latency_ms=latency,
                    detail=f"Responsive with {len(models)} models",
                )
                try:
                    from src.system.agent_awareness import emit as _emit

                    _emit(
                        "ollama",
                        f"Ollama: ONLINE models={len(models)} latency={latency:.0f}ms",
                        level="INFO",
                        source="ollama_service_manager",
                    )
                except Exception:
                    pass
                return self._last_status

        except Exception as e:
            # Check if WSL relay is stale
            wsl_stale = self._check_wsl_relay_stale()

            self._last_status = OllamaStatus(
                healthy=False,
                environment=self.detect_environment(),
                error=str(e)[:200],
                wsl_relay_stale=wsl_stale,
                detail=(
                    "WSL relay stale — run `wsl --shutdown` then restart"
                    if wsl_stale
                    else str(e)[:100]
                ),
            )
            try:
                from src.system.agent_awareness import emit as _emit

                _lvl = "WARNING" if wsl_stale else "ERROR"
                _emit(
                    "ollama",
                    f"Ollama: OFFLINE wsl_stale={wsl_stale} err={str(e)[:80]}",
                    level=_lvl,
                    source="ollama_service_manager",
                )
            except Exception:
                pass
            return self._last_status

    def is_healthy(self) -> bool:
        """Quick health check."""
        return self.check_health().healthy

    def _start_native_windows(self) -> bool:
        """Start Ollama on native Windows."""
        ollama_exe = shutil.which("ollama")
        if not ollama_exe:
            appdata_ollama = (
                Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"
            )
            if appdata_ollama.exists():
                ollama_exe = str(appdata_ollama)
            else:
                logger.error("Cannot find ollama.exe for native Windows start")
                return False

        try:
            # Start as background process
            creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            subprocess.Popen(
                [ollama_exe, "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags,
            )
            logger.info(f"Started native Windows Ollama: {ollama_exe} serve")
            return True
        except Exception as e:
            logger.error(f"Failed to start native Windows Ollama: {e}")
            return False

    def _start_wsl(self, restart_wsl: bool = False) -> bool:
        """Start Ollama in WSL.

        Args:
            restart_wsl: If True, run `wsl --shutdown` first to clear stale relays
        """
        in_wsl_runtime = self._is_wsl_runtime()

        if restart_wsl and not in_wsl_runtime:
            logger.info("Restarting WSL to clear stale relays...")
            try:
                subprocess.run(
                    ["wsl", "--shutdown"],
                    capture_output=True,
                    timeout=30,
                    check=False,
                )
                time.sleep(2)  # Give WSL time to fully shutdown
            except Exception as e:
                logger.warning(f"WSL shutdown failed (continuing anyway): {e}")
        elif restart_wsl and in_wsl_runtime:
            logger.info("Restart requested inside WSL runtime; skipping wsl --shutdown")

        try:
            managed_home = self._managed_ollama_home()
            shell_prefix = (
                f"export HOME={shlex.quote(managed_home)} OLLAMA_HOME={shlex.quote(managed_home)}; "
            )
            env = os.environ.copy()
            env.setdefault("HOME", managed_home)
            env.setdefault("OLLAMA_HOME", managed_home)
            if in_wsl_runtime:
                subprocess.Popen(
                    [
                        "bash",
                        "-lc",
                        f"{shell_prefix}nohup ollama serve > /tmp/ollama-serve.log 2>&1 &",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                    env=env,
                )
                logger.info(
                    "Started Ollama directly inside WSL via: bash -lc 'nohup ollama serve &'"
                )
            else:
                # Start ollama serve in WSL background from the Windows host.
                subprocess.Popen(
                    [
                        "wsl",
                        "-e",
                        "bash",
                        "-lc",
                        f"{shell_prefix}nohup ollama serve > /dev/null 2>&1 &",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env=env,
                )
                logger.info("Started Ollama in WSL via: wsl -e bash -c 'nohup ollama serve &'")
            return True
        except Exception as e:
            logger.error(f"Failed to start Ollama in WSL: {e}")
            return False

    def _start_docker(self) -> bool:
        """Start Ollama Docker container."""
        try:
            subprocess.run(
                ["docker", "start", "ollama"],
                capture_output=True,
                timeout=30,
                check=True,
            )
            logger.info("Started Ollama Docker container")
            return True
        except Exception as e:
            logger.error(f"Failed to start Ollama Docker container: {e}")
            return False

    def start(self, force_wsl_restart: bool = False) -> bool:
        """Start Ollama service based on detected environment.

        Args:
            force_wsl_restart: If True and environment is WSL, run wsl --shutdown first

        Returns:
            True if Ollama becomes healthy within timeout
        """
        env = self.detect_environment()

        if env == OllamaEnvironment.UNAVAILABLE:
            logger.error("Cannot start Ollama — not installed in any known location")
            return False

        # Check current health and WSL relay status
        status = self.check_health()
        if status.healthy:
            logger.info("Ollama already healthy, no start needed")
            return True

        # If WSL relay is stale, force restart
        if status.wsl_relay_stale:
            force_wsl_restart = True
            logger.warning("Detected stale WSL relay — will restart WSL")

        # Start based on environment
        started = False
        if env == OllamaEnvironment.NATIVE_WINDOWS:
            started = self._start_native_windows()
        elif env == OllamaEnvironment.WSL:
            started = self._start_wsl(restart_wsl=force_wsl_restart)
        elif env == OllamaEnvironment.DOCKER:
            started = self._start_docker()

        if not started:
            return False

        # Wait for health
        return self._wait_for_health()

    def _wait_for_health(self) -> bool:
        """Wait for Ollama to become healthy."""
        logger.info(f"Waiting up to {self.START_WAIT_TIMEOUT}s for Ollama to start...")

        for i in range(self.START_WAIT_TIMEOUT):
            time.sleep(1)
            status = self.check_health(force_probe=True)
            if status.healthy:
                logger.info(
                    f"Ollama healthy after {i + 1}s — {status.models_available} models available"
                )
                try:
                    from src.system.agent_awareness import emit as _emit

                    _emit.agent_online(
                        "ollama",
                        f"started in {i + 1}s | {status.models_available} models",
                    )
                except Exception:
                    pass
                return True
            if i % 5 == 4:
                logger.debug(f"Still waiting... ({i + 1}s)")

        logger.error(f"Ollama did not become healthy within {self.START_WAIT_TIMEOUT}s")
        try:
            from src.system.agent_awareness import emit as _emit

            _emit(
                "ollama",
                f"TIMEOUT: did not start within {self.START_WAIT_TIMEOUT}s",
                level="ERROR",
                source="ollama_service",
            )
        except Exception:
            pass
        return False

    def ensure_running(self) -> bool:
        """Ensure Ollama is running, starting it if necessary.

        This is the main entry point for auto-recovery.
        Should be called before any Ollama-dependent operation.

        Returns:
            True if Ollama is healthy (was already running or successfully started)
        """
        status = self.check_health()
        if status.healthy:
            return True

        logger.info(f"Ollama not healthy ({status.detail}), attempting to start...")
        return self.start(force_wsl_restart=status.wsl_relay_stale)

    def restart(self) -> bool:
        """Force restart Ollama (useful for stuck states)."""
        env = self.detect_environment()

        # For WSL, always do a full restart
        if env == OllamaEnvironment.WSL:
            return self.start(force_wsl_restart=True)

        # For native/Docker, just start (it handles duplicate starts gracefully)
        return self.start()


# ── Convenience functions ────────────────────────────────────────────────────


def ensure_ollama() -> bool:
    """Convenience function to ensure Ollama is running.

    Usage:
        from src.services.ollama_service_manager import ensure_ollama

        if ensure_ollama():
            # Ollama is ready to use
            ...
    """
    mgr = OllamaServiceManager()
    return mgr.ensure_running()


def get_ollama_status() -> OllamaStatus:
    """Get current Ollama status without starting."""
    mgr = OllamaServiceManager()
    return mgr.check_health()


# ── CLI entry point ──────────────────────────────────────────────────────────


if __name__ == "__main__":
    import argparse
    import json

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    parser = argparse.ArgumentParser(description="Ollama Service Manager")
    parser.add_argument(
        "action", choices=["status", "start", "restart", "ensure"], help="Action to perform"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    mgr = OllamaServiceManager()

    if args.action == "status":
        status = mgr.check_health()
        if args.json:
            logger.info(json.dumps(status.to_dict(), indent=2))
        else:
            emoji = "✅" if status.healthy else "❌"
            logger.info(f"{emoji} Ollama {status.environment.value}")
            logger.info(f"   Healthy: {status.healthy}")
            if status.models_available:
                logger.info(f"   Models: {status.models_available}")
            if status.latency_ms:
                logger.info(f"   Latency: {status.latency_ms:.0f}ms")
            if status.error:
                logger.error(f"   Error: {status.error}")
            if status.wsl_relay_stale:
                logger.warning("   ⚠️  WSL relay stale — recommend: wsl --shutdown")

    elif args.action == "start":
        success = mgr.start()
        if args.json:
            logger.info(json.dumps({"success": success}))
        else:
            logger.error("✅ Ollama started" if success else "❌ Failed to start Ollama")
        sys.exit(0 if success else 1)

    elif args.action == "restart":
        success = mgr.restart()
        if args.json:
            logger.info(json.dumps({"success": success}))
        else:
            logger.error("✅ Ollama restarted" if success else "❌ Failed to restart Ollama")
        sys.exit(0 if success else 1)

    elif args.action == "ensure":
        success = mgr.ensure_running()
        if args.json:
            logger.info(json.dumps({"success": success}))
        else:
            logger.error(
                "✅ Ollama is running" if success else "❌ Could not ensure Ollama is running"
            )
        sys.exit(0 if success else 1)
