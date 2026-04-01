#!/usr/bin/env python3
"""Startup wrapper with AI health check integration.

This wrapper runs health probes before launching the main system,
allowing work to be gated on AI system availability.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from system.ai_health_probe import (
    gate_on_health,
    run_full_health_check,
    save_health_report,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> int:
    """Run startup with health check."""
    parser = argparse.ArgumentParser(description="Start NuSyQ with AI systems health check")
    parser.add_argument(
        "--skip-health-check",
        action="store_true",
        help="Skip health check and start anyway",
    )
    parser.add_argument(
        "--require",
        nargs="+",
        choices=["ollama", "chatdev", "quantum"],
        help="Require specific systems to be available",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.66,
        help="Minimum health score (0.0-1.0) to proceed (default: 0.66)",
    )
    parser.add_argument(
        "--save-report",
        type=Path,
        default=Path("state/ai_health_report.json"),
        help="Path to save health report JSON",
    )
    parser.add_argument(
        "--health-only",
        action="store_true",
        help="Only run health check, don't start system",
    )

    args = parser.parse_args()

    # Run health check
    if not args.skip_health_check:
        logger.info("=" * 70)
        logger.info("AI SYSTEMS HEALTH CHECK")
        logger.info("=" * 70)

        report = run_full_health_check(timeout_per_system=5)

        # Save report
        save_health_report(report, args.save_report)

        # Gate on health
        if args.require:
            healthy = gate_on_health(report, required_systems=args.require)
        else:
            healthy = gate_on_health(report, min_score=args.min_score)

        logger.info("=" * 70)

        if not healthy:
            logger.error("❌ Health check failed. System will not start.")
            logger.error(f"   Unavailable: {', '.join(report.get_unavailable_systems())}")
            logger.info("   Fix issues or use --skip-health-check to bypass")
            return 1

        logger.info("✅ Health check passed. Proceeding with startup...")
        logger.info("=" * 70)

        if args.health_only:
            logger.info("Health check complete (--health-only mode)")
            return 0

    # Import and run main system
    try:
        # Try to import start_nusyq
        sys.path.insert(0, str(Path(__file__).parent))
        import start_nusyq

        logger.info("🚀 Launching NuSyQ main system...")
        return start_nusyq.main()

    except ImportError as e:
        logger.error(f"❌ Failed to import start_nusyq: {e}")
        logger.info("   Falling back to basic main.py")

        # Fallback to main.py
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent))
            import main

            return main.main() if hasattr(main, "main") else 0

        except Exception as fallback_error:
            logger.error(f"❌ Fallback also failed: {fallback_error}")
            return 1

    except Exception as e:
        logger.error(f"❌ System startup failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
