#!/usr/bin/env python3
"""🏥 Health Dashboard Launcher
Quick launcher for the Enhanced Context Browser with integrated diagnostic systems.

Usage:
    python scripts/launch_health_dashboard.py
    python scripts/launch_health_dashboard.py --port 8501
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main():
    default_port = int(os.getenv("HEALTH_DASHBOARD_PORT", "8501"))
    parser = argparse.ArgumentParser(description="Launch Health Dashboard")
    parser.add_argument(
        "--port",
        type=int,
        default=default_port,
        help=f"Port number (default: {default_port} from env or 8501)",
    )
    parser.add_argument("--browser", action="store_true", help="Open in browser automatically")

    args = parser.parse_args()

    # Get project root
    project_root = Path(__file__).parent.parent
    dashboard_path = project_root / "src" / "interface" / "Enhanced-Interactive-Context-Browser-v2.py"

    if not dashboard_path.exists():
        print(f"❌ Dashboard not found at: {dashboard_path}")
        sys.exit(1)

    print("🏥 Launching NuSyQ-Hub Health Dashboard...")
    print(f"📍 Project: {project_root}")
    print(f"🌐 Port: {args.port}")
    print(f"🔗 URL: http://127.0.0.1:{args.port} (localhost)")
    print("\n" + "=" * 60)
    print("📊 FEATURES:")
    print("  ✅ Real-time system integration status")
    print("  ✅ Dependency health verification")
    print("  ✅ Repository structure checks")
    print("  ✅ Performance metrics tracking")
    print("  ✅ Auto-refresh mode (30s interval)")
    print("=" * 60 + "\n")

    cmd = [
        "streamlit",
        "run",
        str(dashboard_path),
        "--server.port",
        str(args.port),
        "--server.headless",
        "false" if args.browser else "true",
    ]

    try:
        subprocess.run(cmd, cwd=str(project_root))
    except KeyboardInterrupt:
        print("\n\n✅ Dashboard stopped gracefully")
    except Exception as e:
        print(f"\n❌ Error launching dashboard: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
