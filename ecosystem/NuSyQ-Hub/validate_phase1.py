#!/usr/bin/env python3
"""Option A: Validate Phase 1 ChatDev Integration"""

import logging
import sys


def validate_phase1():
    """Validate ChatDev integration is working."""
    try:
        from src.integration.chatdev_launcher import ChatDevLauncher
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        logging.info("✅ ChatDevLauncher imported successfully")

        launcher = ChatDevLauncher()
        logging.info("✅ ChatDevLauncher instantiated")

        # Check API key setup
        launcher.setup_api_key()
        logging.info("✅ API key setup complete")

        # Check environment
        launcher.setup_environment()
        logging.info("✅ Environment setup complete")

        # Check status
        status = launcher.check_status()
        logging.info("✅ Launcher status: %s", status)

        logging.info("\n🎯 OPTION A RESULT: GAS (ChatDev integration is working!)\n")
        return True

    except Exception:
        logging.exception("❌ ERROR during ChatDev Phase1 validation")
        logging.info("\n🎯 OPTION A RESULT: SNAKE_OIL (ChatDev has issues)\n")
        return False


if __name__ == "__main__":
    success = validate_phase1()
    sys.exit(0 if success else 1)
