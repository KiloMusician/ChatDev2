"""Metrics Dashboard Startup Script

Starts the FastAPI metrics dashboard server with automatic dependency installation.

Usage:
    python scripts/start_metrics_dashboard.py
"""

import subprocess
import sys
from pathlib import Path


def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")

    dependencies = ["fastapi>=0.104.0", "uvicorn>=0.24.0", "pydantic>=2.0.0"]

    for dep in dependencies:
        print(f"  → Installing {dep}...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-q", dep], capture_output=True)
        if result.returncode != 0:
            print(f"    ⚠️  Warning: {result.stderr.decode()}")
        else:
            print(f"    ✅ {dep} installed")


def start_server():
    """Start the FastAPI server."""
    print("\n🚀 Starting Metrics Dashboard Server...\n")

    script_path = Path(__file__).parent.parent / "src" / "observability" / "metrics_dashboard_api.py"

    # Start the server
    result = subprocess.run([sys.executable, str(script_path)], cwd=str(Path(__file__).parent.parent))

    return result.returncode


def main():
    """Main startup sequence."""
    print("=" * 70)
    print("📊 NuSyQ Orchestration Metrics Dashboard Startup")
    print("=" * 70)

    # Install dependencies
    try:
        install_dependencies()
    except Exception as e:
        print(f"⚠️  Dependency installation failed: {e}")
        print("Continuing anyway...\n")

    # Start server
    print("\n" + "=" * 70)
    print("Dashboard will be available at: http://127.0.0.1:8000")
    print("API Documentation at: http://127.0.0.1:8000/docs")
    print("=" * 70 + "\n")

    exit_code = start_server()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
