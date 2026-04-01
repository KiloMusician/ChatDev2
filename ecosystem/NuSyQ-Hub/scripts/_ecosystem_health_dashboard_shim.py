"""[DEPRECATED] Ecosystem health dashboard — Use src/observability/health_dashboard_consolidated.py

This file is a compatibility shim redirecting to the unified health dashboard.
Deprecation Date: 2026-02-28
Removal Date: 2026-04-28 (60 days)

⚠️  MIGRATION: Replace imports from scripts.ecosystem_health_dashboard with:
    from src.observability.health_dashboard_consolidated import UnifiedHealthDashboard, HealthCategory

    # Old usage:
    # from scripts.ecosystem_health_dashboard import main

    # New usage:
    # from src.observability.health_dashboard_consolidated import UnifiedHealthDashboard
    # dashboard = UnifiedHealthDashboard()
    # snapshot = await dashboard.get_category_health(HealthCategory.ECOSYSTEM)
"""

import asyncio
import sys
import warnings
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# Deprecation warning
warnings.warn(
    "scripts/ecosystem_health_dashboard.py is deprecated. "
    "Use 'python -m src.observability.health_dashboard_consolidated --category ecosystem' instead. "
    "This shim will be removed on 2026-04-28.",
    DeprecationWarning,
    stacklevel=2,
)

# Import consolidated version
try:
    from src.observability.health_dashboard_consolidated import (
        HealthCategory,
        UnifiedHealthDashboard,
    )
except ImportError as e:
    print(f"❌ Failed to import consolidated health dashboard: {e}", file=sys.stderr)
    print("Install dependencies: pip install -e .", file=sys.stderr)
    sys.exit(1)


async def main():
    """Legacy main function — redirects to consolidated ecosystem health checks."""
    dashboard = UnifiedHealthDashboard()

    print("\n" + "=" * 60)
    print("🌐 ECOSYSTEM HEALTH (Consolidated)")
    print("=" * 60)
    print("⚠️  Using compatibility shim — update imports!")
    print("=" * 60 + "\n")

    # Get ecosystem-specific health checks
    checks = await dashboard.get_category_health(HealthCategory.ECOSYSTEM)

    # Print results
    for check in checks:
        status_emoji = check.status.emoji()
        print(f"{status_emoji} {check.name}")
        print(f"   {check.message}")
        if check.details:
            for key, value in check.details.items():
                print(f"   - {key}: {value}")
        print()

    # Summary
    healthy = sum(1 for c in checks if c.status.value == "healthy")
    warning = sum(1 for c in checks if c.status.value == "warning")
    critical = sum(1 for c in checks if c.status.value == "critical")

    print(f"\n📊 Summary: {healthy} healthy, {warning} warnings, {critical} critical\n")


if __name__ == "__main__":
    print("\n⚠️  DEPRECATION WARNING ⚠️")
    print("scripts/ecosystem_health_dashboard.py will be removed on 2026-04-28")
    print("Use: python -m src.observability.health_dashboard_consolidated --category ecosystem\n")

    # Run ecosystem-specific checks
    asyncio.run(main())
