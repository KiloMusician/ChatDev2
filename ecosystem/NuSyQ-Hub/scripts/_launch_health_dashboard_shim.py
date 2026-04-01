"""[DEPRECATED] Launch health dashboard — Use src/observability/health_dashboard_consolidated.py

This file is a compatibility shim redirecting to the unified health dashboard.
Deprecation Date: 2026-02-28
Removal Date: 2026-04-28 (60 days)

⚠️  MIGRATION: Replace imports from scripts.launch_health_dashboard with:
    from src.observability.health_dashboard_consolidated import UnifiedHealthDashboard

    # Old usage:
    # from scripts.launch_health_dashboard import main

    # New usage:
    # python -m src.observability.health_dashboard_consolidated
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
    "scripts/launch_health_dashboard.py is deprecated. "
    "Use 'python -m src.observability.health_dashboard_consolidated' instead. "
    "This shim will be removed on 2026-04-28.",
    DeprecationWarning,
    stacklevel=2,
)

# Import consolidated version
try:
    from src.observability.health_dashboard_consolidated import main as consolidated_main
except ImportError as e:
    print(f"❌ Failed to import consolidated health dashboard: {e}", file=sys.stderr)
    print("Install dependencies: pip install -e .", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    print("\n⚠️  DEPRECATION WARNING ⚠️")
    print("scripts/launch_health_dashboard.py will be removed on 2026-04-28")
    print("Use: python -m src.observability.health_dashboard_consolidated\n")

    # Run consolidated version (full health report)
    asyncio.run(consolidated_main())
