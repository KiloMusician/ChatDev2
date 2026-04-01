"""[DEPRECATED] Testing dashboard — Use src/observability/health_dashboard_consolidated.py.

This file is a compatibility shim redirecting to the unified health dashboard.
Deprecation Date: 2026-02-28
Removal Date: 2026-04-28 (60 days)

⚠️  MIGRATION: Replace imports from src.diagnostics.testing_dashboard with:
    from src.observability.health_dashboard_consolidated import UnifiedHealthDashboard, HealthCategory

    # Old usage:
    # src.diagnostics.testing_dashboard.main

    # New usage:
    # src.observability.health_dashboard_consolidated.UnifiedHealthDashboard
    # dashboard = UnifiedHealthDashboard()
    # snapshot = await dashboard.get_category_health(HealthCategory.TESTING)
"""

import asyncio
import logging
import sys
import warnings
from pathlib import Path

logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# Deprecation warning
warnings.warn(
    "src/diagnostics/testing_dashboard.py is deprecated. "
    "Use 'python -m src.observability.health_dashboard_consolidated --category testing' instead. "
    "This shim will be removed on 2026-04-28.",
    DeprecationWarning,
    stacklevel=2,
)

# Import consolidated version
try:
    from src.observability.health_dashboard_consolidated import (
        HealthCategory, UnifiedHealthDashboard)
except ImportError as e:
    logger.error(f"❌ Failed to import consolidated health dashboard: {e}", file=sys.stderr)
    logger.info("Install dependencies: pip install -e .", file=sys.stderr)
    sys.exit(1)


async def main():
    """Legacy main function — redirects to consolidated testing health checks."""
    dashboard = UnifiedHealthDashboard()

    logger.info("\n" + "=" * 60)
    logger.info("🧪 TESTING SYSTEM HEALTH (Consolidated)")
    logger.info("=" * 60)
    logger.warning("⚠️  Using compatibility shim — update imports!")
    logger.info("=" * 60 + "\n")

    # Get testing-specific health checks
    checks = await dashboard.get_category_health(HealthCategory.TESTING)

    # Print results
    for check in checks:
        status_emoji = check.status.emoji()
        logger.info(f"{status_emoji} {check.name}")
        logger.info(f"   {check.message}")
        if check.details:
            logger.info(f"   Details: {check.details}")
        logger.info()

    # Summary
    healthy = sum(1 for c in checks if c.status.value == "healthy")
    warning = sum(1 for c in checks if c.status.value == "warning")
    critical = sum(1 for c in checks if c.status.value == "critical")

    logger.warning(f"\n📊 Summary: {healthy} healthy, {warning} warnings, {critical} critical\n")


if __name__ == "__main__":
    logger.warning("\n⚠️  DEPRECATION WARNING ⚠️")
    logger.info("src/diagnostics/testing_dashboard.py will be removed on 2026-04-28")
    logger.info(
        "Use: python -m src.observability.health_dashboard_consolidated --category testing\n"
    )

    # Run testing-specific checks
    asyncio.run(main())
