"""🚀 Enhanced Context Browser Desktop App Launcher.

Launches the Enhanced Interactive Context Browser in a dedicated app window.
"""

import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# Ensure project root on sys.path for config imports
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

try:
    from config.service_config import ServiceConfig
except ImportError:  # pragma: no cover - fallback for packaged contexts
    ServiceConfig = None


def _context_browser_url() -> str:
    env_base = os.environ.get("CONTEXT_BROWSER_BASE_URL") or os.environ.get("STREAMLIT_BASE_URL")
    if env_base:
        return env_base

    host = os.environ.get("CONTEXT_BROWSER_HOST") or os.environ.get(
        "STREAMLIT_HOST",
        "http://127.0.0.1",
    )
    port = os.environ.get("CONTEXT_BROWSER_PORT") or os.environ.get(
        "STREAMLIT_PORT",
        "8501",
    )
    host = host or "http://127.0.0.1"
    return f"{host.rstrip('/')}:" + str(port)


def launch_app() -> None:
    """Launch the Enhanced Context Browser as a desktop app."""
    # Path to the fixed context browser
    app_path = Path(__file__).parent / "Enhanced-Interactive-Context-Browser-Fixed.py"

    context_url = (
        ServiceConfig.get_context_browser_url() if ServiceConfig else _context_browser_url()
    )
    parsed = urlparse(context_url if "://" in context_url else f"http://{context_url}")
    host = parsed.hostname or "localhost"
    port = parsed.port or 8501

    try:
        # Launch Streamlit with app-optimized settings
        cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(app_path),
            "--server.headless=false",
            "--server.runOnSave=true",
            "--browser.gatherUsageStats=false",
            "--theme.base=dark",
            f"--server.address={host}",
            f"--server.port={port}",
            "--global.developmentMode=false",
        ]

        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        time.sleep(3)  # Give it time to start

        # Check if process is running
        if process.poll() is None:
            try:
                # Wait for the process to complete
                process.wait()
            except KeyboardInterrupt:
                process.terminate()
        else:
            _stdout, _stderr = process.communicate()

    except (OSError, subprocess.SubprocessError):
        logger.debug("Suppressed OSError/subprocess", exc_info=True)


if __name__ == "__main__":
    launch_app()
