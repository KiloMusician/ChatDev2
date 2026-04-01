"""Lightweight system verification shim for NuSyQ-Hub.

This file was empty and caused import errors when `main.py` attempted to
`from system_verification import SystemVerificationEngine`.

This module provides a minimal, deterministic `SystemVerificationEngine`
implementation that attempts to import canonical verification modules and,
if those are not present, performs safe fallback checks of core subsystems.

It is intentionally small and defensive so it can be used as a compatibility
shim while the repository is consolidated.
"""

from __future__ import annotations

import importlib
import logging

logger = logging.getLogger(__name__)


class SystemVerificationEngine:
    """Compatibility verification engine.

    Methods:
      - run_full_verification() -> Dict: returns a report with at least
        an 'overall_status' key set to 'healthy' or 'unhealthy'.
    """

    def __init__(self) -> None:
        self._candidates = [
            "src.verification.system_verification",
            "src.system_verification",
            "verification.system_verification",
            "src.tools.system_verification",
        ]

    def _try_import(self, name: str):
        try:
            return importlib.import_module(name)
        except (ImportError, ModuleNotFoundError, AttributeError):
            return None

    def run_full_verification(self) -> dict:
        """Run verification and return a report dict.

        The implementation first tries to find a canonical verification
        implementation in likely locations (useful if code was refactored).
        If none found, it performs a small set of safe import checks to
        determine basic subsystem health.
        """
        # Try to locate a richer implementation and delegate if possible
        for mod_name in self._candidates:
            mod = self._try_import(mod_name)
            if not mod:
                continue
            # Prefer an exported SystemVerificationEngine
            if hasattr(mod, "SystemVerificationEngine"):
                try:
                    impl = mod.SystemVerificationEngine()
                    if hasattr(impl, "run_full_verification"):
                        return impl.run_full_verification()
                except Exception as e:
                    logger.debug("Delegated verification failed: %s", e)
            # Try other common names
            for alt in ("SystemVerifier", "Verifier", "VerificationEngine"):
                if hasattr(mod, alt):
                    try:
                        impl = getattr(mod, alt)()
                        if hasattr(impl, "run_full_verification"):
                            return impl.run_full_verification()
                    except (AttributeError, TypeError, RuntimeError):
                        continue

        # Lightweight fallback checks
        report = {"overall_status": "healthy", "details": {}}
        core_checks = [
            "src.ai.ai_coordinator",
            "src.copilot.copilot_enhancement_bridge",
            "src.integration.Ollama_Integration_Hub",
            "src.integration.chatdev_llm_adapter",
        ]

        for module in core_checks:
            try:
                importlib.import_module(module)
                report["details"][module] = {"ok": True, "error": None}
            except Exception as e:
                report["details"][module] = {"ok": False, "error": str(e)}
                report["overall_status"] = "unhealthy"

        return report


# Backwards compatibility alias
class SystemVerifier(SystemVerificationEngine):
    """System verifier implementation wrapping SystemVerificationEngine."""

    pass
