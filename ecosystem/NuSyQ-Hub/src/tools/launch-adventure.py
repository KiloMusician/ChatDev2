"""🎮 KILO-FOOLISH Unified Launcher with Ollama Auto-Management.

Choose your adventure with seamless AI integration!
"""

import logging
import os
import subprocess
import sys
import time
from pathlib import Path

logger = logging.getLogger(__name__)


def _maybe_get_service_url() -> str | None:
    try:
        from src.config.service_config import ServiceConfig

        return ServiceConfig.get_ollama_url()
    except (ImportError, ModuleNotFoundError, AttributeError):
        return None


def _maybe_get_ollama_host() -> str | None:
    try:
        from src.utils.config_helper import get_ollama_host

        return get_ollama_host()
    except (ImportError, ModuleNotFoundError):
        return None


def _resolve_ollama_url() -> str:
    """Resolve the Ollama base URL using config helper, ServiceConfig, or env.

    This keeps all call sites consistent and avoids hardcoded localhost defaults.
    """
    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1")
    port = os.getenv("OLLAMA_PORT", "11435")
    candidates: list[str | None] = [
        _maybe_get_ollama_host(),
        _maybe_get_service_url(),
        os.getenv("OLLAMA_BASE_URL"),
        f"{host}:{port}",
    ]
    return next((u for u in candidates if u), f"{host}:{port}")


