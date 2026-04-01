"""AI Health Probe - Check availability of Ollama, ChatDev, and Quantum systems.

This module provides health checks for critical AI systems and can gate work
based on their availability. Designed to be called during startup.
"""

from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """Health status for a single AI system."""

    name: str
    available: bool
    version: str | None = None
    endpoint: str | None = None
    latency_ms: float | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "available": self.available,
            "version": self.version,
            "endpoint": self.endpoint,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "metadata": self.metadata or {},
        }


@dataclass
class AIHealthReport:
    """Complete health report for all AI systems."""

    ollama: HealthStatus
    chatdev: HealthStatus
    quantum: HealthStatus
    timestamp: str
    overall_score: float  # 0.0-1.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "ollama": self.ollama.to_dict(),
            "chatdev": self.chatdev.to_dict(),
            "quantum": self.quantum.to_dict(),
            "timestamp": self.timestamp,
            "overall_score": self.overall_score,
        }

    def is_healthy(self, min_score: float = 0.66) -> bool:
        """Check if system is healthy enough to proceed."""
        return self.overall_score >= min_score

    def get_available_systems(self) -> list[str]:
        """Get list of available AI systems."""
        available = []
        if self.ollama.available:
            available.append("ollama")
        if self.chatdev.available:
            available.append("chatdev")
        if self.quantum.available:
            available.append("quantum")
        return available

    def get_unavailable_systems(self) -> list[str]:
        """Get list of unavailable AI systems."""
        unavailable = []
        if not self.ollama.available:
            unavailable.append("ollama")
        if not self.chatdev.available:
            unavailable.append("chatdev")
        if not self.quantum.available:
            unavailable.append("quantum")
        return unavailable


def probe_ollama(timeout: int = 5) -> HealthStatus:
    """Check Ollama availability and version.

    Args:
        timeout: Timeout in seconds for health check

    Returns:
        HealthStatus with Ollama availability info
    """
    import time

    start_time = time.time()

    try:
        # Check if ollama command exists (try --version first, fallback to list)
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        # Fallback to ollama list if --version doesn't work
        if result.returncode != 0:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )

        if result.returncode == 0:
            version = result.stdout.strip()
            latency_ms = (time.time() - start_time) * 1000

            # Try to get endpoint from ServiceConfig or environment
            from src.utils.config_factory import get_service_config

            config = get_service_config()
            endpoint = (
                config.OLLAMA_HOST
                if config
                else os.environ.get("OLLAMA_HOST", "http://localhost:11434")
            )

            # Quick connectivity check
            try:
                import requests

                response = requests.get(f"{endpoint}/api/tags", timeout=2)
                models = response.json().get("models", [])
                metadata = {"models_count": len(models), "endpoint_responsive": True}
            except Exception as e:
                metadata = {"endpoint_responsive": False, "endpoint_error": str(e)}

            return HealthStatus(
                name="Ollama",
                available=True,
                version=version,
                endpoint=endpoint,
                latency_ms=latency_ms,
                metadata=metadata,
            )
        else:
            return HealthStatus(
                name="Ollama",
                available=False,
                error=f"Command failed: {result.stderr.strip()}",
            )

    except FileNotFoundError:
        return HealthStatus(
            name="Ollama",
            available=False,
            error="Ollama command not found in PATH",
        )
    except subprocess.TimeoutExpired:
        return HealthStatus(
            name="Ollama",
            available=False,
            error=f"Health check timeout after {timeout}s",
        )
    except Exception as e:
        return HealthStatus(
            name="Ollama",
            available=False,
            error=f"Unexpected error: {e}",
        )


def probe_chatdev(timeout: int = 5) -> HealthStatus:
    """Check ChatDev availability.

    Args:
        timeout: Timeout in seconds for health check

    Returns:
        HealthStatus with ChatDev availability info
    """
    import time

    start_time = time.time()

    try:
        # Check for ChatDev directory
        chatdev_dir = Path("ChatDev")
        if not chatdev_dir.exists():
            return HealthStatus(
                name="ChatDev",
                available=False,
                error="ChatDev directory not found",
            )

        # Check for required files
        required_files = ["run.py", "chatchain.py"]
        missing = [f for f in required_files if not (chatdev_dir / f).exists()]

        if missing:
            return HealthStatus(
                name="ChatDev",
                available=False,
                error=f"Missing required files: {', '.join(missing)}",
            )

        # Check if Python can import ChatDev modules
        try:
            import sys

            sys.path.insert(0, str(chatdev_dir.absolute()))
            # Try to import without actually loading everything
            spec = __import__("importlib.util").util.find_spec("chatchain")
            if spec is None:
                raise ImportError("chatchain module not found")

            latency_ms = (time.time() - start_time) * 1000
            metadata = {"directory": str(chatdev_dir.absolute()), "importable": True}

            return HealthStatus(
                name="ChatDev",
                available=True,
                version="local",
                latency_ms=latency_ms,
                metadata=metadata,
            )

        except Exception as e:
            return HealthStatus(
                name="ChatDev",
                available=False,
                error=f"Import check failed: {e}",
            )

    except Exception as e:
        return HealthStatus(
            name="ChatDev",
            available=False,
            error=f"Unexpected error: {e}",
        )


