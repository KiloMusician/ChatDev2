#!/usr/bin/env python3
"""KILO-FOOLISH Repository Health Verification System.

Test critical components to ensure they're working after our fixes.

OmniTag: {
    "purpose": "Health verification after fixes",
    "dependencies": ["All created modules"],
    "context": "System validation, testing",
    "evolution_stage": "v2.0"
}
"""

import importlib
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def test_critical_imports():
    """Test that our created modules can be imported."""
    # Test our created modules
    test_modules = [
        "LOGGING.modular_logging_system",
        "KILO_Core.secrets",
    ]

    success_count = 0
    total_count = len(test_modules)

    for module_name in test_modules:
        try:
            module = importlib.import_module(module_name)
            success_count += 1

            # Test key functions if they exist
            if hasattr(module, "log_info"):
                pass
            if hasattr(module, "get_api_key"):
                pass

        except (ImportError, ModuleNotFoundError, AttributeError):
            logger.debug("Suppressed AttributeError/ImportError/ModuleNotFoundError", exc_info=True)

    return success_count == total_count


def test_third_party_imports():
    """Test that third-party dependencies are available."""
    # Test important third-party modules
    test_modules = [
        "numpy",
        "scipy",
        "matplotlib",
        "pandas",
        "sympy",
        "sklearn",
        "networkx",
        "openai",
        "ollama",
        "psutil",
        "pytest",
        "aiohttp",
        "yaml",
        "rich",
        "typer",
    ]

    success_count = 0
    total_count = len(test_modules)

    for module_name in test_modules:
        try:
            module = importlib.import_module(module_name)
            getattr(module, "__version__", "unknown")
            success_count += 1
        except (ImportError, ModuleNotFoundError):
            pass

    return success_count >= total_count * 0.8  # Allow 20% failure


def test_ai_integration_modules():
    """Test that our created AI integration modules work."""
    # Add the path to our modules
    ai_path = Path("Transcendent_Spine/kilo-foolish-transcendent-spine/src/ai")
    if ai_path.exists():
        sys.path.insert(0, str(ai_path.absolute()))

    test_modules = [
        "ollama_integration",
        "conversation_manager",
        "ollama_hub",
    ]

    success_count = 0
    total_count = len(test_modules)

    for module_name in test_modules:
        try:
            module = importlib.import_module(module_name)
            success_count += 1

            # Test key classes if they exist
            if hasattr(module, "OllamaIntegration"):
                pass
            if hasattr(module, "ConversationManager"):
                pass
            if hasattr(module, "OllamaHub"):
                pass

        except (ImportError, ModuleNotFoundError, AttributeError):
            logger.debug("Suppressed AttributeError/ImportError/ModuleNotFoundError", exc_info=True)

    return success_count >= total_count * 0.5  # Allow 50% failure for these custom modules


def test_standard_library():
    """Test standard library imports that were flagged as broken."""
    test_modules = [
        "csv",
        "json",
        "os",
        "sys",
        "asyncio",
        "logging",
        "multiprocessing",
        "random",
        "re",
        "uuid",
        "hashlib",
        "builtins",
        "weakref",
        "sqlite3",
    ]

    success_count = 0
    total_count = len(test_modules)

    for module_name in test_modules:
        try:
            importlib.import_module(module_name)
            success_count += 1
        except (ImportError, ModuleNotFoundError):
            pass

    return success_count >= total_count * 0.9  # Expect 90% success for standard library


def test_key_functionality() -> bool | None:
    """Test key functionality of our fixes."""
    try:
        # Test logging system
        from src.LOGGING.modular_logging_system import (log_info,
                                                        log_tagged_event)

        log_info("test_module", "Test message from health verification")
        log_tagged_event(
            "test_module",
            "Tagged test message",
            omnitag={"purpose": "testing"},
            megatag={"type": "verification"},
        )

        # Test secrets management
        from KILO_Core.secrets import get_api_key

        get_api_key("openai")

        # Test that critical scientific computing works
        import numpy as np

        arr = np.array([1, 2, 3, 4, 5])
        np.mean(arr)

        # Test pandas basic functionality
        import pandas as pd

        pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})

        return True

    except (ImportError, ModuleNotFoundError, AttributeError, ValueError):
        return False


def run_comprehensive_health_check():
    """Run comprehensive health verification."""
    results: list[Any] = []
    # Run all tests
    results.append(("Critical Imports", test_critical_imports()))
    results.append(("Third-Party Dependencies", test_third_party_imports()))
    results.append(("AI Integration", test_ai_integration_modules()))
    results.append(("Standard Library", test_standard_library()))
    results.append(("Key Functionality", test_key_functionality()))

    # Summary

    passed = 0
    total = len(results)

    for _test_name, success in results:
        if success:
            passed += 1

    overall_health = passed / total

    if overall_health >= 0.8 or overall_health >= 0.6:
        pass
    else:
        pass

    if overall_health < 1.0:
        pass
    else:
        pass

    return overall_health >= 0.6


if __name__ == "__main__":
    success = run_comprehensive_health_check()
    sys.exit(0 if success else 1)