def ensure_ollama_running():
    """Ensure Ollama is running before launching adventures."""
    try:
        import requests

        # Quick API probe
        ollama_url = _resolve_ollama_url()
        try:
            response = requests.get(f"{ollama_url}/api/tags", timeout=2)
            if response.status_code == 200:
                response.json().get("models", [])
                return True
        except requests.RequestException:
            # Not running or not responding; attempt to start it
            logger.debug("Suppressed RequestException", exc_info=True)

        # If not running, try to start Ollama (best-effort)
        if sys.platform == "win32":
            from src.utils.safe_subprocess import safe_subprocess

            safe_subprocess.Popen(
                ["ollama", "serve"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        # Wait up to ~20s for the service to appear
        for i in range(20):
            time.sleep(1)
            try:
                ollama_url = _resolve_ollama_url()
                response = requests.get(f"{ollama_url}/api/tags", timeout=2)
                if response.status_code == 200:
                    response.json().get("models", [])
                    return True
            except requests.RequestException:
                if i % 5 == 0:
                    pass
                continue

        return False

    except ImportError:
        # Try to install requests as a convenience, but don't fail hard
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=False)
            import requests  # try again

            return ensure_ollama_running()
        except (subprocess.CalledProcessError, OSError):
            return False

    except OSError:  # Remove duplicate ImportError
        return False


def main() -> None:
    # Auto-start Ollama before showing menu
    ensure_ollama_running()

    choice = input("\nChoose your adventure (1-6): ").strip()

    if choice == "1":
        subprocess.run([sys.executable, "ΞNuSyQ₁-Hub₁/ChatDev-Party-System.py"], check=False)
    elif choice == "2":
        subprocess.run([sys.executable, "src/interface/Enhanced-Wizard-Navigator.py"], check=False)
    elif choice == "3":
        # Launch the new Wizard Navigator module via Python module path
        subprocess.run(
            [sys.executable, "-m", "navigation.wizard_navigator.wizard_navigator"],
            check=False,
        )
    elif choice == "4":
        run_diagnostics()
    elif choice == "5":
        show_repo_status()
    elif choice == "6":
        manage_ollama()
    else:
        pass


def run_diagnostics() -> None:
    # Check Ollama status first
    ensure_ollama_running()

    files_to_check = [
        "src/interface/Enhanced-Wizard-Navigator.py",
        "src/navigation/wizard_navigator/wizard_navigator.py",
        "ΞNuSyQ₁-Hub₁/ChatDev-Party-System.py",
    ]

    for file in files_to_check:
        exists = Path(file).exists()
        status = "✅" if exists else "❌"
        size_kb = round(Path(file).stat().st_size / 1024, 1) if exists else 0
        logger.info(f"{status} {file} ({size_kb} KB)" if exists else f"{status} {file}")

    # Additional diagnostics

    # Check if we're in a virtual environment
    venv_status = (
        "✅ Virtual Environment"
        if hasattr(sys, "real_prefix")
        or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
        else "⚠️ Global Python"
    )
    logger.info(venv_status)


def show_repo_status() -> None:
    repo_root = Path()
    py_count = len(list(repo_root.rglob("*.py")))
    md_count = len(list(repo_root.rglob("*.md")))
    ps_count = len(list(repo_root.rglob("*.ps1")))
    logger.info(f"📦 Files — Python: {py_count}, Markdown: {md_count}, PowerShell: {ps_count}")

    # Check Ollama models if available
    try:
        import requests

        ollama_url = _resolve_ollama_url()
        response = requests.get(f"{ollama_url}/api/tags", timeout=3)
        if response.status_code == 200:
            models = response.json().get("models", [])
            for _model in models[:5]:  # Show first 5 models
                name = _model.get("name", "Unknown")
                size_gb = (_model.get("size", 0) or 0) / (1024**3)
                logger.info(f"  • {name} ({size_gb:.2f} GB)")
            if len(models) > 5:
                logger.info(f"  … and {len(models) - 5} more")
        else:
            pass
    except (ImportError, requests.RequestException, OSError):
        logger.debug("Suppressed ImportError/OSError/requests", exc_info=True)


def manage_ollama() -> None:
    """Simple Ollama management interface."""
    choice = input("\nChoose action (1-5): ").strip()

    if choice == "1":
        ensure_ollama_running()
    elif choice == "2":
        stop_ollama()
    elif choice == "3":
        check_ollama_status()
    elif choice == "4":
        list_ollama_models()
    elif choice == "5":
        stop_ollama()
        time.sleep(2)
        ensure_ollama_running()
    else:
        pass


def stop_ollama() -> None:
    """Stop Ollama service."""
    try:
        if sys.platform == "win32":
            # Windows
            subprocess.run(
                ["taskkill", "/f", "/im", "ollama.exe"],
                capture_output=True,
                check=False,
            )
        else:
            # Unix/Linux/Mac
            subprocess.run(["pkill", "-f", "ollama"], capture_output=True, check=False)

    except OSError:
        logger.debug("Suppressed OSError", exc_info=True)


def check_ollama_status() -> None:
    """Check detailed Ollama status."""
    try:
        import requests

        start_time = time.time()
        ollama_url = _resolve_ollama_url()
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        elapsed = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])

            if models:
                logger.info(
                    f"✅ Ollama responded in {elapsed:.2f}s; {len(models)} models available"
                )
                for model in models[:5]:
                    name = model.get("name", "Unknown")
                    size_gb = (model.get("size", 0) or 0) / (1024**3)
                    modified = model.get("modified", "Unknown")
                    logger.info(f"  • {name} — {size_gb:.2f} GB — modified: {modified}")

        else:
            pass

    except ImportError:
        pass
    except (ConnectionError, TimeoutError, OSError):
        logger.debug("Suppressed ConnectionError/OSError/TimeoutError", exc_info=True)


def list_ollama_models() -> None:
    """List available Ollama models with details."""
    try:
        import requests

        ollama_url = _resolve_ollama_url()
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)

        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])

            if models:
                logger.info(f"📚 Available models ({len(models)}):")
                for _i, model in enumerate(models[:10], 1):
                    name = model.get("name", "Unknown")
                    size_gb = (model.get("size", 0) or 0) / (1024**3)
                    modified = model.get("modified", "Unknown")
                    logger.info(f"  {_i}. {name} — {size_gb:.2f} GB — modified: {modified}")

            else:
                pass
        else:
            pass

    except ImportError:
        pass
    except (requests.RequestException, OSError):
        logger.debug("Suppressed OSError/requests", exc_info=True)
