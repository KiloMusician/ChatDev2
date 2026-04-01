"""Zero-Token Bridge: NuSyQ-Hub ↔ SimulatedVerse Integration.

Coordinates zero-token operations across both repositories.

[OmniTag: zero_token_bridge, cross_repo_integration, sns_core, cost_optimization]
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ZeroTokenBridge:
    """Coordinates zero-token mode across NuSyQ-Hub and SimulatedVerse."""

    def __init__(self, nusyq_hub: Path | None = None, simverse: Path | None = None):
        """Initialize bridge with repository paths."""
        self.nusyq_hub = nusyq_hub or Path.cwd()
        self.simverse = simverse
        self.bridge_log = self.nusyq_hub / "state" / "zero_token_bridge.jsonl"
        self._ensure_bridge_log()

    def _ensure_bridge_log(self) -> None:
        """Ensure bridge log file exists."""
        self.bridge_log.parent.mkdir(parents=True, exist_ok=True)
        if not self.bridge_log.exists():
            self.bridge_log.touch()

    def _log_operation(self, op_type: str, data: dict[str, Any]) -> None:
        """Log zero-token operation."""
        import time

        entry = {
            "timestamp": time.time(),
            "operation": op_type,
            **data,
        }
        try:
            with open(self.bridge_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            logger.debug("Suppressed Exception", exc_info=True)

    def check_simverse_availability(self) -> bool:
        """Check if SimulatedVerse is available and operational."""
        if not self.simverse:
            return False

        if not self.simverse.exists():
            return False

        # Check for key SimulatedVerse files
        required_files = ["package.json", "src"]
        return all((self.simverse / required).exists() for required in required_files)

    def get_zero_token_status(self) -> dict[str, Any]:
        """Get unified zero-token mode status across ecosystem."""
        status = {
            "sns_core": self._get_sns_core_status(),
            "simverse": self._get_simverse_status(),
            "bridge_operational": self.check_simverse_availability(),
            "savings_estimate": {
                "sns_core": "$70-170/year (41% validated)",
                "simverse": "$880/year (95% offline)",
                "combined": "$950-1,050/year potential",
            },
        }
        return status

    def _get_sns_core_status(self) -> dict[str, Any]:
        """Get SNS-Core system status."""
        sns_path = self.nusyq_hub / "temp_sns_core"
        sns_readme = sns_path / "README.md"

        status = {
            "available": sns_path.exists(),
            "path": str(sns_path) if sns_path.exists() else None,
            "validated_reduction": "41%",
            "claimed_reduction": "60-85%",
        }

        if sns_readme.exists():
            status["documentation"] = "available"

        return status

    def _get_simverse_status(self) -> dict[str, Any]:
        """Get SimulatedVerse zero-token mode status."""
        if not self.simverse:
            return {
                "available": False,
                "path": None,
                "zero_token_mode": "unknown",
            }

        available = self.check_simverse_availability()
        status: dict[str, Any] = {
            "available": available,
            "path": str(self.simverse) if available else None,
        }

        if available:
            # Check for zero-token scripts
            scripts_dir = self.simverse / "scripts"
            if scripts_dir.exists():
                zero_token_scripts = list(scripts_dir.glob("*zero*")) + list(
                    scripts_dir.glob("*offline*")
                )
                status["zero_token_scripts"] = len(zero_token_scripts)
                status["zero_token_available"] = len(zero_token_scripts) > 0

        return status

    def convert_ai_response_to_sns(self, response: str) -> tuple[str, dict[str, Any]]:
        """Convert AI response to SNS-Core notation for token savings."""
        try:
            from src.utils.sns_core_helper import convert_to_sns

            sns_response, metadata = convert_to_sns(response, aggressive=False)
            self._log_operation(
                "ai_response_conversion",
                {
                    "original_tokens": metadata["original_tokens_est"],
                    "sns_tokens": metadata["sns_tokens_est"],
                    "savings_pct": metadata["savings_pct"],
                },
            )
            return sns_response, metadata
        except Exception as exc:
            self._log_operation("ai_response_conversion_error", {"error": str(exc)})
            return response, {}

    def estimate_operation_cost(self, operation: str, complexity: str = "normal") -> dict[str, Any]:
        """Estimate cost of operation in zero-token mode vs standard mode."""
        # Complexity: simple, normal, complex
        base_cost = {
            "simple": {"standard": 0.001, "zero_token": 0.0},
            "normal": {"standard": 0.01, "zero_token": 0.0},
            "complex": {"standard": 0.1, "zero_token": 0.0},
        }

        cost_data = base_cost.get(complexity, base_cost["normal"])
        savings = cost_data["standard"] - cost_data["zero_token"]

        return {
            "operation": operation,
            "complexity": complexity,
            "standard_cost": f"${cost_data['standard']:.4f}",
            "zero_token_cost": "$0.0000",
            "savings": f"${savings:.4f}",
            "savings_percentage": 100 if cost_data["zero_token"] == 0 else 0,
        }

    def generate_bridge_report(self) -> str:
        """Generate comprehensive zero-token bridge status report."""
        status = self.get_zero_token_status()
        sns = status["sns_core"]
        sv = status["simverse"]

        report = []
        report.append("🌉 Zero-Token Bridge Status Report")
        report.append("=" * 50)

        report.append("\n🔣 SNS-Core System:")
        report.append(f"  Available: {'✅' if sns['available'] else '❌'}")
        if sns["available"]:
            report.append(f"  Validated Reduction: {sns['validated_reduction']}")
            report.append(f"  Claimed Reduction: {sns['claimed_reduction']}")

        report.append("\n🎮 SimulatedVerse Zero-Token Mode:")
        report.append(f"  Available: {'✅' if sv['available'] else '❌'}")
        if sv["available"] and "zero_token_available" in sv:
            report.append(f"  Zero-Token Scripts: {sv.get('zero_token_scripts', 0)}")

        report.append("\n💰 Savings Estimate:")
        for system, estimate in status["savings_estimate"].items():
            report.append(f"  {system}: {estimate}")

        report.append("\n🔗 Bridge Status:")
        report.append(f"  Operational: {'✅' if status['bridge_operational'] else '⚠️'}")

        report.append("\n📊 Commands:")
        report.append("  • python scripts/start_nusyq.py sns_analyze <text>")
        report.append("  • python scripts/start_nusyq.py sns_convert <text>")
        report.append("  • python scripts/start_nusyq.py zero_token_status")

        return "\n".join(report)


def get_zero_token_bridge(
    nusyq_hub: Path | None = None, simverse: Path | None = None
) -> ZeroTokenBridge:
    """Get or create zero-token bridge instance."""
    return ZeroTokenBridge(nusyq_hub, simverse)


if __name__ == "__main__":
    bridge = ZeroTokenBridge()
    logger.info(bridge.generate_bridge_report())
