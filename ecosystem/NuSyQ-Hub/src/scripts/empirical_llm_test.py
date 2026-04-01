#!/usr/bin/env python3
"""🔬 EMPIRICAL LLM SUBSYSTEM TESTING.

Direct test of what's actually functional vs architectural theater.

Based on user question: "how do we know that the chatdev module is even able
to do anything useful for our repo, at all? is it snake oil? or, is it gas?"
"""

import importlib
import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def test_ollama() -> bool | None:
    """Test if Ollama is actually running and accessible."""
    try:
        # Check if ollama command exists
        result = subprocess.run(
            ["ollama", "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            # Check available models
            models_result = subprocess.run(
                ["ollama", "list"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if models_result.returncode == 0:
                models = models_result.stdout.strip().split("\n")[1:]  # Skip header
                for model in models:
                    if model.strip():
                        pass
                return True
            return False
        return False
    except subprocess.TimeoutExpired:
        return False
    except FileNotFoundError:
        return False
    except (subprocess.CalledProcessError, OSError):
        return False


def test_chatdev_import() -> bool | None:
    """Test if ChatDev can be imported and what version."""
    try:
        # Try to import chatdev
        import chatdev

        # Try to get version
        if hasattr(chatdev, "__version__"):
            pass
        else:
            pass

        # Try to import key components

        return True
    except ImportError:
        return False
    except (AttributeError, RuntimeError):
        return False


def test_our_integrations():
    """Test our custom integration modules."""
    # Add src to path
    repo_root = Path(__file__).parent
    src_path = repo_root / "src"
    sys.path.insert(0, str(src_path))

    success_count = 0
    total_tests = 0

    integrations_to_test = [
        "integration.chatdev_llm_adapter",
        "ai.ollama_chatdev_integrator",
        "integration.ollama_integration",
        "ai.ollama_model_manager",
        "diagnostics.chatdev_capabilities_test",
    ]

    for module_name in integrations_to_test:
        total_tests += 1
        try:
            importlib.import_module(module_name)  # nosemgrep
            success_count += 1
        except (ImportError, ModuleNotFoundError, AttributeError):
            logger.debug("Suppressed AttributeError/ImportError/ModuleNotFoundError", exc_info=True)

    return success_count > 0


def test_external_chatdev() -> bool:
    """Test the external ChatDev installation."""
    default_path = Path(__file__).resolve().parents[2] / "ChatDev-main"
    chatdev_env = os.getenv("CHATDEV_PATH", str(default_path))
    chatdev_path = Path(chatdev_env).expanduser()

    if chatdev_path.exists():
        # Check key files
        key_files = ["run.py", "chatdev/__init__.py", "chatdev/chatdev.py"]
        for file in key_files:
            if (chatdev_path / file).exists():
                pass
            else:
                pass

        # Check if we can run ChatDev
        try:
            old_cwd = os.getcwd()
            os.chdir(chatdev_path)

            result = subprocess.run(
                [sys.executable, "run.py", "--help"],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
            )

            os.chdir(old_cwd)

            return result.returncode == 0

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
            os.chdir(old_cwd)
            return False
    else:
        return False


def main() -> None:
    """Run all empirical tests."""
    results = {
        "ollama": test_ollama(),
        "chatdev_import": test_chatdev_import(),
        "our_integrations": test_our_integrations(),
        "external_chatdev": test_external_chatdev(),
    }

    functional_count = sum(results.values())
    len(results)

    for _test_name, _passed in results.items():
        pass

    if functional_count >= 3 or functional_count >= 2 or functional_count >= 1:
        pass
    else:
        pass

    if not results["ollama"]:
        pass
    if not results["chatdev_import"]:
        pass
    if not results["our_integrations"]:
        pass
    if not results["external_chatdev"]:
        pass


if __name__ == "__main__":
    main()