def probe_quantum(timeout: int = 5) -> HealthStatus:
    """Check Quantum system availability.

    Args:
        timeout: Timeout in seconds for health check

    Returns:
        HealthStatus with Quantum system availability info
    """
    import time

    start_time = time.time()

    try:
        # Check for quantum modules
        quantum_files = [
            "src/quantum/consciousness_substrate.py",
            "src/integration/quantum_bridge.py",
            "src/integration/quantum_kilo_integration_bridge.py",
        ]

        existing = [f for f in quantum_files if Path(f).exists()]
        missing = [f for f in quantum_files if not Path(f).exists()]

        if len(existing) < 2:  # At least 2 core files should exist
            return HealthStatus(
                name="Quantum",
                available=False,
                error=f"Missing critical files: {', '.join(missing)}",
            )

        # Try to import quantum modules
        try:
            from src.quantum import consciousness_substrate

            latency_ms = (time.time() - start_time) * 1000
            metadata = {
                "modules_found": len(existing),
                "importable": True,
            }

            return HealthStatus(
                name="Quantum",
                available=True,
                version="local",
                latency_ms=latency_ms,
                metadata=metadata,
            )

        except ImportError as e:
            # Quantum might exist but have import issues
            latency_ms = (time.time() - start_time) * 1000
            return HealthStatus(
                name="Quantum",
                available=False,
                error=f"Import failed: {e}",
                latency_ms=latency_ms,
                metadata={"modules_found": len(existing), "import_error": str(e)},
            )

    except Exception as e:
        return HealthStatus(
            name="Quantum",
            available=False,
            error=f"Unexpected error: {e}",
        )


def run_full_health_check(timeout_per_system: int = 5) -> AIHealthReport:
    """Run complete health check on all AI systems.

    Args:
        timeout_per_system: Timeout in seconds for each system check

    Returns:
        AIHealthReport with complete health status
    """
    from datetime import datetime

    logger.info("🏥 Running AI systems health check...")

    ollama_status = probe_ollama(timeout=timeout_per_system)
    chatdev_status = probe_chatdev(timeout=timeout_per_system)
    quantum_status = probe_quantum(timeout=timeout_per_system)

    # Calculate overall score (0.0-1.0)
    available_count = sum(
        [ollama_status.available, chatdev_status.available, quantum_status.available]
    )
    overall_score = available_count / 3.0

    report = AIHealthReport(
        ollama=ollama_status,
        chatdev=chatdev_status,
        quantum=quantum_status,
        timestamp=datetime.now().isoformat(),
        overall_score=overall_score,
    )

    # Log results
    logger.info(
        f"   Ollama: {'✅' if ollama_status.available else '❌'} {ollama_status.version or ollama_status.error}"
    )
    logger.info(
        f"   ChatDev: {'✅' if chatdev_status.available else '❌'} {chatdev_status.error or 'Available'}"
    )
    logger.info(
        f"   Quantum: {'✅' if quantum_status.available else '❌'} {quantum_status.error or 'Available'}"
    )
    logger.info(f"   Overall Score: {overall_score:.1%}")

    return report


def save_health_report(report: AIHealthReport, output_path: Path | str) -> None:
    """Save health report to JSON file.

    Args:
        report: AIHealthReport to save
        output_path: Path to output JSON file
    """
    import json

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2)

    logger.info(f"💾 Health report saved to {output_path}")


def gate_on_health(
    report: AIHealthReport,
    required_systems: list[str] | None = None,
    min_score: float = 0.66,
) -> bool:
    """Gate work based on health report.

    Args:
        report: AIHealthReport to check
        required_systems: List of required system names (e.g., ["ollama"])
                         If None, uses min_score threshold
        min_score: Minimum overall score (0.0-1.0) to pass health gate

    Returns:
        True if health check passes, False otherwise

    Raises:
        RuntimeError: If health check fails and strict mode is enabled
    """
    if required_systems:
        # Check specific required systems
        available = report.get_available_systems()
        missing = [s for s in required_systems if s not in available]

        if missing:
            logger.warning(f"⚠️  Required systems unavailable: {', '.join(missing)}")
            return False

        logger.info(f"✅ All required systems available: {', '.join(required_systems)}")
        return True
    else:
        # Check overall score
        if report.overall_score >= min_score:
            logger.info(f"✅ Health score {report.overall_score:.1%} >= {min_score:.1%}")
            return True
        else:
            logger.warning(f"⚠️  Health score {report.overall_score:.1%} < {min_score:.1%}")
            unavailable = report.get_unavailable_systems()
            logger.warning(f"   Unavailable: {', '.join(unavailable)}")
            return False


if __name__ == "__main__":
    # Quick health check for testing
    report = run_full_health_check()

    logger.info("\n" + "=" * 70)
    logger.info("AI SYSTEMS HEALTH REPORT")
    logger.info("=" * 70)
    logger.info(f"Timestamp: {report.timestamp}")
    logger.info(f"Overall Score: {report.overall_score:.1%}\n")

    for system in [report.ollama, report.chatdev, report.quantum]:
        status_icon = "✅" if system.available else "❌"
        logger.info(f"{status_icon} {system.name}")
        if system.available:
            logger.info(f"   Version: {system.version}")
            logger.info(f"   Latency: {system.latency_ms:.1f}ms")
            if system.metadata:
                for key, value in system.metadata.items():
                    logger.info(f"   {key}: {value}")
        else:
            logger.error(f"   Error: {system.error}")
        logger.info()

    logger.info("=" * 70)
    logger.info(f"Available: {', '.join(report.get_available_systems()) or 'None'}")
    logger.info(f"Unavailable: {', '.join(report.get_unavailable_systems()) or 'None'}")
    logger.info("=" * 70)

    # Test gating
    logger.info("\nGating Tests:")
    logger.info(f"  Pass with 66% threshold: {gate_on_health(report, min_score=0.66)}")
    logger.info(
        f"  Pass with Ollama required: {gate_on_health(report, required_systems=['ollama'])}"
    )
