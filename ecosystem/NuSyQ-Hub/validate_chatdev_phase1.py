#!/usr/bin/env python3
"""Phase 1 ChatDev Configuration Validation Script
Validates that the ChatDev integration is properly configured and working.
"""

import sys
import logging
from pathlib import Path


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.info("\n" + "=" * 70)
    logging.info("PHASE 1: CHATDEV CONFIGURATION VALIDATION")
    logging.info("=" * 70 + "\n")

    # Test 1: Configuration file reads ChatDev path
    logging.info("[1/5] Reading ChatDev path from config/settings.json...")
    try:
        import json
        settings_path = Path("config/settings.json")
        if not settings_path.exists():
            logging.error("  ❌ config/settings.json not found at %s", settings_path.absolute())
            return False

        with open(settings_path, encoding="utf-8") as f:
            settings = json.load(f)
            chatdev_path = settings.get("chatdev", {}).get("path")
            if chatdev_path == "chatdev_stub":
                logging.warning("  ⚠️  ChatDev path is still 'chatdev_stub' (needs update)")
                return False
            elif not chatdev_path:
                logging.error("  ❌ No ChatDev path configured")
                return False
            else:
                logging.info("  ✅ ChatDev path: %s", chatdev_path)
    except Exception as e:
        logging.exception("  ❌ Error reading config: %s", e)
        return False

    # Test 2: ChatDev directory exists
    logging.info("\n[2/5] Verifying ChatDev installation directory...")
    try:
        chatdev_dir = Path(chatdev_path)
        if not chatdev_dir.exists():
            logging.error("  ❌ ChatDev directory not found: %s", chatdev_dir)
            return False
        logging.info("  ✅ Directory exists: %s", chatdev_dir)
    except Exception as e:
        logging.exception("  ❌ Error checking directory: %s", e)
        return False

    # Test 3: Required files present
    logging.info("\n[3/5] Checking for required ChatDev files...")
    required_files = ["run.py"]
    all_present = True
    for fname in required_files:
        fpath = chatdev_dir / fname
        if fpath.exists():
            size_kb = fpath.stat().st_size / 1024
            logging.info("  ✅ %s (%.1f KB)", fname, size_kb)
        else:
            logging.error("  ❌ %s missing", fname)
            all_present = False

    if not all_present:
        return False

    # Test 4: Factory pattern detects ChatDev
    logging.info("\n[4/5] Testing ChatDev detection via AIOrchestrator...")
    try:
        from src.factories.ai_orchestrator import AIOrchestrator

        orch = AIOrchestrator()
        detected_path = orch._detect_chatdev()
        if detected_path:
            logging.info("  ✅ ChatDev detected at: %s", detected_path)
        else:
            logging.error("  ❌ ChatDev not detected")
            return False
    except Exception as e:
        logging.exception("  ❌ Error during detection: %s", e)
        return False

    # Test 5: Integration modules available
    logging.info("\n[5/5] Checking integration modules...")
    try:
        from src.integration.chatdev_integration import ChatDevIntegrationManager
        from src.integration.chatdev_launcher import ChatDevLauncher

        _ = (ChatDevLauncher, ChatDevIntegrationManager)
        logging.info("  ✅ ChatDevLauncher available")
        logging.info("  ✅ ChatDevIntegrationManager available")
    except ImportError as e:
        logging.error("  ❌ Missing integration module: %s", e)
        return False

    # Success!
    logging.info("\n" + "=" * 70)
    logging.info("✅ PHASE 1 VALIDATION COMPLETE - ALL CHECKS PASSED!")
    logging.info("=" * 70)
    logging.info("\nNext Steps:")
    logging.info("  Phase 2: Test ChatDev code generation end-to-end")
    logging.info("  Phase 3: Integrate with Ollama for local LLM routing")
    logging.info("  Phase 4: Complete MCP server integration")
    logging.info("")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
